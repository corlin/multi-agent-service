#!/usr/bin/env python3
"""
多智能体演示启动器
Multi-Agent Demo Launcher

快速启动不同类型的多智能体演示
"""

import asyncio
import os
import subprocess
import sys
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
    """检查环境配置"""
    print_section("环境检查")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version >= (3, 12):
        print(f"✅ Python版本: {python_version.major}.{python_version.minor}")
    else:
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor} (需要3.12+)")
        return False
    
    # 检查依赖文件
    if os.path.exists("pyproject.toml"):
        print("✅ 项目配置文件存在")
    else:
        print("❌ 缺少 pyproject.toml 文件")
        return False
    
    # 检查环境变量
    load_dotenv()
    api_keys = [
        ("QWEN_API_KEY", os.getenv("QWEN_API_KEY")),
        ("DEEPSEEK_API_KEY", os.getenv("DEEPSEEK_API_KEY")),
        ("GLM_API_KEY", os.getenv("GLM_API_KEY"))
    ]
    
    valid_keys = 0
    for name, key in api_keys:
        if key and not key.startswith("your_"):
            print(f"✅ {name}: 已配置")
            valid_keys += 1
        else:
            print(f"❌ {name}: 未配置")
    
    if valid_keys > 0:
        print(f"✅ 找到 {valid_keys}/3 个有效API配置")
        return True
    else:
        print("❌ 没有找到有效的API配置")
        return False


def check_service_status():
    """检查服务状态"""
    print_section("服务状态检查")
    
    try:
        import httpx
        
        async def check():
            async with httpx.AsyncClient(timeout=3.0) as client:
                try:
                    response = await client.get("http://localhost:8000/api/v1/health")
                    if response.status_code == 200:
                        health = response.json()
                        if health.get("status") == "healthy":
                            print("✅ 多智能体服务运行正常")
                            return True
                    print("❌ 服务状态异常")
                    return False
                except Exception:
                    print("❌ 服务未启动")
                    return False
        
        return asyncio.run(check())
        
    except ImportError:
        print("❌ 缺少 httpx 依赖")
        return False


def start_service():
    """启动服务"""
    print_section("启动多智能体服务")
    
    try:
        print("🚀 正在启动服务...")
        print("📍 服务地址: http://localhost:8000")
        print("📚 API文档: http://localhost:8000/docs")
        print("⏹️  按 Ctrl+C 停止服务")
        
        # 启动服务
        subprocess.run([
            "uv", "run", "uvicorn", 
            "src.multi_agent_service.main:app",
            "--reload",
            "--host", "0.0.0.0",
            "--port", "8000"
        ])
        
    except KeyboardInterrupt:
        print("\n⏹️ 服务已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")


def run_demo(demo_file: str, demo_name: str):
    """运行演示程序"""
    print_section(f"运行 {demo_name}")
    
    if not os.path.exists(demo_file):
        print(f"❌ 演示文件不存在: {demo_file}")
        return
    
    try:
        print(f"🎬 启动演示: {demo_name}")
        subprocess.run(["python", demo_file])
    except KeyboardInterrupt:
        print(f"\n⏹️ 演示被中断")
    except Exception as e:
        print(f"❌ 演示失败: {e}")


def main():
    """主函数"""
    print_header("多智能体演示启动器")
    
    print("🎯 功能说明:")
    print("   • 环境检查和配置验证")
    print("   • 多智能体服务启动")
    print("   • 各种演示程序快速启动")
    
    while True:
        print_section("选择操作")
        print("1. 环境检查")
        print("2. 启动多智能体服务")
        print("3. 快速多智能体演示")
        print("4. 完整多智能体场景演示")
        print("5. 交互式多智能体演示")
        print("6. API接口测试")
        print("7. 一键快速演示 (无需服务)")
        print("8. 退出")
        
        choice = input("\n请选择 (1-8): ").strip()
        
        if choice == "1":
            env_ok = check_environment()
            if env_ok:
                print("\n✅ 环境检查通过，可以运行演示")
            else:
                print("\n❌ 环境检查失败，请先配置环境")
        
        elif choice == "2":
            start_service()
        
        elif choice == "3":
            if check_service_status():
                run_demo("quick_multi_agent_demo.py", "快速多智能体演示")
            else:
                print("❌ 需要先启动服务 (选择选项2)")
        
        elif choice == "4":
            if check_service_status():
                run_demo("multi_agent_interaction_demo.py", "完整多智能体场景演示")
            else:
                print("❌ 需要先启动服务 (选择选项2)")
        
        elif choice == "5":
            if check_service_status():
                run_demo("interactive_multi_agent_demo.py", "交互式多智能体演示")
            else:
                print("❌ 需要先启动服务 (选择选项2)")
        
        elif choice == "6":
            if check_service_status():
                run_demo("api_demo.py", "API接口测试")
            else:
                print("❌ 需要先启动服务 (选择选项2)")
        
        elif choice == "7":
            run_demo("demo.py", "一键快速演示")
        
        elif choice == "8":
            print("👋 感谢使用多智能体演示系统！")
            break
        
        else:
            print("❌ 无效选择，请重新输入")
        
        # 操作完成后暂停
        if choice in ["1", "3", "4", "5", "6", "7"]:
            input("\n按回车键继续...")


if __name__ == "__main__":
    main()