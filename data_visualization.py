#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据可视化模块（纯 tkinter Canvas 版，无需 matplotlib）
功能：朝代分布、诗人排行、意象词频、诗体分布
"""

import tkinter as tk
from tkinter import ttk
import logging
from collections import Counter

from tk_charts import make_bar_chart, make_pie_chart

log = logging.getLogger("poetry")

# 古典意象词库（用于词频统计）
IMAGERY_WORDS = [
    '明月', '春风', '秋风', '白云', '青山', '流水', '桃花', '杨柳',
    '江南', '长安', '故乡', '相思', '孤舟', '寒江', '斜阳', '黄昏',
    '梅花', '鸿雁', '沧海', '天涯', '归去', '断肠', '烟雨',
    '落花', '浮云', '松柏', '芙蓉', '琵琶', '西楼', '东篱', '南山',
]


class ChartManager:
    """图表管理器（tkinter Canvas 引擎）"""
    
    def __init__(self, db, theme_colors=None):
        self.db = db
        self.theme_colors = theme_colors or {}
    
    def _query(self, sql, params=()):
        """执行查询"""
        try:
            if not self.db or not self.db.conn:
                return []
            cursor = self.db.conn.cursor()
            cursor.execute(sql, params)
            return cursor.fetchall()
        except Exception as e:
            log.error(f"查询失败: {e}")
            return []
    
    def create_dynasty_chart(self, parent):
        """朝代分布（饼图）"""
        rows = self._query('''
            SELECT dynasty, COUNT(*) as cnt FROM poems 
            WHERE dynasty != '' GROUP BY dynasty ORDER BY cnt DESC
        ''')
        
        if not rows:
            return None
        
        # TOP 8 + 其他
        data = [(r[0], r[1]) for r in rows[:8]]
        other = sum(r[1] for r in rows[8:])
        if other > 0:
            data.append(('其他', other))
        
        chart = make_pie_chart(parent, self.theme_colors)
        chart.draw(data, '朝代分布')
        return chart
    
    def create_author_chart(self, parent, top_n=20):
        """诗人排行（条形图）"""
        rows = self._query('''
            SELECT author, COUNT(*) as cnt FROM poems 
            WHERE author != '' GROUP BY author ORDER BY cnt DESC LIMIT ?
        ''', (top_n,))
        
        if not rows:
            return None
        
        data = [(r[0], r[1]) for r in rows]
        chart = make_bar_chart(parent, self.theme_colors)
        chart.draw(data, f'诗人作品数 TOP {top_n}')
        return chart
    
    def create_keyword_chart(self, parent, top_n=15):
        """意象词频（采样统计 + 条形图）"""
        # 随机采样 8000 首
        rows = self._query('SELECT content FROM poems ORDER BY RANDOM() LIMIT 8000')
        
        if not rows:
            return None
        
        counter = Counter()
        for row in rows:
            text = row[0] if row else ''
            if not text:
                continue
            for w in IMAGERY_WORDS:
                if w in text:
                    counter[w] += 1
        
        data = counter.most_common(top_n)
        if not data:
            return None
        chart = make_bar_chart(parent, self.theme_colors)
        chart.draw(data, f'古典意象词频 TOP {top_n}（采样 8000 首）')
        return chart
    
    def create_rhyme_chart(self, parent):
        """诗体分布（饼图）"""
        rows = self._query('''
            SELECT poem_form, COUNT(*) as cnt FROM poems 
            WHERE poem_form != '' AND poem_form != '杂言'
            GROUP BY poem_form ORDER BY cnt DESC LIMIT 8
        ''')
        
        if not rows:
            return None
        
        data = [(r[0], r[1]) for r in rows]
        chart = make_pie_chart(parent, self.theme_colors)
        chart.draw(data, '诗体分布')
        return chart


class VisualizationDialog:
    """数据可视化对话框"""
    
    def __init__(self, parent, db, chart_manager, theme_colors):
        self.parent = parent
        self.db = db
        self.chart_manager = chart_manager
        self.theme_colors = theme_colors or {}
        
        # 确保 chart_manager 有主题色和最新db
        if chart_manager:
            if not getattr(chart_manager, 'theme_colors', None):
                chart_manager.theme_colors = self.theme_colors
            chart_manager.db = db
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("数据可视化")
        self.dialog.geometry("900x680")
        self.dialog.resizable(True, True)
        self.dialog.configure(background=self.theme_colors.get('bg', '#F7F3E8'))
        self.dialog.transient(parent)
        
        # 创建界面
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        colors = self.theme_colors
        bg = colors.get('bg', '#F7F3E8')
        bg_card = colors.get('bg_card', '#FDFAF2')
        
        main_frame = tk.Frame(self.dialog, bg=bg)
        main_frame.pack(fill='both', expand=True, padx=16, pady=16)
        
        # 标题
        tk.Label(main_frame, text="📊 数据可视化", 
                font=('华文中宋', 16, 'bold'),
                bg=bg, fg=colors.get('fg', '#2B2B2B')).pack(pady=(0, 12))
        
        # 选项卡
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)
        
        # 依次创建各选项卡
        tabs = [
            ('朝代分布', 'create_dynasty_chart'),
            ('诗人排行', 'create_author_chart'),
            ('意象词频', 'create_keyword_chart'),
            ('诗体分布', 'create_rhyme_chart'),
        ]
        
        for title, method_name in tabs:
            frame = tk.Frame(notebook, bg=bg_card)
            notebook.add(frame, text=title)
            
            create_fn = getattr(self.chart_manager, method_name, None) if self.chart_manager else None
            
            if create_fn is None:
                tk.Label(frame, text="模块未加载", 
                        bg=bg_card, fg=colors.get('fg_secondary', '#6B6355'),
                        font=('微软雅黑', 11)).pack(expand=True)
                continue
            
            try:
                chart = create_fn(frame)
                if chart:
                    widget = chart.get_tk_widget()
                    widget.pack(fill='both', expand=True)
                else:
                    tk.Label(frame, text="暂无数据", 
                            bg=bg_card, fg=colors.get('fg_secondary', '#6B6355'),
                            font=('微软雅黑', 11)).pack(expand=True)
            except Exception as e:
                log.error(f"创建图表失败: {e}")
                tk.Label(frame, text=f"图表创建失败: {e}", 
                        bg=bg_card, fg=colors.get('accent', '#8C2F39'),
                        font=('微软雅黑', 10)).pack(expand=True)
