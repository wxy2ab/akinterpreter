@echo off
set "env_dir=%~dp0..\env"  
call "%env_dir%\Scripts\activate.bat"

pip install tushare
pip install 'volcengine-python-sdk[ark]'
pip install tencentcloud-sdk-python-hunyuan
pip install  zhiquai
pip install google-cloud-aiplatform
