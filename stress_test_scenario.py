from typing import Dict, List
from datetime import datetime, timedelta
import json
import errfriendly

# Enable the new Proactive Audit feature
# Enable the new Proactive Audit feature and Friendly Warnings
errfriendly.enable_audit()
errfriendly.enable_warnings()

class EventCache:
    def __init__(self):
        self._cache: Dict[str, List[dict]] = {}

    def add_event(self, user_id: str, event: dict):
        if user_id not in self._cache:
            self._cache[user_id] = []
        self._cache[user_id].append(event)

    def get_events(self, user_id: str) -> List[dict]:
        return self._cache.get(user_id, [])

def serialize_event(event: dict) -> str:
    # BUG: default argument hides serialization issues
    return json.dumps(event, default=str)

def process_events(cache: EventCache, user_id: str) -> int:
    today = datetime.utcnow().date()
    count = 0

    for event in cache.get_events(user_id):
        # BUG: serialization masking errors
        raw = serialize_event(event) 
        parsed = json.loads(raw)

        # Potential crash: Missing 'timestamp' key
        if "timestamp" not in parsed:
            continue

        # Potential crash: ValueError if format is bad
        # BUG: Naive UTC vs Local time string mixing
        try:
            event_time = datetime.fromisoformat(parsed["timestamp"])
            if event_time.date() == today:
                count += 1
        except ValueError:
            pass # Silenced for now, but a real bug source

    return count

# --- Stress Test Scenarios ---
cache = EventCache()

# Case 1: Standard datetime (naive UTC)
cache.add_event("u1", {"type": "login", "timestamp": datetime.utcnow()})

# Case 2: String timestamp (potential format mismatch?)
# Note: 'T' separator is standard ISO, but str(datetime) uses space
cache.add_event("u1", {"type": "logout", "timestamp": "2025-12-30T23:59:59"})

# Case 3: Edge Case - Non-serializable object masked by default=str
class ComplexObj:
    def __repr__(self): return "<ComplexObj>"
    
cache.add_event("u1", {"type": "complex", "data": ComplexObj(), "timestamp": datetime.utcnow()})
# Result: "data": "<ComplexObj>" -> Data effectively destroyed/flattened without warning

# Case 4: Edge Case - Timezone Aware vs Naive mismatch
# datetime.now().astimezone() gives aware, utcnow() gives naive.
# default=str dumps aware as "2025-12-30 20:44:00+05:30"
# fromisoformat handles it, but comparison to naive 'today' might warn or fail depending on python version logic/strictness
# But strict equality date() comparison works fine across aware/naive usually.

print("Count:", process_events(cache, "u1"))
