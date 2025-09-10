"""Chart style configurations for patent reports."""

from typing import Dict, Any, List


class ChartStyleConfig:
    """图表样式配置类."""
    
    # 默认颜色调色板
    DEFAULT_COLORS = [
        "#007acc",  # 蓝色
        "#28a745",  # 绿色
        "#ffc107",  # 黄色
        "#dc3545",  # 红色
        "#6f42c1",  # 紫色
        "#fd7e14",  # 橙色
        "#20c997",  # 青色
        "#e83e8c",  # 粉色
        "#6c757d",  # 灰色
        "#17a2b8"   # 蓝绿色
    ]
    
    # 专业颜色调色板
    PROFESSIONAL_COLORS = [
        "#2E86AB",  # 深蓝
        "#A23B72",  # 深粉
        "#F18F01",  # 橙色
        "#C73E1D",  # 深红
        "#592E83",  # 深紫
        "#1B998B",  # 青绿
        "#84A59D",  # 灰绿
        "#F5E960",  # 亮黄
        "#ED254E",  # 亮红
        "#011936"   # 深蓝黑
    ]
    
    # 温和颜色调色板
    SOFT_COLORS = [
        "#A8DADC",  # 浅蓝绿
        "#457B9D",  # 中蓝
        "#1D3557",  # 深蓝
        "#F1FAEE",  # 浅白
        "#E63946",  # 红色
        "#FFB3BA",  # 浅粉
        "#FFDFBA",  # 浅橙
        "#FFFFBA",  # 浅黄
        "#BAFFC9",  # 浅绿
        "#BAE1FF"   # 浅蓝
    ]
    
    @classmethod
    def get_style_config(cls, style_name: str = "default") -> Dict[str, Any]:
        """获取样式配置."""
        styles = {
            "default": {
                "colors": cls.DEFAULT_COLORS,
                "font_family": "Microsoft YaHei",
                "font_size": 12,
                "title_size": 16,
                "grid_alpha": 0.3,
                "figure_size": (10, 6),
                "dpi": 100
            },
            "professional": {
                "colors": cls.PROFESSIONAL_COLORS,
                "font_family": "Arial",
                "font_size": 11,
                "title_size": 14,
                "grid_alpha": 0.2,
                "figure_size": (12, 7),
                "dpi": 150
            },
            "soft": {
                "colors": cls.SOFT_COLORS,
                "font_family": "Microsoft YaHei",
                "font_size": 12,
                "title_size": 15,
                "grid_alpha": 0.4,
                "figure_size": (10, 6),
                "dpi": 100
            },
            "presentation": {
                "colors": cls.DEFAULT_COLORS,
                "font_family": "Microsoft YaHei",
                "font_size": 14,
                "title_size": 18,
                "grid_alpha": 0.3,
                "figure_size": (14, 8),
                "dpi": 150
            }
        }
        
        return styles.get(style_name, styles["default"])
    
    @classmethod
    def get_chart_specific_config(cls, chart_type: str) -> Dict[str, Any]:
        """获取特定图表类型的配置."""
        configs = {
            "line": {
                "marker_size": 6,
                "line_width": 2,
                "marker_style": "o",
                "grid": True
            },
            "pie": {
                "start_angle": 90,
                "autopct": "%1.1f%%",
                "explode_max": 0.1,
                "shadow": False
            },
            "bar": {
                "bar_width": 0.8,
                "edge_color": "white",
                "edge_width": 0.7,
                "alpha": 0.8,
                "show_values": True
            },
            "scatter": {
                "marker_size": 50,
                "alpha": 0.7,
                "edge_colors": "black",
                "edge_width": 0.5
            }
        }
        
        return configs.get(chart_type, {})
    
    @classmethod
    def get_language_config(cls, language: str = "zh") -> Dict[str, Any]:
        """获取语言相关配置."""
        configs = {
            "zh": {
                "font_family": "Microsoft YaHei",
                "unicode_minus": False,
                "default_labels": {
                    "year": "年份",
                    "count": "数量",
                    "percentage": "百分比",
                    "applicant": "申请人",
                    "technology": "技术分类",
                    "country": "国家/地区"
                }
            },
            "en": {
                "font_family": "Arial",
                "unicode_minus": True,
                "default_labels": {
                    "year": "Year",
                    "count": "Count",
                    "percentage": "Percentage",
                    "applicant": "Applicant",
                    "technology": "Technology",
                    "country": "Country/Region"
                }
            }
        }
        
        return configs.get(language, configs["zh"])


class ChartTemplates:
    """图表模板类."""
    
    @staticmethod
    def get_trend_chart_template() -> Dict[str, Any]:
        """获取趋势图表模板."""
        return {
            "type": "line",
            "title": "专利申请趋势",
            "x_label": "年份",
            "y_label": "申请数量",
            "show_grid": True,
            "show_markers": True,
            "show_values": False
        }
    
    @staticmethod
    def get_competition_chart_template() -> Dict[str, Any]:
        """获取竞争分析图表模板."""
        return {
            "type": "pie",
            "title": "主要申请人分布",
            "show_legend": True,
            "show_percentages": True,
            "explode_largest": True
        }
    
    @staticmethod
    def get_technology_chart_template() -> Dict[str, Any]:
        """获取技术分类图表模板."""
        return {
            "type": "bar",
            "title": "技术分类分布",
            "x_label": "技术分类",
            "y_label": "专利数量",
            "show_values": True,
            "horizontal": False
        }
    
    @staticmethod
    def get_geographic_chart_template() -> Dict[str, Any]:
        """获取地域分布图表模板."""
        return {
            "type": "bar",
            "title": "地域分布",
            "x_label": "国家/地区",
            "y_label": "专利数量",
            "show_values": True,
            "horizontal": True
        }