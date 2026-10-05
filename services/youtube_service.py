import re

from loguru import logger
from youtube_transcript_api import YouTubeTranscriptApi


class YouTubeError(Exception):
    pass


def extract_video_id(url: str) -> str:
    patterns = [r'(?:v=|/v/|youtu\.be/|/embed/|/shorts/)([A-Za-z0-9_-]{11})']
    for p in patterns:
        m = re.search(p, url)
        if m:
            return m.group(1)
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', url):
        return url
    raise YouTubeError('Не удалось распознать ID видео')


def _fetch_sync(video_id: str) -> str:
    '''Для youtube-transcript-api 0.6.2 — статические методы.'''
    errors = []

    # 1. Прямая попытка: get_transcript (работает в 0.6.2)
    try:
        data = YouTubeTranscriptApi.get_transcript(video_id, languages=['ru', 'en'])
        text = ' '.join(item.get('text', '') for item in data if isinstance(item, dict)).strip()
        if text:
            return text
    except Exception as e:
        errors.append(f'get_transcript: {e}')

    # 2. Fallback: список субтитров
    try:
        tlist = YouTubeTranscriptApi.list_transcripts(video_id)
        # пробуем сначала ручные, потом авто
        transcript = None
        try:
            transcript = tlist.find_transcript(['ru', 'en'])
        except Exception:
            for tr in tlist:
                transcript = tr
                break
        if transcript:
            fetched = transcript.fetch()
            text = ' '.join(item.get('text', '') for item in fetched if isinstance(item, dict)).strip()
            if text:
                return text
    except Exception as e:
        errors.append(f'list_transcripts: {e}')

    # 3. Fallback: любой доступный язык без указания
    try:
        data = YouTubeTranscriptApi.get_transcript(video_id)
        text = ' '.join(item.get('text', '') for item in data if isinstance(item, dict)).strip()
        if text:
            return text
    except Exception as e:
        errors.append(f'get_transcript (any lang): {e}')

    logger.error(f'YouTube: все попытки провалились: {errors}')
    raise YouTubeError('Субтитры недоступны: ' + '; '.join(errors)[:250])


async def get_youtube_transcript(url: str) -> tuple:
    video_id = extract_video_id(url)
    import asyncio
    loop = asyncio.get_running_loop()
    try:
        text = await loop.run_in_executor(None, _fetch_sync, video_id)
    except YouTubeError:
        raise
    except Exception as e:
        logger.exception(f'YouTube error: {e}')
        raise YouTubeError(str(e)[:200])
    if not text:
        raise YouTubeError('Транскрипт пустой')
    return video_id, text
