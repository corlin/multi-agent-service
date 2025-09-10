"""Patent chart generation system implementation."""

import asyncio
import logging
import os
import base64
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path

try:
    import matplotlib
    matplotlib.use('Agg')  # 使用非交互式后端
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    from matplotlib import rcParams
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.offline import plot
    import plotly.io as pio
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

import json


logger = logging.getLogger(__name__)


class ChartGenerator:
    """专利图表生成器，集成matplotlib和plotly."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化图表生成器."""
        self.config = config or {}
        
        # 图表配置
        self.chart_config = {
            "width": self.config.get("chart_width", 800),
            "height": self.config.get("chart_height", 600),
            "dpi": self.config.get("chart_dpi", 100),
            "format": self.config.get("chart_format", "png"),
            "style": self.config.get("chart_style", "default"),
            "color_palette": self.config.get("color_palette", [
                "#007acc", "#28a745", "#ffc107", "#dc3545", "#6f42c1",
                "#fd7e14", "#20c997", "#e83e8c", "#6c757d", "#17a2b8"
            ]),
            "font_family": self.config.get("font_family", "Microsoft YaHei"),
            "font_size": self.config.get("font_size", 12),
            "output_dir": self.config.get("output_dir", "charts/patent"),
            "cache_charts": self.config.get("cache_charts", True),
            "interactive": self.config.get("interactive", False)
        }
        
        # 确保输出目录存在
        self._ensure_output_directory()
        
        # 配置matplotlib
        self._configure_matplotlib()
        
        # 配置plotly
        self._configure_plotly()
        
        # 图表缓存
        self._chart_cache: Dict[str, Dict[str, Any]] = {}
        
        self.logger = logging.getLogger(f"{__name__}.ChartGenerator")
    
    def _ensure_output_directory(self):
        """确保输出目录存在."""
        try:
            output_dir = Path(self.chart_config["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Chart output directory: {output_dir}")
        except Exception as e:
            self.logger.error(f"Error creating output directory: {str(e)}")
    
    def _configure_matplotlib(self):
        """配置matplotlib."""
        if not MATPLOTLIB_AVAILABLE:
            self.logger.warning("Matplotlib not available, some chart types will be disabled")
            return
        
        try:
            # 设置中文字体
            plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
            plt.rcParams['axes.unicode_minus'] = False
            
            # 设置样式
            if self.chart_config["style"] in plt.style.available:
                plt.style.use(self.chart_config["style"])
            
            # 设置默认字体大小
            plt.rcParams['font.size'] = self.chart_config["font_size"]
            
            self.logger.info("Matplotlib configured successfully")
            
        except Exception as e:
            self.logger.error(f"Error configuring matplotlib: {str(e)}")
    
    def _configure_plotly(self):
        """配置plotly."""
        if not PLOTLY_AVAILABLE:
            self.logger.warning("Plotly not available, interactive charts will be disabled")
            return
        
        try:
            # 设置默认模板
            pio.templates.default = "plotly_white"
            
            # 设置中文字体
            pio.kaleido.scope.default_font = self.chart_config["font_family"]
            
            self.logger.info("Plotly configured successfully")
            
        except Exception as e:
            self.logger.error(f"Error configuring plotly: {str(e)}")
    
    async def generate_charts(self, analysis_data: Dict[str, Any], 
                            report_params: Dict[str, Any]) -> Dict[str, Any]:
        """生成所有图表."""
        try:
            charts = {}
            
            # 检查缓存
            cache_key = self._generate_cache_key(analysis_data, report_params)
            if self.chart_config["cache_charts"] and cache_key in self._chart_cache:
                self.logger.info("Returning cached charts")
                return self._chart_cache[cache_key]
            
            # 生成趋势图表
            if "trend" in analysis_data and "line" in report_params.get("chart_types", []):
                charts["trend_chart"] = await self._generate_trend_chart(
                    analysis_data["trend_analysis"]
                )
            
            # 生成竞争分析图表
            if "competition" in analysis_data and "pie" in report_params.get("chart_types", []):
                charts["competition_chart"] = await self._generate_competition_chart(
                    analysis_data["competition_analysis"]
                )
            
            # 生成技术分类图表
            if "technology" in analysis_data and "bar" in report_params.get("chart_types", []):
                charts["technology_chart"] = await self._generate_technology_chart(
                    analysis_data["technology_analysis"]
                )
            
            # 生成地域分布图表
            if "geographic" in analysis_data:
                charts["geographic_chart"] = await self._generate_geographic_chart(
                    analysis_data["geographic_analysis"]
                )
            
            # 缓存结果
            if self.chart_config["cache_charts"]:
                self._chart_cache[cache_key] = charts
            
            self.logger.info(f"Generated {len(charts)} charts successfully")
            return charts
            
        except Exception as e:
            self.logger.error(f"Error generating charts: {str(e)}")
            return {}
    
    async def _generate_trend_chart(self, trend_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成趋势图表."""
        try:
            yearly_counts = trend_data.get("yearly_counts", {})
            if not yearly_counts:
                return {"error": "No trend data available"}
            
            # 准备数据
            years = sorted(yearly_counts.keys())
            counts = [yearly_counts[year] for year in years]
            
            chart_info = {
                "type": "line",
                "title": "专利申请趋势",
                "data": {"years": years, "counts": counts}
            }
            
            # 使用matplotlib生成静态图表
            if MATPLOTLIB_AVAILABLE:
                static_path = await self._create_matplotlib_line_chart(
                    years, counts, "专利申请趋势", "年份", "申请数量"
                )
                chart_info["static_path"] = static_path
            
            # 使用plotly生成交互式图表
            if PLOTLY_AVAILABLE and self.chart_config["interactive"]:
                interactive_path = await self._create_plotly_line_chart(
                    years, counts, "专利申请趋势", "年份", "申请数量"
                )
                chart_info["interactive_path"] = interactive_path
            
            # 设置主要路径
            chart_info["path"] = chart_info.get("static_path") or chart_info.get("interactive_path")
            chart_info["size"] = self._get_file_size(chart_info["path"]) if chart_info["path"] else "0KB"
            
            return chart_info
            
        except Exception as e:
            self.logger.error(f"Error generating trend chart: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_competition_chart(self, competition_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成竞争分析图表."""
        try:
            applicant_distribution = competition_data.get("applicant_distribution", {})
            if not applicant_distribution:
                return {"error": "No competition data available"}
            
            # 准备数据（取前10个）
            sorted_applicants = sorted(
                applicant_distribution.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            labels = [item[0] for item in sorted_applicants]
            values = [item[1] for item in sorted_applicants]
            
            chart_info = {
                "type": "pie",
                "title": "主要申请人分布",
                "data": {"labels": labels, "values": values}
            }
            
            # 使用matplotlib生成静态图表
            if MATPLOTLIB_AVAILABLE:
                static_path = await self._create_matplotlib_pie_chart(
                    labels, values, "主要申请人分布"
                )
                chart_info["static_path"] = static_path
            
            # 使用plotly生成交互式图表
            if PLOTLY_AVAILABLE and self.chart_config["interactive"]:
                interactive_path = await self._create_plotly_pie_chart(
                    labels, values, "主要申请人分布"
                )
                chart_info["interactive_path"] = interactive_path
            
            # 设置主要路径
            chart_info["path"] = chart_info.get("static_path") or chart_info.get("interactive_path")
            chart_info["size"] = self._get_file_size(chart_info["path"]) if chart_info["path"] else "0KB"
            
            return chart_info
            
        except Exception as e:
            self.logger.error(f"Error generating competition chart: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_technology_chart(self, technology_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成技术分类图表."""
        try:
            ipc_distribution = technology_data.get("ipc_distribution", {})
            if not ipc_distribution:
                return {"error": "No technology data available"}
            
            # 准备数据（取前10个）
            sorted_ipc = sorted(
                ipc_distribution.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            categories = [item[0] for item in sorted_ipc]
            counts = [item[1] for item in sorted_ipc]
            
            chart_info = {
                "type": "bar",
                "title": "技术分类分布",
                "data": {"categories": categories, "counts": counts}
            }
            
            # 使用matplotlib生成静态图表
            if MATPLOTLIB_AVAILABLE:
                static_path = await self._create_matplotlib_bar_chart(
                    categories, counts, "技术分类分布", "IPC分类", "专利数量"
                )
                chart_info["static_path"] = static_path
            
            # 使用plotly生成交互式图表
            if PLOTLY_AVAILABLE and self.chart_config["interactive"]:
                interactive_path = await self._create_plotly_bar_chart(
                    categories, counts, "技术分类分布", "IPC分类", "专利数量"
                )
                chart_info["interactive_path"] = interactive_path
            
            # 设置主要路径
            chart_info["path"] = chart_info.get("static_path") or chart_info.get("interactive_path")
            chart_info["size"] = self._get_file_size(chart_info["path"]) if chart_info["path"] else "0KB"
            
            return chart_info
            
        except Exception as e:
            self.logger.error(f"Error generating technology chart: {str(e)}")
            return {"error": str(e)}
    
    async def _generate_geographic_chart(self, geographic_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成地域分布图表."""
        try:
            country_distribution = geographic_data.get("country_distribution", {})
            if not country_distribution:
                return {"error": "No geographic data available"}
            
            # 准备数据
            sorted_countries = sorted(
                country_distribution.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10]
            
            countries = [item[0] for item in sorted_countries]
            counts = [item[1] for item in sorted_countries]
            
            chart_info = {
                "type": "bar",
                "title": "地域分布",
                "data": {"countries": countries, "counts": counts}
            }
            
            # 使用matplotlib生成静态图表
            if MATPLOTLIB_AVAILABLE:
                static_path = await self._create_matplotlib_bar_chart(
                    countries, counts, "地域分布", "国家/地区", "专利数量"
                )
                chart_info["static_path"] = static_path
            
            # 设置主要路径
            chart_info["path"] = chart_info.get("static_path")
            chart_info["size"] = self._get_file_size(chart_info["path"]) if chart_info["path"] else "0KB"
            
            return chart_info
            
        except Exception as e:
            self.logger.error(f"Error generating geographic chart: {str(e)}")
            return {"error": str(e)}
    
    async def _create_matplotlib_line_chart(self, x_data: List, y_data: List, 
                                          title: str, x_label: str, y_label: str) -> str:
        """使用matplotlib创建折线图."""
        try:
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 绘制折线图
            ax.plot(x_data, y_data, marker='o', linewidth=2, markersize=6, 
                   color=self.chart_config["color_palette"][0])
            
            # 设置标题和标签
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
            
            # 设置网格
            ax.grid(True, alpha=0.3)
            
            # 旋转x轴标签（如果是年份）
            if len(str(x_data[0])) == 4:  # 年份
                plt.xticks(rotation=45)
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trend_chart_{timestamp}.{self.chart_config['format']}"
            filepath = Path(self.chart_config["output_dir"]) / filename
            
            plt.savefig(filepath, dpi=self.chart_config["dpi"], 
                       bbox_inches='tight', facecolor='white')
            plt.close()
            
            self.logger.info(f"Created matplotlib line chart: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error creating matplotlib line chart: {str(e)}")
            raise
    
    async def _create_matplotlib_pie_chart(self, labels: List[str], values: List[int], 
                                         title: str) -> str:
        """使用matplotlib创建饼图."""
        try:
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # 创建饼图
            colors = self.chart_config["color_palette"][:len(labels)]
            wedges, texts, autotexts = ax.pie(
                values, labels=labels, colors=colors, autopct='%1.1f%%',
                startangle=90, textprops={'fontsize': 10}
            )
            
            # 设置标题
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            
            # 调整标签位置
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
            
            # 添加图例
            ax.legend(wedges, labels, title="申请人", loc="center left", 
                     bbox_to_anchor=(1, 0, 0.5, 1))
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"competition_chart_{timestamp}.{self.chart_config['format']}"
            filepath = Path(self.chart_config["output_dir"]) / filename
            
            plt.savefig(filepath, dpi=self.chart_config["dpi"], 
                       bbox_inches='tight', facecolor='white')
            plt.close()
            
            self.logger.info(f"Created matplotlib pie chart: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error creating matplotlib pie chart: {str(e)}")
            raise
    
    async def _create_matplotlib_bar_chart(self, x_data: List, y_data: List, 
                                         title: str, x_label: str, y_label: str) -> str:
        """使用matplotlib创建柱状图."""
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # 创建柱状图
            bars = ax.bar(x_data, y_data, color=self.chart_config["color_palette"][0], 
                         alpha=0.8, edgecolor='white', linewidth=0.7)
            
            # 设置标题和标签
            ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
            ax.set_xlabel(x_label, fontsize=12)
            ax.set_ylabel(y_label, fontsize=12)
            
            # 在柱子上显示数值
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.5,
                       f'{int(height)}', ha='center', va='bottom', fontsize=10)
            
            # 设置网格
            ax.grid(True, alpha=0.3, axis='y')
            
            # 旋转x轴标签
            plt.xticks(rotation=45, ha='right')
            
            # 调整布局
            plt.tight_layout()
            
            # 保存图表
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bar_chart_{timestamp}.{self.chart_config['format']}"
            filepath = Path(self.chart_config["output_dir"]) / filename
            
            plt.savefig(filepath, dpi=self.chart_config["dpi"], 
                       bbox_inches='tight', facecolor='white')
            plt.close()
            
            self.logger.info(f"Created matplotlib bar chart: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error creating matplotlib bar chart: {str(e)}")
            raise
    
    async def _create_plotly_line_chart(self, x_data: List, y_data: List, 
                                      title: str, x_label: str, y_label: str) -> str:
        """使用plotly创建交互式折线图."""
        try:
            fig = go.Figure()
            
            # 添加折线
            fig.add_trace(go.Scatter(
                x=x_data,
                y=y_data,
                mode='lines+markers',
                name='专利申请量',
                line=dict(color=self.chart_config["color_palette"][0], width=3),
                marker=dict(size=8)
            ))
            
            # 设置布局
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=18)),
                xaxis_title=x_label,
                yaxis_title=y_label,
                font=dict(family=self.chart_config["font_family"], size=12),
                hovermode='x unified',
                width=self.chart_config["width"],
                height=self.chart_config["height"]
            )
            
            # 保存图表
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"trend_chart_interactive_{timestamp}.html"
            filepath = Path(self.chart_config["output_dir"]) / filename
            
            fig.write_html(str(filepath))
            
            self.logger.info(f"Created plotly line chart: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error creating plotly line chart: {str(e)}")
            raise
    
    async def _create_plotly_pie_chart(self, labels: List[str], values: List[int], 
                                     title: str) -> str:
        """使用plotly创建交互式饼图."""
        try:
            fig = go.Figure()
            
            # 添加饼图
            fig.add_trace(go.Pie(
                labels=labels,
                values=values,
                hole=0.3,  # 环形图
                textinfo='label+percent',
                textposition='outside',
                marker=dict(colors=self.chart_config["color_palette"][:len(labels)])
            ))
            
            # 设置布局
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=18)),
                font=dict(family=self.chart_config["font_family"], size=12),
                width=self.chart_config["width"],
                height=self.chart_config["height"]
            )
            
            # 保存图表
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"competition_chart_interactive_{timestamp}.html"
            filepath = Path(self.chart_config["output_dir"]) / filename
            
            fig.write_html(str(filepath))
            
            self.logger.info(f"Created plotly pie chart: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error creating plotly pie chart: {str(e)}")
            raise
    
    async def _create_plotly_bar_chart(self, x_data: List, y_data: List, 
                                     title: str, x_label: str, y_label: str) -> str:
        """使用plotly创建交互式柱状图."""
        try:
            fig = go.Figure()
            
            # 添加柱状图
            fig.add_trace(go.Bar(
                x=x_data,
                y=y_data,
                name='专利数量',
                marker=dict(color=self.chart_config["color_palette"][0]),
                text=y_data,
                textposition='outside'
            ))
            
            # 设置布局
            fig.update_layout(
                title=dict(text=title, x=0.5, font=dict(size=18)),
                xaxis_title=x_label,
                yaxis_title=y_label,
                font=dict(family=self.chart_config["font_family"], size=12),
                width=self.chart_config["width"],
                height=self.chart_config["height"]
            )
            
            # 保存图表
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"bar_chart_interactive_{timestamp}.html"
            filepath = Path(self.chart_config["output_dir"]) / filename
            
            fig.write_html(str(filepath))
            
            self.logger.info(f"Created plotly bar chart: {filepath}")
            return str(filepath)
            
        except Exception as e:
            self.logger.error(f"Error creating plotly bar chart: {str(e)}")
            raise
    
    def _generate_cache_key(self, analysis_data: Dict[str, Any], 
                          report_params: Dict[str, Any]) -> str:
        """生成图表缓存键."""
        try:
            # 创建数据摘要
            data_summary = {}
            
            if "trend_analysis" in analysis_data:
                trend_data = analysis_data["trend_analysis"]
                data_summary["trend"] = str(hash(str(trend_data.get("yearly_counts", {}))))
            
            if "competition_analysis" in analysis_data:
                comp_data = analysis_data["competition_analysis"]
                data_summary["competition"] = str(hash(str(comp_data.get("applicant_distribution", {}))))
            
            if "technology_analysis" in analysis_data:
                tech_data = analysis_data["technology_analysis"]
                data_summary["technology"] = str(hash(str(tech_data.get("ipc_distribution", {}))))
            
            # 创建参数摘要
            param_summary = {
                "chart_types": sorted(report_params.get("chart_types", [])),
                "interactive": self.chart_config["interactive"]
            }
            
            # 生成缓存键
            cache_key = f"charts_{hash(str(data_summary))}_{hash(str(param_summary))}"
            return cache_key
            
        except Exception as e:
            self.logger.error(f"Error generating cache key: {str(e)}")
            return f"charts_{datetime.now().timestamp()}"
    
    def _get_file_size(self, filepath: str) -> str:
        """获取文件大小."""
        try:
            if not filepath or not os.path.exists(filepath):
                return "0KB"
            
            size_bytes = os.path.getsize(filepath)
            
            if size_bytes < 1024:
                return f"{size_bytes}B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f}KB"
            else:
                return f"{size_bytes / (1024 * 1024):.1f}MB"
                
        except Exception as e:
            self.logger.error(f"Error getting file size: {str(e)}")
            return "Unknown"
    
    async def create_custom_chart(self, chart_type: str, data: Dict[str, Any], 
                                config: Dict[str, Any]) -> Dict[str, Any]:
        """创建自定义图表."""
        try:
            if chart_type == "line":
                return await self._create_matplotlib_line_chart(
                    data["x"], data["y"], 
                    config.get("title", ""), 
                    config.get("x_label", ""), 
                    config.get("y_label", "")
                )
            elif chart_type == "pie":
                return await self._create_matplotlib_pie_chart(
                    data["labels"], data["values"], 
                    config.get("title", "")
                )
            elif chart_type == "bar":
                return await self._create_matplotlib_bar_chart(
                    data["x"], data["y"], 
                    config.get("title", ""), 
                    config.get("x_label", ""), 
                    config.get("y_label", "")
                )
            else:
                raise ValueError(f"Unsupported chart type: {chart_type}")
                
        except Exception as e:
            self.logger.error(f"Error creating custom chart: {str(e)}")
            return {"error": str(e)}
    
    def get_supported_chart_types(self) -> List[str]:
        """获取支持的图表类型."""
        chart_types = []
        
        if MATPLOTLIB_AVAILABLE:
            chart_types.extend(["line", "pie", "bar", "scatter", "histogram"])
        
        if PLOTLY_AVAILABLE:
            chart_types.extend(["interactive_line", "interactive_pie", "interactive_bar"])
        
        return list(set(chart_types))
    
    def clear_cache(self):
        """清空图表缓存."""
        self._chart_cache.clear()
        self.logger.info("Chart cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """获取缓存信息."""
        return {
            "cache_size": len(self._chart_cache),
            "cache_enabled": self.chart_config["cache_charts"],
            "matplotlib_available": MATPLOTLIB_AVAILABLE,
            "plotly_available": PLOTLY_AVAILABLE
        }