from influxdb_client import InfluxDBClient
import monitor
from monitor import Monitor

# DB server info
url = "http://localhost:8086"
token = "_cx4NpY3vwFLY39anl939pImEQ7k-Vh1_-Da6iKktn_CAET4Mb7ltsVK2gZWmwykpopWRoonYO8NA9LYk7YLtw=="
org = "DavidSW"
bucket = "MassUploadTest1"

# MACs and names
a =[['d6:3e:9f:34:9e:1a','Alex'],['d3:fd:fb:2c:15:02','Bob']]
m = Monitor(a)

client = InfluxDBClient(url=url, token=token, org=org, debug=True)
# parameters for sampling frequency and range
m.watch_start_config()

# number of cycles to run. change to while true for long term
# in future updates change to some timer
for i in range(24):

    m.watch_start()

    # length of each cycle in seconds
    m.watching_for(3600)

    m.watch_end()
    m.upload(client)
m.quit_reset()