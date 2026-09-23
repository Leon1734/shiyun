#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
路径解析模块
支持开发环境和 PyInstaller 打包后的 exe 环境
"""

import sys
from pathlib import Path


def is_frozen():
    """是否运行在打包环境中"""
    return getattr(sys, 'frozen', False)


def get_base_dir():
    """获取应用基础目录"""
    if is_frozen():
        # PyInstaller 打包环境：exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发环境：脚本所在目录
        return Path(__file__).parent


def get_data_dir():
    """获取数据目录（优先 exe 同级的 data 目录）"""
    base = get_base_dir()
    
    # 1. exe 同级的 data 目录
    data_dir = base / "data"
    if (data_dir / "poetry.db").exists():
        return data_dir
    
    # 2. PyInstaller 内部解包目录
    if is_frozen():
        meipass = Path(getattr(sys, '_MEIPASS', base))
        data_dir = meipass / "data"
        if (data_dir / "poetry.db").exists():
            return data_dir
    
    # 3. 开发目录回退
    return Path(__file__).parent / "data"


def get_db_path():
    """获取数据库路径"""
    return get_data_dir() / "poetry.db"


if __name__ == "__main__":
    print(f"frozen: {is_frozen()}")
    print(f"base_dir: {get_base_dir()}")
    print(f"data_dir: {get_data_dir()}")
    print(f"db_path: {get_db_path()}")
    print(f"db exists: {get_db_path().exists()}")
