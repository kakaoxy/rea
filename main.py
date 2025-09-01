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
def read_data_file(file):
    """读取数据文件，支持CSV和Excel格式"""
    try:
        file_name = file.name.lower()
        
        if file_name.endswith('.csv'):
            # 尝试不同的编码格式读取CSV
            try:
                df = pd.read_csv(file, encoding='utf-8')
            except UnicodeDecodeError:
                try:
                    df = pd.read_csv(file, encoding='gbk')
                except UnicodeDecodeError:
                    try:
                        df = pd.read_csv(file, encoding='utf-8-sig')
                    except UnicodeDecodeError:
                        df = pd.read_csv(file, encoding='latin-1')
        
        elif file_name.endswith(('.xlsx', '.xls')):
            # 读取Excel文件
            engine = 'openpyxl' if file_name.endswith('.xlsx') else 'xlrd'
            
            # 首先检查工作表
            try:
                excel_file = pd.ExcelFile(file, engine=engine)
                sheet_names = excel_file.sheet_names
                
                # 如果有多个工作表，默认读取第一个，但可以在侧边栏选择
                if len(sheet_names) > 1:
                    st.sidebar.info(f"📊 {file.name} 包含 {len(sheet_names)} 个工作表")
                    # 这里可以扩展为让用户选择工作表，暂时使用第一个
                    selected_sheet = sheet_names[0]
                else:
                    selected_sheet = sheet_names[0] if sheet_names else 0
                
                df = pd.read_excel(file, sheet_name=selected_sheet, engine=engine)
                
            except Exception as e:
                # 如果读取失败，尝试默认方式
                df = pd.read_excel(file, engine=engine)
        
        else:
            st.error(f"不支持的文件格式: {file_name}")
            return None
        
        # 基本数据清理
        if df is not None:
            # 删除完全空白的行和列
            df = df.dropna(how='all').dropna(axis=1, how='all')
            
            # 如果第一行看起来像标题行，确保它被用作列名
            if df.columns.dtype == 'object' and any(df.columns.str.contains('Unnamed', na=False)):
                # 可能需要重新设置列名
                if not df.iloc[0].isna().all():
                    df.columns = df.iloc[0]
                    df = df.drop(df.index[0]).reset_index(drop=True)
        
        return df
    
    except Exception as e:
        st.error(f"读取文件 {file.name} 时出错: {str(e)}")
        st.error("请确保文件格式正确，且包含有效的数据")
        return None

def standardize_column_names(df, data_type):
    """智能标准化列名"""
    if df is None or df.empty:
        return df
    
    # 创建列名映射字典
    column_mappings = {}
    
    if data_type == '在售房源':
        # 在售房源的列名映射规则
        mapping_rules = {
            '小区名称': ['小区', '楼盘', '项目名称', '楼盘名称', '小区名', '项目'],
            '面积(㎡)': ['建筑面积(㎡)', '建筑面积', '面积', '房屋面积', '建面', '建筑面积（㎡）', '建筑面积(平米)', '面积(平米)'],
            '总价(万)': ['总价(万)', '总价', '房屋总价', '总价（万）', '总价(万元)', '价格(万)', '售价(万)'],
            '单价(元/平)': ['单价(元/平)', '单价', '房屋单价', '单价（元/平）', '单价(元/㎡)', '单价元/平', '均价'],
            '建成年代': ['年代', '建成年份', '建造年代', '房龄', '建筑年代', '竣工年份'],
            '小区名称': ['小区', '楼盘', '项目名称', '楼盘名称', '小区名', '项目'],
            '户型': ['户型', '房型', '房间格局', '格局'],
            '朝向': ['朝向', '房屋朝向', '方向'],
            '楼层': ['楼层', '楼层信息', '所在楼层', '层数'],
            '装修': ['装修', '装修情况', '装修状况', '装修程度'],
            '关注人数': ['关注人数', '关注数', '浏览量', '关注量']
        }
    else:
        # 成交房源的列名映射规则
        mapping_rules = {
            '总价(万)': ['成交总价(万)', '成交价格(万)', '成交总价', '总价(万)', '总价', '成交价(万)'],
            '单价(元/平)': ['成交单价(元/平)', '成交单价', '单价(元/平)', '单价', '成交均价'],
            '成交日期': ['成交日期', '成交时间', '交易日期', '签约日期'],
            '成交周期(天)': ['成交周期(天)', '成交周期', '交易周期', '销售周期'],
            '挂牌价(万)': ['挂牌价(万)', '挂牌价', '原价(万)', '标价(万)'],
            '面积(㎡)': ['建筑面积(㎡)', '建筑面积', '面积', '房屋面积', '建面'],
            '小区名称': ['小区', '楼盘', '项目名称', '楼盘名称', '小区名', '项目'],
            '户型': ['户型', '房型', '房间格局', '格局'],
        }
    
    # 执行列名映射
    for standard_name, possible_names in mapping_rules.items():
        for possible_name in possible_names:
            if possible_name in df.columns and standard_name not in df.columns:
                column_mappings[possible_name] = standard_name
                break
    
    # 应用映射
    if column_mappings:
        df = df.rename(columns=column_mappings)
        
        # 在侧边栏显示映射信息
        if column_mappings:
            with st.sidebar.expander("🔄 列名标准化"):
                for old_name, new_name in column_mappings.items():
                    st.write(f"• {old_name} → {new_name}")
    
    return df

def clean_and_validate_data(df, data_type):
    """数据清洗和质量验证"""
    quality_report = {
        'original_rows': len(df),
        'issues': [],
        'cleaned_rows': 0,
        'numeric_conversions': {},
        'missing_data': {}
    }
    
    if df is None or df.empty:
        return df, quality_report
    
    # 删除完全空白的行
    df_before = len(df)
    df = df.dropna(how='all')
    empty_rows_removed = df_before - len(df)
    if empty_rows_removed > 0:
        quality_report['issues'].append(f"删除了 {empty_rows_removed} 行空白数据")
    
    # 数值列处理
    numeric_cols = ['总价(万)', '单价(元/平)', '面积(㎡)', '建成年代', '挂牌价(万)', '成交周期(天)', '关注人数']
    
    for col in numeric_cols:
        if col in df.columns:
            original_count = df[col].notna().sum()
            
            # 尝试转换为数值
            df[col] = pd.to_numeric(df[col], errors='coerce')
            
            converted_count = df[col].notna().sum()
            missing_count = len(df) - converted_count
            
            quality_report['numeric_conversions'][col] = {
                'original_valid': original_count,
                'converted_valid': converted_count,
                'missing': missing_count,
                'missing_rate': missing_count / len(df) * 100
            }
            
            # 数据范围验证
            if col == '总价(万)' and converted_count > 0:
                invalid_prices = df[(df[col] <= 0) | (df[col] > 50000)].index
                if len(invalid_prices) > 0:
                    df.loc[invalid_prices, col] = np.nan
                    quality_report['issues'].append(f"{col}: 发现 {len(invalid_prices)} 个异常价格值")
            
            elif col == '单价(元/平)' and converted_count > 0:
                invalid_unit_prices = df[(df[col] <= 0) | (df[col] > 500000)].index
                if len(invalid_unit_prices) > 0:
                    df.loc[invalid_unit_prices, col] = np.nan
                    quality_report['issues'].append(f"{col}: 发现 {len(invalid_unit_prices)} 个异常单价值")
            
            elif col == '面积(㎡)' and converted_count > 0:
                invalid_areas = df[(df[col] <= 0) | (df[col] > 1000)].index
                if len(invalid_areas) > 0:
                    df.loc[invalid_areas, col] = np.nan
                    quality_report['issues'].append(f"{col}: 发现 {len(invalid_areas)} 个异常面积值")
            
            elif col == '建成年代' and converted_count > 0:
                current_year = datetime.now().year
                invalid_years = df[(df[col] < 1900) | (df[col] > current_year)].index
                if len(invalid_years) > 0:
                    df.loc[invalid_years, col] = np.nan
                    quality_report['issues'].append(f"{col}: 发现 {len(invalid_years)} 个异常年代值")
    
    # 文本列清理
    text_cols = ['小区名称', '户型', '朝向', '楼层', '装修']
    for col in text_cols:
        if col in df.columns:
            # 去除前后空格
            df[col] = df[col].astype(str).str.strip()
            # 替换空字符串为NaN
            df[col] = df[col].replace('', np.nan)
            df[col] = df[col].replace('nan', np.nan)
    
    # 计算最终数据质量
    quality_report['cleaned_rows'] = len(df)
    quality_report['data_completeness'] = {}
    
    key_columns = ['小区名称', '总价(万)', '单价(元/平)', '面积(㎡)']
    for col in key_columns:
        if col in df.columns:
            completeness = df[col].notna().sum() / len(df) * 100
            quality_report['data_completeness'][col] = completeness
    
    return df, quality_report

def display_data_quality_report(quality_report):
    """显示数据质量报告"""
    st.sidebar.subheader("📊 数据质量报告")
    
    # 基本统计
    st.sidebar.metric("原始数据行数", quality_report['original_rows'])
    st.sidebar.metric("清洗后行数", quality_report['cleaned_rows'])
    
    # 数据完整性
    if quality_report['data_completeness']:
        st.sidebar.write("**关键字段完整性:**")
        for col, completeness in quality_report['data_completeness'].items():
            color = "green" if completeness > 90 else "orange" if completeness > 70 else "red"
            st.sidebar.markdown(f"• {col}: :{color}[{completeness:.1f}%]")
    
    # 数据问题
    if quality_report['issues']:
        st.sidebar.write("**发现的问题:**")
        for issue in quality_report['issues']:
            st.sidebar.warning(f"⚠️ {issue}")
    
    # 数值转换详情
    if quality_report['numeric_conversions']:
        with st.sidebar.expander("🔢 数值转换详情"):
            for col, stats in quality_report['numeric_conversions'].items():
                if stats['missing_rate'] > 0:
                    st.write(f"**{col}:**")
                    st.write(f"  • 有效数据: {stats['converted_valid']} 行")
                    st.write(f"  • 缺失数据: {stats['missing']} 行 ({stats['missing_rate']:.1f}%)")
    
    if not quality_report['issues']:
        st.sidebar.success("✅ 数据质量良好")

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

def analyze_property_competitiveness(selected_property, all_properties):
    """分析房源竞争力"""
    analysis = {}
    
    # 1. 筛选竞争对手
    competitors = filter_competitors(selected_property, all_properties)
    analysis['competitors'] = competitors
    analysis['total_competitors'] = len(competitors)
    
    # 2. 价格竞争力分析
    analysis['price_analysis'] = analyze_price_competitiveness(selected_property, competitors)
    
    # 3. 面积性价比分析
    analysis['area_analysis'] = analyze_area_competitiveness(selected_property, competitors)
    
    # 4. 关注度分析
    analysis['attention_analysis'] = analyze_attention_competitiveness(selected_property, competitors)
    
    # 5. 房源特色分析
    analysis['feature_analysis'] = analyze_feature_competitiveness(selected_property, competitors)
    
    # 6. 综合竞争力评分
    analysis['overall_score'] = calculate_overall_competitiveness(analysis)
    
    return analysis

def filter_competitors(selected_property, all_properties):
    """筛选竞争对手房源"""
    # 排除自己
    competitors = all_properties[all_properties.index != selected_property.name].copy()
    
    # 筛选条件：同户型或相近面积
    target_area = selected_property['建筑面积(㎡)']
    target_rooms = selected_property['户型']
    
    # 面积范围：±20%
    area_range = target_area * 0.2
    area_filter = (competitors['建筑面积(㎡)'] >= target_area - area_range) & \
                  (competitors['建筑面积(㎡)'] <= target_area + area_range)
    
    # 户型匹配或面积相近
    room_filter = competitors['户型'] == target_rooms
    
    # 组合筛选：同户型优先，否则选择面积相近的
    same_room_competitors = competitors[room_filter]
    similar_area_competitors = competitors[area_filter & ~room_filter]
    
    # 合并结果，同户型的排在前面
    final_competitors = pd.concat([same_room_competitors, similar_area_competitors]).drop_duplicates()
    
    return final_competitors

def analyze_price_competitiveness(selected_property, competitors):
    """分析价格竞争力"""
    if len(competitors) == 0:
        return {"rank": "无竞争对手", "percentile": 100}
    
    target_price = selected_property['单价(元/平)']
    competitor_prices = competitors['单价(元/平)'].dropna()
    
    if len(competitor_prices) == 0:
        return {"rank": "无价格数据", "percentile": 50}
    
    # 计算价格排名（价格越低排名越好）
    lower_count = len(competitor_prices[competitor_prices > target_price])
    total_count = len(competitor_prices) + 1  # 包括自己
    percentile = (lower_count + 1) / total_count * 100
    
    avg_price = competitor_prices.mean()
    median_price = competitor_prices.median()
    
    return {
        "target_price": target_price,
        "avg_competitor_price": avg_price,
        "median_competitor_price": median_price,
        "price_advantage": avg_price - target_price,
        "percentile": percentile,
        "rank": f"{lower_count + 1}/{total_count}"
    }

def analyze_area_competitiveness(selected_property, competitors):
    """分析面积性价比竞争力"""
    if len(competitors) == 0:
        return {"rank": "无竞争对手"}
    
    target_area = selected_property['建筑面积(㎡)']
    target_total_price = selected_property['总价(万)']
    
    competitor_data = competitors.dropna(subset=['建筑面积(㎡)', '总价(万)'])
    
    if len(competitor_data) == 0:
        return {"rank": "无面积数据"}
    
    # 计算性价比：面积/总价
    target_value_ratio = target_area / target_total_price
    competitor_ratios = competitor_data['建筑面积(㎡)'] / competitor_data['总价(万)']
    
    # 排名（性价比越高排名越好）
    better_count = len(competitor_ratios[competitor_ratios < target_value_ratio])
    total_count = len(competitor_ratios) + 1
    percentile = (better_count + 1) / total_count * 100
    
    return {
        "target_ratio": target_value_ratio,
        "avg_competitor_ratio": competitor_ratios.mean(),
        "percentile": percentile,
        "rank": f"{better_count + 1}/{total_count}"
    }

def analyze_attention_competitiveness(selected_property, competitors):
    """分析关注度竞争力"""
    if len(competitors) == 0 or '关注人数' not in competitors.columns:
        return {"rank": "无关注度数据"}
    
    target_attention = selected_property['关注人数']
    competitor_attention = competitors['关注人数'].dropna()
    
    if len(competitor_attention) == 0:
        return {"rank": "无关注度数据"}
    
    # 排名（关注度越高排名越好）
    lower_count = len(competitor_attention[competitor_attention < target_attention])
    total_count = len(competitor_attention) + 1
    percentile = (lower_count + 1) / total_count * 100
    
    return {
        "target_attention": target_attention,
        "avg_competitor_attention": competitor_attention.mean(),
        "median_competitor_attention": competitor_attention.median(),
        "percentile": percentile,
        "rank": f"{lower_count + 1}/{total_count}"
    }

def analyze_feature_competitiveness(selected_property, competitors):
    """分析房源特色竞争力"""
    features = {}
    
    # 朝向分析
    if '朝向' in selected_property:
        target_orientation = selected_property['朝向']
        south_facing = '南' in str(target_orientation)
        features['south_facing'] = south_facing
        
        if len(competitors) > 0 and '朝向' in competitors.columns:
            competitor_south = competitors['朝向'].apply(lambda x: '南' in str(x) if pd.notna(x) else False)
            south_ratio = competitor_south.mean() * 100
            features['south_facing_advantage'] = south_facing and south_ratio < 50
    
    # 楼层分析
    if '楼层' in selected_property:
        target_floor = selected_property['楼层']
        is_high_floor = '高楼层' in str(target_floor)
        is_low_floor = '低楼层' in str(target_floor)
        features['floor_type'] = target_floor
        features['is_high_floor'] = is_high_floor
        features['is_low_floor'] = is_low_floor
    
    # 房源标签分析
    if '房源标签' in selected_property and pd.notna(selected_property['房源标签']):
        tags = str(selected_property['房源标签']).split('|')
        features['tags'] = [tag.strip() for tag in tags]
        features['has_metro'] = any('地铁' in tag for tag in tags)
        features['has_vr'] = any('VR' in tag for tag in tags)
        features['tax_advantage'] = any('满五' in tag for tag in tags)
    
    return features

def calculate_overall_competitiveness(analysis):
    """计算综合竞争力评分"""
    scores = []
    weights = []
    
    # 价格竞争力 (权重: 30%)
    if 'percentile' in analysis['price_analysis']:
        price_score = 100 - analysis['price_analysis']['percentile']  # 价格越低分数越高
        scores.append(price_score)
        weights.append(0.3)
    
    # 面积性价比 (权重: 25%)
    if 'percentile' in analysis['area_analysis']:
        area_score = analysis['area_analysis']['percentile']  # 性价比越高分数越高
        scores.append(area_score)
        weights.append(0.25)
    
    # 关注度 (权重: 20%)
    if 'percentile' in analysis['attention_analysis']:
        attention_score = analysis['attention_analysis']['percentile']
        scores.append(attention_score)
        weights.append(0.2)
    
    # 特色加分 (权重: 25%)
    feature_score = 50  # 基础分
    features = analysis['feature_analysis']
    
    if features.get('south_facing', False):
        feature_score += 15
    if features.get('has_metro', False):
        feature_score += 10
    if features.get('tax_advantage', False):
        feature_score += 10
    if features.get('has_vr', False):
        feature_score += 5
    if features.get('is_high_floor', False):
        feature_score += 10
    
    feature_score = min(feature_score, 100)  # 最高100分
    scores.append(feature_score)
    weights.append(0.25)
    
    # 计算加权平均分
    if scores:
        overall_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        return round(overall_score, 1)
    
    return 50.0

def display_competitiveness_analysis(analysis, selected_property):
    """显示竞争力分析结果"""
    
    # 综合评分展示
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        score = analysis['overall_score']
        if score >= 80:
            score_color = "green"
            score_level = "优秀"
            score_icon = "🏆"
        elif score >= 65:
            score_color = "blue"
            score_level = "良好"
            score_icon = "👍"
        elif score >= 50:
            score_color = "orange"
            score_level = "一般"
            score_icon = "⚖️"
        else:
            score_color = "red"
            score_level = "较弱"
            score_icon = "⚠️"
        
        st.markdown(f"### {score_icon} 综合竞争力评分")
        st.markdown(f"## :{score_color}[{score}分] - {score_level}")
    
    with col2:
        st.metric("🏠 竞争对手数量", f"{analysis['total_competitors']}套")
    
    with col3:
        if analysis['total_competitors'] > 0:
            market_position = "激烈竞争" if analysis['total_competitors'] > 10 else "适度竞争" if analysis['total_competitors'] > 5 else "竞争较少"
            st.metric("📊 市场竞争", market_position)
    
    # 详细分析
    st.subheader("📊 详细竞争力分析")
    
    # 创建四个分析维度的标签页
    tab1, tab2, tab3, tab4 = st.tabs(["💰 价格竞争力", "📐 面积性价比", "👥 市场关注度", "⭐ 房源特色"])
    
    with tab1:
        price_analysis = analysis['price_analysis']
        if 'percentile' in price_analysis:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("🏷️ 价格排名", price_analysis['rank'])
                st.metric("📊 价格百分位", f"{price_analysis['percentile']:.1f}%")
                
                if price_analysis['price_advantage'] > 0:
                    st.success(f"💰 价格优势：比均价低 {price_analysis['price_advantage']:,.0f} 元/㎡")
                else:
                    st.warning(f"💸 价格劣势：比均价高 {abs(price_analysis['price_advantage']):,.0f} 元/㎡")
            
            with col2:
                # 价格对比图
                fig_price = go.Figure()
                
                fig_price.add_trace(go.Bar(
                    x=['目标房源', '竞争对手均价', '竞争对手中位价'],
                    y=[price_analysis['target_price'], 
                       price_analysis['avg_competitor_price'], 
                       price_analysis['median_competitor_price']],
                    marker_color=['red', 'blue', 'green'],
                    text=[f"{x:,.0f}" for x in [price_analysis['target_price'], 
                                               price_analysis['avg_competitor_price'], 
                                               price_analysis['median_competitor_price']]],
                    textposition='auto'
                ))
                
                fig_price.update_layout(
                    title="单价对比分析",
                    yaxis_title="单价 (元/㎡)",
                    height=300
                )
                
                st.plotly_chart(fig_price, use_container_width=True)
    
    with tab2:
        area_analysis = analysis['area_analysis']
        if 'percentile' in area_analysis:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("📐 性价比排名", area_analysis['rank'])
                st.metric("📊 性价比百分位", f"{area_analysis['percentile']:.1f}%")
                
                ratio_advantage = area_analysis['target_ratio'] - area_analysis['avg_competitor_ratio']
                if ratio_advantage > 0:
                    st.success(f"🎯 性价比优势：每万元多 {ratio_advantage:.2f} ㎡")
                else:
                    st.warning(f"📉 性价比劣势：每万元少 {abs(ratio_advantage):.2f} ㎡")
            
            with col2:
                # 性价比对比
                fig_ratio = go.Figure()
                
                fig_ratio.add_trace(go.Bar(
                    x=['目标房源', '竞争对手均值'],
                    y=[area_analysis['target_ratio'], area_analysis['avg_competitor_ratio']],
                    marker_color=['red', 'blue'],
                    text=[f"{x:.2f}" for x in [area_analysis['target_ratio'], area_analysis['avg_competitor_ratio']]],
                    textposition='auto'
                ))
                
                fig_ratio.update_layout(
                    title="面积性价比对比 (㎡/万元)",
                    yaxis_title="性价比 (㎡/万元)",
                    height=300
                )
                
                st.plotly_chart(fig_ratio, use_container_width=True)
    
    with tab3:
        attention_analysis = analysis['attention_analysis']
        if 'percentile' in attention_analysis:
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("👥 关注度排名", attention_analysis['rank'])
                st.metric("📊 关注度百分位", f"{attention_analysis['percentile']:.1f}%")
                
                attention_advantage = attention_analysis['target_attention'] - attention_analysis['avg_competitor_attention']
                if attention_advantage > 0:
                    st.success(f"🔥 关注度优势：比均值高 {attention_advantage:.0f} 人")
                else:
                    st.info(f"📊 关注度：比均值低 {abs(attention_advantage):.0f} 人")
            
            with col2:
                # 关注度对比
                fig_attention = go.Figure()
                
                fig_attention.add_trace(go.Bar(
                    x=['目标房源', '竞争对手均值', '竞争对手中位数'],
                    y=[attention_analysis['target_attention'], 
                       attention_analysis['avg_competitor_attention'], 
                       attention_analysis['median_competitor_attention']],
                    marker_color=['red', 'blue', 'green'],
                    text=[f"{x:.0f}" for x in [attention_analysis['target_attention'], 
                                              attention_analysis['avg_competitor_attention'], 
                                              attention_analysis['median_competitor_attention']]],
                    textposition='auto'
                ))
                
                fig_attention.update_layout(
                    title="关注度对比分析",
                    yaxis_title="关注人数",
                    height=300
                )
                
                st.plotly_chart(fig_attention, use_container_width=True)
    
    with tab4:
        features = analysis['feature_analysis']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏠 房源特色")
            
            # 朝向优势
            if features.get('south_facing', False):
                st.success("🌞 朝向优势：南向采光好")
            else:
                st.info(f"🧭 朝向：{selected_property.get('朝向', '未知')}")
            
            # 楼层特点
            if features.get('is_high_floor', False):
                st.success("🏢 楼层优势：高楼层视野好")
            elif features.get('is_low_floor', False):
                st.info("🏢 楼层特点：低楼层出行便利")
            else:
                st.info(f"🏢 楼层：{selected_property.get('楼层', '未知')}")
        
        with col2:
            st.subheader("🏷️ 房源标签优势")
            
            if 'tags' in features:
                for tag in features['tags']:
                    if '地铁' in tag:
                        st.success(f"🚇 {tag}")
                    elif 'VR' in tag:
                        st.info(f"📱 {tag}")
                    elif '满五' in tag:
                        st.success(f"💰 {tag}")
                    else:
                        st.info(f"🏷️ {tag}")
            else:
                st.info("暂无特殊标签")
    
    # 竞争对手列表
    if analysis['total_competitors'] > 0:
        st.subheader("🏘️ 主要竞争对手")
        
        competitors = analysis['competitors']
        
        # 选择显示的竞争对手数量
        display_count = min(10, len(competitors))
        top_competitors = competitors.head(display_count)
        
        # 创建对比表格
        comparison_data = []
        for idx, competitor in top_competitors.iterrows():
            comparison_data.append({
                '小区': competitor['小区'],
                '户型': competitor['户型'],
                '面积(㎡)': competitor['建筑面积(㎡)'],
                '总价(万)': competitor['总价(万)'],
                '单价(元/㎡)': f"{competitor['单价(元/平)']:,.0f}",
                '朝向': competitor['朝向'],
                '楼层': competitor['楼层'],
                '关注人数': competitor['关注人数']
            })
        
        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(comparison_df, use_container_width=True)
        
        # 投资建议
        st.subheader("💡 投资建议")
        
        recommendations = []
        
        # 基于综合评分的建议
        if score >= 80:
            recommendations.append("🏆 **优秀房源**：综合竞争力强，建议优先考虑")
        elif score >= 65:
            recommendations.append("👍 **良好选择**：各方面表现均衡，值得考虑")
        elif score >= 50:
            recommendations.append("⚖️ **谨慎考虑**：存在一定劣势，需要综合评估")
        else:
            recommendations.append("⚠️ **需要谨慎**：竞争力较弱，建议寻找更好选择")
        
        # 基于价格的建议
        price_analysis = analysis['price_analysis']
        if 'price_advantage' in price_analysis:
            if price_analysis['price_advantage'] > 5000:
                recommendations.append("💰 **价格优势明显**：单价比同类房源低，性价比高")
            elif price_analysis['price_advantage'] < -5000:
                recommendations.append("💸 **价格偏高**：建议与业主协商降价空间")
        
        # 基于关注度的建议
        attention_analysis = analysis['attention_analysis']
        if 'percentile' in attention_analysis:
            if attention_analysis['percentile'] > 80:
                recommendations.append("🔥 **市场热门**：关注度高，需要快速决策")
            elif attention_analysis['percentile'] < 20:
                recommendations.append("🤔 **关注度低**：可能存在隐藏问题，需要仔细调研")
        
        # 基于特色的建议
        features = analysis['feature_analysis']
        if features.get('south_facing', False) and features.get('has_metro', False):
            recommendations.append("⭐ **地段优势**：南向+地铁，居住和投资价值都很好")
        
        if features.get('tax_advantage', False):
            recommendations.append("💰 **税费优势**：满五年，交易成本低")
        
        for rec in recommendations:
            st.write(rec)

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
    f"📁 上传「{data_type}」数据文件",
    type=['csv', 'xlsx', 'xls'],
    accept_multiple_files=True,
    help="支持上传多个CSV或Excel文件，系统将自动合并分析"
)

# --- 数据加载与处理 ---
if uploaded_files:
    try:
        # 读取所有上传的数据文件并合并
        df_list = []
        file_info = []
        
        for file in uploaded_files:
            df_temp = read_data_file(file)
            if df_temp is not None:
                df_list.append(df_temp)
                file_info.append({
                    'name': file.name,
                    'rows': len(df_temp),
                    'format': file.name.split('.')[-1].upper()
                })
        
        if not df_list:
            st.error("没有成功读取任何文件，请检查文件格式")
            st.stop()
        
        df = pd.concat(df_list, ignore_index=True)
        
        # 显示文件读取信息
        if len(file_info) > 1:
            st.sidebar.success(f"✅ 成功读取 {len(file_info)} 个文件")
            with st.sidebar.expander("📄 文件详情"):
                for info in file_info:
                    st.write(f"• {info['name']} ({info['format']}) - {info['rows']} 行")
        else:
            st.sidebar.success(f"✅ 成功读取文件: {file_info[0]['name']}")
        
        # 数据预览选项
        if st.sidebar.checkbox("👀 数据预览", help="查看原始数据的前几行"):
            st.sidebar.subheader("📋 数据预览")
            preview_rows = st.sidebar.slider("预览行数", 1, 10, 3)
            st.sidebar.dataframe(df.head(preview_rows), use_container_width=True)
            st.sidebar.caption(f"数据形状: {df.shape[0]} 行 × {df.shape[1]} 列")
        
        # 智能列名标准化处理
        df = standardize_column_names(df, data_type)
        
        # 数据质量检查和清洗
        df, quality_report = clean_and_validate_data(df, data_type)
        
        # 显示数据质量报告
        if quality_report and st.sidebar.checkbox("📊 数据质量报告"):
            display_data_quality_report(quality_report)

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

        # --- 房源竞争力分析 ---
        if data_type == '在售房源':
            st.markdown("---")
            st.header("🎯 房源竞争力分析")
            
            # 房源选择器
            st.subheader("🏠 选择目标房源")
            
            # 创建房源选择的显示格式
            def format_property_display(row):
                return f"{row['小区']} | {row['户型']} | {row['建筑面积(㎡)']}㎡ | {row['总价(万)']}万 | {row['单价(元/平)']:,.0f}元/㎡"
            
            # 为每个房源创建唯一标识
            filtered_df['房源显示'] = filtered_df.apply(format_property_display, axis=1)
            filtered_df['房源ID'] = range(len(filtered_df))
            
            # 房源选择下拉框
            selected_property_idx = st.selectbox(
                "选择要分析的房源：",
                options=filtered_df['房源ID'].tolist(),
                format_func=lambda x: filtered_df.loc[filtered_df['房源ID'] == x, '房源显示'].iloc[0],
                help="选择一套房源进行竞争力分析"
            )
            
            if selected_property_idx is not None:
                selected_property = filtered_df[filtered_df['房源ID'] == selected_property_idx].iloc[0]
                
                # 显示选中房源的详细信息
                st.subheader("📋 目标房源信息")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("🏢 小区", selected_property['小区'])
                    st.metric("🏠 户型", selected_property['户型'])
                with col2:
                    st.metric("💰 总价", f"{selected_property['总价(万)']}万")
                    st.metric("🏷️ 单价", f"{selected_property['单价(元/平)']:,.0f}元/㎡")
                with col3:
                    st.metric("📐 面积", f"{selected_property['建筑面积(㎡)']}㎡")
                    st.metric("🧭 朝向", selected_property['朝向'])
                with col4:
                    st.metric("🏢 楼层", selected_property['楼层'])
                    st.metric("👥 关注度", f"{selected_property['关注人数']}人")
                
                # 房源标签展示
                if '房源标签' in selected_property and pd.notna(selected_property['房源标签']):
                    st.write("🏷️ **房源标签：**", selected_property['房源标签'])
                
                # 竞争力分析
                st.subheader("⚔️ 竞争力分析")
                
                # 定义竞争对手筛选条件
                competitor_analysis = analyze_property_competitiveness(selected_property, filtered_df)
                
                # 显示竞争分析结果
                display_competitiveness_analysis(competitor_analysis, selected_property)

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