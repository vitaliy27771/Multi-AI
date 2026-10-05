import aiohttp
from loguru import logger

from config import settings

GROQ_CHAT_URL = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_AUDIO_URL = 'https://api.groq.com/openai/v1/audio/transcriptions'
TEXT_MODEL = 'openai/gpt-oss-120b'
WHISPER_MODEL = 'whisper-large-v3-turbo'


class GroqError(Exception):
    pass


async def _chat_completion(messages: list, temperature: float = 0.7) -> str:
    if not settings.groq_api_key:
        raise GroqError('GROQ_API_KEY не задан')
    headers = {
        'Authorization': f'Bearer {settings.groq_api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': TEXT_MODEL,
        'messages': messages,
        'temperature': temperature,
        'max_tokens': 2048,
    }
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(GROQ_CHAT_URL, headers=headers, json=payload) as resp:
            data = await resp.json()
            if resp.status != 200:
                logger.error(f'Groq error {resp.status}: {data}')
                raise GroqError(f'Groq {resp.status}')
            try:
                return data['choices'][0]['message']['content'].strip()
            except (KeyError, IndexError) as e:
                raise GroqError(f'parse: {e}')


async def generate_text_groq(prompt: str) -> str:
    messages = [
        {'role': 'system', 'content': 'Ты полезный ассистент. Отвечай на русском.'},
        {'role': 'user', 'content': prompt},
    ]
    return await _chat_completion(messages)


async def summarize_text_groq(text: str, max_words: int = 300) -> str:
    messages = [
        {'role': 'system', 'content': 'Делай выжимки на русском, по пунктам.'},
        {'role': 'user', 'content': f'Выжимка (до {max_words} слов):\n\n{text[:12000]}'},
    ]
    return await _chat_completion(messages, temperature=0.3)


async def transcribe_audio_groq(audio_bytes: bytes, filename: str = 'audio.ogg') -> str:
    if not settings.groq_api_key:
        raise GroqError('GROQ_API_KEY не задан')
    headers = {'Authorization': f'Bearer {settings.groq_api_key}'}
    form = aiohttp.FormData()
    form.add_field('file', audio_bytes, filename=filename, content_type='audio/ogg')
    form.add_field('model', WHISPER_MODEL)
    form.add_field('language', 'ru')
    form.add_field('response_format', 'text')
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(GROQ_AUDIO_URL, headers=headers, data=form) as resp:
            text = await resp.text()
            if resp.status != 200:
                raise GroqError(f'Whisper {resp.status}')
            return text.strip()
