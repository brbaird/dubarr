import asyncio

import httpx
from fuzzywuzzy import fuzz
from nicegui import events, ui

import config

sonarr_api_url = f'{config.host_url}/api/v3'
api = httpx.AsyncClient()
api.headers = {"X-Api-Key": config.api_key}
running_queries = []


def get_series_matches(query, series_list, thresh):
    """
    Returns a list of series that fuzzy-match the query.
    :param str query: The query.
    :param list series_list: List of dicts containing all series.
    :param int thresh: The threshold for fuzzy matching. The higher this is, the less will get matched.
    :return: List of series that matched the query.
    """
    return [x for x in series_list if fuzz.partial_ratio(query.lower(), x['title'].lower()) >= thresh]


async def is_dubbed(show):
    """Returns dub status for an entire show. Will return if a show is fully, partially, or not dubbed."""
    results = await api.get(f'{sonarr_api_url}/episodefile', params={'seriesId': show['id']})
    episodes = results.json()
    dub_status = []
    for episode in episodes:
        try:
            languages = episode['mediaInfo']['audioLanguages'].split(' / ')
        except KeyError:
            dub_status.append(False)
            continue
        dub_status.append(True if 'English' in languages else False)

    if not episodes:
        return 'none'
    if all(dub_status):
        return 'dubbed'
    elif not all(dub_status) and any(dub_status):
        return 'partial'
    else:
        return 'none'


dub_status_colors = {
    'dubbed': 'bg-green',
    'partial': 'bg-orange',
    'none': 'bg-red',
}


def content():
    """Creates the main page."""

    async def search(e: events.ValueChangeEventArguments) -> None:
        """Main searching function. Runs an async request to Sonarr while the user types."""
        global running_queries
        if running_queries:
            for query in running_queries:
                query.cancel()  # cancel the previous query; happens when you type fast
        search_field.classes('mt-2', remove='mt-24')  # move the search field up
        results.clear()

        # store the http coroutine in a task so we can cancel it later if needed
        series_query = asyncio.create_task(api.get(f'{sonarr_api_url}/series'))
        running_queries.append(series_query)
        response = await series_query
        if response.text == '':
            return

        with results:
            series = get_series_matches(e.value.lower(), response.json(), 75)
            # Filter to only anime
            if config.anime_only:
                series = [x for x in series if x['seriesType'] == 'anime']

            for show in series or []:  # iterate over the response data of the api
                image = [x for x in show['images'] if x['coverType'] == 'poster'][0]

                dubbed_query = asyncio.create_task(is_dubbed(show))
                running_queries.append(dubbed_query)
                dubbed = await dubbed_query

                color = dub_status_colors[dubbed]
                with ui.image(f'/image?path={image["url"]}').classes('w-36'):
                    ui.label(show['title']).classes(f'absolute-bottom text-subtitle2 text-center {color}')
        running_queries = []

    # create a search field which is initially focused and leaves space at the top
    search_field = ui.input(on_change=search) \
        .props('autofocus outlined rounded item-aligned input-class="ml-3"') \
        .classes('w-full self-center mt-24 transition-all text-base')
    results = ui.row() \
        .classes('flex self-center h-screen justify-center')
