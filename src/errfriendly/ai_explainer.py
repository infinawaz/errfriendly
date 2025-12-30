"""
ai_explainer.py - AI-powered contextual explanation engine.

This module provides the core AI explanation functionality with pluggable
backends (Ollama, OpenAI, Anthropic, Gemini) and smart prompt engineering.
"""

import hashlib
import json
import re
import time
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
from functools import lru_cache

from .models import (
    ErrorContext, 
    AIExplanation, 
    Config, 
    ExplainDepth, 
    AIBackend,
    ExplanationStyle,
)

# Prompt templates
SYSTEM_PROMPT = """You are a senior Python engineer explaining errors to a developer.

Your task: Analyze the error context and provide a helpful, actionable explanation.

Explanation depth: {depth_instruction}

Constraints:
- Provide 3 specific fixes: (1) Quick workaround, (2) Proper solution, (3) Preventive pattern
- Use markdown with code blocks showing BEFORE/AFTER when helpful
- Be helpful and concise, avoid condescension
- Reference the actual code and variable values when relevant
- If the error pattern is common, mention that

Format your response EXACTLY as follows (include all sections):

## 🤔 What Happened?
[1-3 sentences explaining the error in context of the actual code shown]

## 🔍 Root Cause Analysis
- Primary issue: [Specific code pattern or mistake]
- Contributing factors: [Related code smells if any]
- Confidence: [High/Medium/Low]

## 🛠️ How to Fix

### Option 1: Quick Fix (Immediate)
[Brief description]
```python
# Code fix
```

### Option 2: Robust Solution (Recommended)
[Brief description]
```python
# Better code
```

### Option 3: Prevent Future Occurrences
[Brief description]
```python
# Preventive pattern
```

## 📚 Related Documentation
- [Relevant Python doc or resource]
"""

DEPTH_INSTRUCTIONS = {
    ExplainDepth.BEGINNER: (
        "Explain like I'm a coding student. Use simple language, "
        "avoid jargon, and explain any technical terms you use."
    ),
    ExplainDepth.INTERMEDIATE: (
        "Assume solid Python knowledge. Be concise but thorough. "
        "Reference Python concepts without over-explaining."
    ),
    ExplainDepth.EXPERT: (
        "Go deep on internals and edge cases. Reference CPython behavior, "
        "performance implications, and advanced patterns."
    ),
}


class AIBackendBase(ABC):
    """Abstract base class for AI backends."""
    
    @abstractmethod
    def generate(self, prompt: str, system_prompt: str) -> str:
        """Generate a response from the AI model.
        
        Args:
            prompt: The user prompt with error context.
            system_prompt: System prompt with instructions.
            
        Returns:
            The AI-generated response text.
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if this backend is available and configured.
        
        Returns:
            True if the backend can be used.
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Return the backend name for logging."""
        pass


class OllamaBackend(AIBackendBase):
    """Local Ollama backend for privacy-first AI.
    
    Requires Ollama to be running locally (https://ollama.ai).
    """
    
    def __init__(self, model: str = "codellama", timeout: float = 30.0):
        """Initialize Ollama backend.
        
        Args:
            model: Model name (e.g., 'codellama', 'llama2', 'mistral').
            timeout: Request timeout in seconds.
        """
        self.model = model
        self.timeout = timeout
        self.base_url = "http://localhost:11434"
    
    @property
    def name(self) -> str:
        return f"Ollama ({self.model})"
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            import httpx
            with httpx.Client(timeout=2.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False
    
    def generate(self, prompt: str, system_prompt: str) -> str:
        """Generate response using Ollama."""
        try:
            import httpx
        except ImportError:
            raise ImportError(
                "httpx is required for Ollama backend. "
                "Install it with: pip install errfriendly[ai-local]"
            )
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "system": system_prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
            }
        }
        
        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(
                f"{self.base_url}/api/generate",
                json=payload,
            )
            response.raise_for_status()
            return response.json().get("response", "")


class OpenAIBackend(AIBackendBase):
    """OpenAI API backend."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gpt-4o-mini",
        timeout: float = 30.0
    ):
        """Initialize OpenAI backend.
        
        Args:
            api_key: OpenAI API key. Uses OPENAI_API_KEY env var if not provided.
            model: Model name (e.g., 'gpt-4', 'gpt-4o-mini', 'gpt-3.5-turbo').
            timeout: Request timeout in seconds.
        """
        import os
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return f"OpenAI ({self.model})"
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def generate(self, prompt: str, system_prompt: str) -> str:
        """Generate response using OpenAI API."""
        try:
            import openai
        except ImportError:
            raise ImportError(
                "openai is required for OpenAI backend. "
                "Install it with: pip install errfriendly[ai-openai]"
            )
        
        client = openai.OpenAI(api_key=self.api_key, timeout=self.timeout)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=1500,
        )
        
        return response.choices[0].message.content or ""


class AnthropicBackend(AIBackendBase):
    """Anthropic Claude API backend."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "claude-3-haiku-20240307",
        timeout: float = 30.0
    ):
        """Initialize Anthropic backend.
        
        Args:
            api_key: Anthropic API key. Uses ANTHROPIC_API_KEY env var if not provided.
            model: Model name (e.g., 'claude-3-opus', 'claude-3-sonnet', 'claude-3-haiku').
            timeout: Request timeout in seconds.
        """
        import os
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return f"Anthropic ({self.model})"
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def generate(self, prompt: str, system_prompt: str) -> str:
        """Generate response using Anthropic API."""
        try:
            import anthropic
        except ImportError:
            raise ImportError(
                "anthropic is required for Anthropic backend. "
                "Install it with: pip install errfriendly[ai-anthropic]"
            )
        
        client = anthropic.Anthropic(api_key=self.api_key)
        
        response = client.messages.create(
            model=self.model,
            max_tokens=1500,
            system=system_prompt,
            messages=[
                {"role": "user", "content": prompt},
            ],
        )
        
        return response.content[0].text


class GeminiBackend(AIBackendBase):
    """Google Gemini API backend."""
    
    def __init__(
        self, 
        api_key: Optional[str] = None, 
        model: str = "gemini-1.5-flash",
        timeout: float = 30.0
    ):
        """Initialize Gemini backend.
        
        Args:
            api_key: Google API key. Uses GOOGLE_API_KEY env var if not provided.
            model: Model name (e.g., 'gemini-pro', 'gemini-1.5-flash').
            timeout: Request timeout in seconds.
        """
        import os
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY", "")
        self.model = model
        self.timeout = timeout
    
    @property
    def name(self) -> str:
        return f"Gemini ({self.model})"
    
    def is_available(self) -> bool:
        """Check if API key is configured."""
        return bool(self.api_key)
    
    def generate(self, prompt: str, system_prompt: str) -> str:
        """Generate response using Gemini API."""
        try:
            import google.generativeai as genai
        except ImportError:
            raise ImportError(
                "google-generativeai is required for Gemini backend. "
                "Install it with: pip install errfriendly[ai-gemini]"
            )
        
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        
        full_prompt = f"{system_prompt}\n\n{prompt}"
        response = model.generate_content(full_prompt)
        
        return response.text


class AIExplainer:
    """Main AI explanation orchestrator.
    
    Manages backend selection, caching, prompt building, and response parsing.
    """
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize the AI explainer.
        
        Args:
            config: Configuration options. Uses defaults if not provided.
        """
        self.config = config or Config()
        self._cache: Dict[str, AIExplanation] = {}
        self._backend: Optional[AIBackendBase] = None
        self._last_request_time: float = 0
        self._request_count: int = 0
    
    def _init_backend(self) -> Optional[AIBackendBase]:
        """Initialize the appropriate backend based on config."""
        if self._backend is not None:
            return self._backend
        
        backend_map = {
            AIBackend.LOCAL: lambda: OllamaBackend(
                model=self.config.ai_model,
                timeout=self.config.ai_timeout,
            ),
            AIBackend.OPENAI: lambda: OpenAIBackend(
                model=self.config.ai_model,
                timeout=self.config.ai_timeout,
            ),
            AIBackend.ANTHROPIC: lambda: AnthropicBackend(
                model=self.config.ai_model,
                timeout=self.config.ai_timeout,
            ),
            AIBackend.GEMINI: lambda: GeminiBackend(
                model=self.config.ai_model,
                timeout=self.config.ai_timeout,
            ),
        }
        
        factory = backend_map.get(self.config.ai_backend)
        if factory:
            self._backend = factory()
            return self._backend
        
        return None
    
    def explain(self, context: ErrorContext) -> Optional[AIExplanation]:
        """Generate AI-powered explanation for an error.
        
        Args:
            context: The error context collected by ContextCollector.
            
        Returns:
            AIExplanation if successful, None if AI unavailable or failed.
        """
        # Check if AI is enabled
        if not self.config.ai_enabled:
            return None
        
        # Rate limiting
        if not self._check_rate_limit():
            return None
        
        # Check cache first
        cache_key = self._compute_cache_key(context)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        # Initialize backend
        backend = self._init_backend()
        if backend is None or not backend.is_available():
            return None
        
        # Build prompts
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(context)
        
        # Generate explanation
        try:
            response = backend.generate(user_prompt, system_prompt)
            explanation = self._parse_response(response)
            
            # Cache if high confidence
            if explanation and explanation.confidence >= self.config.ai_threshold:
                # Evict oldest entry if cache is full
                if len(self._cache) >= self.config.max_cache_size:
                    oldest_key = next(iter(self._cache))
                    del self._cache[oldest_key]
                self._cache[cache_key] = explanation
            
            return explanation
            
        except Exception as e:
            # Log error but don't crash
            import sys
            print(f"[errfriendly] AI explanation failed: {e}", file=sys.stderr)
            return None
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits.
        
        Returns:
            True if request is allowed.
        """
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self._last_request_time > 60:
            self._request_count = 0
            self._last_request_time = current_time
        
        if self._request_count >= self.config.max_requests_per_minute:
            return False
        
        self._request_count += 1
        return True
    
    def _compute_cache_key(self, context: ErrorContext) -> str:
        """Create cache key from error signature.
        
        Args:
            context: Error context.
            
        Returns:
            MD5 hash of error signature.
        """
        # Key on error type and message pattern, not exact message
        key_data = f"{context.exception_type}:{context.error_message[:100]}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:16]
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt with depth instruction.
        
        Returns:
            Formatted system prompt.
        """
        depth_instruction = DEPTH_INSTRUCTIONS.get(
            self.config.explain_depth,
            DEPTH_INSTRUCTIONS[ExplainDepth.INTERMEDIATE]
        )
        return SYSTEM_PROMPT.format(depth_instruction=depth_instruction)
    
    def _build_user_prompt(self, context: ErrorContext) -> str:
        """Build user prompt with error context.
        
        Args:
            context: Error context.
            
        Returns:
            Formatted user prompt.
        """
        return f"""Please analyze this Python error:

{context.to_prompt_context()}

Traceback (most recent frame):
{self._format_traceback(context)}

Provide a helpful explanation following the exact format specified."""
    
    def _format_traceback(self, context: ErrorContext) -> str:
        """Format traceback frames for the prompt.
        
        Args:
            context: Error context with frames.
            
        Returns:
            Formatted traceback string.
        """
        lines = []
        for frame in context.full_traceback[-3:]:  # Last 3 frames
            lines.append(f"  File \"{frame.filename}\", line {frame.lineno}, in {frame.function}")
            if frame.code_context:
                for code_line in frame.code_context:
                    lines.append(f"    {code_line}")
        return "\n".join(lines)
    
    def _parse_response(self, response: str) -> Optional[AIExplanation]:
        """Parse AI response into structured explanation.
        
        Args:
            response: Raw AI response text.
            
        Returns:
            Parsed AIExplanation or None if parsing fails.
        """
        if not response:
            return None
        
        # Default values
        what_happened = ""
        root_cause = ""
        confidence = 0.5
        quick_fix = ""
        robust_solution = ""
        preventive = ""
        docs: List[str] = []
        
        # Parse sections using regex
        sections = {
            "what_happened": r"## 🤔 What Happened\??\s*\n(.*?)(?=##|$)",
            "root_cause": r"## 🔍 Root Cause Analysis\s*\n(.*?)(?=##|$)",
            "quick_fix": r"### Option 1:.*?\n(.*?)(?=###|##|$)",
            "robust": r"### Option 2:.*?\n(.*?)(?=###|##|$)",
            "preventive": r"### Option 3:.*?\n(.*?)(?=###|##|$)",
            "docs": r"## 📚 Related Documentation\s*\n(.*?)(?=##|$)",
        }
        
        for key, pattern in sections.items():
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                content = match.group(1).strip()
                if key == "what_happened":
                    what_happened = content
                elif key == "root_cause":
                    root_cause = content
                    # Try to extract confidence
                    conf_match = re.search(r"confidence:\s*(high|medium|low)", content, re.I)
                    if conf_match:
                        conf_map = {"high": 0.9, "medium": 0.7, "low": 0.5}
                        confidence = conf_map.get(conf_match.group(1).lower(), 0.7)
                elif key == "quick_fix":
                    quick_fix = content
                elif key == "robust":
                    robust_solution = content
                elif key == "preventive":
                    preventive = content
                elif key == "docs":
                    # Extract bullet points
                    docs = re.findall(r"[-*]\s*(.+)", content)
        
        # If parsing mostly failed, use the raw response
        if not what_happened and not quick_fix:
            what_happened = response[:500]
            confidence = 0.3
        
        return AIExplanation(
            what_happened=what_happened,
            root_cause_analysis=root_cause,
            confidence=confidence,
            quick_fix=quick_fix,
            robust_solution=robust_solution,
            preventive_pattern=preventive,
            related_docs=docs,
            raw_response=response,
        )
    
    def clear_cache(self):
        """Clear the explanation cache."""
        self._cache.clear()
    
    @property
    def cache_size(self) -> int:
        """Return current cache size."""
        return len(self._cache)
