import httpx
from fastapi.responses import Response

import config

api = httpx.AsyncClient()
api.headers = {"X-Api-Key": config.api_key}


async def get_image(path):
    """
    Obtains image from Sonarr instance. Pass in the path to the image from the root URL.
    For example: if full URL is https://sonarr.example.com/api/MediaCover/39/poster.jpg,
    you would only pass in /MediaCover/39/poster.jpg.
    """
    result = await api.get(f'{config.host_url}/api{path}')
    return Response(content=result.content, media_type='image/jpeg')
