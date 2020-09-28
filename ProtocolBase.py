# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     ProtocolBase
   Description : 用于优化套接字发送协议 降低发送数据大小和加快处理速度（取代json
   Author :       Kinddle
   date：          2020/9/24
-------------------------------------------------
   Change Activity:
                   2020/9/24:
-------------------------------------------------
"""
__author__ = 'Kinddle'

import json

def Total_decode(data, datalink):
    pere=[False, False, False]
    if data[0:1]==b'T':
        rtn=Track_decode(data[1:])
        datalink["T"] = rtn
        pere[0]=True
    elif data[0:1]==b'R':
        rtn = Rate_decode(data[1:])
        datalink['R']= rtn
        pere[1]=True
    elif data[0:1]==b'F':
        rtn = Fall_decode(data[1:])
        datalink['F'] = rtn
        pere[2]=True
    else:
        rtn = "unknow data:{}".format(data)
    return rtn, pere

def Track_encode(confirmedroot):
    sendbin=b'T'
    sendbin += IntToBytes(len(confirmedroot), 1)  # 第二字节说明航迹数量
    for root in confirmedroot:
        tmppos = root.est[0:3, :].T.A
        sendbin+=IntToBytes(len(tmppos), 1)  # 用一个字节说明航迹中点的个数
        for point in tmppos:
            for xyz in point:
                sendbin+=IntToBytes(int(xyz*100) if -327.68 < xyz < 327.67
                                    else 32767 if xyz > 0 else -32768, 2)  # 坐标范围：-327.68~372.67（m)
    return sendbin + bytes(4)

def Track_decode(data):
    '''
    :param data:receive data without first bytes
    :return: dic
    '''
    tracknum = data[0]
    data = data[1:]
    tmptrack = []
    rtntracks = []
    for i in range(0, tracknum):
        pointnum = data[0]
        data = data[1:]
        for j in range(0, pointnum):
            tmptrack.append([BytesToInt(data[0:2])/100.0,
                             BytesToInt(data[2:4])/100.0,
                             BytesToInt(data[4:6])/100.0])
            data = data[6:]
        rtntracks.append(tmptrack)
        tmptrack = []
    assert data == bytes(4)
    #rtndic = rtntracks  # rtntracks->[[[1,2,3],[1,2,3],[3,2,1],[5,8,9],...], [], []...]
    return rtntracks


def Fall_encode(senddata):
    sendbin=b'F'
    sendbin += IntToBytes(senddata,1)
    return sendbin


def Fall_decode(data):
    data=data[0]
    # rtnstr = "无事发生" if data == 0 else "慢蹲坐下" if data == 1 else "跌倒！！！！！！！！！！！！！" if data == 2 else "NULL"
    return [data, 0]


def Rate_encode(vitalsign):
    sendbin=b'R'
    sendbin += IntToBytes(int(vitalsign["outputFilterBreathOut"]*10000), 4) +\
                IntToBytes(int(vitalsign['outputFilterHeartOut']*10000), 4) +\
                IntToBytes(int(vitalsign['breathingRateEst_FFT']*10), 4) +\
                IntToBytes(int(vitalsign['heartRateEst_FFT']*10), 4)
    #
    # senddic = {"type": "rate", "data": [vitalsign["outputFilterBreathOut"], vitalsign['outputFilterHeartOut'],
    #                                     vitalsign['breathingRateEst_FFT'], vitalsign['heartRateEst_FFT']]}
    # sendbin = json.dumps(senddic).encode()
    return sendbin


def Rate_decode(data):
    rtnlist = [BytesToInt(data[0:4])/10000.0, BytesToInt(data[4:8])/10000.0, BytesToInt(data[8:12])/10.0, BytesToInt(data[12:16])/10.0]
    return rtnlist

def IntToBytes(x:int, len:int=4):
    if not -2**(8*4-1)<x<2**(8*4-1):
        x = -2**(8*4-1)+1 if x < 0 else 2**(8*4-1)-1
    return x.to_bytes(len, byteorder="little", signed=True)

def BytesToInt(x:bytes):
    return int.from_bytes(x, byteorder="little", signed=True)

if __name__ == "__main__":
    a=15321
    b=a.to_bytes(4, byteorder='little', signed=True)
    c = int.from_bytes(b,byteorder="little", signed=True)
    print("a:{}\nb:{}\nc:{}\n".format(a,b,c))