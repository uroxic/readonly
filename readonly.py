#!/usr/bin/python3
# -*- coding: utf-8 -*-

import ctypes
import re
import subprocess
import sys
import threading
import time


from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import readonly_resource

DiskPart = "diskpart"


def hideConsole():
    """
    Hides the console window in GUI mode. Necessary for frozen application, because
    this application support both, command line processing AND GUI mode and theirfor
    cannot be run via pythonw.exe.
    """
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 0)
        # if you wanted to close the handles...
        # ctypes.windll.kernel32.CloseHandle(whnd)


def showConsole():
    """Unhides console window"""
    whnd = ctypes.windll.kernel32.GetConsoleWindow()
    if whnd != 0:
        ctypes.windll.user32.ShowWindow(whnd, 1)

async def async_function():
    time.sleep(2)
    return 1


def formatDiskList(DiskList):
    rtn = []
    i = 0
    while (i < len(DiskList)):
        if(DiskList[i] == "###"):
            i += 12
            break
        else:
            i += 1
    temp = DiskList[i]
    while (i < len(DiskList)):
        if (DiskList[i] == temp):
            rtn.append((DiskList[i] + ' ' + DiskList[i+1]))
            rtn.append(DiskList[i+2])
            rtn.append((DiskList[i+3] + ' ' + DiskList[i+4]))
            rtn.append((DiskList[i+5] + ' ' + DiskList[i+6]))
            i += 7
        else:
            i += 1
    return rtn


def getLabelList(DiskList):
    rtn = []
    i = 0
    while (i < len(DiskList)):
        if(DiskList[i] == "###"):
            i -= 1
            break
        else:
            i += 1
    rtn.append(DiskList[i] + " ###")
    rtn.append(DiskList[i+2])
    rtn.append(DiskList[i+3])
    rtn.append(DiskList[i+4])
    return rtn


def setReadOnly(i):
    DP = subprocess.Popen(DiskPart, shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          stdin=subprocess.PIPE)
    DP.stdin.write(b"select disk "+str.encode((str(i)))+b"\n")
    DP.stdin.write(b"attributes disk set readonly")
    DP.stdin.close()
    DP.wait()
    return


def clearReadOnly(i):
    DP = subprocess.Popen(DiskPart, shell=True,
                          stdout=subprocess.PIPE,
                          stderr=subprocess.STDOUT,
                          stdin=subprocess.PIPE)
    DP.stdin.write(b"select disk "+str.encode((str(i)))+b"\n")
    DP.stdin.write(b"attributes disk clear readonly")
    DP.stdin.close()
    DP.wait()
    return


class MainUi(QMainWindow):

    def __init__(self):
        super().__init__()
        self.conn = None
        self.BtnList = {}
        self.TitleList = {}
        self.TextEditList = {}
        self.initUI()  # 界面绘制交给InitUi方法
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.restore)

    def initUI(self):
        self.desktop = QApplication.desktop()
        # 获取显示器分辨率大小
        self.screenRect = self.desktop.screenGeometry()
        self.dpi = ctypes.windll.gdi32.GetDeviceCaps(
            ctypes.windll.user32.GetDC(0), 88)
        self.ratio = self.dpi/96
        self.height = int(self.ratio*self.screenRect.width()*16/80+0.5)
        self.width = int(self.ratio*self.screenRect.width()*12/80+0.5)
        self.unit = int(self.ratio*self.screenRect.width()/240+0.5)

        font = QFont()
        font.setPointSize(int(self.unit/self.ratio))

        self.main_widget = QWidget()
        self.main_widget.setObjectName("MainWindow")
        self.setCentralWidget(self.main_widget)

        self.main_widget.setStyleSheet(
            "QWidget#MainWindow{border-image:url(:/readonly.png);}")
        self.setWindowOpacity(0.9)
        self.setWindowFlag(Qt.FramelessWindowHint)  # 隐藏边框
        self.setAttribute(Qt.WA_TranslucentBackground)  # 设置窗口背景透明
        self.setStyleSheet(
            ''' QWidget{color:#232C51; background:rgba(255,255,255,192); border:1px solid darkGray; border-radius:'''+str(self.unit)+'''px;}''')

        close = QPushButton("")  # 关闭按钮
        large = QPushButton("")  # 最大化按钮
        mini = QPushButton("")  # 最小化按钮
        close.setFixedSize(2*self.unit, 2*self.unit)
        large.setFixedSize(2*self.unit, 2*self.unit)
        mini.setFixedSize(2*self.unit, 2*self.unit)
        close.setStyleSheet(
            '''QPushButton{background:#F76677;border-radius:'''+str(self.unit)+'''px;}QPushButton:hover{background:red;}''')
        large.setStyleSheet(
            '''QPushButton{background:#F7D674;border-radius:'''+str(self.unit)+'''px;}QPushButton:hover{background:#F7C604;}''')
        mini.setStyleSheet(
            '''QPushButton{background:#6DDF6D;border-radius:'''+str(self.unit)+'''px;}QPushButton:hover{background:#0DDF0D;}''')
        close.clicked.connect(QCoreApplication.instance().quit)
        mini.clicked.connect(self.showMinimized)
        large.clicked.connect(self.windowCtl)

        title0 = QLabel('  Disk Readonly  ')
        title0.setFont(font)

        title0_0 = QLabel('Waiting')
        title0_0.setFont(font)
        title0_0.setFixedSize(6*self.unit, int(2.25*self.unit+0.5))
        title0_0.setAlignment(Qt.AlignCenter)
        self.TitleList['title0_0'] = title0_0

        DP = subprocess.Popen("diskpart", stdout=subprocess.PIPE,
                              stdin=subprocess.PIPE)
        DP.stdin.write(b"list disk\n")
        DP.stdin.close()
        out = DP.stdout.read().decode("GB18030")
        DiskList = out.split()
        LabelList = getLabelList(DiskList)
        DiskList = formatDiskList(DiskList)

        text1 = QTableWidget()
        text1.setColumnCount(4)
        text1.resizeRowsToContents()
        text1.verticalHeader().setVisible(False)
        text1.horizontalHeader().setFont(font)
        text1.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        text1.setHorizontalHeaderLabels(LabelList)
        text1.setEditTriggers(QAbstractItemView.NoEditTriggers)
        text1.setSelectionMode(QAbstractItemView.SingleSelection)
        text1.setSelectionBehavior(QAbstractItemView.SelectRows)
        text1.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        text1.setHorizontalScrollMode(QAbstractItemView.ScrollPerPixel)
        self.TextEditList['text1'] = text1
        text1.setStyleSheet(
            '''QTableWidget{border:1px solid gray; border-radius:'''+str(self.unit)+'''px; padding:2px 4px;}''')
        text1.setFont(font)

        text1.setRowCount(len(DiskList)//4)
        i = 0
        while (i < (len(DiskList)//4)):
            text1.setItem(i, 0, QTableWidgetItem(DiskList[4*i+0]))
            text1.setItem(i, 1, QTableWidgetItem(DiskList[4*i+1]))
            text1.setItem(i, 2, QTableWidgetItem(DiskList[4*i+2]))
            text1.setItem(i, 3, QTableWidgetItem(DiskList[4*i+3]))
            i += 1

        btn1 = QPushButton(" Set Readonly ", self)
        btn2 = QPushButton(" Clear Readonly ", self)
        self.BtnList['btn1'] = btn1
        self.BtnList['btn2'] = btn2
        btn1.setStyleSheet('''QPushButton{border:1px solid darkGray;height:'''+str(3*self.unit)+'''px;width:'''+str(10*self.unit)+'''px;}
                               QPushButton:hover{border:1px solid darkGray; border-radius:'''+str(self.unit)+'''px; background:rgba(211,211,211,192);}''')
        btn2.setStyleSheet('''QPushButton{border:1px solid darkGray;height:'''+str(3*self.unit)+'''px;width:'''+str(10*self.unit)+'''px;}
                               QPushButton:hover{border:1px solid darkGray; border-radius:'''+str(self.unit)+'''px; background:rgba(211,211,211,192);}''')
        btn1.setFont(font)
        btn2.setFont(font)

        btn1.clicked.connect(self.buttonClicked)
        btn2.clicked.connect(self.buttonClicked)

        hbox0 = QHBoxLayout()
        hbox0.addWidget(title0_0)
        hbox0.addStretch(1)
        hbox0.addWidget(title0)
        hbox0.addStretch(1)
        hbox0.addWidget(mini)
        hbox0.addWidget(large)
        hbox0.addWidget(close)

        hbox2 = QHBoxLayout()
        hbox2.addStretch(5)
        hbox2.addWidget(btn1)
        hbox2.addStretch(1)
        hbox2.addWidget(btn2)
        hbox2.addStretch(5)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox0)
        vbox.addWidget(text1)
        vbox.addLayout(hbox2)

        self.main_widget.setLayout(vbox)
        self.setGeometry(200, 200, self.width, self.height)
        self.setWindowTitle('readonly')
        self.setWindowIcon(QIcon(':/readonly.ico'))

    def buttonClicked(self):
        sender = self.sender()
        if(sender == self.BtnList['btn1']):
            try:
                index = self.TextEditList['text1'].currentIndex().row()
                if(index != -1):
                    setReadOnly(index)
                    self.TitleList['title0_0'].setText('Success')
                    self.timer.start(3000)
                else:
                    self.TitleList['title0_0'].setText('Fail')
                    self.timer.start(3000)
            except:
                self.TitleList['title0_0'].setText('Fail')
                self.timer.start(3000)
        if(sender == self.BtnList['btn2']):
            try:
                index = self.TextEditList['text1'].currentIndex().row()
                if(index != -1):
                    clearReadOnly(index)
                    self.TitleList['title0_0'].setText('Success')
                    self.timer.start(3000)
                else:
                    self.TitleList['title0_0'].setText('Fail')
                    self.timer.start(3000)
            except:
                self.TitleList['title0_0'].setText('Fail')
                self.timer.start(3000)

    def restore(self):
        self.TitleList['title0_0'].setText('Waiting')

    def windowCtl(self):
        if(self.isMaximized()):
            self.showNormal()
        else:
            self.showMaximized()

    def mouseMoveEvent(self, e: QMouseEvent):  # 重写移动事件
        self._endPos = e.pos() - self._startPos
        self.move(self.pos() + self._endPos)

    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = True
            self._startPos = QPoint(e.x(), e.y())

    def mouseReleaseEvent(self, e: QMouseEvent):
        if e.button() == Qt.LeftButton:
            self._isTracking = False
            self._startPos = None
            self._endPos = None


if __name__ == '__main__':
    hideConsole()
    ctypes.windll.user32.SetProcessDPIAware()
    QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    mui = MainUi()
    mui.show()
    sys.exit(app.exec_())
