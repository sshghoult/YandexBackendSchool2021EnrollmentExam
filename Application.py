from aiohttp import web
import handlers
import logging
import cfg


def run():
    app = web.Application()
    logging.basicConfig(level=logging.DEBUG)

    app.add_routes([web.post('/couriers', handlers.post_couriers), web.post('/couriers/', handlers.post_couriers),
                    web.post('/orders', handlers.post_orders), web.post('/orders/', handlers.post_orders),
                    web.patch(r'/couriers/{courier_id:\d+}', handlers.patch_couriers_id),
                    web.patch(r'/couriers/{courier_id:\d+/}', handlers.patch_couriers_id),
                    web.post('/orders/complete', handlers.post_orders_complete),
                    web.post('/orders/complete/', handlers.post_orders_complete),
                    web.post('/orders/assign', handlers.post_orders_assign), web.post('/orders/assign/', handlers.post_orders_assign),

                    web.get('/', handlers.get_root), web.get(r'/couriers/{courier_id:\d+}', handlers.get_couriers_id)])

    web.run_app(app, port=8080, access_log=logging.getLogger('aiohttp.server'))

