#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
古诗词桌面小工具 v6.0
基于 chinese-poetry 项目数据
功能：多语言支持、插件系统、云端同步

升级内容：
1. 多语言支持 - 国际化、多语言界面
2. 插件系统 - 插件加载、插件管理
3. 云端同步 - 数据备份、云端同步
"""

import json
import os
import random as rng
import re
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime
import threading
import webbrowser
import logging
import time
from collections import defaultdict

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("poetry")

# 数据目录（支持打包环境）
try:
    from app_paths import get_data_dir, get_db_path
    DATA_DIR = get_data_dir()
except ImportError:
    DATA_DIR = Path(__file__).parent / "data"

# 导入繁简转换模块
try:
    from converter import traditional_to_simplified, is_traditional
    HAS_CONVERTER = True
    log.info("繁简转换模块已加载")
except ImportError:
    HAS_CONVERTER = False
    log.warning("converter 模块未找到，繁简转换功能将不可用")

# 导入诗词分类模块
try:
    from poem_classifier import classify_poem, get_all_themes, get_theme_description
    HAS_CLASSIFIER = True
    log.info("诗词分类模块已加载")
except ImportError:
    HAS_CLASSIFIER = False
    log.warning("poem_classifier 模块未找到，分类功能将不可用")
    def classify_poem(title, content, author=""):
        return {'primary': '其他', 'secondary': '', 'imagery': [], 'confidence': 0}
    def get_all_themes():
        return []
    def get_theme_description(theme):
        return ""

# 导入工具模块
try:
    from poetry_utils import (
        get_pinyin, get_pinyin_lines, tts_speak,
        generate_poem_card_html, generate_poem_card_png,
        search_poems_by_mood, get_poem_stats,
        export_poems_to_txt, export_poems_to_csv,
        HAS_PINYIN, HAS_TTS
    )
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False
    log.warning("poetry_utils 模块未找到，部分功能将不可用")

# 导入v3.0模块
try:
    from learning import LearningManager
    HAS_LEARNING = True
except ImportError:
    HAS_LEARNING = False
    log.warning("learning 模块未找到，学习模式将不可用")

try:
    from game import GameManager
    HAS_GAME = True
except ImportError:
    HAS_GAME = False
    log.warning("game 模块未找到，游戏功能将不可用")

try:
    from creation import CreationManager
    HAS_CREATION = True
except ImportError:
    HAS_CREATION = False
    log.warning("creation 模块未找到，创作辅助将不可用")

try:
    from learning_ui import LearningMainUI
    HAS_LEARNING_UI = True
except ImportError:
    HAS_LEARNING_UI = False
    log.warning("learning_ui 模块未找到，学习界面将不可用")

try:
    from game_ui import GameMainUI
    HAS_GAME_UI = True
except ImportError:
    HAS_GAME_UI = False
    log.warning("game_ui 模块未找到，游戏界面将不可用")

try:
    from creation_ui import CreationEditor
    HAS_CREATION_UI = True
except ImportError:
    HAS_CREATION_UI = False
    log.warning("creation_ui 模块未找到，创作界面将不可用")

try:
    from integration import integrate as integrate_features
    HAS_INTEGRATION = True
except ImportError:
    HAS_INTEGRATION = False
    log.warning("integration 模块未找到，集成功能将不可用")

# 古文阅读器
try:
    from guwen_ui import GuwenReader
    HAS_GUWEN_UI = True
    log.info("古文阅读器模块已加载")
except ImportError:
    HAS_GUWEN_UI = False
    log.warning("guwen_ui 模块未找到，古文阅读功能将不可用")

# 导入v4.0模块
try:
    from ui_enhancements import UIEnhancer, AnimationManager
    HAS_UI_ENHANCER = True
    log.info("界面美化模块已加载")
except ImportError:
    HAS_UI_ENHANCER = False
    log.warning("ui_enhancements 模块未找到，界面美化功能将不可用")

try:
    from search_advanced import AdvancedSearchDialog, SearchHistory
    HAS_ADVANCED_SEARCH = True
    log.info("高级搜索模块已加载")
except ImportError:
    HAS_ADVANCED_SEARCH = False
    log.warning("search_advanced 模块未找到，高级搜索功能将不可用")

try:
    from collection_manager import CollectionManager, CollectionDialog
    HAS_COLLECTION_MANAGER = True
    log.info("收藏管理模块已加载")
except ImportError:
    HAS_COLLECTION_MANAGER = False
    log.warning("collection_manager 模块未找到，收藏管理功能将不可用")

# 导入v5.0模块
try:
    from data_visualization import ChartManager, VisualizationDialog
    HAS_VISUALIZATION = True
    log.info("数据可视化模块已加载")
except ImportError:
    HAS_VISUALIZATION = False
    log.warning("data_visualization 模块未找到，数据可视化功能将不可用")

try:
    from performance_optimizer import VirtualList, LazyLoader, MemoryOptimizer
    HAS_PERFORMANCE_OPTIMIZER = True
    log.info("性能优化模块已加载")
except ImportError:
    HAS_PERFORMANCE_OPTIMIZER = False
    log.warning("performance_optimizer 模块未找到，性能优化功能将不可用")

try:
    from ux_enhancements import ContextMenu, DragDropSupport, ToolbarCustomizer
    HAS_UX_ENHANCEMENTS = True
    log.info("用户体验模块已加载")
except ImportError:
    HAS_UX_ENHANCEMENTS = False
    log.warning("ux_enhancements 模块未找到，用户体验功能将不可用")

# 导入v6.0模块
try:
    from i18n_manager import TranslationManager, LanguageSelector
    HAS_I18N = True
    log.info("多语言模块已加载")
except ImportError:
    HAS_I18N = False
    log.warning("i18n_manager 模块未找到，多语言功能将不可用")

try:
    from plugin_system import PluginManager, PluginAPI, PluginConfigDialog
    HAS_PLUGIN_SYSTEM = True
    log.info("插件系统模块已加载")
except ImportError:
    HAS_PLUGIN_SYSTEM = False
    log.warning("plugin_system 模块未找到，插件系统功能将不可用")

try:
    from cloud_sync import CloudSyncManager, SyncDialog
    HAS_CLOUD_SYNC = True
    log.info("云端同步模块已加载")
except ImportError:
    HAS_CLOUD_SYNC = False
    log.warning("cloud_sync 模块未找到，云端同步功能将不可用")

# v7.0 主题系统
try:
    from ui_theme_v2 import THEMES_V2, apply_theme as apply_theme_v2, get_fonts
    HAS_THEME_V2 = True
    log.info("新版主题系统已加载")
except ImportError:
    HAS_THEME_V2 = False
    log.warning("ui_theme_v2 模块未找到，使用旧版主题")

# v7.0 功能（TTS/拼音/每日推荐）
try:
    from features_v7 import TTSEngine, get_pinyin_text, get_pinyin_line, DailyRecommender, HAS_PYPINYIN, HAS_EDGE_TTS
    HAS_FEATURES_V7 = True
    log.info("v7.0功能模块已加载 (TTS/拼音/每日推荐)")
except ImportError as e:
    HAS_FEATURES_V7 = False
    HAS_PYPINYIN = False
    log.warning(f"features_v7 模块未找到: {e}")

# v7.0 对话框（诗人档案/词牌词典/统一搜索）
try:
    from features_ui import PoetProfileWindow, CipaiWindow, UnifiedSearchWindow
    HAS_FEATURES_UI = True
    log.info("v7.0对话框模块已加载 (诗人档案/词牌词典/统一搜索)")
except ImportError as e:
    HAS_FEATURES_UI = False
    log.warning(f"features_ui 模块未找到: {e}")

# v7.0 卡片生成器
try:
    from card_generator import generate_classic_card
    HAS_CARD_V2 = True
except ImportError:
    HAS_CARD_V2 = False

# 词牌词典
try:
    from cipai_dict import get_cipai_info
    HAS_CIPAI_DICT = True
except ImportError:
    HAS_CIPAI_DICT = False

# 名句欣赏
try:
    from quotes_ui import QuotesWindow
    HAS_QUOTES_UI = True
except ImportError:
    HAS_QUOTES_UI = False


# ── 主题配置 ──────────────────────────────────────────────────────────────────

if HAS_THEME_V2:
    # 使用新版古典主题（宣纸/墨色）
    THEMES = THEMES_V2
else:
    THEMES = {
        "dark": {
            "bg":           "#1e1e2e",
            "bg_secondary": "#2a2a3d",
            "bg_tertiary":  "#363650",
            "fg":           "#cdd6f4",
            "fg_secondary": "#a6adc8",
            "accent":       "#89b4fa",
            "accent_hover": "#74c7ec",
            "success":      "#a6e3a1",
            "warning":      "#f9e2af",
            "error":        "#f38ba8",
            "border":       "#45475a",
            "select_bg":    "#45475a",
            "select_fg":    "#cdd6f4",
            "button_bg":    "#313244",
            "button_fg":    "#cdd6f4",
            "entry_bg":     "#313244",
            "entry_fg":     "#cdd6f4",
            "scrollbar":    "#585b70",
            "tooltip_bg":   "#45475a",
        },
        "light": {
            "bg":           "#eff1f5",
            "bg_secondary": "#e6e9ef",
            "bg_tertiary":  "#ccd0da",
            "fg":           "#4c4f69",
            "fg_secondary": "#6c6f85",
            "accent":       "#1e66f5",
            "accent_hover": "#2a7ae9",
            "success":      "#40a02b",
            "warning":      "#df8e1d",
            "error":        "#d20f39",
            "border":       "#bcc0cc",
            "select_bg":    "#bcc0cc",
            "select_fg":    "#4c4f69",
            "button_bg":    "#ccd0da",
            "button_fg":    "#4c4f69",
            "entry_bg":     "#e6e9ef",
            "entry_fg":     "#4c4f69",
            "scrollbar":    "#9ca0b0",
            "tooltip_bg":   "#ccd0da",
        }
    }


class PoetryDB:
    """诗词数据库（SQLite 高速版）"""
    
    def __init__(self, on_progress=None):
        self.poems = []
        self.authors = set()
        self.dynasties = set()
        self.author_index = defaultdict(list)
        self.dynasty_index = defaultdict(list)
        self.conn = None
        
        db_path = DATA_DIR / "poetry.db"
        
        if db_path.exists():
            self._load_from_sqlite(db_path, on_progress)
        else:
            log.warning(f"SQLite 数据库不存在: {db_path}")
            log.warning("请先运行: python json_to_sqlite.py")
            self._load_from_json_fallback(on_progress)
    
    def _load_from_sqlite(self, db_path, on_progress=None):
        """从 SQLite 加载"""
        log.info(f"从 SQLite 加载: {db_path}")
        import sqlite3
        start_time = time.time()
        
        try:
            self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            self.conn.execute("PRAGMA cache_size=-32000")
            self.conn.execute("PRAGMA mmap_size=268435456")
            
            cursor = self.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM poems')
            total = cursor.fetchone()[0]
            
            cursor.execute('SELECT id, title, author, dynasty, theme, poem_form, chars_per_line, collection FROM poems ORDER BY id')
            
            count = 0
            for row in cursor:
                poem = {
                    'id': row['id'], 
                    'title': row['title'], 
                    'author': row['author'], 
                    'dynasty': row['dynasty'], 
                    'theme': row['theme'] if row['theme'] else '',
                    'poem_form': row['poem_form'] if row['poem_form'] else '',
                    'chars_per_line': row['chars_per_line'] if row['chars_per_line'] else 0,
                    'collection': row['collection'] if row['collection'] else ''
                }
                self.poems.append(poem)
                self.authors.add(poem['author'])
                self.dynasties.add(poem['dynasty'])
                self.author_index[poem['author']].append(count)
                self.dynasty_index[poem['dynasty']].append(count)
                count += 1
            
            elapsed = time.time() - start_time
            log.info(f"加载完成: {count:,} 首诗词, {len(self.authors):,} 位诗人, 耗时 {elapsed:.2f}秒")
        
        except Exception as e:
            log.error(f"SQLite 加载失败: {e}")
    
    def _load_from_json_fallback(self, on_progress=None):
        """JSON 回退加载"""
        log.info("使用 JSON 回退加载...")
        import json
        tang_dir = DATA_DIR / "全唐诗"
        if tang_dir.exists():
            for json_file in list(tang_dir.glob("poet.tang.*.json"))[:5]:
                try:
                    with open(json_file, encoding='utf-8') as f:
                        for poem in json.load(f):
                            if 'title' in poem and 'author' in poem:
                                self.poems.append({
                                    'title': poem['title'], 'author': poem['author'],
                                    'dynasty': '唐', 'content': '\n'.join(poem.get('paragraphs', []))
                                })
                except: pass
        log.info(f"JSON 回退: {len(self.poems)} 首")
    
    def _get_content(self, idx):
        """按需从 SQLite 获取内容（按真实id查询，兼容去重后的id间隙）"""
        if not self.conn: return ''
        try:
            if 0 <= idx < len(self.poems):
                poem_id = self.poems[idx].get('id')
            else:
                return ''
            if poem_id is None:
                return ''
            cursor = self.conn.cursor()
            cursor.execute('SELECT content FROM poems WHERE id = ?', (poem_id,))
            row = cursor.fetchone()
            return row[0] if row else ''
        except: return ''
    
    def random_one(self, dynasty=None, author=None, classic_bias=True):
        """随机一首（无筛选时经典加权：75% 从经典池抽取，25% 全库随机）"""
        if not self.poems: return None
        if dynasty:
            indices = self.dynasty_index.get(dynasty, [])
            if not indices: return None
            idx = rng.choice(indices)
        elif author:
            indices = self.author_index.get(author, [])
            if not indices: return None
            idx = rng.choice(indices)
        else:
            # 无筛选：经典加权（60% 耳熟能详池 >=90 / 25% 著名诗人池 >=60 / 15% 全库发现）
            if classic_bias and self.conn:
                try:
                    r = rng.random()
                    threshold = 90 if r < 0.60 else (60 if r < 0.85 else None)
                    cursor = self.conn.cursor()
                    if threshold:
                        cursor.execute('SELECT id, title, author, dynasty FROM poems WHERE classic_score >= ? ORDER BY RANDOM() LIMIT 1', (threshold,))
                        row = cursor.fetchone()
                        if row:
                            cursor.execute('SELECT content FROM poems WHERE id = ?', (row[0],))
                            crow = cursor.fetchone()
                            return {'id': row[0], 'title': row[1], 'author': row[2], 'dynasty': row[3],
                                    'content': crow[0] if crow else ''}
                except Exception as e:
                    log.error(f"经典随机失败: {e}")
            idx = rng.randint(0, len(self.poems) - 1)
        poem = self.poems[idx].copy()
        poem['content'] = self._get_content(idx)
        return poem
    
    def search(self, keyword, limit=50):
        """搜索（LIKE 全文匹配，优先标题/作者，名篇精选优先）：返回带 id 的结果"""
        keyword = keyword.strip()
        if not keyword or not self.conn: return []
        try:
            cursor = self.conn.cursor()
            # 标题/作者优先，再内容匹配；同级中"名篇精选"排前
            cursor.execute('''
                SELECT id, title, author, dynasty, content FROM poems
                WHERE title LIKE ? OR author LIKE ?
                ORDER BY 
                    CASE WHEN title LIKE ? THEN 0 
                         WHEN author LIKE ? THEN 1 
                         ELSE 2 END,
                    classic_score DESC, id
                LIMIT ?
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
            results = [{'id': r[0], 'title': r[1], 'author': r[2], 'dynasty': r[3], 'content': r[4]} 
                       for r in cursor.fetchall()]
            
            # 补充内容匹配
            if len(results) < limit:
                need = limit - len(results)
                cursor.execute('''
                    SELECT id, title, author, dynasty, content FROM poems
                    WHERE content LIKE ?
                    ORDER BY classic_score DESC, id
                    LIMIT ?
                ''', (f'%{keyword}%', need * 3))
                seen = {r['id'] for r in results}
                for r in cursor.fetchall():
                    if r[0] not in seen and len(results) < limit:
                        results.append({'id': r[0], 'title': r[1], 'author': r[2], 
                                       'dynasty': r[3], 'content': r[4]})
            
            return results
        except Exception as e:
            log.error(f"搜索失败: {e}")
            return []
    
    def get_authors(self): return sorted(self.authors)
    def get_dynasties(self): return sorted(self.dynasties)


class PoetryApp:
    """主应用"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("古诗词桌面小工具 v7.0 · 诗韵")
        
        # 读取用户偏好（窗口位置/主题/字号）
        self._prefs = self._load_prefs()
        geom = self._prefs.get('geometry', '')
        if not (isinstance(geom, str) and re.match(r'^\d+x\d+([+-]\d+[+-]\d+)?$', geom.strip())):
            geom = "1280x820"
        self.root.geometry(geom)
        self.root.minsize(1100, 700)
        
        # 主题（恢复上次选择）
        self.current_theme = self._prefs.get('theme', 'light')
        if self.current_theme not in THEMES:
            self.current_theme = 'light'
        self.theme_colors = THEMES[self.current_theme]
        
        # 字体
        if HAS_THEME_V2:
            self.fonts = get_fonts()
        else:
            self.fonts = {'poem': ('楷体', 16), 'title': ('华文中宋', 20, 'bold'), 
                         'ui': ('微软雅黑', 10), 'ui_small': ('微软雅黑', 9),
                         'ui_bold': ('微软雅黑', 10, 'bold'), 'ui_large': ('微软雅黑', 12, 'bold'),
                         'poem_large': ('楷体', 20), 'poem_small': ('楷体', 13),
                         'title_small': ('华文中宋', 14, 'bold'), 'pinyin': ('Arial', 10),
                         'prose': ('仿宋', 13)}
        
        # 数据库
        self.db = None
        self.current_poem = None
        self.favorites = []
        self.history = []
        self.max_history = 100
        
        # 拼音显示状态
        self.show_pinyin = False
        
        # 字号（可调节，恢复上次设置）
        try:
            self.poem_font_size = int(self._prefs.get('font_size', 20))
        except Exception:
            self.poem_font_size = 20
        if not (12 <= self.poem_font_size <= 48):
            self.poem_font_size = 20
        
        # 视图模式: 'poem' 诗词 | 'guwen' 古文
        self.view_mode = 'poem'
        
        # v7.0 功能
        self.tts_engine = None
        self.daily_recommender = None
        if HAS_FEATURES_V7:
            self.tts_engine = TTSEngine()
            self.daily_recommender = DailyRecommender(DATA_DIR / "poetry.db")
        
        # 新功能模块
        self.learning_manager = None
        self.game_manager = None
        self.creation_manager = None
        self.collection_manager = None
        self.chart_manager = None
        
        # v6.0模块
        self.translation_manager = None
        self.plugin_manager = None
        self.cloud_sync_manager = None
        
        # UI增强器
        self.ui_enhancer = None
        self.animation_manager = None
        self.context_menu = None
        self.toolbar_customizer = None
        
        # 初始化样式
        self._init_styles()
        
        # 初始化v6.0模块
        self._init_v6_modules()
        
        # 创建界面
        self._create_widgets()
        
        # 绑定快捷键
        self._bind_shortcuts()
        
        # 加载收藏
        self._load_favorites()
        
        # 窗口关闭时保存偏好
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 异步加载数据
        self._load_data_async()
    
    def _load_prefs(self):
        """读取用户偏好"""
        try:
            p = DATA_DIR / 'user_prefs.json'
            if p.exists():
                data = json.loads(p.read_text(encoding='utf-8'))
                if isinstance(data, dict):
                    return data
        except Exception as e:
            log.debug(f"读取偏好失败: {e}")
        return {}
    
    def _save_prefs(self):
        """保存用户偏好（窗口位置/主题/字号）"""
        try:
            data = dict(getattr(self, '_prefs', {}) or {})
            data.update({
                'geometry': self.root.geometry(),
                'theme': self.current_theme,
                'font_size': self.poem_font_size,
            })
            p = DATA_DIR / 'user_prefs.json'
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        except Exception as e:
            log.debug(f"保存偏好失败: {e}")
    
    def _on_close(self):
        """关闭前保存偏好并退出"""
        self._save_prefs()
        try:
            self.root.destroy()
        except Exception:
            pass
    
    def _init_styles(self):
        """初始化样式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 配置主题样式
        self._apply_theme()
    
    def _apply_theme(self):
        """应用主题"""
        if HAS_THEME_V2:
            # 使用新版主题系统（完整样式配置）
            self.theme_colors, self.fonts = apply_theme_v2(self.root, self.current_theme)
            colors = self.theme_colors
            # 更新样式后的组件刷新
            if hasattr(self, 'dir_tree'):
                try:
                    self.dir_tree.tag_configure('oddrow', background=colors.get('tree_stripe', ''))
                    self.dir_tree.tag_configure('evenrow', background=colors.get('bg_card', ''))
                except:
                    pass
            return
        
        colors = self.theme_colors
        style = ttk.Style()
        
        style.configure('TFrame', background=colors['bg'])
        style.configure('TLabel', background=colors['bg'], foreground=colors['fg'])
        style.configure('TButton', 
                       background=colors['button_bg'], 
                       foreground=colors['button_fg'],
                       borderwidth=1,
                       relief='flat')
        style.map('TButton',
                 background=[('active', colors['accent']), ('pressed', colors['accent_hover'])],
                 foreground=[('active', colors['fg']), ('pressed', colors['fg'])])
        
        style.configure('TEntry',
                       fieldbackground=colors['entry_bg'],
                       foreground=colors['entry_fg'],
                       borderwidth=1,
                       relief='flat')
        
        style.configure('TCombobox',
                       fieldbackground=colors['entry_bg'],
                       foreground=colors['entry_fg'],
                       borderwidth=1,
                       relief='flat')
        
        style.configure('Treeview',
                       background=colors['bg_secondary'],
                       foreground=colors['fg'],
                       fieldbackground=colors['bg_secondary'],
                       borderwidth=1,
                       relief='flat')
        style.configure('Treeview.Heading',
                       background=colors['bg_tertiary'],
                       foreground=colors['fg'],
                       borderwidth=1,
                       relief='flat')
        
        # 配置根窗口背景
        self.root.configure(background=colors['bg'])
    
    def _init_v6_modules(self):
        """初始化v6.0模块"""
        # 初始化多语言模块
        if HAS_I18N:
            self.translation_manager = TranslationManager()
            log.info("多语言管理器已初始化")
        
        # 初始化插件系统
        if HAS_PLUGIN_SYSTEM:
            self.plugin_manager = PluginManager()
            log.info("插件管理器已初始化")
        
        # 初始化云端同步
        if HAS_CLOUD_SYNC:
            self.cloud_sync_manager = CloudSyncManager()
            log.info("云端同步管理器已初始化")
    
    def _toggle_theme(self):
        """切换主题"""
        self.current_theme = "dark" if self.current_theme == "light" else "light"
        self.theme_colors = THEMES[self.current_theme]
        self._apply_theme()
        self._refresh_card_colors()
        log.info(f"切换到{self.current_theme}主题")
    
    def _refresh_card_colors(self):
        """刷新卡片颜色（tk原生组件需手动更新）"""
        try:
            colors = self.theme_colors
            card_bg = colors.get('bg_card', colors['bg_secondary'])
            border = colors.get('border', colors['bg_tertiary'])
            
            if hasattr(self, 'poem_card_frame'):
                self.poem_card_frame.config(bg=border)
            if hasattr(self, 'poem_inner_frame'):
                self.poem_inner_frame.config(bg=card_bg)
            if hasattr(self, 'title_label'):
                self.title_label.config(bg=card_bg, fg=colors['fg'])
            if hasattr(self, 'author_label'):
                self.author_label.config(bg=card_bg, fg=colors.get('fg_secondary', colors['fg']))
            if hasattr(self, 'content_text'):
                self.content_text.config(bg=card_bg, fg=colors['fg'])
            
            # 重渲染内容（更新注音/诗句标签颜色）
            if hasattr(self, 'current_poem') and self.current_poem:
                content = self.current_poem.get('content', '')
                if isinstance(content, list):
                    content = '\n'.join(content)
                if HAS_CONVERTER:
                    content = traditional_to_simplified(content)
                self._render_content(content)
            
            # 更新所有tk.Frame子组件背景
            def update_children(widget):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame) and not isinstance(child, ttk.Frame):
                        try:
                            child.config(bg=card_bg)
                        except:
                            pass
                    update_children(child)
            
            if hasattr(self, 'poem_inner_frame'):
                update_children(self.poem_inner_frame)
        except Exception as e:
            log.debug(f"刷新卡片颜色: {e}")
    
    def _load_data_async(self):
        """异步加载数据"""
        def _load():
            self.db = PoetryDB()
            # 防御性重试：确保回调一定送达主线程
            for _ in range(100):
                try:
                    self.root.after(0, self._on_data_loaded)
                    break
                except RuntimeError:
                    time.sleep(0.1)
        
        thread = threading.Thread(target=_load, daemon=True)
        thread.start()
    
    def _on_data_loaded(self):
        """数据加载完成回调"""
        log.info("数据加载完成")
        
        # 初始化新功能模块
        if HAS_LEARNING:
            self.learning_manager = LearningManager(self.db)
            log.info("学习模式模块已加载")
        
        if HAS_GAME:
            self.game_manager = GameManager(self.db)
            log.info("游戏化模块已加载")
        
        if HAS_CREATION:
            self.creation_manager = CreationManager(self.db)
            log.info("创作辅助模块已加载")
        
        if HAS_COLLECTION_MANAGER:
            self.collection_manager = CollectionManager(self.db)
            log.info("收藏管理模块已加载")
        
        if HAS_VISUALIZATION:
            self.chart_manager = ChartManager(self.db)
            log.info("数据可视化模块已加载")
        
        # 加载插件
        if HAS_PLUGIN_SYSTEM:
            loaded_count = self.plugin_manager.load_all_plugins()
            log.info(f"加载了 {loaded_count} 个插件")
        
        # 更新目录
        self._update_directory()
        
        # 动态更新合集筛选列表
        try:
            if self.db and self.db.conn and hasattr(self, 'collection_combo'):
                cursor = self.db.conn.cursor()
                cursor.execute("SELECT DISTINCT collection FROM poems WHERE collection != '' ORDER BY collection")
                colls = ['全部'] + [r[0] for r in cursor.fetchall()]
                self.collection_combo['values'] = colls
                log.info(f"合集筛选器已更新: {len(colls)-1} 个合集")
        except Exception as e:
            log.debug(f"更新合集列表失败: {e}")
        
        # 显示随机诗句
        self._show_random()
        
        # 更新状态栏
        self.status_label.config(text=f"共 {len(self.db.poems)} 首诗词 | {len(self.db.authors)} 位诗人")
    
    
    def _filter_directory(self):
        """按朝代筛选目录（重置分页）"""
        self.page_var.set(1)
        self._update_directory()
    
    def _search_directory(self):
        """搜索目录"""
        if not self.db:
            return
        
        keyword = self.dir_search_var.get().strip()
        if not keyword:
            self._update_directory()
            return
        
        results = self.db.search(keyword, limit=200)
        self._update_directory(results)
    
    def _random_from_filter(self):
        """从当前筛选结果中随机一首"""
        if not self.db:
            return
        
        # 获取当前筛选条件
        dynasty = self.dynasty_var.get()
        author = self.author_filter_var.get().strip()
        
        # 随机选择
        poem = self.db.random_one(
            dynasty=dynasty if dynasty != '全部' else None,
            author=author if author else None
        )
        
        if poem:
            self._display_poem(poem)
    
    def _prev_page(self):
        """上一页"""
        if self.page_var.get() > 1:
            self.page_var.set(self.page_var.get() - 1)
            self._update_directory()
    
    def _next_page(self):
        """下一页"""
        # 计算总页数
        total = len(self._get_filtered_poems())
        total_pages = (total + self.page_size - 1) // self.page_size
        
        if self.page_var.get() < total_pages:
            self.page_var.set(self.page_var.get() + 1)
            self._update_directory()
    
    def _get_filtered_poems(self):
        """获取筛选后的诗词列表"""
        if not self.db:
            return []
        
        dynasty = self.dynasty_var.get()
        author = self.author_filter_var.get().strip()
        theme = self.theme_var.get() if hasattr(self, 'theme_var') else '全部'
        poem_form = self.poem_form_var.get() if hasattr(self, 'poem_form_var') else '全部'
        chars_per_line = self.chars_per_line_var.get() if hasattr(self, 'chars_per_line_var') else '全部'
        collection = self.collection_var.get() if hasattr(self, 'collection_var') else '全部'
        
        # 使用SQL查询（更快）
        if self.db.conn:
            try:
                cursor = self.db.conn.cursor()
                query = "SELECT id, title, author, dynasty, theme, poem_form, chars_per_line, collection FROM poems WHERE 1=1"
                params = []
                
                if dynasty != '全部':
                    query += " AND dynasty = ?"
                    params.append(dynasty)
                
                if author:
                    query += " AND author LIKE ?"
                    params.append(f"%{author}%")
                
                if theme != '全部' and HAS_CLASSIFIER:
                    query += " AND theme = ?"
                    params.append(theme)
                
                if poem_form != '全部':
                    query += " AND poem_form = ?"
                    params.append(poem_form)
                
                if chars_per_line == '5字':
                    query += " AND chars_per_line = 5"
                elif chars_per_line == '7字':
                    query += " AND chars_per_line = 7"
                elif chars_per_line == '其他':
                    query += " AND chars_per_line NOT IN (5, 7)"
                
                if collection != '全部':
                    query += " AND collection = ?"
                    params.append(collection)
                
                query += " ORDER BY classic_score DESC, id"
                cursor.execute(query, params)
                
                poems = []
                for row in cursor:
                    poems.append({
                        'id': row[0],
                        'title': row[1],
                        'author': row[2],
                        'dynasty': row[3],
                        'theme': row[4] if len(row) > 4 else '',
                        'poem_form': row[5] if len(row) > 5 else '',
                        'chars_per_line': row[6] if len(row) > 6 else 0,
                        'collection': row[7] if len(row) > 7 else ''
                    })
                return poems
            except Exception as e:
                log.error(f"SQL筛选失败: {e}")
        
        # 降级到内存筛选
        poems = self.db.poems
        
        if dynasty != '全部':
            poems = [p for p in poems if p.get('dynasty', '') == dynasty]
        
        if author:
            poems = [p for p in poems if author in p.get('author', '')]
        
        if theme != '全部' and HAS_CLASSIFIER:
            poems = [p for p in poems if p.get('theme', '') == theme]
        
        if poem_form != '全部':
            poems = [p for p in poems if p.get('poem_form', '') == poem_form]
        
        if chars_per_line == '5字':
            poems = [p for p in poems if p.get('chars_per_line', 0) == 5]
        elif chars_per_line == '7字':
            poems = [p for p in poems if p.get('chars_per_line', 0) == 7]
        elif chars_per_line == '其他':
            poems = [p for p in poems if p.get('chars_per_line', 0) not in (5, 7)]
        
        if collection != '全部':
            poems = [p for p in poems if p.get('collection', '') == collection]
        
        return poems
    
    def _ensure_poem_mode(self):
        """诗词专属操作前自动切回诗词模式（修正古文模式下的列表状态混用）"""
        if self.view_mode == 'poem':
            return
        self.view_mode = 'poem'
        try:
            self.dir_title.config(text="📚 诗词目录")
            self.dir_tree.heading('title', text='标题')
            self.dir_tree.heading('author', text='作者')
            self.dir_tree.heading('dynasty', text='朝代')
            self.dir_tree.heading('theme', text='题材')
            self.dir_tree.heading('form', text='诗体')
            if HAS_THEME_V2:
                self.mode_poem_btn.config(style='Accent.TButton')
                self.mode_guwen_btn.config(style='TButton')
        except Exception:
            pass
    
    def _update_directory(self, poems=None):
        """更新目录列表（带分页）"""
        if not self.db:
            return
        
        # 诗词列表操作 → 确保切回诗词模式
        self._ensure_poem_mode()
        
        # 清空目录
        for item in self.dir_tree.get_children():
            self.dir_tree.delete(item)
        
        # 获取要显示的诗词
        if poems is None:
            poems = self._get_filtered_poems()
        
        # 存储当前筛选列表（供顺序导航使用）
        self._all_filtered_poems = poems
        
        # 分页
        total = len(poems)
        total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        
        # 确保页码有效
        if self.page_var.get() > total_pages:
            self.page_var.set(total_pages)
        
        start_idx = (self.page_var.get() - 1) * self.page_size
        end_idx = min(start_idx + self.page_size, total)
        
        page_poems = poems[start_idx:end_idx]
        
        # 填充目录
        for i, poem in enumerate(page_poems):
            title = poem.get('title', '')
            author = poem.get('author', '')
            dynasty = poem.get('dynasty', '')
            theme = poem.get('theme', '')
            poem_form = poem.get('poem_form', '')
            
            # 繁简转换
            if HAS_CONVERTER:
                title = traditional_to_simplified(title)
                author = traditional_to_simplified(author)
            
            # 斑马纹
            stripe = 'oddrow' if i % 2 else 'evenrow'
            self.dir_tree.insert('', 'end', values=(title, author, dynasty, theme, poem_form), 
                                tags=(poem.get('id', ''), stripe))
        
        # 更新分页标签
        self.page_label.config(text=f"{self.page_var.get()}/{total_pages}")
        
        # 更新统计
        self.dir_stats_label.config(text=f"显示 {start_idx+1}-{end_idx} 首 | 共 {total} 首")
    
    def _on_directory_select(self, event):
        """目录点击事件（诗词/古文双模式）"""
        selection = self.dir_tree.selection()
        if not selection:
            return
        
        # 获取选中的条目ID
        item = self.dir_tree.item(selection[0])
        tags = item.get('tags', ())
        if not tags:
            return
        
        tag0 = str(tags[0])
        
        # 古文模式
        if tag0.startswith('gw:'):
            try:
                self._display_guwen(int(tag0[3:]))
            except ValueError:
                pass
            return
        
        # 诗词模式
        if getattr(self, '_nav_syncing', False):
            return  # 程序化同步选中，不重复处理
        
        # 记录顺序导航位置
        try:
            tree_pos = self.dir_tree.index(selection[0])
            self._nav_index = (self.page_var.get() - 1) * self.page_size + tree_pos
        except Exception:
            self._nav_index = -1
        
        poem_id = tag0
        for poem in self.db.poems:
            if str(poem.get('id', '')) == str(poem_id):
                self._display_poem(poem)
                break
        
        # 状态栏位置指示
        try:
            lst = getattr(self, '_all_filtered_poems', None)
            if lst and self._nav_index >= 0:
                self.status_label.config(text=f"第 {self._nav_index + 1} / {len(lst)} 首 · ← → 键切换")
        except Exception:
            pass
    
    def _switch_mode(self, mode):
        """切换 诗词/古文 视图模式"""
        if self.view_mode == mode:
            return
        self.view_mode = mode
        
        # 更新按钮选中态
        try:
            if HAS_THEME_V2:
                if mode == 'guwen':
                    self.mode_guwen_btn.config(style='Accent.TButton')
                    self.mode_poem_btn.config(style='TButton')
                else:
                    self.mode_poem_btn.config(style='Accent.TButton')
                    self.mode_guwen_btn.config(style='TButton')
        except Exception:
            pass
        
        if mode == 'guwen':
            self.dir_title.config(text="📜 古文目录")
            # 列标题改为古文视图
            self.dir_tree.heading('title', text='篇名')
            self.dir_tree.heading('author', text='作者')
            self.dir_tree.heading('dynasty', text='朝代')
            self.dir_tree.heading('theme', text='合集')
            self.dir_tree.heading('form', text='字数')
            self._load_guwen_directory()
        else:
            self.dir_title.config(text="📚 诗词目录")
            # 恢复诗词视图列标题
            self.dir_tree.heading('title', text='标题')
            self.dir_tree.heading('author', text='作者')
            self.dir_tree.heading('dynasty', text='朝代')
            self.dir_tree.heading('theme', text='题材')
            self.dir_tree.heading('form', text='诗体')
            self.page_var.set(1)
            self._update_directory()
    
    def _load_guwen_directory(self):
        """加载古文目录到左侧列表"""
        if not self.db or not self.db.conn:
            return
        
        # 清空
        for item in self.dir_tree.get_children():
            self.dir_tree.delete(item)
        
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("SELECT id, title, author, dynasty, collection, char_count FROM guwen ORDER BY collection, id")
            rows = cursor.fetchall()
        except Exception as e:
            log.error(f"加载古文目录失败: {e}")
            return
        
        # 合集分组显示
        current_collection = None
        i = 0
        for row in rows:
            gid, title, author, dynasty, collection, char_count = row
            collection = collection or '其他'
            
            # 插入合集分组节点
            if collection != current_collection:
                current_collection = collection
                self.dir_tree.insert('', 'end', values=(f"▼ {collection}", '', '', '', ''), 
                                    tags=('group', 'grouprow'))
            
            title = traditional_to_simplified(title) if HAS_CONVERTER else title
            author = traditional_to_simplified(author) if HAS_CONVERTER else author
            stripe = 'oddrow' if i % 2 else 'evenrow'
            i += 1
            self.dir_tree.insert('', 'end',
                values=(f"    {title}", author, dynasty, collection, f"{char_count or 0}字"),
                tags=(f'gw:{gid}', stripe))
        
        self.page_label.config(text="1/1")
        self.dir_stats_label.config(text=f"共 {len(rows)} 篇古文")
    
    def _display_guwen(self, gid):
        """在右侧内容区显示古文"""
        if not self.db or not self.db.conn:
            return
        
        try:
            cursor = self.db.conn.cursor()
            cursor.execute("""SELECT id, title, author, dynasty, content, translation, 
                              appreciation, collection, char_count FROM guwen WHERE id=?""", (gid,))
            row = cursor.fetchone()
        except Exception as e:
            log.error(f"加载古文失败: {e}")
            return
        
        if not row:
            return
        
        gid, title, author, dynasty, content, translation, appreciation, collection, char_count = row
        
        if HAS_CONVERTER:
            title = traditional_to_simplified(title)
            author = traditional_to_simplified(author)
            content = traditional_to_simplified(content or '')
        
        self.current_poem = {
            'id': f'gw:{gid}', 'type': 'guwen', 'title': title, 'author': author,
            'dynasty': dynasty, 'content': content, 'collection': collection or '',
            'translation': translation or '', 'appreciation': appreciation or '',
        }
        
        self.title_label.config(text=f"《{title}》")
        author_text = f"· {author} ({dynasty})"
        if collection:
            author_text += f" · {collection}"
        if char_count:
            author_text += f" · {char_count}字"
        self.author_label.config(text=author_text)
        
        # 渲染正文（古文用仿宋左对齐）
        self._render_guwen_content(content)
        
        # 显示详细解读按钮（若有译文/赏析）
        self._add_history(self.current_poem)
        self.status_label.config(text=f"古文: 《{title}》{author}")
    
    def _render_guwen_content(self, content):
        """渲染古文内容（仿宋、左对齐）"""
        self.content_text.config(state='normal')
        self.content_text.delete('1.0', tk.END)
        self.content_text.insert(tk.END, content, 'guwen')
        self.content_text.tag_config('guwen',
            font=('仿宋', 15),
            foreground=self.theme_colors.get('fg', '#2B2B2B'),
            justify='left', spacing1=5, spacing3=5,
            lmargin1=30, lmargin2=30, rmargin=30)
        self.content_text.config(state='disabled')
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架 - 使用PanedWindow实现左右分栏
        main_paned = ttk.PanedWindow(self.root, orient='horizontal')
        main_paned.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 左侧目录面板
        left_frame = ttk.Frame(main_paned, width=300)
        main_paned.add(left_frame, weight=0)
        
        # 右侧内容面板
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # ── 左侧目录面板 ──
        # 模式切换（诗词 / 古文）
        mode_frame = ttk.Frame(left_frame)
        mode_frame.pack(fill='x', padx=5, pady=(8, 2))
        
        self.mode_poem_btn = ttk.Button(mode_frame, text="📚 诗词", 
                                        style='Accent.TButton' if HAS_THEME_V2 else 'TButton',
                                        command=lambda: self._switch_mode('poem'))
        self.mode_poem_btn.pack(side='left', expand=True, fill='x', padx=1)
        self.mode_guwen_btn = ttk.Button(mode_frame, text="📜 古文", 
                                         command=lambda: self._switch_mode('guwen'))
        self.mode_guwen_btn.pack(side='left', expand=True, fill='x', padx=1)
        
        # 目录标题
        self.dir_title = ttk.Label(left_frame, text="📚 诗词目录", 
                              font=self.fonts.get('title_small', ('华文中宋', 14, 'bold')))
        self.dir_title.pack(fill='x', padx=8, pady=(8, 4))
        
        # 目录筛选框 - 朝代
        filter_frame1 = ttk.Frame(left_frame)
        filter_frame1.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(filter_frame1, text="朝代:").pack(side='left')
        self.dynasty_var = tk.StringVar(value='全部')
        dynasty_combo = ttk.Combobox(filter_frame1, textvariable=self.dynasty_var, 
                                     values=['全部', '唐', '宋', '元', '先秦', '汉', '魏晋', '南北朝', '隋', '五代', '清', '明', '近现代'],
                                     width=8, state='readonly')
        dynasty_combo.pack(side='left', padx=5)
        dynasty_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_directory())
        
        # 目录筛选框 - 作者
        filter_frame2 = ttk.Frame(left_frame)
        filter_frame2.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(filter_frame2, text="作者:").pack(side='left')
        self.author_filter_var = tk.StringVar()
        author_combo = ttk.Combobox(filter_frame2, textvariable=self.author_filter_var, width=10)
        author_combo.pack(side='left', padx=5, fill='x', expand=True)
        author_combo.bind('<Return>', lambda e: self._filter_directory())
        author_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_directory())
        
        # 目录筛选框 - 题材
        filter_frame3 = ttk.Frame(left_frame)
        filter_frame3.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(filter_frame3, text="题材:").pack(side='left')
        self.theme_var = tk.StringVar(value='全部')
        theme_values = ['全部'] + get_all_themes() if HAS_CLASSIFIER else ['全部']
        theme_combo = ttk.Combobox(filter_frame3, textvariable=self.theme_var,
                                   values=theme_values, width=10, state='readonly')
        theme_combo.pack(side='left', padx=5)
        theme_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_directory())
        
        # 目录筛选框 - 诗体
        filter_frame4 = ttk.Frame(left_frame)
        filter_frame4.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(filter_frame4, text="诗体:").pack(side='left')
        self.poem_form_var = tk.StringVar(value='全部')
        poem_form_combo = ttk.Combobox(filter_frame4, textvariable=self.poem_form_var,
                                       values=['全部', '五言绝句', '七言绝句', '五言律诗', '七言律诗',
                                               '五言排律', '七言排律', '五言古诗', '七言古诗',
                                               '词·小令', '词·中调', '词·长调', '曲', 
                                               '诗经·四言', '楚辞体', '杂言'],
                                       width=10, state='readonly')
        poem_form_combo.pack(side='left', padx=5)
        poem_form_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_directory())
        
        # 目录筛选框 - 每句字数
        filter_frame5 = ttk.Frame(left_frame)
        filter_frame5.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(filter_frame5, text="字数:").pack(side='left')
        self.chars_per_line_var = tk.StringVar(value='全部')
        chars_combo = ttk.Combobox(filter_frame5, textvariable=self.chars_per_line_var,
                                   values=['全部', '5字', '7字', '其他'],
                                   width=10, state='readonly')
        chars_combo.pack(side='left', padx=5)
        chars_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_directory())
        
        # 目录筛选框 - 合集
        filter_frame6 = ttk.Frame(left_frame)
        filter_frame6.pack(fill='x', padx=5, pady=2)
        
        ttk.Label(filter_frame6, text="合集:").pack(side='left')
        self.collection_var = tk.StringVar(value='全部')
        self.collection_combo = ttk.Combobox(filter_frame6, textvariable=self.collection_var,
                                        values=['全部', '全唐诗', '全宋诗', '宋词', '元曲', 
                                                '唐诗三百首', '诗经', '楚辞', '纳兰性德',
                                                '花间集', '南唐二主词', '曹操诗集', '蒙学', '中学古诗'],
                                        width=10, state='readonly')
        self.collection_combo.pack(side='left', padx=5)
        self.collection_combo.bind('<<ComboboxSelected>>', lambda e: self._filter_directory())
        
        # 搜索框
        search_dir_frame = ttk.Frame(left_frame)
        search_dir_frame.pack(fill='x', padx=5, pady=2)
        
        self.dir_search_var = tk.StringVar()
        dir_search_entry = ttk.Entry(search_dir_frame, textvariable=self.dir_search_var, width=15)
        dir_search_entry.pack(side='left', fill='x', expand=True)
        dir_search_entry.bind('<Return>', lambda e: self._search_directory())
        ttk.Button(search_dir_frame, text="🔍", command=self._search_directory, width=3).pack(side='left', padx=2)
        ttk.Button(search_dir_frame, text="🎲", command=self._random_from_filter, width=3).pack(side='left', padx=2)
        
        # 目录列表
        dir_list_frame = ttk.Frame(left_frame)
        dir_list_frame.pack(fill='both', expand=True, padx=5, pady=2)
        
        # 目录Treeview - 标题/作者/朝代/题材/诗体
        self.dir_tree = ttk.Treeview(dir_list_frame, columns=('title', 'author', 'dynasty', 'theme', 'form'), show='headings', height=20)
        self.dir_tree.heading('title', text='标题')
        self.dir_tree.heading('author', text='作者')
        self.dir_tree.heading('dynasty', text='朝代')
        self.dir_tree.heading('theme', text='题材')
        self.dir_tree.heading('form', text='诗体')
        self.dir_tree.column('title', width=95)
        self.dir_tree.column('author', width=60)
        self.dir_tree.column('dynasty', width=36)
        self.dir_tree.column('theme', width=58)
        self.dir_tree.column('form', width=55)
        
        dir_scrollbar = ttk.Scrollbar(dir_list_frame, orient='vertical', command=self.dir_tree.yview)
        self.dir_tree.configure(yscrollcommand=dir_scrollbar.set)
        
        self.dir_tree.pack(side='left', fill='both', expand=True)
        dir_scrollbar.pack(side='right', fill='y')
        
        # 绑定目录点击事件
        self.dir_tree.bind('<<TreeviewSelect>>', self._on_directory_select)
        
        # 分页控制
        page_frame = ttk.Frame(left_frame)
        page_frame.pack(fill='x', padx=5, pady=2)
        
        self.page_var = tk.IntVar(value=1)
        self.page_size = 100  # 每页显示100首
        
        ttk.Button(page_frame, text="◀", command=self._prev_page, width=3).pack(side='left')
        self.page_label = ttk.Label(page_frame, text="1/1", font=('微软雅黑', 9))
        self.page_label.pack(side='left', expand=True)
        ttk.Button(page_frame, text="▶", command=self._next_page, width=3).pack(side='left')
        
        # 目录统计
        self.dir_stats_label = ttk.Label(left_frame, text="加载中...", font=('微软雅黑', 9))
        self.dir_stats_label.pack(fill='x', padx=5, pady=2)
        
        # ── 右侧内容面板 ──
        # 顶部工具栏
        toolbar = ttk.Frame(right_frame)
        toolbar.pack(fill='x', pady=(0, 8))
        
        # 随机按钮
        ttk.Button(toolbar, text="🎲 随机", style='Accent.TButton' if HAS_THEME_V2 else 'TButton',
                   command=self._show_random).pack(side='left', padx=3)
        
        # 每日推荐
        if HAS_FEATURES_V7:
            ttk.Button(toolbar, text="📅 每日推荐", command=self._show_daily).pack(side='left', padx=3)
        
        # 朝代筛选
        ttk.Button(toolbar, text="📜 唐诗", command=lambda: self._filter_dynasty('唐')).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🎵 宋词", command=lambda: self._filter_dynasty('宋')).pack(side='left', padx=2)
        ttk.Button(toolbar, text="🎭 元曲", command=lambda: self._filter_dynasty('元')).pack(side='left', padx=2)
        
        # 搜索框
        search_frame = ttk.Frame(toolbar)
        search_frame.pack(side='right')
        
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=18)
        self.search_entry.pack(side='left', padx=2)
        self.search_entry.bind('<Return>', lambda e: self._search())
        
        ttk.Button(search_frame, text="🔍 搜索", command=self._search).pack(side='left', padx=2)
        
        # 统一搜索按钮
        if HAS_FEATURES_UI:
            ttk.Button(search_frame, text="🌐 统一搜索", command=self._open_unified_search).pack(side='left', padx=2)
        
        # 高级搜索按钮
        if HAS_ADVANCED_SEARCH:
            ttk.Button(search_frame, text="🔧 高级", command=self._open_advanced_search).pack(side='left', padx=2)
        
        # 主题切换按钮
        theme_btn = ttk.Button(toolbar, text="🌙 墨色" if self.current_theme == "light" else "☀️ 宣纸", 
                              command=self._toggle_theme)
        theme_btn.pack(side='right', padx=8)
        
        # 新功能按钮栏
        new_features_frame = ttk.Frame(right_frame)
        new_features_frame.pack(fill='x', pady=(0, 8))
        
        if HAS_GUWEN_UI:
            ttk.Button(new_features_frame, text="📜 古文阅读", command=lambda: self._switch_mode('guwen')).pack(side='left', padx=2)
        
        if HAS_LEARNING_UI:
            ttk.Button(new_features_frame, text="📚 学习模式", command=self._open_learning).pack(side='left', padx=2)
        
        if HAS_GAME_UI:
            ttk.Button(new_features_frame, text="🎮 诗词游戏", command=self._open_game).pack(side='left', padx=2)
        
        if HAS_CREATION_UI:
            ttk.Button(new_features_frame, text="✍️ 创作辅助", command=self._open_creation).pack(side='left', padx=2)
        
        if HAS_COLLECTION_MANAGER:
            ttk.Button(new_features_frame, text="📁 收藏管理", command=self._open_collection_manager).pack(side='left', padx=2)
        
        if HAS_VISUALIZATION:
            ttk.Button(new_features_frame, text="📊 数据可视化", command=self._open_visualization).pack(side='left', padx=2)
        
        # v6.0功能按钮
        v6_frame = ttk.Frame(right_frame)
        v6_frame.pack(fill='x', pady=(0, 8))
        
        if HAS_FEATURES_UI:
            ttk.Button(v6_frame, text="👤 诗人档案", command=self._open_poet_profile).pack(side='left', padx=2)
            ttk.Button(v6_frame, text="📖 词牌词典", command=self._open_cipai).pack(side='left', padx=2)
        
        if HAS_QUOTES_UI:
            ttk.Button(v6_frame, text="💡 名句欣赏", command=self._open_quotes).pack(side='left', padx=2)
        
        if HAS_I18N:
            ttk.Button(v6_frame, text="🌐 语言设置", command=self._open_language_settings).pack(side='left', padx=2)
        
        if HAS_PLUGIN_SYSTEM:
            ttk.Button(v6_frame, text="🔌 插件管理", command=self._open_plugin_manager).pack(side='left', padx=2)
        
        if HAS_CLOUD_SYNC:
            ttk.Button(v6_frame, text="☁️ 云端同步", command=self._open_cloud_sync).pack(side='left', padx=2)
        
        # 诗句显示区 - 卡片式设计
        poem_card = tk.Frame(right_frame, bg=self.theme_colors.get('border', '#D8CDB0'))
        poem_card.pack(fill='both', expand=True, pady=(0, 10))
        
        poem_frame = tk.Frame(poem_card, bg=self.theme_colors.get('bg_card', '#FDFAF2'))
        poem_frame.pack(fill='both', expand=True, padx=1, pady=1)
        self.poem_card_frame = poem_card
        self.poem_inner_frame = poem_frame
        
        # 装饰性分隔
        top_spacer = tk.Frame(poem_frame, bg=self.theme_colors.get('bg_card', '#FDFAF2'), height=15)
        top_spacer.pack()
        
        self.title_label = tk.Label(poem_frame, font=self.fonts.get('title', ('华文中宋', 20, 'bold')),
                                    bg=self.theme_colors.get('bg_card', '#FDFAF2'),
                                    fg=self.theme_colors.get('fg', '#2B2B2B'))
        self.title_label.pack(pady=(5, 2))
        
        self.author_label = tk.Label(poem_frame, font=self.fonts.get('ui', ('微软雅黑', 10)),
                                     bg=self.theme_colors.get('bg_card', '#FDFAF2'),
                                     fg=self.theme_colors.get('fg_secondary', '#6B6355'))
        self.author_label.pack(pady=(0, 10))
        
        # 诗句正文 - 楷体大字（注音模式时拼音显示在字上方）
        self.content_text = tk.Text(poem_frame, font=self.fonts.get('poem_large', ('楷体', 20)), 
                                   wrap='char', height=8, relief='flat',
                                   background=self.theme_colors.get('bg_card', '#FDFAF2'),
                                   foreground=self.theme_colors.get('fg', '#2B2B2B'),
                                   spacing1=2, spacing3=2,
                                   padx=20, pady=10,
                                   cursor='arrow')
        self.content_text.pack(fill='both', expand=True, pady=5)
        
        # 选中文字 → 自动复制 + 提示
        self.content_text.bind('<ButtonRelease-1>', self._on_text_select)
        
        # 操作按钮区
        btn_frame = tk.Frame(poem_frame, bg=self.theme_colors.get('bg_card', '#FDFAF2'))
        btn_frame.pack(pady=(8, 12))
        
        # 主操作行：朗读 / 拼音 / 收藏
        main_btn_row = ttk.Frame(btn_frame)
        main_btn_row.pack(pady=3)
        
        if HAS_FEATURES_V7 and self.tts_engine:
            self.speak_btn = ttk.Button(main_btn_row, text="🔊 朗读", style='Accent.TButton' if HAS_THEME_V2 else 'TButton',
                                        command=self._speak_poem)
            self.speak_btn.pack(side='left', padx=4)
        
        if HAS_PYPINYIN:
            self.pinyin_btn = ttk.Button(main_btn_row, text="🔤 拼音", command=self._toggle_pinyin)
            self.pinyin_btn.pack(side='left', padx=4)
        
        ttk.Button(main_btn_row, text="⭐ 收藏", command=self._favorite).pack(side='left', padx=4)
        ttk.Button(main_btn_row, text="⬅️ 上一首", command=self._prev_poem).pack(side='left', padx=4)
        ttk.Button(main_btn_row, text="➡️ 下一首", command=self._next_poem).pack(side='left', padx=4)
        
        # 次操作行
        sub_btn_row = ttk.Frame(btn_frame)
        sub_btn_row.pack(pady=3)
        
        ttk.Button(sub_btn_row, text="📋 复制", command=self._copy_poem).pack(side='left', padx=4)
        ttk.Button(sub_btn_row, text="🖼️ 卡片", command=self._generate_card).pack(side='left', padx=4)
        ttk.Button(sub_btn_row, text="📊 统计", command=self._show_stats).pack(side='left', padx=4)
        ttk.Button(sub_btn_row, text="📤 导出", command=self._export_favorites).pack(side='left', padx=4)
        
        # 第三行：字号调节 + 沉浸阅读
        view_btn_row = ttk.Frame(btn_frame)
        view_btn_row.pack(pady=3)
        
        ttk.Button(view_btn_row, text="A-", width=3, 
                  command=lambda: self._adjust_font(-2)).pack(side='left', padx=4)
        self.font_size_label = tk.Label(view_btn_row, text=str(self.poem_font_size), width=3,
                                        font=self.fonts.get('ui_small', ('微软雅黑', 9)),
                                        bg=self.theme_colors.get('bg_card', '#FDFAF2'),
                                        fg=self.theme_colors.get('fg_secondary', '#6B6355'))
        self.font_size_label.pack(side='left')
        ttk.Button(view_btn_row, text="A+", width=3,
                  command=lambda: self._adjust_font(2)).pack(side='left', padx=4)
        
        ttk.Button(view_btn_row, text="🖥️ 沉浸阅读", command=self._immersive_read).pack(side='left', padx=(15, 4))
        ttk.Button(view_btn_row, text="📖 详细解读", command=self._open_guwen_detail).pack(side='left', padx=4)
        
        # 底部状态栏和收藏/历史
        bottom_frame = ttk.Frame(right_frame)
        bottom_frame.pack(fill='x')
        
        # 状态栏
        self.status_label = ttk.Label(bottom_frame, text="正在加载数据...")
        self.status_label.pack(side='left')
        
        # 收藏夹和历史按钮
        ttk.Button(bottom_frame, text="⭐ 收藏夹", command=self._show_favorites).pack(side='right', padx=2)
        ttk.Button(bottom_frame, text="🕐 历史", command=self._show_history).pack(side='right', padx=2)
        
        # 初始化右键菜单
        if HAS_UX_ENHANCEMENTS:
            self._init_context_menu()
        
        # 加载占位提示（数据就绪后由 _show_random 覆盖）
        self.title_label.config(text="⏳ 正在加载诗库…")
        self.author_label.config(text="首次启动约需 2 秒，请稍候")
    
    def _init_context_menu(self):
        """初始化右键菜单"""
        self.context_menu = ContextMenu(self.root)
        
        menu_items = [
            {'label': '🎲 随机', 'command': self._show_random, 'accelerator': 'F5'},
            {'label': '⬅️ 上一首', 'command': self._prev_poem, 'accelerator': '←'},
            {'label': '➡️ 下一首', 'command': self._next_poem, 'accelerator': '→'},
            '-',
            {'label': '⭐ 收藏', 'command': self._favorite, 'accelerator': 'Ctrl+S'},
            {'label': '📋 复制', 'command': self._copy_poem, 'accelerator': 'Ctrl+C'},
            '-',
            {'label': '🔤 拼音', 'command': self._show_pinyin},
            {'label': '🔊 朗读', 'command': self._speak_poem},
            '-',
            {'label': '📊 统计', 'command': self._show_stats},
            {'label': '📤 导出', 'command': self._export_favorites},
        ]
        
        self.context_menu.create_menu(menu_items)
    
    def _bind_shortcuts(self):
        """绑定快捷键"""
        self.root.bind('<Control-c>', lambda e: self._copy_poem())
        self.root.bind('<Control-s>', lambda e: self._favorite())
        self.root.bind('<Control-f>', lambda e: self._focus_search())
        self.root.bind('<F5>', lambda e: self._show_random())
        self.root.bind('<Escape>', lambda e: self.search_var.set(''))
        # 阅读导航（←/→ 上一首/下一首）
        self.root.bind('<Left>', lambda e: self._on_arrow_key(e, -1))
        self.root.bind('<Right>', lambda e: self._on_arrow_key(e, 1))
        self.root.bind('<F11>', lambda e: self._immersive_read())
    
    def _on_arrow_key(self, event, step):
        """键盘 ←/→：上一首/下一首（输入框内不劫持方向键）"""
        try:
            w = self.root.focus_get()
            cls = w.winfo_class() if w else ''
        except Exception:
            cls = ''
        if cls in ('Entry', 'TEntry', 'Text', 'TCombobox', 'ComboBox'):
            return None
        if self.view_mode != 'poem':
            return None
        if step < 0:
            self._prev_poem()
        else:
            self._next_poem()
        return "break"
    
    def _focus_search(self):
        """聚焦搜索框"""
        try:
            if hasattr(self, 'search_entry'):
                self.search_entry.focus_set()
                self.search_entry.select_range(0, 'end')
                return "break"
        except Exception:
            pass
    
    def _show_random(self):
        """显示随机诗词（古文模式下随机古文）"""
        if not self.db:
            return
        
        # 古文模式：随机一篇古文
        if self.view_mode == 'guwen' and self.db.conn:
            try:
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT id FROM guwen ORDER BY RANDOM() LIMIT 1')
                row = cursor.fetchone()
                if row:
                    self._display_guwen(row[0])
                    return
            except Exception as e:
                log.error(f"随机古文失败: {e}")
        
        poem = self.db.random_one()
        if poem:
            self._display_poem(poem)
            self._nav_index = -1  # 随机显示后重置顺序导航位置
    
    def _next_poem(self):
        """顺序浏览：下一首"""
        self._nav_step(1)
    
    def _prev_poem(self):
        """顺序浏览：上一首"""
        self._nav_step(-1)
    
    def _nav_step(self, step):
        """在当前筛选列表中顺序前进/后退（循环）"""
        if not self.db:
            return
        # 确保导航列表存在
        lst = getattr(self, '_all_filtered_poems', None)
        if not lst:
            try:
                lst = self._get_filtered_poems()
                self._all_filtered_poems = lst
            except Exception:
                lst = None
        if not lst:
            return
        
        idx = getattr(self, '_nav_index', -1)
        if idx < 0 or idx >= len(lst):
            idx = 0 if step > 0 else len(lst) - 1
        else:
            idx = (idx + step) % len(lst)
        self._goto_poem_index(idx)
    
    def _goto_poem_index(self, idx):
        """跳到筛选列表指定位置（同步显示/页码/选中）"""
        lst = getattr(self, '_all_filtered_poems', None)
        if not lst or not (0 <= idx < len(lst)):
            return
        poem = lst[idx]
        self._display_poem(poem)
        self._nav_index = idx
        
        # 状态栏位置指示
        try:
            self.status_label.config(text=f"第 {idx + 1} / {len(lst)} 首 · ← → 键切换")
        except Exception:
            pass
        
        # 同步页码
        page = idx // self.page_size + 1
        if page != self.page_var.get():
            self.page_var.set(page)
            self._update_directory(lst)
        
        # 同步树选中（防递归）
        self._nav_syncing = True
        try:
            items = self.dir_tree.get_children()
            pos = idx - (page - 1) * self.page_size
            if 0 <= pos < len(items):
                self.dir_tree.selection_set(items[pos])
                self.dir_tree.see(items[pos])
        except Exception:
            pass
        finally:
            self._nav_syncing = False
    
    def _filter_dynasty(self, dynasty):
        """按朝代筛选"""
        if not self.db:
            return
        poem = self.db.random_one(dynasty=dynasty)
        if poem:
            self._display_poem(poem)
        else:
            messagebox.showinfo("提示", f"没有找到{dynasty}朝诗词")
    
    def _search(self):
        """搜索（弹窗显示所有结果；古文模式下搜索古文库）"""
        if not self.db:
            return
        keyword = self.search_var.get().strip()
        if not keyword:
            return
        
        # 古文模式：搜索古文库
        if self.view_mode == 'guwen':
            results = self._search_guwen(keyword)
            if results:
                self._show_search_results(keyword, results, is_guwen=True)
                self.status_label.config(text=f"找到 {len(results)} 篇包含'{keyword}'的古文")
            else:
                self._show_toast(f"没有找到包含'{keyword}'的古文")
            return
        
        results = self.db.search(keyword, limit=100)
        if results:
            # 显示搜索结果窗口
            self._show_search_results(keyword, results)
            self.status_label.config(text=f"找到 {len(results)} 首包含'{keyword}'的诗词")
        else:
            self._show_toast(f"没有找到包含'{keyword}'的诗词")
    
    def _search_guwen(self, keyword, limit=100):
        """搜索古文库（标题/作者/正文）"""
        if not self.db or not self.db.conn:
            return []
        try:
            cursor = self.db.conn.cursor()
            cursor.execute('''
                SELECT id, title, author, dynasty, content FROM guwen
                WHERE title LIKE ? OR author LIKE ? OR content LIKE ?
                LIMIT ?
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
            return [{'id': f'gw:{r[0]}', 'title': r[1], 'author': r[2],
                     'dynasty': r[3], 'content': r[4]} for r in cursor.fetchall()]
        except Exception as e:
            log.error(f"古文搜索失败: {e}")
            return []
    
    def _show_search_results(self, keyword, results, is_guwen=False):
        """搜索结果显示窗口"""
        unit = "篇" if is_guwen else "条"
        win = tk.Toplevel(self.root)
        win.title(f"🔍 搜索: {keyword} ({len(results)} {unit})")
        win.geometry("760x560")
        win.transient(self.root)
        win.grab_set()
        
        colors = self.theme_colors
        fonts = self.fonts
        win.configure(bg=colors.get('bg', '#F7F3E8'))
        
        # 顶部信息
        top = tk.Frame(win, bg=colors.get('bg', '#F7F3E8'))
        top.pack(fill='x', padx=12, pady=8)
        
        tk.Label(top, text=f"「{keyword}」共找到 {len(results)} 条结果", 
                font=fonts.get('ui', ('微软雅黑', 10)),
                bg=colors.get('bg', '#F7F3E8'), 
                fg=colors.get('accent', '#8C2F39')).pack(side='left')
        
        # 结果列表
        list_frame = ttk.Frame(win)
        list_frame.pack(fill='both', expand=True, padx=12, pady=(0, 8))
        
        tree = ttk.Treeview(list_frame, columns=('title', 'author', 'dynasty', 'preview'), 
                            show='headings')
        tree.heading('title', text='标题')
        tree.heading('author', text='作者')
        tree.heading('dynasty', text='朝代')
        tree.heading('preview', text='内容预览')
        tree.column('title', width=150)
        tree.column('author', width=70)
        tree.column('dynasty', width=45)
        tree.column('preview', width=420)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 填充结果
        for r in results:
            preview = (r.get('content', '') or '').replace('\n', ' ')[:60]
            tree.insert('', 'end',
                       values=(r.get('title', ''), r.get('author', ''), 
                               r.get('dynasty', ''), preview),
                       tags=(str(r.get('id', '')),))
        
        # 双击查看
        def on_double(event):
            sel = tree.selection()
            if not sel:
                return
            tags = tree.item(sel[0])['tags']
            if tags:
                item_id = str(tags[0])
                # 古文条目
                if item_id.startswith('gw:'):
                    try:
                        self._display_guwen(int(item_id[3:]))
                    except ValueError:
                        return
                    return
                # 诗词条目
                for r in results:
                    if str(r.get('id', '')) == item_id:
                        self._display_poem(r)
                        self.status_label.config(text=f"显示: 《{r.get('title', '')}》")
                        break
        
        tree.bind('<Double-1>', on_double)
        
        # 底部
        bottom = tk.Frame(win, bg=colors.get('bg', '#F7F3E8'))
        bottom.pack(fill='x', padx=12, pady=(0, 10))
        
        tk.Label(bottom, text="双击查看详情", font=fonts.get('ui_small', ('微软雅黑', 9)),
                bg=colors.get('bg', '#F7F3E8'),
                fg=colors.get('fg_secondary', '#6B6355')).pack(side='left')
        
        ttk.Button(bottom, text="关闭", command=win.destroy).pack(side='right')
    
    def _open_advanced_search(self):
        """打开高级搜索"""
        if not HAS_ADVANCED_SEARCH:
            messagebox.showinfo("提示", "高级搜索模块未加载")
            return
        
        if not self.db:
            messagebox.showinfo("提示", "数据尚未加载完成")
            return
        
        dialog = AdvancedSearchDialog(self.root, self.db, self.theme_colors)
        dialog.grab_set()
    
    def _display_poem(self, poem):
        """显示诗句"""
        self.current_poem = poem
        
        # 获取诗词内容
        title = poem.get('title', '')
        author = poem.get('author', '')
        dynasty = poem.get('dynasty', '')
        content = poem.get('content', '')
        theme = poem.get('theme', '')
        poem_form = poem.get('poem_form', '')
        collection = poem.get('collection', '')
        
        # 如果内容为空，从 SQLite 按需加载
        if not content and self.db.conn and 'id' in poem:
            try:
                cursor = self.db.conn.cursor()
                cursor.execute('SELECT content, theme, poem_form, collection FROM poems WHERE id = ?', (poem['id'],))
                row = cursor.fetchone()
                if row:
                    content = row[0]
                    if not theme:
                        theme = row[1] if len(row) > 1 else ''
                    if not poem_form:
                        poem_form = row[2] if len(row) > 2 else ''
                    if not collection:
                        collection = row[3] if len(row) > 3 else ''
            except Exception as e:
                log.error(f"获取诗词内容失败: {e}")
        
        if isinstance(content, list):
            content = '\n'.join(content)
        
        # 繁简转换
        if HAS_CONVERTER:
            title = traditional_to_simplified(title)
            author = traditional_to_simplified(author)
            content = traditional_to_simplified(content)
        
        # 更新显示
        self.title_label.config(text=f"《{title}》")
        author_text = f"· {author} ({dynasty})"
        if theme:
            author_text += f" [{theme}]"
        if poem_form:
            author_text += f" {poem_form}"
        if collection:
            author_text += f" · {collection}"
        
        # 词牌提示（词类诗词显示词牌信息）
        cipai_hint = ''
        if poem_form and '词' in poem_form and HAS_CIPAI_DICT:
            cipai_name = title.split('·')[0] if '·' in title else title
            cipai_info = get_cipai_info(cipai_name)
            if cipai_info:
                cipai_hint = f"  〔{cipai_name}：{cipai_info['字数']}〕"
                author_text += cipai_hint
        
        self.author_label.config(text=author_text)
        
        # 渲染内容（支持注音模式）
        self._render_content(content)
        
        # 添加到历史
        self._add_history(poem)
    
    def _render_content(self, content):
        """渲染诗句内容（支持拼音注音模式 + 动态字号）"""
        self.content_text.config(state='normal')
        self.content_text.delete('1.0', tk.END)
        
        poem_font = ('楷体', self.poem_font_size)
        pinyin_font_size = max(8, self.poem_font_size // 2)
        pinyin_font = ('Arial', pinyin_font_size)
        
        if self.show_pinyin and HAS_PYPINYIN:
            # 注音模式：拼音小字 + 诗句大字，逐行交替
            lines = content.split('\n')
            for line in lines:
                if not line.strip():
                    continue
                # 拼音行（小字、淡色、居中）
                py = get_pinyin_line(line)
                self.content_text.insert(tk.END, py + '\n', 'pinyin')
                # 诗句行（大字、居中）
                self.content_text.insert(tk.END, line + '\n', 'poemline')
            
            # 配置tag样式
            self.content_text.tag_config('pinyin', 
                font=pinyin_font,
                foreground=self.theme_colors.get('fg_muted', '#9C9484'),
                justify='center', spacing1=6, spacing3=0)
            self.content_text.tag_config('poemline',
                font=poem_font,
                foreground=self.theme_colors.get('fg', '#2B2B2B'),
                justify='center', spacing1=0, spacing3=8)
        else:
            # 普通模式：居中显示
            self.content_text.insert(tk.END, content, 'plain')
            self.content_text.tag_config('plain',
                justify='center',
                font=poem_font,
                foreground=self.theme_colors.get('fg', '#2B2B2B'),
                spacing1=4, spacing3=4)
        
        self.content_text.config(state='disabled')
    
    def _adjust_font(self, delta):
        """调整诗文字号"""
        self.poem_font_size = max(12, min(48, self.poem_font_size + delta))
        
        if hasattr(self, 'font_size_label'):
            self.font_size_label.config(text=str(self.poem_font_size))
        
        # 重新渲染当前诗词
        if self.current_poem:
            content = self.current_poem.get('content', '')
            if isinstance(content, list):
                content = '\n'.join(content)
            if HAS_CONVERTER:
                content = traditional_to_simplified(content)
            self._render_content(content)
    
    def _immersive_read(self):
        """沉浸式阅读窗口"""
        if not self.current_poem:
            messagebox.showinfo("提示", "请先选择一首诗词")
            return
        
        win = tk.Toplevel(self.root)
        win.title("沉浸阅读")
        win.attributes('-fullscreen', True)
        
        colors = self.theme_colors
        win.configure(bg=colors.get('bg', '#F7F3E8'))
        
        # ESC 退出
        win.bind('<Escape>', lambda e: win.destroy())
        win.bind('<Double-Button-1>', lambda e: win.destroy())
        
        # 内容
        container = tk.Frame(win, bg=colors.get('bg', '#F7F3E8'))
        container.place(relx=0.5, rely=0.5, anchor='center')
        
        title = self.current_poem.get('title', '')
        author = self.current_poem.get('author', '')
        dynasty = self.current_poem.get('dynasty', '')
        content = self.current_poem.get('content', '')
        if isinstance(content, list):
            content = '\n'.join(content)
        if HAS_CONVERTER:
            title = traditional_to_simplified(title)
            content = traditional_to_simplified(content)
        
        tk.Label(container, text=f"《{title}》", 
                font=('华文中宋', 36, 'bold'),
                bg=colors.get('bg', '#F7F3E8'),
                fg=colors.get('fg', '#2B2B2B')).pack(pady=(0, 10))
        
        tk.Label(container, text=f"· {author} ({dynasty})",
                font=('微软雅黑', 16),
                bg=colors.get('bg', '#F7F3E8'),
                fg=colors.get('fg_secondary', '#6B6355')).pack(pady=(0, 30))
        
        tk.Label(container, text=content,
                font=('楷体', 32),
                bg=colors.get('bg', '#F7F3E8'),
                fg=colors.get('fg', '#2B2B2B'),
                justify='center', wraplength=1400).pack()
        
        tk.Label(container, text="按 ESC 或双击退出",
                font=('微软雅黑', 11),
                bg=colors.get('bg', '#F7F3E8'),
                fg=colors.get('fg_muted', '#9C9484')).pack(pady=(40, 0))
    
    def _toggle_pinyin(self):
        """切换拼音显示（注音式）"""
        if not self.current_poem:
            return
        
        self.show_pinyin = not self.show_pinyin
        
        # 获取内容并重新渲染
        content = self.current_poem.get('content', '')
        if isinstance(content, list):
            content = '\n'.join(content)
        
        # 简繁转换
        if HAS_CONVERTER:
            content = traditional_to_simplified(content)
        
        self._render_content(content)
        
        if hasattr(self, 'pinyin_btn'):
            self.pinyin_btn.config(text="🔤 隐藏拼音" if self.show_pinyin else "🔤 拼音")
    
    def _show_pinyin(self):
        """显示拼音（兼容旧接口）"""
        self._toggle_pinyin()
    
    def _speak_poem(self):
        """朗读诗句 - v7 TTS引擎"""
        if not self.current_poem:
            return
        
        content = self.current_poem.get('content', '')
        if isinstance(content, list):
            content = '\n'.join(content)
        
        title = self.current_poem.get('title', '')
        author = self.current_poem.get('author', '')
        
        # 简繁转换
        if HAS_CONVERTER:
            content = traditional_to_simplified(content)
            title = traditional_to_simplified(title)
            author = traditional_to_simplified(author)
        
        # 朗读文本：标题 + 作者 + 正文
        speak_text = f"{title}。{author}。{content}"
        # 去掉标点间的换行，让朗读更流畅
        speak_text = speak_text.replace('\n', '，')
        
        if HAS_FEATURES_V7 and self.tts_engine:
            if self.tts_engine.is_playing:
                self.tts_engine.stop()
                if hasattr(self, 'speak_btn'):
                    self.speak_btn.config(text="🔊 朗读")
                return
            
            if hasattr(self, 'speak_btn'):
                self.speak_btn.config(text="⏹ 停止")
            
            def on_done(ok):
                self.root.after(0, lambda: self.speak_btn.config(text="🔊 朗读") if hasattr(self, 'speak_btn') else None)
            
            self.tts_engine.speak_async(speak_text, on_done=on_done)
        else:
            # 旧版回退
            if not HAS_UTILS:
                return
            
            def run_tts():
                try:
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    output_file = loop.run_until_complete(tts_speak(content))
                    if output_file:
                        os.startfile(output_file)
                except Exception as e:
                    messagebox.showerror("错误", f"朗读失败: {e}")
            
            threading.Thread(target=run_tts, daemon=True).start()
    
    def _show_daily(self):
        """每日推荐"""
        if not HAS_FEATURES_V7 or not self.daily_recommender:
            messagebox.showinfo("提示", "每日推荐模块未加载")
            return
        
        poem = self.daily_recommender.get_daily_poem()
        if poem:
            self._display_poem(poem)
            # 显示日期提示
            today = datetime.now().strftime('%Y年%m月%d日')
            self.status_label.config(text=f"📅 {today} 每日推荐 · 共 {len(self.db.poems):,} 首诗词")
        else:
            messagebox.showinfo("提示", "获取每日推荐失败")
    
    def _generate_card(self):
        """生成诗词卡片（v7 古典风格）"""
        if not self.current_poem:
            return
        
        # 询问版式
        if HAS_CARD_V2:
            dialog = tk.Toplevel(self.root)
            dialog.title("卡片版式")
            dialog.geometry("300x150")
            dialog.transient(self.root)
            dialog.grab_set()
            
            colors = self.theme_colors
            dialog.configure(bg=colors.get('bg', '#F7F3E8'))
            
            ttk.Label(dialog, text="选择卡片版式:", font=self.fonts.get('ui', ('微软雅黑', 10))).pack(pady=15)
            
            btn_frame = ttk.Frame(dialog)
            btn_frame.pack()
            
            choice = {'value': None}
            
            def choose(v):
                choice['value'] = v
                dialog.destroy()
            
            ttk.Button(btn_frame, text="横排", command=lambda: choose('h')).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="竖排", command=lambda: choose('v')).pack(side='left', padx=5)
            ttk.Button(btn_frame, text="取消", command=dialog.destroy).pack(side='left', padx=5)
            
            self.root.wait_window(dialog)
            
            if not choice['value']:
                return
            
            vertical = (choice['value'] == 'v')
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG图片", "*.png")],
                initialfile=f"poem_card_{datetime.now().strftime('%H%M%S')}"
            )
            
            if not filename:
                return
            
            try:
                output = generate_classic_card(self.current_poem, filename, vertical=vertical)
                if output:
                    messagebox.showinfo("成功", f"卡片已生成:\n{output}")
                    try:
                        os.startfile(output)
                    except:
                        pass
            except Exception as e:
                messagebox.showerror("错误", f"生成卡片失败: {e}")
            return
        
        # 旧版回退
        filename = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[("HTML文件", "*.html"), ("PNG图片", "*.png")],
            initialfile=f"poem_card_{datetime.now().strftime('%H%M%S')}"
        )
        
        if not filename:
            return
        
        try:
            if filename.endswith('.html'):
                html = generate_poem_card_html(self.current_poem)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(html)
                messagebox.showinfo("成功", f"HTML 卡片已生成: {filename}")
                webbrowser.open(filename)
            elif filename.endswith('.png') and HAS_UTILS:
                output_path = generate_poem_card_png(self.current_poem, filename)
                if output_path:
                    messagebox.showinfo("成功", f"PNG 卡片已生成: {output_path}")
            else:
                messagebox.showinfo("提示", "PNG 生成功能需要安装 Pillow")
        except Exception as e:
            messagebox.showerror("错误", f"生成卡片失败: {e}")
    
    def _favorite(self):
        """收藏当前诗句/古文"""
        if not self.current_poem:
            return
        
        is_guwen = str(self.current_poem.get('id', '')).startswith('gw:')
        
        for fav in self.favorites:
            if fav.get('id') == self.current_poem.get('id'):
                self._show_toast("已在收藏夹中")
                return
        
        self.favorites.append(self.current_poem.copy())
        self._save_favorites()
        self._show_toast("✓ 已收藏" + ("古文" if is_guwen else "诗词"))
    
    def _on_text_select(self, event=None):
        """选中文字后自动复制到剪贴板 + 浮动提示"""
        try:
            sel = self.content_text.get('sel.first', 'sel.last')
        except tk.TclError:
            return  # 无选区
        if sel and sel.strip():
            try:
                self.root.clipboard_clear()
                self.root.clipboard_append(sel)
            except Exception:
                return
            preview = sel.strip().replace('\n', ' ')
            if len(preview) > 14:
                preview = preview[:14] + '…'
            self._show_toast(f"✓ 已复制: {preview}")
    
    def _show_toast(self, text, ms=1500):
        """右下角浮动轻提示"""
        try:
            if getattr(self, '_toast_win', None) and self._toast_win.winfo_exists():
                self._toast_win.destroy()
        except Exception:
            pass
        try:
            toast = tk.Toplevel(self.root)
            toast.overrideredirect(True)
            toast.attributes('-topmost', True)
            tk.Label(toast, text=text, bg='#2F2F2F', fg='#FFFFFF',
                    font=self.fonts.get('ui', ('微软雅黑', 10)),
                    padx=14, pady=8).pack()
            toast.update_idletasks()
            # 定位主窗口右下角
            x = self.root.winfo_rootx() + self.root.winfo_width() - toast.winfo_reqwidth() - 40
            y = self.root.winfo_rooty() + self.root.winfo_height() - toast.winfo_reqheight() - 70
            toast.geometry(f'+{max(0,x)}+{max(0,y)}')
            self._toast_win = toast
            self.root.after(ms, lambda: toast.destroy() if toast.winfo_exists() else None)
        except Exception as e:
            log.debug(f"toast失败: {e}")
    
    def _copy_poem(self):
        """复制诗句到剪贴板"""
        if not self.current_poem:
            return
        
        text = f"《{self.current_poem.get('title', '')}》\n"
        text += f"· {self.current_poem.get('author', '')} ({self.current_poem.get('dynasty', '')})\n\n"
        text += self.current_poem.get('content', '')
        
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self._show_toast("✓ 已复制全文到剪贴板")
    
    def _add_history(self, poem):
        """添加到历史记录"""
        self.history = [h for h in self.history if h.get('id') != poem.get('id')]
        self.history.insert(0, poem)
        if len(self.history) > self.max_history:
            self.history = self.history[:self.max_history]
    
    def _show_favorites(self):
        """显示收藏夹"""
        if not self.favorites:
            messagebox.showinfo("收藏夹", "收藏夹为空")
            return
        
        win = tk.Toplevel(self.root)
        win.title("收藏夹")
        win.geometry("500x600")
        
        listbox = tk.Listbox(win, font=('微软雅黑', 10))
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        for fav in self.favorites:
            listbox.insert(tk.END, f"《{fav.get('title', '')}》 - {fav.get('author', '')}")
        
        def on_select(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                poem = self.favorites[index]
                self._display_poem(poem)
                win.destroy()
        
        listbox.bind('<<ListboxSelect>>', on_select)
    
    def _show_history(self):
        """显示历史记录"""
        if not self.history:
            messagebox.showinfo("历史", "历史记录为空")
            return
        
        win = tk.Toplevel(self.root)
        win.title("历史记录")
        win.geometry("500x600")
        
        listbox = tk.Listbox(win, font=('微软雅黑', 10))
        listbox.pack(fill='both', expand=True, padx=10, pady=10)
        
        for h in self.history:
            listbox.insert(tk.END, f"《{h.get('title', '')}》 - {h.get('author', '')}")
        
        def on_select(event):
            selection = listbox.curselection()
            if selection:
                index = selection[0]
                poem = self.history[index]
                self._display_poem(poem)
                win.destroy()
        
        listbox.bind('<<ListboxSelect>>', on_select)
    
    def _show_stats(self):
        """显示统计信息"""
        if not HAS_UTILS or not self.db:
            messagebox.showinfo("提示", "统计功能需要安装 poetry_utils")
            return
        
        stats = get_poem_stats(self.db.poems)
        
        win = tk.Toplevel(self.root)
        win.title("诗词统计")
        win.geometry("400x500")
        
        text = tk.Text(win, font=('微软雅黑', 10))
        text.pack(fill='both', expand=True, padx=10, pady=10)
        
        text.insert(tk.END, "=== 朝代分布 ===\n")
        for dynasty, count in sorted(stats['dynasty'].items()):
            text.insert(tk.END, f"{dynasty}: {count} 首\n")
        
        text.insert(tk.END, "\n=== Top 20 诗人 ===\n")
        for author, count in sorted(stats['top_authors'].items(), key=lambda x: x[1], reverse=True)[:20]:
            text.insert(tk.END, f"{author}: {count} 首\n")
        
        text.config(state='disabled')
    
    def _export_favorites(self):
        """导出收藏夹"""
        if not self.favorites:
            messagebox.showinfo("提示", "收藏夹为空")
            return
        
        format_choice = messagebox.askyesno("导出格式", "选择导出格式:\n是 = JSON\n否 = TXT")
        
        if format_choice:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON文件", "*.json")],
                initialfile=f"poetry_favorites_{datetime.now().strftime('%Y%m%d')}"
            )
            
            if filename:
                try:
                    with open(filename, 'w', encoding='utf-8') as f:
                        json.dump(self.favorites, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("成功", f"已导出到 {filename}")
                except Exception as e:
                    messagebox.showerror("错误", f"导出失败: {e}")
        else:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt")],
                initialfile=f"poetry_favorites_{datetime.now().strftime('%Y%m%d')}"
            )
            
            if filename and HAS_UTILS:
                try:
                    export_poems_to_txt(self.favorites, filename)
                    messagebox.showinfo("成功", f"已导出到 {filename}")
                except Exception as e:
                    messagebox.showerror("错误", f"导出失败: {e}")
    
    def _load_favorites(self):
        """加载收藏（优先 data 目录，兼容旧位置）"""
        candidates = [DATA_DIR / "favorites.json", Path(__file__).parent / "favorites.json"]
        self.favorites = []
        for fav_file in candidates:
            if fav_file.exists():
                try:
                    with open(fav_file, encoding='utf-8') as f:
                        data = json.load(f)
                    if isinstance(data, list):
                        self.favorites = data
                        break
                except Exception:
                    continue
    
    def _save_favorites(self):
        """保存收藏（统一保存到 data 目录，与 exe 共享）"""
        fav_file = DATA_DIR / "favorites.json"
        try:
            with open(fav_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"保存收藏失败: {e}")
    
    # v3.0 新功能
    def _open_guwen(self, preselect_title=None):
        """打开古文阅读器"""
        if not HAS_GUWEN_UI:
            messagebox.showinfo("提示", "古文阅读模块未加载")
            return
        
        win = GuwenReader(self.root, self.theme_colors, preselect_title=preselect_title)
        win.grab_set()
    
    def _open_guwen_detail(self):
        """古文详细解读（译文/注释/赏析）"""
        if self.view_mode != 'guwen':
            self._show_toast("提示: 先切换到古文模式并选择一篇")
            return
        if not self.current_poem or not str(self.current_poem.get('id', '')).startswith('gw:'):
            self._show_toast("提示: 请先在左侧选择一篇古文")
            return
        self._open_guwen(preselect_title=self.current_poem.get('title', ''))
    
    # v7.0 新功能
    def _open_poet_profile(self):
        """打开诗人档案"""
        if not HAS_FEATURES_UI:
            messagebox.showinfo("提示", "诗人档案模块未加载")
            return
        
        # 获取当前诗词的作者
        if self.current_poem:
            author = self.current_poem.get('author', '')
        else:
            author = ''
        
        if not author:
            messagebox.showinfo("提示", "请先选择一首诗词")
            return
        
        win = PoetProfileWindow(self.root, author)
        win.grab_set()
    
    def _open_cipai(self):
        """打开词牌词典"""
        if not HAS_FEATURES_UI:
            messagebox.showinfo("提示", "词牌词典模块未加载")
            return
        
        win = CipaiWindow(self.root)
        win.grab_set()
    
    def _open_quotes(self):
        """打开名句欣赏"""
        if not HAS_QUOTES_UI:
            messagebox.showinfo("提示", "名句欣赏模块未加载")
            return
        
        def on_poem_select(poem_id):
            """点击查看原诗"""
            if not self.db:
                return
            for poem in self.db.poems:
                if poem.get('id') == poem_id:
                    self._display_poem(poem)
                    break
        
        win = QuotesWindow(self.root, on_poem_select=on_poem_select)
        win.grab_set()
    
    def _open_unified_search(self):
        """打开统一搜索"""
        if not HAS_FEATURES_UI:
            messagebox.showinfo("提示", "统一搜索模块未加载")
            return
        
        def on_poem_select(poem_id):
            """选中诗词"""
            for poem in self.db.poems:
                if poem.get('id') == poem_id:
                    self._display_poem(poem)
                    break
        
        def on_guwen_select(guwen_id):
            """选中古文"""
            if HAS_GUWEN_UI:
                win = GuwenReader(self.root, self.theme_colors)
                win.grab_set()
                win.after(300, lambda: win._display_essay(guwen_id))
        
        def on_author_select(author):
            """选中诗人"""
            win = PoetProfileWindow(self.root, author)
            win.grab_set()
        
        win = UnifiedSearchWindow(self.root, 
                                   on_poem_select=on_poem_select,
                                   on_guwen_select=on_guwen_select,
                                   on_author_select=on_author_select)
        win.grab_set()
    
    def _open_learning(self):
        """打开学习模式"""
        if not HAS_LEARNING_UI:
            messagebox.showinfo("提示", "学习模式模块未加载")
            return
        
        if not self.db:
            messagebox.showinfo("提示", "数据尚未加载完成")
            return
        
        ui = LearningMainUI(self.root, self.theme_colors, self.db)
        ui.show()
        self._grab_dialog(ui)
    
    def _open_game(self):
        """打开游戏"""
        if not HAS_GAME_UI:
            messagebox.showinfo("提示", "游戏模块未加载")
            return
        
        if not self.db:
            messagebox.showinfo("提示", "数据尚未加载完成")
            return
        
        ui = GameMainUI(self.root, self.theme_colors, self.db)
        ui.show()
        self._grab_dialog(ui)
    
    def _open_creation(self):
        """打开创作辅助"""
        if not HAS_CREATION_UI:
            messagebox.showinfo("提示", "创作辅助模块未加载")
            return
        
        if not self.db:
            messagebox.showinfo("提示", "数据尚未加载完成")
            return
        
        ui = CreationEditor(self.root, self.theme_colors, self.db)
        ui.show()
        self._grab_dialog(ui)
    
    def _grab_dialog(self, win_obj):
        """统一对对话框执行 grab_set（兼容包装类/Toplevel/win容器）"""
        for attr in ('dialog', 'win'):
            w = getattr(win_obj, attr, None)
            if w is not None:
                try:
                    w.grab_set()
                    return
                except Exception:
                    pass
        try:
            win_obj.grab_set()
        except Exception:
            pass
    
    def _open_collection_manager(self):
        """打开收藏管理"""
        if not HAS_COLLECTION_MANAGER:
            messagebox.showinfo("提示", "收藏管理模块未加载")
            return
        
        if not self.db:
            messagebox.showinfo("提示", "数据尚未加载完成")
            return
        
        dialog = CollectionDialog(self.root, self.db, self.collection_manager, self.theme_colors)
        dialog.parent = self  # 让「查看」能联动主窗口显示
        self._grab_dialog(dialog)
    
    def _open_visualization(self):
        """打开数据可视化"""
        if not HAS_VISUALIZATION:
            messagebox.showinfo("提示", "数据可视化模块未加载")
            return
        
        if not self.db:
            messagebox.showinfo("提示", "数据尚未加载完成")
            return
        
        dialog = VisualizationDialog(self.root, self.db, self.chart_manager, self.theme_colors)
        self._grab_dialog(dialog)
    
    # v6.0 新功能
    def _open_language_settings(self):
        """打开语言设置"""
        if not HAS_I18N:
            messagebox.showinfo("提示", "多语言模块未加载")
            return
        
        dialog = LanguageSelector(self.root, self.translation_manager)
        self._grab_dialog(dialog)
    
    def _open_plugin_manager(self):
        """打开插件管理"""
        if not HAS_PLUGIN_SYSTEM:
            messagebox.showinfo("提示", "插件系统模块未加载")
            return
        
        dialog = PluginConfigDialog(self.root, self.plugin_manager)
        self._grab_dialog(dialog)
    
    def _open_cloud_sync(self):
        """打开云端同步"""
        if not HAS_CLOUD_SYNC:
            messagebox.showinfo("提示", "云端同步模块未加载")
            return
        
        dialog = SyncDialog(self.root, self.cloud_sync_manager)
        self._grab_dialog(dialog)


def main():
    root = tk.Tk()
    app = PoetryApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
