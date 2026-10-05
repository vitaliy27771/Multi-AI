import io

import edge_tts
from loguru import logger

DEFAULT_VOICE = "ru-RU-SvetlanaNeural"


class TTSError(Exception):
    pass


async def synthesize_speech(text: str, voice: str = DEFAULT_VOICE) -> bytes:
    if not text.strip():
        raise TTSError("Пустой текст")

    text = text[:3000]
    try:
        communicate = edge_tts.Communicate(text=text, voice=voice)
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])
        data = buffer.getvalue()
        if not data:
            raise TTSError("Пустой аудиопоток")
        return data
    except Exception as e:
        logger.exception(f"TTS error: {e}")
        raise TTSError(str(e))