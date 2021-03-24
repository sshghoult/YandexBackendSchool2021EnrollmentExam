import asyncio
from collections import deque
from aiohttp import web
import handlers
import logging
import cfg

app = web.Application()
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s %(message)s')

app.add_routes([web.post('/couriers', handlers.post_couriers), web.post('/orders', handlers.post_orders),
                web.patch(r'/couriers/{courier_id:\d+}', handlers.patch_couriers_id),
                web.post('/orders/complete', handlers.post_orders_complete)])

web.run_app(app)  # access_log=logging.getLogger('aiohttp.server')
