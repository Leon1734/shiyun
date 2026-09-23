#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一搜索模块
同时搜索诗词 + 古文 + 诗人
"""

import sqlite3
import logging

try:
    from famous_authors import author_rank
except ImportError:
    def author_rank(a):
        return 0
from pathlib import Path

log = logging.getLogger("poetry")

try:
    from app_paths import get_db_path
    DB_PATH = get_db_path()
except ImportError:
    DB_PATH = Path(__file__).parent / "data" / "poetry.db"


class UnifiedSearch:
    """统一搜索（诗词+古文+诗人）"""
    
    def __init__(self, db_path=None):
        self.db_path = Path(db_path) if db_path else DB_PATH
        self._conn = None
    
    def _get_conn(self):
        if self._conn is None:
            self._conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
        return self._conn
    
    def search_all(self, keyword, limit=30):
        """
        统一搜索
        
        Returns:
            dict: {
                'poems': [...],    # 诗词结果
                'guwen': [...],    # 古文结果
                'authors': [...],  # 诗人结果
                'total': int
            }
        """
        keyword = keyword.strip()
        if not keyword:
            return {'poems': [], 'guwen': [], 'authors': [], 'total': 0}
        
        results = {'poems': [], 'guwen': [], 'authors': [], 'total': 0}
        
        try:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # 1. 诗词搜索（LIKE + 经典度优先排序）
            cursor.execute('''
                SELECT id, title, author, dynasty, collection, poem_form,
                       substr(content, 1, 100) as preview
                FROM poems
                WHERE title LIKE ? OR author LIKE ? OR content LIKE ?
                ORDER BY classic_score DESC, id
                LIMIT ?
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
            
            for r in cursor.fetchall():
                results['poems'].append({
                    'id': r[0], 'title': r[1], 'author': r[2],
                    'dynasty': r[3], 'collection': r[4], 'poem_form': r[5],
                    'preview': r[6]
                })
            
            # 2. 古文搜索（LIKE）
            cursor.execute('''
                SELECT id, title, author, dynasty, collection,
                       substr(content, 1, 100) as preview
                FROM guwen
                WHERE title LIKE ? OR author LIKE ? OR content LIKE ?
                LIMIT ?
            ''', (f'%{keyword}%', f'%{keyword}%', f'%{keyword}%', limit))
            
            for r in cursor.fetchall():
                results['guwen'].append({
                    'id': r[0], 'title': r[1], 'author': r[2],
                    'dynasty': r[3], 'collection': r[4],
                    'preview': r[5]
                })
            
            # 3. 诗人搜索（作者名匹配，著名诗人优先）
            cursor.execute('''
                SELECT author, dynasty, COUNT(*) as cnt FROM poems
                WHERE author LIKE ?
                GROUP BY author ORDER BY cnt DESC LIMIT 30
            ''', (f'%{keyword}%',))
            
            rows = cursor.fetchall()
            rows = sorted(rows, key=lambda r: (-author_rank(r[0]), -r[2]))
            for r in rows[:10]:
                results['authors'].append({
                    'author': r[0], 'dynasty': r[1], 'count': r[2]
                })
            
            results['total'] = len(results['poems']) + len(results['guwen']) + len(results['authors'])
            
        except Exception as e:
            log.error(f"统一搜索失败: {e}")
        
        return results


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("=== 统一搜索测试 ===")
    searcher = UnifiedSearch()
    
    results = searcher.search_all("明月")
    print(f"搜索'明月':")
    print(f"  诗词: {len(results['poems'])} 条")
    print(f"  古文: {len(results['guwen'])} 条")
    print(f"  诗人: {len(results['authors'])} 位")
    print(f"  总计: {results['total']}")
    print()
    
    if results['poems']:
        print(f"  诗词首条: 《{results['poems'][0]['title']}》{results['poems'][0]['author']}")
    
    results2 = searcher.search_all("岳阳楼")
    print()
    print(f"搜索'岳阳楼':")
    print(f"  诗词: {len(results2['poems'])} 条, 古文: {len(results2['guwen'])} 条")
    if results2['guwen']:
        print(f"  古文首条: 《{results2['guwen'][0]['title']}》{results2['guwen'][0]['author']}")
