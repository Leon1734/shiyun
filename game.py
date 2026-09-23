#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
游戏化模块
功能：诗词接龙、飞花令、知识竞赛、排行榜、成就系统
"""

import json
import sqlite3
import random
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import logging

log = logging.getLogger("poetry")

# 数据库路径
# 路径：优先 data 目录（与 exe 共享；打包后 _internal 只读）
try:
    from app_paths import get_data_dir as _get_data_dir
    DB_PATH = _get_data_dir() / "game.db"
except Exception:
    DB_PATH = Path(__file__).parent / "data" / "game.db"


class GameManager:
    """游戏化管理器"""
    
    def __init__(self, db):
        self.db = db
        self.conn = None
        self._init_database()
        self._build_poem_index()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.conn = sqlite3.connect(str(DB_PATH))
            cursor = self.conn.cursor()
            
            # 创建游戏成绩表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT DEFAULT 'default',
                    game_type TEXT NOT NULL,
                    score INTEGER DEFAULT 0,
                    duration INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建成就表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS achievements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_name TEXT DEFAULT 'default',
                    achievement_type TEXT NOT NULL,
                    achievement_name TEXT NOT NULL,
                    achieved_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            log.info("游戏数据库初始化完成")
        except Exception as e:
            log.error(f"初始化游戏数据库失败: {e}")
    
    def _build_poem_index(self):
        """构建诗词索引"""
        self.poem_by_first_char = defaultdict(list)
        self.poem_by_last_char = defaultdict(list)
        self.poem_by_keyword = defaultdict(list)
        
        for poem in self.db.poems:
            content = poem.get('content', '')
            if isinstance(content, list):
                content = '\n'.join(content)
            
            # 按首字索引
            if content:
                first_char = content[0]
                if '\u4e00' <= first_char <= '\u9fff':
                    self.poem_by_first_char[first_char].append(poem)
            
            # 按末字索引
            if content:
                last_char = content[-1]
                if '\u4e00' <= last_char <= '\u9fff':
                    self.poem_by_last_char[last_char].append(poem)
            
            # 按关键词索引
            title = poem.get('title', '')
            for char in title:
                if '\u4e00' <= char <= '\u9fff':
                    self.poem_by_keyword[char].append(poem)
    
    def chain_game_start(self):
        """诗词接龙游戏开始"""
        # 随机选择一首诗作为起始
        start_poem = random.choice(self.db.poems)
        return {
            'poem': start_poem,
            'chain': [start_poem],
            'score': 0,
            'status': 'playing'
        }
    
    def chain_game_play(self, game_state, user_poem):
        """诗词接龙游戏出牌"""
        if game_state['status'] != 'playing':
            return game_state
        
        last_poem = game_state['chain'][-1]
        last_content = last_poem.get('content', '')
        if isinstance(last_content, list):
            last_content = '\n'.join(last_content)
        
        # 获取最后一个字
        last_char = ''
        for char in reversed(last_content):
            if '\u4e00' <= char <= '\u9fff':
                last_char = char
                break
        
        # 获取用户诗词的第一个字
        user_content = user_poem.get('content', '')
        if isinstance(user_content, list):
            user_content = '\n'.join(user_content)
        
        first_char = ''
        for char in user_content:
            if '\u4e00' <= char <= '\u9fff':
                first_char = char
                break
        
        # 检查是否接龙成功
        if last_char == first_char:
            game_state['chain'].append(user_poem)
            game_state['score'] += 1
            return game_state
        else:
            game_state['status'] = 'failed'
            return game_state
    
    def chain_game_hint(self, game_state):
        """诗词接龙提示"""
        last_poem = game_state['chain'][-1]
        last_content = last_poem.get('content', '')
        if isinstance(last_content, list):
            last_content = '\n'.join(last_content)
        
        last_char = ''
        for char in reversed(last_content):
            if '\u4e00' <= char <= '\u9fff':
                last_char = char
                break
        
        # 查找以该字开头的诗词
        candidates = self.poem_by_first_char.get(last_char, [])
        if candidates:
            return random.choice(candidates)
        return None
    
    def feihualing_start(self, keyword=None):
        """飞花令游戏开始"""
        if not keyword:
            # 随机选择一个常见字
            common_chars = ['月', '花', '风', '雪', '春', '秋', '山', '水', '人', '情']
            keyword = random.choice(common_chars)
        
        # 查找包含该字的诗词
        candidates = self.poem_by_keyword.get(keyword, [])
        if not candidates:
            # 如果没有找到，随机选择
            candidates = random.sample(self.db.poems, min(10, len(self.db.poems)))
        
        return {
            'keyword': keyword,
            'candidates': candidates[:10],
            'used': [],
            'score': 0,
            'status': 'playing'
        }
    
    def feihualing_play(self, game_state, user_poem):
        """飞花令游戏出牌"""
        if game_state['status'] != 'playing':
            return game_state
        
        keyword = game_state['keyword']
        user_content = user_poem.get('content', '')
        if isinstance(user_content, list):
            user_content = '\n'.join(user_content)
        
        # 检查是否包含关键字
        if keyword in user_content:
            game_state['used'].append(user_poem)
            game_state['score'] += 1
            return game_state
        else:
            game_state['status'] = 'failed'
            return game_state
    
    def quiz_start(self, count=10):
        """知识竞赛开始"""
        # 随机选择诗词
        poems = random.sample(self.db.poems, min(count, len(self.db.poems)))
        
        questions = []
        for poem in poems:
            content = poem.get('content', '')
            if isinstance(content, list):
                content = '\n'.join(content)
            
            # 生成问题：给出下句，猜上句
            lines = content.split('\n')
            if len(lines) >= 2:
                question = {
                    'poem': poem,
                    'question': f"请补全诗句：{lines[0]}...",
                    'answer': lines[1] if len(lines) > 1 else '',
                    'options': self._generate_options(lines[1] if len(lines) > 1 else '', poem)
                }
                questions.append(question)
        
        return {
            'questions': questions,
            'current': 0,
            'score': 0,
            'status': 'playing'
        }
    
    def _generate_options(self, correct_answer, current_poem):
        """生成选项"""
        options = [correct_answer]
        
        # 从其他诗词中随机选择3个错误选项
        other_poems = [p for p in self.db.poems if p.get('id') != current_poem.get('id')]
        if len(other_poems) >= 3:
            random_poems = random.sample(other_poems, 3)
            for poem in random_poems:
                content = poem.get('content', '')
                if isinstance(content, list):
                    content = '\n'.join(content)
                lines = content.split('\n')
                if len(lines) > 1:
                    options.append(lines[1])
        
        # 随机打乱选项
        random.shuffle(options)
        return options
    
    def quiz_answer(self, game_state, answer_index):
        """知识竞赛回答"""
        if game_state['status'] != 'playing':
            return game_state
        
        current_q = game_state['questions'][game_state['current']]
        correct_answer = current_q['answer']
        options = current_q['options']
        
        if 0 <= answer_index < len(options) and options[answer_index] == correct_answer:
            game_state['score'] += 1
        
        game_state['current'] += 1
        
        if game_state['current'] >= len(game_state['questions']):
            game_state['status'] = 'finished'
        
        return game_state
    
    def save_score(self, game_type, score, duration=0):
        """保存游戏成绩"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO game_scores (game_type, score, duration)
                VALUES (?, ?, ?)
            ''', (game_type, score, duration))
            self.conn.commit()
            return True
        except Exception as e:
            log.error(f"保存游戏成绩失败: {e}")
            return False
    
    def get_leaderboard(self, game_type, limit=10):
        """获取排行榜"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM game_scores 
                WHERE game_type = ? 
                ORDER BY score DESC, duration ASC 
                LIMIT ?
            ''', (game_type, limit))
            return cursor.fetchall()
        except Exception as e:
            log.error(f"获取排行榜失败: {e}")
            return []
    
    def check_achievement(self, game_type, score):
        """检查成就"""
        achievements = []
        
        if game_type == 'chain':
            if score >= 10:
                achievements.append('诗词接龙达人')
            if score >= 20:
                achievements.append('诗词接龙大师')
            if score >= 50:
                achievements.append('诗词接龙宗师')
        
        elif game_type == 'feihualing':
            if score >= 5:
                achievements.append('飞花令新手')
            if score >= 10:
                achievements.append('飞花令高手')
            if score >= 20:
                achievements.append('飞花令大师')
        
        elif game_type == 'quiz':
            if score >= 8:
                achievements.append('知识竞赛优秀')
            if score >= 9:
                achievements.append('知识竞赛卓越')
            if score >= 10:
                achievements.append('知识竞赛满分')
        
        # 保存成就
        for achievement in achievements:
            self._save_achievement(achievement)
        
        return achievements
    
    def _save_achievement(self, achievement_name):
        """保存成就"""
        try:
            cursor = self.conn.cursor()
            
            # 检查是否已有该成就
            cursor.execute(
                "SELECT * FROM achievements WHERE achievement_name = ?",
                (achievement_name,)
            )
            if not cursor.fetchone():
                cursor.execute('''
                    INSERT INTO achievements (achievement_name)
                    VALUES (?)
                ''', (achievement_name,))
                self.conn.commit()
        except Exception as e:
            log.error(f"保存成就失败: {e}")
    
    def get_achievements(self):
        """获取所有成就"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM achievements ORDER BY achieved_at DESC")
            return cursor.fetchall()
        except Exception as e:
            log.error(f"获取成就失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
