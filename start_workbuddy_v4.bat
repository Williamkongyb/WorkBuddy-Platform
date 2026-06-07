@echo off
chcp 65001 > nul
title WorkBuddy 短视频智能中台 v4.0 — 统一启动脚本
color 0B

echo ╔══════════════════════════════════════════════════════╗
echo ║   WorkBuddy 短视频智能中台 v4.0 - 统一启动         ║
echo ╚══════════════════════════════════════════════════════╝
echo.

set PYTHON=C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe
set _ROOT=D:\WB_Workflow

echo [1/5] 启动 AssetTracker (端口 8000)...
start "WB-AssetTracker" /min "%_ROOT%\start_asset_server.bat"
echo    AssetTracker: http://localhost:8000/

echo [2/5] 启动 HTTP 静态服务 (端口 8080)...
start "WB-HTTP" /min "%_ROOT%\start_serve.bat"
echo    HTTP Server:  http://localhost:8080/

echo [3/5] 启动 Orchestrator 桥接 (端口 8200)...
start "WB-Orchestrator" /min "%_ROOT%\start_orchestrator_bridge.bat"
echo    Orchestrator: http://localhost:8200/

echo [4/5] 启动多引擎渲染调度器 (端口 8300)...
start "WB-MultiEngine" /min "%_ROOT%\start_multi_engine.bat"
echo    Multi-Engine: http://localhost:8300/

echo [5/5] 启动中台入口页...
timeout /t 3 /nobreak > nul
start "" http://localhost:8080/workbuddy_platform_v4.html

echo.
echo ╔══════════════════════════════════════════════════════╗
echo ║  所有服务启动完成!                                  ║
echo ╠══════════════════════════════════════════════════════╣
echo ║  中台入口:     http://localhost:8080/workbuddy_platform_v4.html
echo ║  仪表盘 v4.0:  http://localhost:8080/dashboard_v4.html
echo ║  工作流编排:   http://localhost:8080/workflow_editor_v2.html
echo ║  多引擎面板:   http://localhost:8080/multi_engine_panel.html
echo ║  资产管理:     http://localhost:8080/asset_tracker_demo.html
echo ╠══════════════════════════════════════════════════════╣
echo ║  API 端点:                                          ║
echo ║  AssetTracker: http://localhost:8000/api/status      ║
echo ║  Orchestrator: http://localhost:8200/api/pipeline/summary
echo ║  Multi-Engine: http://localhost:8300/api/status      ║
echo ╚══════════════════════════════════════════════════════╝
echo.

pause
