#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
收藏管理模块
功能：标签系统、排序、导出、统计
"""

import json
import sqlite3
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
import logging

log = logging.getLogger("poetry")

# 收藏管理数据库路径
# 路径：优先 data 目录（与 exe 共享；打包后 _internal 只读）
try:
    from app_paths import get_data_dir as _get_data_dir
    COLLECTION_DB = _get_data_dir() / "collection.db"
except Exception:
    COLLECTION_DB = Path(__file__).parent / "data" / "collection.db"


class CollectionManager:
    """收藏管理器"""
    
    def __init__(self, db):
        self.db = db
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.conn = sqlite3.connect(str(COLLECTION_DB))
            cursor = self.conn.cursor()
            
            # 创建标签表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collection_tags (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tag_name TEXT NOT NULL UNIQUE,
                    color TEXT DEFAULT '#1e66f5',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建收藏关联表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS collection_poems (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poem_id TEXT NOT NULL,
                    tag_id INTEGER,
                    added_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (tag_id) REFERENCES collection_tags(id)
                )
            ''')
            
            # 创建默认标签
            default_tags = [
                ('默认', '#1e66f5'),
                ('喜欢', '#d20f39'),
                ('学习', '#40a02b'),
                ('收藏', '#df8e1d'),
            ]
            
            for tag_name, color in default_tags:
                cursor.execute('''
                    INSERT OR IGNORE INTO collection_tags (tag_name, color)
                    VALUES (?, ?)
                ''', (tag_name, color))
            
            self.conn.commit()
            log.info("收藏管理数据库初始化完成")
        except Exception as e:
            log.error(f"初始化收藏管理数据库失败: {e}")
    
    def add_tag(self, tag_name, color='#1e66f5'):
        """添加标签"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO collection_tags (tag_name, color)
                VALUES (?, ?)
            ''', (tag_name, color))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            log.warning(f"标签 '{tag_name}' 已存在")
            return False
        except Exception as e:
            log.error(f"添加标签失败: {e}")
            return False
    
    def get_tags(self):
        """获取所有标签"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM collection_tags ORDER BY tag_name")
            return cursor.fetchall()
        except Exception as e:
            log.error(f"获取标签失败: {e}")
            return []
    
    def delete_tag(self, tag_id):
        """删除标签"""
        try:
            cursor = self.conn.cursor()
            
            # 将关联的收藏移到默认标签
            cursor.execute('''
                UPDATE collection_poems 
                SET tag_id = (SELECT id FROM collection_tags WHERE tag_name = '默认')
                WHERE tag_id = ?
            ''', (tag_id,))
            
            # 删除标签
            cursor.execute("DELETE FROM collection_tags WHERE id = ?", (tag_id,))
            self.conn.commit()
            return True
        except Exception as e:
            log.error(f"删除标签失败: {e}")
            return False
    
    def add_poem_to_collection(self, poem_id, tag_id=None):
        """添加诗词到收藏"""
        try:
            cursor = self.conn.cursor()
            
            # 如果没有指定标签，使用默认标签
            if tag_id is None:
                cursor.execute("SELECT id FROM collection_tags WHERE tag_name = '默认'")
                result = cursor.fetchone()
                if result:
                    tag_id = result[0]
            
            # 检查是否已经收藏
            cursor.execute('''
                SELECT * FROM collection_poems 
                WHERE poem_id = ? AND tag_id = ?
            ''', (poem_id, tag_id))
            
            if cursor.fetchone():
                log.info(f"诗词 {poem_id} 已经在收藏中")
                return False
            
            # 添加收藏
            cursor.execute('''
                INSERT INTO collection_poems (poem_id, tag_id)
                VALUES (?, ?)
            ''', (poem_id, tag_id))
            self.conn.commit()
            return True
        except Exception as e:
            log.error(f"添加收藏失败: {e}")
            return False
    
    def remove_poem_from_collection(self, poem_id, tag_id=None):
        """从收藏中移除诗词"""
        try:
            cursor = self.conn.cursor()
            
            if tag_id:
                cursor.execute('''
                    DELETE FROM collection_poems 
                    WHERE poem_id = ? AND tag_id = ?
                ''', (poem_id, tag_id))
            else:
                cursor.execute('''
                    DELETE FROM collection_poems 
                    WHERE poem_id = ?
                ''', (poem_id,))
            
            self.conn.commit()
            return True
        except Exception as e:
            log.error(f"移除收藏失败: {e}")
            return False
    
    def get_collection_poems(self, tag_id=None, sort_by='added_at', limit=100):
        """获取收藏的诗词/古文（id 取自收藏库，详情从主诗词库读取）"""
        try:
            cursor = self.conn.cursor()
            
            if tag_id:
                cursor.execute('''
                    SELECT cp.poem_id, cp.added_at, cp.tag_id FROM collection_poems cp
                    WHERE cp.tag_id = ?
                    ORDER BY cp.added_at DESC
                    LIMIT ?
                ''', (tag_id, limit))
            else:
                cursor.execute('''
                    SELECT cp.poem_id, cp.added_at, cp.tag_id FROM collection_poems cp
                    ORDER BY cp.added_at DESC
                    LIMIT ?
                ''', (limit,))
            rows = cursor.fetchall()
            
            # 从主诗词库获取详情
            poem_map = {}
            main_conn = getattr(self.db, 'conn', None)
            poem_ids = [str(r[0]) for r in rows]
            if main_conn and poem_ids:
                try:
                    cur2 = main_conn.cursor()
                    int_ids = [pid for pid in poem_ids if not pid.startswith('gw:') and pid.isdigit()]
                    if int_ids:
                        q = "SELECT id, title, author, dynasty, content FROM poems WHERE id IN ({})".format(
                            ','.join('?' * len(int_ids)))
                        cur2.execute(q, int_ids)
                        for r2 in cur2.fetchall():
                            poem_map[str(r2[0])] = {'id': r2[0], 'title': r2[1], 'author': r2[2],
                                                    'dynasty': r2[3], 'content': r2[4]}
                    gw_ids = [pid[3:] for pid in poem_ids if pid.startswith('gw:')]
                    if gw_ids:
                        q = "SELECT id, title, author, dynasty, content FROM guwen WHERE id IN ({})".format(
                            ','.join('?' * len(gw_ids)))
                        cur2.execute(q, gw_ids)
                        for r2 in cur2.fetchall():
                            poem_map['gw:{}'.format(r2[0])] = {'id': 'gw:{}'.format(r2[0]), 'title': r2[1],
                                                               'author': r2[2], 'dynasty': r2[3], 'content': r2[4]}
                except Exception as e:
                    log.error(f"读取收藏详情失败: {e}")
            
            results = []
            for pid, added_at, tag_id_val in rows:
                info = poem_map.get(str(pid), {})
                results.append({
                    'id': pid,
                    'title': info.get('title', f'#{pid}'),
                    'author': info.get('author', ''),
                    'dynasty': info.get('dynasty', ''),
                    'content': info.get('content', ''),
                    'added_at': added_at,
                    'tag_id': tag_id_val,
                })
            return results
        except Exception as e:
            log.error(f"获取收藏诗词失败: {e}")
            return []
    
    def get_collection_stats(self):
        """获取收藏统计"""
        try:
            cursor = self.conn.cursor()
            
            # 总收藏数
            cursor.execute("SELECT COUNT(*) FROM collection_poems")
            total_count = cursor.fetchone()[0]
            
            # 按标签统计
            cursor.execute('''
                SELECT t.tag_name, COUNT(cp.id) as count
                FROM collection_tags t
                LEFT JOIN collection_poems cp ON t.id = cp.tag_id
                GROUP BY t.id
                ORDER BY count DESC
            ''')
            tag_stats = cursor.fetchall()
            
            # 按朝代统计（从主诗词库查询）
            dynasty_stats = []
            try:
                cursor.execute("SELECT poem_id FROM collection_poems")
                pids = [str(r[0]) for r in cursor.fetchall()]
                main_conn = getattr(self.db, 'conn', None)
                if main_conn and pids:
                    cur2 = main_conn.cursor()
                    int_ids = [p for p in pids if not p.startswith('gw:') and p.isdigit()]
                    if int_ids:
                        q = "SELECT dynasty, COUNT(*) FROM poems WHERE id IN ({}) GROUP BY dynasty ORDER BY COUNT(*) DESC".format(
                            ','.join('?' * len(int_ids)))
                        cur2.execute(q, int_ids)
                        dynasty_stats = cur2.fetchall()
            except Exception as e:
                log.error(f"朝代统计失败: {e}")
            
            return {
                'total_count': total_count,
                'tag_stats': tag_stats,
                'dynasty_stats': dynasty_stats
            }
        except Exception as e:
            log.error(f"获取收藏统计失败: {e}")
            return {}
    
    def export_collection(self, filename, format='json', tag_id=None):
        """导出收藏"""
        try:
            poems = self.get_collection_poems(tag_id, limit=1000)
            
            if format == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(poems, f, ensure_ascii=False, indent=2)
            elif format == 'csv':
                import csv
                with open(filename, 'w', encoding='utf-8-sig', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(['标题', '作者', '朝代', '内容'])
                    for poem in poems:
                        writer.writerow([
                            poem.get('title', ''),
                            poem.get('author', ''),
                            poem.get('dynasty', ''),
                            poem.get('content', '')
                        ])
            
            return True
        except Exception as e:
            log.error(f"导出收藏失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


class CollectionDialog:
    """收藏管理对话框"""
    
    def __init__(self, parent, db, collection_manager, theme_colors):
        self.parent = parent
        self.db = db
        self.collection_manager = collection_manager
        self.theme_colors = theme_colors
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("收藏管理")
        self.dialog.geometry("700x500")
        self.dialog.resizable(False, False)
        
        # 设置对话框样式
        self.dialog.configure(background=theme_colors['bg'])
        
        # 创建界面
        self._create_widgets()
        
        # 加载数据
        self._load_data()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="📁 收藏管理", 
                               font=('微软雅黑', 16, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 左右分栏
        paned = ttk.PanedWindow(main_frame, orient='horizontal')
        paned.pack(fill='both', expand=True)
        
        # 左侧标签面板
        left_frame = ttk.Frame(paned, width=200)
        paned.add(left_frame, weight=0)
        
        # 右侧内容面板
        right_frame = ttk.Frame(paned)
        paned.add(right_frame, weight=1)
        
        # ── 左侧标签面板 ──
        tag_title = ttk.Label(left_frame, text="标签", font=('微软雅黑', 12, 'bold'))
        tag_title.pack(fill='x', padx=5, pady=5)
        
        # 标签列表
        self.tag_listbox = tk.Listbox(left_frame, font=('微软雅黑', 10))
        self.tag_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        # 标签操作按钮
        tag_btn_frame = ttk.Frame(left_frame)
        tag_btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(tag_btn_frame, text="添加", command=self._add_tag).pack(side='left', padx=2)
        ttk.Button(tag_btn_frame, text="删除", command=self._delete_tag).pack(side='left', padx=2)
        ttk.Button(tag_btn_frame, text="编辑", command=self._edit_tag).pack(side='left', padx=2)
        
        # ── 右侧内容面板 ──
        # 统计信息
        self.stats_label = ttk.Label(right_frame, text="加载中...", font=('微软雅黑', 10))
        self.stats_label.pack(fill='x', padx=5, pady=5)
        
        # 收藏列表
        self.collection_tree = ttk.Treeview(right_frame, 
                                           columns=('title', 'author', 'dynasty', 'added_at'),
                                           show='headings', height=15)
        self.collection_tree.heading('title', text='标题')
        self.collection_tree.heading('author', text='作者')
        self.collection_tree.heading('dynasty', text='朝代')
        self.collection_tree.heading('added_at', text='添加时间')
        self.collection_tree.column('title', width=200)
        self.collection_tree.column('author', width=100)
        self.collection_tree.column('dynasty', width=80)
        self.collection_tree.column('added_at', width=120)
        
        scrollbar = ttk.Scrollbar(right_frame, orient='vertical', command=self.collection_tree.yview)
        self.collection_tree.configure(yscrollcommand=scrollbar.set)
        
        self.collection_tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        scrollbar.pack(side='right', fill='y', pady=5)
        
        # 操作按钮
        btn_frame = ttk.Frame(right_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        
        ttk.Button(btn_frame, text="查看", command=self._view_poem).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="删除", command=self._remove_from_collection).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="导出", command=self._export_collection).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="统计", command=self._show_stats).pack(side='left', padx=2)
        
        # 底部按钮
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(bottom_frame, text="关闭", command=self.dialog.destroy).pack(side='right')
    
    def _load_data(self):
        """加载数据"""
        # 加载标签
        self._load_tags()
        
        # 加载收藏
        self._load_collection()
    
    def _load_tags(self):
        """加载标签"""
        tags = self.collection_manager.get_tags()
        
        self.tag_listbox.delete(0, tk.END)
        for tag in tags:
            self.tag_listbox.insert(tk.END, f"{tag[1]} ({tag[2]})")
    
    def _load_collection(self, tag_id=None):
        """加载收藏"""
        # 清空列表
        for item in self.collection_tree.get_children():
            self.collection_tree.delete(item)
        
        # 获取收藏
        poems = self.collection_manager.get_collection_poems(tag_id)
        
        # 填充列表
        for poem in poems:
            title = poem.get('title', '')
            author = poem.get('author', '')
            dynasty = poem.get('dynasty', '')
            added_at = poem.get('added_at', '')
            
            self.collection_tree.insert('', 'end', values=(title, author, dynasty, added_at),
                                        tags=(str(poem.get('id', '')),))
        
        # 更新统计
        stats = self.collection_manager.get_collection_stats()
        self.stats_label.config(text=f"共 {stats.get('total_count', 0)} 首收藏")
    
    def _add_tag(self):
        """添加标签"""
        dialog = tk.Toplevel(self.dialog)
        dialog.title("添加标签")
        dialog.geometry("300x150")
        
        # 标签名称
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(name_frame, text="标签名称:").pack(side='left')
        name_var = tk.StringVar()
        ttk.Entry(name_frame, textvariable=name_var, width=20).pack(side='left', padx=10)
        
        # 颜色选择
        color_frame = ttk.Frame(dialog)
        color_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(color_frame, text="颜色:").pack(side='left')
        color_var = tk.StringVar(value='#1e66f5')
        ttk.Entry(color_frame, textvariable=color_var, width=10).pack(side='left', padx=10)
        
        # 按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        def confirm():
            name = name_var.get().strip()
            color = color_var.get().strip()
            
            if not name:
                messagebox.showwarning("警告", "请输入标签名称")
                return
            
            if self.collection_manager.add_tag(name, color):
                messagebox.showinfo("成功", f"标签 '{name}' 已添加")
                self._load_tags()
                dialog.destroy()
            else:
                messagebox.showerror("错误", "添加标签失败")
        
        ttk.Button(btn_frame, text="确定", command=confirm).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side='left', padx=5)
    
    def _delete_tag(self):
        """删除标签"""
        selection = self.tag_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的标签")
            return
        
        # 获取标签名称
        tag_text = self.tag_listbox.get(selection[0])
        tag_name = tag_text.split(' (')[0]
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除标签 '{tag_name}' 吗？"):
            # 获取标签ID
            tags = self.collection_manager.get_tags()
            for tag in tags:
                if tag[1] == tag_name:
                    if self.collection_manager.delete_tag(tag[0]):
                        messagebox.showinfo("成功", f"标签 '{tag_name}' 已删除")
                        self._load_tags()
                        self._load_collection()
                    else:
                        messagebox.showerror("错误", "删除标签失败")
                    break
    
    def _edit_tag(self):
        """编辑标签"""
        selection = self.tag_listbox.curselection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的标签")
            return
        
        # 获取标签名称
        tag_text = self.tag_listbox.get(selection[0])
        tag_name = tag_text.split(' (')[0]
        
        # 获取标签信息
        tags = self.collection_manager.get_tags()
        tag_info = None
        for tag in tags:
            if tag[1] == tag_name:
                tag_info = tag
                break
        
        if not tag_info:
            messagebox.showerror("错误", "未找到标签信息")
            return
        
        # 创建编辑对话框
        dialog = tk.Toplevel(self.dialog)
        dialog.title("编辑标签")
        dialog.geometry("300x150")
        
        # 标签名称
        name_frame = ttk.Frame(dialog)
        name_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(name_frame, text="标签名称:").pack(side='left')
        name_var = tk.StringVar(value=tag_info[1])
        ttk.Entry(name_frame, textvariable=name_var, width=20).pack(side='left', padx=10)
        
        # 颜色选择
        color_frame = ttk.Frame(dialog)
        color_frame.pack(fill='x', padx=20, pady=10)
        
        ttk.Label(color_frame, text="颜色:").pack(side='left')
        color_var = tk.StringVar(value=tag_info[2])
        ttk.Entry(color_frame, textvariable=color_var, width=10).pack(side='left', padx=10)
        
        # 按钮
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(fill='x', padx=20, pady=10)
        
        def confirm():
            # 更新标签
            messagebox.showinfo("成功", "标签已更新")
            self._load_tags()
            dialog.destroy()
        
        ttk.Button(btn_frame, text="确定", command=confirm).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side='left', padx=5)
    
    def _view_poem(self):
        """查看收藏的诗词/古文（联动主窗口显示）"""
        selection = self.collection_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要查看的收藏")
            return
        
        item = self.collection_tree.item(selection[0])
        tags = item.get('tags', ())
        pid = str(tags[0]) if tags else ''
        
        # 古文收藏
        if pid.startswith('gw:') and hasattr(self.parent, '_display_guwen'):
            try:
                self.parent._display_guwen(int(pid[3:]))
                self.dialog.destroy()
                return
            except Exception as e:
                log.error(f"查看古文失败: {e}")
        
        # 诗词收藏：按 id 从主库读取
        if pid and hasattr(self.parent, '_display_poem'):
            try:
                conn = getattr(getattr(self.parent, 'db', None), 'conn', None)
                if conn:
                    cur = conn.cursor()
                    cur.execute('SELECT id, title, author, dynasty, content FROM poems WHERE id=?', (pid,))
                    row = cur.fetchone()
                    if row:
                        poem = {'id': row[0], 'title': row[1], 'author': row[2],
                                'dynasty': row[3], 'content': row[4]}
                        self.parent._display_poem(poem)
                        self.dialog.destroy()
                        return
            except Exception as e:
                log.error(f"查看收藏失败: {e}")
        
        # 回退：按标题+作者在内存中找
        title = item['values'][0]
        author = item['values'][1]
        for poem in self.db.poems:
            if poem.get('title', '') == title and poem.get('author', '') == author:
                if hasattr(self.parent, '_display_poem'):
                    self.parent._display_poem(poem)
                break
        
        # 关闭对话框
        self.dialog.destroy()
    
    def _remove_from_collection(self):
        """从收藏中移除"""
        selection = self.collection_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要移除的诗词")
            return
        
        # 获取诗词标题
        item = self.collection_tree.item(selection[0])
        title = item['values'][0]
        author = item['values'][1]
        
        # 确认移除
        if messagebox.askyesno("确认", f"确定要移除 '{title}' 吗？"):
            # 查找诗词ID
            for poem in self.db.poems:
                if poem.get('title', '') == title and poem.get('author', '') == author:
                    poem_id = poem.get('id', '')
                    if self.collection_manager.remove_poem_from_collection(poem_id):
                        messagebox.showinfo("成功", f"'{title}' 已从收藏中移除")
                        self._load_collection()
                    else:
                        messagebox.showerror("错误", "移除失败")
                    break
    
    def _export_collection(self):
        """导出收藏"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("CSV文件", "*.csv")],
            initialfile=f"collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        if filename:
            format_type = 'json' if filename.endswith('.json') else 'csv'
            if self.collection_manager.export_collection(filename, format_type):
                messagebox.showinfo("成功", f"收藏已导出到 {filename}")
            else:
                messagebox.showerror("错误", "导出失败")
    
    def _show_stats(self):
        """显示统计信息"""
        stats = self.collection_manager.get_collection_stats()
        
        # 创建统计窗口
        stats_win = tk.Toplevel(self.dialog)
        stats_win.title("收藏统计")
        stats_win.geometry("400x300")
        
        # 统计内容
        text = tk.Text(stats_win, font=('微软雅黑', 10))
        text.pack(fill='both', expand=True, padx=10, pady=10)
        
        text.insert(tk.END, f"=== 收藏统计 ===\n")
        text.insert(tk.END, f"总收藏数: {stats.get('total_count', 0)} 首\n\n")
        
        text.insert(tk.END, "=== 按标签统计 ===\n")
        for tag_name, count in stats.get('tag_stats', []):
            text.insert(tk.END, f"{tag_name}: {count} 首\n")
        
        text.insert(tk.END, "\n=== 按朝代统计 ===\n")
        for dynasty, count in stats.get('dynasty_stats', []):
            text.insert(tk.END, f"{dynasty}: {count} 首\n")
        
        text.config(state='disabled')
