import asyncio

import httpx
from fastapi.responses import Response

import config

_api = httpx.AsyncClient()
_api.headers = {"X-Api-Key": config.api_key}


class RunningQueries:
    """Utility class for keeping track of running queries"""

    def __init__(self):
        self.queries: list[asyncio.Task] = []

    @property
    def running(self) -> bool:
        """Returns True if there are running queries, False if not"""
        return bool(self.queries)

    async def create_task(self, coro):
        """Creates and runs a task. First it adds the task to the running queries."""
        task = asyncio.create_task(coro)
        self.queries.append(task)
        return await task

    def cancel(self):
        """Cancels all running queries"""
        for query in self.queries:
            query.cancel()

    def clear(self):
        """Clears the query list"""
        self.queries = []


class RunningSearch:
    """Utility class for a running search"""

    def __init__(self):
        self.search: asyncio.Task | None = None

    def rerun(self, coro):
        """Cancels running task and reruns it"""
        if self.search is None:
            self.search = asyncio.create_task(coro)
            return

        if not self.search.done():
            self.search.cancel()

        self.search = asyncio.create_task(coro)


async def get_image(path):
    """
    Obtains image from Sonarr instance. Pass in the path to the image from the root URL.
    For example: if full URL is https://sonarr.example.com/api/MediaCover/39/poster.jpg,
    you would only pass in /MediaCover/39/poster.jpg.
    """

    result = await _api.get(f'{config.host_url}/api{path}')
    return Response(content=result.content, media_type='image/jpeg')
