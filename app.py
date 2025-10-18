import streamlit as st
import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import pickle

# 设置页面配置
st.set_page_config(
    page_title="ETF基金监控",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义CSS样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 300;
        color: #1f2937;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: 0.1em;
    }
    
    .metric-card {
        background-color: #f8fafc;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #3b82f6;
        margin: 0.5rem 0;
    }
    
    .status-up {
        color: #059669;
        font-weight: 600;
    }
    
    .status-down {
        color: #dc2626;
        font-weight: 600;
    }
    
    .status-neutral {
        color: #6b7280;
        font-weight: 600;
    }
    
    .data-table {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 16px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
        overflow: hidden;
        border: 2px solid #cbd5e1;
        position: relative;
    }
    
    .data-table::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 6px;
        background: linear-gradient(90deg, #667eea, #764ba2, #f093fb, #f5576c, #4facfe, #00f2fe);
        z-index: 1;
    }
    
    .data-table::after {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        background: linear-gradient(45deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
        pointer-events: none;
        z-index: 0;
    }
    
    .stDataFrame {
        border: none !important;
        border-radius: 12px !important;
    }
    
    .stDataFrame table {
        border-radius: 12px !important;
        overflow: hidden !important;
    }
    
    .stDataFrame thead th {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #5a67d8 !important;
        padding: 12px 8px !important;
        text-shadow: 0 1px 2px rgba(0,0,0,0.1) !important;
    }
    
    .stDataFrame tbody td {
        padding: 10px 8px !important;
        border-bottom: 1px solid #e2e8f0 !important;
    }
    
    .stDataFrame tbody tr:nth-child(even) {
        background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%) !important;
    }
    
    .stDataFrame tbody tr:nth-child(odd) {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%) !important;
    }
    
    .stDataFrame tbody tr:hover {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%) !important;
        transform: scale(1.02) !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stDataFrame tbody tr:nth-child(1) td:first-child {
        background: linear-gradient(135deg, #ffd700, #ffed4e) !important;
        color: #8b4513 !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    
    .stDataFrame tbody tr:nth-child(2) td:first-child {
        background: linear-gradient(135deg, #c0c0c0, #e5e5e5) !important;
        color: #4a4a4a !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    
    .stDataFrame tbody tr:nth-child(3) td:first-child {
        background: linear-gradient(135deg, #cd7f32, #daa520) !important;
        color: white !important;
        font-weight: bold !important;
        text-align: center !important;
    }
    
    .footer {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        text-align: center;
        padding: 1rem;
        margin-top: 2rem;
        border-radius: 8px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    .refresh-button {
        background-color: #3b82f6;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 6px;
        cursor: pointer;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# ETF基金配置
ETF_CONFIG = {
    "159941": {"name": "纳指ETF", "symbol": "sz159941"},
    "513050": {"name": "中概互联网ETF", "symbol": "sh513050"},
    "511090": {"name": "30年国债ETF", "symbol": "sh511090"},
    "510300": {"name": "300ETF", "symbol": "sh510300"},
    "159915": {"name": "创业板ETF", "symbol": "sz159915"},
    "518880": {"name": "黄金ETF", "symbol": "sh518880"}
}

def get_etf_data(symbol):
    """获取ETF历史数据（带缓存）"""
    # 先尝试从缓存获取
    cached_data = get_cached_data(symbol)
    if cached_data is not None:
        return cached_data
    
    # 缓存不存在或过期，从API获取
    try:
        df = ak.fund_etf_hist_sina(symbol=symbol)
        if df.empty:
            st.warning(f"ETF {symbol} 数据为空")
            return None
        
        # 确保日期列是datetime类型
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')
        
        # 检查数据质量
        if df['close'].isna().any():
            st.warning(f"ETF {symbol} 存在缺失的收盘价数据")
            df = df.dropna(subset=['close'])
        
        # 确保有足够的数据
        if len(df) < 28:
            st.warning(f"ETF {symbol} 数据不足28个交易日，当前只有 {len(df)} 个数据点")
        
        # 保存到缓存
        save_cached_data(symbol, df)
        
        return df
    except Exception as e:
        st.error(f"获取 {symbol} 数据失败: {str(e)}")
        return None

def calculate_metrics(df):
    """计算20日涨幅、28日均线、6日BIAS和近一年涨幅"""
    if df is None or len(df) < 28:
        return None, None, None, None, None
    
    # 获取最新价格
    latest_price = df['close'].iloc[-1]
    
    # 计算20日涨幅 - 确保是20个交易日
    if len(df) >= 21:  # 需要至少21个数据点（当前+20个交易日前）
        price_20_days_ago = df['close'].iloc[-21]  # 20个交易日前的价格
        if pd.isna(price_20_days_ago) or pd.isna(latest_price):
            change_20d = None
        else:
            change_20d = ((latest_price - price_20_days_ago) / price_20_days_ago) * 100
    else:
        change_20d = None
    
    # 计算28日均线
    ma_28_series = df['close'].rolling(window=28).mean()
    ma_28 = ma_28_series.iloc[-1] if not ma_28_series.empty else None
    
    # 计算6日BIAS
    if len(df) >= 6:
        ma_6_series = df['close'].rolling(window=6).mean()
        ma_6 = ma_6_series.iloc[-1] if not ma_6_series.empty else None
        if pd.isna(ma_6) or pd.isna(latest_price) or ma_6 == 0:
            bias_6 = None
        else:
            bias_6 = ((latest_price - ma_6) / ma_6) * 100
    else:
        bias_6 = None
    
    # 计算近一年涨幅（约250个交易日）
    if len(df) >= 251:  # 需要至少251个数据点（当前+250个交易日前）
        price_1_year_ago = df['close'].iloc[-251]  # 250个交易日前的价格
        if pd.isna(price_1_year_ago) or pd.isna(latest_price):
            change_1y = None
        else:
            change_1y = ((latest_price - price_1_year_ago) / price_1_year_ago) * 100
    else:
        change_1y = None
    
    # 判断是否跌破28日均线
    if pd.isna(ma_28) or pd.isna(latest_price):
        below_ma28 = False
    else:
        below_ma28 = latest_price < ma_28
    
    return change_20d, ma_28, below_ma28, bias_6, change_1y

def format_change(change):
    """格式化涨幅显示"""
    if change is None:
        return "N/A"
    
    if change > 0:
        return f"🔴 +{change:.2f}%"
    elif change < 0:
        return f"🟢 {change:.2f}%"
    else:
        return f"⚪ {change:.2f}%"

def format_bias(bias):
    """格式化BIAS显示"""
    if bias is None:
        return "N/A"
    
    if bias > 0:
        return f"🔴 +{bias:.2f}%"
    elif bias < 0:
        return f"🟢 {bias:.2f}%"
    else:
        return f"⚪ {bias:.2f}%"

def get_status_class(change):
    """获取状态样式类"""
    if change is None:
        return "status-neutral"
    elif change > 0:
        return "status-up"
    else:
        return "status-down"

def get_cached_data(symbol, cache_dir="cache"):
    """获取缓存数据"""
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_file = os.path.join(cache_dir, f"{symbol}.pkl")
    
    if os.path.exists(cache_file):
        # 检查缓存文件时间
        cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
        now = datetime.now()
        
        # 如果缓存超过2天，删除缓存文件
        if (now - cache_time).days >= 2:
            os.remove(cache_file)
            return None
        
        # 读取缓存数据
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
            
            # 检查缓存数据的日期
            if 'date' in cached_data.columns:
                cached_data['date'] = pd.to_datetime(cached_data['date'])
                latest_cache_date = cached_data['date'].max().date()
                today = datetime.now().date()
                
                # 如果缓存数据不是今天的，需要更新
                if latest_cache_date < today:
                    return None
            
            return cached_data
        except:
            return None
    
    return None

def save_cached_data(symbol, data, cache_dir="cache"):
    """保存数据到缓存"""
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    cache_file = os.path.join(cache_dir, f"{symbol}.pkl")
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)
    except:
        pass

def clear_cache(cache_dir="cache"):
    """清除所有缓存"""
    if os.path.exists(cache_dir):
        for file in os.listdir(cache_dir):
            if file.endswith('.pkl'):
                os.remove(os.path.join(cache_dir, file))

def main():
    # 刷新按钮
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("🔄 刷新数据", key="refresh"):
            st.rerun()
    with col3:
        if st.button("🗑️ 清除缓存", key="clear_cache"):
            clear_cache()
            st.success("缓存已清除")
            st.rerun()
    
    st.markdown("---")
    
    # 创建数据容器
    data_container = st.container()
    
    with data_container:
        # 显示加载状态
        with st.spinner("正在获取ETF数据..."):
            results = []
            
            for code, config in ETF_CONFIG.items():
                # 获取数据
                df = get_etf_data(config["symbol"])
                
                if df is not None:
                    # 计算指标
                    change_20d, ma_28, below_ma28, bias_6, change_1y = calculate_metrics(df)
                    latest_price = df['close'].iloc[-1]
                    
                    results.append({
                        "代码": code,
                        "名称": config["name"],
                        "最新价格": f"{latest_price:.3f}",
                        "20日涨幅": change_20d,
                        "28日均线": f"{ma_28:.3f}" if ma_28 else "N/A",
                        "6日BIAS": bias_6,
                        "近一年涨幅": change_1y,
                        "跌破28日均线": "⚠️ 是" if below_ma28 else "✅ 否",
                        "跌破状态": below_ma28
                    })
                else:
                    results.append({
                        "代码": code,
                        "名称": config["name"],
                        "最新价格": "N/A",
                        "20日涨幅": None,
                        "28日均线": "N/A",
                        "6日BIAS": None,
                        "近一年涨幅": None,
                        "跌破28日均线": "N/A",
                        "跌破状态": False
                    })
        
        # 创建DataFrame
        df_results = pd.DataFrame(results)
        
        # 按20日涨幅排序（降序）
        df_results = df_results.sort_values('20日涨幅', ascending=False)
        
        # 格式化显示
        display_df = df_results.copy()
        display_df["20日涨幅"] = display_df["20日涨幅"].apply(format_change)
        display_df["6日BIAS"] = display_df["6日BIAS"].apply(format_bias)
        display_df["近一年涨幅"] = display_df["近一年涨幅"].apply(format_change)
        
        # 移除不需要的列
        display_df = display_df.drop(columns=["跌破状态"])
        
        # 添加行号
        display_df.insert(0, '排名', range(1, len(display_df) + 1))
        
        # 显示表格
        st.markdown('<div class="data-table">', unsafe_allow_html=True)
        
        # 使用st.dataframe显示数据，但先处理颜色
        # 创建颜色化的DataFrame
        colored_df = display_df.copy()
        
        # 为排名列添加特殊样式
        def format_rank(rank):
            if rank == 1:
                return "🥇 1"
            elif rank == 2:
                return "🥈 2"
            elif rank == 3:
                return "🥉 3"
            else:
                return str(rank)
        
        colored_df['排名'] = colored_df['排名'].apply(format_rank)
        
        # 使用st.dataframe显示数据
        st.dataframe(
            colored_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "排名": st.column_config.TextColumn("排名", width="small"),
                "代码": st.column_config.TextColumn("代码", width="small"),
                "名称": st.column_config.TextColumn("名称", width="medium"),
                "最新价格": st.column_config.TextColumn("最新价格", width="small"),
                "20日涨幅": st.column_config.TextColumn("20日涨幅", width="small"),
                "28日均线": st.column_config.TextColumn("28日均线", width="small"),
                "6日BIAS": st.column_config.TextColumn("6日BIAS", width="small"),
                "近一年涨幅": st.column_config.TextColumn("近一年涨幅", width="small"),
                "跌破28日均线": st.column_config.TextColumn("跌破28日均线", width="small")
            }
        )
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # 添加状态说明
        st.markdown("""
        <div style="margin-top: 2rem; padding: 1rem; background-color: #f8fafc; border-radius: 8px;">
            <h4 style="margin: 0 0 0.5rem 0; color: #374151;">说明</h4>
            <ul style="margin: 0; color: #6b7280;">
                <li><strong>排名</strong>: 按20日涨幅从高到低排序</li>
                <li><strong>20日涨幅</strong>: 相对于20个交易日前的价格变化百分比</li>
                <li><strong>28日均线</strong>: 最近28个交易日的平均价格</li>
                <li><strong>6日BIAS</strong>: 当前价格相对于6日均线的偏离度百分比</li>
                <li><strong>近一年涨幅</strong>: 相对于250个交易日前的价格变化百分比</li>
                <li><strong>跌破28日均线</strong>: 当前价格是否低于28日均线</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # 显示更新时间
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 显示缓存状态
        cache_info = []
        for code, config in ETF_CONFIG.items():
            cached_data = get_cached_data(config["symbol"])
            if cached_data is not None:
                cache_info.append(f"{code}: 缓存")
            else:
                cache_info.append(f"{code}: 实时")
        
        cache_status = " | ".join(cache_info)
        
        st.markdown(f'''
        <div style="text-align: center; margin-top: 1rem; color: #9ca3af; font-size: 0.9rem;">
            数据更新时间: {current_time}<br>
            缓存状态: {cache_status}
        </div>
        ''', unsafe_allow_html=True)
        
        # 版权信息
        current_year = datetime.now().year
        st.markdown(f'''
        <div class="footer">
            <p style="margin: 0; font-size: 0.9rem; font-weight: 500;">
                © {current_year} 版权所有 小林动量 | ETF基金监控系统
            </p>
        </div>
        ''', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
