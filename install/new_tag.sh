#!/bin/bash

# 检查是否有需要提交的更改
if [[ -n $(git status -s) ]]; then
    echo "有文件需要提交，正在执行提交和推送操作..."
    git add .
    git commit -m "自动提交更改"
    git push
    echo "等待30秒..."
    sleep 30
else
    echo "没有需要提交的更改。"
fi

# 执行pull操作
echo "正在执行pull操作..."
git pull

# 读取版本号
version_file="./core/__init__.py"
if [[ ! -f "$version_file" ]]; then
    echo "错误：版本文件不存在"
    exit 1
fi

version=$(grep "__version__" "$version_file" | cut -d '"' -f2)
echo "当前版本号: $version"

# 创建新的tag
git tag "v$version"
git push origin "v$version"

echo "新的tag v$version 已创建并推送到远程仓库。"