import asyncio
import aiomysql
from aiomysql import DictCursor  # SELECT`s result will be presented in dicts
import cfg  # configure file
from typing import List, Tuple, Iterable, Dict  # type hints
import logging
import re


# TODO: read about pools of connections and use it instead
# TODO: de-hardcode passwords
# TODO: add logging, otherwise you`ll die trying to debug everything

async def post_couriers_execute_queries(json_request) -> (bool, List[int]):
    conn = await aiomysql.connect(host='localhost', port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=DictCursor, autocommit=False)
    cur = await conn.cursor()
    validation_error = []
    ok = []
    # every step of range is a new element with courier data, outer cycle is outside of try/except,
    # so one invalid element won`t stop others from being processed
    required_data = {"courier_id", "courier_type", "regions", "working_hours"}

    # TODO: There might be corrupted json_request data, prevent KeyError here
    for courier in json_request['data']:
        await conn.begin()
        if set(courier.keys()) != required_data:  # validate keys of the dict with info about courier
            validation_error.append(courier['courier_id'])
            continue
        try:
            await cur.execute("INSERT INTO couriers (courier_id, courier_type) VALUES "
                              "('%s', %s);", (courier['courier_id'], courier['courier_type']))
            for region in courier['regions']:
                await cur.execute("INSERT INTO couriers_regions (courier_id, region) VALUES ('%s', %s)", (courier['courier_id'], region))
            for wh in courier['working_hours']:
                ranges = wh.split('-')
                start = ranges[0]
                end = ranges[1]
                await cur.execute('''INSERT INTO couriers_working_hours (courier_id, time_range_start, time_range_stop)
                    VALUES ('%s', STR_TO_DATE(%s, '%%H:%%i'), STR_TO_DATE(%s, '%%H:%%i'))''', (courier['courier_id'], start, end))

        except aiomysql.Error as error:  # catches invalid value types
            validation_error.append(courier['courier_id'])
            await conn.rollback()  # rollback to the state of last valid insertion
            print(error)
        else:
            ok.append(courier['courier_id'])
            await conn.commit()  # only data on valid couriers is saved
    if validation_error:
        return False, validation_error
    else:
        return True, ok


async def post_orders_assign_execute_queries(json_request) -> (bool, List[int]):
    conn = await aiomysql.connect(host='localhost', port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=DictCursor, autocommit=False)
    cur = await conn.cursor()
    if await cur.execute('SELECT * FROM couriers WHERE courier_id = %s', (json_request['courier_id'],)):

        orders_to_assign = await cur.execute('''
        SELECT timedzeroed.order_id FROM
            (SELECT orders.* FROM
                (SELECT * FROM orders WHERE is_completed = 0) as orders
                JOIN
                    (SELECT dhof.order_id FROM
                        (SELECT * FROM couriers_working_hours WHERE courier_id=%s) as cwh, delivery_hours_of_orders as dhof WHERE
                    cwh.time_range_start <= dhof.time_range_start AND cwh.time_range_stop >= dhof.time_range_stop OR
                    cwh.time_range_start <= dhof.time_range_start AND cwh.time_range_stop <= dhof.time_range_stop OR
                    cwh.time_range_start >= dhof.time_range_start AND cwh.time_range_stop <= dhof.time_range_stop OR
                    cwh.time_range_start >= dhof.time_range_start AND cwh.time_range_stop >= dhof.time_range_stop) as timed
                ON orders.order_id = timed.order_id) AS timedzeroed,
            (SELECT max_weight FROM weights WHERE courier_type = (SELECT courier_type FROM couriers WHERE courier_id = %s)) AS wght
        WHERE timedzeroed.weight <= wght.max_weight AND timedzeroed.region IN (SELECT region FROM couriers_regions WHERE courier_id=%s)''')
        # these orders are not completed yet, have weight <= max_weight of the courier, their region is among the regions of the courier,
        # their delivery hours overlap couriers' working hours

        # this query works extremely slow

    else:
        logging.error(f'post_orders_assign_execute_queries: courier with id = {json_request["courier_id"]} not found')
        return False, []


async def post_orders_execute_queries(json_request) -> (bool, List[int]):
    conn = await aiomysql.connect(host='localhost', port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=DictCursor, autocommit=False)
    cur = await conn.cursor()
    validation_error = []
    ok = []
    required_data = {"order_id", "weight", "region", "delivery_hours"}

    for order in json_request['data']:
        await conn.begin()
        if set(order.keys()) != required_data:
            validation_error.append(order['order_id'])
            continue
        try:
            await cur.execute('''INSERT INTO orders (order_id, weight, region, is_completed) VALUES (%s, %s, %s, %s)''',
                              (order['order_id'], order['weight'], order['region'], 0))
            for wh in order['delivery_hours']:
                ranges = wh.split('-')
                start = ranges[0]
                end = ranges[1]
                await cur.execute('''INSERT INTO delivery_hours_of_orders (order_id, time_range_start, time_range_stop) VALUES 
                (%s, STR_TO_DATE(%s, '%%H:%%i'), STR_TO_DATE(%s, '%%H:%%i'))''', (order['order_id'], start, end))
        except aiomysql.Error as error:
            validation_error.append(order['order_id'])
            await conn.rollback()
            print(error)
        else:
            ok.append(order['order_id'])
            await conn.commit()
    if validation_error:
        return False, validation_error
    else:
        return True, ok


async def patch_couriers_id_execute_queries(courier_id: str, json_request: Dict):
    logging.debug(msg='patch_couriers_id_execute_queries: entered')
    conn = await aiomysql.connect(host='localhost', port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=DictCursor, autocommit=False)
    # each connection starts it`s own transaction so data can`t be corrupted
    cur = await conn.cursor()
    logging.debug(msg='patch_couriers_id_execute_queries: created connection and cursor')
    try:
        await conn.begin()
        logging.debug(msg='patch_couriers_id_execute_queries: started transaction')
        if 'courier_type' in json_request:
            logging.debug(msg='patch_couriers_id_execute_queries: started to change courier_type')
            await cur.execute('''UPDATE orders SET orders.assigned_courier_id = NULL, orders.assignment_id = NULL 
            WHERE weight > (SELECT max_weight FROM weights WHERE courier_type = %s) AND is_completed = 0 AND assigned_courier_id = %s''',
                              (json_request['courier_type'], courier_id))
            await cur.execute('''UPDATE couriers SET courier_type = %s WHERE courier_id = %s''', (json_request['courier_type'], courier_id))
            logging.debug(msg='patch_couriers_id_execute_queries: finished to change courier_type')

        if 'regions' in json_request:
            logging.debug(msg='patch_couriers_id_execute_queries: started to change regions')
            await cur.execute('''DELETE FROM couriers_regions WHERE courier_id = %s''', (courier_id,))
            await cur.executemany('''INSERT INTO couriers_regions (courier_id, region) VALUES (%s, %s)''',
                                  tuple((courier_id, i) for i in json_request['regions']))
            logging.debug(msg='patch_couriers_id_execute_queries: inserted new regions data')

            await cur.execute('''UPDATE orders SET orders.assigned_courier_id = NULL, orders.assignment_id = NULL 
                        WHERE region NOT IN (SELECT couriers_regions.region FROM couriers_regions WHERE courier_id = %s) 
                        AND is_completed = 0 AND assigned_courier_id = %s''',
                              (courier_id, courier_id))
            logging.debug(msg='patch_couriers_id_execute_queries: deassigned inappropriate deliveries')
            logging.debug(msg='patch_couriers_id_execute_queries: finished to change regions')

        if 'working_hours' in json_request:
            logging.debug(msg='patch_couriers_id_execute_queries: started to change working hours')
            await cur.execute('''DELETE FROM couriers_working_hours WHERE courier_id = %s''', (courier_id,))
            await cur.executemany('''INSERT INTO couriers_working_hours (courier_id, time_range_start, time_range_stop)
                                     VALUES (%s, STR_TO_DATE(%s, '%%H:%%i'), STR_TO_DATE(%s, '%%H:%%i'))''',
                                  tuple((courier_id, *i.split('-')) for i in json_request['working_hours']))

            await cur.execute('''UPDATE orders, (SELECT dhof.order_id FROM
                        (SELECT * FROM couriers_working_hours WHERE courier_id=%s) as cwh, delivery_hours_of_orders as dhof WHERE
                    cwh.time_range_start <= dhof.time_range_start AND cwh.time_range_stop >= dhof.time_range_stop OR
                    cwh.time_range_start <= dhof.time_range_start AND cwh.time_range_stop <= dhof.time_range_stop OR
                    cwh.time_range_start >= dhof.time_range_start AND cwh.time_range_stop <= dhof.time_range_stop OR
                    cwh.time_range_start >= dhof.time_range_start AND cwh.time_range_stop >= dhof.time_range_stop) as timed_ok
                    SET orders.assigned_courier_id = NULL, orders.assignment_id = NULL WHERE orders.order_id <> timed_ok.order_id
                    AND orders.is_completed = 0 AND orders.assigned_courier_id = %s''',
                              (courier_id, courier_id))
            logging.debug(msg='patch_couriers_id_execute_queries: finished to change working hours')

    except aiomysql.Error as e:
        await conn.rollback()
        logging.error(msg=f'patch_couriers_id_execute_queries: an aiomysql error occurred: {e}, rolled back')
        return False, {}
    else:
        await conn.commit()
        logging.debug(msg='patch_couriers_id_execute_queries: patch is finished successfully, returning info')
        await cur.execute('''SELECT * FROM couriers WHERE courier_id = %s''', (courier_id, ))
        id_type = await cur.fetchall()
        await cur.execute('''SELECT region FROM couriers_regions WHERE courier_id = %s''', (courier_id, ))
        regions = await cur.fetchall()
        await cur.execute('''SELECT time_range_start, time_range_stop FROM couriers_working_hours WHERE courier_id = %s''', (courier_id, ))
        working_hours = await cur.fetchall()
        print(id_type, regions, working_hours, sep='\n')
        return True, {"courier_id": int(courier_id), "courier_type": id_type[0]['courier_type'], "regions": [x['region'] for x in regions],
                      "working_hours": [str(z['time_range_start'])[:-3]+'-'+str(z['time_range_stop'])[:-3] for z in working_hours]}


async def post_orders_complete_execute_queries(json_request):
    logging.debug('post_orders_complete_execute_queries: entered')
    conn = await aiomysql.connect(host='localhost', port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=DictCursor, autocommit=False)
    cur = await conn.cursor()
    try:
        await conn.begin()
        logging.debug(f'post_orders_complete_execute_queries: checking the order with id = {json_request["order_id"]}')
        await cur.execute('''SELECT * FROM orders WHERE order_id = %s FOR UPDATE''', (json_request['courier_id'], ))
        data = await cur.fetchone()
        logging.debug(f'post_orders_complete_execute_queries: data on order: {data}')

        # TODO: validate timestamp via regex
        timestamp = ' '.join((json_request['complete_time'][:-1].split('T')))

        if data:
            if data['assigned_courier_id'] == json_request['courier_id']:
                logging.debug(f'post_orders_complete_execute_queries: order is found and courier_id is valid')
                await cur.execute('''UPDATE orders SET is_completed = 1, completion_timestamp = TIMESTAMP(%s) WHERE order_id = %s''',
                                  (timestamp, json_request['order_id']))
                await conn.commit()
                logging.debug(f'post_orders_complete_execute_queries: update is successful, returning')
                return True, {'order_id': json_request['order_id']}
            else:
                logging.error(f'post_orders_complete_execute_queries: courier id assigned for this order doesn\'t match id in request')
                await conn.rollback()
                return False, {}
        else:
            logging.error(f'post_orders_complete_execute_queries: order not found')
            await conn.rollback()
            return False, {}

    except aiomysql.Error as e:
        logging.error(f'post_orders_complete_execute_queries: aiomysql.Error occured: {e}')
        return False, {}