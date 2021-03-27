from aiohttp import web
import db_connection
import cfg  # configure file
import json
import logging


async def post_couriers(request: web.Request):
    """
    Handler for "POST /couriers" request. Registers received couriers. See the docs for the complete description.
    aiohttp-level communication is done here, while the actual communication with the database is done in associated db_connection function
    :param request: HTTP-request passed by aiohttp
    :return: Response derived from web.StreamResponse
    """
    logging.info(f'post_couriers: request={request}; entered')
    # VERB = 'POST'
    # URI = '/couriers'
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logging.info(f'post_couriers: request={request}; invalid json, raised 400')
        raise web.HTTPBadRequest
    if type(data) is not dict or set(data.keys()) != {'data'}:
        logging.info(f'post_couriers: request={request}; invalid json, raised 400')
        raise web.HTTPBadRequest

    all_valid, ids = await db_connection.post_couriers_execute_queries(data)
    if all_valid:
        logging.info(f'post_couriers: request={request}; request is valid and fulfilled, creating ok response')
        json_response = {"couriers": [{'id': x} for x in ids]}
        return web.json_response(json.dumps(json_response), status=201, reason='Created')
    else:
        logging.info(f'post_couriers: request={request}; validation error occurred, creating validation_error response')
        json_response = {'validation_error': {"couriers": [{'id': x} for x in ids]}}
        return web.json_response(json.dumps(json_response), status=400, reason='Bad Request')


async def patch_couriers_id(request: web.Request):
    """
    Handler for "PATCH /couriers/{courier_id}" request. Changes data about courier with associated courier_id.
    See the docs for the complete description.
    aiohttp-level communication is done here, while the actual communication with the database is done in associated db_connection function
    :param request: HTTP-request passed by aiohttp
    :return: Response derived from web.StreamResponse
    """
    logging.info(f'patch_couriers_id: request={request}; entered')
    # VERB = 'PATCH'
    # URI = r'/couriers/{courier_id: \d+}'
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logging.info(msg=f'patch_couriers_id: request={request}; invalid json, raised 400')
        raise web.HTTPBadRequest

    required_data = {"courier_type", "regions", "working_hours"}
    if set(data.keys()) - required_data:
        logging.info(msg=f'patch_couriers_id: request={request}; extra columns in json, raised 400')
        raise web.HTTPBadRequest
    # check if there are column names beyond the stated in the docs

    cour_id = request.match_info.get('courier_id')

    logging.debug(f'patch_couriers_id: request={request}; courier_id is {cour_id}')

    all_valid, new_courier_data = await db_connection.patch_couriers_id_execute_queries(cour_id, data)
    if all_valid:
        logging.info(msg=f'patch_couriers_id: request={request}; request has been fulfilled, creating response')
        return web.json_response(json.dumps(new_courier_data), status=200)
    else:
        logging.info(msg=f'patch_couriers_id: request={request}; request is invalid, creating response')
        return web.Response(status=400)


async def post_orders(request: web.Request):
    """
    Handler for "POST /orders" request. Registers received couriers.
    See the docs for the complete description.
    aiohttp-level communication is done here, while the actual communication with the database is done in associated db_connection function
    :param request: HTTP-request passed by aiohttp
    :return: Response derived from web.StreamResponse
    """
    logging.info(f'post_orders: request={request}; entered')
    # VERB = 'POST'
    # URI = '/orders'
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logging.info(f'post_orders: request={request}; invalid json, raising 400')
        raise web.HTTPBadRequest
    if type(data) is not dict or set(data.keys()) != {'data'}:
        logging.info(f'post_orders: request={request}; invalid json, raised 400')
        raise web.HTTPBadRequest

    all_valid, ids = await db_connection.post_orders_execute_queries(data)
    if all_valid:
        logging.info(f'post_orders: request={request}; request is valid and fulfilled, creating ok response')
        json_response = {"orders": [{'id': x} for x in ids]}
        return web.json_response(json.dumps(json_response), status=201, reason='Created')
    else:
        logging.info(f'post_orders: request={request}; validation error occurred, creating validation_error response')
        json_response = {'validation_error': {"orders": [{'id': x} for x in ids]}}
        return web.json_response(json.dumps(json_response), status=400, reason='Bad Request')


async def post_orders_assign(request: web.Request):
    """
    Handler for "POST /orders/assign" request. Assigns all available and appropriate orders to the courier to be delivered.
    See the docs for the complete description.
    aiohttp-level communication is done here, while the actual communication with the database is done in associated db_connection function
    :param request: HTTP-request passed by aiohttp
    :return: Response derived from web.StreamResponse
    """
    logging.info(f'post_orders_assign: request={request}; entered')
    # VERB = 'POST'
    # URI = '/orders/assign'
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logging.info(f'post_orders_assign: request={request}; invalid json, raised 400')
        raise web.HTTPBadRequest

    if set(data.keys()) != {'courier_id'} or type(data['courier_id']) is not int:
        logging.info(f'post_orders_assign: request={request}; invalid json, raising 400')
        raise web.HTTPBadRequest

    all_valid, json_response = await db_connection.post_orders_assign_execute_queries(data)

    if all_valid:
        logging.info(f'post_orders_assign: request={request}; request is valid and fulfilled, creating OK response')
        return web.json_response(json.dumps(json_response), status=200)
    else:
        logging.info(f'post_orders_assign: request={request}; validation error occurred, raising 400')
        raise web.HTTPBadRequest  #


async def post_orders_complete(request: web.Request):
    """
    Handler for "POST /orders/complete" request. Marks passed orders as completed.
    See the docs for the complete description.
    aiohttp-level communication is done here, while the actual communication with the database is done in associated db_connection function
    :param request: HTTP-request passed by aiohttp
    :return: Response derived from web.StreamResponse
    """
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logging.error(msg=f'post_orders_complete: request={request} invalid json, raised 400')
        raise web.HTTPBadRequest

    if type(data) is not dict or set(data.keys()) != {"courier_id", "order_id", "complete_time"}:
        logging.info(f'post_orders_complete: request={request}; invalid json, raised 400')
        raise web.HTTPBadRequest

    all_valid, resp_data = await db_connection.post_orders_complete_execute_queries(data)

    if all_valid:
        logging.info(msg=f'post_orders_complete: request={request};  request has been fulfilled, creating response')
        return web.json_response(json.dumps(resp_data), status=200)
    else:
        logging.error(msg=f'post_orders_complete: request={request}; request is invalid, creating response')
        raise web.HTTPBadRequest


async def get_root(request: web.Request):
    return web.Response(status=200, text='Hello, I\'m alive! Please, don\'t kill me. At least put out the fire afterwards.')


async def get_couriers_id(request: web.Request):
    cour_id = request.match_info.get('courier_id')

    all_valid, data = await db_connection.get_couriers_id_execute_queries(cour_id)
    if all_valid:
        return web.json_response(json.dumps(data), status=200)
    else:
        raise web.HTTPBadRequest
