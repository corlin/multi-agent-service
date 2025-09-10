"""专利数据库存储机制."""

import asyncio
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import json
import aiosqlite

from ..models.patent_data import PatentData, PatentDataset, DataQualityReport
from ...utils.monitoring import metrics_collector


logger = logging.getLogger(__name__)


class PatentDatabaseManager:
    """专利数据库管理器."""
    
    def __init__(self, db_path: str = "data/patent_database.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection_pool = None
        
    async def initialize(self) -> bool:
        """初始化数据库."""
        try:
            logger.info(f"Initializing patent database at {self.db_path}")
            
            # 创建数据库表
            await self._create_tables()
            
            logger.info("Patent database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            return False
    
    async def _create_tables(self):
        """创建数据库表."""
        async with aiosqlite.connect(self.db_path) as db:
            # 专利数据表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS patents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patent_id TEXT UNIQUE NOT NULL,
                    application_number TEXT NOT NULL,
                    publication_number TEXT,
                    title TEXT NOT NULL,
                    abstract TEXT NOT NULL,
                    application_date TEXT NOT NULL,
                    publication_date TEXT,
                    grant_date TEXT,
                    country TEXT NOT NULL,
                    status TEXT NOT NULL,
                    legal_status TEXT,
                    technical_field TEXT,
                    data_source TEXT NOT NULL,
                    data_quality_score REAL DEFAULT 0.0,
                    collection_timestamp TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    similarity_hash TEXT NOT NULL,
                    keywords TEXT,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 申请人表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS patent_applicants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    country TEXT,
                    applicant_type TEXT,
                    FOREIGN KEY (patent_id) REFERENCES patents (patent_id)
                )
            """)
            
            # 发明人表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS patent_inventors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    normalized_name TEXT NOT NULL,
                    country TEXT,
                    FOREIGN KEY (patent_id) REFERENCES patents (patent_id)
                )
            """)
            
            # 分类表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS patent_classifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    patent_id TEXT NOT NULL,
                    ipc_class TEXT,
                    cpc_class TEXT,
                    national_class TEXT,
                    FOREIGN KEY (patent_id) REFERENCES patents (patent_id)
                )
            """)
            
            # 数据集表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS patent_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT UNIQUE NOT NULL,
                    total_count INTEGER DEFAULT 0,
                    search_keywords TEXT,
                    collection_date TEXT NOT NULL,
                    data_sources TEXT,
                    quality_metrics TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 数据集-专利关联表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS dataset_patents (
                    dataset_id TEXT NOT NULL,
                    patent_id TEXT NOT NULL,
                    PRIMARY KEY (dataset_id, patent_id),
                    FOREIGN KEY (dataset_id) REFERENCES patent_datasets (dataset_id),
                    FOREIGN KEY (patent_id) REFERENCES patents (patent_id)
                )
            """)
            
            # 质量报告表
            await db.execute("""
                CREATE TABLE IF NOT EXISTS quality_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    dataset_id TEXT NOT NULL,
                    total_records INTEGER NOT NULL,
                    valid_records INTEGER NOT NULL,
                    invalid_records INTEGER NOT NULL,
                    duplicate_records INTEGER DEFAULT 0,
                    quality_score REAL NOT NULL,
                    completeness_score REAL NOT NULL,
                    accuracy_score REAL NOT NULL,
                    consistency_score REAL NOT NULL,
                    missing_fields TEXT,
                    invalid_formats TEXT,
                    data_anomalies TEXT,
                    recommendations TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            await db.execute("CREATE INDEX IF NOT EXISTS idx_patents_application_number ON patents (application_number)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_patents_content_hash ON patents (content_hash)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_patents_similarity_hash ON patents (similarity_hash)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_patents_country ON patents (country)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_patents_status ON patents (status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_patents_data_source ON patents (data_source)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_applicants_normalized_name ON patent_applicants (normalized_name)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_inventors_normalized_name ON patent_inventors (normalized_name)")
            
            await db.commit()
    
    async def save_patent(self, patent: PatentData) -> bool:
        """保存专利数据."""
        start_time = datetime.now()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 检查是否已存在
                cursor = await db.execute(
                    "SELECT id FROM patents WHERE patent_id = ?",
                    (patent.patent_id,)
                )
                existing = await cursor.fetchone()
                
                if existing:
                    # 更新现有记录
                    await self._update_patent(db, patent)
                    logger.debug(f"Updated patent {patent.patent_id}")
                else:
                    # 插入新记录
                    await self._insert_patent(db, patent)
                    logger.debug(f"Inserted patent {patent.patent_id}")
                
                await db.commit()
                
                # 记录监控指标
                processing_time = (datetime.now() - start_time).total_seconds()
                metrics_collector.record_metric(
                    "patent.database_save_duration",
                    processing_time,
                    tags={"unit": "seconds", "operation": "save_patent"}
                )
                
                return True
                
        except Exception as e:
            logger.error(f"Error saving patent {patent.patent_id}: {str(e)}")
            return False
    
    async def _insert_patent(self, db: aiosqlite.Connection, patent: PatentData):
        """插入专利数据."""
        # 插入主表
        await db.execute("""
            INSERT INTO patents (
                patent_id, application_number, publication_number, title, abstract,
                application_date, publication_date, grant_date, country, status,
                legal_status, technical_field, data_source, data_quality_score,
                collection_timestamp, content_hash, similarity_hash, keywords, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            patent.patent_id,
            patent.application_number,
            patent.publication_number,
            patent.title,
            patent.abstract,
            patent.application_date.isoformat(),
            patent.publication_date.isoformat() if patent.publication_date else None,
            patent.grant_date.isoformat() if patent.grant_date else None,
            patent.country,
            patent.status,
            patent.legal_status,
            patent.technical_field,
            patent.data_source,
            patent.data_quality_score,
            patent.collection_timestamp.isoformat(),
            patent.content_hash,
            patent.similarity_hash,
            json.dumps(patent.keywords),
            json.dumps(patent.metadata)
        ))
        
        # 插入申请人
        for applicant in patent.applicants:
            await db.execute("""
                INSERT INTO patent_applicants (
                    patent_id, name, normalized_name, country, applicant_type
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                patent.patent_id,
                applicant.name,
                applicant.normalized_name,
                applicant.country,
                applicant.applicant_type
            ))
        
        # 插入发明人
        for inventor in patent.inventors:
            await db.execute("""
                INSERT INTO patent_inventors (
                    patent_id, name, normalized_name, country
                ) VALUES (?, ?, ?, ?)
            """, (
                patent.patent_id,
                inventor.name,
                inventor.normalized_name,
                inventor.country
            ))
        
        # 插入分类
        for classification in patent.classifications:
            await db.execute("""
                INSERT INTO patent_classifications (
                    patent_id, ipc_class, cpc_class, national_class
                ) VALUES (?, ?, ?, ?)
            """, (
                patent.patent_id,
                classification.ipc_class,
                classification.cpc_class,
                classification.national_class
            ))
    
    async def _update_patent(self, db: aiosqlite.Connection, patent: PatentData):
        """更新专利数据."""
        # 更新主表
        await db.execute("""
            UPDATE patents SET
                application_number = ?, publication_number = ?, title = ?, abstract = ?,
                application_date = ?, publication_date = ?, grant_date = ?, country = ?,
                status = ?, legal_status = ?, technical_field = ?, data_source = ?,
                data_quality_score = ?, collection_timestamp = ?, content_hash = ?,
                similarity_hash = ?, keywords = ?, metadata = ?, updated_at = CURRENT_TIMESTAMP
            WHERE patent_id = ?
        """, (
            patent.application_number,
            patent.publication_number,
            patent.title,
            patent.abstract,
            patent.application_date.isoformat(),
            patent.publication_date.isoformat() if patent.publication_date else None,
            patent.grant_date.isoformat() if patent.grant_date else None,
            patent.country,
            patent.status,
            patent.legal_status,
            patent.technical_field,
            patent.data_source,
            patent.data_quality_score,
            patent.collection_timestamp.isoformat(),
            patent.content_hash,
            patent.similarity_hash,
            json.dumps(patent.keywords),
            json.dumps(patent.metadata),
            patent.patent_id
        ))
        
        # 删除旧的关联数据
        await db.execute("DELETE FROM patent_applicants WHERE patent_id = ?", (patent.patent_id,))
        await db.execute("DELETE FROM patent_inventors WHERE patent_id = ?", (patent.patent_id,))
        await db.execute("DELETE FROM patent_classifications WHERE patent_id = ?", (patent.patent_id,))
        
        # 重新插入关联数据
        for applicant in patent.applicants:
            await db.execute("""
                INSERT INTO patent_applicants (
                    patent_id, name, normalized_name, country, applicant_type
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                patent.patent_id,
                applicant.name,
                applicant.normalized_name,
                applicant.country,
                applicant.applicant_type
            ))
        
        for inventor in patent.inventors:
            await db.execute("""
                INSERT INTO patent_inventors (
                    patent_id, name, normalized_name, country
                ) VALUES (?, ?, ?, ?)
            """, (
                patent.patent_id,
                inventor.name,
                inventor.normalized_name,
                inventor.country
            ))
        
        for classification in patent.classifications:
            await db.execute("""
                INSERT INTO patent_classifications (
                    patent_id, ipc_class, cpc_class, national_class
                ) VALUES (?, ?, ?, ?)
            """, (
                patent.patent_id,
                classification.ipc_class,
                classification.cpc_class,
                classification.national_class
            ))
    
    async def save_dataset(self, dataset: PatentDataset) -> bool:
        """保存专利数据集."""
        start_time = datetime.now()
        
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 保存数据集信息
                await db.execute("""
                    INSERT OR REPLACE INTO patent_datasets (
                        dataset_id, total_count, search_keywords, collection_date,
                        data_sources, quality_metrics
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    dataset.dataset_id,
                    dataset.total_count,
                    json.dumps(dataset.search_keywords),
                    dataset.collection_date.isoformat(),
                    json.dumps(dataset.data_sources),
                    json.dumps(dataset.quality_metrics)
                ))
                
                # 删除旧的关联关系
                await db.execute("DELETE FROM dataset_patents WHERE dataset_id = ?", (dataset.dataset_id,))
                
                # 保存每个专利并建立关联
                for patent in dataset.patents:
                    await self._insert_or_update_patent(db, patent)
                    
                    # 建立数据集-专利关联
                    await db.execute("""
                        INSERT INTO dataset_patents (dataset_id, patent_id)
                        VALUES (?, ?)
                    """, (dataset.dataset_id, patent.patent_id))
                
                await db.commit()
                
                # 记录监控指标
                processing_time = (datetime.now() - start_time).total_seconds()
                metrics_collector.record_metric(
                    "patent.database_save_duration",
                    processing_time,
                    tags={"unit": "seconds", "operation": "save_dataset", "patent_count": str(len(dataset.patents))}
                )
                
                logger.info(f"Saved dataset {dataset.dataset_id} with {len(dataset.patents)} patents")
                return True
                
        except Exception as e:
            logger.error(f"Error saving dataset {dataset.dataset_id}: {str(e)}")
            return False
    
    async def _insert_or_update_patent(self, db: aiosqlite.Connection, patent: PatentData):
        """插入或更新专利数据."""
        cursor = await db.execute(
            "SELECT id FROM patents WHERE patent_id = ?",
            (patent.patent_id,)
        )
        existing = await cursor.fetchone()
        
        if existing:
            await self._update_patent(db, patent)
        else:
            await self._insert_patent(db, patent)
    
    async def get_patent(self, patent_id: str) -> Optional[PatentData]:
        """获取专利数据."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                # 获取主要信息
                cursor = await db.execute("""
                    SELECT * FROM patents WHERE patent_id = ?
                """, (patent_id,))
                patent_row = await cursor.fetchone()
                
                if not patent_row:
                    return None
                
                # 获取申请人
                cursor = await db.execute("""
                    SELECT * FROM patent_applicants WHERE patent_id = ?
                """, (patent_id,))
                applicant_rows = await cursor.fetchall()
                
                # 获取发明人
                cursor = await db.execute("""
                    SELECT * FROM patent_inventors WHERE patent_id = ?
                """, (patent_id,))
                inventor_rows = await cursor.fetchall()
                
                # 获取分类
                cursor = await db.execute("""
                    SELECT * FROM patent_classifications WHERE patent_id = ?
                """, (patent_id,))
                classification_rows = await cursor.fetchall()
                
                # 构建PatentData对象
                patent_data = self._build_patent_from_rows(
                    patent_row, applicant_rows, inventor_rows, classification_rows
                )
                
                return patent_data
                
        except Exception as e:
            logger.error(f"Error getting patent {patent_id}: {str(e)}")
            return None
    
    def _build_patent_from_rows(self, patent_row, applicant_rows, inventor_rows, classification_rows) -> PatentData:
        """从数据库行构建PatentData对象."""
        from ..models.patent_data import PatentApplicant, PatentInventor, PatentClassification
        
        # 构建申请人列表
        applicants = []
        for row in applicant_rows:
            applicants.append(PatentApplicant(
                name=row['name'],
                normalized_name=row['normalized_name'],
                country=row['country'],
                applicant_type=row['applicant_type']
            ))
        
        # 构建发明人列表
        inventors = []
        for row in inventor_rows:
            inventors.append(PatentInventor(
                name=row['name'],
                normalized_name=row['normalized_name'],
                country=row['country']
            ))
        
        # 构建分类列表
        classifications = []
        for row in classification_rows:
            classifications.append(PatentClassification(
                ipc_class=row['ipc_class'],
                cpc_class=row['cpc_class'],
                national_class=row['national_class']
            ))
        
        # 构建PatentData对象
        patent_data = PatentData(
            patent_id=patent_row['patent_id'],
            application_number=patent_row['application_number'],
            publication_number=patent_row['publication_number'],
            title=patent_row['title'],
            abstract=patent_row['abstract'],
            applicants=applicants,
            inventors=inventors,
            application_date=datetime.fromisoformat(patent_row['application_date']),
            publication_date=datetime.fromisoformat(patent_row['publication_date']) if patent_row['publication_date'] else None,
            grant_date=datetime.fromisoformat(patent_row['grant_date']) if patent_row['grant_date'] else None,
            classifications=classifications,
            country=patent_row['country'],
            priority_countries=[],
            status=patent_row['status'],
            legal_status=patent_row['legal_status'],
            technical_field=patent_row['technical_field'],
            keywords=json.loads(patent_row['keywords']) if patent_row['keywords'] else [],
            data_source=patent_row['data_source'],
            data_quality_score=patent_row['data_quality_score'],
            collection_timestamp=datetime.fromisoformat(patent_row['collection_timestamp']),
            metadata=json.loads(patent_row['metadata']) if patent_row['metadata'] else {}
        )
        
        return patent_data
    
    async def save_quality_report(self, report: DataQualityReport) -> bool:
        """保存质量报告."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO quality_reports (
                        report_id, dataset_id, total_records, valid_records, invalid_records,
                        duplicate_records, quality_score, completeness_score, accuracy_score,
                        consistency_score, missing_fields, invalid_formats, data_anomalies,
                        recommendations
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    report.report_id,
                    report.dataset_id,
                    report.total_records,
                    report.valid_records,
                    report.invalid_records,
                    report.duplicate_records,
                    report.quality_score,
                    report.completeness_score,
                    report.accuracy_score,
                    report.consistency_score,
                    json.dumps(report.missing_fields),
                    json.dumps(report.invalid_formats),
                    json.dumps(report.data_anomalies),
                    json.dumps(report.recommendations)
                ))
                
                await db.commit()
                logger.info(f"Saved quality report {report.report_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error saving quality report {report.report_id}: {str(e)}")
            return False
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                stats = {}
                
                # 专利总数
                cursor = await db.execute("SELECT COUNT(*) FROM patents")
                stats['total_patents'] = (await cursor.fetchone())[0]
                
                # 数据集总数
                cursor = await db.execute("SELECT COUNT(*) FROM patent_datasets")
                stats['total_datasets'] = (await cursor.fetchone())[0]
                
                # 质量报告总数
                cursor = await db.execute("SELECT COUNT(*) FROM quality_reports")
                stats['total_quality_reports'] = (await cursor.fetchone())[0]
                
                # 按国家统计
                cursor = await db.execute("""
                    SELECT country, COUNT(*) as count 
                    FROM patents 
                    GROUP BY country 
                    ORDER BY count DESC 
                    LIMIT 10
                """)
                stats['patents_by_country'] = dict(await cursor.fetchall())
                
                # 按状态统计
                cursor = await db.execute("""
                    SELECT status, COUNT(*) as count 
                    FROM patents 
                    GROUP BY status 
                    ORDER BY count DESC
                """)
                stats['patents_by_status'] = dict(await cursor.fetchall())
                
                # 按数据源统计
                cursor = await db.execute("""
                    SELECT data_source, COUNT(*) as count 
                    FROM patents 
                    GROUP BY data_source 
                    ORDER BY count DESC
                """)
                stats['patents_by_source'] = dict(await cursor.fetchall())
                
                # 平均质量评分
                cursor = await db.execute("SELECT AVG(data_quality_score) FROM patents")
                avg_score = (await cursor.fetchone())[0]
                stats['average_quality_score'] = round(avg_score, 3) if avg_score else 0.0
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}
    
    async def cleanup(self):
        """清理数据库连接."""
        # 如果有连接池，在这里清理
        pass