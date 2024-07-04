# -*- coding:utf-8 -*-
#测试配置文件

# 设置是否在遇到错误时继续执行
continue_on_error = True  # 设置是否在遇到错误时继续执行

##设置日志文件名
log_file = ""  # 不记录日志

#需要测试的测试模块
#在tests数组中添加需要测试的模块
#测试模块需要以test_开头
#模块中test_开头的函数会被测试
#tests = ["test_stat", "test_tick_loader", "test_candle_loader"]
tests = ["*"]