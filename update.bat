@echo off
REM activate virtualenv
call .\env\Scripts\activate

REM  run ./install/update.py
python .\install\update.py

