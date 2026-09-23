#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
学习模式模块
功能：间隔重复算法、学习计划、学习进度追踪、错题本
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import logging

log = logging.getLogger("poetry")

# 数据库路径
# 路径：优先 data 目录（与 exe 共享；打包后 _internal 只读）
try:
    from app_paths import get_data_dir as _get_data_dir
    DB_PATH = _get_data_dir() / "learning.db"
except Exception:
    DB_PATH = Path(__file__).parent / "data" / "learning.db"


class LearningManager:
    """学习模式管理器"""
    
    def __init__(self, db):
        self.db = db
        self.conn = None
        self._init_database()
    
    def _init_database(self):
        """初始化数据库"""
        try:
            self.conn = sqlite3.connect(str(DB_PATH))
            cursor = self.conn.cursor()
            
            # 创建学习记录表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_records (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poem_id TEXT NOT NULL,
                    poem_title TEXT,
                    poem_author TEXT,
                    last_review DATETIME,
                    next_review DATETIME,
                    ease_factor REAL DEFAULT 2.5,
                    interval INTEGER DEFAULT 0,
                    repetitions INTEGER DEFAULT 0,
                    quality INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建学习计划表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS learning_plans (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_name TEXT NOT NULL,
                    daily_count INTEGER DEFAULT 10,
                    dynasty TEXT,
                    author TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # 创建错题本表
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS wrong_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    poem_id TEXT NOT NULL,
                    poem_title TEXT,
                    poem_author TEXT,
                    wrong_count INTEGER DEFAULT 1,
                    last_wrong DATETIME DEFAULT CURRENT_TIMESTAMP,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            self.conn.commit()
            log.info("学习数据库初始化完成")
        except Exception as e:
            log.error(f"初始化学习数据库失败: {e}")
    
    def sm2_algorithm(self, quality, repetitions, ease_factor, interval):
        """
        SM-2间隔重复算法
        
        参数:
            quality: 回忆质量 (0-5)
            repetitions: 重复次数
            ease_factor: 容易度因子
            interval: 间隔天数
        
        返回:
            (repetitions, ease_factor, interval)
        """
        if quality >= 3:
            if repetitions == 0:
                interval = 1
            elif repetitions == 1:
                interval = 6
            else:
                interval = round(interval * ease_factor)
            repetitions += 1
        else:
            repetitions = 0
            interval = 1
        
        ease_factor = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
        if ease_factor < 1.3:
            ease_factor = 1.3
        
        return repetitions, ease_factor, interval
    
    def add_learning_record(self, poem, quality=3):
        """添加学习记录"""
        try:
            cursor = self.conn.cursor()
            
            # 检查是否已有记录
            cursor.execute(
                "SELECT * FROM learning_records WHERE poem_id = ?",
                (poem.get('id', ''),)
            )
            record = cursor.fetchone()
            
            now = datetime.now()
            
            if record:
                # 更新现有记录
                _, _, _, _, _, _, ease_factor, interval, repetitions, _, _ = record
                repetitions, ease_factor, interval = self.sm2_algorithm(
                    quality, repetitions, ease_factor, interval
                )
                next_review = now + timedelta(days=interval)
                
                cursor.execute('''
                    UPDATE learning_records 
                    SET last_review = ?, next_review = ?, ease_factor = ?, 
                        interval = ?, repetitions = ?, quality = ?
                    WHERE poem_id = ?
                ''', (now, next_review, ease_factor, interval, repetitions, quality, poem.get('id', '')))
            else:
                # 创建新记录
                repetitions, ease_factor, interval = self.sm2_algorithm(quality, 0, 2.5, 0)
                next_review = now + timedelta(days=interval)
                
                cursor.execute('''
                    INSERT INTO learning_records 
                    (poem_id, poem_title, poem_author, last_review, next_review, 
                     ease_factor, interval, repetitions, quality)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (poem.get('id', ''), poem.get('title', ''), poem.get('author', ''),
                      now, next_review, ease_factor, interval, repetitions, quality))
            
            self.conn.commit()
            return True
        except Exception as e:
            log.error(f"添加学习记录失败: {e}")
            return False
    
    def get_today_poems(self, count=10):
        """获取今日学习诗词"""
        try:
            cursor = self.conn.cursor()
            now = datetime.now()
            
            # 获取需要复习的诗词
            cursor.execute('''
                SELECT * FROM learning_records 
                WHERE next_review <= ? 
                ORDER BY next_review ASC 
                LIMIT ?
            ''', (now, count))
            records = cursor.fetchall()
            
            poems = []
            for record in records:
                poem_id = record[1]
                # 从数据库中查找诗词
                for poem in self.db.poems:
                    if poem.get('id', '') == poem_id:
                        poems.append(poem)
                        break
            
            # 如果需要复习的诗词不够，添加新诗词
            if len(poems) < count:
                learned_ids = [r[1] for r in records]
                new_poems = [p for p in self.db.poems if p.get('id', '') not in learned_ids]
                if new_poems:
                    import random
                    new_count = min(count - len(poems), len(new_poems))
                    poems.extend(random.sample(new_poems, new_count))
            
            return poems
        except Exception as e:
            log.error(f"获取今日诗词失败: {e}")
            return []
    
    def get_learning_stats(self):
        """获取学习统计"""
        try:
            cursor = self.conn.cursor()
            
            # 总学习诗词数
            cursor.execute("SELECT COUNT(*) FROM learning_records")
            total_learned = cursor.fetchone()[0]
            
            # 今日学习诗词数
            today = datetime.now().date()
            cursor.execute(
                "SELECT COUNT(*) FROM learning_records WHERE DATE(last_review) = ?",
                (today,)
            )
            today_learned = cursor.fetchone()[0]
            
            # 需要复习诗词数
            cursor.execute(
                "SELECT COUNT(*) FROM learning_records WHERE next_review <= ?",
                (datetime.now(),)
            )
            need_review = cursor.fetchone()[0]
            
            # 错题数量
            cursor.execute("SELECT COUNT(*) FROM wrong_answers")
            wrong_count = cursor.fetchone()[0]
            
            return {
                'total_learned': total_learned,
                'today_learned': today_learned,
                'need_review': need_review,
                'wrong_count': wrong_count
            }
        except Exception as e:
            log.error(f"获取学习统计失败: {e}")
            return {}
    
    def add_wrong_answer(self, poem):
        """添加错题"""
        try:
            cursor = self.conn.cursor()
            
            # 检查是否已有记录
            cursor.execute(
                "SELECT * FROM wrong_answers WHERE poem_id = ?",
                (poem.get('id', ''),)
            )
            record = cursor.fetchone()
            
            if record:
                # 更新错题次数
                cursor.execute('''
                    UPDATE wrong_answers 
                    SET wrong_count = wrong_count + 1, last_wrong = ?
                    WHERE poem_id = ?
                ''', (datetime.now(), poem.get('id', '')))
            else:
                # 创建新记录
                cursor.execute('''
                    INSERT INTO wrong_answers (poem_id, poem_title, poem_author)
                    VALUES (?, ?, ?)
                ''', (poem.get('id', ''), poem.get('title', ''), poem.get('author', '')))
            
            self.conn.commit()
            return True
        except Exception as e:
            log.error(f"添加错题失败: {e}")
            return False
    
    def get_wrong_poems(self, limit=50):
        """获取错题本"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT * FROM wrong_answers 
                ORDER BY wrong_count DESC, last_wrong DESC 
                LIMIT ?
            ''', (limit,))
            records = cursor.fetchall()
            
            poems = []
            for record in records:
                poem_id = record[1]
                for poem in self.db.poems:
                    if poem.get('id', '') == poem_id:
                        poems.append(poem)
                        break
            
            return poems
        except Exception as e:
            log.error(f"获取错题本失败: {e}")
            return []
    
    def create_learning_plan(self, plan_name, daily_count=10, dynasty=None, author=None):
        """创建学习计划"""
        try:
            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO learning_plans (plan_name, daily_count, dynasty, author)
                VALUES (?, ?, ?, ?)
            ''', (plan_name, daily_count, dynasty, author))
            self.conn.commit()
            return True
        except Exception as e:
            log.error(f"创建学习计划失败: {e}")
            return False
    
    def get_learning_plans(self):
        """获取学习计划"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM learning_plans ORDER BY created_at DESC")
            return cursor.fetchall()
        except Exception as e:
            log.error(f"获取学习计划失败: {e}")
            return []
    
    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
