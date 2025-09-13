#!/usr/bin/env python3
"""参考 google_patent_scraper 的方法访问 Google Patents."""

import asyncio
import logging
import requests
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import re
from urllib.parse import quote_plus, urljoin
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GooglePatentsScraper:
    """基于 google_patent_scraper 方法的 Google Patents 访问器."""
    
    def __init__(self):
        self.base_url = "https://patents.google.com"
        self.session = requests.Session()
        
        # 设置请求头，模拟真实浏览器
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def search_patents(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """搜索专利."""
        try:
            logger.info(f"搜索专利: {query}")
            
            # 构造搜索URL
            search_url = f"{self.base_url}/?q={quote_plus(query)}"
            logger.info(f"搜索URL: {search_url}")
            
            # 发送请求
            response = self.session.get(search_url, timeout=30)
            response.raise_for_status()
            
            logger.info(f"响应状态码: {response.status_code}")
            logger.info(f"响应内容长度: {len(response.text)}")
            
            # 解析搜索结果
            patents = self._parse_search_results(response.text, num_results)
            
            logger.info(f"找到 {len(patents)} 个专利")
            return patents
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    def _parse_search_results(self, html_content: str, num_results: int) -> List[Dict[str, Any]]:
        """解析搜索结果页面."""
        patents = []
        
        try:
            # 查找专利链接模式
            patent_link_pattern = r'href="(/patent/[^"]+)"'
            patent_links = re.findall(patent_link_pattern, html_content)
            
            logger.info(f"找到 {len(patent_links)} 个专利链接")
            
            # 查找专利标题模式
            title_pattern = r'<h3[^>]*>([^<]+)</h3>'
            titles = re.findall(title_pattern, html_content)
            
            logger.info(f"找到 {len(titles)} 个标题")
            
            # 组合结果
            for i, link in enumerate(patent_links[:num_results]):
                patent = {
                    "patent_url": urljoin(self.base_url, link),
                    "patent_id": self._extract_patent_id_from_url(link),
                    "title": titles[i] if i < len(titles) else "未知标题",
                    "source": "google_patents_scraper",
                    "collected_at": datetime.now().isoformat()
                }
                
                # 尝试获取更多详细信息
                try:
                    patent_details = self.get_patent_details(patent["patent_url"])
                    patent.update(patent_details)
                except Exception as e:
                    logger.warning(f"获取专利详情失败: {e}")
                
                patents.append(patent)
                
                # 添加延迟避免被限制
                time.sleep(1)
            
            return patents
            
        except Exception as e:
            logger.error(f"解析搜索结果失败: {e}")
            return []
    
    def _extract_patent_id_from_url(self, url: str) -> str:
        """从URL中提取专利ID."""
        match = re.search(r'/patent/([^/\?]+)', url)
        return match.group(1) if match else "未知ID"
    
    def get_patent_details(self, patent_url: str) -> Dict[str, Any]:
        """获取专利详细信息."""
        try:
            logger.info(f"获取专利详情: {patent_url}")
            
            response = self.session.get(patent_url, timeout=30)
            response.raise_for_status()
            
            return self._parse_patent_details(response.text)
            
        except Exception as e:
            logger.error(f"获取专利详情失败: {e}")
            return {}
    
    def _parse_patent_details(self, html_content: str) -> Dict[str, Any]:
        """解析专利详情页面."""
        details = {}
        
        try:
            # 提取专利号
            patent_number_pattern = r'<span[^>]*>([A-Z]{2}\d+[A-Z]\d*)</span>'
            patent_number_match = re.search(patent_number_pattern, html_content)
            if patent_number_match:
                details["patent_number"] = patent_number_match.group(1)
            
            # 提取标题
            title_pattern = r'<h1[^>]*>([^<]+)</h1>'
            title_match = re.search(title_pattern, html_content)
            if title_match:
                details["title"] = title_match.group(1).strip()
            
            # 提取摘要
            abstract_pattern = r'<div[^>]*abstract[^>]*>([^<]+)</div>'
            abstract_match = re.search(abstract_pattern, html_content, re.IGNORECASE)
            if abstract_match:
                details["abstract"] = abstract_match.group(1).strip()
            
            # 提取申请人
            assignee_pattern = r'<dd[^>]*>([^<]+)</dd>'
            assignee_matches = re.findall(assignee_pattern, html_content)
            if assignee_matches:
                details["applicants"] = [match.strip() for match in assignee_matches[:3]]
            
            # 提取发布日期
            date_pattern = r'(\d{4}-\d{2}-\d{2})'
            date_match = re.search(date_pattern, html_content)
            if date_match:
                details["publication_date"] = date_match.group(1)
            
            return details
            
        except Exception as e:
            logger.error(f"解析专利详情失败: {e}")
            return {}


async def test_google_patents_scraper():
    """测试 Google Patents 爬虫."""
    logger.info("测试 Google Patents 爬虫...")
    
    scraper = GooglePatentsScraper()
    
    # 测试查询
    test_queries = [
        "artificial intelligence",
        "machine learning",
        "blockchain"
    ]
    
    all_results = {}
    
    for query in test_queries:
        logger.info(f"\n--- 测试查询: {query} ---")
        
        patents = scraper.search_patents(query, num_results=3)
        all_results[query] = patents
        
        if patents:
            logger.info(f"✓ 找到 {len(patents)} 个专利")
            for i, patent in enumerate(patents, 1):
                logger.info(f"\n专利 {i}:")
                logger.info(f"  ID: {patent.get('patent_id', 'N/A')}")
                logger.info(f"  标题: {patent.get('title', 'N/A')}")
                logger.info(f"  专利号: {patent.get('patent_number', 'N/A')}")
                logger.info(f"  URL: {patent.get('patent_url', 'N/A')}")
                if patent.get('applicants'):
                    logger.info(f"  申请人: {', '.join(patent['applicants'])}")
                if patent.get('abstract'):
                    logger.info(f"  摘要: {patent['abstract'][:100]}...")
        else:
            logger.warning(f"✗ 未找到 '{query}' 相关专利")
        
        # 查询间隔
        await asyncio.sleep(2)
    
    # 保存结果
    result_file = f"google_patents_scraper_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        logger.info(f"\n结果已保存到: {result_file}")
    except Exception as e:
        logger.error(f"保存结果失败: {e}")
    
    # 统计
    total_patents = sum(len(patents) for patents in all_results.values())
    successful_queries = sum(1 for patents in all_results.values() if patents)
    
    logger.info(f"\n=== 测试统计 ===")
    logger.info(f"总查询数: {len(test_queries)}")
    logger.info(f"成功查询: {successful_queries}")
    logger.info(f"总专利数: {total_patents}")
    logger.info(f"成功率: {successful_queries/len(test_queries)*100:.1f}%")
    
    return successful_queries > 0


async def main():
    """主测试函数."""
    logger.info("=== Google Patents Scraper 方法测试 ===")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    success = await test_google_patents_scraper()
    
    if success:
        logger.info("\n🎉 Google Patents 爬虫方法测试成功!")
        return 0
    else:
        logger.error("\n❌ Google Patents 爬虫方法测试失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)