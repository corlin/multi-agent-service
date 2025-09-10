#!/usr/bin/env python3
"""
专利系统性能测试执行脚本

使用uv run执行专利系统性能测试的便捷脚本。
"""

import subprocess
import sys
import os
from pathlib import Path


def run_performance_tests():
    """运行专利系统性能测试"""
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🚀 开始运行专利系统性能测试...")
    print(f"📁 工作目录: {project_root}")
    
    # 构建uv run命令
    cmd = [
        "uv", "run", 
        "python", "tests/performance/run_performance_tests.py",
        "--quick"  # 使用快速模式
    ]
    
    try:
        # 执行性能测试
        print(f"🔧 执行命令: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=False, capture_output=False)
        
        if result.returncode == 0:
            print("\n✅ 性能测试全部通过！")
        elif result.returncode == 1:
            print("\n⚠️  性能测试完成，但存在警告")
        else:
            print("\n❌ 性能测试失败")
        
        return result.returncode
        
    except FileNotFoundError:
        print("❌ 错误: 未找到uv命令，请确保已安装uv")
        print("安装uv: curl -LsSf https://astral.sh/uv/install.sh | sh")
        return 1
    except Exception as e:
        print(f"❌ 执行性能测试时发生错误: {e}")
        return 1


def run_specific_tests():
    """运行特定的性能测试"""
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🎯 运行特定性能测试...")
    
    # 可以指定特定的测试
    cmd = [
        "uv", "run", 
        "python", "tests/performance/run_performance_tests.py",
        "--tests", 
        "single_agent_baseline",
        "concurrent_analysis_light"
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ 执行特定测试时发生错误: {e}")
        return 1


def run_pytest_performance_tests():
    """使用pytest运行性能测试"""
    
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    print("🧪 使用pytest运行性能测试...")
    
    # 使用uv run pytest执行性能测试
    cmd = [
        "uv", "run", "pytest", 
        "tests/performance/",
        "-v",
        "--tb=short",
        "-x"  # 遇到第一个失败就停止
    ]
    
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        print(f"❌ 执行pytest性能测试时发生错误: {e}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "specific":
            exit_code = run_specific_tests()
        elif sys.argv[1] == "pytest":
            exit_code = run_pytest_performance_tests()
        else:
            print("用法: python scripts/run_patent_performance_tests.py [specific|pytest]")
            exit_code = 1
    else:
        exit_code = run_performance_tests()
    
    sys.exit(exit_code)