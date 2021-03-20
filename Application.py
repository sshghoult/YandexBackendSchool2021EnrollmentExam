import asyncio
from aiohttp import web
import handlers
import cfg


app = web.Application()
app.add_routes([web.post('/couriers', handlers.post_couriers), web.post('/orders', handlers.post_orders)])
web.run_app(app)