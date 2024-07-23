@echo off
set MINICONDA_URL=https://mirror.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.5.0-0-Windows-x86_64.exe
set INSTALLER_PATH=%TEMP%\miniconda_installer.exe

echo Downloading Miniconda...
powershell -Command "Invoke-WebRequest -Uri '%MINICONDA_URL%' -OutFile '%INSTALLER_PATH%'"

echo Installing Miniconda...
start /wait "" "%INSTALLER_PATH%" /S /D=%CD%\env

echo Installing requirements...
call .\env\Scripts\activate.bat
pip install -r requirements.txt

echo Miniconda installation and setup complete.