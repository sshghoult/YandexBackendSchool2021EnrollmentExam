import asyncio
from aiohttp import web
import handlers
import cfg


app = web.Application()
app.add_routes([web.post('/couriers', handlers.couriers)])
web.run_app(app)