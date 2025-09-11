#!/usr/bin/env python3
"""
测试数据生成器

为真实环境测试生成各种测试数据，包括专利数据、查询数据等。
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
from pathlib import Path


class TestDataGenerator:
    """测试数据生成器."""
    
    def __init__(self):
        """初始化生成器."""
        self.companies = [
            "华为技术有限公司", "腾讯科技", "阿里巴巴", "百度", "字节跳动",
            "Apple Inc.", "Google LLC", "Microsoft Corporation", "IBM Corporation",
            "Samsung Electronics", "Sony Corporation", "Intel Corporation"
        ]
        
        self.inventors = [
            "张伟", "李明", "王华", "刘强", "陈静",
            "John Smith", "Jane Doe", "Michael Johnson", "Sarah Wilson",
            "田中太郎", "佐藤花子", "山田一郎", "鈴木美咲"
        ]
        
        self.tech_keywords = [
            "人工智能", "机器学习", "深度学习", "神经网络", "计算机视觉",
            "自然语言处理", "区块链", "智能合约", "5G通信", "物联网",
            "量子计算", "边缘计算", "云计算", "大数据", "数据挖掘"
        ]
        
        self.ipc_classes = [
            "G06N3/08", "G06N3/04", "G06F18/24", "G06T7/70", "G06F40/30",
            "H04L9/32", "G06Q20/38", "H04W72/04", "H04L27/26", "G06F21/60"
        ]
        
        self.countries = ["US", "CN", "EP", "JP", "KR", "DE", "GB", "FR"]
        self.statuses = ["published", "granted", "pending", "withdrawn"]
    
    def generate_patent_data(self, count: int = 100) -> List[Dict[str, Any]]:
        """生成专利数据."""
        patents = []
        
        for i in range(count):
            # 随机选择国家
            country = random.choice(self.countries)
            
            # 生成申请号
            if country == "US":
                app_number = f"US{random.randint(10000000, 99999999)}"
            elif country == "CN":
                app_number = f"CN{random.randint(202000000000, 202399999999)}"
            elif country == "EP":
                app_number = f"EP{random.randint(20000000, 23999999)}"
            else:
                app_number = f"{country}{random.randint(1000000, 9999999)}"
            
            # 随机日期
            start_date = datetime(2018, 1, 1)
            end_date = datetime(2023, 12, 31)
            app_date = start_date + timedelta(
                days=random.randint(0, (end_date - start_date).days)
            )
            pub_date = app_date + timedelta(days=random.randint(180, 540))
            
            # 生成专利
            patent = {
                "application_number": app_number,
                "title": self._generate_patent_title(),
                "abstract": self._generate_patent_abstract(),
                "applicants": [
                    {
                        "name": random.choice(self.companies),
                        "country": country,
                        "applicant_type": "company"
                    }
                ],
                "inventors": [
                    {
                        "name": random.choice(self.inventors),
                        "country": country
                    }
                ],
                "application_date": app_date.isoformat(),
                "publication_date": pub_date.isoformat(),
                "classifications": [
                    {"ipc_class": random.choice(self.ipc_classes)}
                ],
                "country": country,
                "status": random.choice(self.statuses),
                "keywords": random.sample(self.tech_keywords, k=random.randint(2, 5))
            }
            
            patents.append(patent)
        
        return patents
    
    def _generate_patent_title(self) -> str:
        """生成专利标题."""
        templates = [
            "基于{tech1}的{tech2}方法及系统",
            "{tech1}在{tech2}中的应用",
            "一种{tech1}{tech2}装置",
            "{tech1} System for {tech2}",
            "Method and Apparatus for {tech1} {tech2}",
            "{tech1}-based {tech2} Technology"
        ]
        
        template = random.choice(templates)
        tech1 = random.choice(self.tech_keywords)
        tech2 = random.choice(self.tech_keywords)
        
        return template.format(tech1=tech1, tech2=tech2)
    
    def _generate_patent_abstract(self) -> str:
        """生成专利摘要."""
        templates = [
            "本发明公开了一种{tech}技术，通过{method}实现{goal}。该技术具有{advantage}的优点，能够有效解决现有技术中的{problem}问题。",
            "The present invention relates to {tech} technology that provides {goal} through {method}. This approach offers {advantage} and effectively addresses {problem} in existing systems.",
            "本技术提供了一种新的{tech}解决方案，采用{method}来实现{goal}，相比传统方法具有{advantage}的特点。"
        ]
        
        template = random.choice(templates)
        
        return template.format(
            tech=random.choice(self.tech_keywords),
            method=random.choice(["机器学习算法", "深度神经网络", "优化算法", "分布式计算"]),
            goal=random.choice(["高效处理", "智能识别", "自动分析", "实时预测"]),
            advantage=random.choice(["高精度", "低延迟", "高效率", "强鲁棒性"]),
            problem=random.choice(["计算复杂度高", "准确率低", "处理速度慢", "资源消耗大"])
        )
    
    def generate_query_scenarios(self) -> List[Dict[str, Any]]:
        """生成查询场景."""
        scenarios = []
        
        # 简单查询场景
        for keywords in [
            ["人工智能"],
            ["机器学习", "深度学习"],
            ["计算机视觉", "图像识别"],
            ["自然语言处理"],
            ["区块链", "智能合约"]
        ]:
            scenarios.append({
                "type": "simple_query",
                "keywords": keywords,
                "expected_results": random.randint(10, 100),
                "complexity": "low"
            })
        
        # 复杂分析场景
        for analysis_type in ["trend", "competition", "technology", "geographic"]:
            scenarios.append({
                "type": "complex_analysis",
                "analysis_type": analysis_type,
                "keywords": random.sample(self.tech_keywords, k=3),
                "date_range": {
                    "start_date": "2020-01-01",
                    "end_date": "2023-12-31"
                },
                "countries": random.sample(self.countries, k=3),
                "expected_duration": random.randint(60, 180),
                "complexity": "high"
            })
        
        return scenarios
    
    def generate_performance_test_data(self) -> Dict[str, Any]:
        """生成性能测试数据."""
        return {
            "concurrent_scenarios": [
                {
                    "concurrent_users": users,
                    "request_rate": rate,
                    "duration_seconds": duration,
                    "expected_success_rate": 0.95 - (users * 0.01)  # 随用户数降低
                }
                for users, rate, duration in [
                    (1, 1, 30), (3, 2, 60), (5, 3, 90), (10, 5, 120)
                ]
            ],
            "load_scenarios": [
                {
                    "data_size": size,
                    "processing_mode": mode,
                    "expected_throughput": throughput,
                    "memory_limit_mb": memory
                }
                for size, mode, throughput, memory in [
                    (100, "batch", 50, 256),
                    (500, "batch", 100, 512),
                    (1000, "stream", 150, 1024),
                    (5000, "distributed", 200, 2048)
                ]
            ]
        }
    
    def save_all_test_data(self, output_dir: str = "test_data"):
        """保存所有测试数据."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        # 生成并保存专利数据
        patent_data = {
            "patents": self.generate_patent_data(1000),
            "metadata": {
                "total_count": 1000,
                "generated_at": datetime.now().isoformat(),
                "data_type": "synthetic_patent_data"
            }
        }
        
        with open(output_path / "patent_test_data.json", "w", encoding="utf-8") as f:
            json.dump(patent_data, f, ensure_ascii=False, indent=2)
        
        # 生成并保存查询场景
        query_scenarios = {
            "scenarios": self.generate_query_scenarios(),
            "metadata": {
                "total_scenarios": len(self.generate_query_scenarios()),
                "generated_at": datetime.now().isoformat()
            }
        }
        
        with open(output_path / "query_scenarios.json", "w", encoding="utf-8") as f:
            json.dump(query_scenarios, f, ensure_ascii=False, indent=2)
        
        # 生成并保存性能测试数据
        performance_data = self.generate_performance_test_data()
        performance_data["metadata"] = {
            "generated_at": datetime.now().isoformat(),
            "data_type": "performance_test_scenarios"
        }
        
        with open(output_path / "performance_test_data.json", "w", encoding="utf-8") as f:
            json.dump(performance_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 测试数据已生成并保存到 {output_path} 目录")
        print(f"   - 专利数据: {len(patent_data['patents'])} 条")
        print(f"   - 查询场景: {len(query_scenarios['scenarios'])} 个")
        print(f"   - 性能场景: {len(performance_data['concurrent_scenarios']) + len(performance_data['load_scenarios'])} 个")


def main():
    """主函数."""
    print("🔧 生成真实环境测试数据...")
    
    generator = TestDataGenerator()
    generator.save_all_test_data()
    
    print("✅ 测试数据生成完成！")


if __name__ == "__main__":
    main()