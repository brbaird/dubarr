from nicegui import ui, app

import image_api
import search_page


@app.get('/image')
async def get_image(path):
    return await image_api.get_image(path)


@ui.page('/')
def index_page():
    search_page.content()


ui.run()
