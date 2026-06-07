@echo off
cd /d D:\WB_Workflow
C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe -m http.server 8080 --directory D:\WB_Workflow > http8080.log 2>&1
