@echo off
chcp 65001 >nul 2>&1
echo === WorkBuddy 中台模块验证 ===
echo.

for %%f in (dashboard_v4 workflow_editor_v3 multi_engine_panel asset_tracker_demo) do (
    curl -s -o NUL -w "%%{http_code}" http://localhost:8080/%%f.html > temp_code.txt 2>nul
    set /p code=<temp_code.txt
    if "!code!"=="200" (
        echo ✅ %%f.html - 正常
    ) else (
        echo ❌ %%f.html - 错误: !code!
    )
    del temp_code.txt 2>nul
)

echo.
echo === 验证完成 ===
pause
