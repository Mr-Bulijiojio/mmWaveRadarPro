# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     main
   Description :
   Author :       Kinddle
   date：          2020/9/22
-------------------------------------------------
   Change Activity:
                   2020/9/22:
-------------------------------------------------
"""
__author__ = 'Kinddle'

import TrackandFall as Track3D
import VitalSignIWR1642 as VitalSign
import warnings
import logging
import os
import sys, getopt
warnings.filterwarnings('ignore')

SystemEnv = 'Linux'
TrackHost = ("192.168.137.88", 12001)
FallHost = ("192.168.137.88", 12002)
TwoRate = ("192.168.137.88", 12003)
ServerHost = ('192.168.137.1', 12000)
CLIPortID = [0, 2]
DataPortID = [1, 3]
DebugMode = False

opts, args = getopt.getopt(sys.argv[1:], "d")
for op, value in opts:
    if op == "-d":
        DebugMode = True

absaddr = os.path.abspath(os.path.dirname(__file__))
if not os.path.isdir(os.path.join(absaddr, "logger")):
    os.mkdir(os.path.join(absaddr, "logger"))

dellist = os.listdir(os.path.join(absaddr, "logger"))
for i in dellist:
    filepath = os.path.join(absaddr, 'logger', i)
    assert os.path.isfile(filepath)
    os.remove(filepath)

MyFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
Handler_main = logging.FileHandler(absaddr+"/logger/main_warning.log")
Handler_main.setLevel(logging.DEBUG)
Handler_main.setFormatter(MyFormatter)

logger_main = logging.getLogger(__name__)
logger_main.setLevel(level=logging.INFO)
logger_main.addHandler(Handler_main)

Handler_track_warning = logging.FileHandler(absaddr+"/logger/Track_warning.log")
Handler_track_warning.setLevel(logging.WARNING)
Handler_track_warning.setFormatter(MyFormatter)

Handler_track_debug = logging.FileHandler(absaddr+"/logger/Track_debug.log")
Handler_track_debug.setLevel(logging.DEBUG)
Handler_track_debug.setFormatter(MyFormatter)

logger_track = logging.getLogger("{}.track".format(__name__))
logger_track.setLevel(level=logging.DEBUG if DebugMode else logging.WARNING)
logger_track.addHandler(Handler_track_warning)
logger_track.addHandler(Handler_track_debug)

Handler_rate_warning = logging.FileHandler(absaddr+"/logger/Rate_warning.log")
Handler_rate_warning.setLevel(logging.WARNING)
Handler_rate_warning.setFormatter(MyFormatter)

Handler_rate_debug = logging.FileHandler(absaddr+"/logger/Rate_debug.log")
Handler_rate_debug.setLevel(logging.DEBUG)
Handler_rate_debug.setFormatter(MyFormatter)

logger_rate = logging.getLogger("{}.rate".format(__name__))
logger_rate.setLevel(level=logging.DEBUG if DebugMode else logging.WARNING)
logger_rate.addHandler(Handler_rate_warning)
logger_rate.addHandler(Handler_rate_debug)

try:
    trackandfall = Track3D.TrackandFall(addr_fall=FallHost, addr_track=TrackHost, addr_server=ServerHost,
                                        logger=logger_track,
                                        CLIPortID=CLIPortID[0], DataPortID=DataPortID[0], system=SystemEnv)
    trackandfall.start()
except Exception as z:
    logger_main.error("fail to start module 'trackandfall'\n{}".format(z))
    # print("fail to start module trackandfall")
    # print(z)
else:
    logger_main.info("success to start module trackandfall")
    # print("success to start module trackandfall")

try:
    tworate = VitalSign.TwoRate(addr_2Rate=TwoRate, addr_server=ServerHost,
                                logger=logger_rate, SCID=4,
                                CLIPortID=CLIPortID[1], DataPortID=DataPortID[1], system=SystemEnv)
    tworate.start()
except Exception as z:
    logger_main.error("fail to start module tworate:\n{}".format(z))
    # print("fail to start module tworate")
    # print(z)
else:
    logger_main.info("success to start module two")
    # print("success to start module tworate")

try:
    input(">>")
except KeyboardInterrupt:
    logger_main.info("success to start module two")

del tworate
del trackandfall