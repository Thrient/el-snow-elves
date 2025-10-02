@echo off
setlocal enabledelayedexpansion

title 时雪 Update

echo.
echo ========================================
echo           时雪 自动更新脚本
echo ========================================
echo.


set "API_URL=https://gitee.com/api/v5/repos/thrient/elves/releases/latest?access_token=9fe431e0d9c1cf6dcfcff07c88dbd3c6"
set "TARGET_FILE_NAME=Elves.zip"
set "TARGET_FOLDER=Update"
set "SELF_FILE=%~nx0"

echo [信息] 正在获取最新版本信息...

PowerShell -Command "$ProgressPreference='silentlyContinue'; try { $response = Invoke-WebRequest -Uri '%API_URL%' -Method Get -ErrorAction Stop | ConvertFrom-Json; $targetUrl = $response.assets | Where-Object { $_.name -eq '%TARGET_FILE_NAME%' } | Select-Object -ExpandProperty browser_download_url -ErrorAction Stop; Write-Output $targetUrl; } catch { Write-Output 'ERROR: ' + $_.Exception.Message; exit 1 }" > temp_result.txt

set "RESULT="
<"temp_result.txt" set /p RESULT=

del temp_result.txt 2>nul

if "!RESULT!"=="" (
    echo [错误] 无法获取版本信息，请检查网络连接
    goto end
) else if "!RESULT:~0,5!"=="ERROR" (
    echo [错误] !RESULT!
    goto end
) else (
    echo [成功] 已找到最新版本
    echo [下载] 正在下载 时雪 最新版本...

    curl -L -o "%TARGET_FILE_NAME%" "!RESULT!" --progress-bar
    
    if not exist "%TARGET_FILE_NAME%" (
        echo [错误] 文件下载失败
        goto end
    )

    echo [解压] 正在解压缩文件到 !TARGET_FOLDER! 目录...
        
    mkdir "%TARGET_FOLDER%" 2>nul

    PowerShell -Command "Expand-Archive -Path '%TARGET_FILE_NAME%' -DestinationPath '%TARGET_FOLDER%' -Force"
    
    echo [成功] 解压缩完成

    del "%TARGET_FILE_NAME%" 2>nul

)
echo [清理] 正在删除旧版本文件

for /f "delims=" %%i in ('dir /b /a 2^>nul') do (
    if "%%i" neq "!SELF_FILE!" if "%%i" neq "!TARGET_FOLDER!" (
        if exist "%%i\" (
            rmdir /s /q "%%i" 2>nul
        ) else (
            del /f /q "%%i" 2>nul
        )
    )
)

echo [更新] 正在移动新版本文件

for /f "delims=" %%i in ('dir /b /a "!TARGET_FOLDER!\"') do (
    if /i not "%%i"=="!SELF_FILE!" (
        move /y "!TARGET_FOLDER!\%%i" . 2>nul
    )
)


echo [启动] 正在启动

start "" "%~dp0Elves.exe"

move /y "!TARGET_FOLDER!\!SELF_FILE!" . 2>nul

rmdir /s /q "!TARGET_FOLDER!" 2>nul