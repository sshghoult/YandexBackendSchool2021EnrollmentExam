WEIGHTS = '''
CREATE TABLE `weights` (
  `courier_type` char(10) NOT NULL,
  `max_weight` tinyint unsigned NOT NULL,
  PRIMARY KEY (`courier_type`));
'''

COURIERS = '''
CREATE TABLE `couriers` (
  `courier_id` smallint unsigned NOT NULL,
  `courier_type` char(10) DEFAULT NULL,
  PRIMARY KEY (`courier_id`),
  KEY `courier_type` (`courier_type`),
  CONSTRAINT `couriers_ibfk_1` FOREIGN KEY (`courier_type`) REFERENCES `weights` (`courier_type`) ON DELETE SET NULL ON UPDATE CASCADE
);
'''

COURIERS_REGIONS = '''
CREATE TABLE `couriers_regions` (
  `relation_id` mediumint unsigned NOT NULL AUTO_INCREMENT,
  `courier_id` smallint unsigned DEFAULT NULL,
  `region` tinyint unsigned NOT NULL,
  PRIMARY KEY (`relation_id`),
  KEY `courier_id` (`courier_id`),
  CONSTRAINT `couriers_regions_ibfk_1` FOREIGN KEY (`courier_id`) REFERENCES `couriers` (`courier_id`) ON DELETE CASCADE ON UPDATE CASCADE);
'''

COURIERS_WORKING_HOURS = '''
CREATE TABLE `couriers_working_hours` (
  `relation_id` mediumint unsigned NOT NULL AUTO_INCREMENT,
  `courier_id` smallint unsigned NOT NULL,
  `time_range_start` time DEFAULT NULL,
  `time_range_stop` time DEFAULT NULL,
  PRIMARY KEY (`relation_id`),
  KEY `courier_id` (`courier_id`),
  CONSTRAINT `couriers_working_hours_ibfk_1` FOREIGN KEY (`courier_id`) 
  REFERENCES `couriers` (`courier_id`) ON DELETE CASCADE ON UPDATE CASCADE);'''

ASSIGNMENTS = '''
CREATE TABLE `assignments` (
  `assignment_id` mediumint unsigned NOT NULL AUTO_INCREMENT,
  `assignment_timestamp` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`assignment_id`));'''

ORDERS = '''
CREATE TABLE `orders` (
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
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`assigned_courier_id`) REFERENCES `couriers` (`courier_id`) ON DELETE SET NULL ON UPDATE CASCADE,
  CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`assignment_id`) ON DELETE SET NULL ON UPDATE CASCADE);
'''
