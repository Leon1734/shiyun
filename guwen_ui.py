#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古文阅读器 UI
支持：原文/译文/赏析/背景/精读（逐句+注释）
数据源：《古文观止》222篇 + 中学文言文 40篇
"""

import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
import logging

log = logging.getLogger("poetry")

try:
    from app_paths import get_db_path
    DB_PATH = get_db_path()
except ImportError:
    DB_PATH = Path(__file__).parent / "data" / "poetry.db"

# 新主题系统
try:
    from ui_theme_v2 import THEMES_V2, get_fonts, apply_theme
    HAS_THEME_V2 = True
except ImportError:
    HAS_THEME_V2 = False


class GuwenReader(tk.Toplevel):
    """古文阅读器窗口"""
    
    def __init__(self, parent, theme_colors=None, preselect_title=None):
        super().__init__(parent)
        self.title("📜 古文阅读器 · 古文观止")
        self.geometry("1200x800")
        self._preselect_title = preselect_title
        
        # 主题
        if HAS_THEME_V2:
            self.theme_name = 'paper'
            self.theme_colors, self.fonts = apply_theme(self, 'paper')
        else:
            self.theme_colors = theme_colors or {
                'bg': '#FAFAFA', 'bg_secondary': '#F0F0F0',
                'fg': '#333333', 'fg_secondary': '#666666',
                'accent': '#8B4513'
            }
            self.fonts = {
                'poem': ('楷体', 16), 'title': ('华文中宋', 20, 'bold'),
                'ui': ('微软雅黑', 10), 'ui_small': ('微软雅黑', 9),
                'ui_bold': ('微软雅黑', 10, 'bold'), 'ui_large': ('微软雅黑', 12, 'bold'),
                'prose': ('仿宋', 13), 'pinyin': ('Arial', 10),
                'poem_large': ('楷体', 20), 'poem_small': ('楷体', 13),
                'title_small': ('华文中宋', 14, 'bold'),
            }
        
        self.conn = None
        self.current_essay = None
        
        self._init_db()
        self._create_widgets()
        self._load_list()
    
    def _init_db(self):
        """初始化数据库连接"""
        try:
            self.conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
        except Exception as e:
            log.error(f"古文数据库连接失败: {e}")
    
    def _create_widgets(self):
        """创建界面"""
        # 主分栏
        paned = ttk.PanedWindow(self, orient='horizontal')
        paned.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 左侧列表
        left = ttk.Frame(paned, width=280)
        paned.add(left, weight=0)
        
        # 筛选区
        filter_frame = ttk.Frame(left)
        filter_frame.pack(fill='x', padx=3, pady=3)
        
        ttk.Label(filter_frame, text="合集:").pack(side='left')
        self.collection_var = tk.StringVar(value='全部')
        coll_combo = ttk.Combobox(filter_frame, textvariable=self.collection_var,
                                  values=['全部', '古文观止', '中学文言文'],
                                  width=8, state='readonly')
        coll_combo.pack(side='left', padx=3)
        coll_combo.bind('<<ComboboxSelected>>', lambda e: self._load_list())
        
        ttk.Label(filter_frame, text="朝代:").pack(side='left')
        self.dynasty_var = tk.StringVar(value='全部')
        dyn_combo = ttk.Combobox(filter_frame, textvariable=self.dynasty_var,
                                 values=['全部', '先秦', '汉', '魏晋', '唐', '宋', '明'],
                                 width=6, state='readonly')
        dyn_combo.pack(side='left', padx=3)
        dyn_combo.bind('<<ComboboxSelected>>', lambda e: self._load_list())
        
        # 搜索框
        search_frame = ttk.Frame(left)
        search_frame.pack(fill='x', padx=3, pady=3)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        search_entry.pack(side='left', fill='x', expand=True)
        search_entry.bind('<Return>', lambda e: self._search())
        ttk.Button(search_frame, text="🔍", command=self._search, width=3).pack(side='left', padx=2)
        
        # 文章列表
        list_frame = ttk.Frame(left)
        list_frame.pack(fill='both', expand=True, padx=3, pady=3)
        
        self.list_tree = ttk.Treeview(list_frame, columns=('title', 'author', 'dynasty'),
                                      show='headings', height=20)
        self.list_tree.heading('title', text='篇名')
        self.list_tree.heading('author', text='作者')
        self.list_tree.heading('dynasty', text='朝代')
        self.list_tree.column('title', width=130)
        self.list_tree.column('author', width=70)
        self.list_tree.column('dynasty', width=50)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.list_tree.yview)
        self.list_tree.configure(yscrollcommand=scrollbar.set)
        self.list_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        self.list_tree.bind('<<TreeviewSelect>>', self._on_select)
        
        # 统计标签
        self.stats_label = ttk.Label(left, text="", font=('微软雅黑', 8))
        self.stats_label.pack(fill='x', padx=3, pady=2)
        
        # 右侧内容区
        right = ttk.Frame(paned)
        paned.add(right, weight=1)
        
        # 标题区
        title_frame = ttk.Frame(right)
        title_frame.pack(fill='x', padx=10, pady=5)
        
        colors = self.theme_colors
        self.title_label = tk.Label(title_frame, text="请选择一篇古文", 
                                     font=self.fonts.get('title', ('华文中宋', 20, 'bold')),
                                     bg=colors.get('bg', '#F7F3E8'),
                                     fg=colors.get('fg', '#2B2B2B'))
        self.title_label.pack()
        
        self.author_label = tk.Label(title_frame, text="", font=self.fonts.get('ui', ('微软雅黑', 10)),
                                     bg=colors.get('bg', '#F7F3E8'),
                                     fg=colors.get('fg_secondary', '#6B6355'))
        self.author_label.pack()
        
        # 标签栏
        self.tags_label = tk.Label(title_frame, text="", font=self.fonts.get('ui_small', ('微软雅黑', 9)), 
                                    bg=colors.get('bg', '#F7F3E8'),
                                    fg=colors.get('accent', '#8C2F39'))
        self.tags_label.pack()
        
        # Notebook 选项卡
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        
        # 原文
        self.text_original = self._create_text_tab('📖 原文')
        
        # 译文
        self.text_translation = self._create_text_tab('💬 译文')
        
        # 赏析
        self.text_appreciation = self._create_text_tab('✨ 赏析')
        
        # 背景
        self.text_background = self._create_text_tab('📚 背景')
        
        # 精读（逐句注释）
        self.text_intensive = self._create_text_tab('🔍 精读')
        
        # 底部按钮
        btn_frame = ttk.Frame(right)
        btn_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(btn_frame, text="🔊 朗读全文", command=self._speak_essay).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="📋 复制原文", command=self._copy_original).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="关闭", command=self.destroy).pack(side='right', padx=2)
        
        # TTS引擎
        self.tts_engine = None
        try:
            from features_v7 import TTSEngine
            self.tts_engine = TTSEngine()
        except ImportError:
            pass
    
    def _create_text_tab(self, name):
        """创建文本选项卡"""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=name)
        
        colors = self.theme_colors
        text = tk.Text(frame, wrap='word', font=self.fonts.get('prose', ('仿宋', 13)),
                       relief='flat', padx=16, pady=12,
                       background=colors.get('bg_card', '#FDFAF2'),
                       foreground=colors.get('fg', '#2B2B2B'),
                       spacing1=4, spacing3=4,
                       selectbackground=colors.get('select_bg', '#EDE4D0'),
                       insertbackground=colors.get('fg', '#2B2B2B'))
        
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        
        text.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 选中文字 → 自动复制 + 提示
        text.bind('<ButtonRelease-1>', lambda e, t=text: self._on_text_select(t))
        
        return text
    
    def _on_text_select(self, text_widget):
        """选中文字后自动复制到剪贴板 + 浮动提示"""
        try:
            sel = text_widget.get('sel.first', 'sel.last')
        except tk.TclError:
            return
        if sel and sel.strip():
            try:
                self.clipboard_clear()
                self.clipboard_append(sel)
            except Exception:
                return
            preview = sel.strip().replace('\n', ' ')
            if len(preview) > 14:
                preview = preview[:14] + '…'
            self._show_toast(f"✓ 已复制: {preview}")
    
    def _show_toast(self, text, ms=1500):
        """窗口底部浮动轻提示"""
        try:
            if getattr(self, '_toast_win', None) and self._toast_win.winfo_exists():
                self._toast_win.destroy()
        except Exception:
            pass
        try:
            toast = tk.Toplevel(self)
            toast.overrideredirect(True)
            toast.attributes('-topmost', True)
            tk.Label(toast, text=text, bg='#2F2F2F', fg='#FFFFFF',
                    font=('微软雅黑', 10), padx=14, pady=8).pack()
            toast.update_idletasks()
            x = self.winfo_rootx() + self.winfo_width() - toast.winfo_reqwidth() - 40
            y = self.winfo_rooty() + self.winfo_height() - toast.winfo_reqheight() - 60
            toast.geometry(f'+{max(0,x)}+{max(0,y)}')
            self._toast_win = toast
            self.after(ms, lambda: toast.destroy() if toast.winfo_exists() else None)
        except Exception:
            pass
    
    def _load_list(self):
        """加载文章列表"""
        if not self.conn:
            return
        
        for item in self.list_tree.get_children():
            self.list_tree.delete(item)
        
        try:
            cursor = self.conn.cursor()
            
            query = "SELECT id, title, author, dynasty, collection FROM guwen WHERE 1=1"
            params = []
            
            collection = self.collection_var.get()
            if collection != '全部':
                query += " AND collection = ?"
                params.append(collection)
            
            dynasty = self.dynasty_var.get()
            if dynasty != '全部':
                query += " AND dynasty = ?"
                params.append(dynasty)
            
            query += " ORDER BY id"
            cursor.execute(query, params)
            
            count = 0
            for row in cursor:
                self.list_tree.insert('', 'end', 
                                     values=(row['title'], row['author'], row['dynasty'] or '—'),
                                     tags=(str(row['id']),))
                count += 1
            
            self.stats_label.config(text=f"共 {count} 篇")
            
            # 预选文章（从主窗口带入）
            if self._preselect_title:
                ptitle = self._preselect_title
                for item in self.list_tree.get_children():
                    vals = self.list_tree.item(item)['values']
                    if vals and str(vals[0]) == ptitle:
                        self.list_tree.selection_set(item)
                        self.list_tree.see(item)
                        self._display_essay(int(self.list_tree.item(item)['tags'][0]))
                        break
                self._preselect_title = None
        except Exception as e:
            log.error(f"加载古文列表失败: {e}")
    
    def _search(self):
        """搜索"""
        keyword = self.search_var.get().strip()
        if not keyword:
            self._load_list()
            return
        
        if not self.conn:
            return
        
        for item in self.list_tree.get_children():
            self.list_tree.delete(item)
        
        try:
            cursor = self.conn.cursor()
            # LIKE 搜索（中文更可靠）
            cursor.execute('''
                SELECT id, title, author, dynasty FROM guwen
                WHERE title LIKE ? OR author LIKE ? OR content LIKE ?
                LIMIT 100
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'))
            
            count = 0
            for row in cursor:
                self.list_tree.insert('', 'end',
                                     values=(row[1], row[2], row[3] or '—'),
                                     tags=(str(row[0]),))
                count += 1
            
            self.stats_label.config(text=f"搜索到 {count} 篇")
        except Exception as e:
            log.error(f"搜索失败: {e}")
    
    def _on_select(self, event):
        """选中文章"""
        selection = self.list_tree.selection()
        if not selection:
            return
        
        item = self.list_tree.item(selection[0])
        tags = item.get('tags', ())
        if not tags:
            return
        
        essay_id = tags[0]
        self._display_essay(int(essay_id))
    
    def _display_essay(self, essay_id):
        """显示文章内容"""
        if not self.conn:
            return
        
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM guwen WHERE id = ?", (essay_id,))
            row = cursor.fetchone()
            
            if not row:
                return
            
            self.current_essay = dict(row)
            
            # 标题
            self.title_label.config(text=f"《{row['title']}》")
            
            author_text = f"· {row['author']}"
            if row['dynasty']:
                author_text += f" ({row['dynasty']})"
            if row['char_count']:
                author_text += f" · 全文{row['char_count']}字"
            self.author_label.config(text=author_text)
            
            # 标签
            try:
                tags = json.loads(row['tags']) if row['tags'] else []
                self.tags_label.config(text=' '.join(f"#{t}" for t in tags) if tags else "")
            except:
                self.tags_label.config(text="")
            
            # 填充各标签页
            self._set_text(self.text_original, row['content'] or '（暂无原文）')
            self._set_text(self.text_translation, row['translation'] or '（暂无译文）')
            self._set_text(self.text_appreciation, row['appreciation'] or '（暂无赏析）')
            
            # 背景 + 作者简介
            bg_text = row['background'] or ''
            if row['author_bio']:
                bg_text += '\n\n【作者简介】\n' + row['author_bio']
            self._set_text(self.text_background, bg_text or '（暂无背景资料）')
            
            # 精读
            self._build_intensive(row['paragraphs_json'])
            
        except Exception as e:
            log.error(f"显示古文失败: {e}")
    
    def _set_text(self, widget, content):
        """设置文本内容"""
        widget.config(state='normal')
        widget.delete('1.0', tk.END)
        widget.insert('1.0', content)
        widget.config(state='disabled')
    
    def _build_intensive(self, paragraphs_json):
        """构建精读视图（逐句+字号注释）"""
        self.text_intensive.config(state='normal')
        self.text_intensive.delete('1.0', tk.END)
        
        if not paragraphs_json:
            self.text_intensive.insert('1.0', '（暂无精读数据）')
            self.text_intensive.config(state='disabled')
            return
        
        try:
            paragraphs = json.loads(paragraphs_json)
            
            for para in paragraphs:
                if not isinstance(para, dict):
                    continue
                
                # 段落原文
                self.text_intensive.insert(tk.END, para.get('original', ''), 'original')
                self.text_intensive.insert(tk.END, '\n')
                
                # 段落译文
                trans = para.get('translation', '')
                if trans:
                    self.text_intensive.insert(tk.END, f"〖译〗{trans}\n", 'translation')
                
                # 逐句注释
                sentences = para.get('sentences', [])
                for sent in sentences:
                    if not isinstance(sent, dict):
                        continue
                    
                    words = sent.get('words', [])
                    if words:
                        self.text_intensive.insert(tk.END, '\n')
                        for w in words:
                            if not isinstance(w, dict):
                                continue
                            word = w.get('word', '')
                            pinyin = w.get('pinyin', '')
                            meaning = w.get('meaning', '')
                            wtype = w.get('type', '')
                            
                            if word and meaning:
                                line = f"  【{word}】"
                                if pinyin:
                                    line += f" {pinyin}"
                                if wtype:
                                    line += f" ({wtype})"
                                line += f" — {meaning}\n"
                                self.text_intensive.insert(tk.END, line, 'word')
                
                self.text_intensive.insert(tk.END, '\n' + '─' * 40 + '\n\n')
            
            # 配置样式
            self.text_intensive.tag_config('original', font=('微软雅黑', 11, 'bold'))
            self.text_intensive.tag_config('translation', foreground='#555555', font=('微软雅黑', 10))
            self.text_intensive.tag_config('word', foreground='#8B4513', font=('微软雅黑', 9))
            
        except Exception as e:
            log.error(f"构建精读视图失败: {e}")
            self.text_intensive.insert('1.0', f'（精读数据解析失败）')
        
        self.text_intensive.config(state='disabled')
    
    def _copy_original(self):
        """复制原文"""
        if not self.current_essay:
            return
        
        self.clipboard_clear()
        self.clipboard_append(self.current_essay.get('content', ''))
        messagebox.showinfo("提示", "原文已复制到剪贴板")
    
    def _speak_essay(self):
        """朗读古文"""
        if not self.current_essay:
            messagebox.showinfo("提示", "请先选择一篇古文")
            return
        
        if not self.tts_engine:
            messagebox.showinfo("提示", "TTS 模块未加载")
            return
        
        title = self.current_essay.get('title', '')
        author = self.current_essay.get('author', '')
        content = self.current_essay.get('content', '')
        
        # 朗读文本：标题 + 作者 + 正文（长文截断到合理长度）
        speak_text = f"{title}。{author}。{content}"
        speak_text = speak_text.replace('\n', '，')
        
        # 限制长度（edge-tts 对超长文本处理慢）
        if len(speak_text) > 2000:
            speak_text = speak_text[:2000] + "。由于篇幅限制，朗读到此结束。"
        
        if self.tts_engine.is_playing:
            self.tts_engine.stop()
            return
        
        self.tts_engine.speak_async(speak_text)


def open_guwen_reader(parent, theme_colors=None):
    """打开古文阅读器"""
    reader = GuwenReader(parent, theme_colors)
    reader.grab_set()
    return reader


if __name__ == "__main__":
    # 独立测试
    root = tk.Tk()
    root.withdraw()
    reader = GuwenReader(root)
    reader.protocol("WM_DELETE_WINDOW", lambda: (reader.destroy(), root.destroy()))
    root.mainloop()
