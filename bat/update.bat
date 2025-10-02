@echo off
setlocal enabledelayedexpansion

title ʱѩ Update

echo.
echo ========================================
echo           ʱѩ �Զ����½ű�
echo ========================================
echo.


set "API_URL=https://gitee.com/api/v5/repos/thrient/elves/releases/latest?access_token=9fe431e0d9c1cf6dcfcff07c88dbd3c6"
set "TARGET_FILE_NAME=Elves.zip"
set "TARGET_FOLDER=Update"
set "SELF_FILE=%~nx0"

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

    echo [��ѹ] ���ڽ�ѹ���ļ��� !TARGET_FOLDER! Ŀ¼...
        
    mkdir "%TARGET_FOLDER%" 2>nul

    PowerShell -Command "Expand-Archive -Path '%TARGET_FILE_NAME%' -DestinationPath '%TARGET_FOLDER%' -Force"
    
    echo [�ɹ�] ��ѹ�����

    del "%TARGET_FILE_NAME%" 2>nul

)
echo [����] ����ɾ���ɰ汾�ļ�

for /f "delims=" %%i in ('dir /b /a 2^>nul') do (
    if "%%i" neq "!SELF_FILE!" if "%%i" neq "!TARGET_FOLDER!" (
        if exist "%%i\" (
            rmdir /s /q "%%i" 2>nul
        ) else (
            del /f /q "%%i" 2>nul
        )
    )
)

echo [����] �����ƶ��°汾�ļ�

for /f "delims=" %%i in ('dir /b /a "!TARGET_FOLDER!\"') do (
    if /i not "%%i"=="!SELF_FILE!" (
        move /y "!TARGET_FOLDER!\%%i" . 2>nul
    )
)


echo [����] ��������

start "" "%~dp0Elves.exe"

move /y "!TARGET_FOLDER!\!SELF_FILE!" . 2>nul

rmdir /s /q "!TARGET_FOLDER!" 2>nul