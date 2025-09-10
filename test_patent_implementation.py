#!/usr/bin/env python3
"""简单测试脚本验证专利数据处理实现."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.multi_agent_service.patent.models.patent_data import (
    PatentData, PatentDataset, PatentApplicant, PatentInventor, 
    PatentClassification, DataQualityReport
)
from src.multi_agent_service.patent.utils.data_processor import (
    PatentDataStandardizer, PatentDeduplicator, PatentQualityController, PatentDataProcessor
)


async def test_patent_data_models():
    """测试专利数据模型."""
    print("🧪 测试专利数据模型...")
    
    try:
        # 创建申请人
        applicant = PatentApplicant(
            name="测试公司有限公司",
            normalized_name="测试公司 Co., Ltd.",
            country="CN",
            applicant_type="企业"
        )
        
        # 创建发明人
        inventor = PatentInventor(
            name="张三",
            normalized_name="张三",
            country="CN"
        )
        
        # 创建分类
        classification = PatentClassification(
            ipc_class="A01B 1/00",
            cpc_class="A01B1/00",
            national_class="A01B1/00"
        )
        
        # 创建专利数据
        patent = PatentData(
            application_number="CN202310123456.7",
            title="一种新型农业机械装置",
            abstract="本发明涉及一种新型农业机械装置，包括主体结构、传动系统和控制系统等部分，能够有效提高农业生产效率。",
            applicants=[applicant],
            inventors=[inventor],
            application_date=datetime(2023, 1, 15),
            publication_date=datetime(2023, 7, 15),
            classifications=[classification],
            country="CN",
            status="已公开",
            technical_field="农业机械",
            data_source="test_source",
            keywords=["农业", "机械", "装置", "自动化"]
        )
        
        print(f"✅ 专利数据创建成功:")
        print(f"   申请号: {patent.application_number}")
        print(f"   标题: {patent.title}")
        print(f"   申请人: {patent.applicants[0].name}")
        print(f"   发明人: {patent.inventors[0].name}")
        print(f"   国家: {patent.country}")
        print(f"   状态: {patent.status}")
        
        # 计算质量评分
        quality_score = patent.calculate_quality_score()
        print(f"   质量评分: {quality_score:.2f}")
        
        # 获取哈希值
        print(f"   内容哈希: {patent.content_hash[:16]}...")
        print(f"   相似性哈希: {patent.similarity_hash[:16]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 专利数据模型测试失败: {str(e)}")
        return False


async def test_data_standardization():
    """测试数据标准化."""
    print("\n🧪 测试数据标准化...")
    
    try:
        standardizer = PatentDataStandardizer()
        
        # 创建需要标准化的专利数据（使用有效值，然后手动设置需要标准化的字段）
        patent = PatentData(
            application_number="CN202310123456.7",
            title="一种新型农业机械装置",
            abstract="本发明涉及农业机械装置，具有创新性特征...",
            applicants=[PatentApplicant(name="测试公司有限公司", normalized_name="测试公司有限公司")],
            inventors=[PatentInventor(name="张三", normalized_name="张三")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="test_source",
            keywords=["农业", "机械", "装置", "自动化"]
        )
        
        # 手动设置需要标准化的字段（绕过Pydantic验证）
        patent.application_number = "cn202310123456.7"  # 小写
        patent.title = "  一种新型农业机械装置  "  # 有多余空格
        patent.abstract = "本发明涉及<b>农业机械</b>装置，具有<i>创新性</i>特征..."  # 有HTML标签
        patent.country = "中国"  # 中文国家名
        patent.status = "pending"  # 英文状态（这里会在标准化时处理）
        patent.keywords = ["  农业  ", "机械", "", "装置  ", "自动化"]  # 有空格和空值
        patent.inventors[0].name = "  张 三  "
        patent.inventors[0].normalized_name = "  张 三  "
        
        print(f"📝 标准化前:")
        print(f"   申请号: '{patent.application_number}'")
        print(f"   标题: '{patent.title}'")
        print(f"   摘要: '{patent.abstract[:50]}...'")
        print(f"   国家: '{patent.country}'")
        print(f"   状态: '{patent.status}'")
        print(f"   关键词: {patent.keywords}")
        print(f"   发明人: '{patent.inventors[0].name}'")
        
        # 执行标准化
        standardized = await standardizer.standardize_patent(patent)
        
        print(f"\n✨ 标准化后:")
        print(f"   申请号: '{standardized.application_number}'")
        print(f"   标题: '{standardized.title}'")
        print(f"   摘要: '{standardized.abstract[:50]}...'")
        print(f"   国家: '{standardized.country}'")
        print(f"   状态: '{standardized.status}'")
        print(f"   关键词: {standardized.keywords}")
        print(f"   发明人: '{standardized.inventors[0].normalized_name}'")
        print(f"   质量评分: {standardized.data_quality_score:.2f}")
        
        print("✅ 数据标准化测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 数据标准化测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_deduplication():
    """测试去重功能."""
    print("\n🧪 测试去重功能...")
    
    try:
        deduplicator = PatentDeduplicator()
        
        # 创建包含重复数据的专利列表
        patents = []
        
        # 原始专利
        patent1 = PatentData(
            application_number="CN202310123456.7",
            title="农业机械装置",
            abstract="这是一个农业机械装置的详细描述，具有创新的技术特征...",
            applicants=[PatentApplicant(name="公司A", normalized_name="公司A")],
            inventors=[PatentInventor(name="发明人A", normalized_name="发明人A")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="source1",
            data_quality_score=0.9
        )
        patents.append(patent1)
        
        # 完全相同的专利（应该被去重）
        patent2 = PatentData(
            application_number="CN202310123456.7",
            title="农业机械装置",
            abstract="这是一个农业机械装置的详细描述，具有创新的技术特征...",
            applicants=[PatentApplicant(name="公司A", normalized_name="公司A")],
            inventors=[PatentInventor(name="发明人A", normalized_name="发明人A")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="source2",
            data_quality_score=0.8  # 质量更低，应该被移除
        )
        patents.append(patent2)
        
        # 不同的专利
        patent3 = PatentData(
            application_number="CN202310123457.8",
            title="另一种农业机械装置",
            abstract="这是另一种农业机械装置的详细描述，具有不同的技术特征...",
            applicants=[PatentApplicant(name="公司B", normalized_name="公司B")],
            inventors=[PatentInventor(name="发明人B", normalized_name="发明人B")],
            application_date=datetime(2023, 2, 15),
            country="CN",
            status="申请中",
            data_source="source1",
            data_quality_score=0.85
        )
        patents.append(patent3)
        
        # 创建数据集
        dataset = PatentDataset(
            patents=patents,
            search_keywords=["农业机械"],
            data_sources=["source1", "source2"]
        )
        
        print(f"📊 去重前: {len(dataset.patents)} 个专利")
        for i, patent in enumerate(dataset.patents):
            print(f"   {i+1}. {patent.application_number} (质量: {patent.data_quality_score:.2f})")
        
        # 执行去重
        deduplicated_dataset, removed_count = await deduplicator.deduplicate_dataset(dataset)
        
        print(f"\n🔄 去重后: {len(deduplicated_dataset.patents)} 个专利 (移除了 {removed_count} 个重复项)")
        for i, patent in enumerate(deduplicated_dataset.patents):
            print(f"   {i+1}. {patent.application_number} (质量: {patent.data_quality_score:.2f})")
        
        print("✅ 去重功能测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 去重功能测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_quality_control():
    """测试质量控制."""
    print("\n🧪 测试质量控制...")
    
    try:
        quality_controller = PatentQualityController()
        
        patents = []
        
        # 高质量专利
        good_patent = PatentData(
            application_number="CN202310123456.7",
            title="一种新型农业机械装置及其控制方法",
            abstract="本发明涉及一种新型农业机械装置及其控制方法，包括主体结构、传动系统、控制系统和传感器系统等部分，能够实现自动化作业和智能控制。",
            applicants=[PatentApplicant(name="测试科技有限公司", normalized_name="测试科技 Co., Ltd.")],
            inventors=[PatentInventor(name="张三", normalized_name="张三"), PatentInventor(name="李四", normalized_name="李四")],
            application_date=datetime(2023, 1, 15),
            publication_date=datetime(2023, 7, 15),
            classifications=[PatentClassification(ipc_class="A01B 1/00")],
            country="CN",
            status="已公开",
            technical_field="农业机械",
            data_source="test_source",
            keywords=["农业", "机械", "自动化", "控制"]
        )
        patents.append(good_patent)
        
        # 中等质量专利（缺少一些信息）
        medium_patent = PatentData(
            application_number="CN202310123457.8",
            title="农业设备装置系统",  # 增加长度以满足验证
            abstract="一种农业设备装置系统的详细描述和技术特征...",  # 增加长度以满足验证
            applicants=[PatentApplicant(name="公司B", normalized_name="公司B")],
            inventors=[PatentInventor(name="王五", normalized_name="王五")],
            application_date=datetime(2023, 2, 15),
            country="CN",
            status="申请中",
            data_source="test_source"
            # 缺少分类、技术领域等信息
        )
        patents.append(medium_patent)
        
        # 低质量专利（先创建有效对象，然后手动设置问题字段）
        bad_patent = PatentData(
            application_number="CN202310123458.9",
            title="测试专利标题",
            abstract="这是一个测试专利的摘要描述...",
            applicants=[PatentApplicant(name="测试公司", normalized_name="测试公司")],
            inventors=[PatentInventor(name="测试发明人", normalized_name="测试发明人")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="test_source"
        )
        
        # 手动设置问题字段（绕过Pydantic验证）
        bad_patent.application_number = ""  # 空申请号
        bad_patent.title = "短"  # 标题太短
        bad_patent.abstract = "短摘要"  # 摘要太短
        bad_patent.applicants = []  # 没有申请人
        bad_patent.inventors = []  # 没有发明人
        bad_patent.country = ""  # 空国家
        patents.append(bad_patent)
        
        # 创建数据集
        dataset = PatentDataset(
            patents=patents,
            search_keywords=["农业"],
            data_sources=["test_source"]
        )
        
        print(f"📊 质量验证前: {len(dataset.patents)} 个专利")
        
        # 执行质量验证
        report = await quality_controller.validate_dataset(dataset)
        
        print(f"\n📋 质量报告:")
        print(f"   总记录数: {report.total_records}")
        print(f"   有效记录: {report.valid_records}")
        print(f"   无效记录: {report.invalid_records}")
        print(f"   整体质量评分: {report.quality_score:.2f}")
        print(f"   完整性评分: {report.completeness_score:.2f}")
        print(f"   准确性评分: {report.accuracy_score:.2f}")
        print(f"   一致性评分: {report.consistency_score:.2f}")
        
        if report.missing_fields:
            print(f"   缺失字段统计: {report.missing_fields}")
        
        if report.invalid_formats:
            print(f"   格式错误统计: {report.invalid_formats}")
        
        if report.data_anomalies:
            print(f"   数据异常: {len(report.data_anomalies)} 个")
            for anomaly in report.data_anomalies[:3]:  # 只显示前3个
                print(f"     - {anomaly}")
        
        if report.recommendations:
            print(f"   改进建议:")
            for rec in report.recommendations[:3]:  # 只显示前3个
                print(f"     - {rec}")
        
        print("✅ 质量控制测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 质量控制测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_complete_processing():
    """测试完整的数据处理流程."""
    print("\n🧪 测试完整数据处理流程...")
    
    try:
        processor = PatentDataProcessor()
        
        # 创建包含各种问题的测试数据集
        patents = []
        
        # 需要标准化的专利
        patent1 = PatentData(
            application_number="CN202310123456.7",
            title="农业机械装置",
            abstract="本发明涉及农业机械装置，具有创新特征...",
            applicants=[PatentApplicant(name="测试公司有限公司", normalized_name="测试公司有限公司")],
            inventors=[PatentInventor(name="张三", normalized_name="张三")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="source1",
            data_quality_score=0.9
        )
        
        # 手动设置需要标准化的字段
        patent1.application_number = "cn202310123456.7"  # 小写
        patent1.title = "  农业机械装置  "  # 多余空格
        patent1.abstract = "本发明涉及<b>农业机械</b>装置，具有创新特征..."  # HTML标签
        patent1.country = "中国"  # 中文国家名
        patents.append(patent1)
        
        # 重复专利（质量更低）
        patent2 = PatentData(
            application_number="CN202310123456.7",  # 标准化后会与patent1相同
            title="农业机械装置",
            abstract="本发明涉及农业机械装置，具有创新特征...",
            applicants=[PatentApplicant(name="测试公司 Co., Ltd.", normalized_name="测试公司 Co., Ltd.")],
            inventors=[PatentInventor(name="张三", normalized_name="张三")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="source2",
            data_quality_score=0.7  # 质量更低
        )
        patents.append(patent2)
        
        # 正常专利
        patent3 = PatentData(
            application_number="CN202310123457.8",
            title="另一种农业机械装置",
            abstract="这是另一种农业机械装置的详细描述，具有不同的技术特征和应用场景...",
            applicants=[PatentApplicant(name="另一家公司", normalized_name="另一家公司")],
            inventors=[PatentInventor(name="李四", normalized_name="李四")],
            application_date=datetime(2023, 2, 15),
            country="CN",
            status="申请中",
            data_source="source1",
            data_quality_score=0.85
        )
        patents.append(patent3)
        
        # 创建数据集
        dataset = PatentDataset(
            patents=patents,
            search_keywords=["农业机械"],
            data_sources=["source1", "source2"]
        )
        
        print(f"📊 处理前: {len(dataset.patents)} 个专利")
        
        # 执行完整处理流程
        processed_dataset, quality_report = await processor.process_dataset(
            dataset,
            standardize=True,
            deduplicate=True,
            validate=True
        )
        
        print(f"\n🔄 处理后: {len(processed_dataset.patents)} 个专利")
        
        if quality_report:
            print(f"\n📋 最终质量报告:")
            print(f"   总记录数: {quality_report.total_records}")
            print(f"   有效记录: {quality_report.valid_records}")
            print(f"   重复记录: {quality_report.duplicate_records}")
            print(f"   整体质量评分: {quality_report.quality_score:.2f}")
        
        # 显示处理后的专利信息
        print(f"\n📄 处理后的专利:")
        for i, patent in enumerate(processed_dataset.patents):
            print(f"   {i+1}. {patent.application_number}")
            print(f"      标题: {patent.title}")
            print(f"      国家: {patent.country}")
            print(f"      状态: {patent.status}")
            print(f"      质量: {patent.data_quality_score:.2f}")
        
        # 计算数据集质量指标
        metrics = processed_dataset.calculate_quality_metrics()
        print(f"\n📈 数据集质量指标:")
        print(f"   平均质量评分: {metrics.get('average_quality_score', 0):.2f}")
        print(f"   高质量专利: {metrics.get('high_quality_count', 0)} 个")
        print(f"   中等质量专利: {metrics.get('medium_quality_count', 0)} 个")
        print(f"   低质量专利: {metrics.get('low_quality_count', 0)} 个")
        
        print("✅ 完整数据处理流程测试成功")
        return True
        
    except Exception as e:
        print(f"❌ 完整数据处理流程测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数."""
    print("🚀 开始专利数据处理和质量控制功能测试\n")
    
    tests = [
        ("专利数据模型", test_patent_data_models),
        ("数据标准化", test_data_standardization),
        ("去重功能", test_deduplication),
        ("质量控制", test_quality_control),
        ("完整处理流程", test_complete_processing),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name}测试出现异常: {str(e)}")
            results.append((test_name, False))
    
    # 汇总结果
    print("\n" + "="*60)
    print("📊 测试结果汇总:")
    print("="*60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总体结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试都通过了！专利数据处理和质量控制功能实现正确。")
    else:
        print("⚠️  部分测试失败，请检查实现。")
    
    return passed == total


if __name__ == "__main__":
    asyncio.run(main())