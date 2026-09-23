#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轻量图表引擎（纯 tkinter Canvas，无需 matplotlib）
- 横向条形图（诗人排行、词频）
- 饼图（朝代分布、韵脚分布）
- 适配器：Widget.get_tk_widget() 兼容原 matplotlib 调用
"""

import tkinter as tk
from tkinter import ttk

# 古典配色（宣纸主题）
PALETTE = ['#8C2F39', '#B5651D', '#6B7B3A', '#3A5F8C', '#8A6EAB',
           '#C17F59', '#4A7C6F', '#A0522D', '#7D6B5D', '#5C4B8A']
PALETTE_DARK = ['#D4A843', '#C77B4C', '#8FA05E', '#6E9BC5', '#A88BC7',
                '#D9A06B', '#6FAF9F', '#C97B4A', '#A89888', '#8C7BB5']


class ChartFrame(tk.Frame):
    """图表容器（兼容 matplotlib 的 get_tk_widget 接口）"""
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._canvas = None

    def get_tk_widget(self):
        return self


class BarChart(ChartFrame):
    """横向条形图"""
    
    def __init__(self, parent, bg='#FDFAF2', fg='#2B2B2B', fg_secondary='#6B6355', 
                 accent='#8C2F39', dark=False, **kw):
        super().__init__(parent, bg=bg, **kw)
        self.bg = bg
        self.fg = fg
        self.fg_secondary = fg_secondary
        self.accent = accent
        self.palette = PALETTE_DARK if dark else PALETTE
        self._data = []
        self._title = ''
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._canvas.pack(fill='both', expand=True)
        self._canvas.bind('<Configure>', lambda e: self._redraw())
    
    def draw(self, data, title=''):
        """data: [(label, value), ...]"""
        self._data = data
        self._title = title
        self._redraw()
        return self
    
    def _redraw(self):
        c = self._canvas
        if not c.winfo_exists():
            return
        c.delete('all')
        
        w = c.winfo_width() or 600
        h = c.winfo_height() or 400
        if w < 50 or h < 50:
            return
        
        if not self._data:
            c.create_text(w//2, h//2, text='暂无数据', fill=self.fg_secondary, 
                         font=('微软雅黑', 12))
            return
        
        # 布局
        pad_top = 50 if self._title else 20
        pad_left = 130
        pad_right = 80
        pad_bottom = 15
        row_h = min(34, (h - pad_top - pad_bottom) / len(self._data))
        bar_h = row_h * 0.62
        
        max_val = max(v for _, v in self._data) or 1
        
        if self._title:
            c.create_text(w//2, 24, text=self._title, fill=self.fg,
                         font=('华文中宋', 15, 'bold'))
        
        for i, (label, value) in enumerate(self._data):
            y = pad_top + i * row_h + row_h / 2
            bar_w = (w - pad_left - pad_right) * (value / max_val)
            
            # 标签（右侧对齐）
            c.create_text(pad_left - 10, y, text=label, anchor='e',
                         fill=self.fg, font=('微软雅黑', 10))
            
            # 条形
            color = self.palette[i % len(self.palette)]
            c.create_rectangle(pad_left, y - bar_h/2, pad_left + bar_w, y + bar_h/2,
                              fill=color, outline='')
            
            # 数值
            c.create_text(pad_left + bar_w + 8, y, text=f'{value:,}', anchor='w',
                         fill=self.fg_secondary, font=('微软雅黑', 9))


class PieChart(ChartFrame):
    """饼图 + 图例"""
    
    def __init__(self, parent, bg='#FDFAF2', fg='#2B2B2B', fg_secondary='#6B6355',
                 accent='#8C2F39', dark=False, **kw):
        super().__init__(parent, bg=bg, **kw)
        self.bg = bg
        self.fg = fg
        self.fg_secondary = fg_secondary
        self.palette = PALETTE_DARK if dark else PALETTE
        self._data = []
        self._title = ''
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self._canvas.pack(fill='both', expand=True)
        self._canvas.bind('<Configure>', lambda e: self._redraw())
    
    def draw(self, data, title=''):
        self._data = data
        self._title = title
        self._redraw()
        return self
    
    def _redraw(self):
        c = self._canvas
        if not c.winfo_exists():
            return
        c.delete('all')
        
        w = c.winfo_width() or 600
        h = c.winfo_height() or 400
        if w < 50 or h < 50:
            return
        
        if not self._data:
            c.create_text(w//2, h//2, text='暂无数据', fill=self.fg_secondary,
                         font=('微软雅黑', 12))
            return
        
        if self._title:
            c.create_text(w//2, 24, text=self._title, fill=self.fg,
                         font=('华文中宋', 15, 'bold'))
        
        # 饼图区域（左侧60%）
        cx = w * 0.30
        cy = h * 0.55
        r = min(w * 0.24, h * 0.36)
        
        total = sum(v for _, v in self._data) or 1
        start = 90.0
        
        for i, (label, value) in enumerate(self._data):
            extent = -(value / total) * 360.0
            color = self.palette[i % len(self.palette)]
            if abs(extent) > 0.1:
                c.create_arc(cx - r, cy - r, cx + r, cy + r,
                            start=start, extent=extent, fill=color, outline=self.bg,
                            width=2)
            start += extent
        
        # 中心孔（环形效果）
        hole = r * 0.42
        c.create_oval(cx - hole, cy - hole, cx + hole, cy + hole,
                     fill=self.bg, outline='')
        
        # 图例（右侧40%）
        lx = w * 0.60
        ly = max(60, cy - len(self._data) * 13)
        for i, (label, value) in enumerate(self._data):
            y = ly + i * 26
            color = self.palette[i % len(self.palette)]
            c.create_rectangle(lx, y - 6, lx + 14, y + 6, fill=color, outline='')
            pct = value / total * 100
            c.create_text(lx + 22, y, text=f'{label}  {value:,} ({pct:.1f}%)',
                         anchor='w', fill=self.fg, font=('微软雅黑', 10))


def make_bar_chart(parent, theme_colors=None):
    """工厂：根据主题创建条形图"""
    tc = theme_colors or {}
    bg = tc.get('bg_card', '#FDFAF2')
    is_dark = bg.startswith('#1') or bg.startswith('#2') or bg.startswith('#0')
    return BarChart(parent, bg=bg,
                   fg=tc.get('fg', '#2B2B2B'),
                   fg_secondary=tc.get('fg_secondary', '#6B6355'),
                   accent=tc.get('accent', '#8C2F39'),
                   dark=is_dark)


def make_pie_chart(parent, theme_colors=None):
    """工厂：根据主题创建饼图"""
    tc = theme_colors or {}
    bg = tc.get('bg_card', '#FDFAF2')
    is_dark = bg.startswith('#1') or bg.startswith('#2') or bg.startswith('#0')
    return PieChart(parent, bg=bg,
                    fg=tc.get('fg', '#2B2B2B'),
                    fg_secondary=tc.get('fg_secondary', '#6B6355'),
                    accent=tc.get('accent', '#8C2F39'),
                    dark=is_dark)
