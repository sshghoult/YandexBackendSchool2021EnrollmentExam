import asyncio
import aiomysql
from aiomysql import DictCursor  # SELECT`s result will be presented in dicts
import cfg  # configure file
from typing import List, Tuple, Iterable, Dict  # type hints


# TODO: de-hardcode passwords


async def execute_queries(queries: List[Tuple[str, Iterable]]) -> List[Dict]:
    # TODO: read about pools of connections and use it instead
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
