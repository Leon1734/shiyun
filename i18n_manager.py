#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多语言支持模块
功能：国际化、多语言界面、翻译支持
"""

import json
import sqlite3
import logging
from pathlib import Path

import tkinter as tk
from tkinter import ttk, messagebox

log = logging.getLogger("poetry")

# 翻译数据库路径
# 路径：优先 data 目录（与 exe 共享；打包后 _internal 只读）
try:
    from app_paths import get_data_dir as _get_data_dir
    TRANSLATIONS_DB = _get_data_dir() / "translations.db"
except Exception:
    TRANSLATIONS_DB = Path(__file__).parent / "data" / "translations.db"

# 默认翻译
DEFAULT_TRANSLATIONS = {
    'zh_CN': {
        'app_title': '古诗词桌面小工具',
        'random': '随机',
        'tang_poetry': '唐诗',
        'song_ci': '宋词',
        'yuan_qu': '元曲',
        'search': '搜索',
        'advanced_search': '高级搜索',
        'favorite': '收藏',
        'next': '下一首',
        'copy': '复制',
        'pinyin': '拼音',
        'read_aloud': '朗读',
        'card': '卡片',
        'stats': '统计',
        'export': '导出',
        'learning_mode': '学习模式',
        'poetry_game': '诗词游戏',
        'creation_assist': '创作辅助',
        'collection_manage': '收藏管理',
        'data_visualization': '数据可视化',
        'theme_toggle': '主题切换',
        'favorites': '收藏夹',
        'history': '历史',
        'loading': '加载中...',
        'total_poems': '共 {count} 首诗词',
        'total_poets': '{count} 位诗人',
        'search_results': '找到 {count} 首',
        'no_results': '没有找到结果',
        'added_to_favorites': '已添加到收藏夹',
        'already_in_favorites': '已经在收藏夹中',
        'copied_to_clipboard': '已复制到剪贴板',
        'export_success': '导出成功',
        'export_failed': '导出失败',
        'error': '错误',
        'warning': '警告',
        'info': '提示',
        'confirm': '确认',
        'cancel': '取消',
        'ok': '确定',
        'close': '关闭',
        'save': '保存',
        'delete': '删除',
        'edit': '编辑',
        'add': '添加',
        'settings': '设置',
        'help': '帮助',
        'about': '关于',
        'dynasty': '朝代',
        'author': '作者',
        'title': '标题',
        'content': '内容',
        'all': '全部',
        'poem_directory': '诗词目录',
        'loading_data': '正在加载数据...',
        'data_loaded': '数据加载完成',
        'cache_loaded': '从缓存加载',
        'index_built': '索引构建完成',
        'search_history': '搜索历史',
        'collection_stats': '收藏统计',
        'learning_progress': '学习进度',
        'game_scores': '游戏成绩',
        'daily_poem': '每日诗词',
        'random_poem': '随机诗词',
        'filter_by_dynasty': '按朝代筛选',
        'filter_by_author': '按作者筛选',
        'search_placeholder': '输入关键词搜索...',
        'no_poems_found': '没有找到诗词',
        'poem_displayed': '显示第 {index} 首',
        'total_found': '共找到 {count} 首',
    },
    'en_US': {
        'app_title': 'Chinese Poetry Desktop Tool',
        'random': 'Random',
        'tang_poetry': 'Tang Poetry',
        'song_ci': 'Song Ci',
        'yuan_qu': 'Yuan Qu',
        'search': 'Search',
        'advanced_search': 'Advanced Search',
        'favorite': 'Favorite',
        'next': 'Next',
        'copy': 'Copy',
        'pinyin': 'Pinyin',
        'read_aloud': 'Read Aloud',
        'card': 'Card',
        'stats': 'Stats',
        'export': 'Export',
        'learning_mode': 'Learning Mode',
        'poetry_game': 'Poetry Game',
        'creation_assist': 'Creation Assist',
        'collection_manage': 'Collection Manage',
        'data_visualization': 'Data Visualization',
        'theme_toggle': 'Toggle Theme',
        'favorites': 'Favorites',
        'history': 'History',
        'loading': 'Loading...',
        'total_poems': '{count} poems total',
        'total_poets': '{count} poets',
        'search_results': 'Found {count} poems',
        'no_results': 'No results found',
        'added_to_favorites': 'Added to favorites',
        'already_in_favorites': 'Already in favorites',
        'copied_to_clipboard': 'Copied to clipboard',
        'export_success': 'Export successful',
        'export_failed': 'Export failed',
        'error': 'Error',
        'warning': 'Warning',
        'info': 'Info',
        'confirm': 'Confirm',
        'cancel': 'Cancel',
        'ok': 'OK',
        'close': 'Close',
        'save': 'Save',
        'delete': 'Delete',
        'edit': 'Edit',
        'add': 'Add',
        'settings': 'Settings',
        'help': 'Help',
        'about': 'About',
        'dynasty': 'Dynasty',
        'author': 'Author',
        'title': 'Title',
        'content': 'Content',
        'all': 'All',
        'poem_directory': 'Poem Directory',
        'loading_data': 'Loading data...',
        'data_loaded': 'Data loaded',
        'cache_loaded': 'Loaded from cache',
        'index_built': 'Index built',
        'search_history': 'Search History',
        'collection_stats': 'Collection Stats',
        'learning_progress': 'Learning Progress',
        'game_scores': 'Game Scores',
        'daily_poem': 'Daily Poem',
        'random_poem': 'Random Poem',
        'filter_by_dynasty': 'Filter by Dynasty',
        'filter_by_author': 'Filter by Author',
        'search_placeholder': 'Enter keywords to search...',
        'no_poems_found': 'No poems found',
        'poem_displayed': 'Showing poem {index}',
        'total_found': 'Found {count} poems total',
    }
}


class TranslationManager:
    """翻译管理器"""
    
    def __init__(self):
        self.current_language = 'zh_CN'
        self.translations = DEFAULT_TRANSLATIONS.copy()
        self.conn = None
        self._init_database()
        self._load_translations()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.conn = sqlite3.connect(str(TRANSLATIONS_DB))
            cursor = self.conn.cursor()
            
            # 创建翻译表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL,
                    language TEXT NOT NULL,
                    value TEXT,
                    UNIQUE(key, language)
                )
            ''')
            
            self.conn.commit()
            log.info("翻译数据库初始化完成")
        except Exception as e:
            log.error(f"初始化翻译数据库失败: {e}")
    
    def _load_translations(self):
        """加载翻译"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT key, language, value FROM translations")
            
            for key, language, value in cursor.fetchall():
                if language not in self.translations:
                    self.translations[language] = {}
                self.translations[language][key] = value
            
            log.info(f"加载翻译完成: {len(self.translations)} 种语言")
        except Exception as e:
            log.error(f"加载翻译失败: {e}")
    
    def set_language(self, language):
        """设置当前语言"""
        if language in self.translations:
            self.current_language = language
            log.info(f"切换语言: {language}")
            return True
        return False
    
    def get_language(self):
        """获取当前语言"""
        return self.current_language
    
    def get_available_languages(self):
        """获取可用语言"""
        return list(self.translations.keys())
    
    def translate(self, key, **kwargs):
        """翻译"""
        # 获取当前语言的翻译
        lang_translations = self.translations.get(self.current_language, {})
        
        # 获取翻译文本
        text = lang_translations.get(key, key)
        
        # 格式化参数
        if kwargs:
            try:
                text = text.format(**kwargs)
            except:
                pass
        
        return text
    
    def add_translation(self, key, language, value):
        """添加翻译"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO translations (key, language, value)
                VALUES (?, ?, ?)
            ''', (key, language, value))
            self.conn.commit()
            
            # 更新内存中的翻译
            if language not in self.translations:
                self.translations[language] = {}
            self.translations[language][key] = value
            
            return True
        except Exception as e:
            log.error(f"添加翻译失败: {e}")
            return False
    
    def import_translations(self, filename):
        """导入翻译"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for language, translations in data.items():
                for key, value in translations.items():
                    self.add_translation(key, language, value)
            
            return True
        except Exception as e:
            log.error(f"导入翻译失败: {e}")
            return False
    
    def export_translations(self, filename):
        """导出翻译"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.translations, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            log.error(f"导出翻译失败: {e}")
            return False
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()


class LanguageSelector:
    """语言选择器"""
    
    def __init__(self, parent, translation_manager, callback=None):
        self.parent = parent
        self.translation_manager = translation_manager
        self.callback = callback
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("语言设置")
        self.dialog.geometry("300x200")
        
        # 创建界面
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="选择语言", 
                               font=('微软雅黑', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 语言列表
        self.language_var = tk.StringVar(value=self.translation_manager.get_language())
        
        languages = self.translation_manager.get_available_languages()
        for lang in languages:
            ttk.Radiobutton(main_frame, text=lang, variable=self.language_var, 
                           value=lang).pack(fill='x', pady=5)
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x', pady=(20, 0))
        
        ttk.Button(btn_frame, text="确定", command=self._apply_language).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side='left', padx=5)
    
    def _apply_language(self):
        """应用语言"""
        language = self.language_var.get()
        
        if self.translation_manager.set_language(language):
            if self.callback:
                self.callback(language)
            
            messagebox.showinfo("成功", f"语言已切换为: {language}")
            self.dialog.destroy()
        else:
            messagebox.showerror("错误", "切换语言失败")
