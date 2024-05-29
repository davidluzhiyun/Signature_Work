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
from datetime import timedelta
from influxdb_client import *
from ftplib import FTP_TLS

BUCKET = "DefaultBucket"
MEASUREMENT = "Test1"
LOCATION = "GymCC"

from queue import Queue


class State:
    # init state
    def __init__(self, device, equipment, queue):
        self.device = device
        assert isinstance(self.device, MetaWear)
        self.equipment = equipment
        self.samples = 0
        self.accCallback = FnVoid_VoidP_DataP(self.acc_data_handler)
        self.queue = queue

    # acc callback function
    def acc_data_handler(self, ctx, data):
        self.samples += 1
        line = "%d, %s\n" % (data.contents.epoch, parse_value(data))
        equipment = self.equipment
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
        self.queue.put(point)
        
class Monitor:

    #example of lst: [[mac1,equipment name1],[mac2,equipment name2],.....]
    #connect and initialize
    def __init__(self, lst):
        self.buffer = None
        self.states = []
        self.devices = []
        self.lst = lst
        self.queue = Queue()
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
            s = State(self.devices[i],self.lst[i][1],self.queue)
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


    def from_queue(self):
        if not self.queue.empty():
            self.buffer = self.queue.get()
        return self.buffer

    def start_upload(self,client, bucket=BUCKET):
        data = rx \
            .interval(period=timedelta(seconds=1/600)) \
            .pipe(ops.map(lambda t: self.from_queue()),
                  ops.distinct_until_changed())
        client.write(bucket=BUCKET,record=data)

            
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
        