# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     ReceiveClient
   Description : 用于测试其他三个套接字是否运行良好。基于此可以写图形化界面
   Author :       Kinddle
   date：          2020/9/15
-------------------------------------------------
   Change Activity:
                   2020/9/15:
-------------------------------------------------
"""
__author__ = 'Kinddle'
import socket
import ProtocolBase as PB
import GUIpyqt
from PyQt5 import QtCore, QtGui, QtWidgets
import sys

HOST = '127.0.0.1'
Port = 12000
app = QtWidgets.QApplication(sys.argv)
datainit = {"T": [[[0, 0, 0], [1, 1, 1], [1, 2, 1]], [[3, 3, 3], [3, 3, 2], [3, 2, 1], [3, 3, 3]]],
                'R': [0.45, 0.68, 60, 120],
                'F': 0}
gui = GUIpyqt.MainUi(datainit)
gui.show()
with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
    # s.setblocking(False)
    s.bind((HOST, Port))
    print("ready to get data")
    while(True):
        data, addr = s.recvfrom(65536)
        # if addr == ("127.0.0.1", 12002):
        #     continue
        print("receive data from addr:{}".format(addr))
        get = PB.Total_decode(data)
        print(get)
        print("len of rcv: {}".format(len(data)))
        print("*******************************************************")



sys.exit(app.exec_())
