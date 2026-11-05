# Gemini 3.8 Live API WebSocket Protocol Reference

## 1. Connection Lifecycle
* Endpoint: `models/gemini-3.8-live`
* Library: `google-genai` >= 0.1.1 (`client.aio.live.connect`)
* Transport: Bidirectional WebSocket over TLS
* Modalities: `response_modalities=["AUDIO"]`

## 2. Event Payload Parsing
```python
async for response in session.receive():
    # 1. Content Events (Audio + Transcripts)
    if content := response.server_content:
        # User Speech Transcription:
        if content.input_transcription:
            user_text = content.input_transcription.text
        # Model Speech Transcription:
        if content.output_transcription:
            lina_text = content.output_transcription.text
        # Model Audio Stream:
        if content.model_turn:
            for part in content.model_turn.parts:
                if part.inline_data:
                    raw_audio = part.inline_data.data # 24kHz PCM
        # Interruption Signal (Barge-In):
        if content.interrupted:
            # Client must immediately flush local PBX buffer
            pass

    # 2. Function Calling Events
    if response.tool_call:
        for call in response.tool_call.function_calls:
            # Execute tool locally and reply with session.send_tool_response()
            pass
```

## 3. Rate Limits & Quotas
* Audio Input: $3.00 / 1M tokens (~$0.005/min)
* Audio Output: $12.00 / 1M tokens (~$0.018/min)
* Blended Voice Agent Cost: ~$0.011 - $0.015 / conversation minute
