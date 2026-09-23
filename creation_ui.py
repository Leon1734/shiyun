#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创作辅助界面模块
功能：创作编辑器、押韵检查、格律检查、创作模板选择
依赖：tkinter, poetry_desktop_v2.THEMES
"""

import re
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from datetime import datetime

# ── 声韵 / 格律参考数据 ──────────────────────────────────────────────────────

# 平水韵（简化版）：韵部 → 常见字
RHYME_GROUPS = {
    "一东": "东同铜桐筒童僮瞳中衷忠虫终戎崇嵩弓躬宫融雄熊穹穷冯风枫丰充隆空蒙朦笼聋珑洪红鸿虹丛翁公功工攻蓬篷烘通",
    "二冬": "冬农宗钟龙松冲容蓉庸胸雍浓重从逢缝峰锋丰慵恭供淙侬",
    "三江": "江杠矼扛庞邦双窗腔降撞缸",
    "四支": "支枝移为垂吹陂碑奇宜仪皮儿离施知驰池规危夷师姿迟眉悲之芝时诗棋旗辞词期祠基疑姬丝司葵医帷思滋持随痴维卮麾螭弥慈遗肌脂雌披嬉尸狸炊篱萎差疲亏骑曦曦",
    "五微": "微薇晖辉徽挥韦围帏违霏菲妃飞非扉肥归依稀希衣矶机几讥饥矶",
    "六鱼": "鱼渔初书舒居裾车渠蕖余予誉舆胥狙锄疏蔬梳虚嘘徐猪闾庐驴诸除储如墟",
    "七虞": "虞愚娱隅刍无芜巫于盂衢儒濡襦须株蛛殊瑜榆谀愉腴区驱躯朱珠趋扶符凫雏敷夫肤纡输枢厨俱驹模谟蒲胡湖瑚乎壶狐弧孤辜姑觚菰徒途涂茶图屠奴呼吾梧吴租卢鲈炉芦苏酥乌枯粗都铺禺",
    "八齐": "齐黎藜犁梨妻萋凄堤低氐题提蹄啼鸡稽兮奚蹊霓西栖犀嘶撕梯鼙齑迷泥闺睽奎携畦",
    "九佳": "佳街鞋牌柴钗差崖阶偕谐骸排乖怀淮豺埋霾斋娲蜗娃哇皆揩",
    "十灰": "灰恢魁隈回徊槐梅枚玫媒煤雷催摧堆陪杯嵬推开哀埃台苔该才材财裁来莱栽哉灾猜胎孩洄崔培",
    "十一真": "真因茵辛新薪晨辰臣人仁神亲申伸绅身宾滨邻鳞麟珍瞋尘陈春津秦频苹颦濒银垠筠巾民贫淳醇纯唇伦纶轮沦匀旬巡驯钧均臻榛姻宸寅嫔彬鹑皴遵循甄椿",
    "十二文": "文闻纹蚊云氛分纷芬焚坟群裙君军勤斤筋勋薰曛醺芸耘汾欣芹殷昕翁",
    "十三元": "元原源园猿辕垣烦繁蕃樊翻暄萱喧冤言轩藩魂浑温孙门尊樽存蹲敦墩暾屯论昆昏婚阍根恩吞奔盆浑瘟掀昆琨扪荪髡跟",
    "十四寒": "寒韩翰丹殚安难残干肝竿乾官冠观鸾銮栾峦欢宽盘蟠漫汗郸叹摊奸剜棺钻瘢谩瞒潘拦完莞獾般搬桓纨端湍酸团抟攒官",
    "十五删": "删潸关弯湾还环鬟斑班颁蛮颜奸攀顽山鳏闲间艰闲",
    # ... 简化，仅保留常用韵部
}

# 五言 / 七言绝句 / 律诗格律模板
METER_TEMPLATES = {
    "五言绝句（仄起首句不入韵）": {
        "length": 5,
        "lines": 4,
        "pattern": ["仄仄平平仄", "平平仄仄平", "平平平仄仄", "仄仄仄平平"],
        "rhyme_lines": [1, 3],  # 0-indexed
    },
    "五言绝句（平起首句入韵）": {
        "length": 5,
        "lines": 4,
        "pattern": ["平平仄仄平", "仄仄仄平平", "仄仄平平仄", "平平仄仄平"],
        "rhyme_lines": [0, 1, 3],
    },
    "七言绝句（仄起首句入韵）": {
        "length": 7,
        "lines": 4,
        "pattern": ["仄仄平平仄仄平", "平平仄仄仄平平", "平平仄仄平平仄", "仄仄平平仄仄平"],
        "rhyme_lines": [0, 1, 3],
    },
    "七言绝句（平起首句不入韵）": {
        "length": 7,
        "lines": 4,
        "pattern": ["平平仄仄平平仄", "仄仄平平仄仄平", "仄仄平平平仄仄", "平平仄仄仄平平"],
        "rhyme_lines": [1, 3],
    },
    "五言律诗（仄起首句不入韵）": {
        "length": 5,
        "lines": 8,
        "pattern": [
            "仄仄平平仄", "平平仄仄平", "平平平仄仄", "仄仄仄平平",
            "仄仄平平仄", "平平仄仄平", "平平平仄仄", "仄仄仄平平",
        ],
        "rhyme_lines": [1, 3, 5, 7],
    },
    "七言律诗（平起首句入韵）": {
        "length": 7,
        "lines": 8,
        "pattern": [
            "平平仄仄仄平平", "仄仄平平仄仄平", "仄仄平平平仄仄", "平平仄仄仄平平",
            "平平仄仄平平仄", "仄仄平平仄仄平", "仄仄平平平仄仄", "平平仄仄仄平平",
        ],
        "rhyme_lines": [0, 1, 3, 5, 7],
    },
}

# 简化的平仄判断（基于常见字，实际需查韵书）
TONE_MAP_COMMON = {
    # 常见平声字
    "的": "平", "是": "仄", "不": "仄", "了": "平", "人": "平",
    "在": "仄", "有": "仄", "中": "平", "大": "仄", "为": "平",
    "上": "仄", "来": "平", "到": "仄", "时": "平", "地": "平",
    "出": "仄", "会": "仄", "生": "平", "年": "平", "作": "仄",
    "天": "平", "子": "仄", "自": "仄", "家": "平", "开": "平",
    "山": "平", "水": "仄", "花": "平", "月": "仄", "风": "平",
    "云": "平", "雨": "仄", "雪": "仄", "春": "平", "秋": "平",
    "日": "仄", "夜": "仄", "白": "仄", "青": "平", "红": "平",
    "长": "平", "明": "平", "空": "平", "心": "平", "情": "平",
    "思": "平", "愁": "平", "归": "平", "飞": "平", "知": "平",
    "声": "平", "光": "平", "寒": "平", "高": "平", "深": "平",
    "新": "平", "旧": "仄", "远": "仄", "近": "仄", "古": "仄",
    "今": "平", "南": "平", "北": "仄", "东": "平", "西": "平",
    "一": "仄", "二": "仄", "三": "平", "千": "平", "万": "仄",
    "无": "平", "有": "仄", "多": "平", "少": "仄", "独": "仄",
}


def get_tone(char):
    """获取汉字平仄（简化版）"""
    if char in TONE_MAP_COMMON:
        return TONE_MAP_COMMON[char]
    # 默认：按拼音声调估算（1/2 平，3/4 仄）
    return "平"  # 未知字默认平


def check_rhyme(line1, line2):
    """检查两句是否押韵（尾字韵母相同）"""
    def last_char(text):
        for ch in reversed(text):
            if "\u4e00" <= ch <= "\u9fff":
                return ch
        return ""

    c1, c2 = last_char(line1), last_char(line2)
    if not c1 or not c2:
        return False, ""
    if c1 == c2:
        return True, c1

    # 查韵部
    for group_name, chars in RHYME_GROUPS.items():
        if c1 in chars and c2 in chars:
            return True, group_name
    return False, ""


def check_meter(line, expected_pattern):
    """检查一行的平仄是否符合格律"""
    result = []
    mismatches = 0
    for i, ch in enumerate(line):
        if "\u4e00" <= ch <= "\u9fff":
            actual = get_tone(ch)
            expected = expected_pattern[i] if i < len(expected_pattern) else "平"
            match = actual == expected
            result.append((ch, actual, expected, match))
            if not match:
                mismatches += 1
    return result, mismatches


# ── 创作编辑器 ────────────────────────────────────────────────────────────────

class CreationEditor:
    """诗词创作编辑器"""

    def __init__(self, parent, colors, db=None):
        self.parent = parent
        self.colors = colors
        self.db = db
        self.current_file = None
        self.win = None

    def show(self):
        c = self.colors
        self.win = tk.Toplevel(self.parent)
        self.win.title("✍️ 诗词创作")
        self.win.geometry("680x620")
        self.win.configure(bg=c["bg"])
        self.win.transient(self.parent)

        # ── 顶部工具栏 ──
        toolbar = tk.Frame(self.win, bg=c["bg"])
        toolbar.pack(fill="x", padx=12, pady=(8, 4))

        tk.Button(toolbar, text="📄 新建", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=10, pady=3,
                  command=self._new).pack(side="left", padx=2)

        tk.Button(toolbar, text="📂 打开", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=10, pady=3,
                  command=self._open).pack(side="left", padx=2)

        tk.Button(toolbar, text="💾 保存", font=("微软雅黑", 10),
                  bg=c["button_bg"], fg=c["button_fg"], relief="flat", padx=10, pady=3,
                  command=self._save).pack(side="left", padx=2)

        tk.Button(toolbar, text="📋 格律检查", font=("微软雅黑", 10, "bold"),
                  bg=c["accent"], fg="#ffffff", relief="flat", padx=10, pady=3,
                  command=self._check_meter).pack(side="right", padx=2)

        tk.Button(toolbar, text="🎵 押韵检查", font=("微软雅黑", 10, "bold"),
                  bg=c["success"], fg="#ffffff", relief="flat", padx=10, pady=3,
                  command=self._check_rhyme).pack(side="right", padx=2)

        tk.Button(toolbar, text="📐 模板", font=("微软雅黑", 10),
                  bg=c["warning"], fg="#000000", relief="flat", padx=10, pady=3,
                  command=self._show_templates).pack(side="right", padx=2)

        # ── 标题输入 ──
        title_frame = tk.Frame(self.win, bg=c["bg"])
        title_frame.pack(fill="x", padx=12, pady=4)

        tk.Label(title_frame, text="标题：", font=("微软雅黑", 11),
                 fg=c["fg"], bg=c["bg"]).pack(side="left")
        self.title_var = tk.StringVar()
        title_entry = tk.Entry(title_frame, textvariable=self.title_var,
                                font=("微软雅黑", 11), bg=c["entry_bg"], fg=c["entry_fg"],
                                insertbackground=c["fg"], relief="flat",
                                highlightbackground=c["border"], highlightthickness=1)
        title_entry.pack(side="left", fill="x", expand=True, padx=6)

        # ── 编辑区 ──
        edit_frame = tk.Frame(self.win, bg=c["bg"])
        edit_frame.pack(fill="both", expand=True, padx=12, pady=6)

        line_numbers = tk.Text(edit_frame, font=("微软雅黑", 12), width=3,
                                bg=c["bg_tertiary"], fg=c["fg_secondary"],
                                relief="flat", state="disabled", padx=4)
        line_numbers.pack(side="left", fill="y")

        self.editor = tk.Text(edit_frame, font=("微软雅黑", 13), bg=c["bg_secondary"],
                               fg=c["fg"], relief="flat", wrap="word",
                               spacing1=4, spacing3=4, padx=12, pady=8,
                               selectbackground=c["select_bg"],
                               insertbackground=c["fg"],
                               highlightbackground=c["border"], highlightthickness=1)
        self.editor.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(edit_frame, orient="vertical", command=self.editor.yview)
        self.editor.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        # 行号更新
        def update_line_numbers(event=None):
            line_numbers.config(state="normal")
            line_numbers.delete("1.0", "end")
            line_count = int(self.editor.index("end-1c").split(".")[0])
            for i in range(1, line_count + 1):
                line_numbers.insert("end", f"{i}\n")
            line_numbers.config(state="disabled")

        self.editor.bind("<KeyRelease>", update_line_numbers)
        self.editor.bind("<MouseWheel>", update_line_numbers)
        update_line_numbers()

        # ── 状态栏 / 检查结果 ──
        self.result_frame = tk.Frame(self.win, bg=c["bg_secondary"],
                                      highlightbackground=c["border"], highlightthickness=1)
        self.result_frame.pack(fill="x", padx=12, pady=(4, 8))

        self.result_label = tk.Label(self.result_frame, text="✨ 开始创作吧！",
                                      font=("微软雅黑", 10), fg=c["fg_secondary"],
                                      bg=c["bg_secondary"], anchor="w", padx=12, pady=6)
        self.result_label.pack(fill="x")

        # ── 字数统计 ──
        self.count_label = tk.Label(self.win, font=("微软雅黑", 9),
                                     fg=c["fg_secondary"], bg=c["bg"])
        self.count_label.pack(anchor="e", padx=14, pady=(0, 4))

        def update_count(event=None):
            text = self.editor.get("1.0", "end-1c")
            chars = sum(1 for ch in text if "\u4e00" <= ch <= "\u9fff")
            self.count_label.config(text=f"字数：{chars}")

        self.editor.bind("<KeyRelease>", lambda e: (update_line_numbers(e), update_count(e)))

    def _new(self):
        self.title_var.set("")
        self.editor.delete("1.0", "end")
        self.current_file = None
        self.result_label.config(text="✨ 新建文档")

    def _open(self):
        filename = filedialog.askopenfilename(
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if filename:
            try:
                with open(filename, encoding="utf-8") as f:
                    content = f.read()
                self.editor.delete("1.0", "end")
                self.editor.insert("1.0", content)
                self.current_file = filename
                self.result_label.config(text=f"📂 已打开：{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"打开失败：{e}", parent=self.win)

    def _save(self):
        if self.current_file:
            filename = self.current_file
        else:
            filename = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt")],
                initialfile=f"poem_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
        if filename:
            try:
                content = self.editor.get("1.0", "end-1c")
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(content)
                self.current_file = filename
                self.result_label.config(text=f"💾 已保存：{filename}")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败：{e}", parent=self.win)

    def _get_lines(self):
        """获取编辑器中的诗句行（去除空行）"""
        text = self.editor.get("1.0", "end-1c")
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _check_rhyme(self):
        """押韵检查"""
        c = self.colors
        lines = self._get_lines()
        if len(lines) < 2:
            self.result_label.config(text="⚠️ 至少需要两行诗句才能检查押韵", fg=c["warning"])
            return

        results = []
        # 检查偶数行（传统诗词押韵位）
        rhyme_positions = [i for i in range(len(lines)) if i % 2 == 1 or i == 0]
        last_line = lines[-1]

        for i in range(len(lines) - 1):
            for j in range(i + 1, len(lines)):
                rhymed, info = check_rhyme(lines[i], lines[j])
                if rhymed:
                    results.append(f"✅ 第{i+1}行 与 第{j+1}行 押韵（{info}）")

        if results:
            self.result_label.config(text="  ".join(results), fg=c["success"])
        else:
            self.result_label.config(text="⚠️ 未检测到押韵关系", fg=c["warning"])

    def _check_meter(self):
        """格律检查 — 弹出模板选择后检查"""
        c = self.colors
        lines = self._get_lines()
        if not lines:
            self.result_label.config(text="⚠️ 请先输入诗句", fg=c["warning"])
            return

        # 选择格律模板
        template_names = list(METER_TEMPLATES.keys())
        dialog = tk.Toplevel(self.win)
        dialog.title("选择格律模板")
        dialog.geometry("380x200")
        dialog.configure(bg=c["bg"])
        dialog.transient(self.win)

        tk.Label(dialog, text="选择格律模板：", font=("微软雅黑", 11),
                 fg=c["fg"], bg=c["bg"]).pack(pady=(16, 8))

        selected = tk.StringVar(value=template_names[0])
        combo = ttk.Combobox(dialog, textvariable=selected, values=template_names,
                              state="readonly", font=("微软雅黑", 10), width=30)
        combo.pack(pady=4)

        def do_check():
            dialog.destroy()
            template_name = selected.get()
            template = METER_TEMPLATES[template_name]
            self._apply_meter_check(lines, template, template_name)

        tk.Button(dialog, text="✅ 检查", font=("微软雅黑", 11, "bold"),
                  bg=c["accent"], fg="#ffffff", relief="flat", padx=20, pady=6,
                  command=do_check).pack(pady=16)

    def _apply_meter_check(self, lines, template, template_name):
        """执行格律检查"""
        c = self.colors
        expected_lines = template["lines"]
        char_len = template["length"]
        pattern = template["pattern"]
        rhyme_lines = template["rhyme_lines"]

        issues = []
        details = []

        for i, line in enumerate(lines):
            if i >= expected_lines:
                issues.append(f"⚠️ 第{i+1}行超出模板行数（{expected_lines}行）")
                continue

            # 提取汉字
            han_chars = [ch for ch in line if "\u4e00" <= ch <= "\u9fff"]
            if len(han_chars) != char_len:
                issues.append(f"⚠️ 第{i+1}行应为{char_len}字，实际{len(han_chars)}字")
                continue

            expected_pat = pattern[i]
            result, mismatches = check_meter("".join(han_chars), expected_pat)

            detail_parts = []
            for ch, actual, expected, match in result:
                mark = "✓" if match else "✗"
                detail_parts.append(f"{ch}({actual}/{expected}){'✓' if match else '✗'}")

            details.append(f"第{i+1}行：{''.join(detail_parts)}")
            if mismatches > 0:
                issues.append(f"⚠️ 第{i+1}行有{mismatches}处平仄不符")

        # 押韵检查
        for i in rhyme_lines:
            if i < len(lines):
                for j in rhyme_lines:
                    if j > i and j < len(lines):
                        rhymed, info = check_rhyme(lines[i], lines[j])
                        if not rhymed:
                            issues.append(f"⚠️ 第{i+1}行与第{j+1}行不押韵")

        # 显示结果
        result_text = f"📋 格律检查（{template_name}）\n"
        if issues:
            result_text += "  ".join(issues)
        else:
            result_text += "✅ 完全符合格律！"

        if details:
            result_text += "\n" + "  ".join(details)

        self.result_label.config(text=result_text, fg=self.colors["success"] if not issues else self.colors["warning"])

    def _show_templates(self):
        """显示创作模板选择"""
        TemplateChooser(self.parent, self.colors, self.editor, self.title_var)


# ── 创作模板选择 ──────────────────────────────────────────────────────────────

class TemplateChooser:
    """创作模板选择界面"""

    TEMPLATES = [
        {
            "name": "🌅 五言绝句",
            "desc": "四句五言，简洁明快",
            "template": "□□□□□\n□□□□□\n□□□□□\n□□□□□",
            "hint": "每句 5 字，共 4 句",
        },
        {
            "name": "🌄 七言绝句",
            "desc": "四句七言，意境悠远",
            "template": "□□□□□□□\n□□□□□□□\n□□□□□□□\n□□□□□□□",
            "hint": "每句 7 字，共 4 句",
        },
        {
            "name": "🏔️ 五言律诗",
            "desc": "八句五言，对仗工整",
            "template": "□□□□□\n□□□□□\n□□□□□\n□□□□□\n□□□□□\n□□□□□\n□□□□□\n□□□□□",
            "hint": "每句 5 字，共 8 句，颔联颈联需对仗",
        },
        {
            "name": "🌊 七言律诗",
            "desc": "八句七言，气势磅礴",
            "template": "□□□□□□□\n□□□□□□□\n□□□□□□□\n□□□□□□□\n□□□□□□□\n□□□□□□□\n□□□□□□□\n□□□□□□□",
            "hint": "每句 7 字，共 8 句，颔联颈联需对仗",
        },
        {
            "name": "🎵 宋词（如梦令）",
            "desc": "短小精悍，含蓄婉约",
            "template": "□□□□□□□\n□□□□□□□\n□□□□□\n□□□□□□□\n□□□□□□□\n□□□□□\n□□□□□",
            "hint": "如梦令格式：七七五七七五七",
        },
        {
            "name": "🌸 宋词（浣溪沙）",
            "desc": "清新雅致，情景交融",
            "template": "□□□□□□□\n□□□□□□□\n□□□□□□□\n\n□□□□□□□\n□□□□□□□\n□□□□□□□",
            "hint": "浣溪沙格式：上下两阕，各三句七言",
        },
        {
            "name": "✨ 自由体",
            "desc": "不拘格律，自由抒发",
            "template": "",
            "hint": "自由发挥，不受格律约束",
        },
    ]

    def __init__(self, parent, colors, editor, title_var):
        self.colors = colors
        self.editor = editor
        self.title_var = title_var

        self.win = tk.Toplevel(parent)
        self.win.title("📐 创作模板")
        self.win.geometry("420x520")
        self.win.configure(bg=colors["bg"])
        self.win.transient(parent)
        self._build()

    def _build(self):
        c = self.colors

        tk.Label(self.win, text="📐 选择创作模板", font=("微软雅黑", 14, "bold"),
                 fg=c["accent"], bg=c["bg"]).pack(pady=(12, 8))

        # 可滚动列表
        list_frame = tk.Frame(self.win, bg=c["bg"])
        list_frame.pack(fill="both", expand=True, padx=16, pady=4)

        canvas = tk.Canvas(list_frame, bg=c["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg=c["bg"])

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        for tpl in self.TEMPLATES:
            card = tk.Frame(inner, bg=c["bg_secondary"], cursor="hand2",
                            highlightbackground=c["border"], highlightthickness=1)
            card.pack(fill="x", pady=4, padx=4)

            tk.Label(card, text=tpl["name"], font=("微软雅黑", 12, "bold"),
                     fg=c["accent"], bg=c["bg_secondary"]).pack(anchor="w", padx=12, pady=(8, 0))
            tk.Label(card, text=tpl["desc"], font=("微软雅黑", 9),
                     fg=c["fg_secondary"], bg=c["bg_secondary"]).pack(anchor="w", padx=12)
            tk.Label(card, text=tpl["hint"], font=("微软雅黑", 9),
                     fg=c["warning"], bg=c["bg_secondary"]).pack(anchor="w", padx=12, pady=(0, 8))

            def handler(t=tpl):
                self._apply_template(t)

            card.bind("<Button-1>", lambda e, h=handler: h())
            for child in card.winfo_children():
                child.bind("<Button-1>", lambda e, h=handler: h())

    def _apply_template(self, tpl):
        self.editor.delete("1.0", "end")
        if tpl["template"]:
            self.editor.insert("1.0", tpl["template"])
        self.title_var.set("")
        self.win.destroy()
