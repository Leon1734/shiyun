#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
名句欣赏窗口
- 名句卡片流
- 按作者筛选
- 朗读/复制/查看原诗
"""

import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
import logging

log = logging.getLogger("poetry")

try:
    from app_paths import get_db_path
    DB_PATH = get_db_path()
except ImportError:
    from pathlib import Path
    DB_PATH = Path(__file__).parent / "data" / "poetry.db"

try:
    from ui_theme_v2 import THEMES_V2, get_fonts
    HAS_THEME = True
except ImportError:
    HAS_THEME = False


class QuotesWindow(tk.Toplevel):
    """名句欣赏窗口"""
    
    def __init__(self, parent, on_poem_select=None):
        super().__init__(parent)
        self.title("💡 名句欣赏")
        self.geometry("860x680")
        
        self.on_poem_select = on_poem_select
        self.conn = None
        
        if HAS_THEME:
            self.colors = THEMES_V2['paper']
            self.fonts = get_fonts()
        else:
            self.colors = {
                'bg': '#F7F3E8', 'bg_card': '#FDFAF2', 'fg': '#2B2B2B',
                'fg_secondary': '#6B6355', 'accent': '#8C2F39',
                'border': '#D8CDB0', 'select_bg': '#EDE4D0',
            }
            self.fonts = {
                'poem': ('楷体', 16), 'title': ('华文中宋', 20, 'bold'),
                'ui': ('微软雅黑', 10), 'ui_small': ('微软雅黑', 9),
                'ui_bold': ('微软雅黑', 10, 'bold'), 'ui_large': ('微软雅黑', 12, 'bold'),
                'title_small': ('华文中宋', 14, 'bold'), 'pinyin': ('Arial', 10),
            }
        
        self.configure(bg=self.colors['bg'])
        
        self._init_db()
        self._create_widgets()
        self._load_quotes()
    
    def _init_db(self):
        try:
            self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            log.error(f"名句库连接失败: {e}")
    
    def _create_widgets(self):
        colors = self.colors
        fonts = self.fonts
        
        # 顶栏
        top = tk.Frame(self, bg=colors['bg'])
        top.pack(fill='x', padx=15, pady=10)
        
        tk.Label(top, text="💡 名句欣赏", font=fonts['title_small'],
                bg=colors['bg'], fg=colors['accent']).pack(side='left')
        
        # 作者筛选
        tk.Label(top, text="作者:", font=fonts['ui'],
                bg=colors['bg'], fg=colors['fg']).pack(side='left', padx=(20, 5))
        
        self.author_var = tk.StringVar(value='全部')
        self.author_combo = ttk.Combobox(top, textvariable=self.author_var, width=12, state='readonly')
        self.author_combo.pack(side='left')
        self.author_combo.bind('<<ComboboxSelected>>', lambda e: self._load_quotes())
        
        # 统计
        self.stats_label = tk.Label(top, text="", font=fonts['ui_small'],
                                     bg=colors['bg'], fg=colors['fg_secondary'])
        self.stats_label.pack(side='right')
        
        # 名句列表区（滚动）
        list_frame = tk.Frame(self, bg=colors['bg'])
        list_frame.pack(fill='both', expand=True, padx=15, pady=(0, 10))
        
        self.canvas = tk.Canvas(list_frame, bg=colors['bg'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.quotes_frame = tk.Frame(self.canvas, bg=colors['bg'])
        self.canvas_window = self.canvas.create_window((0, 0), window=self.quotes_frame, anchor='nw')
        
        self.canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 滚动绑定
        self.quotes_frame.bind('<Configure>', self._on_frame_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        self.canvas.bind_all('<MouseWheel>', self._on_mousewheel)
        
        # 底部
        bottom = tk.Frame(self, bg=colors['bg'])
        bottom.pack(fill='x', padx=15, pady=(0, 10))
        
        ttk.Button(bottom, text="🔄 换一批", command=self._load_quotes).pack(side='left')
        ttk.Button(bottom, text="关闭", command=self.destroy).pack(side='right')
    
    def _on_frame_configure(self, event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))
    
    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)
    
    def _on_mousewheel(self, event):
        try:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
        except:
            pass
    
    def _load_quotes(self):
        """加载名句"""
        if not self.conn:
            return
        
        # 清空
        for w in self.quotes_frame.winfo_children():
            w.destroy()
        
        try:
            cursor = self.conn.cursor()
            
            # 更新作者列表
            cursor.execute("SELECT DISTINCT author FROM quotes WHERE author != '' ORDER BY author")
            authors = ['全部'] + [r[0] for r in cursor.fetchall()]
            self.author_combo['values'] = authors
            
            # 查询
            author = self.author_var.get()
            if author != '全部':
                cursor.execute("SELECT * FROM quotes WHERE author = ? ORDER BY RANDOM() LIMIT 30", (author,))
            else:
                cursor.execute("SELECT * FROM quotes ORDER BY RANDOM() LIMIT 30")
            
            quotes = cursor.fetchall()
            self.stats_label.config(text=f"共 {len(quotes)} 条")
            
            # 渲染卡片
            for q in quotes:
                self._create_quote_card(q)
            
        except Exception as e:
            log.error(f"加载名句失败: {e}")
    
    def _create_quote_card(self, q):
        """创建名句卡片"""
        colors = self.colors
        fonts = self.fonts
        
        card = tk.Frame(self.quotes_frame, bg=colors['border'])
        card.pack(fill='x', pady=6)
        
        inner = tk.Frame(card, bg=colors['bg_card'])
        inner.pack(fill='x', padx=1, pady=1)
        
        # 名句文字
        text_label = tk.Label(inner, text=q['text'], font=fonts['poem'],
                              bg=colors['bg_card'], fg=colors['fg'],
                              wraplength=700, justify='left', anchor='w')
        text_label.pack(fill='x', padx=20, pady=(14, 6))
        
        # 出处行
        info = f"—— {q['author']}《{q['title']}》" if q['author'] else f"—— 《{q['title']}》"
        info_label = tk.Label(inner, text=info, font=fonts['ui_small'],
                              bg=colors['bg_card'], fg=colors['fg_secondary'], anchor='e')
        info_label.pack(fill='x', padx=20, pady=(0, 8))
        
        # 操作行
        btn_row = tk.Frame(inner, bg=colors['bg_card'])
        btn_row.pack(fill='x', padx=20, pady=(0, 12))
        
        def copy_quote(text=q['text'], author=q['author'], title=q['title']):
            self.clipboard_clear()
            self.clipboard_append(f"{text} —— {author}《{title}》")
            self.stats_label.config(text="已复制!")
        
        def view_poem(q=q):
            if self.on_poem_select and q['source_id']:
                self.on_poem_select(q['source_id'])
                self.destroy()
        
        def speak(q=q):
            try:
                from features_v7 import TTSEngine
                tts = TTSEngine()
                tts.speak_async(f"{q['text']}。{q['author']}")
            except Exception as e:
                log.error(f"朗读失败: {e}")
        
        for text, cmd in [("📋 复制", copy_quote), ("📜 看原诗", view_poem), ("🔊 朗读", speak)]:
            btn = tk.Label(btn_row, text=text, font=fonts['ui_small'],
                          bg=colors['bg_card'], fg=colors['accent'], cursor='hand2')
            btn.pack(side='left', padx=(0, 15))
            btn.bind('<Button-1>', lambda e, c=cmd: c())


if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    win = QuotesWindow(root)
    win.protocol("WM_DELETE_WINDOW", lambda: (win.destroy(), root.destroy()))
    root.mainloop()
