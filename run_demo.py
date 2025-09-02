#!/usr/bin/env python3
"""
多智能体服务演示启动器
Multi-Agent Service Demo Launcher
"""

import os
import sys
import subprocess
import time
from dotenv import load_dotenv


def print_header(title: str):
    """打印标题"""
    print(f"\n{'='*60}")
    print(f"🚀 {title}")
    print(f"{'='*60}")


def print_section(title: str):
    """打印章节"""
    print(f"\n{'-'*40}")
    print(f"📋 {title}")
    print(f"{'-'*40}")


def check_environment():
    """检查环境"""
    print_section("环境检查")
    
    # 检查Python版本
    python_version = sys.version_info
    print(f"🐍 Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    if python_version < (3, 12):
        print("❌ 需要Python 3.12或更高版本")
        return False
    else:
        print("✅ Python版本符合要求")
    
    # 检查依赖
    required_packages = [
        "fastapi",
        "uvicorn", 
        "httpx",
        "pydantic",
        "python-dotenv"
    ]
    
    print(f"\n📦 检查依赖包:")
    missing_packages = []
    
    for package in required_packages:
        try:
            # Special handling for python-dotenv which imports as 'dotenv'
            if package == "python-dotenv":
                __import__("dotenv")
            else:
                __import__(package.replace("-", "_"))
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} - 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ 缺少依赖包: {', '.join(missing_packages)}")
        print("请运行: uv sync")
        return False
    
    # 检查配置文件
    config_files = [
        "config/agents.json",
        "config/models.json",
        "config/workflows.json"
    ]
    
    print(f"\n📁 检查配置文件:")
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"   ✅ {config_file}")
        else:
            print(f"   ❌ {config_file} - 文件不存在")
            return False
    
    # 检查API密钥
    load_dotenv()
    
    api_keys = {
        "QWEN_API_KEY": os.getenv("QWEN_API_KEY"),
        "DEEPSEEK_API_KEY": os.getenv("DEEPSEEK_API_KEY"),
        "GLM_API_KEY": os.getenv("GLM_API_KEY")
    }
    
    print(f"\n🔑 检查API密钥:")
    valid_keys = 0
    
    for key_name, key_value in api_keys.items():
        if key_value and not key_value.startswith("your_"):
            print(f"   ✅ {key_name}: {key_value[:10]}...")
            valid_keys += 1
        else:
            print(f"   ❌ {key_name}: 未配置")
    
    if valid_keys == 0:
        print(f"\n⚠️ 警告: 没有找到有效的API密钥")
        print("某些功能可能无法正常工作")
        print("请检查 .env 文件配置")
    else:
        print(f"\n✅ 找到 {valid_keys} 个有效的API密钥")
    
    return True


def run_demo(demo_type: str):
    """运行指定类型的演示"""
    demo_files = {
        "quick": "quick_demo.py",
        "api": "api_demo.py", 
        "interactive": "interactive_demo.py",
        "comprehensive": "comprehensive_demo.py"
    }
    
    if demo_type not in demo_files:
        print(f"❌ 未知的演示类型: {demo_type}")
        return False
    
    demo_file = demo_files[demo_type]
    
    if not os.path.exists(demo_file):
        print(f"❌ 演示文件不存在: {demo_file}")
        return False
    
    print(f"🚀 启动 {demo_type} 演示...")
    
    try:
        # 运行演示
        result = subprocess.run([sys.executable, demo_file], check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ 演示运行失败: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n👋 演示被用户中断")
        return True


def start_service():
    """启动服务"""
    print_section("启动服务")
    
    print("🚀 启动多智能体服务...")
    print("📝 日志级别: INFO")
    print("🌐 访问地址: http://localhost:8000")
    print("📚 API文档: http://localhost:8000/docs")
    print("\n按 Ctrl+C 停止服务\n")
    
    try:
        subprocess.run([
            "uv", "run", "uvicorn", 
            "src.multi_agent_service.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 服务启动失败: {e}")
        return False
    except KeyboardInterrupt:
        print(f"\n👋 服务已停止")
        return True


def show_menu():
    """显示菜单"""
    print_header("多智能体服务演示启动器")
    
    print("🎯 可用的演示选项:")
    print("   1. 快速演示 (quick) - 核心功能展示，无需启动服务")
    print("   2. API演示 (api) - 完整API接口测试，需要先启动服务")
    print("   3. 交互式演示 (interactive) - 包含交互式聊天，需要先启动服务")
    print("   4. 综合演示 (comprehensive) - 多提供商模型服务演示")
    print("   5. 启动服务 (service) - 启动FastAPI服务")
    print("   6. 环境检查 (check) - 检查环境配置")
    print("   7. 退出 (quit)")
    
    return input(f"\n请选择演示类型 (1-7): ").strip()


def main():
    """主函数"""
    while True:
        choice = show_menu()
        
        if choice in ['1', 'quick']:
            if check_environment():
                run_demo('quick')
            
        elif choice in ['2', 'api']:
            if check_environment():
                print(f"\n⚠️ 注意: API演示需要服务运行在 http://localhost:8000")
                print("如果服务未启动，请先选择选项5启动服务")
                
                confirm = input("继续API演示? (y/n): ").strip().lower()
                if confirm in ['y', 'yes', '是']:
                    run_demo('api')
            
        elif choice in ['3', 'interactive']:
            if check_environment():
                print(f"\n⚠️ 注意: 交互式演示会自动启动服务")
                print("这可能需要一些时间，请耐心等待")
                
                confirm = input("继续交互式演示? (y/n): ").strip().lower()
                if confirm in ['y', 'yes', '是']:
                    run_demo('interactive')
            
        elif choice in ['4', 'comprehensive']:
            if check_environment():
                run_demo('comprehensive')
            
        elif choice in ['5', 'service']:
            if check_environment():
                start_service()
            
        elif choice in ['6', 'check']:
            check_environment()
            
        elif choice in ['7', 'quit', 'exit', '退出']:
            print("👋 再见！")
            break
            
        else:
            print("❌ 无效选择，请重新输入")
        
        # 询问是否继续
        if choice not in ['7', 'quit', 'exit', '退出']:
            continue_choice = input(f"\n按回车键返回主菜单，或输入 'q' 退出: ").strip()
            if continue_choice.lower() in ['q', 'quit', 'exit']:
                print("👋 再见！")
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n👋 程序被用户中断")
    except Exception as e:
        print(f"\n❌ 程序出错: {e}")