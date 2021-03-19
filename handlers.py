import asyncio
from aiohttp import web
import aiomysql
import db_connection
import cfg  # configure file
import json


async def couriers(request: web.Request):
    # VERB = 'POST'
    # URI = '/couriers'
    data = await request.json()

    queries = []
    try:
        for courier in data['data']:
            # queries.append(
            #     "INSERT INTO couriers (courier_id, courier_type) VALUES ('%d', '%s');" % (courier['courier_id'], courier['courier_type']))
            queries.append(
                ("INSERT INTO couriers (courier_id, courier_type) VALUES ('%s', %s);", (courier['courier_id'], courier['courier_type'])))
            for region in courier['regions']:
                queries.append(
                    ("INSERT INTO couriers_regions (courier_id, region) VALUES ('%s', %s)", (courier['courier_id'], region)))
            for wh in courier['working_hours']:
                ranges = wh.split('-')
                start = ranges[0]
                end = ranges[1]
                queries.append((
                               '''INSERT INTO couriers_working_hours (courier_id, time_range_start, time_range_stop) 
                               VALUES ('%s', STR_TO_DATE(%s, '%%H:%%i'), STR_TO_DATE(%s, '%%H:%%i'))''', (courier['courier_id'], start, end)))
    except KeyError:
        pass

    answer = await db_connection.execute_queries(queries)
    json_response = {'couriers': [{'id': x['courier_id']} for x in data['data']]}
    return web.json_response(json.dumps(json_response), status=201, reason='Created')
