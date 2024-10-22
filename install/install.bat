@echo off
setlocal enabledelayedexpansion

:: Set variables
set SCRIPT_DIR=%~dp0
set MINICONDA_URL=https://mirror.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.5.0-0-Windows-x86_64.exe
set INSTALLER_PATH=%SCRIPT_DIR%miniconda_installer.exe 
set ENV_PATH=%SCRIPT_DIR%env

:: Check if Conda exists in specified directories or PATH environment variable
set CONDA_FOUND=0
for %%P in (C:\miniconda3 D:\miniconda3 C:\Users\%USERNAME%\miniconda3 C:\app\conda\ D:\app\conda\ C:\Users\%USERNAME%\anaconda3 C:\anaconda3 D:\anaconda3) do (
    if exist "%%P\Scripts\conda.exe" (
        set CONDA_FOUND=1
        set MINICONDA_PATH=%%P
        echo Conda is already installed at %MINICONDA_PATH%
        goto skip_install
    )
)

if %CONDA_FOUND%==0 (
    for %%P in (%PATHEXT%) do (
        for %%A in ("%PATH:;=" "%") do (
            if exist "%%~A\conda%%P" (
                set CONDA_FOUND=1
                set MINICONDA_PATH=%%~dpA
                echo Conda is already installed at %MINICONDA_PATH%
                goto skip_install
            )
        )
    )
)

:: 1. Check free space on C, D, and E drives
for %%D in (C D E) do (
    set "FREE_SPACE=%%D:"
    for /f "tokens=3" %%F in ('dir /-c "%%D:\" ^| find "bytes free"') do set FREE_SPACE=%%F 
    set FREE_SPACE=!FREE_SPACE:,=! 
    set "DISK_FREE[%%D]=!FREE_SPACE!"
)

:: 2. Find the drive with the most free space
set MAX_DISK=C
for /f "tokens=2,3 delims=[]" %%D in ('set DISK_FREE[') do (
    if !DISK_FREE[%%D]! gtr !DISK_FREE[%MAX_DISK%]! set MAX_DISK=%%D
)

:: 3. Set Miniconda installation path
set MINICONDA_PATH=%MAX_DISK%:\miniconda3

:: 4. Download and install Miniconda (if not found)
:skip_install
if %CONDA_FOUND%==0 (
    echo Downloading Miniconda...
    powershell.exe -Command "Invoke-WebRequest -Uri '%MINICONDA_URL%' -OutFile '%INSTALLER_PATH%'" 
    if !errorlevel! NEQ 0 (
        echo Error downloading Miniconda. Please check your internet connection and try again.
        exit /b 1
    )

    echo Installing Miniconda...
    start /wait "" "%INSTALLER_PATH%" /InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /S /D="%MINICONDA_PATH%"

    if !errorlevel! NEQ 0 (
        echo Error installing Miniconda. Please try again.
        exit /b 1
    )

    del "%INSTALLER_PATH%"
)

:: 5. Create virtual environment
echo Creating virtual environment...
"%MINICONDA_PATH%\Scripts\conda.exe" create -y -p "%ENV_PATH%" python=3.12

if !errorlevel! NEQ 0 (
    echo Error creating virtual environment. Please try again.
    exit /b 1
)

:: 6. Activate environment and install dependencies
echo Activating environment and installing dependencies...
call "%MINICONDA_PATH%\Scripts\activate.bat" %ENV_PATH% 

if !errorlevel! NEQ 0 (
    echo Error activating virtual environment. Please try again.
    exit /b 1
)

:: Execute pip install in the virtual environment
pip install -r "%SCRIPT_DIR%requirements.txt" 

if !errorlevel! NEQ 0 (
    echo Error installing dependencies. Please try again.
    exit /b 1
)

:: Execute Python script in the virtual environment
python "%SCRIPT_DIR%ctp_llm_strategy.py"

echo Setup completed successfully!