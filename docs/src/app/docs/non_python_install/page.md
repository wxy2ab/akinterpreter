---
title: 没有python环境如何安装
nextjs:
  metadata:
    title: 没有python环境如何安装
    description: 不是所有人都有python环境，如果没有python环境，不懂代码，可以安装akinterpreter吗.
---

其实akinterpreter的存在，最大的意义就是给不懂代码的朋友提供了查询分析的工具。降低了代码的学习成本，和工具的使用成本。哪怕你毫无基础。其实也是可以使用的。

---

##  下载release包

很抱歉，现在的安装还不能做的非常智能和自动化，不过安装过程依然简单.   
访问[https://github.com/wxy2ab/akinterpreter/releases](https://github.com/wxy2ab/akinterpreter/releases)    
在这个页面找到最新的zip包，下载到本地。    
比如 `akinterpreter-0.1.15.zip`    

### 解压缩到飞中文目录

把上一部下载的zip文件，解压缩到一个`磁盘空间足够`,`没有中文路径`的地方.   
因为中文路径可能会导致运行所需的虚拟环境工作不正常。所以切记路径`不要有中文`

比如解压到 `D:\akinterpreter-0.1.15`   

这时候你的目录结构应该是这样的:   
```text
akinterpreter
|-- client
|-- framework
|-- update.sh
|-- wxy2ab.json
|-- cli.py
|-- json
|-- directly.py
|-- install
|-- run.bat  <---Windows注意这个文件
|-- routes
|-- output
|-- core
|-- update.bat
|-- LICENSE
|-- database
|-- run.sh   <---linux/mac注意这个文件
|-- .github
|-- README.md
|-- test
|-- requirements.txt
|-- setting.ini
|-- docs
|-- CONTRIBUTING.md
|-- main.py
|-- setting.ini.template   <---把这个文件的后缀去掉，变成setting.ini
|-- test.py
|-- .vscode
|-- modules
`-- static
```

## 配置setting.ini
请参考配置的章节对setting.ini进行配置。

## 运行

### Windows
 如果是windows，直接双击`run.bat`运行。
 ```shell
 ./run.bat
 ```

### Linux/Mac
 如果是linux/mac，请使用终端运行`run.sh`。
 ```shell
 chmod +x ./run.sh
 ./run.sh
 ```

{% callout title="第一次运行很慢" %}
注意，第一次运行会很慢，因为要下载python虚拟环境，还有很多依赖项。  
如果第一次安装依赖项失败，会导致无法运行   
这个时候删除 ./env 目录。然后重新运行`run.sh` or `run.bat`  
{% /callout %}


---

## 开始使用

安装完成之后，浏览器访问 [http://localhost:8181](http://localhost:8181) 就可以开始使用了。
