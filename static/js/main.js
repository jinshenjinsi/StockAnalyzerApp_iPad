// Main JavaScript for Stock Analyzer App
class StockAnalyzer {
    constructor() {
        this.baseUrl = '/api';
        this.initEventListeners();
    }
    
    initEventListeners() {
        // Handle form submissions
        this.handleFormSubmissions();
        
        // Handle navigation
        this.handleNavigation();
        
        // Initialize charts if Chart.js is available
        if (typeof Chart !== 'undefined') {
            this.initCharts();
        }
    }
    
    handleFormSubmissions() {
        // Stock search form
        const stockForm = document.getElementById('stock-form');
        if (stockForm) {
            stockForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const symbol = document.getElementById('stock-symbol').value.toUpperCase();
                await this.loadStockData(symbol);
            });
        }
        
        // Sentiment analysis form
        const sentimentForm = document.getElementById('sentiment-form');
        if (sentimentForm) {
            sentimentForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                const symbol = document.getElementById('symbol').value.toUpperCase();
                await this.loadSentimentData(symbol);
            });
        }
        
        // Backtest form
        const backtestForm = document.getElementById('backtest-form');
        if (backtestForm) {
            backtestForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.runBacktest();
            });
        }
    }
    
    handleNavigation() {
        // Add any navigation logic here
    }
    
    async loadStockData(symbol) {
        try {
            showLoading('stock-results');
            const response = await fetch(`${this.baseUrl}/stock/${symbol}`);
            const data = await response.json();
            
            if (data.error) {
                showError('stock-results', data.error);
                return;
            }
            
            this.displayStockData(data);
        } catch (error) {
            console.error('Error loading stock data:', error);
            showError('stock-results', '加载股票数据失败');
        } finally {
            hideLoading('stock-results');
        }
    }
    
    async loadSentimentData(symbol) {
        try {
            showLoading('sentiment-results');
            const response = await fetch(`${this.baseUrl}/sentiment/${symbol}`);
            const data = await response.json();
            
            if (data.error) {
                showError('sentiment-results', data.error);
                return;
            }
            
            this.displaySentimentData(data);
        } catch (error) {
            console.error('Error loading sentiment data:', error);
            showError('sentiment-results', '加载情绪分析数据失败');
        } finally {
            hideLoading('sentiment-results');
        }
    }
    
    async runBacktest() {
        const formData = {
            symbol: document.getElementById('backtest-symbol').value.toUpperCase(),
            strategy: document.getElementById('strategy').value,
            startDate: document.getElementById('start-date').value,
            endDate: document.getElementById('end-date').value,
            capital: parseFloat(document.getElementById('capital').value)
        };
        
        try {
            showLoading('backtest-results');
            const response = await fetch(`${this.baseUrl}/backtest`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            });
            
            const data = await response.json();
            
            if (data.error) {
                showError('backtest-results', data.error);
                return;
            }
            
            this.displayBacktestResults(data);
        } catch (error) {
            console.error('Error running backtest:', error);
            showError('backtest-results', '回测执行失败');
        } finally {
            hideLoading('backtest-results');
        }
    }
    
    displayStockData(data) {
        // Implementation for displaying stock data
        const container = document.getElementById('stock-results');
        if (!container) return;
        
        let html = `
            <div class="row">
                <div class="col-md-6">
                    <h4>${data.symbol}</h4>
                    <p><strong>当前价格:</strong> $${data.current_price.toFixed(2)}</p>
                    <p><strong>涨跌幅:</strong> <span class="${data.change_percent >= 0 ? 'text-success' : 'text-danger'}">${data.change_percent.toFixed(2)}%</span></p>
                    <p><strong>市值:</strong> $${(data.market_cap / 1e9).toFixed(2)}B</p>
                </div>
                <div class="col-md-6">
                    <h5>技术指标</h5>
                    <p><strong>RSI:</strong> ${data.rsi?.toFixed(2) || 'N/A'}</p>
                    <p><strong>MACD:</strong> ${data.macd?.toFixed(2) || 'N/A'}</p>
                    <p><strong>布林带:</strong> ${data.bollinger_bands?.upper?.toFixed(2) || 'N/A'} / ${data.bollinger_bands?.middle?.toFixed(2) || 'N/A'} / ${data.bollinger_bands?.lower?.toFixed(2) || 'N/A'}</p>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
    }
    
    displaySentimentData(data) {
        // Implementation from sentiment.html
        let signalColor = 'secondary';
        let signalText = '中性';
        if (data.signal === 'BUY') {
            signalColor = data.strength === 'STRONG' ? 'success' : 'info';
            signalText = data.strength === 'STRONG' ? '强烈买入' : '买入';
        } else if (data.signal === 'SELL') {
            signalColor = data.strength === 'STRONG' ? 'danger' : 'warning';
            signalText = data.strength === 'STRONG' ? '强烈卖出' : '卖出';
        }
        
        const html = `
            <div class="row">
                <div class="col-md-6">
                    <h4>${data.symbol}</h4>
                    <div class="badge bg-${signalColor} fs-5">${signalText}</div>
                    <p class="mt-2"><strong>情绪分数:</strong> ${data.sentiment_score.toFixed(2)}</p>
                    <p><strong>置信度:</strong> ${(data.confidence * 100).toFixed(1)}%</p>
                    <p><strong>分析时间:</strong> ${new Date(data.timestamp).toLocaleString('zh-CN')}</p>
                </div>
                <div class="col-md-6">
                    <h5>新闻情绪</h5>
                    <p>文章数量: ${data.news_data.article_count}</p>
                    <p>新闻情绪: ${data.news_data.sentiment_score.toFixed(2)}</p>
                    
                    <h5 class="mt-3">社交情绪</h5>
                    <p>推文数量: ${data.social_data.tweet_count}</p>
                    <p>社交情绪: ${data.social_data.social_sentiment.toFixed(2)}</p>
                </div>
            </div>
        `;
        
        document.getElementById('sentiment-results').innerHTML = html;
    }
    
    displayBacktestResults(data) {
        // Implementation from backtesting.html
        const performance = data.performance;
        const totalReturnPercent = (performance.total_return * 100).toFixed(2);
        const winRatePercent = (performance.win_rate * 100).toFixed(1);
        
        let returnColor = 'secondary';
        if (performance.total_return > 0) {
            returnColor = 'success';
        } else if (performance.total_return < 0) {
            returnColor = 'danger';
        }
        
        const html = `
            <div class="row">
                <div class="col-md-6">
                    <h4>${data.symbol} - ${data.strategy}</h4>
                    <p><strong>回测期间:</strong> ${data.startDate} 到 ${data.endDate}</p>
                    <p><strong>初始资金:</strong> $${data.capital.toLocaleString()}</p>
                    <p><strong>最终价值:</strong> $${performance.final_value.toLocaleString()}</p>
                </div>
                <div class="col-md-6">
                    <div class="card bg-${returnColor} text-white">
                        <div class="card-body text-center">
                            <h5>总收益</h5>
                            <h3 class="mb-0">${totalReturnPercent}%</h3>
                        </div>
                    </div>
                    <div class="mt-3">
                        <p><strong>胜率:</strong> ${winRatePercent}%</p>
                        <p><strong>最大回撤:</strong> ${(performance.max_drawdown * 100).toFixed(2)}%</p>
                        <p><strong>夏普比率:</strong> ${performance.sharpe_ratio.toFixed(2)}</p>
                    </div>
                </div>
            </div>
            <div class="mt-3">
                <h5>交易记录 (${data.trades.length} 笔)</h5>
                <div style="max-height: 300px; overflow-y: auto;">
                    <table class="table table-sm">
                        <thead>
                            <tr>
                                <th>日期</th>
                                <th>类型</th>
                                <th>价格</th>
                                <th>数量</th>
                                <th>盈亏</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.trades.map(trade => `
                                <tr>
                                    <td>${trade.date}</td>
                                    <td>${trade.type}</td>
                                    <td>$${trade.price.toFixed(2)}</td>
                                    <td>${trade.quantity}</td>
                                    <td class="${trade.profit >= 0 ? 'text-success' : 'text-danger'}">
                                        $${trade.profit.toFixed(2)}
                                    </td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        
        document.getElementById('backtest-results').innerHTML = html;
    }
    
    initCharts() {
        // Initialize any charts here if needed
    }
}

// Utility functions
function showLoading(containerId) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = '<div class="text-center"><div class="spinner-border" role="status"><span class="visually-hidden">Loading...</span></div></div>';
    }
}

function showError(containerId, message) {
    const container = document.getElementById(containerId);
    if (container) {
        container.innerHTML = `<div class="alert alert-danger">${message}</div>`;
    }
}

function hideLoading(containerId) {
    // This is handled by replacing content
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.stockAnalyzer = new StockAnalyzer();
});

// Global error handling
window.addEventListener('error', (event) => {
    console.error('Global error:', event.error);
});