#!/bin/bash

env_dir="$(dirname "$0")/../env"

source "$env_dir/bin/activate"  # 激活虚拟环境 (如果适用)

pip install tushare
pip install 'volcengine-python-sdk[ark]'
pip install tencentcloud-sdk-python-hunyuan
pip install zhiquai
pip install google-cloud-aiplatform
