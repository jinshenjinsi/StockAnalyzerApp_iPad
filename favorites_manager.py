"""
收藏夹管理模块 - 自选股分组和管理功能
支持用户创建、编辑、删除自选股分组，并管理组内的股票
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class FavoritesManager:
    """收藏夹管理器"""
    
    def __init__(self, data_dir: str = "data"):
        """
        初始化收藏夹管理器
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.favorites_file = os.path.join(data_dir, "favorites.json")
        
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 加载现有数据
        self.favorites_data = self._load_favorites()
    
    def _load_favorites(self) -> Dict:
        """加载收藏夹数据"""
        if os.path.exists(self.favorites_file):
            try:
                with open(self.favorites_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"⚠️  警告: 收藏夹数据加载失败，使用默认数据: {e}")
                return self._get_default_favorites()
        else:
            return self._get_default_favorites()
    
    def _get_default_favorites(self) -> Dict:
        """获取默认收藏夹数据"""
        return {
            "groups": {
                "default": {
                    "name": "默认分组",
                    "description": "系统默认分组",
                    "stocks": [],
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
            },
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_favorites(self) -> bool:
        """保存收藏夹数据"""
        try:
            self.favorites_data["last_updated"] = datetime.now().isoformat()
            with open(self.favorites_file, 'w', encoding='utf-8') as f:
                json.dump(self.favorites_data, f, ensure_ascii=False, indent=2)
            return True
        except IOError as e:
            print(f"❌ 错误: 收藏夹数据保存失败: {e}")
            return False
    
    def create_group(self, group_id: str, name: str, description: str = "") -> bool:
        """
        创建新的收藏夹分组
        
        Args:
            group_id: 分组ID（唯一标识符）
            name: 分组名称
            description: 分组描述
            
        Returns:
            bool: 创建是否成功
        """
        if not group_id or not name:
            return False
        
        if group_id in self.favorites_data["groups"]:
            print(f"⚠️  警告: 分组 {group_id} 已存在")
            return False
        
        self.favorites_data["groups"][group_id] = {
            "name": name,
            "description": description,
            "stocks": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return self._save_favorites()
    
    def delete_group(self, group_id: str) -> bool:
        """
        删除收藏夹分组
        
        Args:
            group_id: 分组ID
            
        Returns:
            bool: 删除是否成功
        """
        if group_id not in self.favorites_data["groups"]:
            return False
        
        # 不能删除默认分组
        if group_id == "default":
            print("⚠️  警告: 不能删除默认分组")
            return False
        
        del self.favorites_data["groups"][group_id]
        return self._save_favorites()
    
    def update_group(self, group_id: str, name: str = None, description: str = None) -> bool:
        """
        更新收藏夹分组信息
        
        Args:
            group_id: 分组ID
            name: 新的分组名称（可选）
            description: 新的分组描述（可选）
            
        Returns:
            bool: 更新是否成功
        """
        if group_id not in self.favorites_data["groups"]:
            return False
        
        if name is not None:
            self.favorites_data["groups"][group_id]["name"] = name
        if description is not None:
            self.favorites_data["groups"][group_id]["description"] = description
        
        self.favorites_data["groups"][group_id]["updated_at"] = datetime.now().isoformat()
        return self._save_favorites()
    
    def add_stock_to_group(self, group_id: str, symbol: str, name: str = "", note: str = "") -> bool:
        """
        向分组中添加股票
        
        Args:
            group_id: 分组ID
            symbol: 股票代码
            name: 股票名称（可选）
            note: 备注信息（可选）
            
        Returns:
            bool: 添加是否成功
        """
        if group_id not in self.favorites_data["groups"]:
            return False
        
        # 检查股票是否已存在
        existing_stock = None
        for stock in self.favorites_data["groups"][group_id]["stocks"]:
            if stock["symbol"] == symbol:
                existing_stock = stock
                break
        
        if existing_stock:
            # 更新现有股票信息
            if name:
                existing_stock["name"] = name
            if note:
                existing_stock["note"] = note
            existing_stock["updated_at"] = datetime.now().isoformat()
        else:
            # 添加新股票
            new_stock = {
                "symbol": symbol,
                "name": name or symbol,
                "note": note,
                "added_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            self.favorites_data["groups"][group_id]["stocks"].append(new_stock)
        
        self.favorites_data["groups"][group_id]["updated_at"] = datetime.now().isoformat()
        return self._save_favorites()
    
    def remove_stock_from_group(self, group_id: str, symbol: str) -> bool:
        """
        从分组中移除股票
        
        Args:
            group_id: 分组ID
            symbol: 股票代码
            
        Returns:
            bool: 移除是否成功
        """
        if group_id not in self.favorites_data["groups"]:
            return False
        
        stocks = self.favorites_data["groups"][group_id]["stocks"]
        initial_count = len(stocks)
        self.favorites_data["groups"][group_id]["stocks"] = [
            stock for stock in stocks if stock["symbol"] != symbol
        ]
        
        if len(self.favorites_data["groups"][group_id]["stocks"]) < initial_count:
            self.favorites_data["groups"][group_id]["updated_at"] = datetime.now().isoformat()
            return self._save_favorites()
        
        return False
    
    def get_all_groups(self) -> Dict:
        """
        获取所有收藏夹分组
        
        Returns:
            Dict: 所有分组信息
        """
        return self.favorites_data["groups"]
    
    def get_group_stocks(self, group_id: str) -> List[Dict]:
        """
        获取指定分组的股票列表
        
        Args:
            group_id: 分组ID
            
        Returns:
            List[Dict]: 股票列表
        """
        if group_id not in self.favorites_data["groups"]:
            return []
        
        return self.favorites_data["groups"][group_id]["stocks"]
    
    def get_stock_groups(self, symbol: str) -> List[str]:
        """
        获取包含指定股票的所有分组ID
        
        Args:
            symbol: 股票代码
            
        Returns:
            List[str]: 分组ID列表
        """
        groups = []
        for group_id, group_data in self.favorites_data["groups"].items():
            for stock in group_data["stocks"]:
                if stock["symbol"] == symbol:
                    groups.append(group_id)
                    break
        return groups
    
    def search_stocks(self, keyword: str) -> List[Dict]:
        """
        在所有收藏夹中搜索股票
        
        Args:
            keyword: 搜索关键词（股票代码或名称）
            
        Returns:
            List[Dict]: 匹配的股票信息
        """
        results = []
        keyword_lower = keyword.lower()
        
        for group_id, group_data in self.favorites_data["groups"].items():
            for stock in group_data["stocks"]:
                if (keyword_lower in stock["symbol"].lower() or 
                    keyword_lower in stock["name"].lower()):
                    stock_copy = stock.copy()
                    stock_copy["group_id"] = group_id
                    stock_copy["group_name"] = group_data["name"]
                    results.append(stock_copy)
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        获取收藏夹统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_groups = len(self.favorites_data["groups"])
        total_stocks = 0
        group_stats = {}
        
        for group_id, group_data in self.favorites_data["groups"].items():
            stock_count = len(group_data["stocks"])
            total_stocks += stock_count
            group_stats[group_id] = {
                "name": group_data["name"],
                "stock_count": stock_count,
                "created_at": group_data["created_at"],
                "updated_at": group_data["updated_at"]
            }
        
        return {
            "total_groups": total_groups,
            "total_stocks": total_stocks,
            "groups": group_stats,
            "last_updated": self.favorites_data["last_updated"]
        }

# 全局收藏夹管理器实例
favorites_manager = FavoritesManager()

def get_favorites_manager() -> FavoritesManager:
    """获取全局收藏夹管理器实例"""
    return favorites_manager

# 便捷函数
def create_favorite_group(group_id: str, name: str, description: str = "") -> bool:
    """创建收藏夹分组的便捷函数"""
    return favorites_manager.create_group(group_id, name, description)

def add_stock_to_favorites(symbol: str, name: str = "", note: str = "", group_id: str = "default") -> bool:
    """向收藏夹添加股票的便捷函数"""
    return favorites_manager.add_stock_to_group(group_id, symbol, name, note)

def get_all_favorites() -> Dict:
    """获取所有收藏夹数据的便捷函数"""
    return favorites_manager.get_all_groups()

def get_favorites_statistics() -> Dict:
    """获取收藏夹统计信息的便捷函数"""
    return favorites_manager.get_statistics()