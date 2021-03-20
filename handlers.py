import asyncio
from aiohttp import web
import aiomysql
import db_connection
import cfg  # configure file
import json


async def post_couriers(request: web.Request):
    # VERB = 'POST'
    # URI = '/couriers'
    try:
        data = await request.json()
    except json.decoder.JSONDecodeError:
        raise web.HTTPBadRequest
        # case for invalid json

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
