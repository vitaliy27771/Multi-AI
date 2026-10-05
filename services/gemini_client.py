import aiohttp
from loguru import logger

from config import settings

GEMINI_URL = (
    'https://generativelanguage.googleapis.com/v1beta/models/'
    'gemini-3.8-flash:generateContent'
)


class GeminiError(Exception):
    pass


async def generate_text_gemini(prompt: str) -> str:
    if not settings.gemini_api_key:
        raise GeminiError('GEMINI_API_KEY не задан')
    url = f'{GEMINI_URL}?key={settings.gemini_api_key}'
    payload = {
        'contents': [{'role': 'user', 'parts': [{'text': prompt}]}],
        'generationConfig': {'temperature': 0.7, 'maxOutputTokens': 2048},
    }
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(url, json=payload) as resp:
            data = await resp.json()
            if resp.status != 200:
                logger.error(f'Gemini error {resp.status}: {data}')
                raise GeminiError(f'Gemini {resp.status}')
            try:
                cands = data.get('candidates') or []
                parts = cands[0]['content']['parts']
                return ''.join(p.get('text', '') for p in parts).strip()
            except (KeyError, IndexError) as e:
                raise GeminiError(f'parse: {e}')
