#!/usr/bin/env python3
import subprocess
import sys

def run_cmd(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip()
    except:
        return False, ""

def main():
    print("🚀 开始自动化版本管理...")
    
    # 获取修改描述
    if len(sys.argv) > 1:
        msg = sys.argv[1]
    else:
        msg = input("请输入修改描述: ").strip()
        if not msg:
            msg = "版本更新"
    
    # 检查是否有更改
    success, output = run_cmd("git status --porcelain")
    if not success or not output.strip():
        print("✅ 没有需要提交的更改")
        return
    
    # 获取当前版本号
    success, output = run_cmd("git tag -l")
    version_num = 1
    if success and output:
        versions = [v for v in output.split('\n') if v.startswith('v')]
        if versions:
            # 提取数字部分
            for v in versions:
                if '.' in v:
                    try:
                        num = int(v.split('.')[-1])
                        if num >= version_num:
                            version_num = num + 1
                    except:
                        pass
    
    current_version = f"v1.0.{version_num}"
    print(f"📝 新版本: {current_version}")
    print(f"📝 修改描述: {msg}")
    
    # 添加所有更改
    print("🔄 添加所有更改...")
    run_cmd("git add .")
    
    # 提交更改
    print("💾 提交更改...")
    run_cmd(f'git commit -m "{msg}"')
    
    # 创建版本标签
    print(f"🏷️ 创建版本标签: {current_version}")
    run_cmd(f'git tag -a "{current_version}" -m "版本 {current_version}: {msg}"')
    
    print(f"✅ 版本 {current_version} 创建完成！")
    
    # 显示版本历史
    print("📋 当前所有版本:")
    run_cmd("git tag -l | sort -V")

if __name__ == "__main__":
    main()
