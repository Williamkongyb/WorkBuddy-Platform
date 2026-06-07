@echo off
cd /d D:\WB_Workflow
C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe multi_engine_scheduler.py --serve --port 8300 > multi_engine_api.log 2>&1
