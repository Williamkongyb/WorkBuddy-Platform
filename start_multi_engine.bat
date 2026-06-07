@echo off
cd /d D:\WB_Workflow

echo ===================================================
echo  Starting Multi-Engine Render API (Flask :8300)
echo ===================================================
echo.

C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe ^
  -c "from multi_engine_scheduler import create_app; create_app(port=8300)" ^
  > multi_engine_api.log 2>&1
