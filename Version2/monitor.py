from __future__ import print_function
from mbientlab.metawear import MetaWear, libmetawear, parse_value
from mbientlab.metawear.cbindings import *
from time import sleep
from threading import Event
import reactivex as rx
from influxdb_client import InfluxDBClient, WriteOptions
from reactivex import operators as ops
import os
import csv
import sys
import time
from Parsers import *

from ftplib import FTP_TLS

BUCKET = "DefaultBucket"

class State:
    # init state
    def __init__(self, device, equipment):
        self.device = device
        assert isinstance(self.device,MetaWear)
        self.equipment = equipment
        self.samples = 0
        #
        self.fn = self.equipment + time.strftime("%Y%m%d-%H%M%S") + 'acc.data'
        self.fh = open(self.fn, 'a')
        #
        self.accCallback = FnVoid_VoidP_DataP(self.acc_data_handler)
    
    # acc callback function
    def acc_data_handler(self, ctx, data):
        self.samples += 1
        self.fh.write("%d, %s\n" % (data.contents.epoch, parse_value(data)))
        #epoch(ms), {x : (-)X.XXX, y : (-)Y.YYY, z : (-)Z.ZZZ}  Note: raw data in string format
        
class Monitor:
    #example of lst: [[mac1,equipment name1],[mac2,equipment name2],.....]
    #connect and initialize
    def __init__(self, lst):
        self.states = []
        self.devices = []
        self.lst = lst
        for i in range(len(lst)):
            d = MetaWear(lst[i][0])
            d.connect()
            print("Connected to " + d.address + " over " + ("USB" if d.usb.is_connected else "BLE"))
            self.devices.append(d)
            
    def watch_start_config(self, frequency=100.0, range=16.0):
        for d in self.devices:
            libmetawear.mbl_mw_settings_set_connection_parameters(d.board, 7.5, 7.5, 0, 6000)
            sleep(1.5)
            libmetawear.mbl_mw_acc_set_odr(d.board, frequency)
            libmetawear.mbl_mw_acc_set_range(d.board, range)
            libmetawear.mbl_mw_acc_write_acceleration_config(d.board)
    
    def watch_start(self):
        self.states = []
        for i in range(len(self.devices)):
            #time stamp by initializing states
            s = State(self.devices[i],self.lst[i][1])
            self.states.append(s)
            # get acc and subscribe
            signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
            libmetawear.mbl_mw_datasignal_subscribe(signal, None, s.accCallback)
            # start acc
            libmetawear.mbl_mw_acc_enable_acceleration_sampling(s.device.board)
            libmetawear.mbl_mw_acc_start(s.device.board)
        
    def watching_for(self, sec):
        print("Logging data for %fs" %sec)
        sleep(sec)
    
    def watch_end(self):
        for s in self.states:
            libmetawear.mbl_mw_acc_stop(s.device.board)
            libmetawear.mbl_mw_acc_disable_acceleration_sampling(s.device.board)
            # unsubscribe
            signal = libmetawear.mbl_mw_acc_get_acceleration_data_signal(s.device.board)
            libmetawear.mbl_mw_datasignal_unsubscribe(signal)
            s.fh.close()

            
    # upload, requires session login and cwd to directory before hand. Plz close session manually later
    def upload(self, client, bucket = BUCKET):
        for s in self.states:
            # convert file to sequence of data using rx
            with open(s.fn, 'r') as f:
                data = rx.from_iterable(csv.reader(f)) \
                    .pipe(ops.map(lambda row: point_create(s.fn, row)))
                # create batch processing api
                write_api = client.write_api(write_options=WriteOptions(batch_size=50_000, flush_interval=10_000))
                # write and close
                write_api.write(bucket=bucket, record=data)
                write_api.close()
            # remove file
            os.remove(s.fn)

            
    def quit_reset(self):
        for d in self.states:
            if isinstance(d, State):
                d = d.device
            print("Resetting device")
            
            e = Event()
            d.on_disconnect = lambda status: e.set()
            print("Debug reset")
            libmetawear.mbl_mw_debug_reset(d.board)
            e.wait()
        