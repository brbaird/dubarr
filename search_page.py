import asyncio
from typing import Optional

import httpx
from fuzzywuzzy import fuzz
from nicegui import events, ui

import config

api = httpx.AsyncClient()
api.headers = {"X-Api-Key": config.api_key}
running_query: Optional[asyncio.Task] = None


def get_series_matches(query, series_list, thresh):
    """
    Returns a list of series that fuzzy-match the query.
    :param str query: The query.
    :param list series_list: List of dicts containing all series.
    :param int thresh: The threshold for fuzzy matching. The higher this is, the less will get matched.
    :return: List of series that matched the query.
    """
    return [x for x in series_list if fuzz.partial_ratio(query.lower(), x['title'].lower()) >= thresh]


def content():
    """Creates the main page."""

    async def search(e: events.ValueChangeEventArguments) -> None:
        """Main searching function. Runs an async request to Sonarr while the user types."""
        global running_query
        if running_query:
            running_query.cancel()  # cancel the previous query; happens when you type fast
        search_field.classes('mt-2', remove='mt-24')  # move the search field up
        results.clear()

        # store the http coroutine in a task so we can cancel it later if needed
        running_query = asyncio.create_task(api.get(f'{config.host_url}/api/v3/series'))
        response = await running_query
        if response.text == '':
            return

        with results:
            series = get_series_matches(e.value.lower(), response.json(), 75)
            # Filter to only anime
            if config.anime_only:
                series = [x for x in series if x['seriesType'] == 'anime']

            for show in series or []:  # iterate over the response data of the api
                image = [x for x in show['images'] if x['coverType'] == 'poster'][0]
                with ui.image(f'/image?path={image["url"]}').classes('w-36'):
                    ui.label(show['title']).classes('absolute-bottom text-subtitle2 text-center')
        running_query = None

    # create a search field which is initially focused and leaves space at the top
    search_field = ui.input(on_change=search) \
        .props('autofocus outlined rounded item-aligned input-class="ml-3"') \
        .classes('w-full self-center mt-24 transition-all text-base')
    results = ui.row() \
        .classes('flex self-center h-screen justify-center')
