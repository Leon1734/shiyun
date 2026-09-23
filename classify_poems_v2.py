#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词多维度分类系统
分类维度：朝代、诗体、字数、格律、题材
"""

import sqlite3
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("classify")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "poetry.db"

# 朝代详细分期
DYNASTY_PERIODS = {
    "先秦": {"start": -221, "end": -207, "desc": "秦朝之前（夏商周春秋战国）"},
    "秦": {"start": -221, "end": -207, "desc": "秦朝"},
    "汉": {"start": -206, "end": 220, "desc": "西汉+东汉"},
    "三国": {"start": 220, "end": 280, "desc": "魏蜀吴"},
    "晋": {"start": 265, "end": 420, "desc": "西晋+东晋"},
    "南北朝": {"start": 420, "end": 589, "desc": "南朝+北朝"},
    "隋": {"start": 581, "end": 618, "desc": "隋朝"},
    "唐": {"start": 618, "end": 907, "desc": "唐朝"},
    "五代": {"start": 907, "end": 960, "desc": "五代十国"},
    "宋": {"start": 960, "end": 1279, "desc": "北宋+南宋"},
    "辽": {"start": 907, "end": 1125, "desc": "辽朝"},
    "金": {"start": 1115, "end": 1234, "desc": "金朝"},
    "元": {"start": 1271, "end": 1368, "desc": "元朝"},
    "明": {"start": 1368, "end": 1644, "desc": "明朝"},
    "清": {"start": 1644, "end": 1912, "desc": "清朝"},
    "近现代": {"start": 1912, "end": 2024, "desc": "近现代"},
}

# 诗体分类
POEM_FORMS = {
    "五言绝句": {"chars_per_line": 5, "lines": 4, "desc": "每句5字，共4句"},
    "七言绝句": {"chars_per_line": 7, "lines": 4, "desc": "每句7字，共4句"},
    "五言律诗": {"chars_per_line": 5, "lines": 8, "desc": "每句5字，共8句"},
    "七言律诗": {"chars_per_line": 7, "lines": 8, "desc": "每句7字，共8句"},
    "五言古诗": {"chars_per_line": 5, "lines": None, "desc": "每句5字，句数不限"},
    "七言古诗": {"chars_per_line": 7, "lines": None, "desc": "每句7字，句数不限"},
    "乐府": {"chars_per_line": None, "lines": None, "desc": "乐府诗"},
    "词": {"chars_per_line": None, "lines": None, "desc": "词牌体"},
    "曲": {"chars_per_line": None, "lines": None, "desc": "曲牌体"},
    "杂言": {"chars_per_line": None, "lines": None, "desc": "字数不固定"},
}

def detect_poem_form(content):
    """
    检测诗体
    
    Returns:
        dict: {
            'form': 诗体名称,
            'chars_per_line': 每句字数,
            'lines': 句数,
            'is_regular': 是否格律诗
        }
    """
    if not content:
        return {'form': '未知', 'chars_per_line': 0, 'lines': 0, 'is_regular': False}
    
    # 清理内容
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    
    # 过滤掉标题、作者等非诗句行
    poem_lines = []
    for line in lines:
        # 跳过包含特殊字符的行（可能是标题、注释等）
        if any(c in line for c in ['《', '》', '（', '）', '：', '；']):
            continue
        # 跳过过短的行
        if len(line) < 2:
            continue
        poem_lines.append(line)
    
    if not poem_lines:
        return {'form': '未知', 'chars_per_line': 0, 'lines': 0, 'is_regular': False}
    
    # 统计每句字数
    line_lengths = []
    for line in poem_lines:
        # 去除标点符号
        clean_line = re.sub(r'[，。！？、；：""''（）《》\s]', '', line)
        if clean_line:
            line_lengths.append(len(clean_line))
    
    if not line_lengths:
        return {'form': '未知', 'chars_per_line': 0, 'lines': 0, 'is_regular': False}
    
    # 计算平均字数和句数
    avg_chars = sum(line_lengths) / len(line_lengths)
    num_lines = len(line_lengths)
    
    # 判断诗体
    is_regular = False
    form = '杂言'
    chars_per_line = int(round(avg_chars))
    
    # 检查是否为格律诗（绝句或律诗）
    if num_lines == 4:
        if abs(avg_chars - 5) < 1:
            form = '五言绝句'
            is_regular = True
        elif abs(avg_chars - 7) < 1:
            form = '七言绝句'
            is_regular = True
    elif num_lines == 8:
        if abs(avg_chars - 5) < 1:
            form = '五言律诗'
            is_regular = True
        elif abs(avg_chars - 7) < 1:
            form = '七言律诗'
            is_regular = True
    elif num_lines > 8:
        if abs(avg_chars - 5) < 1:
            form = '五言古诗'
        elif abs(avg_chars - 7) < 1:
            form = '七言古诗'
    elif num_lines < 4:
        if abs(avg_chars - 5) < 1:
            form = '五言绝句'
        elif abs(avg_chars - 7) < 1:
            form = '七言绝句'
    
    return {
        'form': form,
        'chars_per_line': chars_per_line,
        'lines': num_lines,
        'is_regular': is_regular
    }

def classify_all_poems():
    """对所有诗词进行多维度分类"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 添加新列
    cursor.execute("PRAGMA table_info(poems)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = {
        'poem_form': 'TEXT DEFAULT ""',      # 诗体
        'chars_per_line': 'INTEGER DEFAULT 0', # 每句字数
        'line_count': 'INTEGER DEFAULT 0',     # 句数
        'is_regular': 'INTEGER DEFAULT 0',     # 是否格律诗
        'word_count': 'INTEGER DEFAULT 0',     # 总字数
    }
    
    for col, dtype in new_columns.items():
        if col not in columns:
            log.info(f"添加列: {col}")
            cursor.execute(f"ALTER TABLE poems ADD COLUMN {col} {dtype}")
    
    conn.commit()
    
    # 获取总数
    cursor.execute("SELECT COUNT(*) FROM poems")
    total = cursor.fetchone()[0]
    log.info(f"诗词总数: {total}")
    
    # 获取待分类的诗词
    cursor.execute("SELECT id, title, content FROM poems WHERE poem_form = '' OR poem_form IS NULL")
    poems = cursor.fetchall()
    log.info(f"待分类: {len(poems)} 首")
    
    # 批量分类
    batch_size = 1000
    classified = 0
    
    for i in range(0, len(poems), batch_size):
        batch = poems[i:i+batch_size]
        
        for poem in batch:
            poem_id = poem['id']
            content = poem['content'] or ''
            
            # 检测诗体
            result = detect_poem_form(content)
            
            # 计算总字数
            clean_content = re.sub(r'[，。！？、；：""''（）《》\s\n]', '', content)
            word_count = len(clean_content)
            
            # 更新数据库
            cursor.execute("""
                UPDATE poems SET 
                    poem_form = ?, 
                    chars_per_line = ?, 
                    line_count = ?, 
                    is_regular = ?,
                    word_count = ?
                WHERE id = ?
            """, (result['form'], result['chars_per_line'], result['lines'], 
                  1 if result['is_regular'] else 0, word_count, poem_id))
        
        conn.commit()
        classified += len(batch)
        log.info(f"已分类: {classified}/{len(poems)} ({classified*100//len(poems)}%)")
    
    # 创建索引
    log.info("创建索引...")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_poem_form ON poems(poem_form)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_chars_per_line ON poems(chars_per_line)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_line_count ON poems(line_count)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_is_regular ON poems(is_regular)")
    conn.commit()
    
    # 统计
    log.info("\n=== 诗体分布 ===")
    cursor.execute("SELECT poem_form, COUNT(*) FROM poems WHERE poem_form != '' GROUP BY poem_form ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        log.info(f"  {row[0]}: {row[1]} 首")
    
    log.info("\n=== 每句字数分布 ===")
    cursor.execute("SELECT chars_per_line, COUNT(*) FROM poems WHERE chars_per_line > 0 GROUP BY chars_per_line ORDER BY COUNT(*) DESC")
    for row in cursor.fetchall():
        log.info(f"  {row[0]}字: {row[1]} 首")
    
    log.info("\n=== 格律诗统计 ===")
    cursor.execute("SELECT is_regular, COUNT(*) FROM poems GROUP BY is_regular")
    for row in cursor.fetchall():
        label = "格律诗" if row[0] == 1 else "非格律诗"
        log.info(f"  {label}: {row[1]} 首")
    
    conn.close()
    log.info("全部完成!")

if __name__ == "__main__":
    log.info("=== 诗词多维度分类 ===")
    classify_all_poems()
