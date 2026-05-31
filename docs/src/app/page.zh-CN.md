---
title: akinterpreter
---

[English](./page.md) | **简体中文**

akinterpreter 是一个完全免费的开源项目，基于MIT协议发布，欢迎家人们参与到项目的开发和建设之中. {% .lead %}

{% quick-links %}

{% quick-link title="安装" icon="installation" href="/docs/non_python_install" description="如何安装akinterpreter" /%}

{% quick-link title="配置" icon="presets" href="/docs/select_llm_api" description="配置akinterpreter." /%}

{% quick-link title="使用" icon="plugins" href="/docs/instruction" description="如何使用." /%}

{% quick-link title="技巧" icon="theming" href="/docs/use_outside" description="学习一点使用技巧." /%}

{% /quick-links %}



---

## 快速开始

只需要简单几个步骤，立刻上手使用akinterpreter.

### 下载代码

从github仓库下载源代码

```bash
git clone git@github.com:wxy2ab/akinterpreter.git
```


{% callout type="warning" title="发现bug，哈哈😄，对不起你，但真的难免啦" %}
akinterpreter 现在处于早期阶段，每天可能都会有大量的代码签入。所以不可避免的会遇到 `虫子` 如果遇到`虫子`，恳请移步 [issues](https://github.com/wxy2ab/akinterpreter/issues) 提交。大家的使用和参与，提供反馈和意见，才是akinterpreter进步的基石。
{% /callout %}

### 创建虚拟环境

下载代码之后，最好创建虚拟环境

```bash
# 进入项目目录
cd akinterpreter

# 可选，创建虚拟环境, 开发使用python3.12 ，其他版本没测试过，理论上3.10+版本应该都可以(使用了3.10的特性，但是没测试过)
conda create -p ./env python=3.12

# 激活虚拟环境
conda activate ./env
```

{% callout title="为什么推荐在项目目录配置虚拟环境" %}
大家可能都习惯于用自己的虚拟环境。但是对于akinterpreter,推荐大家在项目目录下创建虚拟环境。这是因为akinterpreter是代码生成器，会用到非常多库，你会发现依赖非常多。其实很多并非项目自身的依赖，而是生成代码运行所需的依赖。为了便于管理和维护，建议大家在项目目录下创建虚拟环境。因为每次更新代码，都推荐大家执行一次pip install -r requirements.txt。
{% /callout %}

---

## 安装依赖

```bash
# 每次更新代码，都建议执行一次，避免新的代码特性无法使用
pip install -r requirements.txt
```

## 启动

### cli启动
```bash
python cli.py
```

### web启动

```bash
python main.py
```
打开浏览器，访问 `http://localhost:8181/`

### 如何使用

在输入框输入想要查询或者分析的内容即可。   
    
比如:    
```text
黄金期货今年的走势分析
```

---


## 如何使用tushare
tushare是一个优质的数据平台   
如果想使用tushare，需要两个步骤：  
1. 运行./install/install_additional.bat    
在./install目录下，找到install_additional.bat，执行它。    
这个bat文件会帮你执行pip install tushare   
```shell
.\install\install_additional.bat
```
2. 配置tushare的key    
在settings.ini中，找到tushare_key，填入你申请的key。    
tushare的API KEY 申请地址：[https://tushare.pro/register](https://tushare.pro/register)    
申请之后，还要联系客服，开通权限。    
有了权限之后，在settings.ini中，找到tushare_key，填入你申请的key 就可以使用tushare了   
