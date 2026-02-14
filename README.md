# 🦐 无敌股票分析系统

一个功能完整的股票分析平台，集成了技术分析、机器学习预测、情绪分析和策略回测。

## 🚀 功能特性

### Phase 1 ✅ 基础架构优化
- 100%真实数据源集成
- 统一代码架构
- 安全增强（环境变量API密钥）
- 性能优化（缓存机制）
- 移动友好设计

### Phase 2 ✅ 高级技术分析
- **技术指标**: MACD、RSI、布林带等
- **智能提醒系统**: 价格和技术指标条件触发
- **收藏管理**: 用户股票收藏和分组
- **完整前端界面**: 响应式设计

### Phase 3 🔧 高级分析功能
- **机器学习预测**: LSTM时间序列预测模型
- **市场情绪分析**: 新闻和社交媒体情绪监控
- **策略回测引擎**: 多策略历史性能测试
- **统一API接口**: RESTful API设计
- **性能监控**: 实时系统性能跟踪

## 📋 安装部署

### 环境要求
- Python 3.6+
- pip包管理器

### 安装步骤
```bash
# 克隆仓库
git clone https://github.com/jinshenjinsi/StockAnalyzerApp_iPad.git
cd StockAnalyzerApp_iPad

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入您的API密钥

# 启动应用
./start_app.command
```

## 🎯 使用方法

### Web界面
访问 `http://localhost:5000` 使用完整的Web界面。

### API接口
- `GET /api/stock/{symbol}` - 获取股票数据和技术指标
- `GET /api/sentiment/{symbol}` - 获取市场情绪分析
- `POST /api/backtest` - 运行策略回测
- `GET /api/favorites` - 获取收藏列表
- `POST /api/alerts` - 设置价格提醒

## 🔧 配置文件

### config.py
主配置文件，支持环境变量覆盖。

### 环境变量
- `STOCK_API_KEY` - 股票数据API密钥
- `NEWSAPI_KEY` - 新闻API密钥  
- `TWITTER_BEARER_TOKEN` - Twitter API密钥
- `DATABASE_URL` - 数据库连接URL

## 📊 技术栈

- **后端**: Python Flask
- **前端**: HTML5, Bootstrap 5, JavaScript
- **机器学习**: TensorFlow/Keras, Scikit-learn
- **数据处理**: Pandas, NumPy
- **缓存**: Redis (可选)
- **部署**: Docker支持

## 🚨 注意事项

1. **API密钥**: 请确保在 `.env` 文件中配置所有必要的API密钥
2. **数据源**: 系统支持多个数据源，可在配置中切换
3. **性能**: ML模型训练可能需要较长时间，建议使用GPU加速
4. **安全**: 生产环境请使用HTTPS和适当的认证机制

## 📈 路线图

- [x] Phase 1: 基础架构优化
- [x] Phase 2: 高级技术分析  
- [x] Phase 3: 机器学习和情绪分析
- [ ] Phase 4: 实时交易集成
- [ ] Phase 5: 移动应用版本

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📜 许可证

MIT License

---

**🦐 无敌的股票分析系统 - 让投资决策更智能！**