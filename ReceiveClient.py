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

HOST = '127.0.0.1'
Port = 12000

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
