#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt, QCoreApplication

# 确保中文显示正常
QCoreApplication.setApplicationName("图片批量转换器")

def main():
    # 在函数内部导入以避免循环导入
    from src.main_window import MainWindow
    
    # 启用高DPI支持
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName("图片批量转换器")
    app.setOrganizationName("PictureConverter")
    
    # 创建并显示主窗口
    window = MainWindow()
    print("显示主窗口...")
    window.show()
    print("主窗口已显示")
    
    # 启动事件循环
    print("启动事件循环...")
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()