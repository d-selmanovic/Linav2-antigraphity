import os
import json
import uuid
import time
import asyncio
import logging
from typing import Optional

import numpy as np
import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from dotenv import load_dotenv

from google import genai
from google.genai import types

from prompts import LINA_SYSTEM_INSTRUCTION, AIRTABLE_TOOL_DECLARATION, N8N_TOOL_DECLARATION
from airtable_service import AirtableService
from mcp_bridge import MCPBridge
from audio_recorder import CallRecorder
from telemetry import LinaTracer
from logger_config import get_logger, metrics, setup_logging

load_dotenv(".env")
if os.path.exists("env_config.txt"):
    load_dotenv("env_config.txt", override=True)
elif os.path.exists("env.txt"):
    load_dotenv("env.txt", override=True)

setup_logging()
logger = get_logger("LinaVoiceServer")

# Konfiguration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
VOICE_NAME = os.getenv("VOICE_NAME", "Aoede")
PBX_SAMPLE_RATE = int(os.getenv("PBX_SAMPLE_RATE", "8000"))
ENABLE_CALL_RECORDING = os.getenv("ENABLE_CALL_RECORDING", "true").lower() in ("true", "1", "yes")
RECORDINGS_DIR = os.getenv("RECORDINGS_DIR", "recordings")
MODEL = "models/gemini-3.8-live"

if not GEMINI_API_KEY:
    logger.warning("WARNUNG: GEMINI_API_KEY ist nicht in den Umgebungsvariablen gesetzt!")

# Initialisiere Services
airtable_service = AirtableService()
mcp_bridge = MCPBridge()
tracer = LinaTracer()

# Gemini Client
client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=GEMINI_API_KEY,
)
if hasattr(client, "_api_client") and hasattr(client._api_client, "_websocket_ssl_ctx"):
    client._api_client._websocket_ssl_ctx["ping_interval"] = None
    client._api_client._websocket_ssl_ctx["ping_timeout"] = None

# Kombiniere Tools: Airtable (Direkt), n8n (Webhook), MCP (Erweiterbar)
active_tools = [AIRTABLE_TOOL_DECLARATION, N8N_TOOL_DECLARATION]

# Füge dynamisch MCP-Tools hinzu, falls konfiguriert
mcp_tools = mcp_bridge.get_gemini_tool_declarations()
if mcp_tools:
    active_tools.extend(mcp_tools)

# Gemini Live Konfiguration mit nativer Audio-Transkription
CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
        )
    ),
    input_audio_transcription=types.AudioTranscriptionConfig(),
    output_audio_transcription=types.AudioTranscriptionConfig(),
    context_window_compression=types.ContextWindowCompressionConfig(
        trigger_tokens=104857,
        sliding_window=types.SlidingWindow(target_tokens=52428),
    ),
    system_instruction=types.Content(
        parts=[types.Part.from_text(text=LINA_SYSTEM_INSTRUCTION)],
        role="user",
    ),
    tools=[types.Tool(function_declarations=active_tools)]
)

app = FastAPI(title="Lina Voice Agent - PBX, Airtable, MCP, Recording & Langfuse")


def resample_audio(audio_bytes: bytes, orig_sr: int, target_sr: int) -> bytes:
    """Konvertiert 16-Bit PCM Audio zwischen Abtastraten (z. B. 8kHz PBX <-> 16kHz/24kHz Gemini)"""
    if orig_sr == target_sr or not audio_bytes:
        return audio_bytes
    
    audio_data = np.frombuffer(audio_bytes, dtype=np.int16)
    if len(audio_data) == 0:
        return b""
    
    num_target_samples = int(len(audio_data) * target_sr / orig_sr)
    if num_target_samples == 0:
        return b""
    
    resampled = np.interp(
        np.linspace(0, len(audio_data), num_target_samples, endpoint=False),
        np.arange(len(audio_data)),
        audio_data
    ).astype(np.int16)
    
    return resampled.tobytes()


async def execute_tool_call(name: str, args: dict) -> dict:
    """Führt Function Calls für Airtable, n8n oder MCP aus mit Fehler-Logging & Metriken"""
    logger.info(f"⚡ Ausführung von Tool: {name} mit Daten: {args}")
    try:
        # 1. Direkter Airtable Aufruf
        if name == "sacuvaj_kandidata_u_airtable":
            res = await airtable_service.save_or_update_candidate(args)
            metrics.record_tool_call(name, success=(res.get("status") == "success"))
            # Wenn n8n parallel aktiv ist, benachrichtige auch n8n
            if N8N_WEBHOOK_URL:
                asyncio.create_task(send_to_n8n(args))
            return res

        # 2. n8n Webhook
        elif name == "prosledi_kandidata_u_n8n":
            res = await send_to_n8n(args)
            metrics.record_tool_call(name, success=(res.get("status") == "success"))
            return res

        # 3. Beliebige zukünftige MCP-Tools
        else:
            res = await mcp_bridge.execute_tool(name, args)
            metrics.record_tool_call(name, success=True)
            return res
    except Exception as e:
        logger.exception(f"❌ Kritischer Fehler bei Tool-Ausführung {name}: {e}")
        metrics.record_tool_call(name, success=False)
        metrics.record_error(f"Tool {name} fehlgeschlagen", exc=e)
        return {"status": "error", "message": str(e)}


async def send_to_n8n(data: dict) -> dict:
    """Sendet Daten an n8n Webhook"""
    if not N8N_WEBHOOK_URL:
        return {"status": "skipped", "reason": "no_webhook_url"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            resp = await http_client.post(N8N_WEBHOOK_URL, json=data)
            return {"status": "success", "status_code": resp.status_code}
    except Exception as e:
        logger.exception(f"❌ Fehler bei n8n Webhook: {e}")
        metrics.record_error("n8n Webhook Fehler", exc=e)
        return {"status": "error", "message": str(e)}


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "agent": "Lina (Job-Step)",
        "model": MODEL,
        "voice": VOICE_NAME,
        "airtable_direct": bool(os.getenv("AIRTABLE_API_KEY")),
        "n8n_connected": bool(N8N_WEBHOOK_URL),
        "mcp_enabled": True,
        "call_recording_enabled": ENABLE_CALL_RECORDING,
        "langfuse_tracing_enabled": tracer.is_enabled,
        "active_calls": metrics.active_calls,
        "total_calls": metrics.total_calls,
        "total_errors": metrics.error_count
    }


@app.get("/metrics")
async def get_metrics():
    """Gibt detaillierte Server-, Anruf- und Tool-Metriken für Monitoring zurück"""
    return metrics.get_summary()


@app.get("/debug/errors")
async def get_recent_errors():
    """Gibt die letzten erfassten Fehler mit Zeitstempeln und Details zurück"""
    return {
        "total_errors": metrics.error_count,
        "recent_errors": metrics.recent_errors
    }


@app.websocket("/ws/pbx")
async def pbx_audio_stream(websocket: WebSocket):
    """
    WebSocket-Schnittstelle für Ihre PBX-Telefonanlage (z. B. FreeSWITCH / Asterisk).
    Empfängt Audio vom Anrufer, leitet es an Gemini Live weiter, transkribiert Sprache,
    zeichnet den Anruf auf und überträgt Tracing-Daten an Langfuse.
    """
    await websocket.accept()
    call_id = str(uuid.uuid4())
    caller_id = websocket.query_params.get("caller_id") or websocket.query_params.get("caller") or websocket.query_params.get("from") or ""
    logger.info(f"📞 PBX Anruf verbunden! Call-ID: {call_id} | Caller-ID: {caller_id or 'Unbekannt'}. Starte Gemini 3.8 Live Session...")
    metrics.record_call_start()
    call_has_error = False

    # Initialisiere Audio-Recorder und Langfuse-Trace
    recorder = CallRecorder(
        call_id=call_id,
        caller_id=caller_id,
        sample_rate=PBX_SAMPLE_RATE,
        output_dir=RECORDINGS_DIR,
        enabled=ENABLE_CALL_RECORDING
    )

    trace = tracer.start_call_trace(
        call_id=call_id,
        caller_id=caller_id,
        metadata={
            "pbx_sample_rate": PBX_SAMPLE_RATE,
            "recordings_dir": RECORDINGS_DIR,
            "voice": VOICE_NAME,
            "model": MODEL
        }
    )

    try:
        async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
            logger.info("✨ Gemini Live Session aktiv (Audio, Live-Transkription, Tracing)!")

            audio_to_pbx_queue = asyncio.Queue()

            async def receive_from_gemini():
                """Liest Audio, Transkriptionen und Funktionsaufrufe von Gemini Live"""
                try:
                    async for response in session.receive():
                        server_content = response.server_content
                        if server_content:
                            # A. Live-Transkription des Anrufers
                            if server_content.input_transcription and server_content.input_transcription.text:
                                user_text = server_content.input_transcription.text
                                logger.info(f"🗣️ [Anrufer {caller_id}]: {user_text}")
                                recorder.add_transcript_entry("caller", user_text)
                                trace.event(name="caller_speech", input=user_text)

                            # B. Live-Transkription von Lina
                            if server_content.output_transcription and server_content.output_transcription.text:
                                lina_text = server_content.output_transcription.text
                                logger.info(f"🎙️ [Lina]: {lina_text}")
                                recorder.add_transcript_entry("lina", lina_text)
                                trace.event(name="lina_speech", output=lina_text)

                            # C. Audio von Lina an PBX weiterleiten und aufzeichnen
                            if server_content.model_turn:
                                for part in server_content.model_turn.parts:
                                    if data := getattr(part, "inline_data", None):
                                        pbx_audio = resample_audio(data.data, 24000, PBX_SAMPLE_RATE)
                                        recorder.record_agent_audio(pbx_audio)
                                        await audio_to_pbx_queue.put(pbx_audio)

                            # D. Unterbrechung (Barge-in / Anrufer spricht dazwischen)
                            if server_content.interrupted:
                                logger.info("⚡ Anrufer hat unterbrochen (Barge-in)! Puffer wird geleert...")
                                while not audio_to_pbx_queue.empty():
                                    try:
                                        audio_to_pbx_queue.get_nowait()
                                    except asyncio.QueueEmpty:
                                        break
                                trace.event(name="barge_in_interrupted")

                        # 2. Behandle Function Calling (Airtable, n8n, MCP) mit Langfuse Span
                        if response.tool_call is not None:
                            for function_call in response.tool_call.function_calls:
                                call_id_tool = function_call.id
                                name = function_call.name
                                args = function_call.args

                                # Caller-ID automatisch ergänzen, falls in den Argumenten leer
                                if caller_id and not args.get("broj_telefona"):
                                    args["broj_telefona"] = caller_id

                                # Langfuse Tool Span
                                tool_span = trace.span(
                                    name=f"tool_call:{name}",
                                    input=args,
                                    metadata={"call_id": call_id, "caller_id": caller_id}
                                )

                                tool_result = await execute_tool_call(name, args)

                                tool_span.end(
                                    output=tool_result,
                                    level="DEFAULT" if tool_result.get("status") == "success" else "ERROR",
                                    status_message=str(tool_result.get("status"))
                                )

                                # Sende Tool-Ergebnis zurück an Gemini Live
                                await session.send_tool_response(
                                    function_responses=[
                                        types.FunctionResponse(
                                            name=name,
                                            id=call_id_tool,
                                            response={"result": tool_result}
                                        )
                                    ]
                                )

                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    logger.error(f"Fehler in receive_from_gemini: {e}")

            async def send_audio_to_pbx():
                """Sendet Linas Sprache über den WebSocket zurück an die PBX"""
                try:
                    while True:
                        audio_chunk = await audio_to_pbx_queue.get()
                        await websocket.send_bytes(audio_chunk)
                except (WebSocketDisconnect, asyncio.CancelledError):
                    pass
                except Exception as e:
                    logger.error(f"Fehler in send_audio_to_pbx: {e}")

            async def receive_audio_from_pbx():
                """Empfängt Sprache vom Anrufer (PBX), zeichnet sie auf und schickt sie an Gemini Live"""
                try:
                    while True:
                        message = await websocket.receive()
                        if "bytes" in message and message["bytes"]:
                            raw_audio = message["bytes"]
                            recorder.record_caller_audio(raw_audio)
                            gemini_audio = resample_audio(raw_audio, PBX_SAMPLE_RATE, 16000)
                            await session.send_realtime_input(
                                audio=types.Blob(data=gemini_audio, mime_type="audio/pcm;rate=16000")
                            )
                        elif "text" in message:
                            logger.info(f"PBX Signal empfangen: {message['text']}")
                except (WebSocketDisconnect, asyncio.CancelledError):
                    pass
                except Exception as e:
                    logger.error(f"Fehler in receive_audio_from_pbx: {e}")

            await asyncio.gather(
                receive_from_gemini(),
                send_audio_to_pbx(),
                receive_audio_from_pbx(),
            )

    except WebSocketDisconnect:
        logger.info(f"PBX Anruf {call_id} beendet.")
    except Exception as e:
        call_has_error = True
        logger.exception(f"❌ Unerwarteter Fehler während Anruf {call_id}: {e}")
        metrics.record_error(f"Call {call_id} failed", exc=e)
    finally:
        metrics.record_call_end(success=not call_has_error)
        # Finalisiere Audio-Aufzeichnung & Langfuse-Trace
        wav_path = recorder.finalize()
        trace.update(
            output={
                "status": "error" if call_has_error else "call_ended",
                "recording_wav": wav_path,
                "turns_count": len(recorder.transcript)
            }
        )
        tracer.flush()


@app.get("/")
async def root():
    return HTMLResponse("""
    <html>
        <head><title>Lina Voice Agent Server</title></head>
        <body style="font-family: Arial; padding: 40px; background: #f4f6f8;">
            <h1>🎙️ Lina Voice Agent Server (Job-Step)</h1>
            <p>Status: <span style="color: green; font-weight: bold;">ONLINE</span></p>
            <ul>
                <li><b>Engine:</b> Google Gemini 3.8 Live (models/gemini-3.8-live)</li>
                <li><b>PBX WebSocket:</b> <code>/ws/pbx</code></li>
                <li><b>Native Transkription:</b> Aktiv (Caller + Agent)</li>
                <li><b>Audio-Aufnahme:</b> Aktiv (WAV in /recordings)</li>
                <li><b>Observability:</b> Langfuse Tracing</li>
                <li><b>Health Check:</b> <a href="/health">/health</a></li>
            </ul>
        </body>
    </html>
    """)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🚀 Starte Lina PBX Voice Server auf {host}:{port}...")
    uvicorn.run("server:app", host=host, port=port, reload=False)
