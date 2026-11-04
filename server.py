import os
import json
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

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LinaVoiceServer")

# Konfiguration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL")
VOICE_NAME = os.getenv("VOICE_NAME", "Aoede")
PBX_SAMPLE_RATE = int(os.getenv("PBX_SAMPLE_RATE", "8000"))
MODEL = "models/gemini-3.8-live"

if not GEMINI_API_KEY:
    logger.warning("WARNUNG: GEMINI_API_KEY ist nicht in den Umgebungsvariablen gesetzt!")

# Initialisiere Services
airtable_service = AirtableService()
mcp_bridge = MCPBridge()

# Gemini Client
client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=GEMINI_API_KEY,
)

# Kombiniere Tools: Airtable (Direkt), n8n (Webhook), MCP (Erweiterbar)
active_tools = [AIRTABLE_TOOL_DECLARATION, N8N_TOOL_DECLARATION]

# Füge dynamisch MCP-Tools hinzu, falls konfiguriert
mcp_tools = mcp_bridge.get_gemini_tool_declarations()
if mcp_tools:
    active_tools.extend(mcp_tools)

# Gemini Live Konfiguration
CONFIG = types.LiveConnectConfig(
    response_modalities=["AUDIO"],
    speech_config=types.SpeechConfig(
        voice_config=types.VoiceConfig(
            prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
        )
    ),
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

app = FastAPI(title="Lina Voice Agent - PBX, Airtable & MCP")


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
    """Führt Function Calls für Airtable, n8n oder MCP aus"""
    logger.info(f"⚡ Ausführung von Tool: {name} mit Daten: {args}")

    # 1. Direkter Airtable Aufruf
    if name == "sacuvaj_kandidata_u_airtable":
        res = await airtable_service.save_or_update_candidate(args)
        # Wenn n8n parallel aktiv ist, benachrichtige auch n8n
        if N8N_WEBHOOK_URL:
            asyncio.create_task(send_to_n8n(args))
        return res

    # 2. n8n Webhook
    elif name == "prosledi_kandidata_u_n8n":
        return await send_to_n8n(args)

    # 3. Beliebige zukünftige MCP-Tools
    else:
        return await mcp_bridge.execute_tool(name, args)


async def send_to_n8n(data: dict) -> dict:
    """Sendet Daten an n8n Webhook"""
    if not N8N_WEBHOOK_URL:
        return {"status": "skipped", "reason": "no_webhook_url"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as http_client:
            resp = await http_client.post(N8N_WEBHOOK_URL, json=data)
            return {"status": "success", "status_code": resp.status_code}
    except Exception as e:
        logger.error(f"Fehler bei n8n Webhook: {e}")
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
        "mcp_enabled": True
    }


@app.websocket("/ws/pbx")
async def pbx_audio_stream(websocket: WebSocket):
    """
    WebSocket-Schnittstelle für Ihre PBX-Telefonanlage (z. B. FreeSWITCH / Asterisk).
    Empfängt Audio vom Anrufer, leitet es an Gemini Live weiter und sendet Linas Sprache zurück.
    """
    await websocket.accept()
    caller_id = websocket.query_params.get("caller_id") or websocket.query_params.get("caller") or websocket.query_params.get("from") or ""
    logger.info(f"PBX Anruf verbunden! Caller-ID: {caller_id or 'Unbekannt'}. Starte Gemini 3.8 Live Session...")

    try:
        async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
            logger.info("Gemini Live Session aktiv mit Airtable & MCP!")

            audio_to_pbx_queue = asyncio.Queue()

            async def receive_from_gemini():
                """Liest Audio und Funktionsaufrufe von Gemini Live"""
                try:
                    async for response in session.receive():
                        # 1. Behandle Function Calling (Airtable, n8n, MCP)
                        if response.tool_call is not None:
                            for function_call in response.tool_call.function_calls:
                                call_id = function_call.id
                                name = function_call.name
                                args = function_call.args

                                # Caller-ID automatisch ergänzen, falls in den Argumenten leer
                                if caller_id and not args.get("broj_telefona"):
                                    args["broj_telefona"] = caller_id

                                # Führe Tool aus
                                tool_result = await execute_tool_call(name, args)

                                # Sende Tool-Ergebnis zurück an Gemini Live
                                await session.send_tool_response(
                                    function_responses=[
                                        types.FunctionResponse(
                                            name=name,
                                            id=call_id,
                                            response={"result": tool_result}
                                        )
                                    ]
                                )

                        # 2. Behandle Sprache von Lina (Audio-Out)
                        server_content = response.server_content
                        if server_content and server_content.model_turn:
                            for part in server_content.model_turn.parts:
                                if data := getattr(part, "inline_data", None):
                                    pbx_audio = resample_audio(data.data, 24000, PBX_SAMPLE_RATE)
                                    await audio_to_pbx_queue.put(pbx_audio)

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
                """Empfängt Sprache vom Anrufer (PBX) und schickt sie an Gemini Live"""
                try:
                    while True:
                        message = await websocket.receive()
                        if "bytes" in message and message["bytes"]:
                            gemini_audio = resample_audio(message["bytes"], PBX_SAMPLE_RATE, 16000)
                            await session.send(input={"data": gemini_audio, "mime_type": "audio/pcm"})
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
        logger.info("PBX Anruf beendet.")
    except Exception as e:
        logger.error(f"Fehler während des Anrufs: {e}")


@app.get("/")
async def browser_test_ui():
    html_content = """
    <!DOCTYPE html>
    <html lang="de">
    <head>
        <meta charset="UTF-8">
        <title>Lina (Job-Step) - PBX, Airtable & MCP Server</title>
        <style>
            body { font-family: -apple-system, sans-serif; background: #121212; color: #fff; text-align: center; padding: 40px; }
            .card { background: #1e1e1e; padding: 30px; border-radius: 12px; max-width: 650px; margin: 0 auto; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
            h1 { color: #4285f4; }
            .badge { display: inline-block; padding: 6px 12px; border-radius: 20px; background: #2d3748; margin: 5px; font-size: 14px; }
            .active { background: #0f9d58; }
            p { color: #a0aec0; line-height: 1.6; }
            code { background: #2d3748; padding: 3px 8px; border-radius: 4px; color: #63b3ed; }
        </style>
    </head>
    <body>
        <div class="card">
            <h1>Lina - Job-Step Voice Server</h1>
            <p>Ihr Gemini 3.8 Live Server ist bereit für Telefonie, Airtable und MCP!</p>
            <div>
                <span class="badge active">PBX: Bereit</span>
                <span class="badge active">Airtable: Direkt angebunden</span>
                <span class="badge active">MCP: Aktiv</span>
                <span class="badge">Stimme: Aoede</span>
            </div>
            <hr style="border: 0; border-top: 1px solid #333; margin: 25px 0;">
            <p><strong>PBX WebSocket-Endpunkt:</strong><br><code>ws://&lt;DEINE-SERVER-IP&gt;:8000/ws/pbx</code></p>
            <p>Lina nimmt Anrufe entgegen, führt das Interview auf Bosnisch und schreibt die Daten direkt in Ihre Airtable-Tabelle <strong>Prijave (test)</strong>.</p>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("server:app", host=host, port=port, reload=True)
