#!/bin/bash

# 确保我们在主分支上
git checkout main

# 创建一个新的孤立分支
git checkout --orphan gh-pages

# 删除所有文件
git rm -rf .

# 创建一个空的 index.html 文件
echo "<!DOCTYPE html><html><body><h1>GitHub Pages Placeholder</h1></body></html>" > index.html

# 添加并提交这个文件
git add index.html
git commit -m "Initial gh-pages commit"

# 推送到远程仓库
git push origin gh-pages

# 切回主分支
git checkout main