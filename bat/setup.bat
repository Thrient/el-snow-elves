@echo off
setlocal enabledelayedexpansion

title 时雪 Setup

echo.
echo ========================================
echo           时雪 自动安装脚本
echo ========================================
echo.

set "name=时雪.lnk"

set "target=%~dp0Elves\Elves.exe"

set "API_URL=https://gitee.com/api/v5/repos/thrient/elves/releases/latest?access_token=9fe431e0d9c1cf6dcfcff07c88dbd3c6"
set "TARGET_FILE_NAME=Elves.zip"
set "TARGET_FOLDER=Elves"

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

    if exist "%TARGET_FOLDER%" (
        echo [清理] 删除旧版本文件...
        rmdir /s /q "%TARGET_FOLDER%" 2>nul
    )

    echo [解压] 正在解压缩文件到 !TARGET_FOLDER! 目录...
        
    mkdir "%TARGET_FOLDER%" 2>nul

    PowerShell -Command "Expand-Archive -Path '%TARGET_FILE_NAME%' -DestinationPath '%TARGET_FOLDER%' -Force"
    
    echo [成功] 解压缩完成

    del "%TARGET_FILE_NAME%" 2>nul

)

:end

echo [创建] 正在创建桌面快捷方式

for /f "delims=" %%a in ('powershell -command "[Environment]::GetFolderPath('Desktop')"') do set "desktop=%%a"

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $shortcut = $WshShell.CreateShortcut('%desktop%\%name%'); $shortcut.TargetPath = '%target%'; $shortcut.WorkingDirectory = (Split-Path '%target%' -Parent); $shortcut.Save()"

echo [启动] 正在启动

start "" "%~dp0Elves\Elves.exe"

powershell -Command Remove-Item "%~f0" -Force 2>nul & exit /b
