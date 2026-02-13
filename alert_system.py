"""
股票分析系统的预警系统模块
支持价格突破、技术指标信号等预警功能
"""

import json
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import threading
import time

# 预警数据文件路径
ALERTS_FILE = "alerts.json"
FAVORITES_FILE = "favorites.json"

class AlertSystem:
    def __init__(self):
        self.alerts = self.load_alerts()
        self.favorites = self.load_favorites()
        self.running = False
        self.monitor_thread = None
        
    def load_alerts(self) -> List[Dict[str, Any]]:
        """加载预警配置"""
        try:
            if os.path.exists(ALERTS_FILE):
                with open(ALERTS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
        except Exception as e:
            print(f"加载预警配置失败: {e}")
            return []
    
    def save_alerts(self):
        """保存预警配置"""
        try:
            with open(ALERTS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.alerts, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存预警配置失败: {e}")
    
    def load_favorites(self) -> Dict[str, Any]:
        """加载收藏夹数据"""
        try:
            if os.path.exists(FAVORITES_FILE):
                with open(FAVORITES_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"groups": {}, "default": []}
        except Exception as e:
            print(f"加载收藏夹失败: {e}")
            return {"groups": {}, "default": []}
    
    def save_favorites(self):
        """保存收藏夹数据"""
        try:
            with open(FAVORITES_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.favorites, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存收藏夹失败: {e}")
    
    def add_price_alert(self, symbol: str, alert_type: str, price: float, 
                       notification_method: str = "web") -> Dict[str, Any]:
        """
        添加价格预警
        
        Args:
            symbol: 股票代码
            alert_type: 预警类型 ("above", "below", "cross")
            price: 预警价格
            notification_method: 通知方式 ("web", "email", "sms")
        """
        alert_id = f"price_{symbol}_{alert_type}_{int(time.time())}"
        alert = {
            "id": alert_id,
            "type": "price",
            "symbol": symbol,
            "alert_type": alert_type,
            "price": price,
            "notification_method": notification_method,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "triggered": False,
            "last_checked": None
        }
        
        self.alerts.append(alert)
        self.save_alerts()
        return alert
    
    def add_technical_alert(self, symbol: str, indicator: str, condition: str, 
                           threshold: float, notification_method: str = "web") -> Dict[str, Any]:
        """
        添加技术指标预警
        
        Args:
            symbol: 股票代码
            indicator: 技术指标 ("rsi", "macd", "bollinger", "volume")
            condition: 条件 ("above", "below", "cross_up", "cross_down")
            threshold: 阈值
            notification_method: 通知方式
        """
        alert_id = f"tech_{symbol}_{indicator}_{int(time.time())}"
        alert = {
            "id": alert_id,
            "type": "technical",
            "symbol": symbol,
            "indicator": indicator,
            "condition": condition,
            "threshold": threshold,
            "notification_method": notification_method,
            "created_at": datetime.now().isoformat(),
            "active": True,
            "triggered": False,
            "last_checked": None
        }
        
        self.alerts.append(alert)
        self.save_alerts()
        return alert
    
    def remove_alert(self, alert_id: str) -> bool:
        """移除预警"""
        for i, alert in enumerate(self.alerts):
            if alert["id"] == alert_id:
                del self.alerts[i]
                self.save_alerts()
                return True
        return False
    
    def get_active_alerts(self, symbol: str = None) -> List[Dict[str, Any]]:
        """获取活跃的预警"""
        active_alerts = [alert for alert in self.alerts if alert["active"] and not alert["triggered"]]
        if symbol:
            active_alerts = [alert for alert in active_alerts if alert["symbol"] == symbol]
        return active_alerts
    
    def check_price_alert(self, alert: Dict[str, Any], current_price: float) -> bool:
        """检查价格预警是否触发"""
        if alert["alert_type"] == "above":
            return current_price >= alert["price"]
        elif alert["alert_type"] == "below":
            return current_price <= alert["price"]
        elif alert["alert_type"] == "cross":
            # 检查是否穿越价格（需要历史数据，这里简化处理）
            return abs(current_price - alert["price"]) < (current_price * 0.01)  # 1%范围内
        return False
    
    def check_technical_alert(self, alert: Dict[str, Any], indicators: Dict[str, Any]) -> bool:
        """检查技术指标预警是否触发"""
        indicator_value = indicators.get(alert["indicator"])
        if indicator_value is None:
            return False
            
        if alert["condition"] == "above":
            return indicator_value >= alert["threshold"]
        elif alert["condition"] == "below":
            return indicator_value <= alert["threshold"]
        elif alert["condition"] == "cross_up":
            # 需要历史数据来判断穿越，这里简化处理
            return indicator_value >= alert["threshold"]
        elif alert["condition"] == "cross_down":
            return indicator_value <= alert["threshold"]
            
        return False
    
    def trigger_alert(self, alert: Dict[str, Any], current_data: Dict[str, Any]) -> Dict[str, Any]:
        """触发预警"""
        alert["triggered"] = True
        alert["triggered_at"] = datetime.now().isoformat()
        alert["trigger_data"] = current_data
        
        # 生成预警消息
        message = self.generate_alert_message(alert, current_data)
        alert["message"] = message
        
        self.save_alerts()
        return alert
    
    def generate_alert_message(self, alert: Dict[str, Any], current_data: Dict[str, Any]) -> str:
        """生成预警消息"""
        symbol = alert["symbol"]
        current_price = current_data.get("current_price", 0)
        
        if alert["type"] == "price":
            if alert["alert_type"] == "above":
                return f"{symbol} 股价已上涨至 ${current_price:.2f}，超过预警价格 ${alert['price']:.2f}"
            elif alert["alert_type"] == "below":
                return f"{symbol} 股价已下跌至 ${current_price:.2f}，低于预警价格 ${alert['price']:.2f}"
            else:
                return f"{symbol} 股价 ${current_price:.2f} 触发价格预警"
        else:
            indicator_name = {
                "rsi": "RSI",
                "macd": "MACD",
                "bollinger": "布林带",
                "volume": "成交量"
            }.get(alert["indicator"], alert["indicator"])
            
            return f"{symbol} {indicator_name} 指标触发预警: 当前值 {current_data.get(alert['indicator'], 'N/A')}"
    
    def get_triggered_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """获取已触发的预警（最近的）"""
        triggered = [alert for alert in self.alerts if alert["triggered"]]
        # 按触发时间排序，最新的在前
        triggered.sort(key=lambda x: x.get("triggered_at", ""), reverse=True)
        return triggered[:limit]
    
    def clear_triggered_alerts(self, before_date: str = None):
        """清除已触发的预警"""
        if before_date:
            # 清除指定日期之前的预警
            new_alerts = []
            for alert in self.alerts:
                if not alert["triggered"]:
                    new_alerts.append(alert)
                elif alert.get("triggered_at", "") > before_date:
                    new_alerts.append(alert)
            self.alerts = new_alerts
        else:
            # 清除所有已触发的预警
            self.alerts = [alert for alert in self.alerts if not alert["triggered"]]
        
        self.save_alerts()
    
    # 收藏夹管理方法
    def add_to_favorites(self, symbol: str, group: str = "default", name: str = "") -> bool:
        """添加到收藏夹"""
        if group == "default":
            if symbol not in self.favorites["default"]:
                self.favorites["default"].append(symbol)
                self.save_favorites()
                return True
        else:
            if group not in self.favorites["groups"]:
                self.favorites["groups"][group] = []
            if symbol not in self.favorites["groups"][group]:
                self.favorites["groups"][group].append(symbol)
                self.save_favorites()
                return True
        return False
    
    def remove_from_favorites(self, symbol: str, group: str = "default") -> bool:
        """从收藏夹移除"""
        if group == "default":
            if symbol in self.favorites["default"]:
                self.favorites["default"].remove(symbol)
                self.save_favorites()
                return True
        else:
            if group in self.favorites["groups"] and symbol in self.favorites["groups"][group]:
                self.favorites["groups"][group].remove(symbol)
                self.save_favorites()
                return True
        return False
    
    def create_favorite_group(self, group_name: str) -> bool:
        """创建收藏夹分组"""
        if group_name not in self.favorites["groups"]:
            self.favorites["groups"][group_name] = []
            self.save_favorites()
            return True
        return False
    
    def delete_favorite_group(self, group_name: str) -> bool:
        """删除收藏夹分组"""
        if group_name in self.favorites["groups"]:
            del self.favorites["groups"][group_name]
            self.save_favorites()
            return True
        return False
    
    def rename_favorite_group(self, old_name: str, new_name: str) -> bool:
        """重命名收藏夹分组"""
        if old_name in self.favorites["groups"] and new_name not in self.favorites["groups"]:
            self.favorites["groups"][new_name] = self.favorites["groups"][old_name]
            del self.favorites["groups"][old_name]
            self.save_favorites()
            return True
        return False
    
    def get_favorites(self, group: str = None) -> Dict[str, Any]:
        """获取收藏夹数据"""
        if group is None:
            return self.favorites
        elif group == "default":
            return {"symbols": self.favorites["default"]}
        elif group in self.favorites["groups"]:
            return {"symbols": self.favorites["groups"][group]}
        else:
            return {"symbols": []}
    
    def get_all_favorite_symbols(self) -> List[str]:
        """获取所有收藏的股票代码"""
        all_symbols = set(self.favorites["default"])
        for group_symbols in self.favorites["groups"].values():
            all_symbols.update(group_symbols)
        return list(all_symbols)

# 全局预警系统实例
alert_system = AlertSystem()

def start_alert_monitoring():
    """启动预警监控（后台线程）"""
    if alert_system.running:
        return
    
    alert_system.running = True
    
    def monitor_loop():
        while alert_system.running:
            try:
                # 这里应该定期检查预警，但由于是Web应用，
                # 实际的监控会在API调用时进行
                time.sleep(60)  # 每分钟检查一次
            except Exception as e:
                print(f"预警监控错误: {e}")
                time.sleep(60)
    
    alert_system.monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
    alert_system.monitor_thread.start()

def stop_alert_monitoring():
    """停止预警监控"""
    alert_system.running = False
    if alert_system.monitor_thread:
        alert_system.monitor_thread.join(timeout=5)

# 应用关闭时清理
import atexit
atexit.register(stop_alert_monitoring)