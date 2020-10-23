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
import ProtocolBase as PB
import logging
import threading
import socket

class TwoRate(threading.Thread):
    test_count_dataok = 0
    test_count_try = 0
    if_Screen = True
    CLIport = None
    Dataport = None
    Screenport = None
    outHeartNew_CM = 0
    def __init__(self, addr_2Rate=("127.0.0.1", 12003), addr_server=("127.0.0.1", 12000),
                 CLIPortID=10, DataPortID=9, SCID=13, system="Linux", logger=logging,
                 configFileName='xwr1642_profile_VitalSigns_20fps_Front.cfg'):
        super().__init__(daemon=True)
        # 传入变量的初始化
        self.logger = logger
        self.system = system
        self.SCID = SCID
        # socket
        self.addr_2Rate = addr_2Rate
        self.addr_server = addr_server
        self.socket_Rate = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.socket_Rate.bind(self.addr_2Rate)
        self.socket_Rate.setblocking(False)

        self._init_data()

        # start the port
        self.ComportOK = False
        self.start_conf = [configFileName, CLIPortID, DataPortID]
        self._auto_start(*self.start_conf)



    def _init_data(self):
        self.byteBuffer = np.zeros(2 ** 15, dtype='uint8')
        self.byteBufferLength = 0
        self.configParameters = {}
        self.detObj = {}
        self.breathOK = True
        print("init data successful")
        # self.ComportOK = False

    def _auto_start(self, configFileName, CLIPortID, DataPortID):
        system = self.system
        if system != "Linux" and system != "Windows":
            raise SystemExit("only support Linux and Windows Com")

        try:
            self.serialConfig(configFileName, CLIPortID, DataPortID, system)  # Open the serial ports
        except Exception as err:
            self.logger.error("Open Com Fail...\nThere is the error report:\n{}\n*********************************".format(err))
            return

        try:
            self.parseConfigFile(configFileName)
        except Exception as err:
            self.logger.error("something wrong in config file please check '{}'\nThere is the error report:\n{}\n"
                              "*********************************".format(configFileName, err))
            # print("something wrong in config file please check '{}'".format(configFileName))
            # print("There is the error report:\n{}\n****************************".format(err))
            return
        else:
            self.logger.info("Com open success")

        self.logger.info("Open TrackModule module successfully")
        self.ComportOK = True
        self._init_data()
        self.logger.debug("breathOK:{} ComportOK:{}".format(self.breathOK,self.ComportOK))

    def _auto_close(self):
        if self.CLIport:
            self.CLIport.write(('sensorStop\n').encode())
            print('sensorStop\n')
            self.CLIport.close()
        if self.Dataport:
            self.Dataport.close()
        self.ComportOK = False

    def serialConfig(self, configFileName, CPID, DPID, system="Linux"):
        # Raspberry Linux
        if system == "Linux":
            self.CLIport = serial.Serial('/dev/My_Serial%d' % CPID, 115200)
            self.Dataport = serial.Serial('/dev/My_Serial%d' % DPID, 921600)
            if self.if_Screen:
                self.Screenport=serial.Serial('/dev/My_Serial%d' % self.SCID, 9600)

        # Windows
        elif system == "Windows":
            self.CLIport = serial.Serial('COM%d' % CPID, 115200)
            self.Dataport = serial.Serial('COM%d' % DPID, 921600)
            if self.if_Screen:
                self.Screenport=serial.Serial('COM%d' % self.SCID, 9600)
        # Read the configuration file and send it to the board
        config = [line.rstrip('\r\n') for line in open(configFileName)]
        for i in config:
            print(i)
            self.logger.debug("Comsend:\n{}".format(str(i)))
            # if i[0] != '%':
            self.CLIport.write((i + '\n').encode())
            time.sleep(1)
        print("serial config finish")
        self.logger.info("serial config finish")

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
        elif data == b"dataclear\x00":
            self._init_data()
        else:
            print('unknown cmd...')
            self.logger.warning("unknown cmd...")

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
        self.logger.debug("reading data")
        readBuffer = Dataport.read(Dataport.in_waiting)
        self.logger.debug("read data")
        byteVec = np.frombuffer(readBuffer, dtype='uint8')
        self.logger.debug("byteVec:{}".format(byteVec))
        byteCount = len(byteVec)

        # Check that the buffer is not full, and then add the data to the buffer
        if (self.byteBufferLength + byteCount) < maxBufferSize:
            self.byteBuffer[self.byteBufferLength:(self.byteBufferLength + byteCount)] = byteVec[0:byteCount]
            self.byteBufferLength = self.byteBufferLength + byteCount

        # Check that the buffer has some data
        self.logger.debug("byteBUfferlength>16?{}".format(self.byteBufferLength))
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

            self.logger.debug("startIdX?")
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
            self.logger.debug("magicOK?{}\n totalPacketLen{}\nbyteBUfferlength{}\n"
                              "byteBuffer{}".format(magicOK, totalPacketLen, self.byteBufferLength,
                                                    self.byteBuffer[0:max(self.byteBufferLength, 0)]))
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
            self.logger.debug("numTLVS:{}".format(numTLVs))
            if numTLVs > 2:
                numTLVs = 2
                self.logger.warning("numTLVs Error! value:{}".format(numTLVs))
                # tmplist = self.byteBuffer.tolist()
                self.logger.warning("{}".format(self.byteBuffer))
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
                    vitalsign["heartRateEst_FFT_4Hz"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0] / 2
                    idX += 4
                    vitalsign["heartRateEst_xCorr"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    vitalsign["heartRateEst_peakCount"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
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
                    vitalsign["confidenceMetricHeartOut"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    vitalsign["confidenceMetricHeartOut_4Hz"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    vitalsign["confidenceMetricHeartOut_xCorr"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["sumEnergyBreathWfm"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    # vitalsign["sumEnergyHeartWfm"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    idX += 4
                    vitalsign["motionDetectedFlag"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
                    # if vitalsign["motionDetectedFlag"] == 0:
                    #     vitalsign["heartRateEst_FFT"] = vitalsign["breathingRateEst_FFT"] = 0
                    idX += 44
                    dataOK = 1

                    # define
                    ALPHA_HEARTRATE_CM = 0.6
                    THRESH_HEART_CM = 0.25
                    THRESH_DIFF_EST = 20
                    MIN_HEARTRATE = 75
                    BACK_THRESH_BPM = 4

                    heartRate_CM = vitalsign["confidenceMetricHeartOut"]
                    heartRate_FFT = vitalsign["heartRateEst_FFT"]
                    heartRate_Pk = vitalsign["heartRateEst_peakCount"]
                    # heartRate_xCorr = vitalsign["heartRateEst_xCorr"]
                    # BreathingRate_FFT = vitalsign["breathingRateEst_FFT"]
                    # # new means to get heartrate

                    outHeartPrev_CM = self.outHeartNew_CM
                    self.outHeartNew_CM = ALPHA_HEARTRATE_CM*(heartRate_CM) + (1-ALPHA_HEARTRATE_CM)*outHeartPrev_CM
                    diffEst_heartRate = abs(heartRate_FFT - heartRate_Pk)
                    if self.outHeartNew_CM > THRESH_HEART_CM or diffEst_heartRate < THRESH_DIFF_EST :

                        heartRateEstDisplay = heartRate_FFT
                    else:
                        heartRateEstDisplay =heartRate_Pk
                    print([self.outHeartNew_CM, diffEst_heartRate])
                    print(vitalsign["heartRateEst_FFT"],
                          vitalsign["heartRateEst_peakCount"], "==>",
                          heartRateEstDisplay)
                    vitalsign["heartRateEst_FFT"] = heartRateEstDisplay
                    if vitalsign["heartRateEst_FFT"] < MIN_HEARTRATE:
                        vitalsign["heartRateEst_FFT"] = max(heartRate_FFT, heartRate_Pk)

            # Remove already processed data

            # self.logger.debug("shift!")
            if 0 < idX < self.byteBufferLength:
                shiftSize = totalPacketLen

                self.byteBuffer[:self.byteBufferLength - shiftSize] = self.byteBuffer[shiftSize:self.byteBufferLength]
                self.byteBuffer[self.byteBufferLength - shiftSize:] = np.zeros(len(self.byteBuffer[self.byteBufferLength - shiftSize:]),
                                                                     dtype='uint8')
                self.byteBufferLength = self.byteBufferLength - shiftSize

                # Check that there are no errors with the buffer length
                if self.byteBufferLength < 0:
                    self.logger.warning("byteBufferLength<0")
                    self.byteBufferLength = 0

            # self.logger.debug("shift finish")
        # vitalsign["heartRateEst_FFT"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
        # vitalsign["heartRateEst_FFT_4Hz"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0] / 2
        # vitalsign["heartRateEst_xCorr"] = struct.unpack('<f', self.byteBuffer[idX:idX + 4])[0]
        # self.logger.debug("return parse")
        return dataOK, frameNumber, vitalsign

    def update(self,vitalsign):

        # Read and parse the received data
        sendbin = PB.Rate_encode(vitalsign)
        if self.if_Screen:
            FF = b"\xff\xff\xff"
            # print(vitalsign)
            if not vitalsign['breathingRateEst_FFT']*vitalsign['heartRateEst_FFT']==0:
                self.Screenport.write(('t3.txt="%d"' % int(vitalsign['breathingRateEst_FFT'])).encode()+FF)
                self.Screenport.write(('t2.txt="%d"' % int(vitalsign['heartRateEst_FFT'])).encode()+FF)
            time.sleep(0.01)
            self.Screenport.write(('add 2,0,%d' % int(vitalsign["outputFilterBreathOut"]*20+64)).encode()+FF)
            self.Screenport.write(('add 1,0,%d' % int(vitalsign['outputFilterHeartOut']*20+64)).encode()+FF)
        self.socket_Rate.sendto(sendbin, self.addr_server)
        self.logger.debug("send a frame:\n{}".format(str(sendbin)))
        self.breathOK = True

    def __del__(self):
        self._auto_close()
        self.socket_Rate.close()
        self.logger.info("dataok:{}\ntry:{}\n".format(self.test_count_dataok, self.test_count_try))

    def run(self):
        self.detObj = {}
        # self.frameData = {}
        currentIndex = 0
        while True:
            try:
                # try to get instruction from server
                try:
                    self.logger.debug("intorcvcmddata".format())
                    cmddata_track, addr = self.socket_Rate.recvfrom(1500)
                    if addr != self.addr_server:
                        print("rcv cmd from unknown addr:{}".format(addr))
                        self.logger.warning("rcv cmd from unknown addr".format())
                    self.logger.debug("get a cmdframe:\n{}".format(str(cmddata_track)))
                except Exception:
                    pass
                else:
                    self.logger.debug("ComportOK:{}breathOK:{}".format(self.ComportOK,self.breathOK))
                    self.ParseCmdFrame(cmddata_track, self.socket_Rate)
                # Update the data and check if the data is okay
                    self.logger.debug("ComportOK?".format())
                if self.ComportOK == False:
                    self.logger.debug("ComportOK?".format())
                    time.sleep(0.1)
                    continue
                self.logger.debug("parsedata??".format())
                try:
                    dataOk, frameNumber, vitalsign = self.readAndParseData(self.Dataport, self.configParameters)
                except Exception as Z:
                    self.logger.error("parsedataerr:{}".format(Z))
                    raise KeyboardInterrupt
                self.test_count_try += 1
                self.logger.debug("dataOK?".format())
                if dataOk:
                    self.test_count_dataok += 1
                    self.logger.debug("breathOK?".format())
                    if self.breathOK:
                        self.breathOK = False
                        tmp_thread_rate = threading.Thread(target=self.update, daemon=True,
                                                           args=(vitalsign,))
                        tmp_thread_rate.start()

                time.sleep(0.01)

            # Stop the program and close everything if Ctrl + c is pressed
            except KeyboardInterrupt:
                self._auto_close()
                break

        self.logger.debug("out of while...")
if __name__ == "__main__":
    tst = TwoRate(CLIPortID=10 , DataPortID=9 ,system='Windows')
    tst.run()
