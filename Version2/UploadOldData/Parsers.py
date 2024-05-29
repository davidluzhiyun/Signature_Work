# import required module
import re
from influxdb_client import *

MEASUREMENT = "Test1"
LOCATION = "GymCC"


# retrieve the equipment name from the file name
def parse_equipment(file_name):
    return file_name[:-23]


# split line into manageable tokens
def parse_line(line):
    assert isinstance(line, str)
    return re.split(r'[}{,:\s]+', line)


# create data point
def point_create(file_name: str, line: list) -> Point:
    # CSV reader already makes every line into a list
    # Use default dictionary structure
    equipment = parse_equipment(file_name)
    x = float(line[1][6:])
    y = float(line[2][5:])
    z = float(line[3][:-1][5:])
    time = int(line[0])

    dict_structure = {
        "measurement": MEASUREMENT,
        "tags": {"location": LOCATION,
                 "equipment": equipment},
        "fields": {"x": x,
                   "y": y,
                   "z": z},
        "time": time
    }
    point = Point.from_dict(dict_structure, WritePrecision.MS)
    return point
