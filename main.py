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

SystemEnv = 'Windows'
TrackHost = ("127.0.0.1", 12001)
FallHost = ("127.0.0.1", 12002)
TwoRate = ("127.0.0.1",12003)
ServerHost = ('127.0.0.1', 12000)
CLIPortID = [11, 10]
DataPortID = [12, 9]



try:
    trackandfall = Track3D.TrackandFall(addr_fall=FallHost, addr_track=TrackHost, addr_server=ServerHost,
                                        CLIPortID=CLIPortID[0], DataPortID=DataPortID[0], system=SystemEnv)
    trackandfall.start()
except Exception as z:
    print("fail to start module trackandfall")
else:
    print("success to start module trackandfall")

try:
    tworate = VitalSign.TwoRate(addr_2Rate=TwoRate, addr_server=ServerHost,
                                CLIPortID=CLIPortID[1], DataPortID=DataPortID[1], system=SystemEnv)
    tworate.start()
except Exception as z:
    print("fail to start module tworate")
else:
    print("success to start module tworate")

try:
    while(True):
        pass
except KeyboardInterrupt:
    print("\nExit successfully!")