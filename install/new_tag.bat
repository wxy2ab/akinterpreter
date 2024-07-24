@echo off
setlocal enabledelayedexpansion

REM 检查是否有需要提交的更改
git status --porcelain > nul
if %errorlevel% neq 0 (
    echo 有文件需要提交，正在执行提交和推送操作...
    git add .
    git commit -m "自动提交更改"
    git push
    echo 等待30秒...
    timeout /t 30 /nobreak
) else (
    echo 没有需要提交的更改。
)

REM 执行pull操作
echo 正在执行pull操作...
git pull

REM 读取版本号
set "version_file=.\core\__init__.py"
if not exist "%version_file%" (
    echo 错误：版本文件不存在
    exit /b 1
)

for /f "tokens=2 delims=''" %%a in ('type "%version_file%" ^| findstr "__version__"') do (
    set "version=%%a"
)

echo 当前版本号: %version%

REM 创建新的tag
git tag v%version%
git push origin v%version%

echo 新的tag v%version% 已创建并推送到远程仓库。