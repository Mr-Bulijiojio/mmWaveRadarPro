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
import logging
import os
import time

HOST_S = '192.168.137.1'
HOST_C = '192.168.137.88'
Port = 12000

datalink = {"T": [], 'R': [0, 0, 0, 0], 'F': [0, 0]}  # 初始化数据内容

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.bind((HOST_S, Port))
addrdic = {'T': (HOST_C, 12001), 'R': (HOST_C, 12003), 'F': (HOST_C, 12002)}
absaddr = os.path.abspath(os.path.dirname(__file__))

dellist = os.listdir(os.path.join(absaddr, "logger"))
for i in dellist:
    filepath = os.path.join(absaddr, 'logger', i)
    assert os.path.isfile(filepath)
    os.remove(filepath)

MyFormatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

Handler_GUI_Debug = logging.FileHandler(os.path.join(absaddr, "logger", "GUI_debug.log"))
Handler_GUI_Debug.setLevel(logging.DEBUG)
Handler_GUI_Debug.setFormatter(MyFormatter)
Handler_GUI_warning = logging.FileHandler(os.path.join(absaddr, "logger", "GUI_info.log"))
Handler_GUI_warning.setLevel(logging.WARNING)
Handler_GUI_warning.setFormatter(MyFormatter)

logger_GUI = logging.getLogger(__name__+'.gui')
logger_GUI.setLevel(level=logging.DEBUG)
logger_GUI.addHandler(Handler_GUI_Debug)
logger_GUI.addHandler(Handler_GUI_warning)

Handler_rcv = logging.FileHandler(os.path.join(absaddr, "logger", "Rcv_info.log"))
Handler_rcv.setLevel(logging.DEBUG)
Handler_rcv.setFormatter(MyFormatter)

logger_rcv = logging.getLogger(__name__)
logger_rcv.setLevel(level=logging.DEBUG)
logger_rcv.addHandler(Handler_rcv)

def cmdsend(dst: str, cmddata: str):
    if dst == "T" or dst == 'R' or dst == 'F':
        s.sendto(cmddata.encode() + bytes(1), addrdic[dst])

    elif dst == 'C':
        if cmddata == 'Exit':
            raise KeyboardInterrupt
    else:
        pass
    print('send {} to {}'.format(cmddata, addrdic[dst]))
    logger_rcv.info('send {} to {}'.format(cmddata, addrdic[dst]))

def test_call_number():
    # number是个列表，直接在这里天上你想要骚扰的号码即可
    number = 19981480981
    # 直接一个for循环，循环号码
    # 使用adb打电话

    call = os.popen('adb shell am start -a android.intent.action.CALL -d tel:%s' % number)
    # 这里的sleep时间基本就是你想让通话保持的时间了
    print(call)
    time.sleep(30)
    # 挂断电话
    end = os.popen('adb shell input keyevent 6')  # code6是挂断
    print(end)
    time.sleep(4)

def socketget(gui):
    # with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        # s.setblocking(False)
    try:
        print("ready to get data")
        logger_GUI.info("ready to get data")
        s.setblocking(False)
        while(True):
            try:
                data, addr = s.recvfrom(65536)

            except Exception:
                continue
            # 更新目的地址
            addrdic[data[0:1].decode()] = addr
            if len(data) == 1:
                continue
            get, pere = PB.Total_decode(data, datalink)
            logger_rcv.debug("receive data from addr:{}  len of rcv: {} {} ".format(addr, len(data), get))

            gui.refresh(*pere)
    except KeyboardInterrupt:
        logger_rcv.info('stop to get data')
        s.close()


app = QtWidgets.QApplication(sys.argv)

gui = GUIpyqt.MainUi(datalink, cmdsend, logger_GUI, test_call_number)
gui.show()
threads = threading.Thread(target=socketget, args=(gui,))


threads.start()

sys.exit(app.exec_())





