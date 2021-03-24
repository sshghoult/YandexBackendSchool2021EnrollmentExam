import asyncio
from aiohttp import web
import db_connection
import cfg  # configure file
import json
import logging


async def post_couriers(request: web.Request):
    # VERB = 'POST'
    # URI = '/couriers'
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        raise web.HTTPBadRequest
        # case of invalid json

    all_valid, ids = await db_connection.post_couriers_execute_queries(data)
    if all_valid:
        json_response = {"couriers": [{'id': x} for x in ids]}
        return web.json_response(json.dumps(json_response), status=201, reason='Created')
    else:
        json_response = {'validation_error': {"couriers": [{'id': x} for x in ids]}}
        return web.json_response(json.dumps(json_response), status=400, reason='Bad Request')


async def post_orders(request: web.Request):
    # VERB = 'POST'
    # URI = '/orders'
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        raise web.HTTPBadRequest
    all_valid, ids = await db_connection.post_orders_execute_queries(data)
    if all_valid:
        json_response = {"orders": [{'id': x} for x in ids]}
        return web.json_response(json.dumps(json_response), status=201, reason='Created')
    else:
        json_response = {'validation_error': {"orders": [{'id': x} for x in ids]}}
        return web.json_response(json.dumps(json_response), status=400, reason='Bad Request')


async def post_orders_assign(request: web.Request):
    # VERB = 'POST'
    # URI = '/orders/assign'
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logging.error(msg='post_orders_assign: invalid json, raised 400')
        raise web.HTTPBadRequest

    all_valid, json_response = await db_connection.post_orders_assign_execute_queries(data)


async def patch_couriers_id(request: web.Request):
    logging.debug('patch_couriers_id: entered')
    # VERB = 'PATCH'
    # URI = r'/couriers/{courier_id: \d+}'
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logging.error(msg='patch_couriers_id: invalid json, raised 400')
        raise web.HTTPBadRequest

    required_data = {"courier_id", "courier_type", "regions", "working_hours"}
    if set(data.keys()) - required_data:
        logging.error(msg='patch_couriers_id: extra columns in json, raised 400')
        raise web.HTTPBadRequest
    # check if there are column names beyond the stated in the docs

    # in this case column validation is made here due to the lack of json to send back in case of 400
    # though for the sake of consistency i should think about moving it to the db_connection function
    # cour_id = data['id']
    cour_id = request.match_info.get('courier_id')
    try:
        int(cour_id)
    except ValueError:
        logging.debug(f'patch_couriers_id: courier_id is invalid, raised 400')
        raise web.HTTPBadRequest

    logging.debug(f'patch_couriers_id: courier_id is {cour_id}')

    all_valid, new_courier_data = await db_connection.patch_couriers_id_execute_queries(cour_id, data)
    if all_valid:
        logging.debug(msg='patch_couriers_id: request has been fulfilled, creating response')
        return web.json_response(json.dumps(new_courier_data), status=200)
    else:
        logging.debug(msg='patch_couriers_id: request is invalid, creating response')
        return web.Response(status=400)


async def post_orders_complete(request: web.Request):
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        logging.error(msg='post_orders_complete: invalid json, raised 400')
        raise web.HTTPBadRequest

    all_valid, resp_data = await db_connection.post_orders_complete_execute_queries(data)

    if all_valid:
        logging.info(msg='post_orders_complete:  request has been fulfilled, creating response')
        return web.json_response(json.dumps(resp_data), status=200)
    else:
        logging.error(msg='post_orders_complete: request is invalid, creating response')
        raise web.HTTPBadRequest

