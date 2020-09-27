# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     GUIpyqt
   Description :
   Author :       Kinddle
   date：          2020/9/27
-------------------------------------------------
   Change Activity:
                   2020/9/27:
-------------------------------------------------
"""
__author__ = 'Kinddle'

# coding:utf-8

from PyQt5 import QtCore, QtGui, QtWidgets
import sys
import qtawesome
import pyqtgraph as pg
import re

class MainUi(QtWidgets.QMainWindow):
    def __init__(self, datalink):
        super().__init__()
        self.datadic = datalink
        self.title = 'Contoller'
        self.left = 100
        self.top = 100
        self.width = 960
        self.height = 700
        self.init_ui()
        self.refresh(True,True,True)

    def init_ui(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.main_widget = QtWidgets.QWidget()  # 创建窗口主部件
        self.main_layout = QtWidgets.QGridLayout()  # 创建主部件的网格布局
        self.main_widget.setLayout(self.main_layout)  # 设置窗口主部件布局为网格布局

        self.left_widget = QtWidgets.QWidget()  # 创建左侧部件
        self.left_layout = QtWidgets.QGridLayout()  # 创建左侧部件的网格布局层
        self.left_widget.setLayout(self.left_layout)  # 设置左侧部件布局为网格

        self.right_widget = QtWidgets.QWidget()  # 创建右侧部件
        self.right_layout = QtWidgets.QGridLayout()
        self.right_widget.setLayout(self.right_layout)  # 设置右侧部件布局为网格


        self.control_widget = QtWidgets.QWidget() #创建控制部件
        self.control_layout = QtWidgets.QGridLayout()
        self.control_widget.setLayout(self.control_layout)  # 设置控制部件布局为网格

        self.main_layout.addWidget(self.left_widget, 0, 0, 13, 2)  # 左侧部件在第0行第0列，占8行3列
        self.main_layout.addWidget(self.right_widget, 0, 2, 12, 6)  # 右侧部件在第0行第3列，占8行9列

        self.main_layout.setColumnStretch(0, 2)
        self.main_layout.setColumnStretch(1, 6)
        self.setCentralWidget(self.main_widget)  # 设置窗口主部件

        self.lb1 = QtWidgets.QLabel("呼吸速率:0")
        self.lb2 = QtWidgets.QLabel("心跳速率:0")
        self.lb3 = QtWidgets.QLabel("跌倒检测：")
        self.lb4 = QtWidgets.QLabel('呼吸心跳雷达：')
        self.lb5 = QtWidgets.QLabel('航迹跌倒雷达：')
        self.lb6 = QtWidgets.QLabel('目标检测与跟踪')
        self.txt = QtWidgets.QTextEdit()

        self.plot_Track = pg.PlotWidget()
        self.plot_Rate_breath = pg.PlotWidget()
        self.plot_Rate_heart = pg.PlotWidget()

        btn1 = QtWidgets.QPushButton("R up")
        btn1.clicked.connect(lambda : print(1))
        btn2 = QtWidgets.QPushButton('R down')
        btn2.clicked.connect(lambda : print(1))
        btn3 = QtWidgets.QPushButton('FT up')
        btn3.clicked.connect(lambda : print(1))
        btn4 = QtWidgets.QPushButton('FT down')
        btn4.clicked.connect(lambda : print(1))


        #布局
        self.left_layout.addWidget(self.lb1, 0, 0, 1, 2)
        self.left_layout.addWidget(self.plot_Rate_breath, 1, 0, 3, 2)
        self.left_layout.addWidget(self.lb2, 4, 0, 1, 2)
        self.left_layout.addWidget(self.plot_Rate_heart, 5, 0, 3, 2)
        self.left_layout.addWidget(self.lb3, 8, 0 ,1, 2)
        self.left_layout.addWidget(self.txt, 9, 0, 4, 2)
        self.left_layout.setRowStretch(0, 1)
        self.left_layout.setRowStretch(1, 4)
        self.left_layout.setRowStretch(4, 1)
        self.left_layout.setRowStretch(5, 4)
        self.left_layout.setRowStretch(8, 1)
        self.left_layout.setRowStretch(9, 4)

        self.right_layout.addWidget(self.lb6, 0, 0, 1, 6)
        self.right_layout.addWidget(self.plot_Track, 1, 0, 10, 6)
        self.right_layout.addWidget(self.control_widget, 11, 0, 1, 6)
        self.right_layout.setRowStretch(1, 0)
        self.right_layout.setRowStretch(2, 5)
        self.right_layout.setRowStretch(11,0)

        self.control_layout.addWidget(self.lb4,0,0,1,2)
        self.control_layout.addWidget(self.lb5,0,2,1,2)
        self.control_layout.addWidget(btn1, 1, 0)
        self.control_layout.addWidget(btn2, 1, 1)
        self.control_layout.addWidget(btn3, 1, 2)
        self.control_layout.addWidget(btn4, 1, 3)
        self.right_layout.setRowStretch(0, 1)
        self.right_layout.setRowStretch(1, 1)

    def refresh(self, T=False, R=False, F=False):
        if T:
            pass
        if R:
            self.lb1.setText('呼吸率：%d' % self.datadic['R'][2])
            self.lb2.setText('心率:%d' % self.datadic['R'][3])
            # self.Rate_breath.set('呼吸率：%d' % self.datadic['R'][2])
            # self.Rate_heart.set('心率:%d' % self.datadic['R'][3])
        if F:
            stat = self.datadic['F']
            txt_insert = ('平静' if stat==0 else '慢蹲或坐下' if stat == 1 else '跌倒！！' if stat == 2 else "未知数据")
            now_txt = self.txt.toPlainText()
            sp_txt = re.split('\n', now_txt)
            for i in range(0, min(len(sp_txt),5)):
                txt_insert += '\n'+sp_txt[i]
            self.txt.setPlainText(txt_insert)

def main():
    app = QtWidgets.QApplication(sys.argv)
    datainit = {"T": [[[0,0,0],[1,1,1],[1,2,1]],[[3,3,3],[3,3,2],[3,2,1],[3,3,3]]],
                'R': [0.45,0.68,60,120],
                'F': 0}
    gui = MainUi(datainit)
    gui.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()