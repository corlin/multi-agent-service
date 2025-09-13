#!/usr/bin/env python3
"""高级人类行为模拟 - Google Patents 访问."""

import asyncio
import logging
import random
import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AdvancedHumanSimulator:
    """高级人类行为模拟器."""
    
    def __init__(self):
        # 真实的浏览器指纹数据
        self.browser_profiles = [
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1440, "height": 900},
                "platform": "MacIntel",
                "languages": ["en-US", "en"],
                "timezone": "America/New_York"
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "viewport": {"width": 1920, "height": 1080},
                "platform": "Win32",
                "languages": ["en-US", "en"],
                "timezone": "America/Los_Angeles"
            },
            {
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
                "viewport": {"width": 1680, "height": 1050},
                "platform": "MacIntel",
                "languages": ["en-US", "en"],
                "timezone": "America/Chicago"
            }
        ]
        
        self.current_profile = random.choice(self.browser_profiles)
    
    async def random_human_delay(self, min_seconds: float = 0.5, max_seconds: float = 3.0):
        """更真实的人类延迟."""
        # 使用正态分布模拟人类反应时间
        mean = (min_seconds + max_seconds) / 2
        std = (max_seconds - min_seconds) / 6
        delay = max(min_seconds, min(max_seconds, random.normalvariate(mean, std)))
        await asyncio.sleep(delay)
    
    async def human_mouse_movement(self, page, target_selector: str = None):
        """模拟真实的鼠标移动轨迹."""
        try:
            if target_selector:
                element = await page.query_selector(target_selector)
                if element:
                    box = await element.bounding_box()
                    if box:
                        # 生成曲线路径到目标
                        target_x = box['x'] + box['width'] / 2
                        target_y = box['y'] + box['height'] / 2
                        
                        # 当前鼠标位置（模拟）
                        current_x = random.randint(100, 800)
                        current_y = random.randint(100, 600)
                        
                        # 生成贝塞尔曲线路径
                        steps = random.randint(8, 15)
                        for i in range(steps):
                            progress = i / steps
                            # 添加随机抖动
                            jitter_x = random.uniform(-5, 5)
                            jitter_y = random.uniform(-5, 5)
                            
                            x = current_x + (target_x - current_x) * progress + jitter_x
                            y = current_y + (target_y - current_y) * progress + jitter_y
                            
                            await page.mouse.move(x, y)
                            await asyncio.sleep(random.uniform(0.01, 0.03))
            else:
                # 随机鼠标移动
                for _ in range(random.randint(2, 5)):
                    x = random.randint(100, 1200)
                    y = random.randint(100, 800)
                    await page.mouse.move(x, y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
        except Exception as e:
            logger.debug(f"鼠标移动模拟失败: {e}")
    
    async def human_typing(self, page, selector: str, text: str):
        """高级人类打字模拟."""
        element = await page.query_selector(selector)
        if not element:
            return False
        
        # 先移动鼠标到输入框
        await self.human_mouse_movement(page, selector)
        await self.random_human_delay(0.2, 0.8)
        
        # 点击输入框
        await element.click()
        await self.random_human_delay(0.1, 0.3)
        
        # 清空现有内容
        await page.keyboard.press('Control+a')
        await asyncio.sleep(0.1)
        
        # 模拟真实打字
        for i, char in enumerate(text):
            # 模拟打字错误和修正
            if random.random() < 0.02:  # 2% 概率打错
                wrong_char = random.choice('abcdefghijklmnopqrstuvwxyz')
                await page.keyboard.type(wrong_char)
                await asyncio.sleep(random.uniform(0.1, 0.3))
                await page.keyboard.press('Backspace')
                await asyncio.sleep(random.uniform(0.1, 0.2))
            
            await page.keyboard.type(char)
            
            # 真实的打字间隔
            if char == ' ':
                delay = random.uniform(0.1, 0.3)
            elif i > 0 and text[i-1] in '.,!?':
                delay = random.uniform(0.2, 0.5)
            else:
                delay = random.uniform(0.05, 0.15)
            
            await asyncio.sleep(delay)
        
        # 打字完成后的停顿
        await self.random_human_delay(0.5, 1.5)
        return True
    
    async def human_scroll_behavior(self, page):
        """模拟真实的滚动行为."""
        # 随机滚动模式
        scroll_patterns = [
            # 快速浏览
            [(300, 0.5), (200, 0.3), (400, 0.8)],
            # 仔细阅读
            [(150, 1.2), (100, 2.0), (200, 1.5)],
            # 寻找内容
            [(500, 0.2), (-200, 0.5), (300, 0.3)]
        ]
        
        pattern = random.choice(scroll_patterns)
        for distance, pause in pattern:
            await page.mouse.wheel(0, distance)
            await asyncio.sleep(pause + random.uniform(-0.2, 0.2))


class AdvancedGooglePatentsBrowser:
    """高级 Google Patents 浏览器."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = "https://patents.google.com"
        self.page = None
        self.browser = None
        self.context = None
        self.simulator = AdvancedHumanSimulator()
        
        # 会话状态
        self.session_start_time = time.time()
        self.page_views = 0
        self.search_count = 0
    
    async def initialize(self):
        """初始化高级浏览器环境."""
        try:
            from playwright.async_api import async_playwright
            
            logger.info("初始化高级人类行为模拟浏览器...")
            
            self._playwright = await async_playwright().start()
            
            profile = self.simulator.current_profile
            logger.info(f"使用浏览器配置: {profile['platform']}")
            
            # 启动浏览器
            self.browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-web-security',
                    '--disable-features=VizDisplayCompositor',
                    '--disable-background-timer-throttling',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-renderer-backgrounding',
                    '--disable-field-trial-config',
                    '--disable-ipc-flooding-protection',
                    '--no-first-run',
                    '--no-default-browser-check',
                    '--disable-default-apps',
                    '--disable-popup-blocking',
                    '--disable-translate',
                    '--disable-background-networking',
                    '--disable-sync',
                    '--metrics-recording-only',
                    '--no-report-upload',
                    '--disable-component-update'
                ]
            )
            
            # 创建浏览器上下文
            self.context = await self.browser.new_context(
                user_agent=profile['user_agent'],
                viewport=profile['viewport'],
                locale='en-US',
                timezone_id=profile['timezone'],
                geolocation={'latitude': 40.7128, 'longitude': -74.0060},  # 纽约
                permissions=['geolocation']
            )
            
            # 创建页面
            self.page = await self.context.new_page()
            
            # 注入高级反检测脚本
            await self._inject_advanced_stealth()
            
            # 设置真实的浏览器行为
            await self._setup_realistic_behavior()
            
            logger.info("✓ 高级浏览器环境初始化成功")
            
        except Exception as e:
            logger.error(f"高级浏览器初始化失败: {e}")
            raise e
    
    async def _inject_advanced_stealth(self):
        """注入高级反检测脚本."""
        profile = self.simulator.current_profile
        
        stealth_script = f"""
        // 完全移除 webdriver 痕迹
        Object.defineProperty(navigator, 'webdriver', {{
            get: () => undefined,
        }});
        
        // 设置真实的 platform
        Object.defineProperty(navigator, 'platform', {{
            get: () => '{profile['platform']}',
        }});
        
        // 设置真实的 languages
        Object.defineProperty(navigator, 'languages', {{
            get: () => {json.dumps(profile['languages'])},
        }});
        
        // 模拟真实的 plugins
        Object.defineProperty(navigator, 'plugins', {{
            get: () => {{
                const plugins = [];
                plugins.length = 3;
                plugins[0] = {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' }};
                plugins[1] = {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' }};
                plugins[2] = {{ name: 'Native Client', filename: 'internal-nacl-plugin' }};
                return plugins;
            }},
        }});
        
        // 覆盖 permissions 查询
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({{ state: 'default' }}) :
                originalQuery(parameters)
        );
        
        // 模拟真实的 screen 属性
        Object.defineProperty(screen, 'width', {{
            get: () => {profile['viewport']['width']},
        }});
        Object.defineProperty(screen, 'height', {{
            get: () => {profile['viewport']['height']},
        }});
        
        // 添加真实的鼠标和键盘事件
        let mouseX = Math.random() * window.innerWidth;
        let mouseY = Math.random() * window.innerHeight;
        
        setInterval(() => {{
            mouseX += (Math.random() - 0.5) * 10;
            mouseY += (Math.random() - 0.5) * 10;
            mouseX = Math.max(0, Math.min(window.innerWidth, mouseX));
            mouseY = Math.max(0, Math.min(window.innerHeight, mouseY));
            
            const event = new MouseEvent('mousemove', {{
                clientX: mouseX,
                clientY: mouseY,
                bubbles: true
            }});
            document.dispatchEvent(event);
        }}, 2000 + Math.random() * 3000);
        
        // 模拟真实的页面可见性变化
        let isVisible = true;
        setInterval(() => {{
            if (Math.random() < 0.1) {{
                isVisible = !isVisible;
                Object.defineProperty(document, 'hidden', {{
                    get: () => !isVisible,
                }});
                document.dispatchEvent(new Event('visibilitychange'));
            }}
        }}, 10000 + Math.random() * 20000);
        
        // 覆盖 Date 对象以避免时区检测
        const originalDate = Date;
        Date = class extends originalDate {{
            constructor(...args) {{
                if (args.length === 0) {{
                    super();
                }} else {{
                    super(...args);
                }}
            }}
            
            getTimezoneOffset() {{
                return 300; // EST timezone
            }}
        }};
        
        // 添加真实的性能指标
        if (window.performance && window.performance.timing) {{
            const timing = window.performance.timing;
            Object.defineProperty(timing, 'loadEventEnd', {{
                get: () => Date.now() - Math.random() * 1000,
            }});
        }}
        """
        
        await self.page.add_init_script(stealth_script)
    
    async def _setup_realistic_behavior(self):
        """设置真实的浏览器行为."""
        # 设置真实的请求头
        await self.page.set_extra_http_headers({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Cache-Control': 'max-age=0',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': f'"{self.simulator.current_profile["platform"]}"',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 监听网络请求
        await self.page.route('**/*', self._handle_request)
    
    async def _handle_request(self, route):
        """处理网络请求，添加真实的请求行为."""
        request = route.request
        
        # 添加随机延迟模拟网络延迟
        if random.random() < 0.1:  # 10% 的请求添加延迟
            await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # 继续请求
        await route.continue_()
    
    async def search_patents_advanced(self, query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """高级专利搜索."""
        try:
            logger.info(f"开始高级人类行为搜索: {query}")
            
            # 1. 模拟真实的浏览会话开始
            await self._simulate_session_start()
            
            # 2. 访问主页并模拟浏览行为
            await self._visit_homepage_realistic()
            
            # 3. 执行搜索
            await self._perform_advanced_search(query)
            
            # 4. 等待并处理结果
            patents = await self._collect_results_advanced(max_results)
            
            # 5. 模拟会话结束行为
            await self._simulate_session_end()
            
            logger.info(f"高级搜索完成，找到 {len(patents)} 个专利")
            return patents
            
        except Exception as e:
            logger.error(f"高级搜索失败: {e}")
            return []
    
    async def _simulate_session_start(self):
        """模拟真实的会话开始."""
        logger.info("模拟会话开始...")
        
        # 模拟用户打开浏览器的行为
        await self.simulator.random_human_delay(1, 3)
        
        # 可能先访问其他网站（模拟真实用户行为）
        if random.random() < 0.3:  # 30% 概率先访问其他网站
            logger.info("模拟先访问其他网站...")
            try:
                await self.page.goto('https://www.google.com', timeout=15000)
                await self.simulator.random_human_delay(2, 4)
                await self.simulator.human_scroll_behavior(self.page)
            except:
                pass  # 忽略错误，继续主要任务
    
    async def _visit_homepage_realistic(self):
        """真实地访问主页."""
        logger.info("真实地访问 Google Patents 主页...")
        
        try:
            # 访问主页
            await self.page.goto(self.base_url, timeout=45000)
            self.page_views += 1
            
            # 等待页面加载
            await self.page.wait_for_load_state("domcontentloaded")
            await self.simulator.random_human_delay(2, 5)
            
            # 模拟真实的浏览行为
            await self.simulator.human_mouse_movement(self.page)
            await self.simulator.random_human_delay(1, 3)
            
            # 模拟阅读页面内容
            await self.simulator.human_scroll_behavior(self.page)
            await self.simulator.random_human_delay(2, 4)
            
            # 等待 JavaScript 完全加载
            await self.page.wait_for_load_state("networkidle", timeout=20000)
            await self.simulator.random_human_delay(1, 3)
            
            logger.info("✓ 主页访问完成")
            
        except Exception as e:
            logger.warning(f"主页访问遇到问题: {e}")
            # 尝试重新加载
            try:
                await self.page.reload(timeout=30000)
                await self.simulator.random_human_delay(3, 6)
            except:
                pass
    
    async def _perform_advanced_search(self, query: str):
        """执行高级搜索."""
        logger.info(f"执行高级搜索: {query}")
        
        # 查找搜索框
        search_selectors = [
            'input[name="q"]',
            'input[placeholder*="Search"]',
            'input[placeholder*="search"]',
            'input[type="search"]',
            '#searchInput',
            '.search-input'
        ]
        
        search_input = None
        for selector in search_selectors:
            try:
                search_input = await self.page.wait_for_selector(selector, timeout=8000)
                if search_input:
                    logger.info(f"找到搜索框: {selector}")
                    break
            except:
                continue
        
        if search_input:
            # 高级人类打字模拟
            success = await self.simulator.human_typing(self.page, search_selectors[0], query)
            
            if success:
                # 模拟思考时间
                await self.simulator.random_human_delay(1, 3)
                
                # 按回车搜索
                await self.page.keyboard.press('Enter')
                self.search_count += 1
                logger.info("✓ 搜索已提交")
                
                # 等待搜索结果
                await self.page.wait_for_load_state("domcontentloaded")
                await self.simulator.random_human_delay(3, 6)
                
                try:
                    await self.page.wait_for_load_state("networkidle", timeout=25000)
                except:
                    logger.warning("网络空闲等待超时")
                
                # 额外等待 JavaScript 渲染
                await self.simulator.random_human_delay(2, 5)
            else:
                raise Exception("搜索框输入失败")
        else:
            # 如果找不到搜索框，尝试直接访问搜索URL
            search_url = f"{self.base_url}/?q={query.replace(' ', '+')}"
            logger.info(f"直接访问搜索URL: {search_url}")
            await self.page.goto(search_url, timeout=45000)
            await self.simulator.random_human_delay(3, 6)
    
    async def _collect_results_advanced(self, max_results: int) -> List[Dict[str, Any]]:
        """高级结果收集."""
        logger.info("收集搜索结果...")
        
        patents = []
        
        # 模拟用户查看结果的行为
        await self.simulator.human_scroll_behavior(self.page)
        await self.simulator.random_human_delay(2, 4)
        
        # 保存页面内容用于调试
        content = await self.page.content()
        debug_file = f"google_patents_content_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"页面内容已保存: {debug_file}")
        
        # 保存截图
        screenshot_file = f"google_patents_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        await self.page.screenshot(path=screenshot_file, full_page=True)
        logger.info(f"页面截图已保存: {screenshot_file}")
        
        # 尝试多种方法查找结果
        result_methods = [
            self._find_results_by_articles,
            self._find_results_by_links,
            self._find_results_by_text_analysis
        ]
        
        for method in result_methods:
            try:
                results = await method(max_results)
                if results:
                    patents.extend(results)
                    logger.info(f"通过 {method.__name__} 找到 {len(results)} 个结果")
                    break
            except Exception as e:
                logger.warning(f"{method.__name__} 失败: {e}")
                continue
        
        return patents[:max_results]
    
    async def _find_results_by_articles(self, max_results: int) -> List[Dict[str, Any]]:
        """通过 article 元素查找结果."""
        articles = await self.page.query_selector_all('article')
        results = []
        
        for i, article in enumerate(articles[:max_results]):
            try:
                text = await article.inner_text()
                if text and len(text.strip()) > 20:
                    link = await article.query_selector('a')
                    href = await link.get_attribute('href') if link else None
                    
                    result = {
                        "title": text.split('\n')[0].strip(),
                        "url": href if href and href.startswith('http') else f"https://patents.google.com{href}" if href else None,
                        "patent_id": self._extract_patent_id_from_url(href) if href else f"ARTICLE_{i}",
                        "source": "google_patents_advanced",
                        "method": "articles",
                        "collected_at": datetime.now().isoformat()
                    }
                    results.append(result)
            except:
                continue
        
        return results
    
    async def _find_results_by_links(self, max_results: int) -> List[Dict[str, Any]]:
        """通过专利链接查找结果."""
        all_links = await self.page.query_selector_all('a')
        results = []
        
        for link in all_links:
            if len(results) >= max_results:
                break
            
            try:
                href = await link.get_attribute('href')
                text = await link.inner_text()
                
                if href and '/patent/' in href and text and len(text.strip()) > 10:
                    result = {
                        "title": text.strip(),
                        "url": href if href.startswith('http') else f"https://patents.google.com{href}",
                        "patent_id": self._extract_patent_id_from_url(href),
                        "source": "google_patents_advanced",
                        "method": "links",
                        "collected_at": datetime.now().isoformat()
                    }
                    results.append(result)
            except:
                continue
        
        return results
    
    async def _find_results_by_text_analysis(self, max_results: int) -> List[Dict[str, Any]]:
        """通过文本分析查找结果."""
        content = await self.page.content()
        results = []
        
        # 查找专利号模式
        patent_patterns = [
            r'US\d{7,10}[A-Z]\d*',
            r'EP\d{7,10}[A-Z]\d*',
            r'WO\d{4}/\d{6}',
            r'CN\d{9,12}[A-Z]'
        ]
        
        for pattern in patent_patterns:
            import re
            matches = re.findall(pattern, content)
            for i, match in enumerate(matches[:max_results]):
                if len(results) >= max_results:
                    break
                
                result = {
                    "title": f"Patent {match}",
                    "patent_id": match,
                    "patent_number": match,
                    "url": f"https://patents.google.com/patent/{match}",
                    "source": "google_patents_advanced",
                    "method": "text_analysis",
                    "collected_at": datetime.now().isoformat()
                }
                results.append(result)
        
        return results
    
    def _extract_patent_id_from_url(self, url: str) -> str:
        """从URL中提取专利ID."""
        if not url:
            return f"UNKNOWN_{int(time.time())}"
        
        import re
        match = re.search(r'/patent/([^/\?]+)', url)
        return match.group(1) if match else f"EXTRACTED_{int(time.time())}"
    
    async def _simulate_session_end(self):
        """模拟会话结束."""
        logger.info("模拟会话结束...")
        
        # 模拟用户浏览完成后的行为
        await self.simulator.random_human_delay(2, 5)
        
        # 可能滚动查看更多内容
        if random.random() < 0.5:
            await self.simulator.human_scroll_behavior(self.page)
            await self.simulator.random_human_delay(1, 3)
    
    async def close(self):
        """关闭浏览器."""
        try:
            session_duration = time.time() - self.session_start_time
            logger.info(f"会话统计 - 持续时间: {session_duration:.1f}s, 页面访问: {self.page_views}, 搜索次数: {self.search_count}")
            
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, '_playwright'):
                await self._playwright.stop()
            logger.info("高级浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")


async def test_advanced_human_behavior():
    """测试高级人类行为模拟."""
    logger.info("=== 高级人类行为模拟 Google Patents 测试 ===")
    
    browser = AdvancedGooglePatentsBrowser(headless=True)  # 设为 False 可观察行为
    
    try:
        # 初始化
        await browser.initialize()
        
        # 测试查询
        test_queries = [
            "artificial intelligence patent",
            "machine learning algorithm"
        ]
        
        all_results = {}
        
        for query in test_queries:
            logger.info(f"\n--- 高级测试查询: {query} ---")
            
            patents = await browser.search_patents_advanced(query, max_results=5)
            all_results[query] = patents
            
            if patents:
                logger.info(f"✓ 找到 {len(patents)} 个专利")
                for i, patent in enumerate(patents, 1):
                    logger.info(f"\n专利 {i}:")
                    logger.info(f"  标题: {patent.get('title', 'N/A')}")
                    logger.info(f"  ID: {patent.get('patent_id', 'N/A')}")
                    logger.info(f"  方法: {patent.get('method', 'N/A')}")
                    logger.info(f"  URL: {patent.get('url', 'N/A')}")
            else:
                logger.warning(f"✗ 未找到 '{query}' 相关专利")
            
            # 查询间隔
            await asyncio.sleep(5)
        
        # 保存结果
        result_file = f"advanced_human_patents_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=2)
        logger.info(f"\n结果已保存到: {result_file}")
        
        # 统计
        total_patents = sum(len(patents) for patents in all_results.values())
        successful_queries = sum(1 for patents in all_results.values() if patents)
        
        logger.info(f"\n=== 高级测试统计 ===")
        logger.info(f"总查询数: {len(test_queries)}")
        logger.info(f"成功查询: {successful_queries}")
        logger.info(f"总专利数: {total_patents}")
        logger.info(f"成功率: {successful_queries/len(test_queries)*100:.1f}%")
        
        return successful_queries > 0
        
    finally:
        await browser.close()


async def main():
    """主函数."""
    success = await test_advanced_human_behavior()
    
    if success:
        logger.info("\n🎉 高级人类行为模拟 Google Patents 访问成功!")
        return 0
    else:
        logger.error("\n❌ 高级人类行为模拟 Google Patents 访问失败")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)