#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
补录「名篇精选」：教材家喻户晓名篇（缺失的 + 通行版本）
"""
import sqlite3
from pathlib import Path

DB = Path(__file__).parent / "data" / "poetry.db"

# (标题, 作者, 朝代, 内容, 题材, 诗体, 每句字数)
CURATED = [
    # ── 缺失的教材名篇 ──
    ("敕勒歌", "佚名", "南北朝",
     "敕勒川，阴山下。\n天似穹庐，笼盖四野。\n天苍苍，野茫茫，\n风吹草低见牛羊。",
     "山水田园", "杂言", 0),
    ("村居", "高鼎", "清",
     "草长莺飞二月天，拂堤杨柳醉春烟。\n儿童散学归来早，忙趁东风放纸鸢。",
     "山水田园", "七言绝句", 7),
    ("所见", "袁枚", "清",
     "牧童骑黄牛，歌声振林樾。\n意欲捕鸣蝉，忽然闭口立。",
     "山水田园", "五言绝句", 5),
    ("竹石", "郑燮", "清",
     "咬定青山不放松，立根原在破岩中。\n千磨万击还坚劲，任尔东西南北风。",
     "咏物言志", "七言绝句", 7),
    ("石灰吟", "于谦", "明",
     "千锤万凿出深山，烈火焚烧若等闲。\n粉骨碎身浑不怕，要留清白在人间。",
     "咏物言志", "七言绝句", 7),
    ("墨梅", "王冕", "元",
     "我家洗砚池头树，朵朵花开淡墨痕。\n不要人夸好颜色，只留清气满乾坤。",
     "咏物言志", "七言绝句", 7),
    ("画", "佚名", "唐",
     "远看山有色，近听水无声。\n春去花还在，人来鸟不惊。",
     "山水田园", "五言绝句", 5),
    ("书湖阴先生壁", "王安石", "宋",
     "茅檐长扫净无苔，花木成畦手自栽。\n一水护田将绿绕，两山排闼送青来。",
     "山水田园", "七言绝句", 7),
    ("稚子弄冰", "杨万里", "宋",
     "稚子金盆脱晓冰，彩丝穿取当银钲。\n敲成玉磬穿林响，忽作玻璃碎地声。",
     "山水田园", "七言绝句", 7),
    ("题秋江独钓图", "王士祯", "清",
     "一蓑一笠一扁舟，一丈丝纶一寸钩。\n一曲高歌一樽酒，一人独钓一江秋。",
     "山水田园", "七言绝句", 7),
    ("苔", "袁枚", "清",
     "白日不到处，青春恰自来。\n苔花如米小，也学牡丹开。",
     "咏物言志", "五言绝句", 5),
    ("画鸡", "唐寅", "明",
     "头上红冠不用裁，满身雪白走将来。\n平生不敢轻言语，一叫千门万户开。",
     "咏物言志", "七言绝句", 7),
    ("舟夜书所见", "查慎行", "清",
     "月黑见渔灯，孤光一点萤。\n微微风簇浪，散作满河星。",
     "山水田园", "五言绝句", 5),
    # ── 通行版本（全唐诗文本与此处流传版本不同）──
    ("静夜思", "李白", "唐",
     "床前明月光，疑是地上霜。\n举头望明月，低头思故乡。\n\n（注：本首为家喻户晓的通行版本；《全唐诗》古本作“床前看月光……举头望山月”）",
     "送别怀人", "五言绝句", 5),
    ("泊船瓜洲", "王安石", "宋",
     "京口瓜洲一水间，钟山只隔数重山。\n春风又绿江南岸，明月何时照我还。\n\n（注：本首为通行版本；古本作“春风自绿江南岸”）",
     "送别怀人", "七言绝句", 7),
    ("夏日绝句", "李清照", "宋",
     "生当作人杰，死亦为鬼雄。\n至今思项羽，不肯过江东。\n\n（注：本首为通行版本；古本作“生当为人杰，死亦作鬼雄”）",
     "咏史怀古", "五言绝句", 5),
    ("马诗·其五", "李贺", "唐",
     "大漠沙如雪，燕山月似钩。\n何当金络脑，快走踏清秋。\n\n（注：本首为通行版本；《全唐诗》古本作“大漠山如雪”）",
     "咏物言志", "五言绝句", 5),
]

conn = sqlite3.connect(str(DB))
c = conn.cursor()

# 检查是否已存在
c.execute("SELECT COUNT(*) FROM poems WHERE collection='名篇精选'")
if c.fetchone()[0] > 0:
    print("名篇精选已存在，先删除旧数据")
    c.execute("DELETE FROM poems WHERE collection='名篇精选'")

count = 0
for title, author, dynasty, content, theme, form, chars in CURATED:
    word_count = len(content.replace('\n', ''))
    line_count = content.count('\n') + 1
    c.execute('''
        INSERT INTO poems (title, author, dynasty, content, source, theme, poem_form,
                           chars_per_line, line_count, word_count, collection)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (title, author, dynasty, content, '名篇精选', theme, form, chars, line_count, word_count, '名篇精选'))
    count += 1

conn.commit()

# 验证
print(f"补录完成: {count} 首")
c.execute("SELECT id, title, author FROM poems WHERE collection='名篇精选' ORDER BY id")
for r in c.fetchall():
    print(f"  [{r[0]}] 《{r[1]}》{r[2]}")

# 重建FTS
conn.execute("INSERT INTO poems_fts(poems_fts) VALUES('rebuild')")
conn.commit()
print("FTS已重建")

conn.close()
