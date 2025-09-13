#!/usr/bin/env python3
"""优化的 Google Patents 访问 - 模拟真实人类行为."""

import asyncio
import logging
import random
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class HumanBehaviorSimulator:
    """人类行为模拟器."""
    
    @staticmethod
    async def random_delay(min_seconds: float = 1.0, max_seconds: float = 3.0):
        """随机延迟，模拟人类思考时间."""
        delay = random.uniform(min_seconds, max_seconds)
        await asyncio.sleep(delay)
    
    @staticmethod
    async def human_type(page, selector: str, text: str):
        """模拟人类打字行为."""
        element = await page.query_selector(selector)
        if element:
            # 清空输入框
            await element.click()
            await page.keyboard.press('Control+a')
            await asyncio.sleep(0.1)
            
            # 逐字符输入，模拟真实打字速度
            for char in text:
                await page.keyboard.type(char)
                # 随机打字间隔
                await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # 随机停顿
            await HumanBehaviorSimulator.random_delay(0.5, 1.5)
            return True
        return False
    
    @staticmethod
    async def human_scroll(page, direction: str = "down", distance: int = 300):
        """模拟人类滚动行为."""
        if direction == "down":
            await page.mouse.wheel(0, distance)
        else:
            await page.mouse.wheel(0, -distance)
        
        # 滚动后的停顿
        await HumanBehaviorSimulator.random_delay(0.5, 2.0)
    
    @staticmethod
    async def human_click(page, selector: str):
        """模拟人类点击行为."""
        element = await page.query_selector(selector)
        if element:
            # 移动到元素位置
            await element.hover()
            await HumanBehaviorSimulator.random_delay(0.2, 0.8)
            
            # 点击
            await element.click()
            await HumanBehaviorSimulator.random_delay(0.5, 1.5)
            return True
        return False


class GooglePatentsHumanBrowser:
    """模拟人类行为的 Google Patents 浏览器."""
    
    def __init__(self, headless: bool = False):  # 默认非无头模式便于调试
        self.headless = headless
        self.base_url = "https://patents.google.com"
        self.page = None
        self.browser = None
        self.simulator = HumanBehaviorSimulator()
        
        # 真实的用户代理列表
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
    
    async def initialize(self):
        """初始化浏览器."""
        try:
            from playwright.async_api import async_playwright
            
            logger.info("初始化人类行为模拟浏览器...")
            
            self._playwright = await async_playwright().start()
            
            # 随机选择用户代理
            user_agent = random.choice(self.user_agents)
            logger.info(f"使用用户代理: {user_agent}")
            
            # 启动浏览器
            self.browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--start-maximized',
                    f'--user-agent={user_agent}'
                ]
            )
            
            # 创建页面
            self.page = await self.browser.new_page()
            
            # 设置视窗大小（模拟真实屏幕）
            await self.page.set_viewport_size({
                "width": random.randint(1366, 1920), 
                "height": random.randint(768, 1080)
            })
            
            # 设置额外的请求头
            await self.page.set_extra_http_headers({
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Cache-Control': 'no-cache',
                'Pragma': 'no-cache',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            })
            
            # 注入反检测脚本
            await self._inject_stealth_scripts()
            
            logger.info("✓ 人类行为模拟浏览器初始化成功")
            
        except Exception as e:
            logger.error(f"浏览器初始化失败: {e}")
            raise e
    
    async def _inject_stealth_scripts(self):
        """注入反检测脚本."""
        stealth_script = """
        // 覆盖 webdriver 属性
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // 覆盖 plugins 属性
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // 覆盖 languages 属性
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en'],
        });
        
        // 覆盖 permissions 查询
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // 添加随机鼠标移动
        setInterval(() => {
            const event = new MouseEvent('mousemove', {
                clientX: Math.random() * window.innerWidth,
                clientY: Math.random() * window.innerHeight
            });
            document.dispatchEvent(event);
        }, 5000 + Math.random() * 10000);
        """
        
        await self.page.add_init_script(stealth_script)
    
    async def search_patents(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """搜索专利 - 模拟人类行为."""
        try:
            logger.info(f"开始人类行为模拟搜索: {query}")
            
            # 1. 访问主页
            await self._visit_homepage()
            
            # 2. 执行搜索
            await self._perform_human_search(query)
            
            # 3. 等待结果加载
            await self._wait_for_results()
            
            # 4. 收集结果
            patents = await self._collect_results(max_results)
            
            logger.info(f"搜索完成，找到 {len(patents)} 个专利")
            return patents
            
        except Exception as e:
            logger.error(f"搜索失败: {e}")
            return []
    
    async def _visit_homepage(self):
        """访问主页 - 模拟人类行为."""
        logger.info("访问 Google Patents 主页...")
        
        # 访问主页
        await self.page.goto(self.base_url, timeout=30000)
        
        # 模拟人类浏览行为
        await self.simulator.random_delay(2, 4)
        
        # 等待页面加载
        await self.page.wait_for_load_state("domcontentloaded")
        await self.simulator.random_delay(1, 3)
        
        # 模拟滚动浏览
        await self.simulator.human_scroll(self.page, "down", 200)
        await self.simulator.random_delay(1, 2)
        
        logger.info("✓ 主页访问完成")
    
    async def _perform_human_search(self, query: str):
        """执行人类化搜索."""
        logger.info(f"执行搜索: {query}")
        
        # 查找搜索框
        search_selectors = [
            'input[name="q"]',
            'input[placeholder*="Search"]',
            'input[type="search"]',
            '#searchInput'
        ]
        
        search_input = None
        for selector in search_selectors:
            try:
                search_input = await self.page.wait_for_selector(selector, timeout=5000)
                if search_input:
                    logger.info(f"找到搜索框: {selector}")
                    break
            except:
                continue
        
        if search_input:
            # 模拟人类输入
            await self.simulator.human_type(self.page, search_selectors[0], query)
            
            # 模拟思考时间
            await self.simulator.random_delay(1, 2)
            
            # 按回车搜索
            await self.page.keyboard.press('Enter')
            logger.info("✓ 搜索已提交")
        else:
            # 如果找不到搜索框，尝试直接访问搜索URL
            search_url = f"{self.base_url}/?q={query.replace(' ', '+')}"
            logger.info(f"直接访问搜索URL: {search_url}")
            await self.page.goto(search_url, timeout=30000)
    
    async def _wait_for_results(self):
        """等待搜索结果加载."""
        logger.info("等待搜索结果加载...")
        
        # 等待页面加载
        await self.page.wait_for_load_state("domcontentloaded")
        
        # 模拟人类等待时间
        await self.simulator.random_delay(3, 6)
        
        # 等待网络空闲
        try:
            await self.page.wait_for_load_state("networkidle", timeout=15000)
        except:
            logger.warning("网络空闲等待超时，继续处理")
        
        # 额外等待 JavaScript 渲染
        await self.simulator.random_delay(2, 4)
        
        # 模拟滚动查看结果
        await self.simulator.human_scroll(self.page, "down", 300)
        await self.simulator.random_delay(1, 2)
        
        logger.info("✓ 结果加载完成")
    
    async def _collect_results(self, max_results: int) -> List[Dict[str, Any]]:
        """收集搜索结果."""
        logger.info("收集搜索结果...")
        
        patents = []
        
        # 尝试多种结果选择器
        result_selectors = [
            'article',
            '.search-result-item',
            '.result-item',
            '[data-result]',
            '.patent-result',
            'div[role="article"]',
            '.gs_r'  # Google Scholar 样式
        ]
        
        results_found = False
        for selector in result_selectors:
            try:
                elements = await self.page.query_selector_all(selector)
                if elements and len(elements) > 0:
                    logger.info(f"使用选择器 '{selector}' 找到 {len(elements)} 个结果")
                    
                    for i, element in enumerate(elements[:max_results]):
                        try:
                            patent_data = await self._extract_patent_data(element, i + 1)
                            if patent_data:
                                patents.append(patent_data)
                                
                            # 模拟人类浏览间隔
                            await self.simulator.random_delay(0.5, 1.5)
                            
                        except Exception as e:
                            logger.warning(f"提取第 {i+1} 个结果失败: {e}")
                            continue
                    
                    results_found = True
                    break
                    
            except Exception as e:
                logger.warning(f"选择器 '{selector}' 失败: {e}")
                continue
        
        if not results_found:
            logger.warning("未找到标准结果元素，尝试通用方法...")
            # 尝试查找任何包含专利信息的链接
            all_links = await self.page.query_selector_all('a')
            for link in all_links[:20]:  # 只检查前20个链接
                try:
                    href = await link.get_attribute('href')
                    text = await link.inner_text()
                    if href and '/patent/' in href and text and len(text.strip()) > 10:
                        patent_data = {
                            "title": text.strip(),
                            "url": href if href.startswith('http') else f"https://patents.google.com{href}",
                            "patent_id": self._extract_patent_id_from_url(href),
                            "source": "google_patents_human",
                            "collected_at": datetime.now().isoformat()
                        }
                        patents.append(patent_data)
                        
                        if len(patents) >= max_results:
                            break
                except:
                    continue
        
        # 保存页面截图用于调试
        if len(patents) == 0:
            screenshot_path = f"google_patents_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            await self.page.screenshot(path=screenshot_path, full_page=True)
            logger.info(f"调试截图已保存: {screenshot_path}")
        
        return patents
    
    async def _extract_patent_data(self, element, index: int) -> Optional[Dict[str, Any]]:
        """从结果元素中提取专利数据."""
        try:
            patent_data = {
                "index": index,
                "source": "google_patents_human",
                "collected_at": datetime.now().isoformat()
            }
            
            # 提取文本内容
            text_content = await element.inner_text()
            if not text_content or len(text_content.strip()) < 10:
                return None
            
            # 提取链接
            link_element = await element.query_selector('a')
            if link_element:
                href = await link_element.get_attribute('href')
                if href:
                    patent_data["url"] = href if href.startswith('http') else f"https://patents.google.com{href}"
                    patent_data["patent_id"] = self._extract_patent_id_from_url(href)
            
            # 提取标题（通常是第一行或链接文本）
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            if lines:
                patent_data["title"] = lines[0]
                if len(lines) > 1:
                    patent_data["description"] = ' '.join(lines[1:3])
            
            return patent_data if patent_data.get("title") else None
            
        except Exception as e:
            logger.warning(f"提取专利数据失败: {e}")
            return None
    
    def _extract_patent_id_from_url(self, url: str) -> str:
        """从URL中提取专利ID."""
        import re
        match = re.search(r'/patent/([^/\?]+)', url)
        return match.group(1) if match else f"UNKNOWN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    async def close(self):
        """关闭浏览器."""
        try:
            if self.page:
                await self.page.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, '_playwright'):
                await self._playwright.stop()
            logger.info("浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")


async def test_human_behavior_google_patents():
    """测试人类行为模拟的 Google Patents 访问."""
    logger.info("=== 人类行为模拟 Google Patents 测试 ===")
    
    browser = GooglePatentsHumanBrowser(headless=True)  # 设为 False 可观察行为
    
    try:
        # 初始化
        await browser.initialize()
        
        # 测试查询
        test_queries = [
            "artificial intelligence",
            "machine learning"
        ]
        
        all_results = {}
        
        for query in test_queries:
            logger.info(f"\n--- 测试查询: {query} ---")
            
            patents = await browser.search_patents(query, max_results=3)
            all_results[query] = patents
            
            if patents:
                logger.info(f"✓ 找到 {len(patents)} 个专利")
                for i, patent in enumerate(patents, 1):
                    logger.info(f"\n专利 {i}:")
                    logger.info(f"  标题: {patent.get('title', 'N/A')}")
                    logger.info(f"  ID: {patent.get('patent_id', 'N/A')}")
                    logger.info(f"  URL: {patent.get('url', 'N/A')}")
            else:
                logger.warning(f"✗ 未找到 '{query}' 相关专利")
            
            # 查询间隔
            await asyncio.sleep(3)
        
        # 保存结果
        result_file = f"human_behavior_patents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        logger.info(f"\n结果已保存到: {result_file}")
        
        # 统计
        total_patents = sum(len(patents) for patents in all_results.values())
        successful_queries = sum(1 for patents in all_results.values() if patents)
        
        logger.info(f"\n=== 测试统计 ===")
        logger.info(f"总查询数: {len(test_queries)}")
        logger.info(f"成功查询: {successful_queries}")
        logger.info(f"总专利数: {total_patents}")
        logger.info(f"成功率: {successful_queries/len(test_queries)*100:.1f}%")
        
        return successful_queries > 0
        
    finally:
        await browser.close()


async def main():
    """主函数."""
    success = await test_human_behavior_google_patents()
    
    if success:
        logger.info("\n🎉 人类行为模拟 Google Patents 访问成功!")
        return 0
    else:
        logger.error("\n❌ 人类行为模拟 Google Patents 访问失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)