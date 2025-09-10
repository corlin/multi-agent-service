"""测试专利数据处理和质量控制功能."""

import asyncio
import pytest
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import os

from src.multi_agent_service.patent.models.patent_data import (
    PatentData, PatentDataset, PatentApplicant, PatentInventor, 
    PatentClassification, DataQualityReport
)
from src.multi_agent_service.patent.utils.data_processor import (
    PatentDataStandardizer, PatentDeduplicator, PatentQualityController, PatentDataProcessor
)
from src.multi_agent_service.patent.storage.database import PatentDatabaseManager
from src.multi_agent_service.patent.monitoring.patent_monitor import PatentMonitoringSystem
from src.multi_agent_service.utils.monitoring import MonitoringSystem


class TestPatentDataModels:
    """测试专利数据模型."""
    
    def test_patent_data_creation(self):
        """测试专利数据创建."""
        applicant = PatentApplicant(
            name="测试公司有限公司",
            normalized_name="测试公司 Co., Ltd.",
            country="CN",
            applicant_type="企业"
        )
        
        inventor = PatentInventor(
            name="张三",
            normalized_name="张三",
            country="CN"
        )
        
        classification = PatentClassification(
            ipc_class="A01B 1/00",
            cpc_class="A01B1/00",
            national_class="A01B1/00"
        )
        
        patent = PatentData(
            application_number="CN202310123456.7",
            title="一种新型农业机械装置",
            abstract="本发明涉及一种新型农业机械装置，包括...",
            applicants=[applicant],
            inventors=[inventor],
            application_date=datetime(2023, 1, 15),
            classifications=[classification],
            country="CN",
            status="申请中",
            data_source="test_source",
            keywords=["农业", "机械", "装置"]
        )
        
        assert patent.application_number == "CN202310123456.7"
        assert patent.title == "一种新型农业机械装置"
        assert len(patent.applicants) == 1
        assert len(patent.inventors) == 1
        assert patent.country == "CN"
        assert patent.content_hash is not None
        assert patent.similarity_hash is not None
    
    def test_patent_quality_score_calculation(self):
        """测试专利质量评分计算."""
        patent = PatentData(
            application_number="CN202310123456.7",
            title="一种新型农业机械装置",
            abstract="本发明涉及一种新型农业机械装置，包括主体结构、传动系统和控制系统等部分。",
            applicants=[PatentApplicant(name="测试公司", normalized_name="测试公司")],
            inventors=[PatentInventor(name="张三", normalized_name="张三")],
            application_date=datetime(2023, 1, 15),
            publication_date=datetime(2023, 7, 15),
            classifications=[PatentClassification(ipc_class="A01B 1/00")],
            country="CN",
            status="已公开",
            technical_field="农业机械",
            keywords=["农业", "机械"],
            data_source="test_source"
        )
        
        quality_score = patent.calculate_quality_score()
        assert 0.0 <= quality_score <= 1.0
        assert quality_score > 0.8  # 应该是高质量数据
    
    def test_patent_dataset_operations(self):
        """测试专利数据集操作."""
        dataset = PatentDataset(
            search_keywords=["农业机械"],
            data_sources=["test_source"]
        )
        
        # 创建测试专利
        patent1 = PatentData(
            application_number="CN202310123456.7",
            title="农业机械装置A",
            abstract="这是一个农业机械装置的描述...",
            applicants=[PatentApplicant(name="公司A", normalized_name="公司A")],
            inventors=[PatentInventor(name="发明人A", normalized_name="发明人A")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="test_source"
        )
        
        patent2 = PatentData(
            application_number="CN202310123457.8",
            title="农业机械装置B",
            abstract="这是另一个农业机械装置的描述...",
            applicants=[PatentApplicant(name="公司B", normalized_name="公司B")],
            inventors=[PatentInventor(name="发明人B", normalized_name="发明人B")],
            application_date=datetime(2023, 2, 15),
            country="CN",
            status="申请中",
            data_source="test_source"
        )
        
        # 添加专利
        assert dataset.add_patent(patent1) == True
        assert dataset.add_patent(patent2) == True
        assert dataset.total_count == 2
        
        # 尝试添加重复专利
        duplicate_patent = PatentData(
            application_number="CN202310123456.7",  # 相同申请号
            title="农业机械装置A",
            abstract="这是一个农业机械装置的描述...",
            applicants=[PatentApplicant(name="公司A", normalized_name="公司A")],
            inventors=[PatentInventor(name="发明人A", normalized_name="发明人A")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="test_source"
        )
        
        assert dataset.add_patent(duplicate_patent) == False  # 应该被拒绝
        assert dataset.total_count == 2  # 数量不变
        
        # 计算质量指标
        metrics = dataset.calculate_quality_metrics()
        assert 'total_patents' in metrics
        assert metrics['total_patents'] == 2


class TestPatentDataStandardizer:
    """测试专利数据标准化器."""
    
    @pytest.fixture
    def standardizer(self):
        return PatentDataStandardizer()
    
    @pytest.mark.asyncio
    async def test_standardize_patent(self, standardizer):
        """测试专利标准化."""
        patent = PatentData(
            application_number="cn202310123456.7",  # 小写
            title="  一种新型农业机械装置  ",  # 有多余空格
            abstract="本发明涉及<b>农业机械</b>...",  # 有HTML标签
            applicants=[PatentApplicant(name="测试公司有限公司", normalized_name="测试公司有限公司")],
            inventors=[PatentInventor(name="  张 三  ", normalized_name="  张 三  ")],
            application_date=datetime(2023, 1, 15),
            country="中国",  # 中文国家名
            status="pending",  # 英文状态
            data_source="test_source",
            keywords=["  农业  ", "机械", "", "装置  "]  # 有空格和空值
        )
        
        standardized = await standardizer.standardize_patent(patent)
        
        assert standardized.title == "一种新型农业机械装置"  # 去除空格
        assert standardized.abstract == "本发明涉及农业机械..."  # 去除HTML标签
        assert standardized.country == "CN"  # 标准化国家代码
        assert standardized.status == "申请中"  # 标准化状态
        assert "农业" in standardized.keywords
        assert "机械" in standardized.keywords
        assert "装置" in standardized.keywords
        assert "" not in standardized.keywords  # 空值被移除
    
    @pytest.mark.asyncio
    async def test_standardize_dataset(self, standardizer):
        """测试数据集标准化."""
        patents = []
        for i in range(3):
            patent = PatentData(
                application_number=f"CN20231012345{i}.{i}",
                title=f"  专利标题{i}  ",
                abstract=f"专利摘要{i}的详细描述...",
                applicants=[PatentApplicant(name=f"公司{i}有限公司", normalized_name=f"公司{i}有限公司")],
                inventors=[PatentInventor(name=f"发明人{i}", normalized_name=f"发明人{i}")],
                application_date=datetime(2023, 1, 15 + i),
                country="中国",
                status="pending",
                data_source="test_source"
            )
            patents.append(patent)
        
        dataset = PatentDataset(patents=patents)
        
        standardized_dataset = await standardizer.standardize_dataset(dataset)
        
        assert len(standardized_dataset.patents) == 3
        for patent in standardized_dataset.patents:
            assert patent.country == "CN"
            assert patent.status == "申请中"
            assert not patent.title.startswith(" ")
            assert not patent.title.endswith(" ")


class TestPatentDeduplicator:
    """测试专利去重器."""
    
    @pytest.fixture
    def deduplicator(self):
        return PatentDeduplicator()
    
    @pytest.mark.asyncio
    async def test_deduplicate_dataset(self, deduplicator):
        """测试数据集去重."""
        # 创建包含重复数据的数据集
        patents = []
        
        # 原始专利
        patent1 = PatentData(
            application_number="CN202310123456.7",
            title="农业机械装置",
            abstract="这是一个农业机械装置的详细描述...",
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
            abstract="这是一个农业机械装置的详细描述...",
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
            abstract="这是另一种农业机械装置的详细描述...",
            applicants=[PatentApplicant(name="公司B", normalized_name="公司B")],
            inventors=[PatentInventor(name="发明人B", normalized_name="发明人B")],
            application_date=datetime(2023, 2, 15),
            country="CN",
            status="申请中",
            data_source="source1",
            data_quality_score=0.85
        )
        patents.append(patent3)
        
        dataset = PatentDataset(patents=patents)
        
        deduplicated_dataset, removed_count = await deduplicator.deduplicate_dataset(dataset)
        
        assert removed_count == 1  # 应该移除1个重复项
        assert len(deduplicated_dataset.patents) == 2  # 剩余2个唯一专利
        
        # 验证保留的是质量更高的专利
        remaining_patent_1 = next(p for p in deduplicated_dataset.patents if p.application_number == "CN202310123456.7")
        assert remaining_patent_1.data_quality_score == 0.9  # 保留质量更高的


class TestPatentQualityController:
    """测试专利质量控制器."""
    
    @pytest.fixture
    def quality_controller(self):
        return PatentQualityController()
    
    @pytest.mark.asyncio
    async def test_validate_dataset(self, quality_controller):
        """测试数据集质量验证."""
        patents = []
        
        # 高质量专利
        good_patent = PatentData(
            application_number="CN202310123456.7",
            title="一种新型农业机械装置",
            abstract="本发明涉及一种新型农业机械装置，包括主体结构、传动系统和控制系统等部分。",
            applicants=[PatentApplicant(name="测试公司", normalized_name="测试公司")],
            inventors=[PatentInventor(name="张三", normalized_name="张三")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="test_source"
        )
        patents.append(good_patent)
        
        # 低质量专利（缺少必需字段）
        bad_patent = PatentData(
            application_number="",  # 空申请号
            title="短标题",  # 标题太短
            abstract="短摘要",  # 摘要太短
            applicants=[],  # 没有申请人
            inventors=[],  # 没有发明人
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="test_source"
        )
        patents.append(bad_patent)
        
        dataset = PatentDataset(patents=patents)
        
        report = await quality_controller.validate_dataset(dataset)
        
        assert report.total_records == 2
        assert report.valid_records == 1  # 只有一个有效专利
        assert report.invalid_records == 1  # 一个无效专利
        assert report.quality_score < 1.0  # 整体质量不是满分
        assert len(report.missing_fields) > 0  # 有缺失字段
        assert len(report.recommendations) > 0  # 有改进建议


@pytest.mark.asyncio
class TestPatentDatabaseManager:
    """测试专利数据库管理器."""
    
    @pytest.fixture
    async def db_manager(self):
        """创建临时数据库管理器."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        manager = PatentDatabaseManager(db_path)
        await manager.initialize()
        
        yield manager
        
        # 清理
        await manager.cleanup()
        if os.path.exists(db_path):
            os.unlink(db_path)
    
    async def test_save_and_get_patent(self, db_manager):
        """测试保存和获取专利."""
        patent = PatentData(
            application_number="CN202310123456.7",
            title="测试专利",
            abstract="这是一个测试专利的详细描述...",
            applicants=[PatentApplicant(name="测试公司", normalized_name="测试公司")],
            inventors=[PatentInventor(name="测试发明人", normalized_name="测试发明人")],
            application_date=datetime(2023, 1, 15),
            country="CN",
            status="申请中",
            data_source="test_source"
        )
        
        # 保存专利
        success = await db_manager.save_patent(patent)
        assert success == True
        
        # 获取专利
        retrieved_patent = await db_manager.get_patent(patent.patent_id)
        assert retrieved_patent is not None
        assert retrieved_patent.application_number == patent.application_number
        assert retrieved_patent.title == patent.title
        assert len(retrieved_patent.applicants) == 1
        assert len(retrieved_patent.inventors) == 1
    
    async def test_save_dataset(self, db_manager):
        """测试保存数据集."""
        patents = []
        for i in range(3):
            patent = PatentData(
                application_number=f"CN20231012345{i}.{i}",
                title=f"测试专利{i}",
                abstract=f"这是测试专利{i}的详细描述...",
                applicants=[PatentApplicant(name=f"公司{i}", normalized_name=f"公司{i}")],
                inventors=[PatentInventor(name=f"发明人{i}", normalized_name=f"发明人{i}")],
                application_date=datetime(2023, 1, 15 + i),
                country="CN",
                status="申请中",
                data_source="test_source"
            )
            patents.append(patent)
        
        dataset = PatentDataset(
            patents=patents,
            search_keywords=["测试"],
            data_sources=["test_source"]
        )
        
        # 保存数据集
        success = await db_manager.save_dataset(dataset)
        assert success == True
        
        # 验证数据库统计
        stats = await db_manager.get_database_stats()
        assert stats['total_patents'] == 3
        assert stats['total_datasets'] == 1


@pytest.mark.asyncio
class TestPatentDataProcessor:
    """测试专利数据处理器."""
    
    @pytest.fixture
    def processor(self):
        return PatentDataProcessor()
    
    async def test_process_dataset_complete(self, processor):
        """测试完整的数据集处理流程."""
        # 创建包含各种问题的测试数据集
        patents = []
        
        # 需要标准化的专利
        patent1 = PatentData(
            application_number="cn202310123456.7",  # 小写
            title="  农业机械装置  ",  # 多余空格
            abstract="本发明涉及<b>农业机械</b>装置...",  # HTML标签
            applicants=[PatentApplicant(name="测试公司有限公司", normalized_name="测试公司有限公司")],
            inventors=[PatentInventor(name="张三", normalized_name="张三")],
            application_date=datetime(2023, 1, 15),
            country="中国",  # 中文国家名
            status="pending",  # 英文状态
            data_source="source1",
            data_quality_score=0.9
        )
        patents.append(patent1)
        
        # 重复专利（质量更低）
        patent2 = PatentData(
            application_number="CN202310123456.7",  # 标准化后会与patent1相同
            title="农业机械装置",
            abstract="本发明涉及农业机械装置...",
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
            abstract="这是另一种农业机械装置的详细描述，具有不同的技术特征...",
            applicants=[PatentApplicant(name="另一家公司", normalized_name="另一家公司")],
            inventors=[PatentInventor(name="李四", normalized_name="李四")],
            application_date=datetime(2023, 2, 15),
            country="CN",
            status="申请中",
            data_source="source1",
            data_quality_score=0.85
        )
        patents.append(patent3)
        
        dataset = PatentDataset(
            patents=patents,
            search_keywords=["农业机械"],
            data_sources=["source1", "source2"]
        )
        
        # 处理数据集
        processed_dataset, quality_report = await processor.process_dataset(
            dataset,
            standardize=True,
            deduplicate=True,
            validate=True
        )
        
        # 验证处理结果
        assert len(processed_dataset.patents) == 2  # 去重后剩余2个专利
        assert quality_report is not None
        assert quality_report.total_records == 2
        assert quality_report.duplicate_records == 1  # 移除了1个重复项
        
        # 验证标准化效果
        for patent in processed_dataset.patents:
            assert patent.country == "CN"  # 国家代码已标准化
            assert patent.status in ["申请中", "已公开", "已授权"]  # 状态已标准化
            assert not patent.title.startswith(" ")  # 标题空格已清理
            assert not patent.title.endswith(" ")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v"])