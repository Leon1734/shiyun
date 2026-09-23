#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古典雅致 UI 主题系统 v2
- 宣纸/墨色双主题（中国古典配色）
- 楷体/宋体/华文中宋 字体体系
- ttk Style 全局美化
"""

import tkinter as tk
from tkinter import ttk, font as tkfont
import logging

log = logging.getLogger("poetry")


# ── 字体体系 ──────────────────────────────────────────────────────────────

def _font_available(name):
    """检查字体是否可用"""
    try:
        available = tkfont.families()
        return name in available
    except:
        return False


def get_fonts():
    """获取字体配置（带回退）"""
    # 诗词正文：楷体优先
    poem_font = '楷体' if _font_available('楷体') else ('华文楷体' if _font_available('华文楷体') else '微软雅黑')
    # 标题：中宋/宋体优先
    title_font = '华文中宋' if _font_available('华文中宋') else ('宋体' if _font_available('宋体') else '微软雅黑')
    # UI：雅黑
    ui_font = '微软雅黑' if _font_available('微软雅黑') else 'SimHei'
    # 古文：仿宋/楷体
    prose_font = '仿宋' if _font_available('仿宋') else poem_font

    return {
        'poem': (poem_font, 16),
        'poem_large': (poem_font, 20),
        'poem_small': (poem_font, 13),
        'title': (title_font, 20, 'bold'),
        'title_small': (title_font, 14, 'bold'),
        'ui': (ui_font, 10),
        'ui_small': (ui_font, 9),
        'ui_bold': (ui_font, 10, 'bold'),
        'ui_large': (ui_font, 12, 'bold'),
        'prose': (prose_font, 13),
        'pinyin': ('Arial', 10),
    }


# ── 主题配色 ──────────────────────────────────────────────────────────────

THEMES_V2 = {
    "paper": {
        # 宣纸主题 - 温润典雅
        "bg":           "#F7F3E8",   # 宣纸底
        "bg_secondary": "#F0EAD8",   # 浅宣纸
        "bg_card":      "#FDFAF2",   # 卡片
        "bg_tertiary":  "#E8E0CC",   # 深一档
        "fg":           "#2B2B2B",   # 墨色
        "fg_secondary": "#6B6355",   # 淡墨
        "fg_muted":     "#9C9484",   # 极淡
        "accent":       "#8C2F39",   # 朱砂红
        "accent_hover": "#A84450",
        "accent_soft":  "#F5E6E8",   # 淡朱砂底
        "gold":         "#B8860B",   # 赭金
        "ink_blue":     "#4A5D6B",   # 黛青
        "success":      "#5C7A52",
        "warning":      "#B8860B",
        "error":        "#8C2F39",
        "border":       "#D8CDB0",
        "border_soft":  "#E8E0CC",
        "select_bg":    "#EDE4D0",
        "select_fg":    "#2B2B2B",
        "button_bg":    "#EFE8D5",
        "button_fg":    "#4A4235",
        "button_active": "#E2D8BE",
        "entry_bg":     "#FDFAF2",
        "entry_fg":     "#2B2B2B",
        "scrollbar":    "#C9BFA5",
        "tooltip_bg":   "#4A4235",
        "tooltip_fg":   "#F7F3E8",
        "tree_stripe":  "#F3EDDC",   # 斑马纹
        "highlight":    "#F5E6E8",
    },
    "ink": {
        # 墨色主题 - 深夜书房
        "bg":           "#1A1D24",
        "bg_secondary": "#232830",
        "bg_card":      "#2A3038",
        "bg_tertiary":  "#333A44",
        "fg":           "#E8E0D0",
        "fg_secondary": "#A89F8C",
        "fg_muted":     "#6E6758",
        "accent":       "#D4A843",   # 金
        "accent_hover": "#E0B85C",
        "accent_soft":  "#3A3428",
        "gold":         "#D4A843",
        "ink_blue":     "#7FA3B8",
        "success":      "#8FBC8F",
        "warning":      "#D4A843",
        "error":        "#C97B84",
        "border":       "#3A4148",
        "border_soft":  "#2E353D",
        "select_bg":    "#3A4148",
        "select_fg":    "#E8E0D0",
        "button_bg":    "#2E353D",
        "button_fg":    "#D8D0C0",
        "button_active": "#3A4148",
        "entry_bg":     "#232830",
        "entry_fg":     "#E8E0D0",
        "scrollbar":    "#4A5258",
        "tooltip_bg":   "#3A4148",
        "tooltip_fg":   "#E8E0D0",
        "tree_stripe":  "#20252C",
        "highlight":    "#3A3428",
    }
}

# 兼容旧主题名
THEMES_V2["light"] = THEMES_V2["paper"]
THEMES_V2["dark"] = THEMES_V2["ink"]


# ── ttk Style 配置 ────────────────────────────────────────────────────────

def apply_theme(root, theme_name="paper"):
    """应用主题到整个应用"""
    colors = THEMES_V2.get(theme_name, THEMES_V2["paper"])
    fonts = get_fonts()
    
    style = ttk.Style(root)
    
    # 尝试使用 clam 主题（可定制性最好）
    try:
        style.theme_use('clam')
    except:
        pass
    
    # 全局默认
    root.configure(bg=colors['bg'])
    style.configure('.',
        background=colors['bg'],
        foreground=colors['fg'],
        fieldbackground=colors['entry_bg'],
        borderwidth=0,
        focuscolor=colors['accent'],
    )
    
    # Frame
    style.configure('TFrame', background=colors['bg'])
    style.configure('Card.TFrame', background=colors['bg_card'])
    style.configure('Secondary.TFrame', background=colors['bg_secondary'])
    
    # Label
    style.configure('TLabel', background=colors['bg'], foreground=colors['fg'], font=fonts['ui'])
    style.configure('Title.TLabel', background=colors['bg'], foreground=colors['fg'], font=fonts['title'])
    style.configure('Subtitle.TLabel', background=colors['bg'], foreground=colors['fg_secondary'], font=fonts['ui'])
    style.configure('Muted.TLabel', background=colors['bg'], foreground=colors['fg_muted'], font=fonts['ui_small'])
    style.configure('Accent.TLabel', background=colors['bg'], foreground=colors['accent'], font=fonts['ui_bold'])
    style.configure('Card.TLabel', background=colors['bg_card'], foreground=colors['fg'], font=fonts['ui'])
    style.configure('PoemTitle.TLabel', background=colors['bg_card'], foreground=colors['fg'], font=fonts['title'])
    style.configure('PoemAuthor.TLabel', background=colors['bg_card'], foreground=colors['fg_secondary'], font=fonts['ui'])
    style.configure('CardTitle.TLabel', background=colors['bg_card'], foreground=colors['fg'], font=fonts['ui_large'])
    
    # Button - 主按钮
    style.configure('TButton',
        background=colors['button_bg'],
        foreground=colors['button_fg'],
        font=fonts['ui'],
        borderwidth=0,
        focusthickness=0,
        padding=(12, 6),
        relief='flat',
    )
    style.map('TButton',
        background=[('active', colors['button_active']), ('pressed', colors['accent'])],
        foreground=[('pressed', '#FFFFFF')],
    )
    
    # 强调按钮
    style.configure('Accent.TButton',
        background=colors['accent'],
        foreground='#FFFFFF',
        font=fonts['ui_bold'],
        padding=(14, 7),
    )
    style.map('Accent.TButton',
        background=[('active', colors['accent_hover']), ('pressed', colors['accent'])],
    )
    
    # 幽灵按钮（工具栏）
    style.configure('Ghost.TButton',
        background=colors['bg'],
        foreground=colors['fg_secondary'],
        font=fonts['ui'],
        padding=(10, 5),
    )
    style.map('Ghost.TButton',
        background=[('active', colors['bg_secondary'])],
        foreground=[('active', colors['accent'])],
    )
    
    # Entry
    style.configure('TEntry',
        fieldbackground=colors['entry_bg'],
        foreground=colors['entry_fg'],
        insertcolor=colors['fg'],
        bordercolor=colors['border'],
        lightcolor=colors['border'],
        darkcolor=colors['border'],
        padding=6,
    )
    style.map('TEntry',
        bordercolor=[('focus', colors['accent'])],
    )
    
    # Combobox
    style.configure('TCombobox',
        fieldbackground=colors['entry_bg'],
        background=colors['button_bg'],
        foreground=colors['entry_fg'],
        arrowcolor=colors['fg_secondary'],
        bordercolor=colors['border'],
        padding=4,
    )
    style.map('TCombobox',
        fieldbackground=[('readonly', colors['entry_bg'])],
        bordercolor=[('focus', colors['accent'])],
        selectbackground=[('readonly', colors['entry_bg'])],
        selectforeground=[('readonly', colors['entry_fg'])],
    )
    
    # Treeview
    style.configure('Treeview',
        background=colors['bg_card'],
        foreground=colors['fg'],
        fieldbackground=colors['bg_card'],
        font=fonts['ui_small'],
        rowheight=26,
        borderwidth=0,
    )
    style.map('Treeview',
        background=[('selected', colors['select_bg'])],
        foreground=[('selected', colors['select_fg'])],
    )
    style.configure('Treeview.Heading',
        background=colors['bg_secondary'],
        foreground=colors['fg_secondary'],
        font=fonts['ui_bold'],
        relief='flat',
        padding=4,
    )
    style.map('Treeview.Heading',
        background=[('active', colors['bg_tertiary'])],
    )
    
    # Notebook
    style.configure('TNotebook',
        background=colors['bg'],
        bordercolor=colors['border'],
        tabmargins=(2, 4, 2, 0),
    )
    style.configure('TNotebook.Tab',
        background=colors['bg_secondary'],
        foreground=colors['fg_secondary'],
        font=fonts['ui'],
        padding=(16, 8),
        borderwidth=0,
    )
    style.map('TNotebook.Tab',
        background=[('selected', colors['bg_card'])],
        foreground=[('selected', colors['accent'])],
        expand=[('selected', (0, 0, 0, 2))],
    )
    
    # LabelFrame
    style.configure('TLabelframe',
        background=colors['bg_card'],
        bordercolor=colors['border'],
        borderwidth=1,
        relief='solid',
    )
    style.configure('TLabelframe.Label',
        background=colors['bg_card'],
        foreground=colors['accent'],
        font=fonts['ui_bold'],
    )
    
    # Scrollbar
    style.configure('TScrollbar',
        background=colors['scrollbar'],
        troughcolor=colors['bg_secondary'],
        bordercolor=colors['bg_secondary'],
        arrowcolor=colors['fg_secondary'],
        relief='flat',
    )
    style.map('TScrollbar',
        background=[('active', colors['accent'])],
    )
    
    # Separator
    style.configure('TSeparator', background=colors['border'])
    
    # PanedWindow
    style.configure('TPanedwindow', background=colors['bg'])
    
    # Radiobutton / Checkbutton
    style.configure('TRadiobutton', background=colors['bg'], foreground=colors['fg'], font=fonts['ui'])
    style.configure('TCheckbutton', background=colors['bg'], foreground=colors['fg'], font=fonts['ui'])
    
    return colors, fonts


def make_tooltip(widget, text, colors):
    """创建提示气泡"""
    def enter(event):
        tip = tk.Toplevel(widget)
        tip.wm_overrideredirect(True)
        tip.wm_geometry(f"+{widget.winfo_rootx() + 20}+{widget.winfo_rooty() + widget.winfo_height() + 5}")
        label = tk.Label(tip, text=text, background=colors.get('tooltip_bg', '#333'),
                        foreground=colors.get('tooltip_fg', '#fff'),
                        font=('微软雅黑', 9), padx=8, pady=4)
        label.pack()
        widget._tooltip = tip
    
    def leave(event):
        if hasattr(widget, '_tooltip'):
            widget._tooltip.destroy()
            del widget._tooltip
    
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


class PoemCard(tk.Frame):
    """诗词卡片组件 - 圆角效果模拟"""
    
    def __init__(self, parent, colors, fonts, **kwargs):
        super().__init__(parent, bg=colors['border_soft'], **kwargs)
        self.colors = colors
        self.fonts = fonts
        
        # 内层（模拟边框）
        self.inner = tk.Frame(self, bg=colors['bg_card'])
        self.inner.pack(fill='both', expand=True, padx=1, pady=1)
    
    def get_inner(self):
        return self.inner


if __name__ == "__main__":
    # 测试主题
    root = tk.Tk()
    root.title("主题测试")
    root.geometry("600x400")
    
    colors, fonts = apply_theme(root, "paper")
    print(f"主题色: {colors['bg']} / {colors['accent']}")
    print(f"字体: {fonts['poem']}")
    
    frame = ttk.Frame(root, padding=20)
    frame.pack(fill='both', expand=True)
    
    ttk.Label(frame, text="静夜思", style='Title.TLabel').pack()
    ttk.Label(frame, text="· 李白 (唐)", style='Subtitle.TLabel').pack()
    ttk.Label(frame, text="床前明月光，疑是地上霜。\n举头望明月，低头思故乡。", 
             font=fonts['poem']).pack(pady=20)
    
    ttk.Button(frame, text="随机", style='Accent.TButton').pack()
    ttk.Button(frame, text="普通按钮").pack(pady=5)
    
    root.mainloop()
