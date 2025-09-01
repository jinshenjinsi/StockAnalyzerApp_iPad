import time

# 简易内存缓存：key=(market), value={"ts": timestamp, "rows": list}
ranking_cache = {}

def get_symbols(market_code):
    """获取不同市场的股票代码列表"""
    symbols = []
    try:
        import akshare as ak
        if market_code == "CN":
            df = ak.stock_zh_a_spot_em()
            if not df.empty and '代码' in df.columns:
                symbols = df['代码'].astype(str).tolist()
        elif market_code == "HK":
            df = ak.stock_hk_spot_em()
            if not df.empty and '代码' in df.columns:
                symbols = df['代码'].astype(str).tolist()
    except Exception as e:
        print(f"获取{market_code}市场代码失败: {e}")
        pass
    
    if market_code == "US":
        symbols = [
            "AAPL","MSFT","GOOGL","AMZN","META","NVDA","TSLA","BRK-B","JPM","V",
            "JNJ","WMT","PG","XOM","MA","AVGO","HD","LLY","ORCL","KO"
        ]
    
    # 限量以控制请求与限流
    if market_code in ("CN", "HK"):
        symbols = symbols[:30]  # A股和港股限制30个
    else:
        symbols = symbols[:15]  # 美股限制15个
    
    return symbols

def get_ranking_rows(market, analyze_stock_func):
    """获取排名数据"""
    # 10分钟缓存
    now = time.time()
    cached = ranking_cache.get(market)
    if cached and now - cached.get("ts", 0) < 600 and cached.get("rows"):
        return cached["rows"]

    symbols = get_symbols(market)
    if not symbols:
        print(f"无法获取{market}市场的股票代码")
        return []

    rows = []
    for sym in symbols:
        try:
            # 使用与主分析完全相同的逻辑
            r = analyze_stock_func(sym)
            # 验证数据一致性：确保百分比计算正确
            if r.get("last_price") and r.get("resistance"):
                calculated_pct = round((r["resistance"] / r["last_price"] - 1) * 100, 2)
                # 如果计算值与返回值不一致，使用计算值
                if abs(calculated_pct - r.get("resistance_pct", 0)) > 0.01:
                    print(f"数据不一致修复 {sym}: 原值={r.get('resistance_pct')}, 计算值={calculated_pct}")
                    r["resistance_pct"] = calculated_pct
                
            rows.append({
                "symbol": r["symbol"],
                "name": r.get("name") or "-",  # 确保名称不为None
                "last_price": r["last_price"],
                "resistance": r["resistance"],
                "resistance_pct": r["resistance_pct"],
                "source": r["source"],
            })
        except Exception as e:
            print(f"排名数据获取失败 {sym}: {e}")
            continue
        
        # 成功之间小幅节流，降低限流概率
        time.sleep(0.3)
        if len(rows) >= 10:
            break

    rows = sorted(rows, key=lambda x: x["resistance_pct"], reverse=True)[:10]
    ranking_cache[market] = {"ts": now, "rows": rows}
    print(f"{market}市场排名生成完成，共{len(rows)}条数据")
    return rows

