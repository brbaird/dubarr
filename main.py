from aiopyarr.exceptions import ArrException
from aiopyarr.sonarr_client import SonarrClient
from nicegui import ui, app

import config
from dubarr.pages import search_page
from dubarr.utils import utils

__version__ = 'v0.0.7'


@app.get('/image')
async def get_image(path):
    return await utils.get_image(path)


@ui.page('/')
async def index_page():
    # store the http coroutine in a task, so we can cancel it later if needed
    async with SonarrClient(url=config.host_url, api_token=config.api_key, port=config.port) as client:
        try:
            all_series = await client.async_get_series()
        except ArrException:  # Hate this. Needs better solution
            return

    search_page.content(all_series)


ui.run(title='Dubarr', dark=True, reload=config.reload)
