---
title: 安装
nextjs:
  metadata:
    title: 安装
    description: 针对有python环境，或者代码基础的推荐安装步骤.
---

目前还是推荐大家直接下载源代码来安装。但是这个需要一定的代码基础。需要熟悉如何配置python环境。  

---

## 下载清华源的miniconda

到这个地址：![https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/) 下载miniconda   
推荐这个版本，因为安装比较快。如果使用官方版本，有的时候需要自求多福。   

* **windows**
推荐 ![https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.5.0-0-Windows-x86_64.exe](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.5.0-0-Windows-x86_64.exe)

* **linux**   
intel cpu:   
![https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.5.0-0-Linux-x86_64.sh](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.5.0-0-Linux-x86_64.sh)   

arm cpu:   
![https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.5.0-0-Linux-aarch64.sh](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.5.0-0-Linux-aarch64.sh)

* **mac**
m系列cpu:    
![https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.4.0-0-MacOSX-arm64.sh](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.4.0-0-MacOSX-arm64.sh)

intel cpu:    
![https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.4.0-0-MacOSX-x86_64.sh](https://mirrors.tuna.tsinghua.edu.cn/anaconda/miniconda/Miniconda3-py312_24.4.0-0-MacOSX-x86_64.sh)

## 安装

```bash
# 克隆项目
git clone git@github.com:wxy2ab/akinterpreter.git

# 进入项目目录
cd akinterpreter

# 可选，创建虚拟环境
conda create -p ./env python=3.12

# 激活虚拟环境
conda activate ./env

# 安装依赖
pip install -r requirments.txt

# 启动cli
python cli.py

# 启动web
python main.py
```

## 修改配置

参考修改配置的章节


## 运行
```bash
# 启动cli
python cli.py

# 启动web
python main.py
```



