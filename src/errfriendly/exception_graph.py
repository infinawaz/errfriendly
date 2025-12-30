"""
exception_graph.py - Exception chain analysis and visualization.

This module provides functionality to analyze exception chains (__cause__
and __context__), identify root causes, classify chain types, and generate
debugging narratives.
"""

import traceback
from typing import Type, Optional, List
from dataclasses import dataclass

from .models import ExceptionChain, ChainLink


# Common wrapper exception patterns by framework
WRAPPER_PATTERNS = {
    # requests library
    'RequestException': ['ConnectionError', 'HTTPError', 'Timeout'],
    # Django
    'ValidationError': ['ValueError', 'TypeError'],
    'ImproperlyConfigured': ['ImportError', 'KeyError'],
    # FastAPI/Starlette
    'HTTPException': ['ValueError', 'KeyError', 'TypeError'],
    # SQLAlchemy
    'SQLAlchemyError': ['IntegrityError', 'OperationalError'],
    # Generic patterns
    'RuntimeError': ['ValueError', 'TypeError', 'AttributeError'],
}


class ExceptionChainAnalyzer:
    """Analyzes exception chains for root cause identification.
    
    This class walks through Python's exception chain (__cause__ and
    __context__) to build a complete picture of cascading failures
    and identify the root cause.
    """
    
    def analyze(
        self,
        exc_type: Type[BaseException],
        exc_value: BaseException,
        exc_traceback
    ) -> ExceptionChain:
        """Build complete exception chain analysis.
        
        Args:
            exc_type: The exception class.
            exc_value: The exception instance.
            exc_traceback: The traceback object.
            
        Returns:
            ExceptionChain with full analysis.
        """
        chain = self._build_chain(exc_value)
        
        if not chain:
            return ExceptionChain()
        
        chain_type = self._classify_chain(chain)
        root = self._identify_root_cause(chain)
        priorities = self._rank_fix_priority(chain, chain_type)
        
        return ExceptionChain(
            primary_exception=chain[0],
            chain=chain[1:] if len(chain) > 1 else [],
            root_cause=root,
            chain_type=chain_type,
            fix_priority=priorities,
        )
    
    def _build_chain(self, exc: BaseException) -> List[ChainLink]:
        """Walk the exception chain and build links.
        
        Args:
            exc: The exception to start from.
            
        Returns:
            List of ChainLink objects from primary to root.
        """
        chain = []
        current = exc
        seen = set()  # Prevent infinite loops
        
        while current is not None and id(current) not in seen:
            seen.add(id(current))
            
            # Count frames in this exception's traceback
            frame_count = 0
            tb = current.__traceback__
            while tb is not None:
                frame_count += 1
                tb = tb.tb_next
            
            # Determine cause type
            if current.__cause__ is not None:
                cause_type = "cause"
            elif current.__context__ is not None:
                cause_type = "context"
            else:
                cause_type = "none"
            
            link = ChainLink(
                exception_type=type(current).__name__,
                message=str(current)[:200],  # Limit message length
                traceback_summary=self._summarize_traceback(current.__traceback__),
                cause_type=cause_type,
                is_suppressed=current.__suppress_context__,
                frame_count=frame_count,
            )
            chain.append(link)
            
            # Walk up the chain
            if current.__cause__ is not None:
                current = current.__cause__
            elif current.__context__ is not None and not current.__suppress_context__:
                current = current.__context__
            else:
                break
        
        return chain
    
    def _summarize_traceback(self, tb) -> str:
        """Create a brief traceback summary.
        
        Args:
            tb: Traceback object.
            
        Returns:
            Summary string with file:line info.
        """
        if tb is None:
            return "No traceback"
        
        # Get the last frame
        last_tb = tb
        while last_tb.tb_next is not None:
            last_tb = last_tb.tb_next
        
        frame = last_tb.tb_frame
        filename = frame.f_code.co_filename.split('/')[-1].split('\\')[-1]
        lineno = last_tb.tb_lineno
        func = frame.f_code.co_name
        
        return f"{filename}:{lineno} in {func}"
    
    def _classify_chain(self, chain: List[ChainLink]) -> str:
        """Classify the chain type for fix strategy.
        
        Args:
            chain: List of exception chain links.
            
        Returns:
            Chain type: "simple", "wrapper", "cascade", "cleanup", or "chained".
        """
        if len(chain) == 1:
            return "simple"
        
        # Check for wrapper patterns
        if self._is_wrapper_pattern(chain):
            return "wrapper"
        
        # Check for cascade failures (error causing multiple subsequent errors)
        if self._is_cascade_pattern(chain):
            return "cascade"
        
        # Check for cleanup failures (errors in __exit__ or finally)
        if self._is_cleanup_failure(chain):
            return "cleanup"
        
        return "chained"
    
    def _is_wrapper_pattern(self, chain: List[ChainLink]) -> bool:
        """Check if the chain represents a wrapper pattern.
        
        Wrapper patterns occur when a library catches a low-level
        exception and re-raises it as a high-level exception.
        
        Args:
            chain: Exception chain links.
            
        Returns:
            True if this is a wrapper pattern.
        """
        if len(chain) < 2:
            return False
        
        primary = chain[0].exception_type
        secondary = chain[1].exception_type
        
        # Check known wrapper patterns
        if primary in WRAPPER_PATTERNS:
            return secondary in WRAPPER_PATTERNS[primary]
        
        # Generic heuristics:
        # - Primary ends with "Error" and wraps standard exceptions
        # - "from e" pattern with explicit chaining
        if chain[0].cause_type == "cause":
            standard_errors = {
                'ValueError', 'TypeError', 'KeyError', 'AttributeError',
                'IndexError', 'FileNotFoundError', 'ConnectionError',
            }
            return secondary in standard_errors
        
        return False
    
    def _is_cascade_pattern(self, chain: List[ChainLink]) -> bool:
        """Check if the chain represents a cascade failure.
        
        Cascade failures occur when an initial error causes multiple
        subsequent errors as the program tries to handle the situation.
        
        Args:
            chain: Exception chain links.
            
        Returns:
            True if this is a cascade pattern.
        """
        if len(chain) < 2:
            return False
        
        # Cascade pattern: multiple errors from implicit context chain
        # (not explicit "raise from")
        context_count = sum(1 for link in chain if link.cause_type == "context")
        
        return context_count >= 2
    
    def _is_cleanup_failure(self, chain: List[ChainLink]) -> bool:
        """Check if the chain includes a cleanup failure.
        
        Cleanup failures occur when an error happens in __exit__,
        finally blocks, or exception handlers.
        
        Args:
            chain: Exception chain links.
            
        Returns:
            True if this is a cleanup failure pattern.
        """
        if len(chain) < 2:
            return False
        
        # Look for patterns suggesting cleanup code failure
        cleanup_keywords = ['__exit__', '__del__', 'close', 'cleanup', 'finally']
        
        for link in chain:
            summary = link.traceback_summary.lower()
            if any(keyword in summary for keyword in cleanup_keywords):
                return True
        
        return False
    
    def _identify_root_cause(self, chain: List[ChainLink]) -> Optional[ChainLink]:
        """Find the root cause in the exception chain.
        
        The root cause is typically the deepest non-suppressed exception.
        
        Args:
            chain: Exception chain links.
            
        Returns:
            The root cause ChainLink, or None if chain is empty.
        """
        if not chain:
            return None
        
        # Walk from the end (deepest) to find first non-suppressed
        for link in reversed(chain):
            if not link.is_suppressed:
                return link
        
        # If all suppressed, return the deepest anyway
        return chain[-1]
    
    def _rank_fix_priority(
        self, 
        chain: List[ChainLink], 
        chain_type: str
    ) -> List[int]:
        """Rank exceptions by fix priority.
        
        Different chain types have different fix priorities:
        - Wrapper: Fix the inner exception first
        - Cascade: Fix the root cause
        - Cleanup: Fix both original and cleanup
        
        Args:
            chain: Exception chain links.
            chain_type: Classified chain type.
            
        Returns:
            List of indices ordered by fix priority.
        """
        if not chain:
            return []
        
        if len(chain) == 1:
            return [0]
        
        if chain_type == "wrapper":
            # Fix the wrapped (inner) exception first
            return list(range(len(chain) - 1, -1, -1))
        
        elif chain_type == "cascade":
            # Fix root cause first, then work up
            return list(range(len(chain) - 1, -1, -1))
        
        elif chain_type == "cleanup":
            # Fix both: original error and cleanup code
            # Original error is deeper in chain
            priorities = list(range(len(chain) - 1, -1, -1))
            # But also address the cleanup failure (usually position 0 or 1)
            return priorities
        
        else:
            # Default: fix from root to primary
            return list(range(len(chain) - 1, -1, -1))
    
    def generate_narrative(self, chain: ExceptionChain) -> str:
        """Generate a debugging story from the exception chain.
        
        Creates a human-readable narrative explaining how errors
        cascaded and what the root cause is.
        
        Args:
            chain: Analyzed exception chain.
            
        Returns:
            Narrative string explaining the error chain.
        """
        if chain.primary_exception is None:
            return "No exception information available."
        
        if not chain.has_chain:
            return self._format_simple_narrative(chain.primary_exception)
        
        return self._format_chain_narrative(chain)
    
    def _format_simple_narrative(self, exc: ChainLink) -> str:
        """Format narrative for a simple (non-chained) exception.
        
        Args:
            exc: The single exception.
            
        Returns:
            Simple narrative string.
        """
        return f"""🎯 Direct Error:
{exc.exception_type}: {exc.message}
   Location: {exc.traceback_summary}"""
    
    def _format_chain_narrative(self, chain: ExceptionChain) -> str:
        """Format narrative for a chained exception.
        
        Args:
            chain: Full exception chain.
            
        Returns:
            Chain narrative with visual map and story.
        """
        lines = [
            "🕵️ Exception Investigation Map:",
            "",
            f"[Primary Error] {chain.primary_exception.exception_type}: {chain.primary_exception.message}"
        ]
        
        for i, link in enumerate(chain.chain):
            indent = "    " * (i + 1)
            if link.cause_type == "cause":
                prefix = "Caused by"
            elif link.is_suppressed:
                prefix = "Suppressed during"
            else:
                prefix = "During handling of"
            
            lines.append(
                f"{indent}↳ {prefix}: [{link.exception_type}] {link.message}"
            )
        
        # Add the story
        lines.extend([
            "",
            "📖 Story:",
            self._generate_story(chain),
        ])
        
        # Add fix recommendation
        lines.extend([
            "",
            "🔧 Fix Strategy:",
            self.generate_fix_strategy(chain),
        ])
        
        return "\n".join(lines)
    
    def _generate_story(self, chain: ExceptionChain) -> str:
        """Generate a narrative story explaining the error chain.
        
        Args:
            chain: Exception chain.
            
        Returns:
            Story string.
        """
        if not chain.has_chain:
            return f"A {chain.primary_exception.exception_type} occurred directly."
        
        story_parts = []
        all_links = [chain.primary_exception] + chain.chain
        
        for i, link in enumerate(reversed(all_links), 1):
            if i == 1:
                story_parts.append(
                    f"({i}) First, a {link.exception_type} occurred: \"{link.message[:50]}...\""
                    if len(link.message) > 50 else
                    f"({i}) First, a {link.exception_type} occurred: \"{link.message}\""
                )
            else:
                connector = "which caused" if link.cause_type == "cause" else "during handling, triggered"
                story_parts.append(
                    f"({i}) {connector} a {link.exception_type}: \"{link.message[:50]}...\""
                    if len(link.message) > 50 else
                    f"({i}) {connector} a {link.exception_type}: \"{link.message}\""
                )
        
        return " → ".join(story_parts)
    
    def generate_fix_strategy(self, chain: ExceptionChain) -> str:
        """Generate fix strategy based on chain type.
        
        Args:
            chain: Exception chain.
            
        Returns:
            Fix strategy recommendation.
        """
        strategies = {
            "simple": (
                f"Fix the {chain.primary_exception.exception_type} directly at "
                f"{chain.primary_exception.traceback_summary}."
            ),
            "wrapper": (
                f"Focus on the underlying {chain.root_cause.exception_type}: "
                f"\"{chain.root_cause.message}\". "
                f"The {chain.primary_exception.exception_type} is just a wrapper."
            ) if chain.root_cause else "Fix the underlying exception first.",
            "cascade": (
                f"Fix the root cause ({chain.root_cause.exception_type}) to prevent "
                f"the cascade. Add validation before the operation that triggers "
                f"\"{chain.root_cause.message[:50]}\"."
            ) if chain.root_cause else "Fix the earliest error in the chain.",
            "cleanup": (
                "Two issues to fix:\n"
                f"  1. Original error: {chain.root_cause.exception_type if chain.root_cause else 'unknown'}\n"
                f"  2. Cleanup failure: {chain.primary_exception.exception_type}\n"
                "Fix both separately to ensure proper error handling."
            ),
            "chained": (
                f"Address errors from root to surface:\n" +
                "\n".join(
                    f"  {i+1}. Fix {chain.chain[-(i+1)].exception_type}" 
                    for i in range(min(3, len(chain.chain)))
                ) +
                f"\n  → Then the {chain.primary_exception.exception_type} should resolve."
            ) if chain.chain else "Fix the exception at the reported location.",
        }
        
        return strategies.get(chain.chain_type, strategies["chained"])
