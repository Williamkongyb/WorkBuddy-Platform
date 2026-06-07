@echo off
chcp 65001 >nul
echo ================================================
echo   WorkBuddy 中台测试工具
echo ================================================
echo.

cd /d D:\WB_Workflow

echo [1/4] 检查服务状态...
netstat -an | findstr ":8080" >nul 2>&1
if %errorlevel%==0 (
    echo ✅ 端口 8080 已运行
) else (
    echo ⚠️  端口 8080 未运行，正在启动...
    start "HTTP Server :8080" cmd /k "C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe -m http.server 8080 --directory D:\WB_Workflow"
    timeout /t 3 >nul
)

netstat -an | findstr ":8000" >nul 2>&1
if %errorlevel%==0 (
    echo ✅ 端口 8000 已运行
) else (
    echo ⚠️  端口 8000 未运行，正在启动...
    start "AssetTracker :8000" cmd /k "C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe asset_server.py"
    timeout /t 3 >nul
)

netstat -an | findstr ":8300" >nul 2>&1
if %errorlevel%==0 (
    echo ✅ 端口 8300 已运行
) else (
    echo ⚠️  端口 8300 未运行，正在启动...
    start "Multi-Engine :8300" cmd /k "C:\Users\Confu\AppData\Local\Programs\Python\Python314\python.exe multi_engine_scheduler.py"
    timeout /t 3 >nul
)

echo.
echo [2/4] 等待服务启动...
timeout /t 5 >nul

echo.
echo [3/4] 打开整合版中台...
start "" "http://localhost:8080/workbuddy_platform_v4_integrated.html"

echo.
echo [4/4] 测试完成！
echo.
echo ================================================
echo   整合版中台已打开
echo ================================================
echo.
echo 功能列表：
echo   📊 运营仪表盘 v4.0
echo   🔧 工作流编排器 v3.0
echo   🎮 多引擎渲染面板
echo   📁 媒体资产管理器
echo.
echo 中台地址：<ADDRESS>http://localhost:8080/workbuddy_platform_v4_integrated.html</ADDRESS>
echo.
pause
