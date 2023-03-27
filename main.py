from nicegui import ui

import search_page


@ui.page('/')
def index_page():
    search_page.content()


ui.run()
