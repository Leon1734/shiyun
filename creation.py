#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创作辅助模块
功能：押韵检查、对仗检查、格律检查、创作模板
"""

import json
import re
from pathlib import Path
from collections import defaultdict
import logging

log = logging.getLogger("poetry")

# 韵书数据路径
# 路径：优先 data 目录（与 exe 共享；打包后 _internal 只读）
try:
    from app_paths import get_data_dir as _get_data_dir
    RHYME_DB_PATH = _get_data_dir() / "rhyme.json"
except Exception:
    RHYME_DB_PATH = Path(__file__).parent / "data" / "rhyme.json"


class CreationManager:
    """创作辅助管理器"""
    
    def __init__(self, db):
        self.db = db
        self.rhyme_dict = {}
        self.tone_dict = {}
        self._load_rhyme_data()
        self._build_tone_dict()
    
    def _load_rhyme_data(self):
        """加载韵书数据"""
        try:
            if RHYME_DB_PATH.exists():
                with open(RHYME_DB_PATH, encoding='utf-8') as f:
                    self.rhyme_dict = json.load(f)
                log.info(f"加载韵书数据: {len(self.rhyme_dict)} 个韵部")
            else:
                # 使用简化的韵书数据
                self._create_default_rhyme()
                log.info("使用默认韵书数据")
        except Exception as e:
            log.error(f"加载韵书数据失败: {e}")
            self._create_default_rhyme()
    
    def _create_default_rhyme(self):
        """创建默认韵书数据"""
        # 平水韵简化版（常用韵部）
        self.rhyme_dict = {
            '东': ['东', '同', '中', '虫', '冲', '终', '崇', '嵩', '戎', '宫'],
            '冬': ['冬', '农', '宗', '钟', '龙', '松', '丰', '峰', '锋', '烽'],
            '江': ['江', '窗', '邦', '缸', '降', '双', '庞', '腔', '撞', '桩'],
            '支': ['支', '枝', '移', '为', '垂', '吹', '陂', '碑', '奇', '宜'],
            '微': ['微', '薇', '晖', '辉', '徽', '挥', '韦', '围', '帏', '违'],
            '鱼': ['鱼', '渔', '初', '书', '舒', '居', '裾', '车', '渠', '蕖'],
            '虞': ['虞', '愚', '娱', '隅', '无', '芜', '巫', '于', '盂', '萸'],
            '齐': ['齐', '黎', '犁', '梨', '妻', '萋', '凄', '堤', '低', '题'],
            '佳': ['佳', '街', '鞋', '牌', '柴', '钗', '差', '崖', '涯', '阶'],
            '灰': ['灰', '恢', '魁', '隈', '回', '徊', '槐', '枚', '梅', '媒'],
            '真': ['真', '因', '茵', '新', '晨', '辰', '臣', '人', '仁', '神'],
            '文': ['文', '闻', '纹', '蚊', '云', '氛', '分', '纷', '芬', '焚'],
            '元': ['元', '原', '源', '园', '猿', '垣', '烦', '繁', '蕃', '樊'],
            '寒': ['寒', '韩', '丹', '安', '鞍', '难', '滩', '弹', '残', '干'],
            '删': ['删', '潸', '关', '弯', '湾', '还', '环', '鬟', '斑', '班'],
            '先': ['先', '前', '千', '阡', '笺', '天', '坚', '贤', '弦', '弦'],
            '萧': ['萧', '箫', '刁', '貂', '凋', '凋', '雕', '迢', '条', '调'],
            '肴': ['肴', '巢', '交', '郊', '茅', '嘲', '钞', '包', '胶', '爻'],
            '豪': ['豪', '毫', '操', '条', '刀', '萄', '桃', '糟', '漕', '旄'],
            '歌': ['歌', '多', '罗', '河', '戈', '阿', '和', '波', '科', '柯'],
            '麻': ['麻', '花', '霞', '家', '茶', '华', '沙', '车', '牙', '蛇'],
            '阳': ['阳', '杨', '扬', '香', '乡', '光', '昌', '堂', '张', '王'],
            '庚': ['庚', '更', '行', '衡', '横', '彭', '亨', '英', '明', '平'],
            '青': ['青', '经', '星', '腥', '醒', '形', '刑', '型', '灵', '铃'],
            '蒸': ['蒸', '承', '丞', '惩', '陵', '凌', '冰', '膺', '鹰', '应'],
            '尤': ['尤', '邮', '优', '忧', '流', '留', '游', '牛', '酬', '修'],
            '侵': ['侵', '寻', '浔', '林', '霖', '针', '深', '沉', '心', '琴'],
            '覃': ['覃', '潭', '参', '南', '男', '谙', '庵', '含', '涵', '函'],
            '盐': ['盐', '檐', '廉', '帘', '嫌', '严', '占', '髯', '拈', '淹'],
            '咸': ['咸', '缄', '谗', '衔', '岩', '帆', '衫', '杉', '监', '凡'],
        }
        
        # 保存到文件
        try:
            with open(RHYME_DB_PATH, 'w', encoding='utf-8') as f:
                json.dump(self.rhyme_dict, f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"保存韵书数据失败: {e}")
    
    def _build_tone_dict(self):
        """构建平仄字典"""
        # 简化的平仄数据（常用字）
        # 平声：阴平、阳平
        # 仄声：上声、去声、入声
        self.tone_dict = {
            # 平声字（简化）
            '东': '平', '同': '平', '中': '平', '虫': '平', '冲': '平',
            '江': '平', '窗': '平', '邦': '平', '双': '平', '庞': '平',
            '支': '平', '枝': '平', '移': '平', '为': '平', '垂': '平',
            '微': '平', '薇': '平', '晖': '平', '辉': '平', '徽': '平',
            '鱼': '平', '渔': '平', '初': '平', '书': '平', '舒': '平',
            '虞': '平', '愚': '平', '娱': '平', '隅': '平', '无': '平',
            '齐': '平', '黎': '平', '犁': '平', '梨': '平', '妻': '平',
            '佳': '平', '街': '平', '鞋': '平', '牌': '平', '柴': '平',
            '灰': '平', '恢': '平', '魁': '平', '隈': '平', '回': '平',
            '真': '平', '因': '平', '茵': '平', '新': '平', '晨': '平',
            '文': '平', '闻': '平', '纹': '平', '蚊': '平', '云': '平',
            '元': '平', '原': '平', '源': '平', '园': '平', '猿': '平',
            '寒': '平', '韩': '平', '丹': '平', '安': '平', '鞍': '平',
            '删': '平', '潸': '平', '关': '平', '弯': '平', '湾': '平',
            '先': '平', '前': '平', '千': '平', '阡': '平', '笺': '平',
            '萧': '平', '箫': '平', '刁': '平', '貂': '平', '凋': '平',
            '肴': '平', '巢': '平', '交': '平', '郊': '平', '茅': '平',
            '豪': '平', '毫': '平', '操': '平', '条': '平', '刀': '平',
            '歌': '平', '多': '平', '罗': '平', '河': '平', '戈': '平',
            '麻': '平', '花': '平', '霞': '平', '家': '平', '茶': '平',
            '阳': '平', '杨': '平', '扬': '平', '香': '平', '乡': '平',
            '庚': '平', '更': '平', '行': '平', '衡': '平', '横': '平',
            '青': '平', '经': '平', '星': '平', '腥': '平', '醒': '平',
            '蒸': '平', '承': '平', '丞': '平', '惩': '平', '陵': '平',
            '尤': '平', '邮': '平', '优': '平', '忧': '平', '流': '平',
            '侵': '平', '寻': '平', '浔': '平', '林': '平', '霖': '平',
            '覃': '平', '潭': '平', '参': '平', '南': '平', '男': '平',
            '盐': '平', '檐': '平', '廉': '平', '帘': '平', '嫌': '平',
            '咸': '平', '缄': '平', '谗': '平', '衔': '平', '岩': '平',
            
            # 仄声字（简化）
            '上': '仄', '去': '仄', '入': '仄', '声': '仄', '调': '仄',
            '大': '仄', '小': '仄', '多': '仄', '少': '仄', '好': '仄',
            '坏': '仄', '美': '仄', '丑': '仄', '新': '仄', '旧': '仄',
            '长': '仄', '短': '仄', '高': '仄', '低': '仄', '远': '仄',
            '近': '仄', '深': '仄', '浅': '仄', '宽': '仄', '窄': '仄',
            '快': '仄', '慢': '仄', '强': '仄', '弱': '仄', '硬': '仄',
            '软': '仄', '冷': '仄', '热': '仄', '干': '仄', '湿': '仄',
            '明': '仄', '暗': '仄', '亮': '仄', '黑': '仄', '白': '仄',
            '红': '仄', '绿': '仄', '蓝': '仄', '黄': '仄', '紫': '仄',
        }
    
    def check_rhyme(self, line1, line2):
        """检查两行是否押韵"""
        if not line1 or not line2:
            return False, "诗句不完整"
        
        char1 = line1[-1]
        char2 = line2[-1]
        
        # 查找韵部
        rhyme1 = None
        rhyme2 = None
        
        for rhyme, chars in self.rhyme_dict.items():
            if char1 in chars:
                rhyme1 = rhyme
            if char2 in chars:
                rhyme2 = rhyme
        
        if rhyme1 and rhyme2:
            if rhyme1 == rhyme2:
                return True, f"押韵：{rhyme1}韵"
            else:
                return False, f"不押韵：{rhyme1}韵 vs {rhyme2}韵"
        else:
            return False, "无法判断韵部"
    
    def check_tone(self, line):
        """检查平仄"""
        if not line:
            return "", "诗句不完整"
        
        tones = []
        for char in line:
            if '\u4e00' <= char <= '\u9fff':
                tone = self.tone_dict.get(char, '未知')
                tones.append(tone)
            else:
                tones.append(' ')
        
        return ''.join(tones), "平仄检查完成"
    
    def check_duizhang(self, line1, line2):
        """检查对仗"""
        if not line1 or not line2:
            return False, "诗句不完整"
        
        # 简化对仗检查：字数相同、词性相对
        if len(line1) != len(line2):
            return False, "字数不同，无法对仗"
        
        # 检查平仄相对
        tone1, _ = self.check_tone(line1)
        tone2, _ = self.check_tone(line2)
        
        # 简化检查：平仄相对
        opposite_count = 0
        for t1, t2 in zip(tone1, tone2):
            if t1 == '平' and t2 == '仄':
                opposite_count += 1
            elif t1 == '仄' and t2 == '平':
                opposite_count += 1
        
        if opposite_count >= len(line1) * 0.6:
            return True, f"对仗工整（{opposite_count}/{len(line1)}字平仄相对）"
        else:
            return False, f"对仗不够工整（{opposite_count}/{len(line1)}字平仄相对）"
    
    def get_rhyme_words(self, char):
        """获取同韵字"""
        for rhyme, chars in self.rhyme_dict.items():
            if char in chars:
                return chars
        return []
    
    def get_creation_templates(self):
        """获取创作模板"""
        templates = [
            {
                'name': '五言绝句',
                'format': '首句：___，___。\n次句：___，___。',
                'description': '四句，每句五字，共20字',
                'example': '床前明月光，疑是地上霜。\n举头望明月，低头思故乡。'
            },
            {
                'name': '七言绝句',
                'format': '首句：___，___。\n次句：___，___。\n三句：___，___。\n末句：___，___。',
                'description': '四句，每句七字，共28字',
                'example': '朝辞白帝彩云间，千里江陵一日还。\n两岸猿声啼不住，轻舟已过万重山。'
            },
            {
                'name': '五言律诗',
                'format': '首联：___，___。\n颔联：___，___。\n颈联：___，___。\n尾联：___，___。',
                'description': '八句，每句五字，共40字',
                'example': '国破山河在，城春草木深。\n感时花溅泪，恨别鸟惊心。\n烽火连三月，家书抵万金。\n白头搔更短，浑欲不胜簪。'
            },
            {
                'name': '七言律诗',
                'format': '首联：___，___。\n颔联：___，___。\n颈联：___，___。\n尾联：___，___。',
                'description': '八句，每句七字，共56字',
                'example': '风急天高猿啸哀，渚清沙白鸟飞回。\n无边落木萧萧下，不尽长江滚滚来。\n万里悲秋常作客，百年多病独登台。\n艰难苦恨繁霜鬓，潦倒新停浊酒杯。'
            },
            {
                'name': '词牌·如梦令',
                'format': '___，___。\n___，___。\n___，___，\n___。',
                'description': '三十三字，仄韵',
                'example': '昨夜雨疏风骤，浓睡不消残酒。\n试问卷帘人，却道海棠依旧。\n知否，知否，应是绿肥红瘦。'
            },
            {
                'name': '词牌·水调歌头',
                'format': '___，___。\n___，___，___。\n___，___，___。\n___，___，___。\n___，___，___。\n___，___，___。\n___，___，___。',
                'description': '九十五字，平韵',
                'example': '明月几时有？把酒问青天。\n不知天上宫阙，今夕是何年。\n我欲乘风归去，又恐琼楼玉宇，高处不胜寒。\n起舞弄清影，何似在人间。\n转朱阁，低绮户，照无眠。\n不应有恨，何事长向别时圆？\n人有悲欢离合，月有阴晴圆缺，此事古难全。\n但愿人长久，千里共婵娟。'
            }
        ]
        return templates
    
    def analyze_poem(self, poem):
        """分析诗词的格律"""
        content = poem.get('content', '')
        if isinstance(content, list):
            content = '\n'.join(content)
        
        lines = content.split('\n')
        analysis = {
            'title': poem.get('title', ''),
            'author': poem.get('author', ''),
            'lines': [],
            'rhyme_scheme': '',
            'tone_pattern': ''
        }
        
        for i, line in enumerate(lines):
            if line.strip():
                # 检查平仄
                tone_pattern, _ = self.check_tone(line)
                
                # 检查押韵（与下一句）
                rhyme_info = ""
                if i + 1 < len(lines) and lines[i + 1].strip():
                    is_rhyme, rhyme_msg = self.check_rhyme(line, lines[i + 1])
                    rhyme_info = rhyme_msg
                
                analysis['lines'].append({
                    'line': line,
                    'tone': tone_pattern,
                    'rhyme': rhyme_info
                })
        
        return analysis
    
    def close(self):
        """关闭"""
        pass
