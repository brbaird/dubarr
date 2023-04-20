import asyncio

import langcodes
from aiopyarr.exceptions import ArrException
from aiopyarr.sonarr_client import SonarrClient, SonarrSeries
from fuzzywuzzy import fuzz
from nicegui import events, ui

import config
from dubarr.utils import utils, series_utils as sutils
from . import drawers


def get_series_matches(query, series_list, thresh):
    """
    Returns a list of series that fuzzy-match the query.
    :param str query: The query.
    :param list series_list: List of dicts containing all series.
    :param int thresh: The threshold for fuzzy matching. The higher this is, the less will get matched.
    :return: List of series that matched the query.
    """
    return [x for x in series_list if fuzz.partial_ratio(query.lower(), x.title.lower()) >= thresh]


def get_status_color(status: sutils.LangStatus):
    lang_status_colors = {
        sutils.LangStatus.all: 'bg-green',
        sutils.LangStatus.some: 'bg-orange',
        sutils.LangStatus.none: 'bg-red',
    }
    return lang_status_colors[status]


def content(all_series_orig: list[SonarrSeries]):
    """Creates the main page."""
    rq = utils.RunningQueries()
    series_cache = {}  # Used to cache Series instances so that queries don't run on every search

    async def _search(e: events.ValueChangeEventArguments | None) -> None:
        """Main searching function. Runs an async request to Sonarr while the user types."""
        nonlocal rq, series_cache
        if rq.running:
            rq.cancel()
        results.clear()

        with results:
            all_series = all_series_orig.copy()
            # Filter results to search value
            if e is not None and e.value:
                all_series = get_series_matches(e.value.lower(), all_series, 75)
            # Filter to only anime
            if config.anime_only:
                all_series = [x for x in all_series if x.seriesType == 'anime']

            if not all_series:
                return

            # Sort all_series by date added to Sonarr. Will be reimplemented as a drawer item later
            all_series.sort(key=lambda x: x.added, reverse=True)

            for series in all_series:
                await asyncio.sleep(0)  # Very important, yield to the loop to allow for task cancelling
                image = [x for x in series.images if x.coverType == 'poster'][0]

                try:
                    s = series_cache[series.id]
                except KeyError:
                    async with SonarrClient(url=config.host_url, api_token=config.api_key, port=config.port) as client:
                        try:
                            s = await rq.create_task(sutils.get_series(client, series))
                            series_cache[series.id] = s
                        except ArrException:  # Hate this. Needs better solution
                            return

                if not s.episodes:  # No episodes, we can skip this series
                    continue

                with ui.dialog() as dialog, ui.card().classes('flex-nowrap items-stretch flex-auto'):
                    ui.label(series.title)
                    for season_num, season in sorted(s.seasons.items()):
                        season_disp_name = "Specials" if season_num == 0 else f'Season {season_num}'
                        with ui.expansion(season_disp_name) \
                                .classes(f'{get_status_color(season.get_lang_status(wanted_languages))}') \
                                .props('group=season'):  # Groups expansions together for accordian style

                            for ep in season.episodes:
                                ui.label(f'{ep.ep_info.episodeNumber}. {ep.ep_info.title}') \
                                    .classes(f'{get_status_color(ep.get_lang_status(wanted_languages))}')
                    ui.button('Close', on_click=dialog.close)

                color = get_status_color(s.get_lang_status(wanted_languages))
                with ui.image(f'/image?path={image.url}') \
                        .classes('w-36 hover:cursor-pointer') \
                        .on('click', dialog.open):
                    ui.label(series.title).classes(f'absolute-bottom text-subtitle2 text-center {color}')
        rq.clear()

    wanted_languages = [langcodes.Language.get('en')]

    # For some reason, we can't just ensure_future here. It needs to be delayed.
    ui.timer(interval=0.01, callback=lambda: asyncio.ensure_future(_search(None)), once=True)

    running_search = utils.RunningSearch()

    async def search(*args, **kwargs):
        running_search.rerun(_search(*args, **kwargs))

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
    drawers.content(wanted_languages, search, search_field)
