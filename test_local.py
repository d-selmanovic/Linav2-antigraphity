"""
Lokales Test-Skript für Lina (Job-Step)
Ermöglicht es Ihnen, den Agenten direkt über Ihr Mac-Mikrofon und Lautsprecher zu testen –
inklusive direkter Airtable-Speicherung, MCP und n8n-Webhook!
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

from google import genai
from google.genai import types

from prompts import LINA_SYSTEM_INSTRUCTION, AIRTABLE_TOOL_DECLARATION, N8N_TOOL_DECLARATION
from airtable_service import AirtableService
from mcp_bridge import MCPBridge

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("LinaLocalTest")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VOICE_NAME = os.getenv("VOICE_NAME", "Aoede")
MODEL = "models/gemini-3.8-live"

if not GEMINI_API_KEY:
    raise ValueError("Bitte tragen Sie Ihren GEMINI_API_KEY in die .env Datei ein!")

airtable_service = AirtableService()
mcp_bridge = MCPBridge()

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=GEMINI_API_KEY,
)

active_tools = [AIRTABLE_TOOL_DECLARATION, N8N_TOOL_DECLARATION]
mcp_tools = mcp_bridge.get_gemini_tool_declarations()
if mcp_tools:
    active_tools.extend(mcp_tools)

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

try:
    import pyaudio
except ImportError:
    pyaudio = None
    logger.warning("PyAudio ist nicht installiert. Installieren Sie es mit: pip install pyaudio")


async def run_test():
    if not pyaudio:
        print("Bitte zuerst 'pip install pyaudio' ausführen, um über das Mikrofon zu sprechen.")
        return

    p = pyaudio.PyAudio()
    
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE_IN = 16000
    RATE_OUT = 24000

    mic_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE_IN, input=True, frames_per_buffer=CHUNK)
    speaker_stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE_OUT, output=True)

    print("\n" + "="*55)
    print("🎙️ LINA (JOB-STEP) LOKALER TEST (AIRTABLE & MCP AKTIV)")
    print(f"Stimme: {VOICE_NAME} | Modell: {MODEL}")
    print("Sprechen Sie jetzt ins Mikrofon (z.B. 'Dobar dan!').")
    print("Drücken Sie Strg+C zum Beenden.")
    print("="*55 + "\n")

    async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
        
        async def mic_loop():
            while True:
                data = await asyncio.to_thread(mic_stream.read, CHUNK, exception_on_overflow=False)
                await session.send(input={"data": data, "mime_type": "audio/pcm"})

        async def speaker_loop():
            async for response in session.receive():
                # Tool Call Handling
                if response.tool_call is not None:
                    for fc in response.tool_call.function_calls:
                        logger.info(f"\n⚡ LINA RUFT TOOL AUF: {fc.name}")
                        print(f"📦 Datenpaket: {fc.args}")
                        
                        if fc.name == "sacuvaj_kandidata_u_airtable":
                            res = await airtable_service.save_or_update_candidate(fc.args)
                        else:
                            res = await mcp_bridge.execute_tool(fc.name, fc.args)

                        await session.send_tool_response(
                            function_responses=[
                                types.FunctionResponse(name=fc.name, id=fc.id, response={"result": res})
                            ]
                        )

                # Audio
                if server_content := response.server_content:
                    if model_turn := server_content.model_turn:
                        for part in model_turn.parts:
                            if inline_data := getattr(part, "inline_data", None):
                                await asyncio.to_thread(speaker_stream.write, inline_data.data)

        await asyncio.gather(mic_loop(), speaker_loop())


if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\nTest beendet.")
