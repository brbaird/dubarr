import asyncio

import langcodes
from nicegui import events, ui

possible_languages = [langcodes.Language.get('en'), langcodes.Language.get('ja')]
running_search = None


def content(wanted_languages: list[langcodes.Language], search_func, search_field: ui.input):
    with ui.header(elevated=True).style('background-color: #3874c8').classes('items-center justify-between'):
        ui.button(on_click=lambda: left_drawer.toggle()).props('flat color=white icon=menu')

    with ui.left_drawer(top_corner=False, bottom_corner=True) as left_drawer:

        # Terrible hack to update results. Definitely needs to be revisited
        async def update_langs(e):
            global running_search
            lang = language_checkboxes[e.sender]
            if lang in wanted_languages and not e.value:
                wanted_languages.remove(lang)
            else:
                wanted_languages.append(lang)

            val = search_field.value
            if running_search:
                running_search.cancel()
            running_search = asyncio.create_task(search_func(events.ValueChangeEventArguments(None, None, val)))
            await running_search
            running_search = None

        language_checkboxes = {}
        for lang in possible_languages:
            val = lang in wanted_languages
            cb = ui.checkbox(lang.display_name(), on_change=update_langs, value=val)
            language_checkboxes[cb] = lang
