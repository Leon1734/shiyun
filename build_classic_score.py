#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
经典度评分系统：给每首诗打分（选本收录 + 名句原诗 + 著名诗人）
用法: python build_classic_score.py
"""
import sqlite3
import re
from pathlib import Path

DB = Path(__file__).parent / "data" / "poetry.db"

# ── 选本加分 ──
COLLECTION_WEIGHTS = {
    '名篇精选': 100,
    '唐诗三百首': 95,
    '宋词三百首': 95,
    '千家诗': 90,
    '中学古诗': 90,
    '诗经': 65,
    '楚辞': 65,
    '纳兰性德': 60,
    '南唐二主词': 60,
    '曹操诗集': 60,
    '花间集': 55,
}

# ── 名句原诗加分 ──
QUOTE_WEIGHT = 70

# ── 著名诗人（国民级 +60）──
MEGA_AUTHORS = [
    '李白', '杜甫', '苏轼', '辛弃疾', '李清照', '白居易', '王维', '李商隐', '杜牧',
    '陆游', '王安石', '孟浩然', '王昌龄', '柳永', '纳兰性德', '李煜', '陶渊明',
    '屈原', '曹操',
]

# ── 著名诗人（著名 +40）──
STAR_AUTHORS = [
    '韩愈', '柳宗元', '刘禹锡', '岑参', '高适', '王之涣', '王勃', '骆宾王', '陈子昂',
    '张若虚', '贺知章', '韦应物', '李贺', '温庭筠', '元稹', '李绅', '崔颢', '张继',
    '孟郊', '贾岛', '刘长卿', '张九龄', '王翰', '杜秋娘', '欧阳修', '范仲淹', '晏殊',
    '晏几道', '秦观', '周邦彦', '贺铸', '岳飞', '文天祥', '杨万里', '范成大', '朱熹',
    '梅尧臣', '黄庭坚', '张孝祥', '叶绍翁', '林升', '朱淑真', '李之仪', '苏辙',
    '曹植', '曹丕', '阮籍', '嵇康', '左思', '谢灵运', '谢朓', '鲍照', '庾信',
    '李璟', '韦庄', '冯延巳', '马致远', '关汉卿', '张养浩', '白朴', '乔吉', '张可久',
    '睢景臣', '王冕', '于谦', '唐寅', '郑燮', '龚自珍', '高鼎', '袁枚', '查慎行',
    '赵翼', '刘邦', '项羽', '荆轲', '卓文君', '杜荀鹤', '毛泽东',
]


def norm(s):
    """去除非汉字字符"""
    return re.sub(r'[^\u4e00-\u9fff]', '', s or '')


def main():
    conn = sqlite3.connect(str(DB))
    c = conn.cursor()

    # 1. 加列
    c.execute("PRAGMA table_info(poems)")
    cols = [r[1] for r in c.fetchall()]
    if 'classic_score' not in cols:
        c.execute("ALTER TABLE poems ADD COLUMN classic_score INTEGER DEFAULT 0")
        print("已添加 classic_score 列")
    else:
        print("classic_score 列已存在，重新计算")

    # 2. 收集选本的规范化内容
    collection_keys = {}  # norm_content -> weight
    for coll, w in COLLECTION_WEIGHTS.items():
        c.execute("SELECT content FROM poems WHERE collection=?", (coll,))
        n = 0
        for (content,) in c.fetchall():
            key = norm(content)
            if key:
                collection_keys[key] = max(collection_keys.get(key, 0), w)
                n += 1
        print(f"  {coll}: {n}首 → 采集键")

    # 3. 收集名句匹配串（前10字）
    c.execute("SELECT text FROM quotes")
    needles = []
    for (text,) in c.fetchall():
        nt = norm(text)[:10]
        if len(nt) >= 4:
            needles.append(nt)
    print(f"  名句匹配串: {len(needles)}条")

    # 4. 全库扫描打分
    print("全库扫描打分中...")
    c.execute("SELECT id, title, content, author FROM poems")
    updates = []
    for pid, title, content, author in c.fetchall():
        score = 0
        key = norm(content)
        # a. 选本匹配
        if key in collection_keys:
            score += collection_keys[key]
        # b. 名句匹配（叠加）
        for needle in needles:
            if needle in key:
                score += QUOTE_WEIGHT
                break
        # c. 诗人
        if author in MEGA_AUTHORS:
            score += 60
        elif author in STAR_AUTHORS:
            score += 40
        if score:
            updates.append((score, pid))

    print(f"  打分条目: {len(updates)}")
    c.executemany("UPDATE poems SET classic_score=? WHERE id=?", updates)
    conn.commit()

    # 5. 建索引
    c.execute("CREATE INDEX IF NOT EXISTS idx_classic ON poems(classic_score)")
    conn.commit()

    # 6. 统计
    c.execute("SELECT COUNT(*) FROM poems WHERE classic_score >= 90")
    print(f"  经典度>=90: {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM poems WHERE classic_score >= 60")
    print(f"  经典度>=60: {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM poems WHERE classic_score > 0")
    print(f"  经典度>0: {c.fetchone()[0]}")
    c.execute("SELECT COUNT(*) FROM poems")
    print(f"  全库: {c.fetchone()[0]}")

    # 7. 预览高分诗
    print()
    print("=== 高分诗词预览（前20）===")
    c.execute("SELECT title, author, classic_score FROM poems ORDER BY classic_score DESC, id LIMIT 20")
    for r in c.fetchall():
        print(f"  [{r[2]}分] 《{r[0]}》{r[1]}")

    conn.close()


if __name__ == '__main__':
    main()
