#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗人档案模块
- 诗人统计（作品数、朝代、合集分布）
- 题材分布分析
- 代表作推荐
- 印章式头像生成
"""

import sqlite3
import logging
from pathlib import Path
from collections import Counter

log = logging.getLogger("poetry")

try:
    from app_paths import get_db_path
    DB_PATH = get_db_path()
except ImportError:
    DB_PATH = Path(__file__).parent / "data" / "poetry.db"

try:
    from famous_authors import author_rank
except ImportError:
    def author_rank(a):
        return 0


class PoetProfile:
    """诗人档案数据类"""
    
    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._conn = None
    
    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def get_profile(self, author):
        """获取诗人档案"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 基本信息
            cursor.execute('''
                SELECT dynasty, COUNT(*) as cnt,
                       MIN(id) as first_id
                FROM poems WHERE author = ?
                GROUP BY dynasty
                ORDER BY cnt DESC
            ''', (author,))
            dynasties = cursor.fetchall()
            
            if not dynasties:
                return None
            
            primary_dynasty = dynasties[0]['dynasty']
            total_poems = sum(d['cnt'] for d in dynasties)
            
            # 合集分布
            cursor.execute('''
                SELECT collection, COUNT(*) as cnt FROM poems
                WHERE author = ? AND collection != ''
                GROUP BY collection ORDER BY cnt DESC
            ''', (author,))
            collections = [(r['collection'], r['cnt']) for r in cursor.fetchall()]
            
            # 题材分布
            cursor.execute('''
                SELECT theme, COUNT(*) as cnt FROM poems
                WHERE author = ? AND theme != ''
                GROUP BY theme ORDER BY cnt DESC LIMIT 8
            ''', (author,))
            themes = [(r['theme'], r['cnt']) for r in cursor.fetchall()]
            
            # 诗体分布
            cursor.execute('''
                SELECT poem_form, COUNT(*) as cnt FROM poems
                WHERE author = ? AND poem_form != ''
                GROUP BY poem_form ORDER BY cnt DESC LIMIT 8
            ''', (author,))
            forms = [(r['poem_form'], r['cnt']) for r in cursor.fetchall()]
            
            # 代表作（经典度优先）
            cursor.execute('''
                SELECT id, title, dynasty, collection, content
                FROM poems WHERE author = ?
                ORDER BY classic_score DESC, LENGTH(content) LIMIT 5
            ''', (author,))
            famous = [dict(r) for r in cursor.fetchall()]
            
            return {
                'author': author,
                'dynasty': primary_dynasty,
                'total': total_poems,
                'dynasties': [(d['dynasty'], d['cnt']) for d in dynasties],
                'collections': collections,
                'themes': themes,
                'forms': forms,
                'famous': famous,
            }
        except Exception as e:
            log.error(f"获取诗人档案失败: {e}")
            return None
    
    def get_top_authors(self, limit=50):
        """获取诗人排行（著名诗人优先，其次高产）"""
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute('''
                SELECT author, dynasty, COUNT(*) as cnt FROM poems
                GROUP BY author ORDER BY cnt DESC LIMIT 300
            ''')
            rows = [(r['author'], r['dynasty'], r['cnt']) for r in cursor.fetchall()]
            rows.sort(key=lambda r: (-author_rank(r[0]), -r[2]))
            return rows[:limit]
        except Exception as e:
            log.error(f"获取诗人排行失败: {e}")
            return []


def generate_seal_avatar(author_name, size=120, output_path=None):
    """
    生成印章风格诗人头像
    - 朱砂红方印
    - 白文（阴刻）字体效果
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return None
    
    # 取名字（最多2字用于印章）
    name = author_name[:2] if len(author_name) > 2 else author_name
    if len(author_name) > 2:
        # 三字以上取最后1-2字更传统（如"李太白"→"太白"）
        name = author_name[-2:]
    
    # 创建图片
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 印章底色（朱砂红）
    seal_color = (140, 47, 57, 255)  # #8C2F39
    margin = 4
    draw.rounded_rectangle([margin, margin, size-margin, size-margin], 
                           radius=8, fill=seal_color)
    
    # 边框（白色内框）
    draw.rounded_rectangle([margin+4, margin+4, size-margin-4, size-margin-4],
                           radius=5, outline=(255, 248, 240, 200), width=2)
    
    # 字体
    font = None
    font_size = size // 2 - 8
    for fp in ["C:/Windows/Fonts/simkai.ttf", "C:/Windows/Fonts/STKAITI.TTF",
               "C:/Windows/Fonts/simsun.ttc", "C:/Windows/Fonts/msyh.ttc"]:
        try:
            font = ImageFont.truetype(fp, font_size)
            break
        except:
            continue
    
    if font is None:
        font = ImageFont.load_default()
    
    # 绘制文字（白色，印章式）
    if len(name) == 1:
        # 单字居中
        bbox = draw.textbbox((0, 0), name, font=font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text(((size-tw)/2 - bbox[0], (size-th)/2 - bbox[1]), name, 
                  font=font, fill=(255, 248, 240, 255))
    else:
        # 双字竖排
        font_size2 = size // 2 - 12
        for fp in ["C:/Windows/Fonts/simkai.ttf", "C:/Windows/Fonts/STKAITI.TTF"]:
            try:
                font2 = ImageFont.truetype(fp, font_size2)
                break
            except:
                font2 = font
                continue
        
        for i, char in enumerate(name[:2]):
            bbox = draw.textbbox((0, 0), char, font=font2)
            tw = bbox[2] - bbox[0]
            x = (size - tw) / 2 - bbox[0]
            y = margin + 10 + i * (font_size2 + 2)
            draw.text((x, y), char, font=font2, fill=(255, 248, 240, 255))
    
    if output_path:
        img.save(output_path)
        return output_path
    return img


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== 诗人档案测试 ===")
    prof = PoetProfile()
    
    # 测试苏轼
    profile = prof.get_profile('苏轼')
    if profile:
        print(f"诗人: {profile['author']} ({profile['dynasty']})")
        print(f"作品总数: {profile['total']}")
        print(f"合集分布: {profile['collections'][:3]}")
        print(f"题材分布: {profile['themes'][:3]}")
        print(f"诗体分布: {profile['forms'][:3]}")
        print(f"代表作: {[f['title'] for f in profile['famous'][:3]]}")
    
    print()
    print("=== 印章头像测试 ===")
    path = generate_seal_avatar('李白', output_path='test_seal.png')
    print(f"印章生成: {path}")
