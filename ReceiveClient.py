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
import threading


HOST_S = '192.168.137.1'
HOST_C = '192.168.137.88'
Port = 12000

datalink = {"T": [], 'R': [0, 0, 0, 0], 'F': [0, 0]}  # 初始化数据内容

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((HOST_S, Port))
addrdic = {'T': (HOST_C, 12001), 'R': (HOST_C, 12003), 'F': (HOST_C, 12002)}


def cmdsend(dst: str, cmddata: str):
    if dst == "T" or dst == 'R' or dst == 'F':
        s.sendto(cmddata.encode() + bytes(1), addrdic[dst])

    elif dst == 'C':
        if cmddata == 'Exit':
            raise KeyboardInterrupt
    else:
        pass
    print('send {} to {}'.format(cmddata, addrdic[dst]))

def socketget(gui):
    # with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # s.setblocking(False)
    try:
        print("ready to get data")
        s.setblocking(False)
        while(True):
            try:
                data, addr = s.recvfrom(65536)

            except Exception:
                continue
            print("receive data from addr:{}".format(addr))
            # 更新目的地址
            addrdic[data[0:1].decode()] = addr
            if len(data) == 1:
                continue
            get, pere = PB.Total_decode(data, datalink)

            print(get)
            print("len of rcv: {}".format(len(data)))
            print("*******************************************************")
            gui.refresh(*pere)
    except KeyboardInterrupt:
        print('stop to get data')
        s.close()


app = QtWidgets.QApplication(sys.argv)

gui = GUIpyqt.MainUi(datalink, cmdsend)
gui.show()
threads = threading.Thread(target=socketget, args=(gui,))


threads.start()

sys.exit(app.exec_())





