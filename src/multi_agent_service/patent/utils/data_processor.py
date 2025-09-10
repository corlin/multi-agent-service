"""专利数据处理和质量控制工具."""

import asyncio
import logging
import re
from collections import defaultdict, Counter
from datetime import datetime
from typing import Any, Dict, List, Optional, Set, Tuple
from difflib import SequenceMatcher
import hashlib

from ..models.patent_data import (
    PatentData, 
    PatentDataset, 
    DataQualityReport,
    PatentApplicant,
    PatentInventor,
    PatentClassification
)
from ...utils.monitoring import metrics_collector


logger = logging.getLogger(__name__)


class PatentDataStandardizer:
    """专利数据标准化器."""
    
    def __init__(self):
        self.country_codes = {
            '中国': 'CN', '美国': 'US', '日本': 'JP', '德国': 'DE', 
            '英国': 'GB', '法国': 'FR', '韩国': 'KR', '加拿大': 'CA',
            'China': 'CN', 'United States': 'US', 'Japan': 'JP', 
            'Germany': 'DE', 'United Kingdom': 'GB', 'France': 'FR',
            'South Korea': 'KR', 'Canada': 'CA'
        }
        
        self.status_mapping = {
            'pending': '申请中', 'published': '已公开', 'granted': '已授权',
            'expired': '已失效', 'withdrawn': '已撤回', 'rejected': '已驳回',
            'application': '申请中', 'publication': '已公开', 'grant': '已授权'
        }
        
        self.company_suffixes = {
            '有限公司': 'Co., Ltd.',
            '股份有限公司': 'Co., Ltd.',
            '科技有限公司': 'Technology Co., Ltd.',
            '技术有限公司': 'Technology Co., Ltd.',
            'Inc.': 'Inc.',
            'Corp.': 'Corp.',
            'Corporation': 'Corp.',
            'LLC': 'LLC',
            'Ltd.': 'Ltd.',
            'Limited': 'Ltd.'
        }
    
    async def standardize_patent(self, patent: PatentData) -> PatentData:
        """标准化单个专利数据."""
        try:
            # 标准化国家代码
            patent.country = self._standardize_country(patent.country)
            
            # 标准化专利状态
            patent.status = self._standardize_status(patent.status)
            
            # 标准化申请人信息
            for applicant in patent.applicants:
                applicant.normalized_name = self._standardize_company_name(applicant.name)
                if applicant.country:
                    applicant.country = self._standardize_country(applicant.country)
            
            # 标准化发明人信息
            for inventor in patent.inventors:
                inventor.normalized_name = self._standardize_person_name(inventor.name)
                if inventor.country:
                    inventor.country = self._standardize_country(inventor.country)
            
            # 标准化分类信息
            for classification in patent.classifications:
                if classification.ipc_class:
                    classification.ipc_class = self._standardize_ipc_class(classification.ipc_class)
            
            # 标准化标题和摘要
            patent.title = self._clean_text(patent.title)
            patent.abstract = self._clean_text(patent.abstract)
            
            # 标准化关键词
            patent.keywords = self._standardize_keywords(patent.keywords)
            
            # 更新质量评分
            patent.data_quality_score = patent.calculate_quality_score()
            
            logger.debug(f"Standardized patent {patent.application_number}")
            return patent
            
        except Exception as e:
            logger.error(f"Error standardizing patent {patent.application_number}: {str(e)}")
            raise
    
    async def standardize_dataset(self, dataset: PatentDataset) -> PatentDataset:
        """标准化专利数据集."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting standardization of {len(dataset.patents)} patents")
            
            # 并行处理专利数据
            tasks = [self.standardize_patent(patent) for patent in dataset.patents]
            standardized_patents = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 过滤处理成功的专利
            valid_patents = []
            error_count = 0
            
            for i, result in enumerate(standardized_patents):
                if isinstance(result, Exception):
                    logger.error(f"Failed to standardize patent {i}: {str(result)}")
                    error_count += 1
                else:
                    valid_patents.append(result)
            
            dataset.patents = valid_patents
            dataset.total_count = len(valid_patents)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 记录监控指标
            metrics_collector.record_metric(
                "patent.data_standardization_duration",
                processing_time,
                tags={"unit": "seconds", "patent_count": str(len(valid_patents))}
            )
            
            metrics_collector.record_metric(
                "patent.standardization_error_count",
                error_count,
                tags={"unit": "count"}
            )
            
            logger.info(f"Standardization completed: {len(valid_patents)} patents processed, {error_count} errors")
            return dataset
            
        except Exception as e:
            logger.error(f"Error standardizing dataset: {str(e)}")
            raise
    
    def _standardize_country(self, country: str) -> str:
        """标准化国家代码."""
        if not country:
            return 'UNKNOWN'
        
        country = country.strip()
        
        # 直接匹配
        if country.upper() in ['CN', 'US', 'JP', 'DE', 'GB', 'FR', 'KR', 'CA']:
            return country.upper()
        
        # 名称匹配
        return self.country_codes.get(country, country.upper())
    
    def _standardize_status(self, status: str) -> str:
        """标准化专利状态."""
        if not status:
            return '未知'
        
        status_lower = status.lower().strip()
        return self.status_mapping.get(status_lower, status)
    
    def _standardize_company_name(self, name: str) -> str:
        """标准化公司名称."""
        if not name:
            return name
        
        # 清理多余空格
        name = re.sub(r'\s+', ' ', name.strip())
        
        # 统一公司后缀
        for suffix, standard_suffix in self.company_suffixes.items():
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip() + ' ' + standard_suffix
                break
        
        # 移除特殊字符
        name = re.sub(r'[^\w\s\.,\-()]', '', name)
        
        return name.strip()
    
    def _standardize_person_name(self, name: str) -> str:
        """标准化人名."""
        if not name:
            return name
        
        # 清理多余空格
        name = re.sub(r'\s+', ' ', name.strip())
        
        # 移除特殊字符（保留常见的人名字符）
        name = re.sub(r'[^\w\s\-\.]', '', name)
        
        return name.strip()
    
    def _standardize_ipc_class(self, ipc_class: str) -> str:
        """标准化IPC分类号."""
        if not ipc_class:
            return ipc_class
        
        # 移除多余空格并转换为大写
        ipc_class = re.sub(r'\s+', '', ipc_class.upper())
        
        # 标准化格式 (例如: A01B1/00)
        match = re.match(r'^([A-H])(\d{2})([A-Z])(\d+)/(\d+)', ipc_class)
        if match:
            return f"{match.group(1)}{match.group(2)}{match.group(3)} {match.group(4)}/{match.group(5)}"
        
        return ipc_class
    
    def _clean_text(self, text: str) -> str:
        """清理文本内容."""
        if not text:
            return text
        
        # 移除多余空格和换行符
        text = re.sub(r'\s+', ' ', text.strip())
        
        # 移除HTML标签
        text = re.sub(r'<[^>]+>', '', text)
        
        # 移除特殊字符（保留基本标点）
        text = re.sub(r'[^\w\s\.,;:!?()[\]{}"\'-]', '', text)
        
        return text.strip()
    
    def _standardize_keywords(self, keywords: List[str]) -> List[str]:
        """标准化关键词."""
        if not keywords:
            return []
        
        standardized = []
        for keyword in keywords:
            if keyword and keyword.strip():
                # 转换为小写并清理
                clean_keyword = self._clean_text(keyword.lower())
                if clean_keyword and len(clean_keyword) >= 2:
                    standardized.append(clean_keyword)
        
        # 去重并排序
        return sorted(list(set(standardized)))


class PatentDeduplicator:
    """专利去重器."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    async def deduplicate_dataset(self, dataset: PatentDataset) -> Tuple[PatentDataset, int]:
        """去重专利数据集."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting deduplication of {len(dataset.patents)} patents")
            
            # 构建哈希索引
            content_hashes = {}
            similarity_groups = defaultdict(list)
            removed_count = 0
            
            for i, patent in enumerate(dataset.patents):
                # 精确匹配去重
                if patent.content_hash in content_hashes:
                    logger.debug(f"Found exact duplicate: {patent.application_number}")
                    removed_count += 1
                    continue
                
                content_hashes[patent.content_hash] = i
                similarity_groups[patent.similarity_hash].append(i)
            
            # 处理相似性去重
            unique_indices = set(content_hashes.values())
            
            for similar_indices in similarity_groups.values():
                if len(similar_indices) > 1:
                    # 保留质量评分最高的专利
                    best_index = max(similar_indices, 
                                   key=lambda i: dataset.patents[i].data_quality_score)
                    
                    for index in similar_indices:
                        if index != best_index and index in unique_indices:
                            unique_indices.remove(index)
                            removed_count += 1
                            logger.debug(f"Removed similar patent at index {index}")
            
            # 构建去重后的数据集
            unique_patents = [dataset.patents[i] for i in sorted(unique_indices)]
            
            new_dataset = PatentDataset(
                patents=unique_patents,
                total_count=len(unique_patents),
                search_keywords=dataset.search_keywords,
                collection_date=dataset.collection_date,
                data_sources=dataset.data_sources
            )
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 记录监控指标
            metrics_collector.record_metric(
                "patent.deduplication_duration",
                processing_time,
                tags={"unit": "seconds"}
            )
            
            metrics_collector.record_metric(
                "patent.duplicates_removed",
                removed_count,
                tags={"unit": "count"}
            )
            
            logger.info(f"Deduplication completed: removed {removed_count} duplicates, {len(unique_patents)} unique patents remain")
            return new_dataset, removed_count
            
        except Exception as e:
            logger.error(f"Error during deduplication: {str(e)}")
            raise


class PatentQualityController:
    """专利质量控制器."""
    
    def __init__(self):
        self.required_fields = [
            'application_number', 'title', 'abstract', 'application_date', 'country'
        ]
        
        self.validation_rules = {
            'application_number': self._validate_application_number,
            'title': self._validate_title,
            'abstract': self._validate_abstract,
            'application_date': self._validate_date,
            'country': self._validate_country
        }
    
    async def validate_dataset(self, dataset: PatentDataset) -> DataQualityReport:
        """验证数据集质量."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting quality validation of {len(dataset.patents)} patents")
            
            report = DataQualityReport(
                dataset_id=dataset.dataset_id,
                total_records=len(dataset.patents),
                valid_records=0,
                invalid_records=0,
                duplicate_records=0,
                quality_score=0.0,
                completeness_score=0.0,
                accuracy_score=0.0,
                consistency_score=0.0
            )
            
            # 验证每个专利
            validation_results = []
            for patent in dataset.patents:
                result = await self._validate_patent(patent)
                validation_results.append(result)
            
            # 统计结果
            valid_count = sum(1 for r in validation_results if r['is_valid'])
            report.valid_records = valid_count
            report.invalid_records = len(dataset.patents) - valid_count
            
            # 计算质量指标
            report.completeness_score = self._calculate_completeness_score(validation_results)
            report.accuracy_score = self._calculate_accuracy_score(validation_results)
            report.consistency_score = self._calculate_consistency_score(dataset.patents)
            report.quality_score = report.calculate_overall_score()
            
            # 统计问题
            report.missing_fields = self._count_missing_fields(validation_results)
            report.invalid_formats = self._count_invalid_formats(validation_results)
            report.data_anomalies = self._detect_anomalies(dataset.patents)
            
            # 生成建议
            self._generate_recommendations(report)
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 记录监控指标
            metrics_collector.record_metric(
                "patent.quality_validation_duration",
                processing_time,
                tags={"unit": "seconds"}
            )
            
            metrics_collector.record_metric(
                "patent.quality_score",
                report.quality_score,
                tags={"unit": "score"}
            )
            
            logger.info(f"Quality validation completed: {report.quality_score:.2f} overall score")
            return report
            
        except Exception as e:
            logger.error(f"Error during quality validation: {str(e)}")
            raise
    
    async def _validate_patent(self, patent: PatentData) -> Dict[str, Any]:
        """验证单个专利."""
        result = {
            'patent_id': patent.patent_id,
            'is_valid': True,
            'missing_fields': [],
            'invalid_formats': [],
            'errors': []
        }
        
        try:
            # 检查必需字段
            for field in self.required_fields:
                value = getattr(patent, field, None)
                if not value:
                    result['missing_fields'].append(field)
                    result['is_valid'] = False
            
            # 验证字段格式
            for field, validator in self.validation_rules.items():
                value = getattr(patent, field, None)
                if value and not validator(value):
                    result['invalid_formats'].append(field)
                    result['is_valid'] = False
            
            # 验证日期逻辑
            if patent.application_date and patent.publication_date:
                if patent.publication_date < patent.application_date:
                    result['errors'].append('publication_date_before_application_date')
                    result['is_valid'] = False
            
            # 验证申请人和发明人
            if not patent.applicants:
                result['missing_fields'].append('applicants')
                result['is_valid'] = False
            
            if not patent.inventors:
                result['missing_fields'].append('inventors')
                result['is_valid'] = False
            
        except Exception as e:
            result['errors'].append(f'validation_error: {str(e)}')
            result['is_valid'] = False
        
        return result
    
    def _validate_application_number(self, value: str) -> bool:
        """验证申请号格式."""
        if not isinstance(value, str) or len(value) < 5:
            return False
        return bool(re.match(r'^[A-Z0-9\-\.]+$', value))
    
    def _validate_title(self, value: str) -> bool:
        """验证标题."""
        return isinstance(value, str) and 5 <= len(value) <= 500
    
    def _validate_abstract(self, value: str) -> bool:
        """验证摘要."""
        return isinstance(value, str) and 10 <= len(value) <= 5000
    
    def _validate_date(self, value: datetime) -> bool:
        """验证日期."""
        if not isinstance(value, datetime):
            return False
        # 检查日期是否合理（1800年后，未来不超过1年）
        min_date = datetime(1800, 1, 1)
        max_date = datetime.now().replace(year=datetime.now().year + 1)
        return min_date <= value <= max_date
    
    def _validate_country(self, value: str) -> bool:
        """验证国家代码."""
        return isinstance(value, str) and len(value) >= 2
    
    def _calculate_completeness_score(self, validation_results: List[Dict[str, Any]]) -> float:
        """计算完整性评分."""
        if not validation_results:
            return 0.0
        
        total_fields = len(self.required_fields) * len(validation_results)
        missing_fields = sum(len(r['missing_fields']) for r in validation_results)
        
        return max(0.0, (total_fields - missing_fields) / total_fields)
    
    def _calculate_accuracy_score(self, validation_results: List[Dict[str, Any]]) -> float:
        """计算准确性评分."""
        if not validation_results:
            return 0.0
        
        total_validations = len(validation_results)
        invalid_formats = sum(len(r['invalid_formats']) for r in validation_results)
        errors = sum(len(r['errors']) for r in validation_results)
        
        total_issues = invalid_formats + errors
        return max(0.0, (total_validations - total_issues) / total_validations)
    
    def _calculate_consistency_score(self, patents: List[PatentData]) -> float:
        """计算一致性评分."""
        if not patents:
            return 0.0
        
        # 检查数据源一致性
        sources = [p.data_source for p in patents]
        source_consistency = len(set(sources)) / len(sources) if sources else 0.0
        
        # 检查国家代码一致性
        countries = [p.country for p in patents if p.country]
        country_consistency = len(set(countries)) / len(countries) if countries else 0.0
        
        # 检查状态一致性
        statuses = [p.status for p in patents if p.status]
        status_consistency = len(set(statuses)) / len(statuses) if statuses else 0.0
        
        # 综合一致性评分（值越小越一致，所以用1减去）
        consistency = 1.0 - (source_consistency + country_consistency + status_consistency) / 3.0
        return max(0.0, consistency)
    
    def _count_missing_fields(self, validation_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计缺失字段."""
        missing_count = defaultdict(int)
        for result in validation_results:
            for field in result['missing_fields']:
                missing_count[field] += 1
        return dict(missing_count)
    
    def _count_invalid_formats(self, validation_results: List[Dict[str, Any]]) -> Dict[str, int]:
        """统计格式错误."""
        invalid_count = defaultdict(int)
        for result in validation_results:
            for field in result['invalid_formats']:
                invalid_count[field] += 1
        return dict(invalid_count)
    
    def _detect_anomalies(self, patents: List[PatentData]) -> List[str]:
        """检测数据异常."""
        anomalies = []
        
        if not patents:
            return anomalies
        
        # 检测异常长的标题或摘要
        title_lengths = [len(p.title) for p in patents if p.title]
        if title_lengths:
            avg_title_length = sum(title_lengths) / len(title_lengths)
            for patent in patents:
                if patent.title and len(patent.title) > avg_title_length * 3:
                    anomalies.append(f"异常长标题: {patent.application_number}")
        
        # 检测异常的申请日期
        dates = [p.application_date for p in patents if p.application_date]
        if dates:
            min_date = min(dates)
            max_date = max(dates)
            date_range = (max_date - min_date).days
            
            if date_range > 365 * 50:  # 超过50年
                anomalies.append(f"申请日期跨度异常: {date_range}天")
        
        # 检测重复的申请号
        app_numbers = [p.application_number for p in patents if p.application_number]
        duplicates = [num for num, count in Counter(app_numbers).items() if count > 1]
        for dup in duplicates:
            anomalies.append(f"重复申请号: {dup}")
        
        return anomalies
    
    def _generate_recommendations(self, report: DataQualityReport):
        """生成改进建议."""
        if report.completeness_score < 0.8:
            report.add_recommendation("提高数据完整性：确保所有必需字段都有值")
        
        if report.accuracy_score < 0.8:
            report.add_recommendation("改善数据准确性：检查并修正格式错误和逻辑错误")
        
        if report.consistency_score < 0.8:
            report.add_recommendation("增强数据一致性：统一数据格式和编码标准")
        
        if report.missing_fields:
            most_missing = max(report.missing_fields.items(), key=lambda x: x[1])
            report.add_recommendation(f"优先补充缺失最多的字段: {most_missing[0]} (缺失{most_missing[1]}条记录)")
        
        if report.invalid_formats:
            most_invalid = max(report.invalid_formats.items(), key=lambda x: x[1])
            report.add_recommendation(f"优先修正格式错误最多的字段: {most_invalid[0]} (错误{most_invalid[1]}条记录)")
        
        if report.data_anomalies:
            report.add_recommendation(f"处理检测到的{len(report.data_anomalies)}个数据异常")


class PatentDataProcessor:
    """专利数据处理器主类."""
    
    def __init__(self):
        self.standardizer = PatentDataStandardizer()
        self.deduplicator = PatentDeduplicator()
        self.quality_controller = PatentQualityController()
    
    async def process_dataset(self, dataset: PatentDataset, 
                            standardize: bool = True,
                            deduplicate: bool = True,
                            validate: bool = True) -> Tuple[PatentDataset, DataQualityReport]:
        """处理专利数据集."""
        start_time = datetime.now()
        
        try:
            logger.info(f"Starting processing of dataset {dataset.dataset_id}")
            
            processed_dataset = dataset
            removed_duplicates = 0
            
            # 数据标准化
            if standardize:
                logger.info("Standardizing dataset...")
                processed_dataset = await self.standardizer.standardize_dataset(processed_dataset)
            
            # 去重处理
            if deduplicate:
                logger.info("Deduplicating dataset...")
                processed_dataset, removed_duplicates = await self.deduplicator.deduplicate_dataset(processed_dataset)
            
            # 质量验证
            quality_report = None
            if validate:
                logger.info("Validating dataset quality...")
                quality_report = await self.quality_controller.validate_dataset(processed_dataset)
                quality_report.duplicate_records = removed_duplicates
            
            # 计算质量指标
            processed_dataset.calculate_quality_metrics()
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 记录监控指标
            metrics_collector.record_metric(
                "patent.dataset_processing_duration",
                processing_time,
                tags={"unit": "seconds", "patent_count": str(len(processed_dataset.patents))}
            )
            
            logger.info(f"Dataset processing completed in {processing_time:.2f}s")
            
            return processed_dataset, quality_report
            
        except Exception as e:
            logger.error(f"Error processing dataset: {str(e)}")
            raise