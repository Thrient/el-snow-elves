@echo off
setlocal enabledelayedexpansion

title ʱѩ Setup

echo.
echo ========================================
echo           ʱѩ �Զ���װ�ű�
echo ========================================
echo.

set "name=ʱѩ.lnk"

set "target=%~dp0Elves\Elves.exe"

set "API_URL=https://gitee.com/api/v5/repos/thrient/elves/releases/latest?access_token=9fe431e0d9c1cf6dcfcff07c88dbd3c6"
set "TARGET_FILE_NAME=Elves.zip"
set "TARGET_FOLDER=Elves"

echo [��Ϣ] ���ڻ�ȡ���°汾��Ϣ...

PowerShell -Command "$ProgressPreference='silentlyContinue'; try { $response = Invoke-WebRequest -Uri '%API_URL%' -Method Get -ErrorAction Stop | ConvertFrom-Json; $targetUrl = $response.assets | Where-Object { $_.name -eq '%TARGET_FILE_NAME%' } | Select-Object -ExpandProperty browser_download_url -ErrorAction Stop; Write-Output $targetUrl; } catch { Write-Output 'ERROR: ' + $_.Exception.Message; exit 1 }" > temp_result.txt


set "RESULT="
<"temp_result.txt" set /p RESULT=

del temp_result.txt 2>nul

if "!RESULT!"=="" (
    echo [����] �޷���ȡ�汾��Ϣ��������������
    goto end
) else if "!RESULT:~0,5!"=="ERROR" (
    echo [����] !RESULT!
    goto end
) else (
    echo [�ɹ�] ���ҵ����°汾
    echo [����] �������� ʱѩ ���°汾...

    curl -L -o "%TARGET_FILE_NAME%" "!RESULT!" --progress-bar
    
    if not exist "%TARGET_FILE_NAME%" (
        echo [����] �ļ�����ʧ��
        goto end
    )

    if exist "%TARGET_FOLDER%" (
        echo [����] ɾ���ɰ汾�ļ�...
        rmdir /s /q "%TARGET_FOLDER%" 2>nul
    )

    echo [��ѹ] ���ڽ�ѹ���ļ��� !TARGET_FOLDER! Ŀ¼...
        
    mkdir "%TARGET_FOLDER%" 2>nul

    PowerShell -Command "Expand-Archive -Path '%TARGET_FILE_NAME%' -DestinationPath '%TARGET_FOLDER%' -Force"
    
    echo [�ɹ�] ��ѹ�����

    del "%TARGET_FILE_NAME%" 2>nul

)

:end

echo [����] ���ڴ��������ݷ�ʽ

for /f "delims=" %%a in ('powershell -command "[Environment]::GetFolderPath('Desktop')"') do set "desktop=%%a"

powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $shortcut = $WshShell.CreateShortcut('%desktop%\%name%'); $shortcut.TargetPath = '%target%'; $shortcut.WorkingDirectory = (Split-Path '%target%' -Parent); $shortcut.Save()"

echo [����] ��������

start "" "%~dp0Elves\Elves.exe"

powershell -Command Remove-Item "%~f0" -Force 2>nul & exit /b
