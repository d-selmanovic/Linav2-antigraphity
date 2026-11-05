import os
import time
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("LinaTracer")

try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False


class DummySpan:
    """Fallback-Span, falls Langfuse nicht aktiv ist"""
    def end(self, output: Any = None, level: str = "DEFAULT", status_message: str = ""):
        pass


class DummyTrace:
    """Fallback-Trace, falls Langfuse nicht aktiv ist"""
    def span(self, name: str, input: Any = None, metadata: Optional[Dict] = None):
        return DummySpan()

    def generation(self, name: str, input: Any = None, output: Any = None, metadata: Optional[Dict] = None):
        return DummySpan()

    def event(self, name: str, input: Any = None, output: Any = None, metadata: Optional[Dict] = None):
        pass

    def update(self, output: Any = None, metadata: Optional[Dict] = None, tags: Optional[list] = None):
        pass


class LinaTracer:
    """
    Langfuse-Observability-Manager für den Lina Voice Agent.
    Erfasst Anrufe, Live-Transkriptionen, Tool-Aufrufe (Airtable/n8n/MCP) und Latenzen.
    """

    def __init__(self):
        self.public_key = os.getenv("LANGFUSE_PUBLIC_KEY")
        self.secret_key = os.getenv("LANGFUSE_SECRET_KEY")
        self.host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
        self.client: Optional[Any] = None

        if LANGFUSE_AVAILABLE and self.public_key and self.secret_key:
            try:
                self.client = Langfuse(
                    public_key=self.public_key,
                    secret_key=self.secret_key,
                    host=self.host
                )
                logger.info(f"🚀 Langfuse Tracing aktiv! Verbunden mit Host: {self.host}")
            except Exception as e:
                logger.warning(f"Konnte Langfuse nicht initialisieren: {e}. Tracing wird deaktiviert.")
                self.client = None
        else:
            if not LANGFUSE_AVAILABLE:
                logger.info("ℹ️ Langfuse SDK nicht installiert (pip install langfuse). Tracing läuft im Dummy-Modus.")
            else:
                logger.info("ℹ️ Keine Langfuse-Keys gesetzt (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY). Tracing inaktiv.")

    @property
    def is_enabled(self) -> bool:
        return self.client is not None

    def start_call_trace(self, call_id: str, caller_id: str, metadata: Optional[Dict] = None):
        """Startet einen neuen Trace für den aktuellen Telefonanruf"""
        if not self.is_enabled:
            return DummyTrace()

        try:
            meta = {
                "caller_id": caller_id,
                "agent": "Lina (Job-Step)",
                "campaign": "Bihać Casting 16-20.11.",
                "language": "Bosnian (ijekavski)",
                **(metadata or {})
            }

            trace = self.client.trace(
                name="lina-voice-call",
                session_id=call_id,
                user_id=caller_id or "anonymous",
                tags=["voice-agent", "gemini-3.8-live", "job-step-recruiting"],
                metadata=meta
            )
            return trace
        except Exception as e:
            logger.error(f"Fehler beim Erstellen des Langfuse-Traces: {e}")
            return DummyTrace()

    def flush(self):
        """Sendet verbleibende Tracing-Daten asynchron an Langfuse"""
        if self.is_enabled:
            try:
                self.client.flush()
            except Exception as e:
                logger.error(f"Fehler bei Langfuse Flush: {e}")
