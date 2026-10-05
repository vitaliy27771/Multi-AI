from loguru import logger

from services.groq_client import GroqError, transcribe_audio_groq


class STTError(Exception):
    pass


async def transcribe_audio(audio_bytes: bytes, filename: str = "voice.ogg") -> str:
    try:
        return await transcribe_audio_groq(audio_bytes, filename=filename)
    except GroqError as e:
        logger.error(f"STT error: {e}")
        raise STTError(str(e))