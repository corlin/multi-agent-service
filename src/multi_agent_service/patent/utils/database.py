"""Patent database integration utilities."""

import asyncio
import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from contextlib import asynccontextmanager
from dataclasses import asdict

from ..models.data import Patent, PatentDataset, PatentDataQuality
from ...utils.monitoring import metrics_collector, measure_performance


class PatentDatabaseManager:
    """专利数据库管理器，集成现有数据库存储机制."""
    
    def __init__(self, db_path: str = "data/patent.db"):
        """初始化数据库管理器."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        self._connection_pool = []
        self._max_connections = 10
        
    async def initialize(self):
        """初始化数据库表结构."""
        try:
            with measure_performance("patent.database.initialize"):
                async with self._get_connection() as conn:
                    await self._create_tables(conn)
                    self.logger.info("Patent database initialized successfully")
                    
                    # 记录监控指标
                    metrics_collector.record_metric(
                        "patent.database.initialization", 
                        1, 
                        tags={"status": "success"}
                    )
                    
        except Exception as e:
            self.logger.error(f"Failed to initialize patent database: {str(e)}")
            metrics_collector.record_metric(
                "patent.database.initialization", 
                1, 
                tags={"status": "error"}
            )
            raise e
    
    @asynccontextmanager
    async def _get_connection(self):
        """获取数据库连接."""
        conn = None
        try:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            yield conn
        except Exception as e:
            self.logger.error(f"Database connection error: {str(e)}")
            raise e
        finally:
            if conn:
                conn.close()
    
    async def _create_tables(self, conn: sqlite3.Connection):
        """创建数据库表."""
        try:
            # 专利表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_number TEXT UNIQUE NOT NULL,
                    title TEXT NOT NULL,
                    abstract TEXT,
                    applicants TEXT NOT NULL,  -- JSON array
                    inventors TEXT NOT NULL,   -- JSON array
                    application_date TEXT NOT NULL,
                    publication_date TEXT,
                    ipc_classes TEXT,          -- JSON array
                    country TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority_date TEXT,
                    grant_date TEXT,
                    family_id TEXT,
                    citations TEXT,            -- JSON array
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 专利数据集表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS patent_datasets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT UNIQUE NOT NULL,
                    total_count INTEGER NOT NULL,
                    search_keywords TEXT NOT NULL,  -- JSON array
                    collection_date TEXT NOT NULL,
                    data_sources TEXT NOT NULL,     -- JSON array
                    quality_score REAL DEFAULT 0.0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 数据质量记录表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS data_quality_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT NOT NULL,
                    completeness_score REAL NOT NULL,
                    accuracy_score REAL NOT NULL,
                    consistency_score REAL NOT NULL,
                    timeliness_score REAL NOT NULL,
                    overall_score REAL NOT NULL,
                    issues TEXT,                    -- JSON array
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dataset_id) REFERENCES patent_datasets(dataset_id)
                )
            """)
            
            # 数据处理统计表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS processing_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT NOT NULL,
                    total_processed INTEGER NOT NULL,
                    standardized_count INTEGER NOT NULL,
                    duplicates_removed INTEGER NOT NULL,
                    invalid_patents_removed INTEGER NOT NULL,
                    quality_issues_fixed INTEGER NOT NULL,
                    processing_duration REAL NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (dataset_id) REFERENCES patent_datasets(dataset_id)
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patents_app_number ON patents(application_number)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patents_country ON patents(country)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_patents_app_date ON patents(application_date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_datasets_collection_date ON patent_datasets(collection_date)")
            
            conn.commit()
            
        except Exception as e:
            conn.rollback()
            raise e
    
    async def save_patent_dataset(self, dataset: PatentDataset, dataset_id: str) -> bool:
        """保存专利数据集."""
        try:
            with measure_performance("patent.database.save_dataset"):
                async with self._get_connection() as conn:
                    # 保存数据集元信息
                    conn.execute("""
                        INSERT OR REPLACE INTO patent_datasets 
                        (dataset_id, total_count, search_keywords, collection_date, data_sources, quality_score)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        dataset_id,
                        dataset.total_count,
                        json.dumps(dataset.search_keywords),
                        dataset.collection_date.isoformat(),
                        json.dumps(dataset.data_sources),
                        dataset.quality_score
                    ))
                    
                    # 保存专利数据
                    for patent in dataset.patents:
                        await self._save_patent(conn, patent)
                    
                    conn.commit()
                    
                    # 记录监控指标
                    metrics_collector.record_metric(
                        "patent.database.dataset_saved", 
                        1, 
                        tags={"dataset_id": dataset_id, "patent_count": str(len(dataset.patents))}
                    )
                    
                    self.logger.info(f"Saved patent dataset {dataset_id} with {len(dataset.patents)} patents")
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to save patent dataset {dataset_id}: {str(e)}")
            metrics_collector.record_metric(
                "patent.database.save_error", 
                1, 
                tags={"dataset_id": dataset_id, "error": str(e)[:50]}
            )
            return False
    
    async def _save_patent(self, conn: sqlite3.Connection, patent: Patent):
        """保存单个专利."""
        try:
            conn.execute("""
                INSERT OR REPLACE INTO patents 
                (application_number, title, abstract, applicants, inventors, 
                 application_date, publication_date, ipc_classes, country, status,
                 priority_date, grant_date, family_id, citations, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                patent.application_number,
                patent.title,
                patent.abstract,
                json.dumps(patent.applicants),
                json.dumps(patent.inventors),
                patent.application_date.isoformat() if patent.application_date else None,
                patent.publication_date.isoformat() if patent.publication_date else None,
                json.dumps(patent.ipc_classes),
                patent.country,
                patent.status,
                patent.priority_date.isoformat() if patent.priority_date else None,
                patent.grant_date.isoformat() if patent.grant_date else None,
                patent.family_id,
                json.dumps(patent.citations),
                datetime.now().isoformat()
            ))
            
        except Exception as e:
            self.logger.warning(f"Failed to save patent {patent.application_number}: {str(e)}")
            raise e
    
    async def load_patent_dataset(self, dataset_id: str) -> Optional[PatentDataset]:
        """加载专利数据集."""
        try:
            with measure_performance("patent.database.load_dataset"):
                async with self._get_connection() as conn:
                    # 加载数据集元信息
                    cursor = conn.execute("""
                        SELECT * FROM patent_datasets WHERE dataset_id = ?
                    """, (dataset_id,))
                    
                    dataset_row = cursor.fetchone()
                    if not dataset_row:
                        return None
                    
                    # 加载专利数据
                    patents = await self._load_patents_for_dataset(conn, dataset_id)
                    
                    dataset = PatentDataset(
                        patents=patents,
                        total_count=dataset_row['total_count'],
                        search_keywords=json.loads(dataset_row['search_keywords']),
                        collection_date=datetime.fromisoformat(dataset_row['collection_date']),
                        data_sources=json.loads(dataset_row['data_sources']),
                        quality_score=dataset_row['quality_score']
                    )
                    
                    # 记录监控指标
                    metrics_collector.record_metric(
                        "patent.database.dataset_loaded", 
                        1, 
                        tags={"dataset_id": dataset_id, "patent_count": str(len(patents))}
                    )
                    
                    return dataset
                    
        except Exception as e:
            self.logger.error(f"Failed to load patent dataset {dataset_id}: {str(e)}")
            metrics_collector.record_metric(
                "patent.database.load_error", 
                1, 
                tags={"dataset_id": dataset_id, "error": str(e)[:50]}
            )
            return None
    
    async def _load_patents_for_dataset(self, conn: sqlite3.Connection, dataset_id: str) -> List[Patent]:
        """加载数据集的专利数据."""
        try:
            # 这里简化处理，实际应该有专利与数据集的关联表
            cursor = conn.execute("""
                SELECT * FROM patents 
                ORDER BY created_at DESC 
                LIMIT 1000
            """)
            
            patents = []
            for row in cursor.fetchall():
                patent = Patent(
                    application_number=row['application_number'],
                    title=row['title'],
                    abstract=row['abstract'] or "",
                    applicants=json.loads(row['applicants']),
                    inventors=json.loads(row['inventors']),
                    application_date=datetime.fromisoformat(row['application_date']) if row['application_date'] else datetime.now(),
                    publication_date=datetime.fromisoformat(row['publication_date']) if row['publication_date'] else None,
                    ipc_classes=json.loads(row['ipc_classes']) if row['ipc_classes'] else [],
                    country=row['country'],
                    status=row['status'],
                    priority_date=datetime.fromisoformat(row['priority_date']) if row['priority_date'] else None,
                    grant_date=datetime.fromisoformat(row['grant_date']) if row['grant_date'] else None,
                    family_id=row['family_id'],
                    citations=json.loads(row['citations']) if row['citations'] else []
                )
                patents.append(patent)
            
            return patents
            
        except Exception as e:
            self.logger.error(f"Failed to load patents for dataset {dataset_id}: {str(e)}")
            return []
    
    async def save_quality_record(self, dataset_id: str, quality: PatentDataQuality) -> bool:
        """保存数据质量记录."""
        try:
            with measure_performance("patent.database.save_quality"):
                async with self._get_connection() as conn:
                    conn.execute("""
                        INSERT INTO data_quality_records 
                        (dataset_id, completeness_score, accuracy_score, consistency_score, 
                         timeliness_score, overall_score, issues)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        dataset_id,
                        quality.completeness_score,
                        quality.accuracy_score,
                        quality.consistency_score,
                        quality.timeliness_score,
                        quality.overall_score,
                        json.dumps(quality.issues)
                    ))
                    
                    conn.commit()
                    
                    # 记录监控指标
                    metrics_collector.record_metric(
                        "patent.database.quality_saved", 
                        1, 
                        tags={"dataset_id": dataset_id, "overall_score": f"{quality.overall_score:.2f}"}
                    )
                    
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to save quality record for dataset {dataset_id}: {str(e)}")
            return False
    
    async def save_processing_stats(self, dataset_id: str, stats: Dict[str, Any], duration: float) -> bool:
        """保存数据处理统计信息."""
        try:
            with measure_performance("patent.database.save_stats"):
                async with self._get_connection() as conn:
                    conn.execute("""
                        INSERT INTO processing_stats 
                        (dataset_id, total_processed, standardized_count, duplicates_removed, 
                         invalid_patents_removed, quality_issues_fixed, processing_duration)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        dataset_id,
                        stats.get('total_processed', 0),
                        stats.get('standardized_count', 0),
                        stats.get('duplicates_removed', 0),
                        stats.get('invalid_patents_removed', 0),
                        stats.get('quality_issues_fixed', 0),
                        duration
                    ))
                    
                    conn.commit()
                    
                    # 记录监控指标
                    metrics_collector.record_metric(
                        "patent.database.stats_saved", 
                        1, 
                        tags={"dataset_id": dataset_id, "duration": f"{duration:.2f}"}
                    )
                    
                    return True
                    
        except Exception as e:
            self.logger.error(f"Failed to save processing stats for dataset {dataset_id}: {str(e)}")
            return False
    
    async def get_quality_history(self, dataset_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取数据质量历史记录."""
        try:
            async with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM data_quality_records 
                    WHERE dataset_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (dataset_id, limit))
                
                records = []
                for row in cursor.fetchall():
                    record = {
                        'id': row['id'],
                        'dataset_id': row['dataset_id'],
                        'completeness_score': row['completeness_score'],
                        'accuracy_score': row['accuracy_score'],
                        'consistency_score': row['consistency_score'],
                        'timeliness_score': row['timeliness_score'],
                        'overall_score': row['overall_score'],
                        'issues': json.loads(row['issues']) if row['issues'] else [],
                        'created_at': row['created_at']
                    }
                    records.append(record)
                
                return records
                
        except Exception as e:
            self.logger.error(f"Failed to get quality history for dataset {dataset_id}: {str(e)}")
            return []
    
    async def get_processing_history(self, dataset_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """获取数据处理历史记录."""
        try:
            async with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT * FROM processing_stats 
                    WHERE dataset_id = ? 
                    ORDER BY created_at DESC 
                    LIMIT ?
                """, (dataset_id, limit))
                
                records = []
                for row in cursor.fetchall():
                    record = {
                        'id': row['id'],
                        'dataset_id': row['dataset_id'],
                        'total_processed': row['total_processed'],
                        'standardized_count': row['standardized_count'],
                        'duplicates_removed': row['duplicates_removed'],
                        'invalid_patents_removed': row['invalid_patents_removed'],
                        'quality_issues_fixed': row['quality_issues_fixed'],
                        'processing_duration': row['processing_duration'],
                        'created_at': row['created_at']
                    }
                    records.append(record)
                
                return records
                
        except Exception as e:
            self.logger.error(f"Failed to get processing history for dataset {dataset_id}: {str(e)}")
            return []
    
    async def cleanup_old_records(self, days: int = 30) -> bool:
        """清理旧记录."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            async with self._get_connection() as conn:
                # 清理旧的质量记录
                cursor = conn.execute("""
                    DELETE FROM data_quality_records 
                    WHERE created_at < ?
                """, (cutoff_date.isoformat(),))
                
                quality_deleted = cursor.rowcount
                
                # 清理旧的处理统计
                cursor = conn.execute("""
                    DELETE FROM processing_stats 
                    WHERE created_at < ?
                """, (cutoff_date.isoformat(),))
                
                stats_deleted = cursor.rowcount
                
                conn.commit()
                
                self.logger.info(f"Cleaned up {quality_deleted} quality records and {stats_deleted} processing stats")
                
                # 记录监控指标
                metrics_collector.record_metric(
                    "patent.database.cleanup", 
                    quality_deleted + stats_deleted, 
                    tags={"days": str(days)}
                )
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to cleanup old records: {str(e)}")
            return False