#!/bin/bash

# 自动化版本管理脚本
# 使用方法: ./auto_version.sh "修改描述"

echo "🚀 开始自动化版本管理..."

# 获取当前最高版本号
current_version=$(git tag -l | grep "^v[0-9]\+\.[0-9]\+\.[0-9]\+$" | sort -V | tail -n1)

if [ -z "$current_version" ]; then
    # 如果没有版本标签，从v1.0.0开始
    new_version="v1.0.0"
    echo "📝 创建第一个版本: $new_version"
else
    # 解析版本号并递增
    major=$(echo $current_version | cut -d. -f1 | tr -d "v")
    minor=$(echo $current_version | cut -d. -f2)
    patch=$(echo $current_version | cut -d. -f3)
    
    # 递增补丁版本号
    new_patch=$((patch + 1))
    new_version="v$major.$minor.$new_patch"
    echo "�� 当前版本: $current_version -> 新版本: $new_version"
fi

# 获取修改描述
if [ -n "$1" ]; then
    commit_message="$1"
else
    commit_message="版本更新: $new_version"
fi

echo "🔄 添加所有更改到Git..."
git add .

echo "💾 提交更改..."
git commit -m "$commit_message"

echo "🏷️ 创建版本标签: $new_version"
git tag -a "$new_version" -m "版本 $new_version: $commit_message"

echo "📊 显示版本历史..."
git log --oneline --decorate -5

echo "✅ 版本 $new_version 创建完成！"
echo "📋 当前所有版本:"
git tag -l | sort -V
