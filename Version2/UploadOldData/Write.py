import os
import csv
from time import sleep

from Parsers import point_create
from influxdb_client import InfluxDBClient, WriteOptions
import reactivex as rx
from reactivex import operators as ops

# DB server info
url = "http://localhost:8086"
token = "_cx4NpY3vwFLY39anl939pImEQ7k-Vh1_-Da6iKktn_CAET4Mb7ltsVK2gZWmwykpopWRoonYO8NA9LYk7YLtw=="
org = "DavidSW"
bucket = "MassUploadTest1"

path_of_the_directory = "D:/david/DKU/SW/TimeSeriesDBTest/DBTest3(MassUpload)/DataCollected/"
ext = '.data'

# initialize client instance for writing
client = InfluxDBClient(url=url, token=token, org=org, debug=True)


# go through files in directory that ends with '.data'
for file in os.listdir(path_of_the_directory):
    if file.endswith(ext):
        # convert file to sequence of data using rx
        with open(path_of_the_directory+file, 'r') as f:
            data = rx.from_iterable(csv.reader(f)) \
                .pipe(ops.map(lambda row: point_create(file, row)))
            # create batch processing api
            write_api = client.write_api(write_options=WriteOptions(batch_size=50_000, flush_interval=10_000))
            # write and close
            write_api.write(bucket=bucket, record=data)
            write_api.close()
    else:
        continue

client.close()
