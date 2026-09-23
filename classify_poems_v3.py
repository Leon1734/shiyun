#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诗词分类修复 v3
修复诗体检测逻辑：按标点切分句子，统计每句字数
"""

import sqlite3
import re
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger("classify")

DATA_DIR = Path(__file__).parent / "data"
DB_PATH = DATA_DIR / "poetry.db"


def detect_poem_form_v3(content):
    """
    检测诗体 v3 - 按标点切分句子
    
    诗句格式: '床前看月光，疑是地上霜。\n举头望山月，低头思故乡。'
    → 切分后: ['床前看月光', '疑是地上霜', '举头望山月', '低头思故乡']
    → 每句5字，共4句 → 五言绝句
    """
    if not content:
        return {'form': '未知', 'chars_per_line': 0, 'lines': 0, 'is_regular': False}
    
    # 按中文标点切分句子
    sentences = re.split(r'[，。！？、；：\n]', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    # 过滤掉可能的标题行（包含《》等）
    sentences = [s for s in sentences if not re.search(r'[《》（）\u3000]', s)]
    
    if not sentences:
        return {'form': '未知', 'chars_per_line': 0, 'lines': 0, 'is_regular': False}
    
    # 统计每句字数
    sent_lengths = [len(s) for s in sentences]
    
    # 计算平均字数和句数
    avg_len = sum(sent_lengths) / len(sent_lengths)
    num_sentences = len(sent_lengths)
    
    # 判断五言/七言
    is_5char = all(4 <= l <= 6 for l in sent_lengths)
    is_7char = all(6 <= l <= 8 for l in sent_lengths)
    
    # 判断格律诗
    is_regular = False
    form = '杂言'
    
    if is_7char and 6 >= avg_len >= 6.5:
        pass  # will handle below
    
    if is_5char and not is_7char:
        # 五言
        if num_sentences == 4:
            form = '五言绝句'
            is_regular = True
        elif num_sentences == 8:
            form = '五言律诗'
            is_regular = True
        elif num_sentences == 12 or num_sentences == 16 or num_sentences == 20:
            form = f'五言排律({num_sentences}句)'
            is_regular = True
        elif num_sentences > 4:
            form = '五言古诗'
    elif is_7char and not is_5char:
        # 七言
        if num_sentences == 4:
            form = '七言绝句'
            is_regular = True
        elif num_sentences == 8:
            form = '七言律诗'
            is_regular = True
        elif num_sentences == 12 or num_sentences == 16 or num_sentences == 20:
            form = f'七言排律({num_sentences}句)'
            is_regular = True
        elif num_sentences > 4:
            form = '七言古诗'
    else:
        # 杂言 - 检查是否接近五言或七言
        if 4.5 <= avg_len <= 5.5 and num_sentences >= 4:
            if num_sentences == 4:
                form = '五言绝句'
                is_regular = True
            elif num_sentences == 8:
                form = '五言律诗'
                is_regular = True
            elif num_sentences > 4:
                form = '五言古诗'
        elif 6.5 <= avg_len <= 7.5 and num_sentences >= 4:
            if num_sentences == 4:
                form = '七言绝句'
                is_regular = True
            elif num_sentences == 8:
                form = '七言律诗'
                is_regular = True
            elif num_sentences > 4:
                form = '七言古诗'
        else:
            form = '杂言'
    
    return {
        'form': form,
        'chars_per_line': int(round(avg_len)),
        'lines': num_sentences,
        'is_regular': is_regular
    }


def classify_from_source(source):
    """根据数据来源判断体裁"""
    if not source:
        return None
    if 'yuanqu' in source or 'qu' in source.lower():
        return '曲'
    if 'ci' in source.lower() and 'tang' not in source.lower():
        return '词'
    return None


def reclassify_all():
    """重新分类所有诗词"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # 获取总数
    cursor.execute("SELECT COUNT(*) FROM poems")
    total = cursor.fetchone()[0]
    log.info(f"诗词总数: {total}")
    
    # 获取所有诗词
    cursor.execute("SELECT id, title, content, source FROM poems")
    poems = cursor.fetchall()
    
    batch_size = 2000
    updated = 0
    stats = {}
    
    for i in range(0, len(poems), batch_size):
        batch = poems[i:i+batch_size]
        
        for poem in batch:
            poem_id = poem['id']
            content = poem['content'] or ''
            source = poem['source'] or ''
            
            # 先检查来源（元曲、宋词）
            source_form = classify_from_source(source)
            
            if source_form == '曲':
                form = '曲'
                chars_per_line = 0
                lines = 0
                is_regular = False
            elif source_form == '词':
                form = '词'
                chars_per_line = 0
                lines = 0
                is_regular = False
            else:
                # 用v3逻辑检测
                result = detect_poem_form_v3(content)
                form = result['form']
                chars_per_line = result['chars_per_line']
                lines = result['lines']
                is_regular = result['is_regular']
            
            # 统计
            stats[form] = stats.get(form, 0) + 1
            
            # 更新数据库
            cursor.execute("""
                UPDATE poems SET 
                    poem_form = ?, 
                    chars_per_line = ?, 
                    line_count = ?, 
                    is_regular = ?
                WHERE id = ?
            """, (form, chars_per_line, lines, 1 if is_regular else 0, poem_id))
        
        conn.commit()
        updated += len(batch)
        log.info(f"已更新: {updated}/{len(poems)} ({updated*100//len(poems)}%)")
    
    # 打印统计
    log.info("\n=== 诗体分布 (v3) ===")
    for form, count in sorted(stats.items(), key=lambda x: -x[1]):
        log.info(f"  {form}: {count} 首")
    
    conn.close()
    log.info("完成!")


if __name__ == "__main__":
    log.info("=== 诗词诗体分类 v3 ===")
    reclassify_all()
