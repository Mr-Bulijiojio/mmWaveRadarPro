# -*- coding: utf-8 -*-
"""
-------------------------------------------------
   File Name：     GUI
   Description :
   Author :       Kinddle
   date：          2020/9/27
-------------------------------------------------
   Change Activity:
                   2020/9/27:
-------------------------------------------------
"""
__author__ = 'Kinddle'
import tkinter as tk
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk


mpl.rcParams['font.sans-serif'] = ['SimHei']  #中文显示
mpl.rcParams['axes.unicode_minus']=False      #负号显示


class GUI():
    root = tk.Tk()
    def __init__(self, datalink=None, flesh_f=0.1):
        self.datadic = datalink
        root = self.root
        width = root.winfo_screenwidth() * 0.6
        height = root.winfo_screenheight() * 0.8
        self.center_window(width, height)  # 设置窗口位置
        # 可变标签初始化
        self.Rate_breath = tk.StringVar()
        self.Rate_breath.set('呼吸率:0')
        self.Rate_heart = tk.StringVar()
        self.Rate_heart.set("心率:0")

        # 设置框架
        self.controller_frm = tk.Frame(root, bg='#FFFFFF')
        self.Track_frm = tk.Frame(root, bg="#242424")
        self.Rate_frm = tk.Frame(root ,bg ="#CCFFFF")
        self.Fall_frm = tk.Frame(root,bg="#FFFF66")
        # 框架的初始化
        self.cfg_controller()
        self.cfg_Track()
        self.cfg_Rate()
        self.cfg_Fall()

    def refresh(self, T=False, R=False, F=False):
        if T:
            pass
        if R:
            self.Rate_breath.set('呼吸率：%d' % self.datadic['R'][2])
            self.Rate_heart.set('心率:%d' % self.datadic['R'][3])
        if F:
            stat = self.datadic['F']
            self.Fall_txt.insert(0.0, '\n')
            txt_insert = '平静' if stat==0 else '慢蹲或坐下' if stat == 1 else '跌倒！！' if stat == 2 else "未知数据"
            self.Fall_txt.insert(0.0,txt_insert)
# ---------------------------------------------------------------------------------#
    def center_window(self, width, height):
        root = self.root
        root.title('Contoller')
        screenwidth = root.winfo_screenwidth()
        screenheight = root.winfo_screenheight()
        size = '%dx%d+%d+%d' % (width, height, (screenwidth - width) / 2, (screenheight - height) / 2)
        print(size)
        root.geometry(size)
        print(id(root) == id(self.root))
        #self.root = root
        #root.update()
        print(root.winfo_x())

    def _Mydestroy(self):
        self.root.destroy()

    def cfg_controller(self):
        root = self.controller_frm
        root.place(relx=0, rely=1, relwidth=1, height=50, y=-50)
        # 退出按钮
        btnc1 = tk.Button(root, text='退出', command=self._Mydestroy)
        btnc1.place(relx=0.9, rely=0.1, relheight=0.8, relwidth=0.1*0.95)

    def cfg_Track(self):
        root=self.Track_frm
        root.place(relx=0.2, rely=0, relwidth= 0.8, relheight=1, height=-50)
        # self.canvas = tk.Canvas()
        # test
        # fingure = self.test_matplotlib(1, title='Track', bgcolor="#242424")
        # self.create_form(fingure, root)

    def cfg_Rate(self):
        root = self.Rate_frm
        root.place(relheight=0.6, relwidth=0.2, height=0)
        lb_breath = tk.Label(root, textvariable=self.Rate_breath, font=30, bg='#83d7e6', relief = tk.GROOVE)
        lb_heart = tk.Label(root, textvariable=self.Rate_heart, font=30, bg='#83d7e6', relief = tk.GROOVE)
        lb_breath.place(relx=0.05, rely=0.05, relheight=0.1, relwidth=0.9)
        lb_heart.place(relx=0.05, rely=0.15, relheight=0.1, relwidth=0.9)
        self.outputbreath = tk.Frame(root, bg="#ce9de8")
        self.outputheart = tk.Frame(root, bg="#8d43b5")
        self.outputbreath.place(rely=0.3, relheight=0.35, relwidth=1)
        self.outputheart.place(rely=0.65, relheight=0.35, relwidth=1)
        # test
        # figure = self.test_matplotlib(2, title='Heart', bgcolor="#ce9de8")
        # self.create_form(figure, self.outputheart)
        #
        # figure = self.test_matplotlib(3, title='Breath', bgcolor="#8d43b5")
        # self.create_form(figure, self.outputbreath)

    def cfg_Fall(self):
        root=self.Fall_frm
        root.place(rely=0.6, relheight=0.4, relwidth=0.2, height=-50)
        lb = tk.Label(root,text="跌倒检测", bg='#f2e599')
        lb.place(relheight=0.15, relwidth=1)
        self.Fall_txt=tk.Text(root, bg='#f5eec9')
        self.Fall_txt.place(rely=0.15, relheight=0.85, relwidth=1)

    def test_matplotlib(self,No, title=None, bgcolor='pink'):
        '''
        测试用函数图像
        :return:
        '''
        # 创建绘图对象f
        f = plt.figure(num=No, figsize=(16, 12), dpi=80, facecolor=bgcolor, edgecolor='green', frameon=True)
        # 创建一副子图
        fig1 = plt.subplot(1, 1, 1)

        x = np.arange(0, 2 * np.pi, 0.1)
        y1 = np.sin(x)
        y2 = np.cos(x)

        line1, = fig1.plot(x, y1, color='red', linewidth=3, linestyle='--')  # 画第一条线
        line2, = fig1.plot(x, y2)
        plt.setp(line2, color='black', linewidth=8, linestyle='-', alpha=0.3)  # 华第二条线

        fig1.set_title(title, loc='center', pad=20, fontsize='xx-large', color='red')  # 设置标题
        line1.set_label("正弦曲线")  # 确定图例
        fig1.legend(['正弦', '余弦'], loc='upper left', facecolor='green', frameon=True, shadow=True, framealpha=0.5,
                    fontsize='xx-large')

        fig1.set_xlabel('横坐标')  # 确定坐标轴标题
        fig1.set_ylabel("纵坐标")
        fig1.set_yticks([-1, -1 / 2, 0, 1 / 2, 1])  # 设置坐标轴刻度
        fig1.grid(which='major', axis='x', color='r', linestyle='-', linewidth=2)  # 设置网格

        return f

    def create_form(self, figure, frame):
        '''
        负责画图，不负责update，每张图占用一个frm
        :param figure:matplotlib画出图像的返回值f
        :param frame: 根窗口，Frame，tabcontrol均可
        :return:None
        '''
        # 把绘制的图形显示到tkinter窗口上
        canvas = FigureCanvasTkAgg(figure, frame)
        canvas.draw()  # 以前的版本使用show()方法，matplotlib 2.2之后不再推荐show（）用draw代替，但是用show不会报错，会显示警告
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        # self.canvas.get_tk_widget().place(x=100, y=100, relheight=0.8, relwidth=1)
        # 把matplotlib绘制图形的导航工具栏显示到tkinter窗口上
        # toolbar = NavigationToolbar2Tk(self.canvas,
        #                                frame)  # matplotlib 2.2版本之后推荐使用NavigationToolbar2Tk，若使用NavigationToolbar2TkAgg会警告
        # toolbar.update()
        canvas._tkcanvas.place(relheight=1, relwidth=1)
        # plt.cla()



if __name__=="__main__":
    datainit = {"T": [[[0,0,0],[1,1,1],[1,2,1]],[[3,3,3],[3,3,2],[3,2,1],[3,3,3]]],
                'R': [0.45,0.68,60,120],
                'F': 0}
    x = GUI(datainit)
    x.refresh(True, True, True)
    datainit['F'] = 2
    x.refresh(F=True)
    x.root.mainloop()
