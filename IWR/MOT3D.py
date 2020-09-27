#
# File:         实现逻辑法航迹起始，NN法数据关联，卡尔曼滤波以及传统航迹管理（3维）
#               主要实现了MOT迭代函数
# Author:       UESTC Yu Xuyao
# Email:        yxy19991102@163.com
#

import scipy.io as scio
import numpy
import scipy.stats as st
import time
from IWR.track import *

threshold = st.chi2.ppf(0.80, 3)
T = 0.1

F = numpy.mat([[1, 0, 0, T, 0, 0], [0, 1, 0, 0, T, 0], [0, 0, 1, 0, 0, T], [0, 0, 0, 1, 0, 0], [0, 0, 0, 0, 1, 0],
               [0, 0, 0, 0, 0, 1]])
H = numpy.mat([[1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 0], [0, 0, 1, 0, 0, 0]])
Gamma = numpy.mat([[T * T / 2, 0, 0], [0, T * T / 2, 0], [0, 0, T * T / 2], [T, 0, 0], [0, T, 0], [0, 0, T]])
Q = Gamma * Gamma.T * 0.5
R = 0.1 * H * H.T

vmin = 0.2
vmax = 4

max_velocity = 2

def beginTrack(points):
    global threshold, T, F, H, Gamma, Q, R, vmin, vmax

    outside = []

    index = 0
    testroot = []

    Z_k = (points[0])
    Z_k_plus1 = (points[1])

    for j in range(0, Z_k.shape[1]):
        for k in range(0, Z_k_plus1.shape[1]):
            d = max(0, numpy.linalg.norm(Z_k_plus1[:, k] - Z_k[:, j]) - vmax * T) + max(0, -numpy.linalg.norm(
                Z_k_plus1[:, k] - Z_k[:, j]) + vmin * T)
            D = d / numpy.linalg.det(R + R) * d
            if D <= threshold:
                temp = TestTrack(Z_k[:, j])
                temp.addseq(Z_k_plus1[:, k])

                Px0 = 5 * numpy.eye(6)
                P = F * Px0 * F.T + Q
                S = H * P * H.T + R * 0.2
                K = P * H.T * numpy.linalg.inv(S)
                Pkk = (numpy.eye(6) - K * H) * P

                x_init = numpy.concatenate((Z_k_plus1[:, k], (Z_k_plus1[:, k] - Z_k[:, j]) / T), axis=0)
                x_forest = F * x_init

                temp.est = x_init
                temp.pkk = Pkk
                temp.x_predict = x_forest
                temp.M = 2
                temp.N = 2

                testroot.append(temp)

    return testroot


def TestToConfirmed(testroot):
    confirmedroot = ConfirmedTrack(testroot.start)
    confirmedroot.seq = testroot.seq
    confirmedroot.est = testroot.est
    confirmedroot.pkk = testroot.pkk
    confirmedroot.seq = testroot.seq
    confirmedroot.x_predict = testroot.x_predict
    return confirmedroot


def MOT(Z_k, Z_k_prev, confirmedroot, testroot):
    global threshold, T, F, H, Gamma, Q, R, vmin, vmax

    Z_k_present = Z_k

    if Z_k.shape[1] == 0:
        if len(confirmedroot) != 0:
            pos = []
            for kk in range(0, len(confirmedroot)):
                confirmedroot[kk].board += 1
                if confirmedroot[kk].board >= 4:
                    pos.append(kk)
            confirmedroot = numpy.delete(confirmedroot, pos)
            confirmedroot = confirmedroot.tolist()

    if Z_k.shape[1] != 0:
        if len(confirmedroot) != 0:
            pos = []
            for kk in range(0, len(confirmedroot)):
                if Z_k.shape[1] == 0:
                    break

                P = F * confirmedroot[kk].pkk * F.T + Q
                S = H * P * H.T + R
                K = P * H.T * numpy.linalg.inv(S)
                outside = H * confirmedroot[kk].x_predict
                V = []
                for i in range(0, Z_k.shape[1]):
                    V.append((Z_k[:, i] - outside).T * numpy.linalg.inv(S) * (Z_k[:, i] - outside))

                index = numpy.argmin(V)
                val = numpy.amin(V)
                if val <= threshold:
                    confirmedroot[kk].addseq(Z_k[:, index])
                    est = confirmedroot[kk].x_predict + K * (Z_k[:, index] - outside)
                    confirmedroot[kk].addest(est)
                    confirmedroot[kk].pkk = (numpy.eye(6) - K * H) * P
                    confirmedroot[kk].x_predict = F * est
                    confirmedroot[kk].board = 0

                    Z_k = numpy.delete(Z_k, index, axis=1)
                else:
                    confirmedroot[kk].addseq(outside)
                    confirmedroot[kk].addest(confirmedroot[kk].x_predict)
                    confirmedroot[kk].pkk = P
                    confirmedroot[kk].x_predict = F * confirmedroot[kk].est[:, -1]
                    confirmedroot[kk].board += 1

                if confirmedroot[kk].board >= 4 or numpy.linalg.norm(confirmedroot[kk].est[3:6, -1]) > max_velocity:
                    pos.append(kk)

            confirmedroot = numpy.delete(confirmedroot, pos)
            confirmedroot = confirmedroot.tolist()

    if Z_k.shape[1] != 0:
        if len(testroot) != 0:
            pos = []
            for kk in range(0, len(testroot)):
                if Z_k.shape[1] == 0:
                    break

                P = F * testroot[kk].pkk * F.T + Q
                S = H * P * H.T + R
                K = P * H.T * numpy.linalg.inv(S)
                outside = H * testroot[kk].x_predict
                V = []
                for i in range(0, Z_k.shape[1]):
                    V.append((Z_k[:, i] - outside).T * numpy.linalg.inv(S) * (Z_k[:, i] - outside))

                index = numpy.argmin(V)
                val = numpy.amin(V)
                if val <= threshold:
                    testroot[kk].addseq(Z_k[:, index])
                    est = testroot[kk].x_predict + K * (Z_k[:, index] - outside)
                    testroot[kk].addest(est)
                    testroot[kk].pkk = (numpy.eye(6) - K * H) * P
                    testroot[kk].x_predict = F * est
                    testroot[kk].M += 1
                    testroot[kk].N += 1
                    Z_k = numpy.delete(Z_k, index, axis=1)
                else:
                    testroot[kk].addseq(outside)
                    testroot[kk].addest(testroot[kk].x_predict)
                    testroot[kk].pkk = P
                    testroot[kk].x_predict = F * testroot[kk].est[:, -1]
                    testroot[kk].N += 1

                if testroot[kk].N == 6:
                    if testroot[kk].M >= 4 and numpy.linalg.norm(testroot[kk].est[3:6, -1]) < max_velocity:
                        confirmedroot.append(TestToConfirmed(testroot[kk]))
                    else:
                        pos.append(kk)

            testroot = numpy.delete(testroot, pos)
            testroot = testroot.tolist()

    if Z_k.shape[1] != 0:
        testroot.extend(beginTrack([Z_k_prev, Z_k_present]))

    Z_k_prev = Z_k_present
    return confirmedroot, testroot, Z_k_present
