@echo off
setlocal enabledelayedexpansion

REM 获取提交说明参数
set "commit_message=%~1"
if "%commit_message%"=="" set "commit_message=自动提交文件"

REM 检查是否有需要提交的更改
git status --porcelain > nul
if %errorlevel% equ 0 (
    echo 没有需要提交的更改。
    goto pull
)

REM 有文件需要提交，执行提交和推送操作
echo 有文件需要提交，正在执行提交和推送操作...
git add .
git commit -m "%commit_message%"
git push

echo 等待30秒...
timeout /t 30 /nobreak

:pull
REM 执行pull操作
echo 正在执行pull操作...
git pull

echo 操作完成。