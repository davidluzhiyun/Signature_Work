from influxdb_client import InfluxDBClient, WriteOptions
import monitor
from monitor import Monitor
from ftplib import FTP_TLS
from time import sleep

# DB server info
url = "http://localhost:8086"
token = "_cx4NpY3vwFLY39anl939pImEQ7k-Vh1_-Da6iKktn_CAET4Mb7ltsVK2gZWmwykpopWRoonYO8NA9LYk7YLtw=="
org = "DavidSW"
bucket = "MassUploadTest1"

# MACs and names
a =[['d6:3e:9f:34:9e:1a','Alex'],['d3:fd:fb:2c:15:02','Bob']]
m = Monitor(a)

client = InfluxDBClient(url=url, token=token, org=org, debug=True)
write_api = client.write_api(write_options=WriteOptions(batch_size=100))


# parameters for sampling frequency and range
m.watch_start_config()

m.watch_start()

sleep(0.1)
m.start_upload(write_api)
m.watching_for(3600)

m.watch_end()
m.quit_reset()