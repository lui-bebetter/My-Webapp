import asyncio 
from  aiohttp import web
import logging;logging.basicConfig(level=logging.INFO,format='%(filename)s\
    [line:%(lineno)d]%(levelname)s%(messages)s')

async def init(loop):
    app=web.Application(loop=loop)
    app.router.add_route('GET','/',home)
    srv=await app.create_server(app.make_handle(),'127.0.0.1',9000)
    logging.info('server started at http://127.0.0.1:9000...')
    return src

async def home(request):
    await asyncio.sleep(0.5)
    return web.Response(body='<h1>Awesome<h1>')

loop=asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

