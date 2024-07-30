@echo off
REM activate virtualenv
call .\env\Scripts\activate

REM  run ./install/update.py
python .\install\update.py

REM  run ./install/build_or_recreate.py
python .\install\build_or_recreate.py

REM  install requirements
pip install -r requirements.txt

