#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
v7.0 功能模块
1. TTS 朗读（edge-tts 高音质 + Windows SAPI 离线回退）
2. 拼音标注（pypinyin）
3. 每日推荐（诗词 + 古文）
"""

import os
import sys
import time
import ctypes
import hashlib
import logging
import threading
import tempfile
import sqlite3
from pathlib import Path
from datetime import date, datetime

log = logging.getLogger("poetry")

# 依赖检查
try:
    import edge_tts
    import asyncio
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

try:
    import win32com.client
    HAS_SAPI = True
except ImportError:
    HAS_SAPI = False

try:
    from pypinyin import pinyin, Style
    HAS_PYPINYIN = True
except ImportError:
    HAS_PYPINYIN = False


# ── TTS 引擎 ──────────────────────────────────────────────────────────────

class TTSEngine:
    """TTS 朗读引擎
    
    优先级: edge-tts（高音质）→ Windows SAPI（离线）
    播放: Windows MCI（异步）
    """
    
    VOICES = {
        '晓晓(女声)': 'zh-CN-XiaoxiaoNeural',
        '云希(男声)': 'zh-CN-YunxiNeural',
        '云健(男声)': 'zh-CN-YunjianNeural',
        '晓伊(女声)': 'zh-CN-XiaoyiNeural',
        '云扬(男声)': 'zh-CN-YunyangNeural',
    }
    
    def __init__(self):
        self._playing = False
        self._thread = None
        self._temp_files = []
        self._sapi = None
        self.voice = 'zh-CN-XiaoxiaoNeural'
        self.rate = '+0%'
        self._mci_winmm = ctypes.windll.winmm if sys.platform == 'win32' else None
        self._alias_counter = 0
    
    @property
    def is_playing(self):
        return self._playing
    
    def speak_async(self, text, on_done=None, on_error=None):
        """异步朗读"""
        if self._playing:
            self.stop()
        
        def _worker():
            try:
                self._playing = True
                if HAS_EDGE_TTS:
                    ok = self._speak_edge(text)
                elif HAS_SAPI:
                    ok = self._speak_sapi(text)
                else:
                    ok = False
                    log.warning("无可用的TTS引擎")
                
                if on_done:
                    on_done(ok)
            except Exception as e:
                log.error(f"TTS失败: {e}")
                if on_error:
                    on_error(str(e))
            finally:
                self._playing = False
        
        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()
    
    def _speak_edge(self, text):
        """edge-tts 高音质朗读"""
        try:
            # 生成音频到临时文件
            tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False,
                                              dir=tempfile.gettempdir())
            tmp.close()
            
            async def gen():
                communicate = edge_tts.Communicate(text, self.voice, rate=self.rate)
                await communicate.save(tmp.name)
            
            asyncio.run(gen())
            
            if not os.path.exists(tmp.name) or os.path.getsize(tmp.name) < 100:
                return self._speak_sapi(text)  # 回退
            
            # MCI 播放
            self._play_mci(tmp.name)
            self._temp_files.append(tmp.name)
            return True
        except Exception as e:
            log.warning(f"edge-tts 失败，回退 SAPI: {e}")
            return self._speak_sapi(text)
    
    def _play_mci(self, mp3_path):
        """用 Windows MCI 播放 mp3（异步）"""
        if not self._mci_winmm:
            return False
        
        self._alias_counter += 1
        alias = f'poetry_tts_{self._alias_counter}'
        
        path = os.path.abspath(mp3_path).replace('\\', '/')
        self._mci_winmm.mciSendStringW(f'open "{path}" type mpegvideo alias {alias}', None, 0, None)
        self._mci_winmm.mciSendStringW(f'play {alias} wait', None, 0, None)
        self._mci_winmm.mciSendStringW(f'close {alias}', None, 0, None)
        return True
    
    def _speak_sapi(self, text):
        """Windows SAPI 离线朗读"""
        if not HAS_SAPI:
            return False
        try:
            if self._sapi is None:
                self._sapi = win32com.client.Dispatch("SAPI.SpVoice")
                # 选中文语音
                voices = self._sapi.GetVoices()
                for i in range(voices.Count):
                    v = voices.Item(i)
                    if 'Chinese' in v.GetDescription():
                        self._sapi.Voice = v
                        break
            self._sapi.Speak(text)
            return True
        except Exception as e:
            log.error(f"SAPI失败: {e}")
            return False
    
    def stop(self):
        """停止播放"""
        try:
            if self._sapi:
                self._sapi.Speak("", 3)  # SVSFPurgeBeforeSpeak
        except:
            pass
        self._playing = False
    
    def cleanup(self):
        """清理临时文件"""
        for f in self._temp_files:
            try:
                if os.path.exists(f):
                    os.remove(f)
            except:
                pass
        self._temp_files.clear()


# ── 拼音工具 ──────────────────────────────────────────────────────────────

def get_pinyin_line(line):
    """获取一行文字的拼音（空格分隔）"""
    if not HAS_PYPINYIN:
        return ''
    
    result = []
    for char in line:
        if '\u4e00' <= char <= '\u9fff':
            py = pinyin(char, style=Style.TONE)
            result.append(py[0][0] if py else char)
        elif char in '，。！？、；：""''（）《》·—':
            result.append(char)
        elif char.strip():
            result.append(char)
    
    return ' '.join(result)


def get_pinyin_text(text):
    """获取全文拼音（每行: 拼音行 + 原行）"""
    if not HAS_PYPINYIN:
        return text
    
    lines = text.split('\n')
    result = []
    for line in lines:
        if not line.strip():
            result.append('')
            continue
        py = get_pinyin_line(line)
        result.append(py)
        result.append(line)
    return '\n'.join(result)


def build_pinyin_display(text):
    """构建拼音对照显示（拼音在上，汉字在下，对齐）"""
    if not HAS_PYPINYIN:
        return text, text
    
    lines = text.split('\n')
    py_lines = []
    for line in lines:
        if not line.strip():
            py_lines.append('')
            continue
        # 逐字拼音
        chars = []
        for char in line:
            if '\u4e00' <= char <= '\u9fff':
                py = pinyin(char, style=Style.TONE)
                chars.append(py[0][0] if py else char)
            else:
                chars.append(char)
        # 用空格对齐
        py_lines.append(' '.join(chars))
    
    return '\n'.join(py_lines), text


# ── 每日推荐 ──────────────────────────────────────────────────────────────

class DailyRecommender:
    """每日推荐（基于日期的确定性选择）"""
    
    # 名篇优先池（唐诗三百首 + 宋词精选 + 五代 + 清词）
    FAMOUS_TITLES = [
        '静夜思', '春晓', '登鹳雀楼', '相思', '悯农', '江雪', '寻隐者不遇',
        '鹿柴', '竹里馆', '送别', '杂诗', '登乐游原', '怨情', '八阵图',
        '问刘十九', '池上', '微雨', '春思', '秋浦歌', '独坐敬亭山',
        '望庐山瀑布', '早发白帝城', '黄鹤楼送孟浩然之广陵', '赠汪伦',
        '望天门山', '闻王昌龄左迁龙标遥有此寄', '春夜洛城闻笛',
        '绝句', '江畔独步寻花', '江南逢李龟年', '赠花卿', '春望',
        '月夜', '春夜喜雨', '旅夜书怀', '登岳阳楼', '蜀相', '客至',
        '水调歌头·明月几时有', '念奴娇·大江东去', '江城子·乙卯正月二十日夜记梦',
        '定风波·莫听穿林打叶声', '蝶恋花·春景', '卜算子·黄州定慧院寓居作',
        '声声慢·寻寻觅觅', '如梦令·常记溪亭日暮', '一剪梅·红藕香残玉簟秋',
        '醉花阴·薄雾浓云愁永昼', '武陵春·春晚', '渔家傲·天接云涛连晓雾',
        '满江红·怒发冲冠', '青玉案·元夕', '破阵子·为陈同甫赋壮词以寄之',
        '永遇乐·京口北固亭怀古', '丑奴儿·书博山道中壁', '西江月·夜行黄沙道中',
        '雨霖铃·寒蝉凄切', '望海潮·东南形胜', '蝶恋花·伫倚危楼风细细',
        '鹊桥仙·纤云弄巧', '浣溪沙·一曲新词酒一杯', '蝶恋花·槛菊愁烟兰泣露',
        '虞美人·春花秋月何时了', '相见欢·无言独上西楼', '浪淘沙令·帘外雨潺潺',
        '苏幕遮·怀旧', '渔家傲·秋思', '天净沙·秋思', '山坡羊·潼关怀古',
        # 五代·南唐二主
        '虞美人·春花秋月何时了', '相见欢·无言独上西楼', '浪淘沙令·帘外雨潺潺',
        '相见欢·林花谢了春红', '破阵子·四十年来家国',
        # 清·纳兰性德
        '木兰花令·拟古决绝词', '长相思·山一程', '浣溪沙·谁念西风独自凉',
        '画堂春·一生一代一双人', '采桑子·明月多情应笑我',
        # 汉·曹操
        '观沧海', '短歌行', '龟虽寿',
        # 五代·花间集
        '菩萨蛮·小山重叠金明灭', '更漏子·玉炉香', '梦江南·千万恨',
    ]
    
    def __init__(self, db_path):
        self.db_path = Path(db_path)
        self._conn = None
    
    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    # 同名诗的作者偏好（避免匹配到宋诗中同名的诗）
    PREFERRED_AUTHORS = {
        '悯农': '李绅', '怨情': '李白', '绝句': '杜甫', '送别': '王维',
        '杂诗': '王维', '春思': '李白', '池上': '白居易', '微雨': '李商隐',
        '静夜思': '李白', '相思': '王维', '春晓': '孟浩然',
        '登鹳雀楼': '王之涣', '江雪': '柳宗元', '寻隐者不遇': '贾岛',
        '鹿柴': '王维', '竹里馆': '王维', '登乐游原': '李商隐',
        '问刘十九': '白居易', '秋浦歌': '李白', '独坐敬亭山': '李白',
        '望庐山瀑布': '李白', '早发白帝城': '李白', '赠汪伦': '李白',
        '望天门山': '李白', '春夜洛城闻笛': '李白', '赠花卿': '杜甫',
        '春望': '杜甫', '月夜': '杜甫', '春夜喜雨': '杜甫',
        '旅夜书怀': '杜甫', '登岳阳楼': '杜甫', '蜀相': '杜甫', '客至': '杜甫',
    }
    
    # 内容探测（标题在库中不同名的诗）
    CONTENT_PROBES = {
        '悯农': '粒粒皆辛苦',
        '古朗月行': '小时不识月',
        '长歌行（节选）': '少壮不努力',
    }
    
    def get_daily_poem(self, day=None):
        """获取每日诗词（每天固定，跨天变化，名篇优先）"""
        day = day or date.today()
        seed = int(hashlib.md5(f"poem_{day.isoformat()}".encode()).hexdigest()[:8], 16)
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 优先从名篇池选取
            title = self.FAMOUS_TITLES[seed % len(self.FAMOUS_TITLES)]
            
            # 优先按偏好作者匹配
            row = None
            preferred = self.PREFERRED_AUTHORS.get(title)
            if preferred:
                cursor.execute('''
                    SELECT id, title, author, dynasty, content, collection, poem_form, theme
                    FROM poems WHERE title = ? AND author = ?
                    ORDER BY classic_score DESC, id
                    LIMIT 1
                ''', (title, preferred))
                row = cursor.fetchone()
            
            # 内容探测（标题不同名的情况，如悯农→古风二首）
            if not row and title in self.CONTENT_PROBES:
                probe = self.CONTENT_PROBES[title]
                if preferred:
                    cursor.execute('''
                        SELECT id, title, author, dynasty, content, collection, poem_form, theme
                        FROM poems WHERE content LIKE ? AND author = ?
                        ORDER BY classic_score DESC, id
                        LIMIT 1
                    ''', (f'%{probe}%', preferred))
                    row = cursor.fetchone()
                if not row:
                    cursor.execute('''
                        SELECT id, title, author, dynasty, content, collection, poem_form, theme
                        FROM poems WHERE content LIKE ?
                        ORDER BY classic_score DESC, id
                        LIMIT 1
                    ''', (f'%{probe}%',))
                    row = cursor.fetchone()
            
            # 退回到经典合集匹配
            if not row:
                cursor.execute('''
                    SELECT id, title, author, dynasty, content, collection, poem_form, theme
                    FROM poems WHERE title = ?
                    ORDER BY classic_score DESC, id
                    LIMIT 1
                ''', (title,))
                row = cursor.fetchone()
            
            # 再退回到书名匹配
            if not row:
                cursor.execute('''
                    SELECT id, title, author, dynasty, content, collection, poem_form, theme
                    FROM poems WHERE title LIKE ?
                    ORDER BY classic_score DESC, id
                    LIMIT 1
                ''', (f'%{title}%',))
                row = cursor.fetchone()
            
            if not row:
                # 名篇找不到时，从经典池（classic_score>=90）确定性选取
                cursor.execute("SELECT COUNT(*) FROM poems WHERE classic_score >= 90")
                count = cursor.fetchone()[0]
                if count > 0:
                    offset = seed % count
                    cursor.execute('''
                        SELECT id, title, author, dynasty, content, collection, poem_form, theme
                        FROM poems 
                        WHERE classic_score >= 90
                        ORDER BY id LIMIT 1 OFFSET ?
                    ''', (offset,))
                    row = cursor.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'author': row['author'],
                    'dynasty': row['dynasty'],
                    'content': row['content'],
                    'collection': row['collection'],
                    'poem_form': row['poem_form'],
                    'theme': row['theme'],
                    'date': day.isoformat()
                }
        except Exception as e:
            log.error(f"每日推荐失败: {e}")
        
        return None
    
    def get_daily_guwen(self, day=None):
        """获取每日古文"""
        day = day or date.today()
        seed = int(hashlib.md5(f"guwen_{day.isoformat()}".encode()).hexdigest()[:8], 16)
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM guwen WHERE collection = '古文观止'")
            count = cursor.fetchone()[0]
            
            if count == 0:
                return None
            
            offset = seed % count
            cursor.execute('''
                SELECT id, title, author, dynasty, content, translation, background, appreciation, char_count
                FROM guwen WHERE collection = '古文观止'
                ORDER BY id LIMIT 1 OFFSET ?
            ''', (offset,))
            
            row = cursor.fetchone()
            if row:
                return {
                    'id': row['id'],
                    'title': row['title'],
                    'author': row['author'],
                    'dynasty': row['dynasty'],
                    'content': row['content'],
                    'translation': row['translation'],
                    'background': row['background'],
                    'appreciation': row['appreciation'],
                    'char_count': row['char_count'],
                    'date': day.isoformat()
                }
        except Exception as e:
            log.error(f"每日古文失败: {e}")
        
        return None


if __name__ == "__main__":
    # 测试
    logging.basicConfig(level=logging.INFO)
    
    print("=== TTS 测试 ===")
    tts = TTSEngine()
    print(f"edge-tts: {HAS_EDGE_TTS}, SAPI: {HAS_SAPI}")
    
    print()
    print("=== 拼音测试 ===")
    print(get_pinyin_text("床前明月光，疑是地上霜。"))
    
    print()
    print("=== 每日推荐测试 ===")
    rec = DailyRecommender(Path(__file__).parent / "data" / "poetry.db")
    poem = rec.get_daily_poem()
    if poem:
        print(f"今日诗词: 《{poem['title']}》{poem['author']} ({poem['collection']})")
    guwen = rec.get_daily_guwen()
    if guwen:
        print(f"今日古文: 《{guwen['title']}》{guwen['author']}")
