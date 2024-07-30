#!/bin/bash

# 激活虚拟环境
source ./env/bin/activate

# 运行 ./install/update.py
python ./install/update.py

# 运行 ./install/build_or_recreate.py
python ./install/build_or_recreate.py

# install requirements
pip install -r requirements.txt