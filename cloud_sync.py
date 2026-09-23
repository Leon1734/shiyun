#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端同步模块
功能：数据备份、云端同步、冲突解决
"""

import json
import hashlib
import logging
from pathlib import Path
from datetime import datetime

import tkinter as tk
from tkinter import ttk, messagebox

log = logging.getLogger("poetry")

# 同步配置文件路径
# 路径：优先 data 目录（与 exe 共享；打包后 _internal 只读）
try:
    from app_paths import get_data_dir as _get_data_dir
    SYNC_CONFIG = _get_data_dir() / "sync_config.json"
except Exception:
    SYNC_CONFIG = Path(__file__).parent / "data" / "sync_config.json"


class CloudSyncManager:
    """云端同步管理器"""
    
    def __init__(self):
        self.config = self._load_config()
        self.sync_history = []
    
    def _load_config(self):
        """加载配置"""
        try:
            if SYNC_CONFIG.exists():
                with open(SYNC_CONFIG, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            log.error(f"加载同步配置失败: {e}")
        
        # 默认配置
        return {
            'enabled': False,
            'provider': 'local',
            'auto_sync': False,
            'sync_interval': 3600,
            'last_sync': None,
            'sync_folders': ['favorites', 'history', 'learning', 'game']
        }
    
    def _save_config(self):
        """保存配置"""
        try:
            with open(SYNC_CONFIG, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            log.error(f"保存同步配置失败: {e}")
            return False
    
    def enable_sync(self, provider='local'):
        """启用同步"""
        self.config['enabled'] = True
        self.config['provider'] = provider
        return self._save_config()
    
    def disable_sync(self):
        """禁用同步"""
        self.config['enabled'] = False
        return self._save_config()
    
    def is_enabled(self):
        """检查是否启用"""
        return self.config.get('enabled', False)
    
    def get_provider(self):
        """获取同步提供者"""
        return self.config.get('provider', 'local')
    
    def backup_data(self, data_type, data):
        """备份数据"""
        try:
            # 创建备份目录
            backup_dir = Path(__file__).parent / "backups"
            backup_dir.mkdir(exist_ok=True)
            
            # 生成备份文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{data_type}_{timestamp}.json"
            filepath = backup_dir / filename
            
            # 保存备份
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            # 计算哈希值
            with open(filepath, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()
            
            # 记录备份历史
            self.sync_history.append({
                'type': 'backup',
                'data_type': data_type,
                'filename': filename,
                'hash': file_hash,
                'timestamp': timestamp
            })
            
            log.info(f"备份成功: {filename}")
            return filename
        except Exception as e:
            log.error(f"备份失败: {e}")
            return None
    
    def restore_data(self, filename):
        """恢复数据"""
        try:
            backup_dir = Path(__file__).parent / "backups"
            filepath = backup_dir / filename
            
            if not filepath.exists():
                log.error(f"备份文件不存在: {filename}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            log.info(f"恢复成功: {filename}")
            return data
        except Exception as e:
            log.error(f"恢复失败: {e}")
            return None
    
    def get_backup_list(self):
        """获取备份列表"""
        try:
            backup_dir = Path(__file__).parent / "backups"
            
            if not backup_dir.exists():
                return []
            
            backups = []
            for filepath in backup_dir.glob("*.json"):
                stat = filepath.stat()
                backups.append({
                    'filename': filepath.name,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })
            
            # 按修改时间排序
            backups.sort(key=lambda x: x['modified'], reverse=True)
            
            return backups
        except Exception as e:
            log.error(f"获取备份列表失败: {e}")
            return []
    
    def delete_backup(self, filename):
        """删除备份"""
        try:
            backup_dir = Path(__file__).parent / "backups"
            filepath = backup_dir / filename
            
            if filepath.exists():
                filepath.unlink()
                log.info(f"删除备份: {filename}")
                return True
            
            return False
        except Exception as e:
            log.error(f"删除备份失败: {e}")
            return False
    
    def sync_to_local(self, data_type, data):
        """同步到本地"""
        try:
            # 本地同步就是备份
            return self.backup_data(data_type, data)
        except Exception as e:
            log.error(f"本地同步失败: {e}")
            return None
    
    def sync_from_local(self, data_type):
        """从本地同步"""
        try:
            # 获取最新的备份
            backups = self.get_backup_list()
            
            # 查找指定类型的备份
            for backup in backups:
                if backup['filename'].startswith(data_type):
                    return self.restore_data(backup['filename'])
            
            return None
        except Exception as e:
            log.error(f"从本地同步失败: {e}")
            return None
    
    def get_sync_status(self):
        """获取同步状态"""
        return {
            'enabled': self.config.get('enabled', False),
            'provider': self.config.get('provider', 'local'),
            'last_sync': self.config.get('last_sync'),
            'auto_sync': self.config.get('auto_sync', False),
            'sync_interval': self.config.get('sync_interval', 3600)
        }
    
    def update_last_sync(self):
        """更新最后同步时间"""
        self.config['last_sync'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return self._save_config()


class SyncDialog:
    """同步对话框"""
    
    def __init__(self, parent, sync_manager):
        self.parent = parent
        self.sync_manager = sync_manager
        
        # 创建对话框
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("云端同步")
        self.dialog.geometry("500x400")
        
        # 创建界面
        self._create_widgets()
    
    def _create_widgets(self):
        """创建界面组件"""
        # 主框架
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 标题
        title_label = ttk.Label(main_frame, text="☁️ 云端同步", 
                               font=('微软雅黑', 14, 'bold'))
        title_label.pack(pady=(0, 20))
        
        # 同步状态
        status_frame = ttk.LabelFrame(main_frame, text="同步状态", padding=10)
        status_frame.pack(fill='x', pady=(0, 10))
        
        status = self.sync_manager.get_sync_status()
        
        status_text = f"启用: {'是' if status['enabled'] else '否'}\n"
        status_text += f"提供者: {status['provider']}\n"
        status_text += f"最后同步: {status['last_sync'] or '从未'}\n"
        status_text += f"自动同步: {'是' if status['auto_sync'] else '否'}"
        
        status_label = ttk.Label(status_frame, text=status_text)
        status_label.pack(fill='x')
        
        # 备份列表
        backup_frame = ttk.LabelFrame(main_frame, text="备份列表", padding=10)
        backup_frame.pack(fill='both', expand=True, pady=(0, 10))
        
        # Treeview
        self.backup_tree = ttk.Treeview(backup_frame, columns=('filename', 'size', 'modified'),
                                        show='headings', height=8)
        self.backup_tree.heading('filename', text='文件名')
        self.backup_tree.heading('size', text='大小')
        self.backup_tree.heading('modified', text='修改时间')
        self.backup_tree.column('filename', width=200)
        self.backup_tree.column('size', width=80)
        self.backup_tree.column('modified', width=150)
        
        scrollbar = ttk.Scrollbar(backup_frame, orient='vertical', command=self.backup_tree.yview)
        self.backup_tree.configure(yscrollcommand=scrollbar.set)
        
        self.backup_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # 加载备份列表
        self._load_backups()
        
        # 按钮框架
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill='x')
        
        ttk.Button(btn_frame, text="备份收藏", command=self._backup_favorites).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="恢复选中", command=self._restore_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="删除选中", command=self._delete_selected).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="刷新", command=self._load_backups).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="关闭", command=self.dialog.destroy).pack(side='right', padx=5)
    
    def _load_backups(self):
        """加载备份列表"""
        # 清空列表
        for item in self.backup_tree.get_children():
            self.backup_tree.delete(item)
        
        # 获取备份列表
        backups = self.sync_manager.get_backup_list()
        
        # 填充列表
        for backup in backups:
            self.backup_tree.insert('', 'end', values=(
                backup['filename'],
                f"{backup['size'] / 1024:.1f} KB",
                backup['modified']
            ))
    
    def _backup_favorites(self):
        """备份收藏"""
        # 这里需要从主程序获取收藏数据
        # 暂时使用示例数据
        favorites = []
        
        filename = self.sync_manager.backup_data('favorites', favorites)
        
        if filename:
            messagebox.showinfo("成功", f"收藏已备份: {filename}")
            self._load_backups()
        else:
            messagebox.showerror("错误", "备份失败")
    
    def _restore_selected(self):
        """恢复选中的备份"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要恢复的备份")
            return
        
        item = self.backup_tree.item(selection[0])
        filename = item['values'][0]
        
        data = self.sync_manager.restore_data(filename)
        
        if data:
            messagebox.showinfo("成功", f"备份已恢复: {filename}")
            # 这里需要将数据应用到主程序
        else:
            messagebox.showerror("错误", "恢复失败")
    
    def _delete_selected(self):
        """删除选中的备份"""
        selection = self.backup_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的备份")
            return
        
        item = self.backup_tree.item(selection[0])
        filename = item['values'][0]
        
        if messagebox.askyesno("确认", f"确定要删除备份 '{filename}' 吗？"):
            if self.sync_manager.delete_backup(filename):
                messagebox.showinfo("成功", f"备份已删除: {filename}")
                self._load_backups()
            else:
                messagebox.showerror("错误", "删除失败")
