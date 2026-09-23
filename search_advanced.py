#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级搜索模块
功能：多条件组合搜索、正则表达式搜索、模糊搜索、搜索历史
"""

import re
import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path
from datetime import datetime
import logging

log = logging.getLogger("poetry")

# 搜索历史数据库路径
# 路径：优先 data 目录（与 exe 共享；打包后 _internal 只读）
try:
    from app_paths import get_data_dir as _get_data_dir
    SEARCH_HISTORY_DB = _get_data_dir() / "search_history.db"
except Exception:
    SEARCH_HISTORY_DB = Path(__file__).parent / "data" / "search_history.db"


class SearchHistory:
    """搜索历史管理"""
    
    def __init__(self):
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.conn = sqlite3.connect(str(SEARCH_HISTORY_DB))
            cursor = self.conn.cursor()
            
            # 创建搜索历史表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    keyword TEXT NOT NULL,
                    search_type TEXT DEFAULT 'basic',
                    result_count INTEGER DEFAULT 0,
                    searched_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            log.info("搜索历史数据库初始化完成")
        except Exception as e:
            log.error(f"初始化搜索历史数据库失败: {e}")
    
    def add_search(self, keyword, search_type='basic', result_count=0):
        """添加搜索记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO search_history (keyword, search_type, result_count)
                VALUES (?, ?, ?)
            ''', (keyword, search_type, result_count))
            self.conn.commit()
            return True
        except Exception as e:
            log.error(f"添加搜索记录失败: {e}")
            return False
    
    def get_recent_searches(self, limit=20):
        """获取最近的搜索记录"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT keyword, search_type, result_count, searched_at 
                FROM search_history 
                ORDER BY searched_at DESC 
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        except Exception as e:
            log.error(f"获取搜索历史失败: {e}")
            return []
    
    def get_popular_searches(self, limit=10):
        """获取热门搜索"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT keyword, COUNT(*) as search_count
                FROM search_history
                GROUP BY keyword
                ORDER BY search_count DESC
                LIMIT ?
            ''', (limit,))
            return cursor.fetchall()
        except Exception as e:
            log.error(f"获取热门搜索失败: {e}")
            return []
    
    def clear_history(self):
        """清空搜索历史"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM search_history")
            self.conn.commit()
            return True
        except Exception as e:
            log.error(f"清空搜索历史失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


class AdvancedSearchDialog:
    """高级搜索对话框"""
    
    def __init__(self, parent, db, theme_colors):
        self.parent = parent
        self.db = db
        self.theme_colors = theme_colors
        self.search_history = SearchHistory()
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("高级搜索")
        self.dialog.geometry("600x500")
        self.dialog.resizable(False, False)
        
        # 设置对话框样式
        self.dialog.configure(background=theme_colors['bg'])
        
        # 创建界面
        self._create_widgets()
        
        # 加载搜索历史
        self._load_search_history()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🔍 高级搜索", 
                               font=('微软雅黑', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 搜索条件区域
        search_frame = ttk.LabelFrame(main_frame, text="搜索条件", padding=10)
        search_frame.pack(fill='x', pady=(0, 10))
        
        # 关键词搜索
        keyword_frame = ttk.Frame(search_frame)
        keyword_frame.pack(fill='x', pady=5)
        
        ttk.Label(keyword_frame, text="关键词:").pack(side='left')
        self.keyword_var = tk.StringVar()
        keyword_entry = ttk.Entry(keyword_frame, textvariable=self.keyword_var, width=30)
        keyword_entry.pack(side='left', padx=10, fill='x', expand=True)
        
        # 搜索类型
        type_frame = ttk.Frame(search_frame)
        type_frame.pack(fill='x', pady=5)
        
        ttk.Label(type_frame, text="搜索类型:").pack(side='left')
        self.search_type_var = tk.StringVar(value='contains')
        
        types = [('包含', 'contains'), ('正则表达式', 'regex'), ('模糊搜索', 'fuzzy')]
        for text, value in types:
            ttk.Radiobutton(type_frame, text=text, variable=self.search_type_var, 
                           value=value).pack(side='left', padx=10)
        
        # 朝代筛选
        dynasty_frame = ttk.Frame(search_frame)
        dynasty_frame.pack(fill='x', pady=5)
        
        ttk.Label(dynasty_frame, text="朝代:").pack(side='left')
        self.dynasty_var = tk.StringVar(value='全部')
        dynasty_combo = ttk.Combobox(dynasty_frame, textvariable=self.dynasty_var,
                                     values=['全部', '唐', '宋', '元', '先秦', '汉', '魏晋', '南北朝', '隋'],
                                     width=10, state='readonly')
        dynasty_combo.pack(side='left', padx=10)
        
        # 作者筛选
        author_frame = ttk.Frame(search_frame)
        author_frame.pack(fill='x', pady=5)
        
        ttk.Label(author_frame, text="作者:").pack(side='left')
        self.author_var = tk.StringVar()
        author_entry = ttk.Entry(author_frame, textvariable=self.author_var, width=20)
        author_entry.pack(side='left', padx=10)
        
        # 搜索范围
        scope_frame = ttk.Frame(search_frame)
        scope_frame.pack(fill='x', pady=5)
        
        ttk.Label(scope_frame, text="搜索范围:").pack(side='left')
        self.scope_var = tk.StringVar(value='all')
        
        scopes = [('全部', 'all'), ('标题', 'title'), ('内容', 'content'), ('作者', 'author')]
        for text, value in scopes:
            ttk.Radiobutton(scope_frame, text=text, variable=self.scope_var, 
                           value=value).pack(side='left', padx=10)
        
        # 搜索按钮
        btn_frame = ttk.Frame(search_frame)
        btn_frame.pack(fill='x', pady=10)
        
        ttk.Button(btn_frame, text="🔍 搜索", command=self._perform_search).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="🔄 重置", command=self._reset_search).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="📋 历史", command=self._show_history).pack(side='left', padx=5)
        
        # 结果区域
        result_frame = ttk.LabelFrame(main_frame, text="搜索结果", padding=10)
        result_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # 结果统计
        self.result_stats = ttk.Label(result_frame, text="输入搜索条件后点击搜索")
        self.result_stats.pack(fill='x', pady=(0, 10))
        
        # 结果列表
        self.result_tree = ttk.Treeview(result_frame, columns=('title', 'author', 'dynasty'), 
                                        show='headings', height=10)
        self.result_tree.heading('title', text='标题')
        self.result_tree.heading('author', text='作者')
        self.result_tree.heading('dynasty', text='朝代')
        self.result_tree.column('title', width=200)
        self.result_tree.column('author', width=100)
        self.result_tree.column('dynasty', width=80)
        
        scrollbar = ttk.Scrollbar(result_frame, orient='vertical', command=self.result_tree.yview)
        self.result_tree.configure(yscrollcommand=scrollbar.set)
        
        self.result_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 绑定双击事件
        self.result_tree.bind('<Double-1>', self._on_result_double_click)
        
        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill='x')
        
        ttk.Button(bottom_frame, text="关闭", command=self.dialog.destroy).pack(side='right')
        ttk.Button(bottom_frame, text="导出结果", command=self._export_results).pack(side='right', padx=10)
    
    def _perform_search(self):
        """执行搜索"""
        keyword = self.keyword_var.get().strip()
        if not keyword:
            messagebox.showwarning("警告", "请输入搜索关键词")
            return
        
        search_type = self.search_type_var.get()
        dynasty = self.dynasty_var.get()
        author = self.author_var.get().strip()
        scope = self.scope_var.get()
        
        # 执行搜索
        results = self._search(keyword, search_type, dynasty, author, scope)
        
        # 更新结果
        self._update_results(results)
        
        # 保存搜索历史
        self.search_history.add_search(keyword, search_type, len(results))
    
    def _search(self, keyword, search_type, dynasty, author, scope):
        """执行搜索逻辑"""
        results = []
        
        for poem in self.db.poems:
            # 朝代筛选
            if dynasty != '全部' and poem.get('dynasty', '') != dynasty:
                continue
            
            # 作者筛选
            if author and author not in poem.get('author', ''):
                continue
            
            # 获取搜索内容
            title = poem.get('title', '')
            content = poem.get('content', '')
            if isinstance(content, list):
                content = '\n'.join(content)
            
            # 根据搜索范围选择内容
            if scope == 'title':
                search_content = title
            elif scope == 'content':
                search_content = content
            elif scope == 'author':
                search_content = poem.get('author', '')
            else:
                search_content = f"{title} {content} {poem.get('author', '')}"
            
            # 执行搜索
            if search_type == 'contains':
                if keyword in search_content:
                    results.append(poem)
            elif search_type == 'regex':
                try:
                    if re.search(keyword, search_content):
                        results.append(poem)
                except re.error:
                    messagebox.showerror("错误", "正则表达式语法错误")
                    return []
            elif search_type == 'fuzzy':
                # 简单的模糊搜索：检查所有字符是否按顺序出现
                if self._fuzzy_match(keyword, search_content):
                    results.append(poem)
        
        return results
    
    def _fuzzy_match(self, pattern, text):
        """模糊匹配"""
        pattern_idx = 0
        text_idx = 0
        
        while pattern_idx < len(pattern) and text_idx < len(text):
            if pattern[pattern_idx] == text[text_idx]:
                pattern_idx += 1
            text_idx += 1
        
        return pattern_idx == len(pattern)
    
    def _update_results(self, results):
        """更新搜索结果"""
        # 清空结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        # 填充结果
        for poem in results:
            title = poem.get('title', '')
            author = poem.get('author', '')
            dynasty = poem.get('dynasty', '')
            
            # 繁简转换
            if hasattr(self, 'HAS_CONVERTER') and self.HAS_CONVERTER:
                title = self.traditional_to_simplified(title)
                author = self.traditional_to_simplified(author)
            
            self.result_tree.insert('', 'end', values=(title, author, dynasty))
        
        # 更新统计
        self.result_stats.config(text=f"找到 {len(results)} 首诗词")
    
    def _reset_search(self):
        """重置搜索"""
        self.keyword_var.set('')
        self.author_var.set('')
        self.dynasty_var.set('全部')
        self.search_type_var.set('contains')
        self.scope_var.set('all')
        
        # 清空结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
        
        self.result_stats.config(text="输入搜索条件后点击搜索")
    
    def _show_history(self):
        """显示搜索历史"""
        history = self.search_history.get_recent_searches(20)
        
        if not history:
            messagebox.showinfo("搜索历史", "暂无搜索历史")
            return
        
        # 创建历史窗口
        history_win = tk.Toplevel(self.dialog)
        history_win.title("搜索历史")
        history_win.geometry("400x300")
        
        # 历史列表
        listbox = tk.Listbox(history_win, font=('微软雅黑', 10))
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        for keyword, search_type, result_count, searched_at in history:
            listbox.insert(tk.END, f"{keyword} ({search_type}) - {result_count}首 - {searched_at}")
        
        def on_select(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                keyword = history[index][0]
                self.keyword_var.set(keyword)
                history_win.destroy()
        
        listbox.bind('<<ListboxSelect>>', on_select)
    
    def _export_results(self):
        """导出搜索结果"""
        results = []
        for item in self.result_tree.get_children():
            values = self.result_tree.item(item)['values']
            results.append({
                'title': values[0],
                'author': values[1],
                'dynasty': values[2]
            })
        
        if not results:
            messagebox.showinfo("提示", "没有搜索结果可导出")
            return
        
        filename = tk.filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv")],
            initialfile=f"search_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if filename:
            try:
                if filename.endswith('.json'):
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(results, f, ensure_ascii=False, indent=2)
                else:
                    import csv
                    with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(['标题', '作者', '朝代'])
                        for result in results:
                            writer.writerow([result['title'], result['author'], result['dynasty']])
                
                messagebox.showinfo("成功", f"搜索结果已导出到 {filename}")
            except Exception as e:
                messagebox.showerror("错误", f"导出失败: {e}")
    
    def _on_result_double_click(self, event):
        """结果双击事件"""
        selection = self.result_tree.selection()
        if not selection:
            return
        
        # 获取选中的诗词
        item = self.result_tree.item(selection[0])
        title = item['values'][0]
        author = item['values'][1]
        
        # 查找对应的诗词
        for poem in self.db.poems:
            if poem.get('title', '') == title and poem.get('author', '') == author:
                # 在父窗口中显示诗词
                if hasattr(self.parent, '_display_poem'):
                    self.parent._display_poem(poem)
                break
        
        # 关闭对话框
        self.dialog.destroy()
    
    def _load_search_history(self):
        """加载搜索历史"""
        # 搜索历史会在对话框打开时自动加载
        pass
    
    def destroy(self):
        """销毁对话框"""
        self.search_history.close()
        self.dialog.destroy()
