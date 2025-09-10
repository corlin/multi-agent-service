#!/usr/bin/env python3
"""
专利分析演示测试数据和验证脚本

这个脚本提供测试数据和验证功能，确保演示流程的正确性。
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class PatentDemoTestData:
    """专利演示测试数据类."""
    
    def __init__(self):
        """初始化测试数据."""
        self.sample_patents = self._generate_sample_patents()
        self.expected_responses = self._generate_expected_responses()
        self.validation_rules = self._define_validation_rules()
    
    def _generate_sample_patents(self) -> List[Dict[str, Any]]:
        """生成样本专利数据."""
        return [
            {
                "application_number": "CN202310001234.5",
                "title": "基于深度学习的图像识别方法及系统",
                "abstract": "本发明公开了一种基于深度学习的图像识别方法，通过卷积神经网络实现高精度图像分类...",
                "applicants": ["华为技术有限公司"],
                "inventors": ["张三", "李四"],
                "application_date": "2023-01-15",
                "publication_date": "2023-07-15",
                "ipc_classes": ["G06N3/04", "G06F18/24"],
                "country": "CN",
                "status": "已授权",
                "keywords": ["深度学习", "图像识别", "卷积神经网络"]
            },
            {
                "application_number": "US17/123456",
                "title": "Blockchain-based Smart Contract System",
                "abstract": "A blockchain-based smart contract system that enables secure and automated execution of contracts...",
                "applicants": ["IBM Corporation"],
                "inventors": ["John Smith", "Jane Doe"],
                "application_date": "2023-02-20",
                "publication_date": "2023-08-20",
                "ipc_classes": ["G06Q20/38", "H04L9/32"],
                "country": "US",
                "status": "审查中",
                "keywords": ["区块链", "智能合约", "分布式账本"]
            },
            {
                "application_number": "JP2023-567890",
                "title": "5G通信システムにおける信号処理方法",
                "abstract": "5G通信システムにおいて、高速かつ低遅延の信号処理を実現する方法を提供する...",
                "applicants": ["ソニー株式会社"],
                "inventors": ["田中太郎", "佐藤花子"],
                "application_date": "2023-03-10",
                "publication_date": "2023-09-10",
                "ipc_classes": ["H04W72/04", "H04L27/26"],
                "country": "JP",
                "status": "已公开",
                "keywords": ["5G", "通信技术", "信号处理"]
            }
        ]
    
    def _generate_expected_responses(self) -> Dict[str, Dict[str, Any]]:
        """生成预期响应模板."""
        return {
            "quick_search": {
                "min_confidence": 0.7,
                "expected_keywords": ["检索", "搜索", "专利"],
                "expected_sections": ["搜索结果", "数据统计"],
                "max_execution_time": 60
            },
            "comprehensive_analysis": {
                "min_confidence": 0.8,
                "expected_keywords": ["分析", "趋势", "技术", "竞争"],
                "expected_sections": ["数据收集", "搜索增强", "深度分析", "报告生成"],
                "max_execution_time": 300
            },
            "trend_analysis": {
                "min_confidence": 0.75,
                "expected_keywords": ["趋势", "发展", "年度", "增长"],
                "expected_sections": ["趋势分析", "技术发展"],
                "max_execution_time": 180
            },
            "competitive_analysis": {
                "min_confidence": 0.75,
                "expected_keywords": ["竞争", "申请人", "市场", "份额"],
                "expected_sections": ["竞争分析", "申请人分布"],
                "max_execution_time": 200
            }
        }
    
    def _define_validation_rules(self) -> Dict[str, Any]:
        """定义验证规则."""
        return {
            "response_structure": {
                "required_fields": ["agent_id", "content", "confidence"],
                "optional_fields": ["metadata", "next_actions"]
            },
            "content_quality": {
                "min_length": 50,
                "max_length": 10000,
                "required_patterns": [r"专利", r"分析|检索|搜索"]
            },
            "execution_metrics": {
                "max_total_time": 600,  # 10分钟
                "min_success_rate": 0.8
            }
        }
    
    def validate_demo_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """验证演示结果."""
        validation_result = {
            "is_valid": True,
            "score": 0.0,
            "issues": [],
            "recommendations": []
        }
        
        try:
            scenario = result.get("scenario", {})
            analysis_type = scenario.get("analysis_type", "unknown")
            
            # 基础结构验证
            if not result.get("success"):
                validation_result["issues"].append("场景执行失败")
                validation_result["is_valid"] = False
                return validation_result
            
            response = result.get("response", {})
            
            # 验证必需字段
            required_fields = self.validation_rules["response_structure"]["required_fields"]
            for field in required_fields:
                if field not in response:
                    validation_result["issues"].append(f"缺少必需字段: {field}")
                    validation_result["is_valid"] = False
            
            # 验证置信度
            confidence = response.get("confidence", 0)
            expected = self.expected_responses.get(analysis_type, {})
            min_confidence = expected.get("min_confidence", 0.5)
            
            if confidence < min_confidence:
                validation_result["issues"].append(f"置信度过低: {confidence} < {min_confidence}")
                validation_result["score"] -= 0.2
            
            # 验证执行时间
            execution_time = result.get("execution_time", 0)
            max_time = expected.get("max_execution_time", 300)
            
            if execution_time > max_time:
                validation_result["issues"].append(f"执行时间过长: {execution_time}s > {max_time}s")
                validation_result["score"] -= 0.1
            
            # 验证内容质量
            content = response.get("content", "")
            content_rules = self.validation_rules["content_quality"]
            
            if len(content) < content_rules["min_length"]:
                validation_result["issues"].append(f"响应内容过短: {len(content)} < {content_rules['min_length']}")
                validation_result["score"] -= 0.1
            
            # 验证关键词存在
            expected_keywords = expected.get("expected_keywords", [])
            content_lower = content.lower()
            missing_keywords = [kw for kw in expected_keywords if kw not in content_lower]
            
            if missing_keywords:
                validation_result["issues"].append(f"缺少预期关键词: {', '.join(missing_keywords)}")
                validation_result["score"] -= 0.1
            
            # 计算总分
            base_score = 1.0
            validation_result["score"] = max(base_score + validation_result["score"], 0.0)
            
            # 生成建议
            if validation_result["score"] < 0.7:
                validation_result["recommendations"].append("考虑优化Agent响应质量")
            
            if execution_time > max_time * 0.8:
                validation_result["recommendations"].append("考虑优化执行性能")
            
            return validation_result
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"验证过程异常: {str(e)}")
            return validation_result
    
    def validate_all_results(self, demo_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """验证所有演示结果."""
        overall_validation = {
            "total_scenarios": len(demo_results),
            "valid_scenarios": 0,
            "invalid_scenarios": 0,
            "average_score": 0.0,
            "success_rate": 0.0,
            "detailed_results": [],
            "summary": {
                "issues": [],
                "recommendations": []
            }
        }
        
        try:
            total_score = 0.0
            successful_count = 0
            
            for result in demo_results:
                validation = self.validate_demo_result(result)
                overall_validation["detailed_results"].append({
                    "scenario_name": result.get("scenario", {}).get("name", "Unknown"),
                    "validation": validation
                })
                
                if validation["is_valid"]:
                    overall_validation["valid_scenarios"] += 1
                    total_score += validation["score"]
                else:
                    overall_validation["invalid_scenarios"] += 1
                
                if result.get("success"):
                    successful_count += 1
            
            # 计算平均分和成功率
            if overall_validation["valid_scenarios"] > 0:
                overall_validation["average_score"] = total_score / overall_validation["valid_scenarios"]
            
            overall_validation["success_rate"] = successful_count / len(demo_results) if demo_results else 0.0
            
            # 生成总体建议
            if overall_validation["success_rate"] < 0.8:
                overall_validation["summary"]["issues"].append("整体成功率偏低")
                overall_validation["summary"]["recommendations"].append("检查系统配置和Agent健康状态")
            
            if overall_validation["average_score"] < 0.7:
                overall_validation["summary"]["issues"].append("整体质量分数偏低")
                overall_validation["summary"]["recommendations"].append("优化Agent响应质量和内容生成")
            
            return overall_validation
            
        except Exception as e:
            overall_validation["summary"]["issues"].append(f"整体验证异常: {str(e)}")
            return overall_validation
    
    def generate_test_report(self, demo_results: List[Dict[str, Any]]) -> str:
        """生成测试报告."""
        try:
            validation = self.validate_all_results(demo_results)
            
            report = f"""
# 专利分析系统演示测试报告

## 测试概览
- **测试时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
- **总场景数**: {validation['total_scenarios']}
- **成功场景**: {validation['valid_scenarios']}
- **失败场景**: {validation['invalid_scenarios']}
- **成功率**: {validation['success_rate']:.1%}
- **平均质量分**: {validation['average_score']:.2f}/1.00

## 详细结果

"""
            
            for detail in validation["detailed_results"]:
                scenario_name = detail["scenario_name"]
                val = detail["validation"]
                
                report += f"### {scenario_name}\n"
                report += f"- **验证状态**: {'✅ 通过' if val['is_valid'] else '❌ 失败'}\n"
                report += f"- **质量分数**: {val['score']:.2f}/1.00\n"
                
                if val["issues"]:
                    report += f"- **问题**: {', '.join(val['issues'])}\n"
                
                if val["recommendations"]:
                    report += f"- **建议**: {', '.join(val['recommendations'])}\n"
                
                report += "\n"
            
            # 总体建议
            if validation["summary"]["issues"] or validation["summary"]["recommendations"]:
                report += "## 总体建议\n\n"
                
                if validation["summary"]["issues"]:
                    report += "### 发现的问题\n"
                    for issue in validation["summary"]["issues"]:
                        report += f"- {issue}\n"
                    report += "\n"
                
                if validation["summary"]["recommendations"]:
                    report += "### 改进建议\n"
                    for rec in validation["summary"]["recommendations"]:
                        report += f"- {rec}\n"
                    report += "\n"
            
            return report
            
        except Exception as e:
            return f"生成测试报告失败: {str(e)}"


def save_test_data():
    """保存测试数据到文件."""
    try:
        test_data = PatentDemoTestData()
        
        data = {
            "sample_patents": test_data.sample_patents,
            "expected_responses": test_data.expected_responses,
            "validation_rules": test_data.validation_rules,
            "generated_at": datetime.now().isoformat()
        }
        
        with open("patent_demo_test_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print("✅ 测试数据已保存到 patent_demo_test_data.json")
        
    except Exception as e:
        print(f"❌ 保存测试数据失败: {str(e)}")


if __name__ == "__main__":
    save_test_data()