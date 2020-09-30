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

warnings.filterwarnings('ignore')

SystemEnv = 'Linux'
TrackHost = ("192.168.137.88", 12001)
FallHost = ("192.168.137.88", 12002)
TwoRate = ("192.168.137.88",12003)
ServerHost = ('192.168.137.1', 12000)
CLIPortID = [0, 2]
DataPortID = [1, 3]



try:
    trackandfall = Track3D.TrackandFall(addr_fall=FallHost, addr_track=TrackHost, addr_server=ServerHost,
                                        CLIPortID=CLIPortID[0], DataPortID=DataPortID[0], system=SystemEnv)
    trackandfall.start()
except Exception as z:
    print("fail to start module trackandfall")
    print(z)
else:
    print("success to start module trackandfall")

try:
    tworate = VitalSign.TwoRate(addr_2Rate=TwoRate, addr_server=ServerHost,
                                CLIPortID=CLIPortID[1], DataPortID=DataPortID[1], system=SystemEnv)
    tworate.start()
except Exception as z:
    print("fail to start module tworate")
    print(z)
else:
    print("success to start module tworate")

try:
    input(">>")
except KeyboardInterrupt:
    print("\nExit successfully!")

del tworate
del trackandfall