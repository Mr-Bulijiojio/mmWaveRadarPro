#
# File:         通过串口读取IWR1642平台的处理得到的心跳与呼吸的波形速率
# Author:       UESTC Yu Xuyao
# Email:        yxy19991102@163.com
# Acknowledge:  串口读取以及缓冲区的维护数据解析由github用户 Yi Zhang (zhangyibupt@163.com) 完成，感谢!!!
#

import serial
import time
import numpy as np
import struct
# import pyqtgraph as pg
# from pyqtgraph.Qt import QtGui
# from sklearn.cluster import dbscan
# import pandas
import ProtocolBase as PB

import threading
import socket

class TwoRate(threading.Thread):
    test_count_dataok = 0
    test_count_try = 0
    def __init__(self, addr_2Rate=("127.0.0.1", 12003), addr_server=("127.0.0.1", 12000),
                 CLIPortID=10, DataPortID=9, system="Linux",
                 configFileName='xwr1642_profile_VitalSigns_20fps_Front.cfg'):
        super().__init__(daemon=True)
        self.CLIport = None
        self.Dataport = None
        self.byteBuffer = np.zeros(2 ** 15, dtype='uint8')
        self.byteBufferLength = 0
        self.Breathsignal = list(range(0, 250))
        self.Heartbeatsignal = list(range(0, 250))
        self.configParameters = {}
        self.detObj = {}
        self.breathOK = True
        self.ComportOK = False
        self.addr_2Rate = addr_2Rate
        self.addr_server = addr_server
        self.socket_Rate = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_Rate.bind(self.addr_2Rate)
        self.socket_Rate.setblocking(False)
        self.socket_Rate.sendto(b'R',addr_server)
        self.system = system

        self.start_conf = [configFileName, CLIPortID, DataPortID]
        self._auto_start(*self.start_conf)

        # self.system = system
        # if system != "Linux" and system != "Windows":
        #     raise SystemExit("only support Linux and Windows Com")
        # self.serialConfig(configFileName, CLIPortID, DataPortID, system)  # Open the serial ports
        # try:
        #     self.parseConfigFile(configFileName)
        # except Exception as err:
        #     print("something wrong in config file please check '{}'".format(configFileName))
        #     print("There is the error report:\n{}\n****************************".format(err))
        #     return
        # print("open TwoRate module success")
    def _auto_start(self, configFileName, CLIPortID, DataPortID):
        system = self.system
        if system != "Linux" and system != "Windows":
            raise SystemExit("only support Linux and Windows Com")

        try:
            self.serialConfig(configFileName, CLIPortID, DataPortID, system)  # Open the serial ports
        except Exception as err:
            print('open Com Fail...')
            print('There is the error report:\n{}\n****************************'.format(err))
            return
        try:
            self.parseConfigFile(configFileName)
        except Exception as err:
            print("something wrong in config file please check '{}'".format(configFileName))
            print("There is the error report:\n{}\n****************************".format(err))
            return
        print("Open VitalSign module successfully")
        self.ComportOK = True

    def _auto_close(self):
        if self.CLIport:
            self.CLIport.write(('sensorStop\n').encode())
            print('sensorStop\n')
            self.CLIport.close()
        if self.Dataport:
            self.Dataport.close()
        self.ComportOK = False

    def serialConfig(self, configFileName, CPID, DPID, system="Linux"):
        # global CLIport
        # global Dataport
        # # Open the serial ports for the configuration and the data ports

        # Raspberry Linux
        if system == "Linux":
            self.CLIport = serial.Serial('/dev/My_Serial%d' % CPID, 115200)
            self.Dataport = serial.Serial('/dev/My_Serial%d' % DPID, 921600)

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
            time.sleep(1)

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

    def ParseCmdFrame(self, data, so):
        if data == b'Exit\x00':  # 完全退出 包括套接字等
            raise KeyboardInterrupt('服务器指令退出')
        elif data == b'Close\x00':
            if self.ComportOK:
                self._auto_close()
        elif data == b"Start\x00":
            if not self.ComportOK:
                self._auto_start(*self.start_conf)
        else:
            print('unknown cmd...')

    def readAndParseData(self, Dataport, configParameters):
        # global byteBuffer, byteBufferLength

        # Constants
        OBJ_STRUCT_SIZE_BYTES = 12
        BYTE_VEC_ACC_MAX_SIZE = 2 ** 15
        MMWDEMO_UART_MSG_DETECTED_POINTS = 1
        MMWDEMO_UART_MSG_RANGE_PROFILE = 2
        MMWDEMO_UART_MSG_VITALSIGN = 6
        maxBufferSize = 2 ** 15
        tlvHeaderLengthInBytes = 8
        pointLengthInBytes = 16
        magicWord = [2, 1, 4, 3, 6, 5, 8, 7]

        # Initialize variables
        magicOK = 0  # Checks if magic number has been read
        dataOK = 0  # Checks if the data has been read correctly
        frameNumber = 0
        vitalsign = {}

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
                    print('byteBufferLength')
                    self.byteBufferLength = 0
                if self.byteBufferLength < 16:
                    return dataOK,None,None
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
            reserved = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
            idX += 4

            # Read the TLV messages
            for tlvIdx in range(numTLVs):

                # Check the header of the TLV message
                tlv_type = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
                idX += 4
                tlv_length = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
                idX += 4

                # Read the data depending on the TLV message
                if tlv_type == MMWDEMO_UART_MSG_VITALSIGN:
                    # vitalsign["rangeBinIndexMax"] = int.from_bytes(self.byteBuffer[idX:idX + 2], byteorder='little')
                    idX += 2
                    # vitalsign["rangeBinIndexPhase"] = int.from_bytes(self.byteBuffer[idX:idX + 2], byteorder='little')
                    idX += 2
                    # vitalsign["maxVal"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["processingCyclesOut"] = int.from_bytes(self.byteBuffer[idX:idX + 4], byteorder='little')
                    idX += 4
                    # vitalsign["rangeBinStartIndex"] = int.from_bytes(self.byteBuffer[idX:idX + 2], byteorder='little')
                    idX += 2
                    # vitalsign["rangeBinEndIndex"] = int.from_bytes(self.byteBuffer[idX:idX + 2], byteorder='little')
                    idX += 2
                    # vitalsign["unwrapPhasePeak_mm"] = self.byteBuffer[idX:idX + 4].view(dtype=np.float32)
                    idX += 4
                    vitalsign["outputFilterBreathOut"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    vitalsign["outputFilterHeartOut"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    vitalsign["heartRateEst_FFT"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["heartRateEst_FFT_4Hz"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0] / 2
                    idX += 4
                    # vitalsign["heartRateEst_xCorr"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["heartRateEst_peakCount"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    vitalsign["breathingRateEst_FFT"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["breathingRateEst_xCorr"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["breathingRateEst_peakCount"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["confidenceMetricBreathOut"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["confidenceMetricBreathOut_xCorr"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["confidenceMetricHeartOut"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["confidenceMetricHeartOut_4Hz"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["confidenceMetricHeartOut_xCorr"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["sumEnergyBreathWfm"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["sumEnergyHeartWfm"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    vitalsign["motionDetectedFlag"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 44
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

        return dataOK, frameNumber, vitalsign

    def update(self):

        # Read and parse the received data
        dataOk, frameNumber, vitalsign = self.readAndParseData(self.Dataport, self.configParameters)
        self.test_count_try+=1
        if dataOk:
            self.test_count_dataok+=1
            sendbin = PB.Rate_encode(vitalsign)
            # with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            #     s.bind(self.addr_2Rate)
            self.socket_Rate.sendto(sendbin, self.addr_server)
        self.breathOK = True

        return dataOk

    def __del__(self):
        self._auto_close()
        self.socket_Rate.close()
        print("dataok:{}\ntry:{}\n".format(self.test_count_dataok, self.test_count_try))

    def run(self):
        self.detObj = {}
        # self.frameData = {}
        currentIndex = 0
        while True:
            try:
                # try to get instruction from server
                try:
                    cmddata_track, addr = self.socket_Rate.recvfrom(1500)
                    assert addr == self.addr_server
                except Exception:
                    pass
                else:
                    self.ParseCmdFrame(cmddata_track, self.socket_Rate)
                # Update the data and check if the data is okay
                if self.ComportOK == False:
                    continue
                if self.breathOK == True:
                    self.breathOK = False
                    self.update()

                time.sleep(0.04)

            # Stop the program and close everything if Ctrl + c is pressed
            except KeyboardInterrupt:
                self._auto_close()
                break

if __name__ == "__main__":
    tst = TwoRate(CLIPortID=10 , DataPortID=9 ,system='Windows')
    tst.run()
