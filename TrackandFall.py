# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     TrackandFall
   Description :
   Author :       Kinddle
   date：          2020/9/23
-------------------------------------------------
   Change Activity:
                   2020/9/23:
-------------------------------------------------
"""
__author__ = 'Kinddle'

import serial
import time
import numpy as np
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui
import pyqtgraph.opengl as gl
from IWR.MOT3D import *
import numpy
from sklearn.cluster import dbscan
import pandas

import MLP.MLP_forward as MLP_forward
import MLP.MLP_backward as MLP_backward
from MLP.MLP_app import *
import tensorflow as tf
import ProtocolBase as PB

import os
import threading
import socket
import json


class TrackandFall(threading.Thread):
    test_count_try =0
    test_count_dataok = 0
    test_count_fallok = 0
    test_count_trackok = 0
    def __init__(self, addr_track=("127.0.0.1", 12001), addr_fall=("127.0.0.1", 12002), addr_server=("127.0.0.1", 12000),
                 CLIPortID=4, DataPortID=5, system="Linux",
                 configFileName='profile_iwr6843_ods_3d.cfg'):
        super().__init__(daemon=True)
        self.CLIport=None
        self.Dataport=None
        self.byteBuffer = np.zeros(2 ** 15, dtype='uint8')
        self.byteBufferLength = 0
        self.testroot = []
        self.confirmedroot = []
        self.Z_k_prev = numpy.mat([])
        self.frameData = np.array([0, 0, 0])
        self.system = system

        self.fallOK = True
        self.trackOK = True
        self.step = 0

        self.addr_track = addr_track
        self.addr_fall = addr_fall
        self.addr_server = addr_server

        if system != "Linux" and system != "Windows":
            raise SystemExit("only support Linux and Windows Com")
        self.serialConfig(configFileName, CLIPortID, DataPortID, system)  # Open the serial ports

        try:
            self.parseConfigFile(configFileName)
        except Exception as err:
            print("something wrong in config file please check '{}'".format(configFileName))
            print("There is the error report:\n{}\n****************************".format(err))
            return
        print("open TrackModule module success")


    def serialConfig(self, configFileName, CPID, DPID, system="Linux"):
        # global CLIport
        # global Dataport
        # # Open the serial ports for the configuration and the data ports

        # Raspberry Linux
        if system == "Linux":
            self.CLIport = serial.Serial('/dev/ttyACM%d' % CPID, 115200)
            self.Dataport = serial.Serial('/dev/ttyACM%d' % DPID, 921600)

        # Windows
        elif system == "Windows":
            self.CLIport = serial.Serial('COM%d' % CPID, 115200)
            self.Dataport = serial.Serial('COM%d' % DPID, 921600)

        # Read the configuration file and send it to the board
        config = [line.rstrip('\r\n') for line in open(configFileName)]
        for i in config:
            print(i)
            # if i[0] != '%':
            self.CLIport.write((i + '\n').encode())
            time.sleep(0.01)

        # return self.CLIport, self.Dataport

    def parseConfigFile(self, configFileName):
        configParameters = {}  # Initialize an empty dictionary to store the configuration parameters

        # Read the configuration file and send it to the board
        config = [line.rstrip('\r\n') for line in open(configFileName)]
        chirpEndIdx = None
        chirpStartIdx = None
        numLoops = None
        numTxAnt = None
        numAdcSamplesRoundTo2 = None
        digOutSampleRate = None
        freqSlopeConst = None
        numAdcSamples = None
        startFreq = None
        idleTime = None
        rampEndTime = None

        for i in config:

            # Split the line
            splitWords = i.split(" ")

            # Hard code the number of antennas, change if other configuration is used
            numRxAnt = 4
            numTxAnt = 3

            # Get the information about the profile configuration
            if "profileCfg" in splitWords[0]:
                startFreq = int(float(splitWords[2]))
                idleTime = int(splitWords[3])
                rampEndTime = float(splitWords[5])
                freqSlopeConst = float(splitWords[8])
                numAdcSamples = int(splitWords[10])
                numAdcSamplesRoundTo2 = 1

                while numAdcSamples > numAdcSamplesRoundTo2:
                    numAdcSamplesRoundTo2 = numAdcSamplesRoundTo2 * 2

                digOutSampleRate = int(splitWords[11])

            # Get the information about the frame configuration
            elif "frameCfg" in splitWords[0]:
                chirpStartIdx = int(splitWords[1])
                chirpEndIdx = int(splitWords[2])
                numLoops = int(splitWords[3])
                numFrames = int(splitWords[4])
                framePeriodicity = float(splitWords[5])

        # Combine the read data to obtain the configuration parameters
        numChirpsPerFrame = (chirpEndIdx - chirpStartIdx + 1) * numLoops
        configParameters["numDopplerBins"] = numChirpsPerFrame / numTxAnt
        configParameters["numRangeBins"] = numAdcSamplesRoundTo2
        configParameters["rangeResolutionMeters"] = (3e8 * digOutSampleRate * 1e3) / (
                2 * freqSlopeConst * 1e12 * numAdcSamples)
        configParameters["rangeIdxToMeters"] = (3e8 * digOutSampleRate * 1e3) / (
                2 * freqSlopeConst * 1e12 * configParameters["numRangeBins"])
        configParameters["dopplerResolutionMps"] = 3e8 / (
                2 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * configParameters["numDopplerBins"] * numTxAnt)
        configParameters["maxRange"] = (300 * 0.9 * digOutSampleRate) / (2 * freqSlopeConst * 1e3)
        configParameters["maxVelocity"] = 3e8 / (4 * startFreq * 1e9 * (idleTime + rampEndTime) * 1e-6 * numTxAnt)

        self.configParameters = configParameters

    def readAndParseData(self, Dataport, configParameters):
        # byteBuffer = self.byteBuffer
        # byteBufferLength = self.byteBufferLength

        # Constants
        OBJ_STRUCT_SIZE_BYTES = 12
        BYTE_VEC_ACC_MAX_SIZE = 2 ** 15
        MMWDEMO_UART_MSG_DETECTED_POINTS = 1
        MMWDEMO_UART_MSG_RANGE_PROFILE = 2
        maxBufferSize = 2 ** 15
        tlvHeaderLengthInBytes = 8
        pointLengthInBytes = 16
        magicWord = [2, 1, 4, 3, 6, 5, 8, 7]

        # Initialize variables
        magicOK = 0  # Checks if magic number has been read
        dataOK = 0  # Checks if the data has been read correctly
        frameNumber = 0
        detObj = {}

        readBuffer = Dataport.read(Dataport.in_waiting)
        byteVec = np.frombuffer(readBuffer, dtype='uint8')
        byteCount = len(byteVec)

        # Check that the buffer is not full, and then add the data to the buffer
        if (self.byteBufferLength + byteCount) < maxBufferSize:
            self.byteBuffer[self.byteBufferLength:(self.byteBufferLength + byteCount)] = byteVec[0:byteCount]
            self.byteBufferLength = self.byteBufferLength + byteCount

        # Check that the buffer has some data
        if self.byteBufferLength > 16:

            # Check for all possible locations of the magic word
            possibleLocs = np.where(self.byteBuffer == magicWord[0])[0]

            # Confirm that is the beginning of the magic word and store the index in startIdx
            startIdx = []
            for loc in possibleLocs:
                check = self.byteBuffer[loc:loc + 8]
                if np.all(check == magicWord):
                    startIdx.append(loc)

            # Check that startIdx is not empty
            if startIdx:

                # Remove the data before the first start index
                if 0 < startIdx[0] < self.byteBufferLength:
                    self.byteBuffer[:self.byteBufferLength - startIdx[0]] = self.byteBuffer[startIdx[0]:self.byteBufferLength]
                    self.byteBuffer[self.byteBufferLength - startIdx[0]:] = np.zeros(
                        len(self.byteBuffer[self.byteBufferLength - startIdx[0]:]),
                        dtype='uint8')
                    self.byteBufferLength = self.byteBufferLength - startIdx[0]

                # Check that there have no errors with the byte buffer length
                if self.byteBufferLength < 0:
                    self.byteBufferLength = 0

                # Read the total packet length
                totalPacketLen = int.from_bytes(self.byteBuffer[12:12 + 4], byteorder='little')

                # Check that all the packet has been read
                if (self.byteBufferLength >= totalPacketLen) and (self.byteBufferLength != 0):
                    magicOK = 1

        # If magicOK is equal to 1 then process the message
        if magicOK:

            # Initialize the pointer index
            idX = 0

            # Read the header
            magicNumber = self.byteBuffer[idX:idX + 8]
            idX += 8
            version = format(int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little'), 'x')
            idX += 4
            totalPacketLen = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
            idX += 4
            platform = format(int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little'), 'x')
            idX += 4
            frameNumber = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
            idX += 4
            timeCpuCycles = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
            idX += 4
            numDetectedObj = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
            idX += 4
            numTLVs = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
            idX += 4
            subFrameNumber = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
            idX += 4

            # Read the TLV messages
            for tlvIdx in range(numTLVs):

                # Check the header of the TLV message
                tlv_type = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
                idX += 4
                tlv_length = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
                idX += 4

                # Read the data depending on the TLV message
                if tlv_type == MMWDEMO_UART_MSG_DETECTED_POINTS:

                    # Initialize the arrays
                    x = np.zeros(numDetectedObj, dtype=np.float32)
                    y = np.zeros(numDetectedObj, dtype=np.float32)
                    z = np.zeros(numDetectedObj, dtype=np.float32)
                    velocity = np.zeros(numDetectedObj, dtype=np.float32)

                    for objectNum in range(numDetectedObj):
                        # Read the data for each object
                        x[objectNum] = self.byteBuffer[idX:idX + 4].view(dtype=np.float32)
                        idX += 4
                        y[objectNum] = self.byteBuffer[idX:idX + 4].view(dtype=np.float32)
                        idX += 4
                        z[objectNum] = self.byteBuffer[idX:idX + 4].view(dtype=np.float32)
                        idX += 4
                        velocity[objectNum] = self.byteBuffer[idX:idX + 4].view(dtype=np.float32)
                        idX += 4

                    # Store the data in the detObj dictionary
                    detObj = {"numObj": numDetectedObj, "x": x, "y": y, "z": z, "velocity": velocity}
                    dataOK = 1

            # Remove already processed data
            if 0 < idX < self.byteBufferLength:
                shiftSize = totalPacketLen

                self.byteBuffer[:self.byteBufferLength - shiftSize] = self.byteBuffer[shiftSize:self.byteBufferLength]
                self.byteBuffer[self.byteBufferLength - shiftSize:] = np.zeros(len(self.byteBuffer[self.byteBufferLength - shiftSize:]),
                                                                     dtype='uint8')
                self.byteBufferLength = self.byteBufferLength - shiftSize

                # Check that there are no errors with the buffer length
                if self.byteBufferLength < 0:
                    self.byteBufferLength = 0

        return dataOK, frameNumber, detObj

    def update_Track(self, Z_k):

            self.confirmedroot, self.testroot, self.Z_k_prev = MOT(Z_k, self.Z_k_prev, self.confirmedroot, self.testroot)
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM)as s:

                sendbin = PB.Track_encode(self.confirmedroot)
                #print('len of send' + str(len(sendbin)))
                s.bind(self.addr_track)
                s.sendto(sendbin, self.addr_server)
            self.trackOK = True



    def update_fall(self, sess, sessx, sessy, data):
        '''
        更新数据
        :return:dataOK tmp
        '''

        self.frameData = np.vstack((self.frameData, data))
        if self.frameData.shape[0] == 10:  # 维护的cache大小
            self.step += 1
            if self.step == 5:
                testData = self.frameData.reshape(1, 30)
                for j in range(30):
                    if testData[0][j] == 0:
                        testData[0][j] = -0.5
                y_out = sess.run(sessy, feed_dict={sessx: testData})
                if y_out[0] < 0.05:
                    print("\033[1;31;40m摔倒{}".format(y_out[0]))
                    senddata=2
                elif y_out[0] < 0.2 and y_out[0] > 0.05:
                    print("\033[0;32;46m坐下或慢蹲{}".format(y_out[0]))
                    senddata=1
                else:
                    print("\033[0;32;46m无事发生{}".format(y_out[0]))
                    senddata=0
                # print(y_out)
                self.step = 0
                with socket.socket(socket.AF_INET, socket.SOCK_DGRAM)as s:

                    sendbin = PB.Fall_encode(senddata ,max(y_out[0]))
                    #print('len of send' + str(len(sendbin)))

                    s.bind(self.addr_fall)
                    s.sendto(sendbin, self.addr_server)
            self.frameData = np.delete(self.frameData, 0, axis=0)

        self.fallOK = True
    def __del__(self):
        print("try:{}\ndataok:{}\ntrackok:{}\nfallok:{}\n".format(self.test_count_try, self.test_count_dataok, self.test_count_trackok, self.test_count_fallok))

    # ------------------------------main----------------------------
    def run(self):
        # frameData = {}
        # currentIndex = 0
        with tf.Graph().as_default() as tg:
            sessx = tf.placeholder(tf.float32, [None, MLP_forward.INPUT_NODE])
            sessy = MLP_forward.forward(sessx, None)

            variable_averages = tf.train.ExponentialMovingAverage(MLP_backward.MOVING_AVERAGE_DECAY)
            variables_to_restore = variable_averages.variables_to_restore()
            saver = tf.train.Saver(variables_to_restore)

            with tf.Session() as sess:
                abspath=os.path.abspath(os.path.dirname(__file__))
                checkpoint = abspath + ('/model' if self.system == "Linux" else r'\model')
                print(checkpoint)
                ckpt = tf.train.get_checkpoint_state(checkpoint if True else
                                                     "/home/ai-box/Desktop/mmWaveRadar/Data/model")
                                                        # MLP.MLP_backward.MODEL_SAVE_PATH

                if ckpt and ckpt.model_checkpoint_path:
                    saver.restore(sess, ckpt.model_checkpoint_path)
                    print("**MainLoop************************************************************")
                    while True:
                        try:
                            # Update the data and check if the data is okay
                            dataOk, frameNumber, detObj = self.readAndParseData(self.Dataport, self.configParameters)
                            self.test_count_try+=1
                            if dataOk:
                                self.test_count_dataok +=1
                                x = detObj["x"]
                                y = detObj["y"]
                                z = detObj["z"]
                                tmp = np.array([[0, 0, 0]])
                                if len(x) != 0:
                                    core_samples, cluster_ids = dbscan(np.vstack((x, y, z)).T, eps=0.3, min_samples=3)
                                    df = pandas.DataFrame(np.c_[np.vstack((x, y, z)).T, cluster_ids],
                                                          columns=['x', 'y', 'z', 'cluster_id'])
                                    df = df[df.cluster_id != -1]
                                    count = df['cluster_id'].value_counts()

                                    x = []
                                    y = []
                                    z = []
                                    if count.shape[0] >= 1:
                                        for i in range(0, count.shape[0]):
                                            df1 = df[df.cluster_id == i]
                                            mean = np.mean([df1['x'], df1['y'], df1['z']], 1)
                                            x.append(mean[0])
                                            y.append(mean[1])
                                            z.append(mean[2])
                                    if count.shape[0] >= 1 and count[0] >= 5:
                                        tmp = np.vstack((x[0], y[0], z[0])).T
                                Z_k = numpy.mat([x, y, z])

                                if self.fallOK:
                                    self.fallOK = False
                                    self.test_count_fallok +=1
                                    tmp_thread_fall = threading.Thread(target=self.update_fall,
                                                                       args=(sess, sessx, sessy, tmp[0]))
                                    tmp_thread_fall.start()
                                    # self.update_fall(sess, sessx, sessy, tmp[0])
                                if self.trackOK:
                                    self.trackOK = False
                                    self.test_count_trackok +=1
                                    tmp_thread_track = threading.Thread(target=self.update_Track,
                                                                        args=(Z_k,))
                                    tmp_thread_track.start()
                                    # self.update_Track(Z_k)
                            # self.update(sess, x, y)

                            time.sleep(0.01)
                        # Stop the program and close everything if Ctrl + c is pressed
                        except KeyboardInterrupt:
                            self.CLIport.write(('sensorStop\n').encode())
                            print('sensorStop\n')
                            self.CLIport.close()
                            self.Dataport.close()
                            print(self.test_count_dataok)
                            print(self.test_count_fallok)
                            print(self.test_count_trackok)
                            break

                else:
                    print("No checkpoint file found")
        # while True:
        #     try:
        #         # Update the data and check if the data is okay
        #         dataOk = 0
        #         dataOk, frameNumber, detObj = self.readAndParseData(self.Dataport, self.configParameters)
        #         dataOk = self.update_Track(dataOk, frameNumber, detObj)
        #
        #         # if dataOk:
        #         #     # Store the current frame into frameData
        #         #     frameData[currentIndex] = detObj
        #         #     currentIndex += 0
        #
        #         time.sleep(0.01)  # Sampling frequency of 20 Hz

            # # Stop the program and close everything if Ctrl + c is pressed
            # except KeyboardInterrupt:
            #     self.CLIport.write(('sensorStop\n').encode())
            #     print('sensorStop\n')
            #     self.CLIport.close()
            #     self.Dataport.close()
            #     break

if __name__ == "__main__":
    tst = TrackandFall(CLIPortID=11, DataPortID=12, system="Windows")
    tst.run()



