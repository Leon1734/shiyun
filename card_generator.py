#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
精美诗词卡片生成器 v2
- 宣纸质感背景
- 朱砂印章
- 竖排/横排支持
- 装饰边框
"""

import logging
from pathlib import Path
from datetime import datetime

log = logging.getLogger("poetry")


def _load_font(size, style='kai'):
    """加载字体"""
    from PIL import ImageFont
    
    fonts = {
        'kai': ["C:/Windows/Fonts/simkai.ttf", "C:/Windows/Fonts/STKAITI.TTF"],
        'song': ["C:/Windows/Fonts/STZHONGS.TTF", "C:/Windows/Fonts/simsun.ttc"],
        'hei': ["C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf"],
    }
    
    for fp in fonts.get(style, fonts['kai']):
        try:
            return ImageFont.truetype(fp, size)
        except:
            continue
    
    return ImageFont.load_default()


def generate_classic_card(poem, output_path="poem_card.png", 
                          width=800, vertical=False, show_seal=True):
    """
    生成古典风格诗词卡片
    
    Args:
        poem: 诗词dict (title, author, dynasty, content)
        output_path: 输出路径
        width: 卡片宽度
        vertical: 是否竖排
        show_seal: 是否显示印章
    """
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        log.error("Pillow 未安装")
        return None
    
    title = poem.get('title', '')
    author = poem.get('author', '')
    dynasty = poem.get('dynasty', '')
    content = poem.get('content', '')
    if isinstance(content, list):
        content = '\n'.join(content)
    
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    
    # ── 配色 ──
    BG = (247, 243, 232)        # 宣纸底
    INK = (43, 43, 43)          # 墨色
    INK_LIGHT = (107, 99, 85)   # 淡墨
    SEAL = (140, 47, 57)        # 朱砂红
    BORDER = (216, 205, 176)    # 边框色
    
    # ── 布局计算 ──
    if vertical:
        # 竖排：从右往左
        line_height = 52
        char_size = 38
        font = _load_font(char_size, 'kai')
        title_font = _load_font(46, 'song')
        info_font = _load_font(22, 'kai')
        
        n_cols = len(lines)
        height = max(600, 160 + n_cols * line_height + 100)
        img = Image.new('RGB', (width, height), BG)
        draw = ImageDraw.Draw(img)
        
        # 边框
        draw.rectangle([20, 20, width-20, height-20], outline=BORDER, width=2)
        draw.rectangle([28, 28, width-28, height-28], outline=BORDER, width=1)
        
        # 标题（竖排）
        title_x = width - 100
        for i, char in enumerate(title):
            draw.text((title_x, 60 + i * 50), char, font=title_font, fill=INK)
        
        # 正文（竖排，从右到左）
        start_x = width - 170
        for col_idx, line in enumerate(lines):
            x = start_x - col_idx * line_height
            for char_idx, char in enumerate(line):
                y = 90 + char_idx * (char_size + 8)
                draw.text((x, y), char, font=font, fill=INK)
        
        # 落款
        info = f"{dynasty}·{author}"
        draw.text((60, height - 70), info, font=info_font, fill=INK_LIGHT)
    
    else:
        # 横排（默认）
        font = _load_font(36, 'kai')
        title_font = _load_font(50, 'song')
        info_font = _load_font(24, 'kai')
        small_font = _load_font(18, 'kai')
        
        # 动态高度
        height = max(600, 240 + len(lines) * 58 + 120)
        img = Image.new('RGB', (width, height), BG)
        draw = ImageDraw.Draw(img)
        
        # 双线边框
        draw.rectangle([20, 20, width-20, height-20], outline=BORDER, width=2)
        draw.rectangle([28, 28, width-28, height-28], outline=BORDER, width=1)
        
        # 四角装饰
        corner_len = 24
        for cx, cy in [(36, 36), (width-36, 36), (36, height-36), (width-36, height-36)]:
            draw.ellipse([cx-4, cy-4, cx+4, cy+4], fill=SEAL)
        
        # 标题（居中）
        bbox = draw.textbbox((0, 0), title, font=title_font)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) / 2, 70), title, font=title_font, fill=INK)
        
        # 标题下方装饰线
        draw.line([(width//2 - 60, 140), (width//2 + 60, 140)], fill=SEAL, width=2)
        
        # 作者
        info = f"{dynasty} · {author}"
        bbox = draw.textbbox((0, 0), info, font=info_font)
        tw = bbox[2] - bbox[0]
        draw.text(((width - tw) / 2, 155), info, font=info_font, fill=INK_LIGHT)
        
        # 正文（居中）
        y = 230
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            tw = bbox[2] - bbox[0]
            draw.text(((width - tw) / 2, y), line, font=font, fill=INK)
            y += 58
        
        # 底部
        footer = "古诗词桌面小工具 · 诗韵"
        draw.text((60, height - 60), footer, font=small_font, fill=INK_LIGHT)
        date_str = datetime.now().strftime('%Y-%m-%d')
        bbox = draw.textbbox((0, 0), date_str, font=small_font)
        tw = bbox[2] - bbox[0]
        draw.text((width - 60 - tw, height - 60), date_str, font=small_font, fill=INK_LIGHT)
    
    # ── 印章 ──
    if show_seal:
        seal_size = 70
        seal_img = Image.new('RGBA', (seal_size, seal_size), (0, 0, 0, 0))
        seal_draw = ImageDraw.Draw(seal_img)
        seal_draw.rounded_rectangle([2, 2, seal_size-2, seal_size-2], 
                                     radius=6, fill=SEAL)
        
        # 印章文字（作者名字最后一字或"诗"字）
        seal_char = author[-1] if author and author != '佚名' else '诗'
        seal_font = _load_font(40, 'kai')
        bbox = seal_draw.textbbox((0, 0), seal_char, font=seal_font)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        seal_draw.text(((seal_size-tw)/2 - bbox[0], (seal_size-th)/2 - bbox[1]), 
                       seal_char, font=seal_font, fill=(255, 248, 240))
        
        # 贴到右下角
        img.paste(seal_img, (width - 110, height - 130), seal_img)
    
    img.save(output_path)
    return output_path


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_poem = {
        'title': '静夜思',
        'author': '李白',
        'dynasty': '唐',
        'content': '床前明月光，疑是地上霜。\n举头望明月，低头思故乡。'
    }
    
    print("=== 卡片生成测试 ===")
    p1 = generate_classic_card(test_poem, 'test_card_h.png')
    print(f"横排卡片: {p1}")
    p2 = generate_classic_card(test_poem, 'test_card_v.png', vertical=True)
    print(f"竖排卡片: {p2}")
