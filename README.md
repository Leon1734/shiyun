# 诗韵 · 古诗词桌面小工具

> 一款基于 [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) 开放数据的 Windows 桌面诗词工具
> Python + tkinter + SQLite · 345,000+ 首诗词 · 免安装独立 exe

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-lightgrey)]()
[![Data](https://img.shields.io/badge/Data-345%2C000%2B%20poems-orange)]()

---

## ✨ 功能特性

### 📚 海量数据
- **345,000+ 首诗词**：全唐诗（57,435）· 全宋诗（254,225）· 宋词（21,053）· 元曲（10,914）
- **经典选本**：唐诗三百首 · 宋词三百首 · 千家诗 · 名篇精选 · 中学古诗 · 诗经 · 楚辞 · 花间集 · 纳兰性德 · 南唐二主词 · 曹操诗集
- **533 篇古文**：古文观止 + 中学文言文
- **181 条名句**：按作者/主题浏览欣赏
- 全部内容**简体化**（OpenCC 繁简转换）

### 🔍 查找与浏览
- **统一搜索**：诗词 / 古文 / 诗人三合一，全文匹配
- **多维筛选**：朝代 · 作者 · 题材 · 诗体 · 字数 · 合集
- **经典度排序**：耳熟能详的名篇自动置顶（见下方"经典度评分"）
- **经典加权随机**：点"随机"优先遇见传诵度高的好诗
- **每日推荐**：每天固定一首诗词 + 一篇古文，跨天自动更新

### 🎨 阅读与体验
- 宣纸 / 墨色双主题，沉浸式阅读模式
- 字号调节 · 顺序导航 · 快捷键（←/→ 翻诗、Ctrl+F 搜索、F5 随机、F11 沉浸）
- 拼音注音 · 朗读（edge-tts）· 选中复制
- 古典卡片生成：为每首诗生成古风分享卡片

### 🧩 拓展功能
- **学习模式**：记忆练习与进度跟踪
- **游戏化**：诗词小游戏（飞花令等）
- **创作辅助**：格律校验与灵感工具
- **诗人档案**：生平统计 · 题材分布 · 代表作推荐
- **词牌词典**：词牌格律与名作对照
- **数据可视化**：纯 tkinter Canvas 图表（免 matplotlib）
- 收藏夹 · 名句欣赏 · 繁简转换 · 多语言界面

---

## 🚀 快速开始

### 方式一：下载打包版（推荐，免 Python）

1. 从 [Releases](https://github.com/Leon1734/shiyun/releases) 下载最新 `shiyun-v7.0-win64.zip`
2. 解压到任意目录（已内置数据库）
3. 双击 `诗韵.exe` 即可运行

> 无需安装 Python，Windows 10/11 64 位均可运行。

### 方式二：源码运行

```bash
# 1. 克隆仓库
git clone https://github.com/Leon1734/shiyun.git && cd shiyun

# 2. 安装依赖
pip install -r requirements.txt

# 3. 准备数据（见下方「数据构建」，或从 Releases 下载 poetry.db 放入 data/）

# 4. 启动
python poetry_desktop.py
# 或双击 start.bat
```

---

## 🗂 数据构建

> 完整数据（1.4GB 源 JSON + 267MB SQLite）未包含在仓库中。
> 快速体验请直接从 [Releases](https://github.com/Leon1734/shiyun/releases) 下载打包版；自行构建请按以下步骤。

### 1. 获取源数据

从 [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) 获取以下数据集，放入 `data/` 对应目录：

| 数据集 | 目录 | 数量 |
|--------|------|------|
| 全唐诗 | `data/全唐诗/` | 57,000+ |
| 全宋诗 | `data/全宋诗/` | 254,000+ |
| 宋词 | `data/宋词/` | 21,000+ |
| 元曲 | `data/元曲/` | 11,000+ |
| 诗经 · 楚辞 · 论语 · 四书五经 | `data/诗经/` 等 | 305 / 65 / ... |
| 纳兰性德 · 花间集 · 南唐二主词 · 曹操诗集 | `data/纳兰性德/` 等 | 257 / 498 / 45 / 26 |
| 蒙学 · 幽梦影 | `data/蒙学/` · `data/幽梦影/` | 11 部 / 219 |

> 国内网络可用镜像加速：`https://gh-proxy.com/https://github.com/chinese-poetry/chinese-poetry`

### 2. 一键构建（按顺序执行）

```bash
python json_to_sqlite.py        # JSON → SQLite 主库（含繁简转换）
python import_more.py           # 导入纳兰性德/花间集/南唐二主词/曹操/蒙学/幽梦影
python import_anthologies.py    # 导入 千家诗/唐诗三百首/宋词三百首（结构化）
python add_curated.py           # 补录名篇精选（17 首通行版本）
python add_curated2.py          # 补录汉魏六朝名篇（18 首：木兰诗/古诗十九首/陶渊明等）
python classify_poems_v3.py     # 题材/诗体分类
python classify_more.py         # 补充合集分类
python normalize_data.py apply  # 标题规范化 + 异体字统一（如 疎→疏、鏁→锁）
python build_classic_score.py   # 经典度评分（排序依据，见下）
python build_quotes.py          # 构建名句库
```

古文部分：

```bash
python download_guwen.py        # 下载古文观止（via gh-proxy）
python import_guwen.py          # 导入 222 篇
python import_school.py         # 导入中学文言文
```

---

## ⭐ 经典度评分（排序核心）

项目为每首诗词计算 **classic_score**（经典度），作为目录排序、搜索结果、随机推荐的核心依据：

| 维度 | 加分 | 说明 |
|------|------|------|
| 名篇精选 | +100 | 家喻户晓的通行版本（静夜思、悯农等） |
| 唐诗三百首 / 宋词三百首 | +95 | 经典选本 |
| 千家诗 / 中学古诗 | +90 | 启蒙与教材名篇 |
| 诗经 / 楚辞 | +65 | 源头经典 |
| 名句原诗 | +70 | 181 条名句对应原诗 |
| 国民级诗人（李白/杜甫/苏轼等 19 位） | +60 | 作者加分 |
| 著名诗人（约 80 位） | +40 | 作者加分 |

**效果**：打开目录第一屏即是《静夜思》《泊船瓜洲》《将进酒》《春望》……；
搜"静夜思"优先显示通行版；点"随机"60% 概率遇见传诵名篇。

---

## 📁 项目结构

```
chinese-poetry/
├── poetry_desktop.py        # 主程序（tkinter GUI）
├── start.bat                # 启动脚本
├── build_exe.bat            # 打包脚本（PyInstaller）
├── build.spec               # PyInstaller 配置
├── requirements.txt         # 依赖清单
│
├── data/                    # 数据目录（不提交，见「数据构建」）
│   └── poetry.db            # SQLite 主库（267MB）
│
├── # ── 核心模块 ──
├── app_paths.py             # 路径管理（源码/exe 统一）
├── converter.py             # 繁简转换
├── poem_classifier.py       # 诗体/题材分类器
├── famous_authors.py        # 著名诗人名单（公共）
├── features_v7.py           # 每日推荐等 v7 功能
├── features_ui.py           # 诗人档案/词牌词典/统一搜索窗口
├── poet_profile.py          # 诗人档案数据层
├── unified_search.py        # 统一搜索引擎
├── quotes_ui.py             # 名句欣赏
├── guwen_ui.py              # 古文阅读
├── card_generator.py        # 古典卡片生成
├── cipai_dict.py            # 词牌词典
├── learning.py / learning_ui.py   # 学习模式
├── game.py / game_ui.py           # 游戏化
├── creation.py / creation_ui.py   # 创作辅助
├── collection_manager.py    # 收藏夹
├── search_advanced.py       # 高级搜索
├── data_visualization.py    # 数据可视化
├── ui_theme_v2.py           # 主题系统
├── plugin_system.py         # 插件系统
│
├── # ── 数据构建脚本 ──
├── json_to_sqlite.py        # 主库构建
├── import_*.py              # 合集导入（more/anthologies/classics/guwen/school/missing）
├── download_*.py            # 数据下载（guwen/more/wudai）
├── classify_*.py            # 题材/诗体分类
├── normalize_data.py        # 标题规范化 + 异体字统一
├── build_classic_score.py   # 经典度评分
├── build_quotes.py          # 名句库构建
├── fix_edge_cases.py        # 边缘数据修复
├── fix_yuanqu_titles.py     # 元曲标题修复
└── add_curated*.py          # 名篇精选补录
```

---

## 📦 打包发行

```bash
# 方式一：双击
build_exe.bat

# 方式二：命令行
pyinstaller build.spec --noconfirm --clean
```

产物：`dist/诗韵/诗韵.exe`（onedir 模式，约 93MB）。

> **注意**：exe 通过目录链接（junction）引用 `data/poetry.db`。
> 分发时需将 `data/poetry.db` 一并放入 `dist/诗韵/data/`。

---

## 🔧 技术要点

| 要点 | 说明 |
|------|------|
| **SQLite 取代 JSON** | 加载速度 40s → 0.94s；LIKE 全文搜索优于 FTS5 中文分词 |
| **繁简转换** | 数据加载阶段 OpenCC `t2s` 统一转换 |
| **经典度评分** | 选本收录 + 名句原诗 + 诗人知名度三维加权（见上） |
| **异体字治理** | 疎→疏、迳→径、鏁→锁、徧→遍 等 40+ 组古籍异体字统一，保证搜索命中 |
| **数据修复** | 乐府分类前缀剥离、元曲截断标题还原、选集去重、异文保留原则 |
| **免依赖可视化** | 纯 tkinter Canvas 实现图表，打包体积减小 ~40MB |

---

## 📜 数据来源与致谢

| 来源 | 内容 | 许可 |
|------|------|------|
| [chinese-poetry](https://github.com/chinese-poetry/chinese-poetry) | 全唐诗/全宋诗/宋词/元曲/诗经/楚辞等 | MIT |
| [niuniu-869/guwenguanzhi](https://github.com/niuniu-869/guwenguanzhi) | 古文观止 222 篇 | - |
| [lanhin/SchoolChinese](https://github.com/lanhin/SchoolChinese) | 中学古诗文 | - |
| 项目补充 | 名篇精选（35 首通行版本）、经典度评分 | MIT |

## 📄 License

代码部分：MIT License
数据部分：遵循各上游来源许可（主要为 MIT），仅供学习交流使用。
