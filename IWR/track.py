#
# File:         Track类用于航迹的管理
# Author:       UESTC Yu Xuyao
# Email:        yxy19991102@163.com
#

import numpy
import matplotlib.pyplot as plt


class TestTrack:
    def __init__(self, Z: numpy.mat):
        self.start = Z
        self.seq = Z
        self.est = []
        self.pkk = []
        self.x_predict = []
        self.M = 0
        self.N = 0

    def addseq(self, Z):
        self.seq = numpy.hstack((self.seq, Z))

    def addest(self, est):
        self.est = numpy.hstack((self.est, est))


class ConfirmedTrack:
    def __init__(self, Z: numpy.mat):
        self.start = Z
        self.seq = Z
        self.est = []
        self.pkk = []
        self.S = []
        self.x_predict = []
        self.board = 0
        self.boardclear = 0

    def addseq(self, Z):
        self.seq = numpy.hstack((self.seq, Z))
        if self.seq.shape[1] > 20:
            self.seq = numpy.delete(self.seq, 0, axis=1)

    def addest(self, Z):
        self.est = numpy.hstack((self.est, Z))
        if self.est.shape[1] > 20:
            self.est = numpy.delete(self.est, 0, axis=1)

    def show2D(self, plt):
        plt.plot(numpy.array(self.est[0, :])[0], numpy.array(self.est[1, :])[0], color="blue", linewidth=1.5,
                 linestyle="-")

