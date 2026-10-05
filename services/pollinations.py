import asyncio
import base64
import urllib.parse

import aiohttp
from loguru import logger

from config import settings

HORDE_URL = 'https://stablehorde.net/api/v2/generate/async'
HORDE_STATUS = 'https://stablehorde.net/api/v2/generate/status/{job_id}'


class ImageGenError(Exception):
    pass


async def translate_to_english(text: str) -> str:
    if not settings.groq_api_key:
        return text
    if all(ord(c) < 128 for c in text):
        return text
    url = 'https://api.groq.com/openai/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {settings.groq_api_key}',
        'Content-Type': 'application/json',
    }
    payload = {
        'model': 'openai/gpt-oss-120b',
        'messages': [
            {'role': 'system', 'content': 'Translate user text to English for an image prompt. Output ONLY translation, no quotes.'},
            {'role': 'user', 'content': text},
        ],
        'temperature': 0.2,
        'max_tokens': 200,
    }
    try:
        timeout = aiohttp.ClientTimeout(total=15)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, headers=headers, json=payload) as resp:
                if resp.status != 200:
                    return text
                data = await resp.json()
                return data['choices'][0]['message']['content'].strip().strip('"').strip("'")
    except Exception as e:
        logger.warning(f'Translation failed: {e}')
        return text


async def generate_image(prompt: str) -> bytes:
    if not settings.horde_api_key:
        raise ImageGenError('HORDE_API_KEY не задан в .env')

    en_prompt = await translate_to_english(prompt)
    logger.info(f'Horde: ru={prompt!r} -> en={en_prompt!r}')

    headers = {
        'Content-Type': 'application/json',
        'apikey': settings.horde_api_key,
        'Client-Agent': 'neuro-bot:1.0:github.com/neurobot',
    }
    payload = {
        'prompt': f'{en_prompt} ### blurry, low quality, distorted, ugly, bad anatomy',
        'params': {
    	    'width': 384,
            'height': 384,
            'steps': 15,
            'cfg_scale': 7,
            'sampler_name': 'k_euler_a',
            'n': 1,
            'karras': True,
    },
        'nsfw': False,
        'censor_nsfw': True,
        'trusted_workers': False,
        'slow_workers': True,
        'models': ['stable_diffusion'],
    }

    timeout = aiohttp.ClientTimeout(total=300)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(HORDE_URL, headers=headers, json=payload) as resp:
            data = await resp.json()
            if resp.status == 401:
                raise ImageGenError('Horde: неверный API-ключ (401)')
            if resp.status == 403:
                raise ImageGenError(f'Horde 403: {data.get("message", "")}')
            if resp.status not in (200, 202):
                raise ImageGenError(f'Horde {resp.status}: {str(data)[:200]}')
            job_id = data.get('id')
            if not job_id:
                raise ImageGenError(f'Нет id: {data}')
            logger.info(f'Horde job={job_id}')

        for attempt in range(90):
            await asyncio.sleep(2)
            url = HORDE_STATUS.format(job_id=job_id)
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    continue
                data = await resp.json()
                if data.get('done'):
                    gens = data.get('generations') or []
                    if not gens:
                        raise ImageGenError('Horde: пусто')
                    img_url = gens[0].get('img')
                    async with session.get(img_url) as img_resp:
                        if img_resp.status != 200:
                            raise ImageGenError(f'Download {img_resp.status}')
                        return await img_resp.read()
                elif data.get('faulted'):
                    raise ImageGenError('Horde: faulted')
                else:
                    if attempt % 5 == 0:
                        logger.info(f'Horde: queue={data.get("queue_position", "?")}, wait={data.get("wait_time", 0)}s')
        raise ImageGenError('Horde: timeout 180 сек')


async def generate_image_pollinations(prompt: str, width: int = 1024, height: int = 1024) -> bytes:
    return await generate_image(prompt)


async def generate_image_hf(prompt: str) -> bytes:
    return await generate_image(prompt)
