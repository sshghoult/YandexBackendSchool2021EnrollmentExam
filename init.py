import Application
import aiomysql
import asyncio
import cfg


async def init():
    conn = await aiomysql.connect(host=cfg.DB_HOST, password=cfg.DB_PASSWORD, port=cfg.DB_PORT,
                                  user=cfg.DB_USER, cursorclass=aiomysql.DictCursor, autocommit=False)

    cur = await conn.cursor()
    await conn.begin()

    await cur.execute('USE `candy_delivery_app`')
    await cur.execute('''CREATE TABLE IF NOT EXISTS `weights` 
        (
            `courier_type` char(10) NOT NULL,
            `max_weight` tinyint unsigned NOT NULL,
            PRIMARY KEY (`courier_type`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci''')

    await cur.execute('''INSERT IGNORE INTO `weights` VALUES ("foot", 10), ("bike", 15), ("car", 50)''')

    await cur.execute('''CREATE TABLE IF NOT EXISTS `assignments` 
        (
            `assignment_id` mediumint unsigned NOT NULL AUTO_INCREMENT,
            `assignment_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (`assignment_id`)
        ) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci''')

    await cur.execute('''CREATE TABLE IF NOT EXISTS `couriers` 
        (
            `courier_id` smallint unsigned NOT NULL,
            `courier_type` char(10) DEFAULT NULL,
            `current_assignment_id` mediumint unsigned DEFAULT NULL,
            PRIMARY KEY (`courier_id`),
            KEY `courier_type` (`courier_type`),
            KEY `current_assignment_id` (`current_assignment_id`),
            CONSTRAINT `couriers_ibfk_1` FOREIGN KEY (`courier_type`) REFERENCES `weights` (`courier_type`) 
            ON DELETE SET NULL ON UPDATE CASCADE,
            CONSTRAINT `couriers_ibfk_2` FOREIGN KEY (`current_assignment_id`) REFERENCES `assignments` (`assignment_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci''')

    await cur.execute('''CREATE TABLE IF NOT EXISTS `couriers_working_hours` 
        (
            `relation_id` mediumint unsigned NOT NULL AUTO_INCREMENT,
            `courier_id` smallint unsigned NOT NULL,
            `time_range_start` time DEFAULT NULL,
            `time_range_stop` time DEFAULT NULL,
            PRIMARY KEY (`relation_id`),
            KEY `courier_id` (`courier_id`),
            CONSTRAINT `couriers_working_hours_ibfk_1` FOREIGN KEY (`courier_id`) REFERENCES `couriers` (`courier_id`) 
            ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB AUTO_INCREMENT=35 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci''')

    await cur.execute('''CREATE TABLE IF NOT EXISTS `couriers_regions` 
        (
            `relation_id` mediumint unsigned NOT NULL AUTO_INCREMENT,
            `courier_id` smallint unsigned DEFAULT NULL,
            `region` tinyint unsigned NOT NULL,
              PRIMARY KEY (`relation_id`),
              KEY `courier_id` (`courier_id`),
              CONSTRAINT `couriers_regions_ibfk_1` FOREIGN KEY (`courier_id`) REFERENCES `couriers` (`courier_id`) ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB AUTO_INCREMENT=154 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci''')

    await cur.execute('''CREATE TABLE IF NOT EXISTS `orders` 
        (
            `order_id` int unsigned NOT NULL AUTO_INCREMENT,
            `weight` decimal(5,2) NOT NULL,
            `region` tinyint unsigned NOT NULL,
            `assigned_courier_id` smallint unsigned DEFAULT NULL,
            `is_completed` tinyint(1) NOT NULL,
            `assignment_id` mediumint unsigned DEFAULT NULL,
            `completion_timestamp` timestamp NULL DEFAULT NULL,
            PRIMARY KEY (`order_id`),
            KEY `assigned_courier_id` (`assigned_courier_id`),
            KEY `assignment_id` (`assignment_id`),
            KEY `weight_index` (`weight`),
            KEY `region_index` (`region`),
            CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`assigned_courier_id`) REFERENCES `couriers` (`courier_id`) 
            ON DELETE SET NULL ON UPDATE CASCADE,
            CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`assignment_id`) 
            ON DELETE SET NULL ON UPDATE CASCADE
        ) ENGINE=InnoDB AUTO_INCREMENT=40 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci''')

    await cur.execute('''CREATE TABLE IF NOT EXISTS `delivery_hours_of_orders` 
        (
            `order_id` int unsigned DEFAULT NULL,
            `time_range_start` time NOT NULL,
            `time_range_stop` time NOT NULL,
            KEY `order_id` (`order_id`),
            CONSTRAINT `delivery_hours_of_orders_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) 
            ON DELETE CASCADE ON UPDATE CASCADE
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci''')

    await conn.commit()
    conn.close()



if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init())
    Application.run()
