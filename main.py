from nicegui import ui, app

import config
import image_api
import search_page

__version__ = 'v0.0.0'


@app.get('/image')
async def get_image(path):
    return await image_api.get_image(path)


@ui.page('/')
def index_page():
    search_page.content()


ui.run(title='Dubarr', dark=True, reload=config.reload)
