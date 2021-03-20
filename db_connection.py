import asyncio
import aiomysql
from aiomysql import DictCursor  # SELECT`s result will be presented in dicts
import cfg  # configure file
from typing import List, Tuple, Iterable, Dict  # type hints


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

    for courier in json_request['data']:
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


async def post_orders_execute_queries(json_request) -> (bool, List[int]):
    conn = await aiomysql.connect(host='localhost', port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=DictCursor, autocommit=False)
    cur = await conn.cursor()
    validation_error = []
    ok = []
    required_data = {"order_id", "weight", "region", "delivery_hours"}

    for order in json_request['data']:
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



async def execute_queries(queries: List[Tuple[str, Iterable]]) -> List[Dict]:
    """
    Async function that executes queries on the database.
    Database parameters are imported from cfg.py file and should be stated there and only there
    :param queries: list of tuples, where first element is a parametrised query and second is a tuple of arguments for the query
    :return: list of the fetched data in the order corresponding to the order of queries
    """
    conn = await aiomysql.connect(host='localhost', port=cfg.DB_PORT,
                                  user=cfg.DB_USER, password=cfg.DB_PASSWORD,
                                  db=cfg.DATABASE, cursorclass=DictCursor, autocommit=True)
    cur = await conn.cursor()
    result = []
    for q in queries:
        await cur.execute(q[0], args=q[1])
        # parametrised queries are used here to prevent SQL injection
        result.append(cur.fetchall())
    # can`t use cur.executemany here due to collections` elements (collections are json dict values) having to be inserted in VALUES
    # Non-SELECT queries return empty list, which is fine
    conn.close()
    return result

#
# async def main():
#     qs = [("INSERT INTO couriers (courier_id, courier_type) VALUES (%s, %s);", (1, 'foot'))]
#
#     a = await asyncio.wait_for(execute_queries(qs), timeout=100)
#     print(*(i.result() for i in a), sep='\n')
#
# if __name__ == '__main__':
#     asyncio.run(main())
