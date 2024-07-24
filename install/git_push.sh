#!/bin/bash

# 获取提交说明参数
commit_message="${1:-自动提交文件}"

# 检查是否有需要提交的更改
if [[ -z $(git status -s) ]]; then
    echo "没有需要提交的更改。"
else
    # 有文件需要提交，执行提交和推送操作
    echo "有文件需要提交，正在执行提交和推送操作..."
    git add .
    git commit -m "$commit_message"
    git push

    echo "等待30秒..."
    sleep 30
fi

# 执行pull操作
echo "正在执行pull操作..."
git pull

echo "操作完成。"