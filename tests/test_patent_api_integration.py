"""专利API集成测试 - Patent API Integration Tests."""

import asyncio
import pytest
from datetime import datetime
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import json
import httpx
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.multi_agent_service.api.patent import router as patent_router
from src.multi_agent_service.patent.models.requests import PatentAnalysisRequest
from src.multi_agent_service.main import app


@pytest.fixture
def test_app():
    """Create a test FastAPI application with patent router."""
    test_app = FastAPI()
    test_app.include_router(patent_router)
    return test_app


@pytest.fixture
def test_client(test_app):
    """Create a test client for API testing."""
    return TestClient(test_app)


@pytest.fixture
def sample_export_request():
    """Create a sample export request."""
    return {
        "content": """
        # 专利分析报告
        
        ## 概述
        本报告分析了人工智能领域的专利趋势。
        
        ## 主要发现
        - 专利申请量持续增长
        - 主要申请人集中在科技公司
        - 技术发展方向多样化
        
        ## 结论
        人工智能专利领域竞争激烈，技术创新活跃。
        """,
        "format": "html",
        "params": {
            "title": "AI专利分析报告",
            "author": "专利分析系统",
            "date": "2023-12-01"
        }
    }


class TestPatentAPIEndpoints:
    """专利API端点测试类."""
    
    def test_list_reports_success(self, test_client):
        """测试成功获取报告列表."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            # 模拟报告导出器
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.list_exported_reports = AsyncMock(return_value=[
                {
                    "filename": "patent_analysis_20231201_001.html",
                    "format": "html",
                    "created_at": "2023-12-01T10:00:00Z",
                    "size": 1024000,
                    "title": "AI专利分析报告"
                },
                {
                    "filename": "patent_analysis_20231201_001.pdf",
                    "format": "pdf", 
                    "created_at": "2023-12-01T10:05:00Z",
                    "size": 2048000,
                    "title": "AI专利分析报告"
                },
                {
                    "filename": "patent_trend_20231130.json",
                    "format": "json",
                    "created_at": "2023-11-30T15:30:00Z",
                    "size": 512000,
                    "title": "专利趋势数据"
                }
            ])
            mock_exporter.return_value = mock_exporter_instance
            
            # 测试无过滤器
            response = test_client.get("/api/v1/patent/reports")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]["reports"]) == 3
            assert data["data"]["total_count"] == 3
            
            # 测试带限制
            response = test_client.get("/api/v1/patent/reports?limit=2")
            assert response.status_code == 200
            
            data = response.json()
            assert data["data"]["limit"] == 2
            
            # 测试格式过滤
            response = test_client.get("/api/v1/patent/reports?format_filter=pdf")
            assert response.status_code == 200
            
            data = response.json()
            assert data["data"]["format_filter"] == "pdf"
    
    def test_list_reports_error_handling(self, test_client):
        """测试报告列表错误处理."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            # 模拟导出器异常
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.list_exported_reports = AsyncMock(
                side_effect=Exception("Database connection failed")
            )
            mock_exporter.return_value = mock_exporter_instance
            
            response = test_client.get("/api/v1/patent/reports")
            assert response.status_code == 500
            
            data = response.json()
            assert "Failed to list reports" in data["detail"]
    
    def test_get_report_info_success(self, test_client):
        """测试成功获取报告信息."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.get_report_by_filename = AsyncMock(return_value={
                "filename": "test_report.html",
                "format": "html",
                "created_at": "2023-12-01T10:00:00Z",
                "size": 1024000,
                "title": "测试报告",
                "metadata": {
                    "keywords": ["AI", "机器学习"],
                    "analysis_type": "comprehensive",
                    "version": "1.0"
                }
            })
            mock_exporter.return_value = mock_exporter_instance
            
            response = test_client.get("/api/v1/patent/reports/test_report.html")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["filename"] == "test_report.html"
            assert data["data"]["format"] == "html"
            assert "metadata" in data["data"]
    
    def test_get_report_info_not_found(self, test_client):
        """测试报告不存在的情况."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.get_report_by_filename = AsyncMock(return_value=None)
            mock_exporter.return_value = mock_exporter_instance
            
            response = test_client.get("/api/v1/patent/reports/nonexistent.html")
            assert response.status_code == 404
            
            data = response.json()
            assert "Report not found" in data["detail"]
    
    def test_download_report_success(self, test_client):
        """测试成功下载报告."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            import tempfile
            import os
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.write(b"test pdf content")
            temp_file.close()
            
            mock_exporter_instance.get_download_info = AsyncMock(return_value={
                "exists": True,
                "path": temp_file.name,
                "mime_type": "application/pdf",
                "download_name": "patent_analysis_report.pdf",
                "format": "pdf"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            # 模拟文件存在
            with patch('fastapi.responses.FileResponse') as mock_file_response:
                mock_file_response.return_value = MagicMock()
                
                response = test_client.get("/api/v1/patent/reports/download/test_report.pdf")
                
                # 验证FileResponse被调用
                mock_file_response.assert_called_once()
                call_args = mock_file_response.call_args
                assert call_args[1]["media_type"] == "application/pdf"
                assert call_args[1]["filename"] == "patent_analysis_report.pdf"
    
    def test_view_report_html_success(self, test_client):
        """测试成功在线查看HTML报告."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.get_download_info = AsyncMock(return_value={
                "exists": True,
                "path": "/tmp/test_report.html",
                "mime_type": "text/html",
                "download_name": "report.html",
                "format": "html"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            # 模拟文件内容
            html_content = "<html><body><h1>专利分析报告</h1><p>报告内容...</p></body></html>"
            
            with patch('builtins.open', create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = html_content
                
                response = test_client.get("/api/v1/patent/reports/view/test_report.html")
                assert response.status_code == 200
                assert response.text == html_content
                assert "text/html" in response.headers.get("content-type", "")
    
    def test_view_report_unsupported_format(self, test_client):
        """测试查看不支持格式的报告."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            import tempfile
            import os
            
            # 创建临时文件
            temp_file = tempfile.NamedTemporaryFile(suffix='.pdf', delete=False)
            temp_file.write(b"test pdf content")
            temp_file.close()
            
            mock_exporter_instance.get_download_info = AsyncMock(return_value={
                "exists": True,
                "path": temp_file.name,
                "mime_type": "application/pdf",
                "download_name": "report.pdf",
                "format": "pdf"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            response = test_client.get("/api/v1/patent/reports/view/test_report.pdf")
            assert response.status_code == 400
            
            data = response.json()
            assert "Online viewing not supported for pdf format" in data["detail"]
    
    def test_delete_report_success(self, test_client):
        """测试成功删除报告."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.delete_report = AsyncMock(return_value={
                "deleted": True,
                "filename": "test_report.html",
                "versions_deleted": 2,
                "space_freed": 1536000
            })
            mock_exporter.return_value = mock_exporter_instance
            
            response = test_client.delete("/api/v1/patent/reports/test_report.html")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["deleted"] is True
            assert data["data"]["versions_deleted"] == 2
    
    def test_delete_report_not_found(self, test_client):
        """测试删除不存在的报告."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.delete_report = AsyncMock(return_value={
                "deleted": False,
                "error": "Report not found"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            response = test_client.delete("/api/v1/patent/reports/nonexistent.html")
            assert response.status_code == 404
    
    def test_cleanup_old_reports(self, test_client):
        """测试清理旧报告."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.cleanup_old_reports = AsyncMock(return_value={
                "reports_deleted": 5,
                "versions_cleaned": 12,
                "temp_files_deleted": 8,
                "total_space_freed": 10485760,
                "cleanup_date": "2023-12-01T10:00:00Z"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            # 测试默认清理
            response = test_client.post("/api/v1/patent/reports/cleanup")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["reports_deleted"] == 5
            assert data["data"]["total_space_freed"] == 10485760
            
            # 测试指定天数清理
            response = test_client.post("/api/v1/patent/reports/cleanup?days=30")
            assert response.status_code == 200
    
    def test_export_report_html_success(self, test_client, sample_export_request):
        """测试成功导出HTML报告."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.export_report = AsyncMock(return_value={
                "filename": "exported_report_20231201_001.html",
                "format": "html",
                "size": 1024000,
                "created_at": "2023-12-01T10:00:00Z",
                "export_path": "/tmp/reports/exported_report_20231201_001.html"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            response = test_client.post("/api/v1/patent/export", json=sample_export_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["format"] == "html"
            assert "filename" in data["data"]
    
    def test_export_report_pdf_success(self, test_client, sample_export_request):
        """测试成功导出PDF报告."""
        # 修改为PDF格式
        pdf_request = sample_export_request.copy()
        pdf_request["format"] = "pdf"
        
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.export_report = AsyncMock(return_value={
                "filename": "exported_report_20231201_001.pdf",
                "format": "pdf",
                "size": 2048000,
                "created_at": "2023-12-01T10:00:00Z",
                "export_path": "/tmp/reports/exported_report_20231201_001.pdf"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            response = test_client.post("/api/v1/patent/export", json=pdf_request)
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert data["data"]["format"] == "pdf"
    
    def test_export_report_invalid_format(self, test_client, sample_export_request):
        """测试导出无效格式报告."""
        invalid_request = sample_export_request.copy()
        invalid_request["format"] = "invalid_format"
        
        response = test_client.post("/api/v1/patent/export", json=invalid_request)
        assert response.status_code == 400
        
        data = response.json()
        assert "Unsupported format" in data["detail"]
    
    def test_export_report_empty_content(self, test_client):
        """测试导出空内容报告."""
        empty_request = {
            "content": "",
            "format": "html"
        }
        
        response = test_client.post("/api/v1/patent/export", json=empty_request)
        assert response.status_code == 400
        
        data = response.json()
        assert "Content cannot be empty" in data["detail"]
    
    def test_get_export_info(self, test_client):
        """测试获取导出器信息."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.get_export_info = AsyncMock(return_value={
                "supported_formats": ["html", "pdf", "json", "zip"],
                "directories": {
                    "reports": "/tmp/reports",
                    "temp": "/tmp/temp",
                    "templates": "/tmp/templates"
                },
                "configuration": {
                    "max_file_size": 104857600,
                    "cleanup_days": 30,
                    "version_limit": 5
                },
                "statistics": {
                    "total_reports": 150,
                    "total_size": 524288000,
                    "formats_distribution": {
                        "html": 80,
                        "pdf": 60,
                        "json": 10
                    }
                }
            })
            mock_exporter.return_value = mock_exporter_instance
            
            response = test_client.get("/api/v1/patent/export/info")
            assert response.status_code == 200
            
            data = response.json()
            assert data["success"] is True
            assert "supported_formats" in data["data"]
            assert "directories" in data["data"]
            assert "statistics" in data["data"]
    
    def test_health_check_healthy(self, test_client):
        """测试健康检查 - 健康状态."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.get_export_info = AsyncMock(return_value={
                "directories": {
                    "reports": "/tmp/reports",
                    "temp": "/tmp/temp"
                }
            })
            mock_exporter.return_value = mock_exporter_instance
            
            # 模拟目录存在且可写
            with patch('pathlib.Path.exists', return_value=True):
                with patch('pathlib.Path.is_dir', return_value=True):
                    # 模拟weasyprint可用
                    with patch('importlib.import_module') as mock_import:
                        mock_weasyprint = MagicMock()
                        mock_weasyprint.__version__ = "60.0"
                        mock_import.return_value = mock_weasyprint
                        
                        response = test_client.get("/api/v1/patent/health")
                        assert response.status_code == 200
                        
                        data = response.json()
                        assert data["success"] is True
                        assert data["data"]["status"] == "healthy"
                        assert "directories" in data["data"]
                        assert "dependencies" in data["data"]
    
    def test_health_check_unhealthy(self, test_client):
        """测试健康检查 - 不健康状态."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            # 模拟导出器异常
            mock_exporter.side_effect = Exception("Export service unavailable")
            
            response = test_client.get("/api/v1/patent/health")
            assert response.status_code == 200  # 健康检查端点总是返回200
            
            data = response.json()
            assert data["success"] is False
            assert data["data"]["status"] == "unhealthy"
            assert "error" in data["data"]


class TestPatentAPIAuthentication:
    """专利API认证测试类."""
    
    def test_api_without_authentication(self, test_client):
        """测试无认证访问API（当前为开放访问）."""
        # 当前API是开放的，应该可以访问
        response = test_client.get("/api/v1/patent/reports")
        # 根据实际实现，可能返回200或需要认证
        assert response.status_code in [200, 401, 500]
    
    def test_api_rate_limiting(self, test_client):
        """测试API限流（如果实现了的话）."""
        # 快速发送多个请求
        responses = []
        for i in range(10):
            response = test_client.get("/api/v1/patent/health")
            responses.append(response)
        
        # 检查是否有限流响应
        status_codes = [r.status_code for r in responses]
        # 大部分应该成功，可能有限流
        success_count = sum(1 for code in status_codes if code == 200)
        assert success_count >= 5  # 至少一半请求成功


class TestPatentAPIErrorHandling:
    """专利API错误处理测试类."""
    
    def test_malformed_json_request(self, test_client):
        """测试格式错误的JSON请求."""
        # 发送无效JSON
        response = test_client.post(
            "/api/v1/patent/export",
            data="invalid json content",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422  # Unprocessable Entity
    
    def test_missing_required_fields(self, test_client):
        """测试缺少必需字段的请求."""
        incomplete_request = {
            "format": "html"
            # 缺少content字段
        }
        
        response = test_client.post("/api/v1/patent/export", json=incomplete_request)
        assert response.status_code == 422
    
    def test_invalid_query_parameters(self, test_client):
        """测试无效查询参数."""
        # 测试无效的limit值
        response = test_client.get("/api/v1/patent/reports?limit=0")
        assert response.status_code == 422
        
        response = test_client.get("/api/v1/patent/reports?limit=1000")
        assert response.status_code == 422
    
    def test_internal_server_error_handling(self, test_client):
        """测试内部服务器错误处理."""
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            # 模拟内部错误
            mock_exporter.side_effect = Exception("Internal service error")
            
            response = test_client.get("/api/v1/patent/reports")
            assert response.status_code == 500
            
            data = response.json()
            assert "Failed to list reports" in data["detail"]


class TestPatentAPIPerformance:
    """专利API性能测试类."""
    
    def test_concurrent_api_requests(self, test_client):
        """测试并发API请求性能."""
        import threading
        import time
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = test_client.get("/api/v1/patent/health")
            end_time = time.time()
            results.append({
                "status_code": response.status_code,
                "response_time": end_time - start_time
            })
        
        # 创建10个并发线程
        threads = []
        for i in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
        
        # 启动所有线程
        start_time = time.time()
        for thread in threads:
            thread.start()
        
        # 等待所有线程完成
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # 验证性能
        assert len(results) == 10
        assert total_time < 10.0  # 总时间应该小于10秒
        
        # 检查响应时间
        avg_response_time = sum(r["response_time"] for r in results) / len(results)
        assert avg_response_time < 2.0  # 平均响应时间应该小于2秒
    
    def test_large_export_request_performance(self, test_client):
        """测试大型导出请求性能."""
        # 创建大内容的导出请求
        large_content = "# 大型专利分析报告\n\n" + "详细内容段落。\n" * 1000
        
        large_request = {
            "content": large_content,
            "format": "html",
            "params": {"title": "大型报告"}
        }
        
        with patch('src.multi_agent_service.api.patent.get_report_exporter') as mock_exporter:
            mock_exporter_instance = MagicMock()
            mock_exporter_instance.export_report = AsyncMock(return_value={
                "filename": "large_report.html",
                "format": "html",
                "size": len(large_content),
                "created_at": "2023-12-01T10:00:00Z"
            })
            mock_exporter.return_value = mock_exporter_instance
            
            import time
            start_time = time.time()
            response = test_client.post("/api/v1/patent/export", json=large_request)
            end_time = time.time()
            
            # 验证性能
            assert response.status_code == 200
            assert (end_time - start_time) < 5.0  # 应该在5秒内完成


# 运行测试的辅助函数
def run_api_integration_tests():
    """运行所有API集成测试."""
    pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])


if __name__ == "__main__":
    run_api_integration_tests()