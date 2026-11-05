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
from logger_config import setup_logging, get_logger, metrics

load_dotenv(".env")
if os.path.exists("env_config.txt"):
    load_dotenv("env_config.txt", override=True)
elif os.path.exists("env.txt"):
    load_dotenv("env.txt", override=True)

setup_logging()
logger = get_logger("LinaLocalTest")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VOICE_NAME = os.getenv("VOICE_NAME", "Aoede")
MODEL = "models/gemini-3.8-live"

if not GEMINI_API_KEY or GEMINI_API_KEY == "your_gemini_api_key_here":
    raise ValueError("Bitte tragen Sie Ihren echten GEMINI_API_KEY in die .env oder env_config.txt Datei ein!")

airtable_service = AirtableService()
mcp_bridge = MCPBridge()

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=GEMINI_API_KEY,
)
if hasattr(client, "_api_client") and hasattr(client._api_client, "_websocket_ssl_ctx"):
    client._api_client._websocket_ssl_ctx["ping_interval"] = None
    client._api_client._websocket_ssl_ctx["ping_timeout"] = None

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

    playback_queue = asyncio.Queue()
    is_speaking = False

    async def playback_worker():
        nonlocal is_speaking
        try:
            while True:
                chunk = await playback_queue.get()
                if chunk is None:
                    break
                await asyncio.to_thread(speaker_stream.write, chunk)
                playback_queue.task_done()
        except asyncio.CancelledError:
            pass

    async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
        logger.info("✨ Lokale Gemini Live Session aktiv.")

        playback_task = asyncio.create_task(playback_worker())

        async def mic_loop():
            nonlocal is_speaking
            while True:
                data = await asyncio.to_thread(mic_stream.read, CHUNK, exception_on_overflow=False)
                # Echo-Schutz: Wenn Lina über Laptop-Lautsprecher spricht, Mikrofon dämpfen
                # um Selbst-Unterbrechung (Acoustic Echo Barge-in) zu verhindern
                if is_speaking:
                    await asyncio.sleep(0.01)
                    continue

                await session.send_realtime_input(
                    audio=types.Blob(data=data, mime_type="audio/pcm;rate=16000")
                )

        async def speaker_loop():
            nonlocal is_speaking
            lina_has_spoken_turn = False

            async for response in session.receive():
                # Server Content (Audio & Live-Transkription)
                if server_content := response.server_content:
                    # User Transkription
                    if server_content.input_transcription and server_content.input_transcription.text:
                        print(f"\n🗣️ Vi: {server_content.input_transcription.text}")

                    # Lina Transkription
                    if server_content.output_transcription and server_content.output_transcription.text:
                        if not lina_has_spoken_turn:
                            print(f"\n🎙️ Lina: ", end="", flush=True)
                            lina_has_spoken_turn = True
                        print(server_content.output_transcription.text, end="", flush=True)

                    # Audio Playback
                    if model_turn := server_content.model_turn:
                        is_speaking = True
                        for part in model_turn.parts:
                            if inline_data := getattr(part, "inline_data", None):
                                await playback_queue.put(inline_data.data)

                    # Wenn Unterbrechung erkannt wurde
                    if server_content.interrupted:
                        logger.info("⚡ Unterbrechung erkannt.")
                        while not playback_queue.empty():
                            try:
                                playback_queue.get_nowait()
                                playback_queue.task_done()
                            except (asyncio.QueueEmpty, ValueError):
                                break
                        is_speaking = False
                        lina_has_spoken_turn = False

                    # Wenn Lina ihren Satz beendet hat
                    if server_content.turn_complete:
                        # Warte bis Audio fertig abgespielt wurde
                        await playback_queue.join()
                        is_speaking = False
                        lina_has_spoken_turn = False
                        print("\n🟢 Slušam vas... (Sprechen Sie jetzt)")

                # Tool Call Handling
                if response.tool_call is not None:
                    for fc in response.tool_call.function_calls:
                        logger.info(f"\n⚡ LINA RUFT TOOL AUF: {fc.name}")
                        print(f"\n📦 Airtable Datenpaket: {fc.args}")
                        
                        if fc.name == "sacuvaj_kandidata_u_airtable":
                            res = await airtable_service.save_or_update_candidate(fc.args)
                        else:
                            res = await mcp_bridge.execute_tool(fc.name, fc.args)

                        await session.send_tool_response(
                            function_responses=[
                                types.FunctionResponse(name=fc.name, id=fc.id, response={"result": res})
                            ]
                        )

        try:
            await asyncio.gather(mic_loop(), speaker_loop())
        finally:
            playback_task.cancel()


if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except KeyboardInterrupt:
        print("\nTest beendet.")
    except Exception as e:
        logger.exception(f"Unerwarteter Fehler in test_local: {e}")
        metrics.record_error("Fehler in test_local", exc=e)
        raise
