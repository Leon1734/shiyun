# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller 打包配置
古诗词桌面小工具 v7.0 · 诗韵

用法: pyinstaller build.spec
输出: dist/诗韵/诗韵.exe (onedir 模式，数据库外部引用)
"""

import sys
from pathlib import Path

block_cipher = None

# 项目根目录
ROOT = Path(SPECPATH)

# 需要打包的 Python 模块（隐式导入）
hidden_imports = [
    'converter',
    'poem_classifier',
    'poetry_utils',
    'app_paths',
    'famous_authors',
    'features_v7',
    'features_ui',
    'card_generator',
    'cipai_dict',
    'poet_profile',
    'unified_search',
    'guwen_ui',
    'quotes_ui',
    'tk_charts',
    'ui_theme_v2',
    'learning', 'learning_ui',
    'game', 'game_ui',
    'creation', 'creation_ui',
    'collection_manager',
    'search_advanced',
    'data_visualization',
    'performance_optimizer',
    'ux_enhancements',
    'i18n_manager',
    'plugin_system',
    'cloud_sync',
    'integration',
    'pypinyin',
    'edge_tts',
    'opencc',
]

# 需要排除的大模块（减小体积）
excludes = [
    'matplotlib', 'numpy', 'scipy', 'pandas',
    'PyQt5', 'PyQt6', 'PySide2', 'PySide6',
    'notebook', 'IPython',
]

a = Analysis(
    ['poetry_desktop.py'],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[],
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='诗韵',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,      # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='诗韵',
)
