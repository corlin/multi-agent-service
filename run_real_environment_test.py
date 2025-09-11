#!/usr/bin/env python3
"""
真实环境测试运行脚本

简化的测试运行入口，支持不同的测试模式和配置选项。
"""

import asyncio
import argparse
import sys
import json
from pathlib import Path
from test_real_environment_scenarios import RealEnvironmentTester


def parse_arguments():
    """解析命令行参数."""
    parser = argparse.ArgumentParser(
        description="专利系统真实环境测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
测试模式:
  quick    - 快速测试（仅关键功能）
  standard - 标准测试（大部分功能）
  full     - 完整测试（所有功能）
  custom   - 自定义测试（指定类别）

示例:
  python run_real_environment_test.py --mode quick
  python run_real_environment_test.py --mode custom --categories system functionality
  python run_real_environment_test.py --mode full --config custom_config.json
        """
    )
    
    parser.add_argument(
        "--mode", 
        choices=["quick", "standard", "full", "custom"],
        default="standard",
        help="测试模式 (默认: standard)"
    )
    
    parser.add_argument(
        "--categories",
        nargs="+",
        choices=["system", "functionality", "workflow", "performance", "scalability", "reliability", "integration", "stability"],
        help="自定义模式下的测试类别"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        default="real_environment_test_config.json",
        help="配置文件路径 (默认: real_environment_test_config.json)"
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="real_environment_test_report.json",
        help="输出报告文件路径"
    )
    
    parser.add_argument(
        "--timeout",
        type=int,
        default=600,
        help="总测试超时时间（秒）"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出模式"
    )
    
    return parser.parse_args()


async def main():
    """主函数."""
    args = parse_arguments()
    
    print("🚀 专利系统真实环境测试")
    print("="*60)
    print(f"测试模式: {args.mode}")
    
    if args.categories:
        print(f"测试类别: {', '.join(args.categories)}")
    
    try:
        # 创建测试器
        tester = RealEnvironmentTester()
        
        # 根据模式过滤测试场景
        if args.mode == "quick":
            # 只运行高优先级的系统和功能测试
            tester.test_scenarios = [
                s for s in tester.test_scenarios 
                if s.priority == "high" and s.category in ["system", "functionality"]
            ]
        elif args.mode == "standard":
            # 运行高和中优先级测试，排除稳定性测试
            tester.test_scenarios = [
                s for s in tester.test_scenarios 
                if s.priority in ["high", "medium"] and s.category != "stability"
            ]
        elif args.mode == "custom" and args.categories:
            # 运行指定类别的测试
            tester.test_scenarios = [
                s for s in tester.test_scenarios 
                if s.category in args.categories
            ]
        # full 模式运行所有测试
        
        print(f"将运行 {len(tester.test_scenarios)} 个测试场景")
        print("="*60)
        
        # 运行测试
        summary = await tester.run_all_scenarios()
        
        # 保存自定义输出文件
        if args.output != "real_environment_test_report.json":
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            print(f"\n📋 报告已保存到: {args.output}")
        
        # 返回退出码
        return 0 if summary.get("overall_status") == "PASS" else 1
        
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
        return 0
    except Exception as e:
        print(f"\n❌ 测试执行失败: {str(e)}")
        return 2


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)