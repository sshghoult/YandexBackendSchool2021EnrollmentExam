WEIGHTS = '''
CREATE TABLE Weights (
courier_type CHAR(10) PRIMARY KEY,
max_weight TINYINT UNSIGNED NOT NULL
);
'''

COURIERS = '''
CREATE TABLE Couriers (
courier_id SMALLINT UNSIGNED PRIMARY KEY,
courier_type CHAR(10),
FOREIGN KEY (courier_type)
    REFERENCES Weights (courier_type)
    ON UPDATE CASCADE ON DELETE SET NULL
);
'''

COURIERS_REGIONS = '''
CREATE TABLE Couriers_regions (
relation_id MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
courier_id SMALLINT UNSIGNED,
region TINYINT UNSIGNED NOT NULL,
FOREIGN KEY (courier_id)
    REFERENCES Couriers (courier_id)
    ON UPDATE CASCADE ON DELETE CASCADE);
'''

COURIERS_WORKING_HOURS = '''
CREATE TABLE Couriers_working_hours(
relation_id MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
courier_id SMALLINT UNSIGNED,
time_range_start TIME NOT NULL,
time_range_stop TIME NOT NULL,
FOREIGN KEY (courier_id)
    REFERENCES Couriers (courier_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);'''


ASSIGNMENTS = '''
CREATE TABLE Assignments(
assignment_id MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
assignment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);'''

ORDERS = '''
CREATE TABLE Orders(
order_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
weight TINYINT UNSIGNED NOT NULL,
region TINYINT UNSIGNED NOT NULL,
assigned_courier_id SMALLINT UNSIGNED,
is_completed BOOLEAN NOT NULL,
assignment_id MEDIUMINT UNSIGNED,
completion_timestamp TIMESTAMP,

FOREIGN KEY (assigned_courier_id)
    REFERENCES Couriers (courier_id)
    ON UPDATE CASCADE ON DELETE SET NULL,

FOREIGN KEY (assignment_id)
    REFERENCES Assignments (assignment_id)
    ON UPDATE CASCADE ON DELETE SET NULL
);
'''

DELIVERY_HOURS = '''
CREATE TABLE Delivery_hours_of_orders (
order_id INT UNSIGNED,
time_range_start TIME NOT NULL, 
time_range_stop TIME NOT NULL, 

FOREIGN KEY (order_id)
    REFERENCES Orders (order_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);'''


ALTOGETHER = '''
CREATE TABLE Weights (
courier_type CHAR(10) PRIMARY KEY,
max_weight TINYINT UNSIGNED NOT NULL
);

CREATE TABLE Weights (
courier_type CHAR(10) PRIMARY KEY,
max_weight TINYINT UNSIGNED NOT NULL
);

CREATE TABLE Couriers (
courier_id SMALLINT UNSIGNED PRIMARY KEY,
courier_type CHAR(10),
FOREIGN KEY (courier_type)
    REFERENCES Weights (courier_type)
    ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE Couriers_regions (
relation_id MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
courier_id SMALLINT UNSIGNED,
region TINYINT UNSIGNED NOT NULL,
FOREIGN KEY (courier_id)
    REFERENCES Couriers (courier_id)
    ON UPDATE CASCADE ON DELETE CASCADE);
CREATE TABLE Couriers_working_hours(
relation_id MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
courier_id SMALLINT UNSIGNED,
time_range_start TIME NOT NULL,
time_range_stop TIME NOT NULL,
FOREIGN KEY (courier_id)
    REFERENCES Couriers (courier_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

CREATE TABLE Assignments(
assignment_id MEDIUMINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
assignment_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL
);

CREATE TABLE Orders(
order_id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
weight TINYINT UNSIGNED NOT NULL,
region TINYINT UNSIGNED NOT NULL,
assigned_courier_id SMALLINT UNSIGNED,
is_completed BOOLEAN NOT NULL,
assignment_id MEDIUMINT UNSIGNED,
completion_timestamp TIMESTAMP,

FOREIGN KEY (assigned_courier_id)
    REFERENCES Couriers (courier_id)
    ON UPDATE CASCADE ON DELETE SET NULL,

FOREIGN KEY (assignment_id)
    REFERENCES Assignments (assignment_id)
    ON UPDATE CASCADE ON DELETE SET NULL
);

CREATE TABLE Delivery_hours_of_orders (
order_id INT UNSIGNED,
time_range_start TIME NOT NULL, 
time_range_stop TIME NOT NULL, 

FOREIGN KEY (order_id)
    REFERENCES Orders (order_id)
    ON UPDATE CASCADE ON DELETE CASCADE
);

'''