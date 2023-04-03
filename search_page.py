import asyncio

from aiopyarr.exceptions import ArrException
from aiopyarr.sonarr_client import SonarrClient
from fuzzywuzzy import fuzz
from nicegui import events, ui

import config
import series_utils as sutils

sonarr_api_url = f'{config.host_url}/api/v3'
running_queries = []


def get_series_matches(query, series_list, thresh):
    """
    Returns a list of series that fuzzy-match the query.
    :param str query: The query.
    :param list series_list: List of dicts containing all series.
    :param int thresh: The threshold for fuzzy matching. The higher this is, the less will get matched.
    :return: List of series that matched the query.
    """
    return [x for x in series_list if fuzz.partial_ratio(query.lower(), x.title.lower()) >= thresh]


def get_status_color(status: sutils.DubStatus):
    dub_status_colors = {
        sutils.DubStatus.dubbed: 'bg-green',
        sutils.DubStatus.partially_dubbed: 'bg-orange',
        sutils.DubStatus.not_dubbed: 'bg-red',
    }
    return dub_status_colors[status]


def content():
    """Creates the main page."""

    async def search(e: events.ValueChangeEventArguments | None) -> None:
        """Main searching function. Runs an async request to Sonarr while the user types."""
        global running_queries
        if running_queries:
            for query in running_queries:
                query.cancel()  # cancel the previous query; happens when you type fast
        results.clear()

        # store the http coroutine in a task so we can cancel it later if needed
        async with SonarrClient(url=config.host_url, api_token=config.api_key, port=config.port) as client:
            all_series_query = asyncio.create_task(client.async_get_series())
            running_queries.append(all_series_query)
            try:
                all_series = await all_series_query
            except ArrException:  # Hate this. Needs better solution
                return

        with results:
            # Filter results to search value
            if e is not None and e.value:
                all_series = get_series_matches(e.value.lower(), all_series, 75)
            # Filter to only anime
            if config.anime_only:
                all_series = [x for x in all_series if x.seriesType == 'anime']

            if not all_series:
                return

            for series in all_series:  # iterate over the response data of the api
                image = [x for x in series.images if x.coverType == 'poster'][0]

                async with SonarrClient(url=config.host_url, api_token=config.api_key, port=config.port) as client:
                    single_series_query = asyncio.create_task(sutils.get_series(client, series))
                    running_queries.append(single_series_query)
                    try:
                        s = await single_series_query
                    except ArrException:  # Hate this. Needs better solution
                        return

                with ui.dialog() as dialog, ui.card().classes('flex-nowrap items-stretch flex-auto'):
                    ui.label(series.title)
                    for season_num, season in sorted(s.seasons.items()):
                        season_disp_name = "Specials" if season_num == 0 else f'Season {season_num}'
                        with ui.expansion(season_disp_name) \
                                .classes(f'{get_status_color(season.dub_status)}') \
                                .props('group=season'):  # Groups expansions together for accordian style

                            for ep in season.episodes:
                                ui.label(f'{ep.ep_info.episodeNumber}. {ep.ep_info.title}') \
                                    .classes(f'{get_status_color(ep.dub_status)}')
                    ui.button('Close', on_click=dialog.close)

                color = get_status_color(s.dub_status)
                with ui.image(f'/image?path={image.url}') \
                        .classes('w-36 hover:cursor-pointer') \
                        .on('click', dialog.open):
                    ui.label(series.title).classes(f'absolute-bottom text-subtitle2 text-center {color}')
        running_queries = []

    # For some reason, we can't just ensure_future here. It needs to be delayed.
    ui.timer(interval=0.01, callback=lambda: asyncio.ensure_future(search(None)), once=True)

    # create a search field which is initially focused and leaves space at the top
    with ui.input(on_change=search, placeholder='Search for a show') \
            .props('autofocus outlined rounded item-aligned input-class="ml-3"') \
            .classes('md: w-full w-2/3 self-center mt-2 transition-all text-base') as search_field:

        # Need this in order to clear search field via button
        def clear_search_field():
            search_field.value = ''

        ui.icon('clear', color='grey-14').classes('h-screen self-center mr-2 text-4xl hover:cursor-pointer') \
            .on('click', clear_search_field)
    results = ui.row() \
        .classes('flex self-center justify-center')
