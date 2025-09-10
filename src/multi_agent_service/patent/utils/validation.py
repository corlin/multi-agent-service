"""Patent data validation utilities using existing validation framework."""

import re
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field, field_validator, ValidationError

from ..models.data import Patent, PatentDataset, PatentDataQuality
from ...utils.monitoring import metrics_collector, measure_performance


class PatentValidationError(Exception):
    """专利验证错误."""
    pass


class PatentFieldValidation(BaseModel):
    """专利字段验证模型."""
    
    field_name: str = Field(..., description="字段名称")
    is_valid: bool = Field(..., description="是否有效")
    error_message: Optional[str] = Field(None, description="错误信息")
    suggested_fix: Optional[str] = Field(None, description="建议修复")


class PatentValidationResult(BaseModel):
    """专利验证结果模型."""
    
    patent_id: str = Field(..., description="专利ID")
    is_valid: bool = Field(default=False, description="整体是否有效")
    field_validations: List[PatentFieldValidation] = Field(default_factory=list, description="字段验证结果")
    overall_score: float = Field(default=0.0, description="整体评分")
    critical_errors: List[str] = Field(default_factory=list, description="严重错误")
    warnings: List[str] = Field(default_factory=list, description="警告")
    
    def add_field_validation(self, field_name: str, is_valid: bool, 
                           error_message: Optional[str] = None, 
                           suggested_fix: Optional[str] = None):
        """添加字段验证结果."""
        validation = PatentFieldValidation(
            field_name=field_name,
            is_valid=is_valid,
            error_message=error_message,
            suggested_fix=suggested_fix
        )
        self.field_validations.append(validation)
        
        if not is_valid and error_message:
            if "必需" in error_message or "缺失" in error_message:
                self.critical_errors.append(f"{field_name}: {error_message}")
            else:
                self.warnings.append(f"{field_name}: {error_message}")
    
    def calculate_score(self):
        """计算整体评分."""
        if not self.field_validations:
            self.overall_score = 0.0
            return
        
        valid_count = sum(1 for v in self.field_validations if v.is_valid)
        self.overall_score = valid_count / len(self.field_validations)
        
        # 严重错误会大幅降低评分
        if self.critical_errors:
            self.overall_score *= 0.5
        
        self.is_valid = self.overall_score >= 0.8 and len(self.critical_errors) == 0


class DatasetValidationResult(BaseModel):
    """数据集验证结果模型."""
    
    dataset_id: str = Field(..., description="数据集ID")
    total_patents: int = Field(..., description="专利总数")
    valid_patents: int = Field(0, description="有效专利数")
    invalid_patents: int = Field(0, description="无效专利数")
    validation_score: float = Field(0.0, description="验证评分")
    patent_results: List[PatentValidationResult] = Field(default_factory=list, description="专利验证结果")
    summary_issues: List[str] = Field(default_factory=list, description="汇总问题")
    
    def calculate_summary(self):
        """计算汇总统计."""
        self.valid_patents = sum(1 for r in self.patent_results if r.is_valid)
        self.invalid_patents = self.total_patents - self.valid_patents
        
        if self.total_patents > 0:
            self.validation_score = self.valid_patents / self.total_patents
        
        # 汇总常见问题
        field_errors = {}
        for result in self.patent_results:
            for validation in result.field_validations:
                if not validation.is_valid and validation.error_message:
                    field_errors[validation.field_name] = field_errors.get(validation.field_name, 0) + 1
        
        # 生成汇总问题
        for field, count in field_errors.items():
            if count > self.total_patents * 0.1:  # 超过10%的专利有此问题
                self.summary_issues.append(f"{field}字段问题: {count}个专利受影响")


class PatentValidator:
    """专利数据验证器，利用现有验证框架."""
    
    def __init__(self):
        """初始化验证器."""
        self.logger = logging.getLogger(__name__)
        
        # 验证规则配置
        self.validation_rules = {
            'application_number': {
                'required': True,
                'min_length': 5,
                'max_length': 50,
                'pattern': r'^[A-Z0-9]+$',
                'description': '申请号必须为5-50位字母数字组合'
            },
            'title': {
                'required': True,
                'min_length': 5,
                'max_length': 500,
                'description': '标题长度必须在5-500字符之间'
            },
            'abstract': {
                'required': False,
                'min_length': 10,
                'max_length': 5000,
                'description': '摘要长度应在10-5000字符之间'
            },
            'applicants': {
                'required': True,
                'min_items': 1,
                'max_items': 20,
                'description': '申请人至少1个，最多20个'
            },
            'inventors': {
                'required': True,
                'min_items': 1,
                'max_items': 50,
                'description': '发明人至少1个，最多50个'
            },
            'application_date': {
                'required': True,
                'min_year': 1970,
                'max_year_offset': 1,  # 允许未来1年
                'description': '申请日期必须在合理范围内'
            },
            'ipc_classes': {
                'required': False,
                'min_items': 0,
                'max_items': 20,
                'pattern': r'^[A-H]\d{2}[A-Z]\d+/\d+$',
                'description': 'IPC分类格式应为标准格式'
            },
            'country': {
                'required': True,
                'valid_codes': ['CN', 'US', 'JP', 'DE', 'GB', 'FR', 'KR', 'EP', 'WO'],
                'description': '国家代码必须为有效的ISO代码'
            }
        }
        
        # 统计信息
        self.validation_stats = {
            'total_validated': 0,
            'valid_patents': 0,
            'invalid_patents': 0,
            'field_error_counts': {},
            'validation_duration': 0.0
        }
    
    async def validate_patent(self, patent: Patent) -> PatentValidationResult:
        """验证单个专利."""
        try:
            with measure_performance("patent.validation.single_patent"):
                result = PatentValidationResult(
                    patent_id=patent.application_number or "UNKNOWN"
                )
                
                # 验证各个字段
                await self._validate_application_number(patent, result)
                await self._validate_title(patent, result)
                await self._validate_abstract(patent, result)
                await self._validate_applicants(patent, result)
                await self._validate_inventors(patent, result)
                await self._validate_application_date(patent, result)
                await self._validate_ipc_classes(patent, result)
                await self._validate_country(patent, result)
                await self._validate_status(patent, result)
                
                # 计算整体评分
                result.calculate_score()
                
                # 更新统计
                self.validation_stats['total_validated'] += 1
                if result.is_valid:
                    self.validation_stats['valid_patents'] += 1
                else:
                    self.validation_stats['invalid_patents'] += 1
                
                # 记录监控指标
                metrics_collector.record_metric(
                    "patent.validation.patent_validated", 
                    1, 
                    tags={
                        "is_valid": str(result.is_valid),
                        "score": f"{result.overall_score:.2f}"
                    }
                )
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error validating patent {patent.application_number}: {str(e)}")
            result = PatentValidationResult(
                patent_id=patent.application_number or "UNKNOWN",
                is_valid=False
            )
            result.critical_errors.append(f"验证过程出错: {str(e)}")
            return result
    
    async def _validate_application_number(self, patent: Patent, result: PatentValidationResult):
        """验证申请号."""
        rules = self.validation_rules['application_number']
        
        if not patent.application_number:
            if rules['required']:
                result.add_field_validation(
                    'application_number', False, 
                    '申请号为必需字段', 
                    '请提供有效的申请号'
                )
            return
        
        app_num = patent.application_number.strip()
        
        # 长度检查
        if len(app_num) < rules['min_length'] or len(app_num) > rules['max_length']:
            result.add_field_validation(
                'application_number', False,
                f'申请号长度应在{rules["min_length"]}-{rules["max_length"]}字符之间',
                f'当前长度: {len(app_num)}'
            )
            return
        
        # 格式检查
        if not re.match(rules['pattern'], app_num):
            result.add_field_validation(
                'application_number', False,
                '申请号格式不正确，应为字母数字组合',
                '请检查申请号格式'
            )
            return
        
        result.add_field_validation('application_number', True)
    
    async def _validate_title(self, patent: Patent, result: PatentValidationResult):
        """验证标题."""
        rules = self.validation_rules['title']
        
        if not patent.title:
            if rules['required']:
                result.add_field_validation(
                    'title', False,
                    '标题为必需字段',
                    '请提供专利标题'
                )
            return
        
        title = patent.title.strip()
        
        # 长度检查
        if len(title) < rules['min_length'] or len(title) > rules['max_length']:
            result.add_field_validation(
                'title', False,
                f'标题长度应在{rules["min_length"]}-{rules["max_length"]}字符之间',
                f'当前长度: {len(title)}'
            )
            return
        
        # 内容检查
        if title.lower() in ['unknown', 'untitled', '未知', '无标题']:
            result.add_field_validation(
                'title', False,
                '标题内容无效',
                '请提供有意义的专利标题'
            )
            return
        
        result.add_field_validation('title', True)
    
    async def _validate_abstract(self, patent: Patent, result: PatentValidationResult):
        """验证摘要."""
        rules = self.validation_rules['abstract']
        
        if not patent.abstract:
            if rules['required']:
                result.add_field_validation(
                    'abstract', False,
                    '摘要为必需字段',
                    '请提供专利摘要'
                )
            else:
                result.add_field_validation('abstract', True)  # 可选字段
            return
        
        abstract = patent.abstract.strip()
        
        # 长度检查
        if len(abstract) < rules['min_length'] or len(abstract) > rules['max_length']:
            result.add_field_validation(
                'abstract', False,
                f'摘要长度应在{rules["min_length"]}-{rules["max_length"]}字符之间',
                f'当前长度: {len(abstract)}'
            )
            return
        
        result.add_field_validation('abstract', True)
    
    async def _validate_applicants(self, patent: Patent, result: PatentValidationResult):
        """验证申请人."""
        rules = self.validation_rules['applicants']
        
        if not patent.applicants:
            if rules['required']:
                result.add_field_validation(
                    'applicants', False,
                    '申请人为必需字段',
                    '请提供至少一个申请人'
                )
            return
        
        # 数量检查
        if len(patent.applicants) < rules['min_items'] or len(patent.applicants) > rules['max_items']:
            result.add_field_validation(
                'applicants', False,
                f'申请人数量应在{rules["min_items"]}-{rules["max_items"]}之间',
                f'当前数量: {len(patent.applicants)}'
            )
            return
        
        # 内容检查
        valid_applicants = []
        for applicant in patent.applicants:
            if applicant and applicant.strip() and len(applicant.strip()) >= 2:
                valid_applicants.append(applicant.strip())
        
        if len(valid_applicants) == 0:
            result.add_field_validation(
                'applicants', False,
                '没有有效的申请人',
                '请提供有效的申请人名称'
            )
            return
        
        result.add_field_validation('applicants', True)
    
    async def _validate_inventors(self, patent: Patent, result: PatentValidationResult):
        """验证发明人."""
        rules = self.validation_rules['inventors']
        
        if not patent.inventors:
            if rules['required']:
                result.add_field_validation(
                    'inventors', False,
                    '发明人为必需字段',
                    '请提供至少一个发明人'
                )
            return
        
        # 数量检查
        if len(patent.inventors) < rules['min_items'] or len(patent.inventors) > rules['max_items']:
            result.add_field_validation(
                'inventors', False,
                f'发明人数量应在{rules["min_items"]}-{rules["max_items"]}之间',
                f'当前数量: {len(patent.inventors)}'
            )
            return
        
        # 内容检查
        valid_inventors = []
        for inventor in patent.inventors:
            if inventor and inventor.strip() and len(inventor.strip()) >= 2:
                valid_inventors.append(inventor.strip())
        
        if len(valid_inventors) == 0:
            result.add_field_validation(
                'inventors', False,
                '没有有效的发明人',
                '请提供有效的发明人姓名'
            )
            return
        
        result.add_field_validation('inventors', True)
    
    async def _validate_application_date(self, patent: Patent, result: PatentValidationResult):
        """验证申请日期."""
        rules = self.validation_rules['application_date']
        
        if not patent.application_date:
            if rules['required']:
                result.add_field_validation(
                    'application_date', False,
                    '申请日期为必需字段',
                    '请提供有效的申请日期'
                )
            return
        
        # 年份范围检查
        current_year = datetime.now().year
        min_year = rules['min_year']
        max_year = current_year + rules['max_year_offset']
        
        if patent.application_date.year < min_year or patent.application_date.year > max_year:
            result.add_field_validation(
                'application_date', False,
                f'申请日期年份应在{min_year}-{max_year}之间',
                f'当前年份: {patent.application_date.year}'
            )
            return
        
        # 未来日期检查
        if patent.application_date > datetime.now() + timedelta(days=365):
            result.add_field_validation(
                'application_date', False,
                '申请日期不能超过未来一年',
                '请检查申请日期是否正确'
            )
            return
        
        result.add_field_validation('application_date', True)
    
    async def _validate_ipc_classes(self, patent: Patent, result: PatentValidationResult):
        """验证IPC分类."""
        rules = self.validation_rules['ipc_classes']
        
        if not patent.ipc_classes:
            result.add_field_validation('ipc_classes', True)  # 可选字段
            return
        
        # 数量检查
        if len(patent.ipc_classes) > rules['max_items']:
            result.add_field_validation(
                'ipc_classes', False,
                f'IPC分类数量不能超过{rules["max_items"]}个',
                f'当前数量: {len(patent.ipc_classes)}'
            )
            return
        
        # 格式检查
        invalid_ipc = []
        for ipc in patent.ipc_classes:
            if not re.match(rules['pattern'], ipc):
                invalid_ipc.append(ipc)
        
        if invalid_ipc:
            result.add_field_validation(
                'ipc_classes', False,
                f'IPC分类格式不正确: {", ".join(invalid_ipc[:3])}',
                '请使用标准IPC格式，如: G06F15/00'
            )
            return
        
        result.add_field_validation('ipc_classes', True)
    
    async def _validate_country(self, patent: Patent, result: PatentValidationResult):
        """验证国家代码."""
        rules = self.validation_rules['country']
        
        if not patent.country:
            if rules['required']:
                result.add_field_validation(
                    'country', False,
                    '国家代码为必需字段',
                    '请提供有效的国家代码'
                )
            return
        
        country_code = patent.country.strip().upper()
        
        if country_code not in rules['valid_codes']:
            result.add_field_validation(
                'country', False,
                f'无效的国家代码: {country_code}',
                f'有效代码: {", ".join(rules["valid_codes"])}'
            )
            return
        
        result.add_field_validation('country', True)
    
    async def _validate_status(self, patent: Patent, result: PatentValidationResult):
        """验证专利状态."""
        if not patent.status:
            result.add_field_validation(
                'status', False,
                '专利状态为必需字段',
                '请提供专利状态'
            )
            return
        
        valid_statuses = ['已公开', '已授权', '审查中', '已过期', '已撤回', '已驳回', 
                         'published', 'granted', 'pending', 'expired', 'withdrawn', 'rejected']
        
        if patent.status.lower() not in [s.lower() for s in valid_statuses]:
            result.add_field_validation(
                'status', False,
                f'无效的专利状态: {patent.status}',
                f'有效状态: {", ".join(valid_statuses[:6])}'
            )
            return
        
        result.add_field_validation('status', True)
    
    async def validate_dataset(self, patents: List[Patent], dataset_id: str = "unknown") -> DatasetValidationResult:
        """验证专利数据集."""
        try:
            with measure_performance("patent.validation.dataset"):
                result = DatasetValidationResult(
                    dataset_id=dataset_id,
                    total_patents=len(patents)
                )
                
                # 验证每个专利
                for patent in patents:
                    patent_result = await self.validate_patent(patent)
                    result.patent_results.append(patent_result)
                
                # 计算汇总统计
                result.calculate_summary()
                
                # 记录监控指标
                metrics_collector.record_metric(
                    "patent.validation.dataset_validated", 
                    1, 
                    tags={
                        "dataset_id": dataset_id,
                        "total_patents": str(result.total_patents),
                        "valid_patents": str(result.valid_patents),
                        "validation_score": f"{result.validation_score:.2f}"
                    }
                )
                
                self.logger.info(
                    f"Dataset validation completed: {result.valid_patents}/{result.total_patents} "
                    f"patents valid (score: {result.validation_score:.2f})"
                )
                
                return result
                
        except Exception as e:
            self.logger.error(f"Error validating dataset {dataset_id}: {str(e)}")
            result = DatasetValidationResult(
                dataset_id=dataset_id,
                total_patents=len(patents)
            )
            result.summary_issues.append(f"数据集验证过程出错: {str(e)}")
            return result
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """获取验证统计信息."""
        return self.validation_stats.copy()
    
    def reset_stats(self):
        """重置统计信息."""
        self.validation_stats = {
            'total_validated': 0,
            'valid_patents': 0,
            'invalid_patents': 0,
            'field_error_counts': {},
            'validation_duration': 0.0
        }


class PatentDataQualityValidator:
    """专利数据质量验证器."""
    
    def __init__(self):
        """初始化质量验证器."""
        self.logger = logging.getLogger(__name__)
        self.validator = PatentValidator()
    
    async def validate_and_assess_quality(self, patents: List[Patent], dataset_id: str = "unknown") -> Tuple[DatasetValidationResult, PatentDataQuality]:
        """验证数据并评估质量."""
        try:
            with measure_performance("patent.validation.quality_assessment"):
                # 数据验证
                validation_result = await self.validator.validate_dataset(patents, dataset_id)
                
                # 质量评估
                quality = PatentDataQuality()
                
                if validation_result.total_patents > 0:
                    # 完整性评分 = 有效专利比例
                    quality.completeness_score = validation_result.validation_score
                    
                    # 准确性评分 = 平均字段验证评分
                    total_score = sum(r.overall_score for r in validation_result.patent_results)
                    quality.accuracy_score = total_score / validation_result.total_patents
                    
                    # 一致性评分 = 格式一致性
                    quality.consistency_score = await self._calculate_consistency_score(validation_result)
                    
                    # 时效性评分 = 基于申请日期分布
                    quality.timeliness_score = await self._calculate_timeliness_score(patents)
                    
                    # 计算总体评分
                    quality.calculate_overall_score()
                    
                    # 收集质量问题
                    quality.issues.extend(validation_result.summary_issues)
                    await self._identify_additional_quality_issues(quality, validation_result)
                
                # 记录监控指标
                metrics_collector.record_metric(
                    "patent.validation.quality_assessed", 
                    1, 
                    tags={
                        "dataset_id": dataset_id,
                        "overall_score": f"{quality.overall_score:.2f}"
                    }
                )
                
                return validation_result, quality
                
        except Exception as e:
            self.logger.error(f"Error in quality validation for dataset {dataset_id}: {str(e)}")
            # 返回默认结果
            validation_result = DatasetValidationResult(
                dataset_id=dataset_id,
                total_patents=len(patents)
            )
            quality = PatentDataQuality()
            quality.issues.append(f"质量验证过程出错: {str(e)}")
            return validation_result, quality
    
    async def _calculate_consistency_score(self, validation_result: DatasetValidationResult) -> float:
        """计算一致性评分."""
        try:
            if not validation_result.patent_results:
                return 0.0
            
            # 统计各字段的验证通过率
            field_pass_rates = {}
            for result in validation_result.patent_results:
                for validation in result.field_validations:
                    field_name = validation.field_name
                    if field_name not in field_pass_rates:
                        field_pass_rates[field_name] = []
                    field_pass_rates[field_name].append(validation.is_valid)
            
            # 计算平均一致性
            consistency_scores = []
            for field_name, validations in field_pass_rates.items():
                pass_rate = sum(validations) / len(validations)
                consistency_scores.append(pass_rate)
            
            return sum(consistency_scores) / len(consistency_scores) if consistency_scores else 0.0
            
        except Exception as e:
            self.logger.warning(f"Error calculating consistency score: {str(e)}")
            return 0.0
    
    async def _calculate_timeliness_score(self, patents: List[Patent]) -> float:
        """计算时效性评分."""
        try:
            if not patents:
                return 0.0
            
            current_year = datetime.now().year
            recent_patents = 0
            
            for patent in patents:
                if patent.application_date:
                    # 近5年的专利认为是较新的
                    if current_year - patent.application_date.year <= 5:
                        recent_patents += 1
            
            return recent_patents / len(patents)
            
        except Exception as e:
            self.logger.warning(f"Error calculating timeliness score: {str(e)}")
            return 0.0
    
    async def _identify_additional_quality_issues(self, quality: PatentDataQuality, validation_result: DatasetValidationResult):
        """识别额外的质量问题."""
        try:
            total_patents = validation_result.total_patents
            
            # 统计字段问题
            field_issues = {}
            for result in validation_result.patent_results:
                for validation in result.field_validations:
                    if not validation.is_valid:
                        field_name = validation.field_name
                        field_issues[field_name] = field_issues.get(field_name, 0) + 1
            
            # 识别普遍性问题
            for field_name, issue_count in field_issues.items():
                if issue_count > total_patents * 0.2:  # 超过20%的专利有此问题
                    quality.issues.append(f"{field_name}字段问题普遍: {issue_count}/{total_patents}个专利受影响")
            
            # 检查严重错误比例
            critical_error_count = sum(1 for r in validation_result.patent_results if r.critical_errors)
            if critical_error_count > total_patents * 0.1:  # 超过10%有严重错误
                quality.issues.append(f"严重错误比例过高: {critical_error_count}/{total_patents}个专利有严重错误")
            
        except Exception as e:
            self.logger.warning(f"Error identifying additional quality issues: {str(e)}")