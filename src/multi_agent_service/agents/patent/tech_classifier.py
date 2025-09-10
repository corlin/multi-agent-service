"""Technology classifier for patent analysis."""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import re
from datetime import datetime


logger = logging.getLogger(__name__)


class TechClassifier:
    """技术分类器，实现专利技术分类和聚类分析."""
    
    def __init__(self):
        """初始化技术分类器."""
        self.logger = logging.getLogger(f"{__name__}.TechClassifier")
        
        # IPC分类映射
        self.ipc_mapping = {
            "G06F": "数据处理系统",
            "H04L": "数字信息传输",
            "G06N": "人工智能",
            "H04W": "无线通信网络",
            "G06Q": "数据处理系统或方法",
            "H01L": "半导体器件",
            "G06K": "数据识别",
            "H04N": "图像通信",
            "G06T": "图像数据处理",
            "G01S": "无线电定位"
        }
        
        # 技术关键词映射
        self.tech_keywords = {
            "人工智能": ["人工智能", "AI", "机器学习", "深度学习", "神经网络", "算法"],
            "区块链": ["区块链", "blockchain", "分布式账本", "智能合约", "加密货币"],
            "物联网": ["物联网", "IoT", "传感器", "智能设备", "连接"],
            "5G通信": ["5G", "通信", "无线", "网络", "基站"],
            "新能源": ["新能源", "电池", "太阳能", "风能", "储能"],
            "生物技术": ["生物", "基因", "蛋白质", "细胞", "医疗"],
            "芯片技术": ["芯片", "半导体", "处理器", "集成电路", "微电子"]
        }
    
    async def classify_technologies(self, patent_data: List[Dict[str, Any]], analysis_params: Dict[str, Any]) -> Dict[str, Any]:
        """对专利进行技术分类分析."""
        try:
            self.logger.info(f"Starting technology classification for {len(patent_data)} patents")
            
            # IPC分类统计
            ipc_analysis = self._analyze_ipc_classes(patent_data)
            
            # 关键词聚类分析
            keyword_analysis = self._analyze_keywords(patent_data)
            
            # 技术领域识别
            tech_domains = self._identify_tech_domains(patent_data)
            
            # 技术演进分析
            tech_evolution = self._analyze_tech_evolution(patent_data)
            
            # 识别主要技术
            main_technologies = self._identify_main_technologies(ipc_analysis, keyword_analysis, tech_domains)
            
            result = {
                "ipc_distribution": ipc_analysis["distribution"],
                "ipc_categories": ipc_analysis["categories"],
                "keyword_clusters": keyword_analysis["clusters"],
                "tech_domains": tech_domains,
                "tech_evolution": tech_evolution,
                "main_technologies": main_technologies,
                "classification_summary": self._generate_classification_summary(ipc_analysis, tech_domains),
                "total_patents_classified": len(patent_data)
            }
            
            self.logger.info("Technology classification completed successfully")
            return result
            
        except Exception as e:
            self.logger.error(f"Error in technology classification: {str(e)}")
            return {"error": str(e), "success": False}
    
    def _analyze_ipc_classes(self, patent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析IPC分类分布."""
        try:
            ipc_counts = defaultdict(int)
            ipc_details = defaultdict(list)
            
            for patent in patent_data:
                ipc_classes = patent.get("ipc_classes", [])
                for ipc in ipc_classes:
                    # 提取主分类（前4位）
                    main_ipc = ipc[:4] if len(ipc) >= 4 else ipc
                    ipc_counts[main_ipc] += 1
                    ipc_details[main_ipc].append({
                        "patent_id": patent.get("application_number", ""),
                        "title": patent.get("title", ""),
                        "full_ipc": ipc
                    })
            
            # 转换为分类名称
            ipc_categories = {}
            for ipc, count in ipc_counts.items():
                category_name = self.ipc_mapping.get(ipc, f"其他分类({ipc})")
                ipc_categories[category_name] = count
            
            # 排序
            sorted_ipc = sorted(ipc_counts.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "distribution": dict(ipc_counts),
                "categories": ipc_categories,
                "sorted_classes": sorted_ipc,
                "details": dict(ipc_details),
                "total_classes": len(ipc_counts)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing IPC classes: {str(e)}")
            return {"distribution": {}, "categories": {}, "sorted_classes": []}
    
    def _analyze_keywords(self, patent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析关键词和技术聚类."""
        try:
            # 提取所有文本内容
            all_text = []
            for patent in patent_data:
                text_parts = [
                    patent.get("title", ""),
                    patent.get("abstract", "")
                ]
                all_text.extend([text for text in text_parts if text])
            
            # 关键词提取
            keywords = self._extract_keywords_from_text(all_text)
            
            # 技术聚类
            clusters = self._cluster_keywords(keywords)
            
            return {
                "keywords": keywords,
                "clusters": clusters,
                "keyword_frequency": dict(Counter(keywords).most_common(20))
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing keywords: {str(e)}")
            return {"keywords": [], "clusters": [], "keyword_frequency": {}}
    
    def _extract_keywords_from_text(self, text_list: List[str]) -> List[str]:
        """从文本中提取关键词."""
        try:
            keywords = []
            
            # 合并所有文本
            combined_text = " ".join(text_list).lower()
            
            # 技术相关的正则表达式模式
            tech_patterns = [
                r'(人工智能|AI|机器学习|深度学习)',
                r'(区块链|blockchain)',
                r'(物联网|IoT)',
                r'(5G|通信技术)',
                r'(新能源|电池技术)',
                r'(生物技术|基因)',
                r'(芯片|半导体)',
                r'(云计算|大数据)',
                r'(虚拟现实|VR|增强现实|AR)',
                r'(自动驾驶|无人驾驶)',
            ]
            
            for pattern in tech_patterns:
                matches = re.findall(pattern, combined_text)
                keywords.extend(matches)
            
            # 通用技术词汇
            common_tech_words = [
                "算法", "系统", "方法", "装置", "设备", "网络", "数据", "信息",
                "处理", "控制", "检测", "识别", "分析", "优化", "管理", "服务"
            ]
            
            for word in common_tech_words:
                if word in combined_text:
                    keywords.append(word)
            
            return list(set(keywords))  # 去重
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {str(e)}")
            return []
    
    def _cluster_keywords(self, keywords: List[str]) -> List[Dict[str, Any]]:
        """对关键词进行聚类."""
        try:
            clusters = []
            
            # 基于预定义的技术领域进行聚类
            for domain, domain_keywords in self.tech_keywords.items():
                cluster_keywords = []
                for keyword in keywords:
                    if any(dk in keyword.lower() for dk in domain_keywords):
                        cluster_keywords.append(keyword)
                
                if cluster_keywords:
                    clusters.append({
                        "domain": domain,
                        "keywords": cluster_keywords,
                        "size": len(cluster_keywords)
                    })
            
            # 未分类的关键词
            classified_keywords = set()
            for cluster in clusters:
                classified_keywords.update(cluster["keywords"])
            
            unclassified = [kw for kw in keywords if kw not in classified_keywords]
            if unclassified:
                clusters.append({
                    "domain": "其他技术",
                    "keywords": unclassified,
                    "size": len(unclassified)
                })
            
            # 按大小排序
            clusters.sort(key=lambda x: x["size"], reverse=True)
            
            return clusters
            
        except Exception as e:
            self.logger.error(f"Error clustering keywords: {str(e)}")
            return []
    
    def _identify_tech_domains(self, patent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """识别技术领域分布."""
        try:
            domain_counts = defaultdict(int)
            domain_patents = defaultdict(list)
            
            for patent in patent_data:
                title = patent.get("title", "").lower()
                abstract = patent.get("abstract", "").lower()
                combined_text = f"{title} {abstract}"
                
                # 检查每个技术领域
                patent_domains = []
                for domain, keywords in self.tech_keywords.items():
                    if any(keyword.lower() in combined_text for keyword in keywords):
                        domain_counts[domain] += 1
                        patent_domains.append(domain)
                        domain_patents[domain].append({
                            "patent_id": patent.get("application_number", ""),
                            "title": patent.get("title", "")
                        })
                
                # 如果没有匹配到任何领域，归类为"其他"
                if not patent_domains:
                    domain_counts["其他技术"] += 1
                    domain_patents["其他技术"].append({
                        "patent_id": patent.get("application_number", ""),
                        "title": patent.get("title", "")
                    })
            
            # 计算百分比
            total_patents = len(patent_data)
            domain_percentages = {
                domain: (count / total_patents) * 100
                for domain, count in domain_counts.items()
            }
            
            # 排序
            sorted_domains = sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)
            
            return {
                "domain_distribution": dict(domain_counts),
                "domain_percentages": domain_percentages,
                "sorted_domains": sorted_domains,
                "domain_patents": dict(domain_patents),
                "total_domains": len(domain_counts)
            }
            
        except Exception as e:
            self.logger.error(f"Error identifying tech domains: {str(e)}")
            return {"domain_distribution": {}, "domain_percentages": {}}
    
    def _analyze_tech_evolution(self, patent_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析技术演进趋势."""
        try:
            # 按年份和技术领域统计
            yearly_tech_counts = defaultdict(lambda: defaultdict(int))
            
            for patent in patent_data:
                # 提取年份
                app_date = patent.get("application_date", "")
                if app_date:
                    try:
                        year = int(app_date.split("-")[0])
                    except (ValueError, IndexError):
                        continue
                else:
                    continue
                
                # 识别技术领域
                title = patent.get("title", "").lower()
                abstract = patent.get("abstract", "").lower()
                combined_text = f"{title} {abstract}"
                
                for domain, keywords in self.tech_keywords.items():
                    if any(keyword.lower() in combined_text for keyword in keywords):
                        yearly_tech_counts[year][domain] += 1
            
            # 计算技术演进趋势
            tech_trends = {}
            for domain in self.tech_keywords.keys():
                domain_data = {}
                for year in sorted(yearly_tech_counts.keys()):
                    domain_data[year] = yearly_tech_counts[year][domain]
                tech_trends[domain] = domain_data
            
            return {
                "yearly_tech_distribution": dict(yearly_tech_counts),
                "tech_trends": tech_trends,
                "evolution_summary": self._summarize_tech_evolution(tech_trends)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing tech evolution: {str(e)}")
            return {"yearly_tech_distribution": {}, "tech_trends": {}}
    
    def _summarize_tech_evolution(self, tech_trends: Dict[str, Dict[int, int]]) -> Dict[str, str]:
        """总结技术演进趋势."""
        try:
            summaries = {}
            
            for domain, yearly_data in tech_trends.items():
                if not yearly_data:
                    continue
                
                years = sorted(yearly_data.keys())
                if len(years) < 2:
                    summaries[domain] = "数据不足"
                    continue
                
                # 计算总体趋势
                early_avg = sum(yearly_data[year] for year in years[:len(years)//2]) / (len(years)//2)
                late_avg = sum(yearly_data[year] for year in years[len(years)//2:]) / (len(years) - len(years)//2)
                
                if late_avg > early_avg * 1.2:
                    summaries[domain] = "快速增长"
                elif late_avg > early_avg * 1.05:
                    summaries[domain] = "稳定增长"
                elif late_avg < early_avg * 0.8:
                    summaries[domain] = "下降趋势"
                else:
                    summaries[domain] = "相对稳定"
            
            return summaries
            
        except Exception as e:
            self.logger.error(f"Error summarizing tech evolution: {str(e)}")
            return {}
    
    def _identify_main_technologies(self, ipc_analysis: Dict[str, Any], keyword_analysis: Dict[str, Any], tech_domains: Dict[str, Any]) -> List[str]:
        """识别主要技术领域."""
        try:
            main_techs = []
            
            # 基于IPC分类
            ipc_categories = ipc_analysis.get("categories", {})
            if ipc_categories:
                top_ipc = sorted(ipc_categories.items(), key=lambda x: x[1], reverse=True)[:3]
                main_techs.extend([category for category, _ in top_ipc])
            
            # 基于技术领域分布
            domain_distribution = tech_domains.get("domain_distribution", {})
            if domain_distribution:
                top_domains = sorted(domain_distribution.items(), key=lambda x: x[1], reverse=True)[:3]
                for domain, _ in top_domains:
                    if domain not in main_techs:
                        main_techs.append(domain)
            
            # 基于关键词聚类
            clusters = keyword_analysis.get("clusters", [])
            for cluster in clusters[:2]:  # 取前两个最大的聚类
                domain = cluster.get("domain", "")
                if domain and domain not in main_techs:
                    main_techs.append(domain)
            
            return main_techs[:5]  # 返回前5个主要技术
            
        except Exception as e:
            self.logger.error(f"Error identifying main technologies: {str(e)}")
            return []
    
    def _generate_classification_summary(self, ipc_analysis: Dict[str, Any], tech_domains: Dict[str, Any]) -> str:
        """生成分类总结."""
        try:
            summary_parts = []
            
            # IPC分类总结
            ipc_categories = ipc_analysis.get("categories", {})
            if ipc_categories:
                top_ipc = sorted(ipc_categories.items(), key=lambda x: x[1], reverse=True)[0]
                summary_parts.append(f"主要IPC分类为{top_ipc[0]}({top_ipc[1]}件)")
            
            # 技术领域总结
            domain_distribution = tech_domains.get("domain_distribution", {})
            if domain_distribution:
                top_domain = sorted(domain_distribution.items(), key=lambda x: x[1], reverse=True)[0]
                summary_parts.append(f"主要技术领域为{top_domain[0]}({top_domain[1]}件)")
            
            # 多样性分析
            total_domains = tech_domains.get("total_domains", 0)
            if total_domains > 5:
                summary_parts.append("技术领域分布较为多样化")
            elif total_domains > 2:
                summary_parts.append("技术领域相对集中")
            else:
                summary_parts.append("技术领域高度集中")
            
            return "，".join(summary_parts) if summary_parts else "分类信息不足"
            
        except Exception as e:
            self.logger.error(f"Error generating classification summary: {str(e)}")
            return "分类总结生成失败"