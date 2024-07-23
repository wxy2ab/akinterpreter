@echo off

if not exist ".\env" (
    echo Environment not found. Installing Miniconda...
    pushd .\install
    call install.bat
    popd
    if errorlevel 1 (
        echo Installation failed. Please check the error messages above.
        exit /b 1
    )
)

echo Running main.py with the installed Python...
.\env\python.exe main.py