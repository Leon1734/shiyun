#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v7.0 功能对话框
- 诗人档案窗口
- 词牌词典窗口
- 统一搜索窗口
"""

import tkinter as tk
from tkinter import ttk, messagebox
import logging

log = logging.getLogger("poetry")

# 主题
try:
    from ui_theme_v2 import THEMES_V2, get_fonts
    HAS_THEME_V2 = True
except ImportError:
    HAS_THEME_V2 = False

# 数据模块
try:
    from poet_profile import PoetProfile, generate_seal_avatar
    HAS_PROFILE = True
except ImportError:
    HAS_PROFILE = False

try:
    from cipai_dict import CIPAI_DICT, get_cipai_info, search_cipai, get_all_cipai
    HAS_CIPAI = True
except ImportError:
    HAS_CIPAI = False

try:
    from unified_search import UnifiedSearch
    HAS_UNIFIED = True
except ImportError:
    HAS_UNIFIED = False

try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


def _colors_fonts():
    """获取颜色和字体"""
    if HAS_THEME_V2:
        colors = THEMES_V2['paper']
        fonts = get_fonts()
    else:
        colors = {
            'bg': '#F7F3E8', 'bg_secondary': '#F0EAD8', 'bg_card': '#FDFAF2',
            'fg': '#2B2B2B', 'fg_secondary': '#6B6355', 'fg_muted': '#9C9484',
            'accent': '#8C2F39', 'border': '#D8CDB0', 'select_bg': '#EDE4D0',
        }
        fonts = {
            'poem': ('楷体', 16), 'title': ('华文中宋', 20, 'bold'),
            'ui': ('微软雅黑', 10), 'ui_small': ('微软雅黑', 9),
            'ui_bold': ('微软雅黑', 10, 'bold'), 'ui_large': ('微软雅黑', 12, 'bold'),
            'title_small': ('华文中宋', 14, 'bold'),
        }
    return colors, fonts


class PoetProfileWindow(tk.Toplevel):
    """诗人档案窗口"""
    
    def __init__(self, parent, author_name):
        super().__init__(parent)
        self.title(f"诗人档案 · {author_name}")
        self.geometry("780x640")
        
        self.author = author_name
        self.colors, self.fonts = _colors_fonts()
        
        self.configure(bg=self.colors['bg'])
        
        self.profile = None
        self._load_profile()
        self._create_widgets()
    
    def _load_profile(self):
        if HAS_PROFILE:
            prof = PoetProfile()
            self.profile = prof.get_profile(self.author)
    
    def _create_widgets(self):
        colors = self.colors
        fonts = self.fonts
        
        if not self.profile:
            ttk.Label(self, text=f"未找到 {self.author} 的档案", font=fonts['ui']).pack(pady=50)
            return
        
        p = self.profile
        
        # ── 顶部：印章头像 + 基本信息 ──
        top = tk.Frame(self, bg=colors['bg_card'])
        top.pack(fill='x', padx=15, pady=15)
        
        # 印章头像
        if HAS_PIL:
            try:
                seal_img = generate_seal_avatar(self.author, size=100)
                if seal_img:
                    self.seal_photo = ImageTk.PhotoImage(seal_img)
                    seal_label = tk.Label(top, image=self.seal_photo, bg=colors['bg_card'])
                    seal_label.pack(side='left', padx=(20, 15), pady=15)
            except Exception as e:
                log.debug(f"印章生成失败: {e}")
        
        info_frame = tk.Frame(top, bg=colors['bg_card'])
        info_frame.pack(side='left', fill='both', expand=True, pady=15)
        
        tk.Label(info_frame, text=p['author'], font=fonts['title'],
                bg=colors['bg_card'], fg=colors['fg']).pack(anchor='w')
        
        sub = f"{p['dynasty']} · 作品 {p['total']:,} 首"
        tk.Label(info_frame, text=sub, font=fonts['ui'],
                bg=colors['bg_card'], fg=colors['fg_secondary']).pack(anchor='w', pady=2)
        
        # 合集标签
        coll_text = ' · '.join(f"{c}({n:,})" for c, n in p['collections'][:4])
        if coll_text:
            tk.Label(info_frame, text=coll_text, font=fonts['ui_small'],
                    bg=colors['bg_card'], fg=colors['fg_muted']).pack(anchor='w', pady=2)
        
        # ── 统计区 ──
        stats_frame = tk.Frame(self, bg=colors['bg'])
        stats_frame.pack(fill='x', padx=15, pady=5)
        
        # 题材分布
        left_stats = tk.Frame(stats_frame, bg=colors['bg_card'])
        left_stats.pack(side='left', fill='both', expand=True, padx=(0, 5))
        
        tk.Label(left_stats, text="📊 题材分布", font=fonts['ui_bold'],
                bg=colors['bg_card'], fg=colors['accent']).pack(anchor='w', padx=10, pady=(8, 4))
        
        for theme, cnt in p['themes'][:6]:
            row = tk.Frame(left_stats, bg=colors['bg_card'])
            row.pack(fill='x', padx=10, pady=1)
            tk.Label(row, text=theme, font=fonts['ui_small'], width=8, anchor='w',
                    bg=colors['bg_card'], fg=colors['fg']).pack(side='left')
            # 简易条形图
            bar_len = min(20, max(1, cnt * 20 // max(1, p['themes'][0][1])))
            bar = tk.Label(row, text='█' * bar_len, font=('Arial', 8),
                          bg=colors['bg_card'], fg=colors['accent'])
            bar.pack(side='left', padx=3)
            tk.Label(row, text=str(cnt), font=fonts['ui_small'],
                    bg=colors['bg_card'], fg=colors['fg_secondary']).pack(side='left')
        
        left_stats.pack_propagate(False)
        
        # 诗体分布
        right_stats = tk.Frame(stats_frame, bg=colors['bg_card'])
        right_stats.pack(side='left', fill='both', expand=True, padx=(5, 0))
        
        tk.Label(right_stats, text="📝 诗体分布", font=fonts['ui_bold'],
                bg=colors['bg_card'], fg=colors['accent']).pack(anchor='w', padx=10, pady=(8, 4))
        
        for form, cnt in p['forms'][:6]:
            row = tk.Frame(right_stats, bg=colors['bg_card'])
            row.pack(fill='x', padx=10, pady=1)
            tk.Label(row, text=form, font=fonts['ui_small'], width=10, anchor='w',
                    bg=colors['bg_card'], fg=colors['fg']).pack(side='left')
            tk.Label(row, text=str(cnt), font=fonts['ui_small'],
                    bg=colors['bg_card'], fg=colors['fg_secondary']).pack(side='left', padx=3)
        
        # ── 代表作 ──
        works_frame = tk.Frame(self, bg=colors['bg_card'])
        works_frame.pack(fill='both', expand=True, padx=15, pady=15)
        
        tk.Label(works_frame, text="⭐ 代表作", font=fonts['ui_bold'],
                bg=colors['bg_card'], fg=colors['accent']).pack(anchor='w', padx=10, pady=(8, 4))
        
        for w in p['famous'][:4]:
            item = tk.Frame(works_frame, bg=colors['bg_card'])
            item.pack(fill='x', padx=10, pady=2)
            
            title_text = f"《{w['title']}》"
            tk.Label(item, text=title_text, font=fonts['ui'],
                    bg=colors['bg_card'], fg=colors['fg'], anchor='w').pack(anchor='w')
            
            preview = w.get('content', '').replace('\n', ' ')[:40]
            if preview:
                tk.Label(item, text=preview + '...', font=fonts['ui_small'],
                        bg=colors['bg_card'], fg=colors['fg_muted'], anchor='w').pack(anchor='w')
        
        # 关闭按钮
        ttk.Button(self, text="关闭", command=self.destroy).pack(pady=10)


class CipaiWindow(tk.Toplevel):
    """词牌词典窗口"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.title("📖 词牌词典")
        self.geometry("820x620")
        
        self.colors, self.fonts = _colors_fonts()
        self.configure(bg=self.colors['bg'])
        
        self._create_widgets()
    
    def _create_widgets(self):
        colors = self.colors
        fonts = self.fonts
        
        # 搜索栏
        search_frame = tk.Frame(self, bg=colors['bg'])
        search_frame.pack(fill='x', padx=15, pady=10)
        
        tk.Label(search_frame, text="搜索词牌:", font=fonts['ui'],
                bg=colors['bg'], fg=colors['fg']).pack(side='left')
        
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        entry.pack(side='left', padx=8)
        entry.bind('<Return>', lambda e: self._search())
        
        ttk.Button(search_frame, text="🔍 搜索", command=self._search).pack(side='left')
        ttk.Button(search_frame, text="全部", command=self._show_all).pack(side='left', padx=5)
        
        # 主区域：左侧列表 + 右侧详情
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=15, pady=(0, 15))
        
        # 左侧词牌列表
        left = ttk.Frame(paned)
        paned.add(left, weight=0)
        
        self.listbox = tk.Listbox(left, font=fonts['ui'], width=14,
                                   bg=colors['bg_card'], fg=colors['fg'],
                                   selectbackground=colors['select_bg'],
                                   selectforeground=colors['fg'],
                                   relief='flat', highlightthickness=0,
                                   activestyle='none')
        self.listbox.pack(fill='both', expand=True)
        self.listbox.bind('<<ListboxSelect>>', self._on_select)
        
        # 右侧详情
        right = ttk.Frame(paned)
        paned.add(right, weight=1)
        
        self.detail_text = tk.Text(right, wrap='word', font=fonts['ui'],
                                    bg=colors['bg_card'], fg=colors['fg'],
                                    relief='flat', padx=15, pady=12,
                                    spacing1=3, spacing3=3)
        scrollbar = ttk.Scrollbar(right, orient='vertical', command=self.detail_text.yview)
        self.detail_text.configure(yscrollcommand=scrollbar.set)
        self.detail_text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 配置标签样式
        self.detail_text.tag_config('title', font=fonts['title_small'], 
                                     foreground=colors['accent'], spacing1=5, spacing3=10)
        self.detail_text.tag_config('label', font=fonts['ui_bold'], 
                                     foreground=colors['fg_secondary'])
        self.detail_text.tag_config('content', font=fonts['ui'], 
                                     foreground=colors['fg'])
        
        self._show_all()
    
    def _show_all(self):
        """显示全部词牌"""
        self.listbox.delete(0, tk.END)
        for name in get_all_cipai():
            self.listbox.insert(tk.END, name)
    
    def _search(self):
        """搜索词牌"""
        keyword = self.search_var.get().strip()
        if not keyword:
            self._show_all()
            return
        
        results = search_cipai(keyword)
        self.listbox.delete(0, tk.END)
        for name, _ in results:
            self.listbox.insert(tk.END, name)
    
    def _on_select(self, event):
        """显示词牌详情"""
        selection = self.listbox.curselection()
        if not selection:
            return
        
        name = self.listbox.get(selection[0])
        info = CIPAI_DICT.get(name)
        if not info:
            return
        
        self.detail_text.config(state='normal')
        self.detail_text.delete('1.0', tk.END)
        
        self.detail_text.insert(tk.END, f"《{name}》\n", 'title')
        
        if info.get('别名'):
            self.detail_text.insert(tk.END, "别名: ", 'label')
            self.detail_text.insert(tk.END, '、'.join(info['别名']) + '\n\n', 'content')
        
        if info.get('字数'):
            self.detail_text.insert(tk.END, "字数: ", 'label')
            self.detail_text.insert(tk.END, info['字数'] + '\n\n', 'content')
        
        if info.get('句式'):
            self.detail_text.insert(tk.END, "句式: ", 'label')
            self.detail_text.insert(tk.END, info['句式'] + '\n\n', 'content')
        
        if info.get('起源'):
            self.detail_text.insert(tk.END, "起源: ", 'label')
            self.detail_text.insert(tk.END, info['起源'] + '\n\n', 'content')
        
        if info.get('代表'):
            self.detail_text.insert(tk.END, "代表作: ", 'label')
            self.detail_text.insert(tk.END, info['代表'] + '\n', 'content')
        
        self.detail_text.config(state='disabled')


class UnifiedSearchWindow(tk.Toplevel):
    """统一搜索窗口（诗词+古文+诗人）"""
    
    def __init__(self, parent, on_poem_select=None, on_guwen_select=None, on_author_select=None):
        super().__init__(parent)
        self.title("🔍 统一搜索")
        self.geometry("900x650")
        
        self.colors, self.fonts = _colors_fonts()
        self.configure(bg=self.colors['bg'])
        
        self.on_poem_select = on_poem_select
        self.on_guwen_select = on_guwen_select
        self.on_author_select = on_author_select
        
        self.searcher = UnifiedSearch() if HAS_UNIFIED else None
        
        self._create_widgets()
    
    def _create_widgets(self):
        colors = self.colors
        fonts = self.fonts
        
        # 搜索栏
        search_frame = tk.Frame(self, bg=colors['bg'])
        search_frame.pack(fill='x', padx=15, pady=12)
        
        tk.Label(search_frame, text="搜索:", font=fonts['ui_large'],
                bg=colors['bg'], fg=colors['fg']).pack(side='left')
        
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        entry.pack(side='left', padx=8, ipady=3)
        entry.bind('<Return>', lambda e: self._do_search())
        entry.focus_set()
        
        ttk.Button(search_frame, text="🔍 搜索", style='Accent.TButton' if HAS_THEME_V2 else 'TButton',
                  command=self._do_search).pack(side='left', padx=3)
        
        # 结果统计
        self.stats_label = tk.Label(self, text="输入关键词搜索诗词、古文、诗人", 
                                     font=fonts['ui_small'], bg=colors['bg'], 
                                     fg=colors['fg_secondary'])
        self.stats_label.pack(anchor='w', padx=15)
        
        # Notebook 分类结果
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill='both', expand=True, padx=15, pady=10)
        
        # 诗词结果
        self.poems_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.poems_frame, text="📜 诗词")
        self.poems_tree = self._create_result_tree(self.poems_frame, 
                                                    ('title', 'author', 'dynasty', 'collection'))
        
        # 古文结果
        self.guwen_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.guwen_frame, text="📖 古文")
        self.guwen_tree = self._create_result_tree(self.guwen_frame,
                                                    ('title', 'author', 'dynasty', 'collection'))
        
        # 诗人结果
        self.authors_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.authors_frame, text="👤 诗人")
        self.authors_tree = self._create_result_tree(self.authors_frame,
                                                      ('author', 'dynasty', 'count'))
        
        # 绑定双击
        self.poems_tree.bind('<Double-1>', self._on_poem_double)
        self.guwen_tree.bind('<Double-1>', self._on_guwen_double)
        self.authors_tree.bind('<Double-1>', self._on_author_double)
    
    def _create_result_tree(self, parent, columns):
        """创建结果列表"""
        tree = ttk.Treeview(parent, columns=columns, show='headings')
        
        headers = {
            'title': '标题', 'author': '作者', 'dynasty': '朝代',
            'collection': '合集', 'count': '作品数'
        }
        widths = {'title': 280, 'author': 100, 'dynasty': 60, 'collection': 90, 'count': 80}
        
        for col in columns:
            tree.heading(col, text=headers.get(col, col))
            tree.column(col, width=widths.get(col, 100))
        
        scrollbar = ttk.Scrollbar(parent, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        return tree
    
    def _do_search(self):
        """执行搜索"""
        keyword = self.search_var.get().strip()
        if not keyword or not self.searcher:
            return
        
        results = self.searcher.search_all(keyword, limit=100)
        
        # 清空
        for tree in [self.poems_tree, self.guwen_tree, self.authors_tree]:
            for item in tree.get_children():
                tree.delete(item)
        
        # 填充诗词
        for p in results['poems']:
            self.poems_tree.insert('', 'end', 
                                   values=(p['title'], p['author'], p['dynasty'], p.get('collection', '')),
                                   tags=(str(p['id']), 'poem'))
        
        # 填充古文
        for g in results['guwen']:
            self.guwen_tree.insert('', 'end',
                                   values=(g['title'], g['author'], g['dynasty'], g.get('collection', '')),
                                   tags=(str(g['id']), 'guwen'))
        
        # 填充诗人
        for a in results['authors']:
            self.authors_tree.insert('', 'end',
                                     values=(a['author'], a['dynasty'], a['count']),
                                     tags=(a['author'], 'author'))
        
        # 更新统计和标签
        self.stats_label.config(
            text=f"「{keyword}」找到 {len(results['poems'])} 首诗词 · {len(results['guwen'])} 篇古文 · {len(results['authors'])} 位诗人"
        )
        
        self.notebook.tab(0, text=f"📜 诗词 ({len(results['poems'])})")
        self.notebook.tab(1, text=f"📖 古文 ({len(results['guwen'])})")
        self.notebook.tab(2, text=f"👤 诗人 ({len(results['authors'])})")
    
    def _on_poem_double(self, event):
        """双击诗词结果"""
        selection = self.poems_tree.selection()
        if not selection:
            return
        tags = self.poems_tree.item(selection[0])['tags']
        if tags and self.on_poem_select:
            self.on_poem_select(int(tags[0]))
    
    def _on_guwen_double(self, event):
        """双击古文结果"""
        selection = self.guwen_tree.selection()
        if not selection:
            return
        tags = self.guwen_tree.item(selection[0])['tags']
        if tags and self.on_guwen_select:
            self.on_guwen_select(int(tags[0]))
    
    def _on_author_double(self, event):
        """双击诗人结果"""
        selection = self.authors_tree.selection()
        if not selection:
            return
        tags = self.authors_tree.item(selection[0])['tags']
        if tags and self.on_author_select:
            self.on_author_select(tags[0])
