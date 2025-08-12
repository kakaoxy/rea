# 房产数据分析看板

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import os

# --- 页面基础设置 ---
st.set_page_config(
    page_title="房产市场数据分析看板",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 辅助函数 ---
def calculate_price_per_sqm_stats(df, price_col, area_col):
    """计算单价统计信息"""
    if price_col in df.columns and area_col in df.columns:
        valid_data = df.dropna(subset=[price_col, area_col])
        if len(valid_data) > 0:
            return {
                'mean': valid_data[price_col].mean(),
                'median': valid_data[price_col].median(),
                'std': valid_data[price_col].std(),
                'q25': valid_data[price_col].quantile(0.25),
                'q75': valid_data[price_col].quantile(0.75)
            }
    return None

def analyze_market_segments(df, price_col, area_col):
    """市场细分分析"""
    segments = {}
    if price_col in df.columns and area_col in df.columns:
        valid_data = df.dropna(subset=[price_col, area_col])
        if len(valid_data) > 0:
            # 按面积分段
            valid_data['面积段'] = pd.cut(valid_data[area_col], 
                                      bins=[0, 50, 70, 90, 120, float('inf')], 
                                      labels=['小户型(<50㎡)', '紧凑型(50-70㎡)', '标准型(70-90㎡)', '舒适型(90-120㎡)', '大户型(>120㎡)'])
            
            # 按总价分段 - 修复重复边界问题
            try:
                price_quantiles = valid_data[price_col].quantile([0.33, 0.67])
                q1, q3 = price_quantiles.iloc[0], price_quantiles.iloc[1]
                
                # 检查是否有重复的边界值
                if q1 == q3 or q1 == 0:
                    # 如果有重复值或第一个分位数为0，使用固定分段
                    min_price = valid_data[price_col].min()
                    max_price = valid_data[price_col].max()
                    price_range = max_price - min_price
                    
                    # 确保分段有意义
                    if price_range > 0:
                        third = price_range / 3
                        bins = [min_price, min_price + third, min_price + 2*third, max_price + 0.1]
                    else:
                        # 如果价格范围为0，创建一个简单的两段分类
                        bins = [min_price - 0.1, min_price, min_price + 0.1]
                        labels = ['经济型', '中端型']
                        valid_data['价格段'] = pd.cut(valid_data[price_col], bins=bins, labels=labels)
                        segments['price_segments'] = valid_data.groupby('价格段', observed=True)[area_col].agg(['count', 'mean', 'median']).round(2)
                        segments['area_segments'] = valid_data.groupby('面积段', observed=True)[price_col].agg(['count', 'mean', 'median']).round(2)
                        segments['data'] = valid_data
                        return segments
                else:
                    bins = [0, q1, q3, float('inf')]
                
                valid_data['价格段'] = pd.cut(valid_data[price_col], 
                                          bins=bins, 
                                          labels=['经济型', '中端型', '高端型'])
            except Exception as e:
                # 如果分段失败，使用简单的三等分
                try:
                    min_price = valid_data[price_col].min()
                    max_price = valid_data[price_col].max()
                    price_range = max_price - min_price
                    
                    if price_range > 0:
                        third = price_range / 3
                        bins = [min_price, min_price + third, min_price + 2*third, max_price + 0.1]
                        valid_data['价格段'] = pd.cut(valid_data[price_col], 
                                              bins=bins, 
                                              labels=['经济型', '中端型', '高端型'])
                    else:
                        # 如果所有价格相同，只创建一个类别
                        valid_data['价格段'] = '中端型'
                except:
                    # 最后的备选方案：跳过价格分段
                    valid_data['价格段'] = '未分类'
            
            segments['area_segments'] = valid_data.groupby('面积段', observed=True)[price_col].agg(['count', 'mean', 'median']).round(2)
            segments['price_segments'] = valid_data.groupby('价格段', observed=True)[area_col].agg(['count', 'mean', 'median']).round(2)
            segments['data'] = valid_data
    return segments

# --- 侧边栏控制面板 ---
st.sidebar.title("🏢 房产市场分析控制台")
st.sidebar.markdown("---")

# 数据类型选择
data_type = st.sidebar.radio(
    "📊 选择分析数据类型：", 
    ('在售房源', '成交房源'),
    help="在售房源分析当前市场供应情况，成交房源分析历史交易数据"
)

# 文件上传
uploaded_files = st.sidebar.file_uploader(
    f"📁 上传「{data_type}」CSV文件",
    type=['csv'],
    accept_multiple_files=True,
    help="支持上传多个CSV文件，系统将自动合并分析"
)

# --- 数据加载与处理 ---
if uploaded_files:
    try:
        # 读取所有上传的CSV文件并合并
        df_list = [pd.read_csv(file) for file in uploaded_files]
        df = pd.concat(df_list, ignore_index=True)
        
        # 数据标准化处理
        if data_type == '在售房源':
            column_mapping = {
                '小区': '小区名称',
                '建筑面积(㎡)': '面积(㎡)',
                '总价(万)': '总价(万)',
                '单价(元/平)': '单价(元/平)',
                '年代': '建成年代'
            }
        else:
            column_mapping = {
                '成交总价(万)': '总价(万)',
                '成交单价(元/平)': '单价(元/平)'
            }
        
        # 应用列名映射
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df[new_name] = df[old_name]

        # 数据清洗
        numeric_cols = ['总价(万)', '单价(元/平)', '面积(㎡)', '建成年代', '挂牌价(万)', '成交周期(天)', '关注人数']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        df.dropna(how='all', inplace=True)

        # --- 主页面标题 ---
        st.title("🏢 房产市场数据分析报告")
        
        # 数据概览卡片
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 数据总量", f"{len(df):,}条")
        with col2:
            if '总价(万)' in df.columns:
                total_value = df['总价(万)'].sum()
                st.metric("💰 总市值", f"{total_value:,.0f}万元")
        with col3:
            if '面积(㎡)' in df.columns:
                total_area = df['面积(㎡)'].sum()
                st.metric("🏠 总面积", f"{total_area:,.0f}㎡")
        with col4:
            if data_type == '成交房源' and '成交日期' in df.columns:
                # 解析成交日期并计算时间跨度
                try:
                    df['成交日期'] = pd.to_datetime(df['成交日期'])
                    date_range = (df['成交日期'].max() - df['成交日期'].min()).days
                    st.metric("📅 数据跨度", f"{date_range}天")
                except:
                    st.metric("📅 数据跨度", "N/A")
            else:
                st.metric("🔍 数据类型", data_type)

        st.markdown("---")

        # --- 数据筛选器 ---
        st.sidebar.header("🔍 数据筛选器")
        
        # 筛选器重置按钮
        if st.sidebar.button("🔄 重置所有筛选器", help="重置所有筛选条件到默认状态"):
            st.rerun()
        
        st.sidebar.markdown("---")
        
        # === 地理位置筛选 ===
        st.sidebar.subheader("📍 地理位置")
        
        # 区域和商圈筛选
        if data_type == '在售房源' and '区域' in df.columns:
            districts = sorted(df['区域'].unique())
            selected_districts = st.sidebar.multiselect(
                '🏙️ 选择区域', 
                options=districts, 
                default=districts,
                help="选择要分析的行政区域"
            )
            
            if '商圈' in df.columns:
                available_circles = sorted(df[df['区域'].isin(selected_districts)]['商圈'].unique())
                selected_circles = st.sidebar.multiselect(
                    '🏪 选择商圈', 
                    options=available_circles, 
                    default=available_circles,
                    help="选择具体的商业圈"
                )
        
        # === 价格和面积筛选 ===
        st.sidebar.subheader("💰 价格与面积")
        
        # 价格区间筛选
        if '总价(万)' in df.columns and not df['总价(万)'].isna().all():
            price_data = df['总价(万)'].dropna()
            if len(price_data) > 0:
                price_range = st.sidebar.slider(
                    '💰 总价区间 (万元)',
                    min_value=int(price_data.min()),
                    max_value=int(price_data.max()),
                    value=(int(price_data.min()), int(price_data.max())),
                    help="设置房源总价筛选范围"
                )
                min_price, max_price = price_range
        
        # 面积筛选
        if '面积(㎡)' in df.columns and not df['面积(㎡)'].isna().all():
            area_data = df['面积(㎡)'].dropna()
            if len(area_data) > 0:
                area_range = st.sidebar.slider(
                    '🏠 面积区间 (㎡)',
                    min_value=int(area_data.min()),
                    max_value=int(area_data.max()),
                    value=(int(area_data.min()), int(area_data.max())),
                    help="设置房源面积筛选范围"
                )
                min_area, max_area = area_range
        
        # === 房屋属性筛选 ===
        st.sidebar.subheader("🏠 房屋属性")
        
        # 房龄筛选
        year_col = '建成年代' if '建成年代' in df.columns else '年代'
        if year_col in df.columns and not df[year_col].isna().all():
            year_data = df[year_col].dropna()
            if len(year_data) > 0:
                current_year = datetime.now().year
                min_year, max_year = int(year_data.min()), int(year_data.max())
                selected_years = st.sidebar.slider(
                    '🏗️ 建成年代',
                    min_value=min_year,
                    max_value=max_year,
                    value=(min_year, max_year),
                    help="选择房屋建成年代范围"
                )
                
                # 显示对应房龄
                min_age = current_year - selected_years[1]
                max_age = current_year - selected_years[0]
                st.sidebar.caption(f"对应房龄：{min_age}-{max_age}年")

        # 户型分类筛选
        if '户型' in df.columns:
            # 提取户型主要类别
            def extract_room_type(huxing):
                if pd.isna(huxing):
                    return '未知'
                huxing_str = str(huxing)
                if '1室' in huxing_str:
                    return '1室'
                elif '2室' in huxing_str:
                    return '2室'
                elif '3室' in huxing_str:
                    return '3室'
                elif '4室' in huxing_str:
                    return '4室'
                elif '5室' in huxing_str:
                    return '5室+'
                else:
                    return '其他'
            
            df['户型分类'] = df['户型'].apply(extract_room_type)
            room_types = sorted(df['户型分类'].unique())
            
            selected_room_types = st.sidebar.multiselect(
                '🏠 选择户型',
                options=room_types,
                default=room_types,
                help="选择要分析的户型类别"
            )

        # 楼层分类筛选
        floor_col = '楼层信息' if '楼层信息' in df.columns else '楼层'
        if floor_col in df.columns:
            # 提取楼层分类
            def extract_floor_type(floor_info):
                if pd.isna(floor_info):
                    return '未知'
                floor_str = str(floor_info)
                if '低楼层' in floor_str or '底层' in floor_str:
                    return '低楼层'
                elif '中楼层' in floor_str or '中层' in floor_str:
                    return '中楼层'
                elif '高楼层' in floor_str or '顶层' in floor_str:
                    return '高楼层'
                else:
                    return '其他'
            
            df['楼层分类'] = df[floor_col].apply(extract_floor_type)
            floor_types = sorted(df['楼层分类'].unique())
            
            selected_floor_types = st.sidebar.multiselect(
                '🏢 选择楼层',
                options=floor_types,
                default=floor_types,
                help="选择要分析的楼层类别"
            )

        # 装修状况筛选
        if '装修' in df.columns:
            decoration_types = sorted(df['装修'].dropna().unique())
            if len(decoration_types) > 0:
                selected_decorations = st.sidebar.multiselect(
                    '🎨 选择装修状况',
                    options=decoration_types,
                    default=decoration_types,
                    help="选择要分析的装修状况"
                )

        # 应用筛选条件
        filtered_df = df.copy()
        
        # 区域和商圈筛选
        if data_type == '在售房源' and '区域' in df.columns:
            filtered_df = filtered_df[filtered_df['区域'].isin(selected_districts)]
            if '商圈' in df.columns and 'selected_circles' in locals():
                filtered_df = filtered_df[filtered_df['商圈'].isin(selected_circles)]
        
        # 价格筛选
        if '总价(万)' in df.columns and 'min_price' in locals():
            filtered_df = filtered_df[
                (filtered_df['总价(万)'] >= min_price) &
                (filtered_df['总价(万)'] <= max_price)
            ]
        
        # 面积筛选
        if '面积(㎡)' in df.columns and 'min_area' in locals():
            filtered_df = filtered_df[
                (filtered_df['面积(㎡)'] >= min_area) &
                (filtered_df['面积(㎡)'] <= max_area)
            ]
        
        # 房龄筛选
        if year_col in df.columns and 'selected_years' in locals():
            filtered_df = filtered_df[
                (filtered_df[year_col] >= selected_years[0]) &
                (filtered_df[year_col] <= selected_years[1])
            ]
        
        # 户型筛选
        if '户型' in df.columns and 'selected_room_types' in locals():
            filtered_df = filtered_df[filtered_df['户型分类'].isin(selected_room_types)]
        
        # 楼层筛选
        if floor_col in df.columns and 'selected_floor_types' in locals():
            filtered_df = filtered_df[filtered_df['楼层分类'].isin(selected_floor_types)]
        
        # 装修状况筛选
        if '装修' in df.columns and 'selected_decorations' in locals():
            filtered_df = filtered_df[filtered_df['装修'].isin(selected_decorations)]
        
        # 筛选结果提示
        filter_ratio = len(filtered_df) / len(df) * 100
        st.sidebar.markdown("---")
        st.sidebar.subheader("📊 筛选结果")
        
        # 详细筛选摘要
        col1, col2 = st.sidebar.columns(2)
        with col1:
            st.metric("筛选后数据", f"{len(filtered_df):,}条")
        with col2:
            st.metric("筛选比例", f"{filter_ratio:.1f}%")
        
        # 筛选条件摘要
        active_filters = []
        if data_type == '在售房源' and '区域' in df.columns and 'selected_districts' in locals():
            if len(selected_districts) < len(df['区域'].unique()):
                active_filters.append(f"区域: {len(selected_districts)}个")
        
        if '户型' in df.columns and 'selected_room_types' in locals():
            if len(selected_room_types) < len(df['户型分类'].unique()):
                active_filters.append(f"户型: {len(selected_room_types)}类")
        
        if floor_col in df.columns and 'selected_floor_types' in locals():
            if len(selected_floor_types) < len(df['楼层分类'].unique()):
                active_filters.append(f"楼层: {len(selected_floor_types)}类")
        
        if '装修' in df.columns and 'selected_decorations' in locals():
            if len(selected_decorations) < len(df['装修'].dropna().unique()):
                active_filters.append(f"装修: {len(selected_decorations)}类")
        
        if active_filters:
            st.sidebar.info("🔍 活跃筛选器:\n" + "\n".join([f"• {f}" for f in active_filters]))
        else:
            st.sidebar.success("✅ 显示全部数据")
        
        if len(filtered_df) == 0:
            st.warning("⚠️ 当前筛选条件下没有数据，请调整筛选条件")
            st.stop()

        # --- 市场分析核心指标 ---
        st.header("📈 市场核心指标分析")
        
        # 计算市场细分数据
        segments = analyze_market_segments(filtered_df, '总价(万)', '面积(㎡)')
        price_stats = calculate_price_per_sqm_stats(filtered_df, '单价(元/平)', '面积(㎡)')
        
        # 核心指标展示
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            if '总价(万)' in filtered_df.columns:
                avg_price = filtered_df['总价(万)'].mean()
                median_price = filtered_df['总价(万)'].median()
                st.metric(
                    "💰 平均总价", 
                    f"{avg_price:.1f}万",
                    delta=f"中位数: {median_price:.1f}万"
                )
        
        with col2:
            if price_stats:
                st.metric(
                    "🏷️ 平均单价", 
                    f"{price_stats['mean']:,.0f}元/㎡",
                    delta=f"中位数: {price_stats['median']:,.0f}元/㎡"
                )
        
        with col3:
            if '面积(㎡)' in filtered_df.columns:
                avg_area = filtered_df['面积(㎡)'].mean()
                median_area = filtered_df['面积(㎡)'].median()
                st.metric(
                    "🏠 平均面积", 
                    f"{avg_area:.1f}㎡",
                    delta=f"中位数: {median_area:.1f}㎡"
                )
        
        with col4:
            if data_type == '成交房源' and '成交周期(天)' in filtered_df.columns:
                avg_cycle = filtered_df['成交周期(天)'].mean()
                median_cycle = filtered_df['成交周期(天)'].median()
                st.metric(
                    "⏱️ 平均成交周期", 
                    f"{avg_cycle:.0f}天",
                    delta=f"中位数: {median_cycle:.0f}天"
                )
            elif '关注人数' in filtered_df.columns:
                avg_attention = filtered_df['关注人数'].mean()
                st.metric("👥 平均关注度", f"{avg_attention:.0f}人")
        
        with col5:
            if price_stats:
                price_cv = price_stats['std'] / price_stats['mean'] * 100
                st.metric(
                    "📊 价格离散度", 
                    f"{price_cv:.1f}%",
                    help="变异系数，反映价格分布的离散程度"
                )

        st.markdown("---")

        # --- 图表分析 ---
        st.header("📊 市场分析图表")
        
        # 第一行图表
        col1, col2 = st.columns(2)
        
        with col1:
            # 价格分布箱线图
            if '单价(元/平)' in filtered_df.columns:
                st.subheader("💹 单价分布分析")
                
                fig_box = go.Figure()
                
                if data_type == '在售房源' and '区域' in filtered_df.columns:
                    for district in filtered_df['区域'].unique():
                        district_data = filtered_df[filtered_df['区域'] == district]['单价(元/平)'].dropna()
                        if len(district_data) > 0:
                            fig_box.add_trace(go.Box(
                                y=district_data,
                                name=district,
                                boxpoints='outliers'
                            ))
                    fig_box.update_layout(
                        title="各区域单价分布对比",
                        yaxis_title="单价 (元/㎡)",
                        showlegend=True
                    )
                else:
                    price_data = filtered_df['单价(元/平)'].dropna()
                    fig_box.add_trace(go.Box(
                        y=price_data,
                        name="整体分布",
                        boxpoints='outliers'
                    ))
                    fig_box.update_layout(
                        title="单价整体分布",
                        yaxis_title="单价 (元/㎡)"
                    )
                
                st.plotly_chart(fig_box, use_container_width=True)
        
        with col2:
            # 面积-价格散点图（增强版）
            if '面积(㎡)' in filtered_df.columns and '总价(万)' in filtered_df.columns:
                st.subheader("🎯 面积-价格关系分析")
                
                scatter_data = filtered_df.dropna(subset=['面积(㎡)', '总价(万)', '单价(元/平)'])
                if len(scatter_data) > 0:
                    fig_scatter = px.scatter(
                        scatter_data,
                        x='面积(㎡)',
                        y='总价(万)',
                        size='单价(元/平)',
                        color='区域' if '区域' in scatter_data.columns else None,
                        hover_data=['小区名称', '户型'] if '小区名称' in scatter_data.columns else None,
                        title="面积-总价-单价三维关系",
                        labels={'size': '单价(元/㎡)'}
                    )
                    
                    # 添加简单的线性趋势线（不依赖statsmodels）
                    try:
                        x_vals = scatter_data['面积(㎡)'].values
                        y_vals = scatter_data['总价(万)'].values
                        
                        # 使用numpy进行简单线性回归
                        z = np.polyfit(x_vals, y_vals, 1)
                        p = np.poly1d(z)
                        
                        fig_scatter.add_trace(go.Scatter(
                            x=x_vals,
                            y=p(x_vals),
                            mode='lines',
                            name='趋势线',
                            line=dict(color='red', dash='dash')
                        ))
                    except:
                        pass  # 如果趋势线添加失败，继续显示散点图
                    
                    st.plotly_chart(fig_scatter, use_container_width=True)

        # 第二行图表
        col1, col2 = st.columns(2)
        
        with col1:
            # 市场细分分析
            if segments and 'area_segments' in segments:
                st.subheader("🏘️ 户型市场细分")
                
                area_seg_data = segments['area_segments'].reset_index()
                
                fig_seg = make_subplots(
                    rows=1, cols=2,
                    subplot_titles=('房源数量分布', '平均总价对比'),
                    specs=[[{"secondary_y": False}, {"secondary_y": False}]]
                )
                
                # 数量分布
                fig_seg.add_trace(
                    go.Bar(x=area_seg_data['面积段'], y=area_seg_data['count'], 
                           name='房源数量', marker_color='lightblue'),
                    row=1, col=1
                )
                
                # 平均价格
                fig_seg.add_trace(
                    go.Bar(x=area_seg_data['面积段'], y=area_seg_data['mean'], 
                           name='平均总价', marker_color='orange'),
                    row=1, col=2
                )
                
                fig_seg.update_layout(height=400, showlegend=False)
                fig_seg.update_xaxes(tickangle=45)
                
                st.plotly_chart(fig_seg, use_container_width=True)
        
        with col2:
            # 房龄分析
            year_col = '建成年代' if '建成年代' in filtered_df.columns else '年代'
            if year_col in filtered_df.columns:
                st.subheader("🏗️ 房龄与价格关系")
                
                year_data = filtered_df.dropna(subset=[year_col, '单价(元/平)'])
                if len(year_data) > 0:
                    current_year = datetime.now().year
                    year_data['房龄'] = current_year - year_data[year_col]
                    
                    # 按房龄分组
                    age_groups = pd.cut(year_data['房龄'], 
                                      bins=[0, 5, 10, 20, 30, float('inf')], 
                                      labels=['新房(≤5年)', '次新房(6-10年)', '中等房龄(11-20年)', '老房(21-30年)', '超老房(>30年)'])
                    year_data['房龄段'] = age_groups
                    
                    age_price = year_data.groupby('房龄段', observed=True)['单价(元/平)'].agg(['mean', 'count']).reset_index()
                    
                    fig_age = go.Figure()
                    fig_age.add_trace(go.Bar(
                        x=age_price['房龄段'],
                        y=age_price['mean'],
                        text=[f'{x:.0f}元/㎡<br>({y}套)' for x, y in zip(age_price['mean'], age_price['count'])],
                        textposition='auto',
                        marker_color='green'
                    ))
                    
                    fig_age.update_layout(
                        title="不同房龄段平均单价",
                        xaxis_title="房龄段",
                        yaxis_title="平均单价 (元/㎡)"
                    )
                    
                    st.plotly_chart(fig_age, use_container_width=True)

        # --- 成交数据特殊分析 ---
        if data_type == '成交房源':
            st.markdown("---")
            st.header("📅 成交趋势分析")
            
            # 时间序列数据处理
            if '成交日期' in filtered_df.columns:
                try:
                    # 确保成交日期是datetime格式
                    filtered_df['成交日期'] = pd.to_datetime(filtered_df['成交日期'], errors='coerce')
                    time_data = filtered_df.dropna(subset=['成交日期'])
                    
                    if len(time_data) > 0:
                        # 添加时间维度列
                        time_data['年月'] = time_data['成交日期'].dt.to_period('M')
                        time_data['季度'] = time_data['成交日期'].dt.to_period('Q')
                        time_data['年份'] = time_data['成交日期'].dt.year
                        time_data['月份'] = time_data['成交日期'].dt.month
                        
                        # === 核心量价趋势分析 ===
                        st.subheader("📈 量价趋势核心分析")
                        
                        # 按月统计成交量和均价
                        monthly_stats = time_data.groupby('年月').agg({
                            '总价(万)': ['count', 'mean', 'median'],
                            '单价(元/平)': ['mean', 'median'],
                            '面积(㎡)': 'mean',
                            '成交周期(天)': 'mean'
                        }).round(2)
                        
                        # 重命名列
                        monthly_stats.columns = ['成交量', '平均总价', '中位总价', '平均单价', '中位单价', '平均面积', '平均成交周期']
                        monthly_stats = monthly_stats.reset_index()
                        monthly_stats['年月日期'] = monthly_stats['年月'].dt.to_timestamp()
                        
                        # 创建量价双轴图表
                        fig_volume_price = make_subplots(
                            rows=2, cols=1,
                            subplot_titles=('📊 月度成交量趋势', '💰 月度价格趋势'),
                            vertical_spacing=0.1,
                            specs=[[{"secondary_y": True}], [{"secondary_y": True}]]
                        )
                        
                        # 第一行：成交量趋势
                        fig_volume_price.add_trace(
                            go.Bar(
                                x=monthly_stats['年月日期'],
                                y=monthly_stats['成交量'],
                                name='月成交量',
                                marker_color='lightblue',
                                yaxis='y1'
                            ),
                            row=1, col=1
                        )
                        
                        # 添加成交量趋势线
                        fig_volume_price.add_trace(
                            go.Scatter(
                                x=monthly_stats['年月日期'],
                                y=monthly_stats['成交量'],
                                mode='lines+markers',
                                name='成交量趋势',
                                line=dict(color='blue', width=3),
                                yaxis='y2'
                            ),
                            row=1, col=1, secondary_y=True
                        )
                        
                        # 第二行：价格趋势
                        fig_volume_price.add_trace(
                            go.Scatter(
                                x=monthly_stats['年月日期'],
                                y=monthly_stats['平均单价'],
                                mode='lines+markers',
                                name='平均单价',
                                line=dict(color='red', width=3),
                                marker=dict(size=8)
                            ),
                            row=2, col=1
                        )
                        
                        fig_volume_price.add_trace(
                            go.Scatter(
                                x=monthly_stats['年月日期'],
                                y=monthly_stats['中位单价'],
                                mode='lines+markers',
                                name='中位单价',
                                line=dict(color='orange', width=2, dash='dash'),
                                marker=dict(size=6)
                            ),
                            row=2, col=1
                        )
                        
                        # 更新布局
                        fig_volume_price.update_layout(
                            height=600,
                            title_text="🏠 房产市场量价趋势分析",
                            showlegend=True
                        )
                        
                        # 更新Y轴标签
                        fig_volume_price.update_yaxes(title_text="成交套数", row=1, col=1)
                        fig_volume_price.update_yaxes(title_text="单价 (元/㎡)", row=2, col=1)
                        fig_volume_price.update_xaxes(title_text="时间", row=2, col=1)
                        
                        st.plotly_chart(fig_volume_price, use_container_width=True)
                        
                        # === 市场热度分析 ===
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("🔥 市场热度指标")
                            
                            # 计算市场热度指标
                            latest_month = monthly_stats.iloc[-1] if len(monthly_stats) > 0 else None
                            prev_month = monthly_stats.iloc[-2] if len(monthly_stats) > 1 else None
                            
                            if latest_month is not None and prev_month is not None:
                                volume_change = ((latest_month['成交量'] - prev_month['成交量']) / prev_month['成交量'] * 100)
                                price_change = ((latest_month['平均单价'] - prev_month['平均单价']) / prev_month['平均单价'] * 100)
                                cycle_change = ((latest_month['平均成交周期'] - prev_month['平均成交周期']) / prev_month['平均成交周期'] * 100)
                                
                                # 显示关键指标
                                st.metric("📈 成交量环比", f"{latest_month['成交量']:.0f}套", f"{volume_change:+.1f}%")
                                st.metric("💰 均价环比", f"{latest_month['平均单价']:,.0f}元/㎡", f"{price_change:+.1f}%")
                                st.metric("⏱️ 成交周期", f"{latest_month['平均成交周期']:.0f}天", f"{cycle_change:+.1f}%")
                                
                                # 市场状态判断
                                if volume_change > 10 and price_change > 0:
                                    market_status = "🔥 市场火热"
                                    status_color = "red"
                                elif volume_change < -10 and price_change < 0:
                                    market_status = "❄️ 市场冷淡"
                                    status_color = "blue"
                                elif abs(volume_change) <= 10 and abs(price_change) <= 5:
                                    market_status = "⚖️ 市场平稳"
                                    status_color = "green"
                                else:
                                    market_status = "📊 市场调整"
                                    status_color = "orange"
                                
                                st.markdown(f"**市场状态**: :{status_color}[{market_status}]")
                        
                        with col2:
                            st.subheader("📊 季度对比分析")
                            
                            # 季度统计
                            quarterly_stats = time_data.groupby('季度').agg({
                                '总价(万)': ['count', 'mean'],
                                '单价(元/平)': 'mean',
                                '成交周期(天)': 'mean'
                            }).round(2)
                            
                            quarterly_stats.columns = ['成交量', '平均总价', '平均单价', '平均成交周期']
                            quarterly_stats = quarterly_stats.reset_index()
                            
                            if len(quarterly_stats) > 0:
                                fig_quarterly = go.Figure()
                                
                                fig_quarterly.add_trace(go.Bar(
                                    x=[str(q) for q in quarterly_stats['季度']],
                                    y=quarterly_stats['成交量'],
                                    name='季度成交量',
                                    text=quarterly_stats['成交量'],
                                    textposition='auto',
                                    marker_color='lightgreen'
                                ))
                                
                                fig_quarterly.update_layout(
                                    title="季度成交量对比",
                                    xaxis_title="季度",
                                    yaxis_title="成交套数",
                                    height=300
                                )
                                
                                st.plotly_chart(fig_quarterly, use_container_width=True)
                        
                        # === 详细时间分析表格 ===
                        st.subheader("📋 月度详细数据")
                        
                        # 计算环比变化
                        monthly_display = monthly_stats.copy()
                        monthly_display['成交量环比'] = monthly_display['成交量'].pct_change() * 100
                        monthly_display['单价环比'] = monthly_display['平均单价'].pct_change() * 100
                        
                        # 格式化显示
                        monthly_display['年月'] = monthly_display['年月'].astype(str)
                        monthly_display = monthly_display[['年月', '成交量', '成交量环比', '平均单价', '单价环比', '平均成交周期']].round(2)
                        
                        # 添加颜色标识
                        def highlight_changes(val):
                            if pd.isna(val):
                                return ''
                            elif val > 0:
                                return 'color: red'
                            elif val < 0:
                                return 'color: green'
                            else:
                                return ''
                        
                        styled_df = monthly_display.style.applymap(highlight_changes, subset=['成交量环比', '单价环比'])
                        st.dataframe(styled_df, use_container_width=True)
                        
                except Exception as e:
                    st.warning(f"时间序列分析出现问题: {str(e)}")
            
            # 原有的成交分析
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                # 成交周期分析
                if '成交周期(天)' in filtered_df.columns:
                    st.subheader("⏰ 成交周期分布")
                    
                    cycle_data = filtered_df['成交周期(天)'].dropna()
                    if len(cycle_data) > 0:
                        # 成交周期分段
                        cycle_bins = [0, 30, 60, 90, 180, float('inf')]
                        cycle_labels = ['快速成交(≤30天)', '正常成交(31-60天)', '缓慢成交(61-90天)', '困难成交(91-180天)', '超长周期(>180天)']
                        cycle_groups = pd.cut(cycle_data, bins=cycle_bins, labels=cycle_labels)
                        
                        cycle_dist = cycle_groups.value_counts().reset_index()
                        cycle_dist.columns = ['成交周期段', '数量']
                        
                        fig_cycle = px.pie(cycle_dist, names='成交周期段', values='数量', 
                                         title="成交周期分布")
                        st.plotly_chart(fig_cycle, use_container_width=True)
            
            with col2:
                # 折价率分析
                if '挂牌价(万)' in filtered_df.columns and '总价(万)' in filtered_df.columns:
                    st.subheader("💸 成交折价率分析")
                    
                    price_data = filtered_df.dropna(subset=['挂牌价(万)', '总价(万)'])
                    if len(price_data) > 0:
                        price_data['折价率'] = (price_data['挂牌价(万)'] - price_data['总价(万)']) / price_data['挂牌价(万)'] * 100
                        
                        fig_discount = px.histogram(
                            price_data, 
                            x='折价率', 
                            nbins=20,
                            title="成交折价率分布",
                            labels={'折价率': '折价率 (%)', 'count': '房源数量'}
                        )
                        
                        # 添加平均折价率线
                        avg_discount = price_data['折价率'].mean()
                        fig_discount.add_vline(x=avg_discount, line_dash="dash", 
                                             annotation_text=f"平均折价率: {avg_discount:.1f}%")
                        
                        st.plotly_chart(fig_discount, use_container_width=True)

        # --- 小区排行榜 ---
        if data_type == '成交房源' and '小区名称' in filtered_df.columns:
            st.markdown("---")
            st.header("🏆 小区排行榜")
            
            # 排行榜控制选项
            ranking_col1, ranking_col2, ranking_col3 = st.columns(3)
            
            with ranking_col1:
                ranking_metric = st.selectbox(
                    "排序维度",
                    ["成交量", "成交均价", "成交总价", "成交周期"],
                    help="选择小区排行的评判标准"
                )
            
            with ranking_col2:
                top_n = st.selectbox(
                    "显示数量",
                    [10, 20, 30, 50],
                    help="选择显示排行榜前N名"
                )
            
            with ranking_col3:
                sort_order = st.selectbox(
                    "排序方式",
                    ["从高到低", "从低到高"],
                    help="选择排序顺序"
                )
            
            # 计算小区统计数据
            try:
                community_stats = filtered_df.groupby('小区名称').agg({
                    '总价(万)': ['count', 'mean', 'sum'],
                    '单价(元/平)': 'mean' if '单价(元/平)' in filtered_df.columns else lambda x: None,
                    '面积(㎡)': 'mean',
                    '成交周期(天)': 'mean' if '成交周期(天)' in filtered_df.columns else lambda x: None
                }).round(2)
                
                # 重命名列
                if '成交周期(天)' in filtered_df.columns and '单价(元/平)' in filtered_df.columns:
                    community_stats.columns = ['成交套数', '平均总价', '总成交额', '平均单价', '平均面积', '平均成交周期']
                elif '单价(元/平)' in filtered_df.columns:
                    community_stats.columns = ['成交套数', '平均总价', '总成交额', '平均单价', '平均面积']
                    community_stats['平均成交周期'] = None
                elif '成交周期(天)' in filtered_df.columns:
                    community_stats.columns = ['成交套数', '平均总价', '总成交额', '平均面积', '平均成交周期']
                    community_stats['平均单价'] = None
                else:
                    community_stats.columns = ['成交套数', '平均总价', '总成交额', '平均面积']
                    community_stats['平均单价'] = None
                    community_stats['平均成交周期'] = None
                
                community_stats = community_stats.reset_index()
                
                # 过滤掉成交套数少于3套的小区（避免数据不具代表性）
                community_stats = community_stats[community_stats['成交套数'] >= 3]
                
                if len(community_stats) > 0:
                    # 根据选择的维度排序
                    if ranking_metric == "成交量":
                        sort_col = '成交套数'
                        metric_unit = '套'
                        metric_desc = '成交套数越多，说明小区越受欢迎'
                    elif ranking_metric == "成交均价":
                        if '平均单价' in community_stats.columns and community_stats['平均单价'].notna().any():
                            sort_col = '平均单价'
                            metric_unit = '元/㎡'
                            metric_desc = '单价越高，说明小区品质和地段越好'
                        else:
                            st.warning("当前数据中没有单价信息，改为按成交量排序")
                            sort_col = '成交套数'
                            metric_unit = '套'
                            metric_desc = '成交套数越多，说明小区越受欢迎'
                    elif ranking_metric == "成交总价":
                        sort_col = '平均总价'
                        metric_unit = '万元'
                        metric_desc = '总价越高，说明小区房源价值越高'
                    elif ranking_metric == "成交周期":
                        if '平均成交周期' in community_stats.columns and community_stats['平均成交周期'].notna().any():
                            sort_col = '平均成交周期'
                            metric_unit = '天'
                            metric_desc = '成交周期越短，说明小区房源越好卖'
                        else:
                            st.warning("当前数据中没有成交周期信息，改为按成交量排序")
                            sort_col = '成交套数'
                            metric_unit = '套'
                            metric_desc = '成交套数越多，说明小区越受欢迎'
                    
                    # 处理成交周期为空的情况
                    if sort_col == '平均成交周期' and community_stats['平均成交周期'].isna().all():
                        st.warning("成交周期数据不完整，改为按成交量排序")
                        sort_col = '成交套数'
                        metric_unit = '套'
                        metric_desc = '成交套数越多，说明小区越受欢迎'
                    
                    # 排序
                    ascending = (sort_order == "从低到高")
                    if sort_col == '平均成交周期':
                        # 成交周期排序时，先过滤掉空值
                        valid_cycle_data = community_stats.dropna(subset=[sort_col])
                        if len(valid_cycle_data) > 0:
                            community_ranking = valid_cycle_data.sort_values(sort_col, ascending=ascending).head(top_n)
                        else:
                            st.warning("没有有效的成交周期数据")
                            community_ranking = community_stats.sort_values('成交套数', ascending=False).head(top_n)
                    else:
                        community_ranking = community_stats.sort_values(sort_col, ascending=ascending).head(top_n)
                    
                    # 显示排行榜
                    st.subheader(f"🏆 {ranking_metric}排行榜 TOP {top_n}")
                    st.caption(f"💡 {metric_desc}")
                    
                    # 创建排行榜可视化
                    fig_ranking = go.Figure()
                    
                    # 添加柱状图
                    fig_ranking.add_trace(go.Bar(
                        y=community_ranking['小区名称'][::-1],  # 反转顺序，让第一名在顶部
                        x=community_ranking[sort_col][::-1],
                        orientation='h',
                        text=[f"{val:.0f}{metric_unit}" if not pd.isna(val) else "N/A" 
                              for val in community_ranking[sort_col][::-1]],
                        textposition='auto',
                        marker=dict(
                            color=community_ranking[sort_col][::-1],
                            colorscale='Viridis',
                            showscale=True,
                            colorbar=dict(title=f"{ranking_metric}({metric_unit})")
                        )
                    ))
                    
                    fig_ranking.update_layout(
                        title=f"{ranking_metric}排行榜",
                        xaxis_title=f"{ranking_metric} ({metric_unit})",
                        yaxis_title="小区名称",
                        height=max(400, len(community_ranking) * 25),
                        showlegend=False
                    )
                    
                    st.plotly_chart(fig_ranking, use_container_width=True)
                    
                    # 显示详细排行榜表格
                    st.subheader("📋 详细排行榜数据")
                    
                    # 添加排名列
                    ranking_display = community_ranking.copy()
                    ranking_display.insert(0, '排名', range(1, len(ranking_display) + 1))
                    
                    # 格式化数值显示
                    if '平均单价' in ranking_display.columns:
                        ranking_display['平均单价'] = ranking_display['平均单价'].apply(lambda x: f"{x:,.0f}" if not pd.isna(x) else "N/A")
                    ranking_display['平均总价'] = ranking_display['平均总价'].apply(lambda x: f"{x:.1f}" if not pd.isna(x) else "N/A")
                    ranking_display['总成交额'] = ranking_display['总成交额'].apply(lambda x: f"{x:.1f}" if not pd.isna(x) else "N/A")
                    ranking_display['平均面积'] = ranking_display['平均面积'].apply(lambda x: f"{x:.1f}" if not pd.isna(x) else "N/A")
                    if '平均成交周期' in ranking_display.columns:
                        ranking_display['平均成交周期'] = ranking_display['平均成交周期'].apply(lambda x: f"{x:.0f}" if not pd.isna(x) else "N/A")
                    
                    # 重命名列以便显示
                    display_columns = {
                        '排名': '排名',
                        '小区名称': '小区名称',
                        '成交套数': '成交套数',
                        '平均单价': '平均单价(元/㎡)',
                        '平均总价': '平均总价(万)',
                        '总成交额': '总成交额(万)',
                        '平均面积': '平均面积(㎡)'
                    }
                    
                    if '平均成交周期' in ranking_display.columns:
                        display_columns['平均成交周期'] = '平均成交周期(天)'
                    
                    ranking_display = ranking_display.rename(columns=display_columns)
                    
                    # 高亮显示前三名
                    def highlight_top3(row):
                        if row['排名'] == 1:
                            return ['background-color: #FFD700'] * len(row)  # 金色
                        elif row['排名'] == 2:
                            return ['background-color: #C0C0C0'] * len(row)  # 银色
                        elif row['排名'] == 3:
                            return ['background-color: #CD7F32'] * len(row)  # 铜色
                        else:
                            return [''] * len(row)
                    
                    styled_ranking = ranking_display.style.apply(highlight_top3, axis=1)
                    st.dataframe(styled_ranking, use_container_width=True)
                    
                    # 排行榜洞察
                    st.subheader("💡 排行榜洞察")
                    
                    insights = []
                    
                    if len(community_ranking) > 0:
                        top1 = community_ranking.iloc[0]
                        top1_value = top1[sort_col]
                        
                        if ranking_metric == "成交量":
                            insights.append(f"🥇 **{top1['小区名称']}** 以 **{top1_value:.0f}套** 成交量位居榜首，是最受欢迎的小区")
                            if len(community_ranking) > 1:
                                avg_volume = community_ranking['成交套数'].mean()
                                insights.append(f"📊 榜单小区平均成交量为 **{avg_volume:.1f}套**，显示了活跃的交易市场")
                        
                        elif ranking_metric == "成交均价":
                            insights.append(f"🥇 **{top1['小区名称']}** 以 **{top1_value:,.0f}元/㎡** 的均价位居榜首，是区域内的高端小区")
                            if len(community_ranking) > 1:
                                price_range = community_ranking['平均单价'].max() - community_ranking['平均单价'].min()
                                insights.append(f"💰 榜单小区价格差距为 **{price_range:,.0f}元/㎡**，显示了明显的品质分层")
                        
                        elif ranking_metric == "成交总价":
                            insights.append(f"🥇 **{top1['小区名称']}** 以 **{top1_value:.1f}万元** 的均价位居榜首，房源价值最高")
                            avg_area = top1['平均面积']
                            insights.append(f"🏠 该小区平均面积为 **{avg_area:.1f}㎡**，属于{'大户型' if avg_area > 100 else '中等户型' if avg_area > 70 else '小户型'}定位")
                        
                        elif ranking_metric == "成交周期" and not pd.isna(top1_value):
                            insights.append(f"🥇 **{top1['小区名称']}** 以 **{top1_value:.0f}天** 的成交周期位居榜首，是最容易成交的小区")
                            if top1_value <= 30:
                                insights.append("⚡ 成交周期在30天以内，属于快速成交，说明房源非常抢手")
                            elif top1_value <= 60:
                                insights.append("✅ 成交周期在60天以内，属于正常成交速度")
                    
                    # 显示洞察
                    for insight in insights:
                        st.markdown(insight)
                    
                else:
                    st.warning("没有足够的小区数据进行排行榜分析（需要至少3套成交记录）")
                    
            except Exception as e:
                st.error(f"小区排行榜分析出现错误: {str(e)}")

        # --- 详细数据表格 ---
        st.markdown("---")
        st.header("📋 详细数据查看")
        
        # 数据表格选项
        col1, col2, col3 = st.columns(3)
        with col1:
            show_all_columns = st.checkbox("显示所有列", value=False)
        with col2:
            rows_to_show = st.selectbox("显示行数", [10, 25, 50, 100], index=1)
        with col3:
            if st.button("📥 导出数据"):
                csv = filtered_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="下载CSV文件",
                    data=csv,
                    file_name=f"{data_type}_分析数据_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        # 显示数据表格
        if show_all_columns:
            st.dataframe(filtered_df.head(rows_to_show), use_container_width=True)
        else:
            # 选择关键列显示
            key_columns = ['小区名称', '户型', '面积(㎡)', '总价(万)', '单价(元/平)']
            if data_type == '在售房源':
                key_columns.extend(['区域', '商圈', '朝向', '装修', '楼层'])
            else:
                key_columns.extend(['成交日期', '成交周期(天)', '挂牌价(万)'])
            
            available_columns = [col for col in key_columns if col in filtered_df.columns]
            st.dataframe(filtered_df[available_columns].head(rows_to_show), use_container_width=True)

        # --- 洞察报告 ---
        st.markdown("---")
        st.header("🎯 市场洞察")
        
        insights_col1, insights_col2 = st.columns(2)
        
        with insights_col1:
            st.subheader("📊 市场洞察")
            
            insights = []
            
            # 基于筛选条件的洞察
            if active_filters:
                insights.append("🔸 当前分析基于筛选条件，结果更具针对性")
                
                # 户型筛选洞察
                if '户型' in df.columns and 'selected_room_types' in locals():
                    if len(selected_room_types) == 1:
                        insights.append(f"🔸 专注分析{selected_room_types[0]}户型，数据更精准")
                    elif len(selected_room_types) < len(df['户型分类'].unique()):
                        insights.append(f"🔸 对比分析{len(selected_room_types)}种户型，便于横向比较")
                
                # 楼层筛选洞察
                if floor_col in df.columns and 'selected_floor_types' in locals():
                    if len(selected_floor_types) == 1:
                        floor_type = selected_floor_types[0]
                        if floor_type == '高楼层':
                            insights.append("🔸 高楼层房源通常视野好、采光佳，但价格相对较高")
                        elif floor_type == '低楼层':
                            insights.append("🔸 低楼层房源出行便利，适合老人居住，价格相对实惠")
                        elif floor_type == '中楼层':
                            insights.append("🔸 中楼层房源平衡了价格和居住体验，是热门选择")
                
                # 装修筛选洞察
                if '装修' in df.columns and 'selected_decorations' in locals():
                    if len(selected_decorations) == 1:
                        decoration = selected_decorations[0]
                        if decoration == '精装':
                            insights.append("🔸 精装房源即买即住，但总价较高，适合追求便利的购房者")
                        elif decoration == '简装':
                            insights.append("🔸 简装房源价格适中，可根据个人喜好再装修")
                        elif decoration == '毛坯':
                            insights.append("🔸 毛坯房源价格最低，但需要额外装修成本和时间")
            
            # 价格洞察
            if price_stats:
                if price_stats['std'] / price_stats['mean'] > 0.3:
                    insights.append("🔸 市场价格分化明显，存在较大价格差异，投资需谨慎选择区域")
                else:
                    insights.append("🔸 市场价格相对稳定，价格区间集中，适合稳健投资")
            
            # 面积洞察
            if '面积(㎡)' in filtered_df.columns:
                area_data = filtered_df['面积(㎡)'].dropna()
                if len(area_data) > 0:
                    small_ratio = len(area_data[area_data <= 70]) / len(area_data) * 100
                    if small_ratio > 60:
                        insights.append(f"🔸 小户型占主导地位({small_ratio:.1f}%)，刚需市场活跃，租赁需求旺盛")
                    elif small_ratio < 30:
                        insights.append(f"🔸 改善型需求为主({100-small_ratio:.1f}%为大户型)，高端市场活跃")
            
            # 时间序列洞察（仅成交数据）
            if data_type == '成交房源' and '成交日期' in filtered_df.columns:
                try:
                    time_data = filtered_df.dropna(subset=['成交日期'])
                    if len(time_data) > 0:
                        time_data['年月'] = pd.to_datetime(time_data['成交日期']).dt.to_period('M')
                        monthly_volume = time_data.groupby('年月').size()
                        monthly_price = time_data.groupby('年月')['单价(元/平)'].mean()
                        
                        if len(monthly_volume) >= 3:
                            # 成交量趋势分析
                            recent_volumes = monthly_volume.tail(3).values
                            if recent_volumes[-1] > recent_volumes[0] * 1.2:
                                insights.append("🔸 近期成交量呈上升趋势，市场活跃度提升")
                            elif recent_volumes[-1] < recent_volumes[0] * 0.8:
                                insights.append("🔸 近期成交量下降，市场观望情绪浓厚")
                            
                            # 价格趋势分析
                            recent_prices = monthly_price.tail(3).values
                            if len(recent_prices) >= 2:
                                price_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0] * 100
                                if price_trend > 5:
                                    insights.append(f"🔸 价格上涨趋势明显({price_trend:.1f}%)，建议尽早入市")
                                elif price_trend < -5:
                                    insights.append(f"🔸 价格下跌趋势({price_trend:.1f}%)，可等待更好时机")
                                else:
                                    insights.append("🔸 价格相对稳定，市场处于平衡状态")
                except:
                    pass
            
            # 成交周期洞察
            if data_type == '成交房源' and '成交周期(天)' in filtered_df.columns:
                cycle_data = filtered_df['成交周期(天)'].dropna()
                if len(cycle_data) > 0:
                    fast_ratio = len(cycle_data[cycle_data <= 30]) / len(cycle_data) * 100
                    avg_cycle = cycle_data.mean()
                    if fast_ratio > 50:
                        insights.append(f"🔸 市场活跃度高，{fast_ratio:.1f}%房源30天内成交，卖方市场特征明显")
                    elif avg_cycle > 90:
                        insights.append(f"🔸 平均成交周期{avg_cycle:.0f}天，市场消化较慢，买方议价空间大")
                    else:
                        insights.append("🔸 成交周期适中，市场供需相对平衡")
            
            # 折价率洞察
            if data_type == '成交房源' and '挂牌价(万)' in filtered_df.columns and '总价(万)' in filtered_df.columns:
                price_data = filtered_df.dropna(subset=['挂牌价(万)', '总价(万)'])
                if len(price_data) > 0:
                    discount_rates = (price_data['挂牌价(万)'] - price_data['总价(万)']) / price_data['挂牌价(万)'] * 100
                    avg_discount = discount_rates.mean()
                    if avg_discount > 10:
                        insights.append(f"🔸 平均折价率{avg_discount:.1f}%，买方议价能力强")
                    elif avg_discount < 5:
                        insights.append(f"🔸 平均折价率仅{avg_discount:.1f}%，卖方定价权强")
            
            for insight in insights:
                st.write(insight)
        
        with insights_col2:
            st.subheader("💡 投资建议")
            
            recommendations = []
            
            # 基于筛选条件的投资建议
            if active_filters:
                recommendations.append("🔹 基于当前筛选条件的建议：")
                
                # 户型筛选建议
                if '户型' in df.columns and 'selected_room_types' in locals():
                    if '1室' in selected_room_types and len(selected_room_types) == 1:
                        recommendations.append("🔹 1室户型投资回报率高，适合出租给单身白领")
                    elif '2室' in selected_room_types and len(selected_room_types) == 1:
                        recommendations.append("🔹 2室户型需求稳定，适合小家庭和情侣租住")
                    elif '3室' in selected_room_types and len(selected_room_types) == 1:
                        recommendations.append("🔹 3室户型适合三口之家，保值性好，转手容易")
                
                # 楼层筛选建议
                if floor_col in df.columns and 'selected_floor_types' in locals():
                    if '高楼层' in selected_floor_types and len(selected_floor_types) == 1:
                        recommendations.append("🔹 高楼层房源溢价明显，但要注意电梯维护成本")
                    elif '低楼层' in selected_floor_types and len(selected_floor_types) == 1:
                        recommendations.append("🔹 低楼层房源性价比高，适合预算有限的首次购房者")
                
                # 装修筛选建议
                if '装修' in df.columns and 'selected_decorations' in locals():
                    if '毛坯' in selected_decorations and len(selected_decorations) == 1:
                        recommendations.append("🔹 毛坯房总价低，但需预留10-20万装修预算")
                    elif '精装' in selected_decorations and len(selected_decorations) == 1:
                        recommendations.append("🔹 精装房即买即住，适合工作繁忙的购房者")
            
            if data_type == '在售房源':
                # 基于价格分布的建议
                if price_stats and price_stats['std'] / price_stats['mean'] > 0.3:
                    recommendations.append("🔹 价格分化大，重点关注单价低于市场均价20%的优质房源")
                
                # 基于户型分布的建议
                if '面积(㎡)' in filtered_df.columns:
                    area_data = filtered_df['面积(㎡)'].dropna()
                    if len(area_data) > 0:
                        small_ratio = len(area_data[area_data <= 70]) / len(area_data) * 100
                        if small_ratio > 60:
                            recommendations.append("🔹 小户型占主导，适合投资出租，关注地铁沿线和商业区")
                        else:
                            recommendations.append("🔹 大户型较多，适合改善性购房，关注学区和环境品质")
                
                recommendations.extend([
                    "🔹 关注关注人数高但价格合理的房源，市场认可度高",
                    "🔹 优先选择满五唯一的房源，税费成本低"
                ])
            
            else:  # 成交房源
                # 基于时间趋势的建议
                try:
                    if '成交日期' in filtered_df.columns:
                        time_data = filtered_df.dropna(subset=['成交日期'])
                        if len(time_data) > 0:
                            time_data['年月'] = pd.to_datetime(time_data['成交日期']).dt.to_period('M')
                            monthly_volume = time_data.groupby('年月').size()
                            
                            if len(monthly_volume) >= 3:
                                recent_volumes = monthly_volume.tail(3).values
                                if recent_volumes[-1] > recent_volumes[0] * 1.2:
                                    recommendations.append("🔹 成交量上升趋势，建议尽快入市，避免错过机会")
                                elif recent_volumes[-1] < recent_volumes[0] * 0.8:
                                    recommendations.append("🔹 成交量下降，可适当等待，寻找更好的议价机会")
                except:
                    pass
                
                # 基于成交周期的建议
                if '成交周期(天)' in filtered_df.columns:
                    cycle_data = filtered_df['成交周期(天)'].dropna()
                    if len(cycle_data) > 0:
                        avg_cycle = cycle_data.mean()
                        if avg_cycle > 90:
                            recommendations.append("🔹 成交周期较长，买方市场，可适当压价谈判")
                        else:
                            recommendations.append("🔹 成交周期较短，市场活跃，定价需贴近市场")
                
                # 基于折价率的建议
                if '挂牌价(万)' in filtered_df.columns and '总价(万)' in filtered_df.columns:
                    price_data = filtered_df.dropna(subset=['挂牌价(万)', '总价(万)'])
                    if len(price_data) > 0:
                        discount_rates = (price_data['挂牌价(万)'] - price_data['总价(万)']) / price_data['挂牌价(万)'] * 100
                        avg_discount = discount_rates.mean()
                        recommendations.append(f"🔹 参考平均折价率{avg_discount:.1f}%，合理设定期望价格")
                
                recommendations.extend([
                    "🔹 关注成交周期短且折价率低的区域，市场热度高",
                    "🔹 分析季节性波动，选择合适的交易时机"
                ])
            
            for rec in recommendations:
                st.write(rec)

    except Exception as e:
        st.error(f"数据处理出现错误: {str(e)}")
        st.info("请检查上传的CSV文件格式是否正确")

else:
    st.info("👈 请在左侧上传 CSV 文件以开始分析")