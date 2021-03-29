import aiomysql
import cfg  # configure file
from typing import List, Dict  # type hints
import logging


# all DB_connect coroutines are isolated for the convenience of work with the transactions and connections

# TODO: use pools of connections instead


async def post_couriers_execute_queries(json_request: Dict) -> (bool, Dict):
    """
    A coroutine for the associated handler-coroutine that 'talks' to the DB.
    :param json_request: dict loaded from request via standard library, schema is specified in the docs
    :return: tuple of bool and list, bool indicates if everything was processed correctly, list is a list of couriers' ids
    that were processed correctly (if all of them were),
    otherwise it`s a tuple of couriers' ids during the processing of which errors were encountered
    """
    logging.info(f'post_couriers_execute_queries: json_request={json_request} entered')
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=False)
    # cursorclass=aiomysql.DictCursor: SELECT`s result will be presented in dicts
    # each connection starts it`s own transaction so data can`t be corrupted

    cur = await conn.cursor()
    validation_error = []
    ok = []
    # every step of range is a new element with courier data, outer cycle is outside of try/except,
    # so one invalid element won`t stop others from being processed
    # the same is the reason to make validation of data here

    required_data = {"courier_id", "courier_type", "regions", "working_hours"}

    for courier in json_request['data']:
        await conn.begin()
        if set(courier.keys()) != required_data:  # validate keys of the dict with info about courier
            logging.info(f'post_couriers_execute_queries: json_request={json_request}; '
                         f'invalid data on courier id={courier["courier_id"]}')
            validation_error.append(courier['courier_id'])
            await conn.rollback()
            continue
        if type(courier["courier_id"]) is not int or type(courier["courier_type"]) is not str or type(
                courier["regions"]) is not list or any(
            (type(x) is not int for x in courier["regions"])) or type(courier["working_hours"]) is not list or any(
            (type(x) is not str for x in courier["working_hours"])):
            # this one might be a bit extra due to broad exception further,
            # but from time to time it`ll save us some time because we won`t have to connect to the DB and lock the table
            logging.info(
                f'post_couriers_execute_queries: json_request={json_request}; invalid data on courier id={courier["courier_id"]}')
            validation_error.append(courier['courier_id'])
            await conn.rollback()
            continue

        logging.debug(
            f'post_couriers_execute_queries: json_request={json_request}; data on courier id={courier["courier_id"]} '
            f'has not been suspended, proceeding')
        try:
            await cur.execute("INSERT INTO couriers (courier_id, courier_type) VALUES "
                              "(%s, %s);", (courier['courier_id'], courier['courier_type']))
            logging.debug(
                f'post_couriers_execute_queries: json_request={json_request}; inserted data on courier id={courier["courier_id"]} '
                f'into table couriers')
            for region in courier['regions']:
                await cur.execute("INSERT INTO couriers_regions (courier_id, region) VALUES ('%s', %s)", (courier['courier_id'], region))
            logging.debug(
                f'post_couriers_execute_queries: json_request={json_request}; inserted data on courier id={courier["courier_id"]} '
                f'into table couriers_regions')
            for wh in courier['working_hours']:
                ranges = wh.split('-')
                start = ranges[0]
                end = ranges[1]
                await cur.execute('''INSERT INTO couriers_working_hours (courier_id, time_range_start, time_range_stop)
                    VALUES ('%s', STR_TO_DATE(%s, '%%H:%%i'), STR_TO_DATE(%s, '%%H:%%i'))''', (courier['courier_id'], start, end))
            logging.debug(
                f'post_couriers_execute_queries: json_request={json_request}; inserted data on courier id={courier["courier_id"]} '
                f'into table couriers_working_hours')

        except Exception as error:
            # catches invalid value types and invalid formats,
            # broad Exception is used to prevent status 500 on badly formed requests
            # (e.g. injections, which might be split and then indexed incorrectly, raising IndexError)
            logging.debug(
                f'post_couriers_execute_queries: json_request={json_request}; during the processing of courier with id={courier["courier_id"]}'
                f'an exception occurred: {error}')
            validation_error.append(courier['courier_id'])
            await conn.rollback()  # rollback to the state of last valid insertion
        else:
            logging.debug(f'post_couriers_execute_queries: json_request={json_request}; courier id={courier["courier_id"]} '
                          f'is fulfilled successfully')
            ok.append(courier['courier_id'])
            await conn.commit()  # only data on valid couriers is saved

    if validation_error:
        logging.info(f'post_couriers_execute_queries: json_request={json_request}; request has invalid data in it, returning')
        conn.close()
        return False, validation_error
    else:
        logging.info(f'post_couriers_execute_queries: json_request={json_request}; request has been fulfilled successfully, returning')
        conn.close()
        return True, ok


async def patch_couriers_id_execute_queries(courier_id: str, json_request: Dict) -> (bool, Dict):
    """
    A coroutine for the associated handler-coroutine that 'talks' to the DB.
    :param courier_id: id of the courier retrieved from the URI
    :param json_request: dict with data to change to
    :return: tuple of bool and dict, bool indicates if everything was processed correctly,
    dict is a dict with all data on the updates courier
    """
    logging.info(msg='patch_couriers_id_execute_queries: entered')
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=False)
    # cursorclass=aiomysql.DictCursor: SELECT`s result will be presented in dicts
    # each connection starts it`s own transaction so data can`t be corrupted

    cur = await conn.cursor()
    logging.debug(msg='patch_couriers_id_execute_queries: created connection and cursor')
    try:
        await conn.begin()
        logging.debug(msg='patch_couriers_id_execute_queries: started transaction')
        if 'courier_type' in json_request:
            logging.debug(msg='patch_couriers_id_execute_queries: started to change courier_type')
            await cur.execute('''UPDATE orders SET orders.assigned_courier_id = NULL, orders.assignment_id = NULL 
            WHERE orders.weight > (SELECT max_weight FROM weights WHERE courier_type = %s) AND orders.is_completed = 0 
            AND orders.assigned_courier_id = %s''',
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
            logging.debug(msg='patch_couriers_id_execute_queries: de-assigned inappropriate deliveries')
            logging.debug(msg='patch_couriers_id_execute_queries: finished to change regions')

        if 'working_hours' in json_request:
            logging.debug(msg='patch_couriers_id_execute_queries: started to change working hours')
            await cur.execute('''DELETE FROM couriers_working_hours WHERE courier_id = %s''', (courier_id,))
            await cur.executemany('''INSERT INTO couriers_working_hours (courier_id, time_range_start, time_range_stop)
                                     VALUES (%s, STR_TO_DATE(%s, '%%H:%%i'), STR_TO_DATE(%s, '%%H:%%i'))''',
                                  tuple((courier_id, *i.split('-')) for i in json_request['working_hours']))
            logging.debug(f'patch_couriers_id_execute_queries: updated couriers_working_hours')

            await cur.execute('''UPDATE orders SET orders.assigned_courier_id = NULL,
            orders.assignment_id = NULL WHERE orders.order_id NOT IN (SELECT timedzeroed.order_id FROM
                (SELECT orders.* FROM (SELECT * FROM orders WHERE is_completed = 0 AND assigned_courier_id IS NULL) as orders
                JOIN (SELECT DISTINCT dhof.order_id FROM (SELECT * FROM couriers_working_hours WHERE courier_id=%s) as cwh,
                    delivery_hours_of_orders as dhof WHERE
                        cwh.time_range_start <= dhof.time_range_start AND dhof.time_range_start <= cwh.time_range_stop AND
                        cwh.time_range_stop <= dhof.time_range_stop OR
                        cwh.time_range_start <= dhof.time_range_start AND dhof.time_range_start <= dhof.time_range_stop AND
                        dhof.time_range_stop <= cwh.time_range_stop OR
                        dhof.time_range_start <= cwh.time_range_start AND cwh.time_range_start <= dhof.time_range_stop AND
                        dhof.time_range_stop <= cwh.time_range_stop OR
                        dhof.time_range_start <= cwh.time_range_start AND cwh.time_range_start <= cwh.time_range_stop AND
                        cwh.time_range_stop <= dhof.time_range_stop)
                as timed
                ON orders.order_id = timed.order_id) AS timedzeroed,
                (SELECT max_weight FROM weights WHERE courier_type = (SELECT courier_type FROM couriers WHERE courier_id = %s)) AS wght
                WHERE timedzeroed.weight <= wght.max_weight AND
                      timedzeroed.region IN (SELECT region FROM couriers_regions WHERE courier_id=%s)) AND
                orders.assignment_id = (SELECT current_assignment_id FROM couriers WHERE courier_id = %s);''',
                              (courier_id, courier_id, courier_id, courier_id))
            logging.debug(f'patch_couriers_id_execute_queries: updated orders')

            ids = await cur.fetchall()

            await cur.executemany('''UPDATE orders SET assignment_id = (SELECT current_assignment_id FROM couriers WHERE courier_id = %s), 
            assigned_courier_id = %s WHERE order_id = %s''',
                                  tuple((courier_id, courier_id, x['order_id']) for x in ids))
            # TODO: it's rather ineffective, I should think about optimizing it
            logging.debug(msg='patch_couriers_id_execute_queries: finished to change working hours')

            await cur.execute("SELECT order_id, assignment_id FROM orders WHERE assignment_id ="
                              " (SELECT current_assignment_id FROM couriers WHERE courier_id = %s) AND is_completed = 0",
                              (courier_id,))

            data = await cur.fetchall()
            if not data:
                logging.info(f'patch de-assigned all remaining orders of courier {courier_id}, setting current_assignment_id to NULL')
                # checking if assignment is empty after changes
                await cur.execute("UPDATE couriers SET current_assignment_id = NULL WHERE courier_id = %s",
                                  (courier_id,))

    except Exception as error:
        await conn.rollback()
        conn.close()
        logging.info(msg=f'patch_couriers_id_execute_queries: an error occurred: {error}, rolled back')
        return False, {}
    else:
        await conn.commit()
        logging.info(msg='patch_couriers_id_execute_queries: patch is finished successfully, returning info')
        await cur.execute('''SELECT * FROM couriers WHERE courier_id = %s''', (courier_id,))
        id_type = await cur.fetchall()
        await cur.execute('''SELECT region FROM couriers_regions WHERE courier_id = %s''', (courier_id,))
        regions = await cur.fetchall()
        await cur.execute('''SELECT time_range_start, time_range_stop FROM couriers_working_hours WHERE courier_id = %s''', (courier_id,))
        working_hours = await cur.fetchall()
        conn.close()
        return True, {"courier_id": int(courier_id), "courier_type": id_type[0]['courier_type'], "regions": [x['region'] for x in regions],
                      "working_hours": [str(z['time_range_start'])[:-3] + '-' + str(z['time_range_stop'])[:-3]+'Z' for z in working_hours]}


async def post_orders_execute_queries(json_request: Dict) -> (bool, List[int]):
    """
    A coroutine for the associated handler-coroutine that 'talks' to the DB.
    :param json_request: dict loaded from request via standard library, schema is specified in the docs
    :return: tuple of bool and list, bool indicates if everything was processed correctly, list is a list of orders' ids
    that were processed correctly (if all of them were),
    otherwise it`s a tuple of orders' ids during the processing of which errors were encountered
    """
    logging.info(f'post_orders_execute_queries: json_request={json_request}; entered')
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=False)
    cur = await conn.cursor()
    validation_error = []
    ok = []
    required_data = {"order_id", "weight", "region", "delivery_hours"}

    for order in json_request['data']:
        await conn.begin()
        if set(order.keys()) != required_data or type(order['order_id']) is not int or not (
                type(order['weight']) is not float or type(order['weight']) is not int) or type(order['region']) is not int \
                or type(order['delivery_hours']) is not list or any(type(x) is not str for x in order['delivery_hours']):
            logging.info(f'post_orders_execute_queries: json_request={json_request}; invalid data on order id={order["order_id"]}')
            validation_error.append(order['order_id'])
            await conn.rollback()
            continue

        logging.debug(
            f'post_orders_execute_queries: json_request={json_request}; data on order id={order["order_id"]} '
            f'has not been suspended, proceeding')
        try:
            await cur.execute('''INSERT INTO orders (order_id, weight, region, is_completed) VALUES (%s, %s, %s, %s)''',
                              (order['order_id'], order['weight'], order['region'], 0))
            logging.debug(
                f'post_orders_execute_queries: json_request={json_request}; inserted into orders the order id={order["order_id"]}')
            for dh in order['delivery_hours']:
                ranges = dh.split('-')
                start = ranges[0]
                end = ranges[1]
                await cur.execute('''INSERT INTO delivery_hours_of_orders (order_id, time_range_start, time_range_stop) VALUES 
                (%s, STR_TO_DATE(%s, '%%H:%%i'), STR_TO_DATE(%s, '%%H:%%i'))''', (order['order_id'], start, end))
            logging.debug(
                f'post_orders_execute_queries: json_request={json_request}; inserted into delivery_hours_of_orders the order id={order["order_id"]}')
        except Exception as error:
            logging.debug(
                f'post_orders_execute_queries: json_request={json_request}; during the processing of the order with id={order["order_id"]}'
                f'an exception occurred: {error}')
            validation_error.append(order['order_id'])
            await conn.rollback()

        else:
            logging.debug(f'post_orders_execute_queries: json_request={json_request}; order id={order["order_id"]} '
                          f'is fulfilled successfully')
            ok.append(order['order_id'])
            await conn.commit()

    if validation_error:
        logging.info(f'post_orders_execute_queries: json_request={json_request}; request has invalid data in it, returning')
        conn.close()
        return False, validation_error
    else:
        logging.info(f'post_orders_execute_queries: json_request={json_request}; request has been fulfilled successfully, returning')
        conn.close()
        return True, ok


async def post_orders_assign_execute_queries(json_request: Dict) -> (bool, Dict):
    """
    A coroutine for the associated handler-coroutine that 'talks' to the DB.
    :param json_request: dict loaded from request via standard library, schema is specified in the docs
    :return: tuple of bool and dict, bool indicates if everything was processed correctly,
    dict is a ready-to-be-dumped info about assigned orders: {"orders": [{"id": int}], "assign_time": assignment_timestamp_str}
    """
    logging.info(f'post_orders_assign_execute_queries: json_request={json_request} entered')
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=False)
    # cursorclass=aiomysql.DictCursor: SELECT`s result will be presented in dicts
    # each connection starts it`s own transaction so data can`t be corrupted

    cur = await conn.cursor()
    try:
        await conn.begin()
        await cur.execute('SELECT * FROM couriers WHERE courier_id = %s', (json_request['courier_id'],))
        courier_data = await cur.fetchone()
        if courier_data:
            logging.debug(f'post_orders_assign_execute_queries: json_request={json_request}; '
                          f'courier with id = {json_request["courier_id"]} is found')
            cur_assignment = courier_data['current_assignment_id']
            if cur_assignment is None:
                logging.debug(f'post_orders_assign_execute_queries: json_request={json_request}; '
                              f'current assignment of the courier is None, looking up orders for the new one')
                await cur.execute('''SELECT timedzeroed.order_id FROM
                (SELECT orders.* FROM (SELECT * FROM orders WHERE is_completed = 0 AND assigned_courier_id IS NULL) as orders
                JOIN (SELECT DISTINCT dhof.order_id FROM (SELECT * FROM couriers_working_hours WHERE courier_id=%s) as cwh,
                    delivery_hours_of_orders as dhof WHERE
                        cwh.time_range_start <= dhof.time_range_start AND dhof.time_range_start <= cwh.time_range_stop AND
                        cwh.time_range_stop <= dhof.time_range_stop OR
                        cwh.time_range_start <= dhof.time_range_start AND dhof.time_range_start <= dhof.time_range_stop AND
                        dhof.time_range_stop <= cwh.time_range_stop OR
                        dhof.time_range_start <= cwh.time_range_start AND cwh.time_range_start <= dhof.time_range_stop AND
                        dhof.time_range_stop <= cwh.time_range_stop OR
                        dhof.time_range_start <= cwh.time_range_start AND cwh.time_range_start <= cwh.time_range_stop AND
                        cwh.time_range_stop <= dhof.time_range_stop)
                as timed
                ON orders.order_id = timed.order_id) AS timedzeroed,
                (SELECT max_weight FROM weights WHERE courier_type = (SELECT courier_type FROM couriers WHERE courier_id = %s)) AS wght
                WHERE timedzeroed.weight <= wght.max_weight AND
                      timedzeroed.region IN (SELECT region FROM couriers_regions WHERE courier_id=%s) FOR UPDATE''',
                                  (json_request['courier_id'], json_request['courier_id'], json_request['courier_id']))

                # these orders are not completed yet, have weight <= max_weight of the courier,
                # their region is among the regions of the courier,
                # their delivery hours overlap couriers' working hours, they are not assigned yet
                ids = await cur.fetchall()

                if not ids:
                    logging.info(f"post_orders_assign_execute_queries: json_request={json_request}; "
                                 f"have found no appropriate orders for the courier {json_request['courier_id']}, returning")
                    await conn.rollback()
                    conn.close()
                    return True, {'orders': []}

                logging.debug(f'''post_orders_assign_execute_queries: json_request={json_request}; selected orders, creating assignment''')
                await cur.execute('''INSERT INTO assignments (assignment_id, assignment_timestamp) VALUES (DEFAULT, DEFAULT)''')
                logging.debug(f'''post_orders_assign_execute_queries: json_request={json_request}; updating courier current assignment''')
                await cur.execute('''UPDATE couriers SET current_assignment_id = (SELECT assignment_id FROM assignments 
                ORDER BY assignment_id DESC LIMIT 1) WHERE courier_id = %s''', (json_request['courier_id'],))
                logging.debug(f'''post_orders_assign_execute_queries: json_request={json_request}; updating orders''')
                await cur.executemany('''UPDATE orders SET assignment_id = (SELECT assignment_id FROM assignments 
                ORDER BY assignment_id DESC LIMIT 1), assigned_courier_id = %s WHERE order_id = %s''',
                                      tuple((json_request['courier_id'], x['order_id']) for x in ids))

                await cur.execute('''SELECT assignment_timestamp FROM assignments 
                            WHERE assignment_id = (SELECT current_assignment_id FROM couriers WHERE courier_id = %s)''',
                                  (json_request['courier_id'],))
                assignment_time = await cur.fetchone()
                assignment_time = assignment_time['assignment_timestamp']
                logging.info(f'''post_orders_assign_execute_queries: json_request={json_request}; created new assignment, returning''')
                await conn.commit()
                conn.close()
                return True, {'orders': [{'id': x['order_id']} for x in ids], 'assign_time': str(assignment_time.isoformat())}

            else:
                await cur.execute('''SELECT order_id FROM orders WHERE assignment_id = %s''',
                                  (cur_assignment,))
                ids = await cur.fetchall()
                await cur.execute('''SELECT assignment_timestamp FROM assignments 
                WHERE assignment_id = (SELECT current_assignment_id FROM couriers WHERE courier_id = %s)''', (json_request['courier_id'],))
                assignment_time = await cur.fetchone()
                assignment_time = assignment_time['assignment_timestamp']
                logging.info(f"post_orders_assign_execute_queries: json_request={json_request}; "
                             f"assignment is not finished yet, returning with remaining orders")
                await conn.commit()
                conn.close()
                return True, {'orders': [{'id': x['order_id']} for x in ids], 'assign_time': str(assignment_time.isoformat())}
        else:
            logging.info(f'post_orders_assign_execute_queries: json_request={json_request}; '
                         f'courier with id = {json_request["courier_id"]} not found, returning')
            await conn.rollback()
            conn.close()
            return False, {}
    except Exception as error:
        logging.info(f'post_orders_assign_execute_queries: json_request={json_request}; an exception occurred: {error}, returning')
        await conn.rollback()
        conn.close()
        return False, {}


async def post_orders_complete_execute_queries(json_request: Dict) -> (bool, Dict):
    """
    A coroutine for the associated handler-coroutine that 'talks' to the DB.
    :param json_request: dict loaded from request via standard library, schema is specified in the docs
    :return: tuple of bool and dict, bool indicates if everything was processed correctly,
    dict contains an order id if bool is true and is empty otherwise
    """
    logging.debug(f'post_orders_complete_execute_queries: json_request={json_request}; entered')
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=False)
    # cursorclass=aiomysql.DictCursor: SELECT`s result will be presented in dicts
    # each connection starts it`s own transaction so data can`t be corrupted

    cur = await conn.cursor()
    try:
        await conn.begin()
        logging.debug(f'post_orders_complete_execute_queries: json_request={json_request}; checking the order with id = {json_request["order_id"]}')
        await cur.execute('''SELECT * FROM orders WHERE order_id = %s FOR UPDATE''', (json_request['order_id'],))
        data = await cur.fetchone()
        logging.debug(f'post_orders_complete_execute_queries: json_request={json_request}; data on order: {data}')

        # TODO: validate timestamp via regex
        timestamp = ' '.join((json_request['complete_time'][:-1].split('T')))

        if data:
            if data['assigned_courier_id'] == json_request['courier_id']:
                logging.debug(f'post_orders_complete_execute_queries: json_request={json_request}; order is found and courier_id is valid')
                await cur.execute('''UPDATE orders SET is_completed = 1, completion_timestamp = TIMESTAMP(%s) WHERE order_id = %s''',
                                  (timestamp, json_request['order_id']))

                await cur.execute("SELECT order_id, assignment_id FROM orders WHERE assignment_id ="
                                  " (SELECT current_assignment_id FROM couriers WHERE courier_id = %s) AND is_completed = 0",
                                  (json_request['courier_id'],))
                data = await cur.fetchall()
                if not data:
                    logging.info(f'order {json_request["order_id"]} was the last one in the assignment '
                                 f'{data["assignment_id"]} of the courier {json_request["courier_id"]}, setting current assignment to NULL')
                    # repeated completion of the task from the previous assignment won`t trigger this,
                    # because current assignment is retrieved here
                    await cur.execute("UPDATE couriers SET current_assignment_id = NULL WHERE courier_id = %s",
                                      (json_request['courier_id'],))
                await conn.commit()

                logging.debug(f'post_orders_complete_execute_queries: json_request={json_request}; update is successful, returning')
                conn.close()
                return True, {'order_id': json_request['order_id']}
            else:
                logging.info(f'post_orders_complete_execute_queries: json_request={json_request};'
                             f' courier id assigned for this order doesn\'t match id in request')
                await conn.rollback()
                conn.close()
                return False, {}
        else:
            logging.info(f'post_orders_complete_execute_queries: json_request={json_request}; order not found')
            await conn.rollback()
            conn.close()
            return False, {}

    except Exception as error:
        logging.info(f'post_orders_complete_execute_queries: json_request={json_request}; error occurred: {error}')
        conn.close()
        return False, {}


async def get_couriers_id_execute_queries(courier_id):
    conn = await aiomysql.connect(host=cfg.DB_HOST, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=aiomysql.DictCursor, autocommit=False)
    cur = await conn.cursor()
    try:
        await cur.execute('''SELECT * FROM couriers WHERE courier_id = %s''', (courier_id,))
        couriers = await cur.fetchall()

        await cur.execute('''SELECT * FROM couriers_regions WHERE courier_id = %s''', (courier_id,))
        regs = await cur.fetchall()

        await cur.execute('''SELECT * FROM couriers_working_hours WHERE courier_id = %s''', (courier_id,))
        whs = await cur.fetchall()
    except aiomysql.Error:
        conn.close()
        return False, []
    else:
        conn.close()
        return True, [couriers, regs, [{i: str(x[i]) for i in x} for x in whs]]
