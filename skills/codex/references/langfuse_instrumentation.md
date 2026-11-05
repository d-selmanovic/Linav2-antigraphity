# Langfuse v2 Instrumentation Reference

## 1. SDK Initialization
```python
from langfuse import Langfuse
import os

langfuse = Langfuse(
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
)
```

## 2. Event Types & Hierarchy
* **Trace:** 1 per PBX phone call (`session_id=call_id`, `user_id=caller_id`).
* **Generation:** Model output turns (transcripts from Gemini Live).
* **Span:** Internal function execution (e.g. `save_or_update_candidate` in Airtable).
* **Event:** Immediate discrete signals (e.g. `barge_in_interrupted`, `dialplan_transfer`).

## 3. Flush Strategy
Call `langfuse.flush()` in the `finally` block of `server.py` to ensure events are dispatched before WebSocket teardown.
