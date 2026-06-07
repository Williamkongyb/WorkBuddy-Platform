@echo off
chcp 65001 >nul
title WorkBuddy v4.0 一键启动
cd /d D:\WB_Workflow
C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe start_all.py
echo.
echo 按任意键关闭此窗口...
pause >nul
