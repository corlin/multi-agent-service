#!/usr/bin/env python3
"""
测试设置验证脚本

验证真实环境测试工具的基本设置和依赖是否正确。
"""

import sys
import json
import importlib
from pathlib import Path


def check_python_version():
    """检查Python版本."""
    print("🐍 检查Python版本...")
    version = sys.version_info
    
    if version.major >= 3 and version.minor >= 8:
        print(f"   ✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print("   需要Python 3.8或更高版本")
        return False


def check_required_modules():
    """检查必需的模块."""
    print("\n📦 检查必需模块...")
    
    required_modules = [
        "asyncio", "logging", "json", "time", "datetime", 
        "pathlib", "typing", "dataclasses", "tempfile"
    ]
    
    optional_modules = [
        "psutil", "concurrent.futures"
    ]
    
    missing_required = []
    missing_optional = []
    
    # 检查必需模块
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ❌ {module} (必需)")
            missing_required.append(module)
    
    # 检查可选模块
    for module in optional_modules:
        try:
            importlib.import_module(module)
            print(f"   ✅ {module}")
        except ImportError:
            print(f"   ⚠️  {module} (可选，建议安装)")
            missing_optional.append(module)
    
    if missing_required:
        print(f"\n   ❌ 缺少必需模块: {', '.join(missing_required)}")
        return False
    
    if missing_optional:
        print(f"\n   ⚠️  缺少可选模块: {', '.join(missing_optional)}")
        print("   建议安装: pip install psutil")
    
    return True


def check_project_structure():
    """检查项目结构."""
    print("\n📁 检查项目结构...")
    
    required_files = [
        "test_real_environment_scenarios.py",
        "run_real_environment_test.py", 
        "real_environment_test_config.json",
        "generate_test_data.py"
    ]
    
    optional_files = [
        "validate_patent_system.py",
        "src/multi_agent_service/core/patent_system_initializer.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} (必需)")
            missing_files.append(file_path)
    
    for file_path in optional_files:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ⚠️  {file_path} (可选)")
    
    if missing_files:
        print(f"\n   ❌ 缺少必需文件: {', '.join(missing_files)}")
        return False
    
    return True


def check_config_file():
    """检查配置文件."""
    print("\n⚙️  检查配置文件...")
    
    config_file = "real_environment_test_config.json"
    
    if not Path(config_file).exists():
        print(f"   ❌ 配置文件不存在: {config_file}")
        return False
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        required_sections = [
            "test_configuration",
            "performance_baselines", 
            "test_scenarios_config",
            "success_criteria"
        ]
        
        missing_sections = []
        for section in required_sections:
            if section in config:
                print(f"   ✅ {section}")
            else:
                print(f"   ❌ {section}")
                missing_sections.append(section)
        
        if missing_sections:
            print(f"\n   ❌ 配置文件缺少必需部分: {', '.join(missing_sections)}")
            return False
        
        print(f"   ✅ 配置文件格式正确")
        return True
        
    except json.JSONDecodeError as e:
        print(f"   ❌ 配置文件JSON格式错误: {e}")
        return False
    except Exception as e:
        print(f"   ❌ 读取配置文件失败: {e}")
        return False


def check_test_script_syntax():
    """检查测试脚本语法."""
    print("\n🔍 检查测试脚本语法...")
    
    test_scripts = [
        "test_real_environment_scenarios.py",
        "run_real_environment_test.py",
        "generate_test_data.py"
    ]
    
    syntax_errors = []
    
    for script in test_scripts:
        if not Path(script).exists():
            continue
            
        try:
            with open(script, 'r', encoding='utf-8') as f:
                code = f.read()
            
            compile(code, script, 'exec')
            print(f"   ✅ {script}")
            
        except SyntaxError as e:
            print(f"   ❌ {script}: 语法错误 - {e}")
            syntax_errors.append(script)
        except Exception as e:
            print(f"   ⚠️  {script}: 检查异常 - {e}")
    
    if syntax_errors:
        print(f"\n   ❌ 语法错误的脚本: {', '.join(syntax_errors)}")
        return False
    
    return True


def check_permissions():
    """检查文件权限."""
    print("\n🔐 检查文件权限...")
    
    executable_files = [
        "test_real_environment_scenarios.py",
        "run_real_environment_test.py",
        "generate_test_data.py",
        "validate_test_setup.py"
    ]
    
    permission_issues = []
    
    for file_path in executable_files:
        path = Path(file_path)
        if path.exists():
            try:
                # 尝试读取文件
                with open(path, 'r') as f:
                    f.read(1)
                print(f"   ✅ {file_path} (可读)")
            except PermissionError:
                print(f"   ❌ {file_path} (权限不足)")
                permission_issues.append(file_path)
            except Exception:
                print(f"   ⚠️  {file_path} (检查异常)")
    
    # 检查写入权限
    try:
        test_file = Path("test_write_permission.tmp")
        test_file.write_text("test")
        test_file.unlink()
        print(f"   ✅ 当前目录可写")
    except Exception:
        print(f"   ❌ 当前目录不可写")
        permission_issues.append("current_directory")
    
    if permission_issues:
        print(f"\n   ❌ 权限问题: {', '.join(permission_issues)}")
        return False
    
    return True


def generate_test_report(results):
    """生成验证报告."""
    print(f"\n{'='*60}")
    print(f"📋 验证报告")
    print(f"{'='*60}")
    
    total_checks = len(results)
    passed_checks = sum(1 for result in results.values() if result)
    
    print(f"总检查项: {total_checks}")
    print(f"通过检查: {passed_checks}")
    print(f"失败检查: {total_checks - passed_checks}")
    print(f"通过率: {passed_checks/total_checks:.1%}")
    
    print(f"\n详细结果:")
    for check_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"  - {check_name}: {status}")
    
    if passed_checks == total_checks:
        print(f"\n🎉 所有检查通过！测试环境设置正确。")
        print(f"可以运行以下命令开始测试:")
        print(f"  python generate_test_data.py")
        print(f"  python run_real_environment_test.py --mode quick")
        return True
    else:
        print(f"\n⚠️  部分检查失败，请修复上述问题后重新验证。")
        return False


def main():
    """主函数."""
    print("🔧 真实环境测试设置验证")
    print("="*60)
    print("验证测试工具的基本设置和依赖...")
    
    # 执行各项检查
    results = {
        "Python版本": check_python_version(),
        "必需模块": check_required_modules(), 
        "项目结构": check_project_structure(),
        "配置文件": check_config_file(),
        "脚本语法": check_test_script_syntax(),
        "文件权限": check_permissions()
    }
    
    # 生成报告
    success = generate_test_report(results)
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)