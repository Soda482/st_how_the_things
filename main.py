"""
主应用程序入口
你今天活得怎么样？
全生活操作系统 - 第二大脑 + 私人生活教练
"""

import streamlit as st
import sys
from pathlib import Path
from datetime import datetime, date

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from utils.config_loader import load_config, get_config
from utils.logger import setup_logger
from database import init_db, check_connection
from modules.diet.diet_records import DietRecord, add_diet_record, get_diet_by_date, get_diet_summary
from modules.diet.enhanced_nutrition_calculator import EnhancedNutritionCalculator
from modules.diet.food_database import search_food, get_food_by_name, get_food_categories, get_foods_by_category, calculate_nutrition, init_food_database

# 配置日志
logger = setup_logger()

# 页面配置
st.set_page_config(
    page_title="你今天活得怎么样？",
    page_icon="🌟",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 自定义 CSS
with open("css/styles.css", "r", encoding="utf-8") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def init_session_state():
    """初始化会话状态"""
    if "initialized" not in st.session_state:
        st.session_state.initialized = True
        st.session_state.current_date = date.today().isoformat()
        st.session_state.theme = get_config("theme.default", "purple")
        st.session_state.anonymous_mode = get_config("app.anonymous_mode", False)


def load_custom_css():
    """加载自定义样式"""
    theme = st.session_state.get("theme", "purple")
    
    theme_css = ""
    if theme == "fresh_blue":
        theme_css = """
        <style>
        [data-theme="fresh_blue"] {
            --primary: #0EA5E9;
            --bg-primary: #FFFFFF;
            --bg-secondary: #F0F9FF;
            --bg-card: #FFFFFF;
            --text-primary: #0C4A6E;
            --text-secondary: #075985;
        }
        </style>
        """
    elif theme == "fresh_green":
        theme_css = """
        <style>
        [data-theme="fresh_green"] {
            --primary: #10B981;
            --bg-primary: #FFFFFF;
            --bg-secondary: #F0FDF4;
            --bg-card: #FFFFFF;
            --text-primary: #064E3B;
            --text-secondary: #047857;
        }
        </style>
        """
    elif theme == "warm_orange":
        theme_css = """
        <style>
        [data-theme="warm_orange"] {
            --primary: #F97316;
            --bg-primary: #FFFFFF;
            --bg-secondary: #FFF7ED;
            --bg-card: #FFFFFF;
            --text-primary: #7C2D12;
            --text-secondary: #9A3412;
        }
        </style>
        """
    
    st.markdown(theme_css, unsafe_allow_html=True)


def get_ai_greeting():
    """获取 AI 问候语"""
    hour = datetime.now().hour
    
    if 5 <= hour < 12:
        greeting = "早上好！今天也要元气满满哦 ☀️"
    elif 12 <= hour < 14:
        greeting = "中午好！记得吃午饭呀 🍱"
    elif 14 <= hour < 18:
        greeting = "下午好！来杯咖啡提提神 ☕"
    elif 18 <= hour < 22:
        greeting = "晚上好！今天辛苦了 🌙"
    else:
        greeting = "夜深了，早点休息吧 🌟"
    
    return greeting


def main():
    """主函数"""
    try:
        # 加载配置
        load_config()
        
        # 初始化会话
        init_session_state()
        
        # 加载主题样式
        load_custom_css()
        
        # 初始化数据库（确保所有表都存在）
        init_db()
        
        # 检查数据库连接
        if not check_connection():
            st.error("数据库连接失败！")
            return
        
        # 侧边栏导航
        with st.sidebar:
            st.markdown("### 🌟 生活驾驶舱")
            
            # 主题选择
            themes = ["purple", "fresh_blue", "fresh_green", "warm_orange"]
            theme_names = {
                "purple": "💜 优雅紫",
                "fresh_blue": "💙 清新蓝",
                "fresh_green": "💚 清新绿",
                "warm_orange": "🧡 温暖橙"
            }
            
            # 如果当前主题不在新列表中，默认选择第一个
            if st.session_state.theme not in themes:
                st.session_state.theme = themes[0]
            
            theme = st.selectbox(
                "选择主题",
                themes,
                index=themes.index(st.session_state.theme),
                format_func=lambda x: theme_names.get(x, x)
            )
            
            if theme != st.session_state.theme:
                st.session_state.theme = theme
                st.rerun()
            
            st.divider()
            
            # 导航菜单
            menu_items = {
                "仪表盘": "dashboard",
                "饮食营养": "diet",
                "消费记账": "expense",
                "运动健康": "exercise",
                "睡眠管理": "sleep",
                "情绪日记": "mood",
                "AI 助手": "ai",
                "设置": "settings"
            }
            
            for label, page in menu_items.items():
                icon = {
                    "仪表盘": "🏠",
                    "饮食营养": "🍽️",
                    "消费记账": "💰",
                    "运动健康": "🏃",
                    "睡眠管理": "😴",
                    "情绪日记": "💭",
                    "AI 助手": "🤖",
                    "设置": "⚙️"
                }.get(label, "📌")
                
                if st.button(f"{icon} {label}", key=f"nav_{page}", use_container_width=True):
                    st.session_state.current_page = page
                    st.rerun()
        
        # 主内容区
        current_page = st.session_state.get("current_page", "dashboard")
        
        if current_page == "dashboard":
            render_dashboard()
        elif current_page == "diet":
            render_diet_page()
        elif current_page == "expense":
            render_expense_page()
        elif current_page == "exercise":
            render_exercise_page()
        elif current_page == "sleep":
            render_sleep_page()
        elif current_page == "mood":
            render_mood_page()
        elif current_page == "ai":
            render_ai_page()
        elif current_page == "settings":
            render_settings_page()
        else:
            render_dashboard()
        
        # 底部快捷操作
        render_quick_actions()
        
    except Exception as e:
        logger.error(f"应用错误: {e}")
        st.error(f"发生错误: {e}")


def render_dashboard():
    """渲染仪表盘页面"""
    st.title("🌟 你今天活得怎么样？")
    st.markdown(f"**{get_ai_greeting()}**")
    
    # 日期选择器
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        selected_date = st.date_input("选择日期", date.today())
    with col2:
        st.metric("今日摄入", "0", "0")
    with col3:
        st.metric("今日支出", "¥0", "¥0")
    
    st.divider()
    
    # 四大核心指标
    st.markdown("### 📊 今日概览")
    
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = [
        ("🔥 热量", "0/2000", "0%", "#EF4444"),
        ("🏃 运动", "0/10000", "0%", "#10B981"),
        ("😴 睡眠", "0/8h", "0%", "#3B82F6"),
        ("💰 预算", "¥0/¥3000", "0%", "#F59E0B")
    ]
    
    for col, (label, value, pct, color) in zip([col1, col2, col3, col4], metrics):
        with col:
            st.markdown(f"""
            <div class="card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{label}</div>
                <div style="font-size: 1.5rem; font-weight: bold;">{value}</div>
                <div class="progress-bar" style="margin-top: 0.5rem;">
                    <div class="fill" style="width: {pct}; background: {color};"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # 动态时间轴
    st.markdown("### ⏰ 今日时间轴")
    
    st.info("📝 暂无今日记录，开始记录你的生活吧！")
    
    # 成就徽章展示区
    st.markdown("### 🏆 成就徽章")
    
    badge_col1, badge_col2, badge_col3, badge_col4 = st.columns(4)
    badges = ["初学者", "坚持3天", "健康达人", "省钱高手"]
    
    for col, badge in zip([badge_col1, badge_col2, badge_col3, badge_col4], badges):
        with col:
            st.markdown(f"""
            <div style="text-align: center; opacity: 0.5;">
                <div style="font-size: 2rem;">🔒</div>
                <div style="font-size: 0.85rem; color: var(--text-secondary);">{badge}</div>
            </div>
            """, unsafe_allow_html=True)


def render_diet_page():
    """渲染饮食营养页面"""
    st.title("🍽️ 饮食营养")
    
    # 初始化减肥模式和食物数据库
    if "weight_loss_mode" not in st.session_state:
        st.session_state.weight_loss_mode = False
    if "food_search_results" not in st.session_state:
        st.session_state.food_search_results = []
    if "selected_food" not in st.session_state:
        st.session_state.selected_food = None
    if "food_quantity" not in st.session_state:
        st.session_state.food_quantity = 100
    
    # 初始化食物数据库（首次运行）
    init_food_database()
    
    # 减肥模式开关
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        weight_loss_mode = st.toggle(
            "🔥 减肥模式", 
            value=st.session_state.weight_loss_mode,
            help="开启后会自动调整建议摄入热量，制造热量缺口"
        )
        if weight_loss_mode != st.session_state.weight_loss_mode:
            st.session_state.weight_loss_mode = weight_loss_mode
            st.rerun()
    
    with col2:
        st.metric("今日摄入", "0", "0")
    
    with col3:
        st.metric("剩余额度", "0", "0")
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 记录", "📊 统计", "🎯 建议", "🍱 模板"])
    
    with tab1:
        st.markdown("#### 快速记录")
        
        # 初始化会话状态
        if "selected_category" not in st.session_state:
            st.session_state.selected_category = "全部"
        
        # 搜索区域布局
        col_search, col_category = st.columns([2, 1])
        
        with col_search:
            search_keyword = st.text_input(
                "🔍 搜索食物", 
                placeholder="输入食物名称，如：米饭、鸡胸肉",
                key="food_search_input"
            )
        
        with col_category:
            # 获取所有分类
            categories = ["全部"] + get_food_categories()
            st.session_state.selected_category = st.selectbox(
                "📁 分类",
                categories,
                index=categories.index(st.session_state.selected_category) if st.session_state.selected_category in categories else 0
            )
        
        # 搜索结果展示区域
        search_results = []
        if search_keyword or st.session_state.selected_category != "全部":
            if st.session_state.selected_category != "全部":
                # 按分类筛选
                category_foods = get_foods_by_category(st.session_state.selected_category)
                if search_keyword:
                    # 同时按关键词筛选
                    search_results = [f for f in category_foods if search_keyword.lower() in f["food_name"].lower()]
                else:
                    search_results = category_foods
            else:
                # 仅按关键词搜索
                search_results = search_food(search_keyword)
        
        # 显示搜索结果
        if search_results:
            st.markdown("##### 🥗 匹配结果")
            
            # 使用两列展示食物卡片
            cols = st.columns(2)
            for i, food in enumerate(search_results):
                with cols[i % 2]:
                    # 创建食物卡片容器
                    with st.container():
                        st.markdown(f"**{food['food_name']}**")
                        st.markdown(f"<span style='color: var(--text-muted); font-size: 0.8rem;'>{food['category']}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='font-size: 0.9rem;'>🔥 {food['calories']} kcal/{food['serving_size']}{food['serving_unit']}</span>", unsafe_allow_html=True)
                        st.markdown(f"<span style='font-size: 0.8rem; color: var(--text-muted);'>🥚 {food['protein']}g | 🥑 {food['fat']}g | 🍞 {food['carbs']}g</span>", unsafe_allow_html=True)
                        if st.button(f"选择", key=f"btn_{food['id']}", use_container_width=True):
                            st.session_state.selected_food = food
                            st.session_state.food_quantity = food.get("serving_size", 100)
                            st.rerun()
                    st.divider()
        else:
            if search_keyword or st.session_state.selected_category != "全部":
                st.info("暂无匹配的食物")
            else:
                st.info("开始记录今天的饮食吧！")
        
        # 显示选中的食物信息
        if st.session_state.selected_food:
            food = st.session_state.selected_food
            st.markdown(f"##### ✅ 已选择: {food['food_name']}")
            
            # 选中食物的详细信息卡片
            with st.container():
                # 食物信息和操作区域
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    # 餐次选择和分量输入
                    meal_type_map = {"早餐": "breakfast", "午餐": "lunch", "晚餐": "dinner", "加餐": "snack"}
                    meal_type = st.selectbox("餐次", ["早餐", "午餐", "晚餐", "加餐"], key="meal_type_select")
                    
                    # 默认使用食物的标准分量单位
                    default_unit = food.get("serving_unit", "g")
                    st.session_state.food_quantity = st.number_input(
                        f"分量 ({default_unit})", 
                        min_value=0.1, 
                        value=float(st.session_state.food_quantity),
                        step=0.1,
                        key="food_quantity_input"
                    )
                
                with col_right:
                    # 计算营养成分
                    nutrition = calculate_nutrition(food, st.session_state.food_quantity, default_unit)
                    
                    st.markdown("**营养成分（自动计算）**")
                    nutri_cols = st.columns(2)
                    with nutri_cols[0]:
                        st.write(f"🔥 热量: {nutrition['calories']} kcal")
                        st.write(f"🥚 蛋白质: {nutrition['protein']} g")
                    with nutri_cols[1]:
                        st.write(f"🥑 脂肪: {nutrition['fat']} g")
                        st.write(f"🍞 碳水: {nutrition['carbs']} g")
            
            notes = st.text_input("备注（可选）", placeholder="添加备注信息...", key="food_notes")
            
            # 操作按钮
            col_btn1, col_btn2 = st.columns([3, 1])
            with col_btn1:
                if st.button("➕ 添加记录", type="primary", use_container_width=True):
                    record = DietRecord(
                        date=date.today().isoformat(),
                        meal_type=meal_type_map[meal_type],
                        food_name=food["food_name"],
                        food_id=food["id"],
                        calories=nutrition["calories"],
                        protein=nutrition["protein"],
                        fat=nutrition["fat"],
                        carbs=nutrition["carbs"],
                        fiber=nutrition["fiber"],
                        sugar=nutrition["sugar"],
                        sodium=nutrition["sodium"],
                        quantity=st.session_state.food_quantity,
                        unit=default_unit,
                        notes=notes
                    )
                    if add_diet_record(record):
                        st.success("✅ 记录已添加！")
                        st.session_state.selected_food = None
                        st.rerun()
                    else:
                        st.error("❌ 添加失败，请重试")
            with col_btn2:
                if st.button("🗑️ 取消", use_container_width=True):
                    st.session_state.selected_food = None
                    st.rerun()
        
        else:
            # 手动输入模式
            st.markdown("##### 手动输入（未搜索到食物时使用）")
            
            col1, col2 = st.columns(2)
            with col1:
                meal_type_map = {"早餐": "breakfast", "午餐": "lunch", "晚餐": "dinner", "加餐": "snack"}
                meal_type = st.selectbox("餐次", ["早餐", "午餐", "晚餐", "加餐"])
                food_name = st.text_input("食物名称")
                calories = st.number_input("热量 (kcal)", min_value=0, value=0)
            
            with col2:
                protein = st.number_input("蛋白质 (g)", min_value=0, value=0)
                fat = st.number_input("脂肪 (g)", min_value=0, value=0)
                carbs = st.number_input("碳水 (g)", min_value=0, value=0)
            
            if st.button("添加记录", type="primary"):
                record = DietRecord(
                    date=date.today().isoformat(),
                    meal_type=meal_type_map[meal_type],
                    food_name=food_name,
                    calories=calories,
                    protein=protein,
                    fat=fat,
                    carbs=carbs
                )
                if add_diet_record(record):
                    st.success("记录已添加！")
                    st.rerun()
                else:
                    st.error("添加失败，请重试")
    
    with tab2:
        st.markdown("#### 📊 今日营养统计")
        
        # 获取用户基础信息
        user_height = st.session_state.get("user_height", 170)
        user_weight = st.session_state.get("user_weight", 65)
        user_age = st.session_state.get("user_age", 25)
        user_gender = st.session_state.get("user_gender", "男")
        
        # 创建营养计算器
        calculator = EnhancedNutritionCalculator(
            weight_loss_mode=st.session_state.weight_loss_mode,
            user_weight=user_weight,
            user_height=user_height,
            user_age=user_age,
            user_gender=user_gender
        )
        
        # 获取今日数据
        today = date.today().isoformat()
        daily_summary = get_diet_summary(today)
        diet_records = get_diet_by_date(today)
        
        # 按餐次分组
        meal_records = {"breakfast": [], "lunch": [], "dinner": [], "snack": []}
        for record in diet_records:
            meal_records[record.meal_type].append(record.to_dict())
        
        # 显示每日摘要
        summary = calculator.get_daily_summary(daily_summary)
        
        # 显示建议摄入量
        st.markdown("##### 🎯 每日建议摄入量")
        recommended = calculator.recommended
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("热量", f"{recommended['calories']} kcal", 
                     f"{'🔥 减肥模式' if st.session_state.weight_loss_mode else '正常模式'}")
        with col2:
            st.metric("蛋白质", f"{recommended['protein']} g", "")
        with col3:
            st.metric("脂肪", f"{recommended['fat']} g", "")
        with col4:
            st.metric("碳水", f"{recommended['carbs']} g", "")
        
        st.divider()
        
        # 显示实际摄入与建议对比
        st.markdown("##### 📈 实际摄入 vs 建议")
        
        nutrients = [
            ("热量", "calories", "kcal"),
            ("蛋白质", "protein", "g"),
            ("脂肪", "fat", "g"),
            ("碳水", "carbs", "g"),
            ("膳食纤维", "fiber", "g"),
            ("钠", "sodium", "mg")
        ]
        
        for name, key, unit in nutrients:
            actual = daily_summary.get(f"total_{key}", 0)
            recommended_value = recommended[key]
            percentage = (actual / recommended_value * 100) if recommended_value > 0 else 0
            
            # 根据百分比设置颜色
            if percentage < 50:
                color = "#3B82F6"  # 蓝色 - 不足
            elif percentage <= 100:
                color = "#10B981"  # 绿色 - 正常
            elif percentage <= 120:
                color = "#F59E0B"  # 橙色 - 略高
            else:
                color = "#EF4444"  # 红色 - 过高
            
            st.markdown(f"""
            <div style="margin-bottom: 1rem;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                    <span style="font-weight: 600;">{name}</span>
                    <span style="color: {color}; font-weight: bold;">{actual} / {recommended_value} {unit} ({percentage:.0f}%)</span>
                </div>
                <div style="height: 8px; background: var(--bg-hover); border-radius: 4px; overflow: hidden;">
                    <div style="height: 100%; background: {color}; width: {min(percentage, 100)}%; border-radius: 4px; transition: width 0.3s;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # 营养成分占比饼图
        st.markdown("##### 🥧 营养成分占比")
        
        # 计算三大营养素的热量
        protein_cal = daily_summary.get("total_protein", 0) * 4  # 蛋白质 4kcal/g
        fat_cal = daily_summary.get("total_fat", 0) * 9           # 脂肪 9kcal/g
        carbs_cal = daily_summary.get("total_carbs", 0) * 4     # 碳水 4kcal/g
        total_cal = protein_cal + fat_cal + carbs_cal
        
        if total_cal > 0:
            import plotly.express as px
            import pandas as pd
            
            nutrients_data = {
                '营养素': ['蛋白质', '脂肪', '碳水'],
                '热量': [protein_cal, fat_cal, carbs_cal],
                '重量': [daily_summary.get("total_protein", 0), daily_summary.get("total_fat", 0), daily_summary.get("total_carbs", 0)]
            }
            df = pd.DataFrame(nutrients_data)
            
            # 饼图
            fig = px.pie(df, values='热量', names='营养素', hole=0.4, 
                        color='营养素',
                        color_discrete_map={'蛋白质': '#3B82F6', '脂肪': '#F59E0B', '碳水': '#10B981'})
            fig.update_layout(
                margin=dict(l=20, r=20, t=20, b=20),
                height=280,
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2)
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示详细数据
            col1, col2, col3 = st.columns(3)
            with col1:
                protein_pct = protein_cal / total_cal * 100
                st.metric("蛋白质", f"{daily_summary.get('total_protein', 0):.1f}g", f"{protein_pct:.1f}%")
            with col2:
                fat_pct = fat_cal / total_cal * 100
                st.metric("脂肪", f"{daily_summary.get('total_fat', 0):.1f}g", f"{fat_pct:.1f}%")
            with col3:
                carbs_pct = carbs_cal / total_cal * 100
                st.metric("碳水", f"{daily_summary.get('total_carbs', 0):.1f}g", f"{carbs_pct:.1f}%")
        else:
            st.info("暂无营养数据，请先记录饮食")
        
        st.divider()
        
        # 显示警告信息
        if summary["warnings"]:
            st.markdown("##### ⚠️ 健康提醒")
            for warning in summary["warnings"]:
                st.warning(warning)
        
        st.divider()
        
        # 显示三餐对比
        st.markdown("##### 🍽️ 三餐摄入对比")
        
        meal_comparison = calculator.get_meal_comparison(meal_records)
        
        for meal_type, data in meal_comparison.items():
            with st.expander(f"{data['name']} ({data['record_count']}条记录)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**实际摄入**")
                    st.write(f"热量: {data['actual']['calories']} kcal")
                    st.write(f"蛋白质: {data['actual']['protein']} g")
                    st.write(f"脂肪: {data['actual']['fat']} g")
                    st.write(f"碳水: {data['actual']['carbs']} g")
                
                with col2:
                    st.markdown("**建议摄入**")
                    st.write(f"热量: {data['recommended']['calories']} kcal")
                    st.write(f"蛋白质: {data['recommended']['protein']} g")
                    st.write(f"脂肪: {data['recommended']['fat']} g")
                    st.write(f"碳水: {data['recommended']['carbs']} g")
                
                # 显示完成度
                st.markdown("**完成度**")
                for nutrient in ["calories", "protein", "fat", "carbs"]:
                    completion = data['completion'][nutrient]
                    color = "#10B981" if 80 <= completion <= 120 else "#F59E0B" if completion < 80 else "#EF4444"
                    st.markdown(f"- {nutrient}: <span style='color: {color};'>{completion:.0f}%</span>", unsafe_allow_html=True)
    
    with tab3:
        st.markdown("#### 🎯 营养建议")
        
        # 获取用户基础信息
        user_height = st.session_state.get("user_height", 170)
        user_weight = st.session_state.get("user_weight", 65)
        user_age = st.session_state.get("user_age", 25)
        user_gender = st.session_state.get("user_gender", "男")
        
        # 创建营养计算器
        calculator = EnhancedNutritionCalculator(
            weight_loss_mode=st.session_state.weight_loss_mode,
            user_weight=user_weight,
            user_height=user_height,
            user_age=user_age,
            user_gender=user_gender
        )
        
        # 显示基础代谢信息
        st.markdown("##### 📊 您的身体数据")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("基础代谢率 (BMR)", f"{calculator.bmr:.0f} kcal")
        with col2:
            st.metric("每日总消耗 (TDEE)", f"{calculator.tdee:.0f} kcal")
        with col3:
            bmi = EnhancedNutritionCalculator.calculate_bmi(user_weight, user_height)
            st.metric("BMI", f"{bmi:.1f}", EnhancedNutritionCalculator.get_bmi_category(bmi))
        
        st.divider()
        
        # 显示三餐建议
        st.markdown("##### 🍽️ 三餐热量分配建议")
        
        meal_recommendations = calculator.get_meal_recommendations()
        
        for meal_type, data in meal_recommendations.items():
            st.markdown(f"""
            <div style="padding: 1rem; background: var(--bg-hover); border-radius: 12px; margin-bottom: 0.5rem;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: 600; font-size: 1.1rem;">{data['name']}</div>
                        <div style="font-size: 0.85rem; color: var(--text-muted);">占比 {data['ratio']*100:.0f}%</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.5rem; font-weight: bold; color: var(--primary);">{data['calories']} kcal</div>
                        <div style="font-size: 0.8rem; color: var(--text-muted);">
                            蛋白质 {data['protein']}g | 脂肪 {data['fat']}g | 碳水 {data['carbs']}g
                        </div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.divider()
        
        # 显示减肥模式说明
        if st.session_state.weight_loss_mode:
            st.markdown("##### 🔥 减肥模式说明")
            st.info("""
            **减肥模式已开启！**
            
            - 热量目标：在 TDEE 基础上减少 500 kcal/天
            - 蛋白质比例：提高至 18%（保护肌肉）
            - 脂肪比例：降低至 25%
            - 糖分限制：减少至 25g/天
            
            **预计效果**：每周可减重约 0.5kg
            
            ⚠️ 请确保热量摄入不低于 1200 kcal/天，避免影响健康
            """)
        else:
            st.markdown("##### 💡 正常模式说明")
            st.info("""
            **正常模式**
            
            - 热量目标：等于 TDEE（维持体重）
            - 蛋白质比例：15%
            - 脂肪比例：30%
            - 碳水比例：50%
            
            适合维持当前体重和健康的生活方式
            """)
    
    with tab4:
        st.markdown("#### 🍱 场景模板")
        
        templates = {
            "食堂套餐": ["米饭 100g", "青菜 150g", "红烧肉 80g"],
            "外卖常点": ["黄焖鸡米饭", "可乐", "水果拼盘"],
            "家庭食谱": ["番茄炒蛋", "紫菜蛋花汤", "杂粮饭"],
            "减肥餐": ["鸡胸肉 150g", "西兰花 200g", "糙米饭 100g"],
            "高蛋白": ["三文鱼 100g", "鸡蛋 2个", "牛奶 250ml"]
        }
        
        for name, foods in templates.items():
            with st.expander(f"🍱 {name}"):
                for food in foods:
                    st.write(f"• {food}")


def render_expense_page():
    """渲染消费记账页面"""
    st.title("💰 消费记账")
    
    # 导入新的统计函数
    from modules.expense.expense_tracker import (
        get_weekly_summary, get_yearly_summary, get_daily_details,
        get_monthly_summary, add_expense_record, ExpenseRecord
    )
    
    tab1, tab2, tab3 = st.tabs(["📝 记录", "📊 统计", "📥 导入"])
    
    with tab1:
        st.markdown("#### 快速记账")
        
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("金额 (¥)", min_value=0.0, value=0.0, step=0.1)
            category = st.selectbox("分类", ["餐饮", "交通", "购物", "娱乐", "医疗", "居住", "通讯", "服饰", "教育", "其他"])
        
        with col2:
            description = st.text_input("描述", placeholder="消费内容...")
            payment_method = st.selectbox("支付方式", ["微信", "支付宝", "现金", "银行卡"])
        
        if st.button("记一笔", type="primary"):
            if amount > 0:
                record = ExpenseRecord(
                    date=date.today().isoformat(),
                    amount=amount,
                    category=category,
                    description=description,
                    payment_method=payment_method
                )
                if add_expense_record(record):
                    st.success("记账成功！")
                    st.rerun()
                else:
                    st.error("记账失败，请重试")
            else:
                st.warning("请输入金额")
    
    with tab2:
        st.markdown("#### 消费统计")
        
        # 选择统计时间范围
        stat_type = st.radio("统计维度", ["周", "月", "年"], horizontal=True)
        
        today = date.today()
        
        if stat_type == "周":
            weekly_data = get_weekly_summary(today.isoformat())
            
            # 周总支出
            st.markdown(f"**{weekly_data.get('week_start', '')} 至 {weekly_data.get('week_end', '')}**")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("本周支出", f"¥{weekly_data.get('total', 0):.2f}")
            with col2:
                category_count = len(weekly_data.get('by_category', []))
                st.metric("消费类别", f"{category_count} 类")
            
            st.divider()
            
            # 分类饼图
            st.markdown("##### 📊 分类占比")
            by_category = weekly_data.get('by_category', [])
            if by_category:
                # 准备饼图数据
                categories = [item['category'] for item in by_category]
                amounts = [item['total'] for item in by_category]
                
                # 使用 Plotly 饼图
                import plotly.express as px
                import pandas as pd
                
                df = pd.DataFrame({
                    '分类': categories,
                    '金额': amounts
                })
                fig = px.pie(df, values='金额', names='分类', hole=0.4)
                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("本周暂无消费记录")
            
            st.divider()
            
            # 每日柱状图
            st.markdown("##### 📈 每日支出")
            by_day = weekly_data.get('by_day', [])
            if by_day:
                import plotly.express as px
                import pandas as pd
                
                df = pd.DataFrame(by_day)
                fig = px.bar(df, x='date', y='total', title='每日支出')
                fig.update_layout(
                    xaxis_title="日期",
                    yaxis_title="金额 (¥)",
                    height=250,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("本周暂无消费记录")
        
        elif stat_type == "月":
            monthly_data = get_monthly_summary(today.year, today.month)
            
            # 月总支出
            col1, col2 = st.columns(2)
            total = sum(item['total'] for item in monthly_data)
            with col1:
                st.metric(f"{today.year}年{today.month}月支出", f"¥{total:.2f}")
            with col2:
                st.metric("消费类别", f"{len(monthly_data)} 类")
            
            st.divider()
            
            # 分类饼图
            st.markdown("##### 📊 分类占比")
            if monthly_data:
                import plotly.express as px
                import pandas as pd
                
                categories = [item['category'] for item in monthly_data]
                amounts = [item['total'] for item in monthly_data]
                
                df = pd.DataFrame({
                    '分类': categories,
                    '金额': amounts
                })
                fig = px.pie(df, values='金额', names='分类', hole=0.4)
                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("本月暂无消费记录")
            
            st.divider()
            
            # 日支出柱状图
            st.markdown("##### 📈 日支出趋势")
            daily_data = get_daily_details(today.year, today.month)
            if daily_data:
                import plotly.express as px
                import pandas as pd
                from collections import defaultdict
                
                # 按日期汇总
                daily_totals = defaultdict(float)
                for item in daily_data:
                    daily_totals[item['date']] += item['amount']
                
                df = pd.DataFrame([
                    {'date': k, 'total': v} for k, v in daily_totals.items()
                ])
                df = df.sort_values('date')
                
                fig = px.bar(df, x='date', y='total', title='每日支出')
                fig.update_layout(
                    xaxis_title="日期",
                    yaxis_title="金额 (¥)",
                    height=250,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("本月暂无消费记录")
            
            st.divider()
            
            # 日支出明细表
            st.markdown("##### 📋 日支出明细")
            if daily_data:
                # 按日期分组显示
                from collections import defaultdict
                daily_groups = defaultdict(list)
                for item in daily_data:
                    daily_groups[item['date']].append(item)
                
                for day_date in sorted(daily_groups.keys(), reverse=True):
                    with st.expander(f"📅 {day_date} (¥{sum(item['amount'] for item in daily_groups[day_date]):.2f})"):
                        for item in daily_groups[day_date]:
                            col1, col2, col3 = st.columns([2, 3, 1])
                            with col1:
                                st.write(f"**{item['category']}**")
                            with col2:
                                st.write(item.get('description', '-'))
                            with col3:
                                st.write(f"¥{item['amount']:.2f}")
                            st.divider()
            else:
                st.info("本月暂无消费记录")
        
        else:  # 年
            yearly_data = get_yearly_summary(today.year)
            
            # 年总支出
            col1, col2 = st.columns(2)
            with col1:
                st.metric(f"{today.year}年支出", f"¥{yearly_data.get('total', 0):.2f}")
            with col2:
                category_count = len(yearly_data.get('by_category', []))
                st.metric("消费类别", f"{category_count} 类")
            
            st.divider()
            
            # 分类饼图
            st.markdown("##### 📊 分类占比")
            by_category = yearly_data.get('by_category', [])
            if by_category:
                import plotly.express as px
                import pandas as pd
                
                categories = [item['category'] for item in by_category]
                amounts = [item['total'] for item in by_category]
                
                df = pd.DataFrame({
                    '分类': categories,
                    '金额': amounts
                })
                fig = px.pie(df, values='金额', names='分类', hole=0.4)
                fig.update_layout(
                    margin=dict(l=20, r=20, t=20, b=20),
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("今年暂无消费记录")
            
            st.divider()
            
            # 月支出柱状图
            st.markdown("##### 📈 月支出趋势")
            by_month = yearly_data.get('by_month', [])
            if by_month:
                import plotly.express as px
                import pandas as pd
                
                # 补全所有月份
                month_totals = {f"{today.year}-{m:02d}": 0 for m in range(1, 13)}
                for item in by_month:
                    month_key = f"{today.year}-{item['month']}"
                    month_totals[month_key] = item['total']
                
                df = pd.DataFrame([
                    {'month': k, 'total': v} for k, v in month_totals.items()
                ])
                df['month'] = pd.to_datetime(df['month'])
                
                fig = px.bar(df, x='month.dt.strftime("%m月")', y='total', title='每月支出')
                fig.update_layout(
                    xaxis_title="月份",
                    yaxis_title="金额 (¥)",
                    height=250,
                    margin=dict(l=20, r=20, t=40, b=20)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("今年暂无消费记录")
    
    with tab3:
        st.markdown("#### 导入账单")
        st.info("支持微信/支付宝标准格式导出账单")
        
        uploaded_file = st.file_uploader("上传 CSV 文件", type=["csv"])
        if uploaded_file:
            st.success("文件已上传")
            st.caption("正在解析账单数据...")


def render_exercise_page():
    """渲染运动健康页面"""
    from modules.exercise.exercise_tracker import (
        ExerciseRecord, add_exercise_record, get_exercise_by_date, get_exercise_summary,
        get_weekly_summary, get_monthly_summary, get_yearly_summary,
        get_average_calories, get_average_steps, get_exercise_type_stats,
        EXERCISE_TYPES, EXERCISE_INFO, calculate_calories, calculate_pace
    )
    import plotly.express as px
    import plotly.graph_objects as go
    import pandas as pd
    import random
    
    st.title("🏃 运动健康")
    
    # 获取用户体重（用于计算热量）
    user_weight = st.session_state.get("user_weight", 70)
    
    # 今日运动汇总
    today_summary = get_exercise_summary(date.today().isoformat())
    
    # 顶部指标卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("今日步数", f"{today_summary['total_steps']:,}", "步")
    with col2:
        st.metric("今日消耗", f"{today_summary['total_calories']:.0f}", "kcal")
    with col3:
        st.metric("今日时长", f"{today_summary['total_duration']}", "分钟")
    with col4:
        st.metric("今日距离", f"{today_summary['total_distance']:.2f}", "公里")
    
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["📝 记录", "📊 统计", "🏅 运动"])
    
    with tab1:
        st.markdown("#### 运动记录")
        
        col1, col2 = st.columns(2)
        with col1:
            # 创建带 emoji 的运动类型选项
            exercise_type_options = [f"{EXERCISE_INFO.get(k, {}).get('emoji', '🏃')} {k}" for k in EXERCISE_TYPES.keys()]
            selected_with_emoji = st.selectbox("运动类型", exercise_type_options)
            # 提取纯运动类型名称
            exercise_type = selected_with_emoji.split(' ', 1)[-1]
            
            duration = st.number_input("时长 (分钟)", min_value=1, value=30)
            distance = st.number_input("距离 (公里)", min_value=0.0, value=0.0, step=0.1)
        
        with col2:
            # 自动计算热量
            met = EXERCISE_TYPES.get(exercise_type, 5.0)
            auto_calories = calculate_calories(user_weight, met, duration)
            calories = st.number_input("消耗热量 (kcal)", min_value=0, value=int(auto_calories))
            steps = st.number_input("步数", min_value=0, value=0)
        
        # 自动计算配速并显示
        if distance > 0 and duration > 0:
            pace = calculate_pace(duration, distance)
            st.success(f"⚡ 配速: {pace:.1f} 分钟/公里")
        elif distance > 0:
            st.info("💡 请输入时长以计算配速")
        elif duration > 0:
            st.info("💡 请输入距离以计算配速")
        
        # 显示运动类型描述
        exercise_info = EXERCISE_INFO.get(exercise_type, {})
        if exercise_info.get('description'):
            st.info(f"💡 {exercise_info['description']}")
        
        notes = st.text_input("备注（可选）", placeholder="记录运动感受...")
        
        if st.button("➕ 记录运动", type="primary", use_container_width=True):
            record = ExerciseRecord(
                date=date.today().isoformat(),
                exercise_type=exercise_type,
                duration=duration,
                calories=calories,
                steps=steps,
                distance=distance if distance > 0 else None,
                notes=notes
            )
            if add_exercise_record(record):
                st.success("✅ 运动记录已添加！")
                st.rerun()
            else:
                st.error("❌ 添加失败，请重试")
        
        st.divider()
        
        # 今日运动记录列表
        st.markdown("#### 今日运动记录")
        today_records = get_exercise_by_date(date.today().isoformat())
        if today_records:
            for record in today_records:
                with st.container():
                    col1, col2, col3 = st.columns([2, 2, 1])
                    with col1:
                        st.markdown(f"**{record.exercise_type}**")
                        st.caption(f"{record.duration} 分钟")
                    with col2:
                        st.markdown(f"🔥 {record.calories:.0f} kcal")
                        if record.distance:
                            pace = record.pace if record.pace else (record.duration / record.distance if record.distance > 0 else 0)
                            st.caption(f"{record.distance:.2f} km | 配速 {pace:.1f} min/km")
                    with col3:
                        if record.steps:
                            st.markdown(f"👣 {record.steps:,}")
        else:
            st.info("今日暂无运动记录，开始运动吧！")
    
    with tab2:
        st.markdown("#### 运动统计")
        
        # 统计周期选择
        period = st.selectbox("统计周期", ["本周", "本月", "本年"], key="exercise_period")
        
        if period == "本周":
            # 周统计
            weekly_data = get_weekly_summary(date.today().isoformat())
            avg_calories = get_average_calories(7)
            avg_steps = get_average_steps(7)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("本周平均消耗", f"{avg_calories:.0f}", "kcal/天")
            with col2:
                st.metric("本周平均步数", f"{avg_steps:.0f}", "步/天")
            
            st.divider()
            
            # 每日卡路里消耗柱状图
            if weekly_data:
                df = pd.DataFrame(weekly_data)
                # 转换日期格式为星期几
                df['weekday'] = pd.to_datetime(df['date']).dt.day_name(locale='Chinese')
                df['weekday_short'] = pd.to_datetime(df['date']).dt.strftime('%a')
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['weekday'],
                    y=df['calories'],
                    name='卡路里消耗',
                    marker_color='#3B82F6'
                ))
                fig.update_layout(
                    title="每日卡路里消耗",
                    xaxis_title="日期",
                    yaxis_title="卡路里 (kcal)",
                    height=300,
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 每日步数柱状图
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(
                    x=df['weekday'],
                    y=df['steps'],
                    name='步数',
                    marker_color='#10B981'
                ))
                fig2.update_layout(
                    title="每日步数统计",
                    xaxis_title="日期",
                    yaxis_title="步数",
                    height=300,
                    xaxis_tickangle=-45
                )
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("本周暂无运动数据")
        
        elif period == "本月":
            # 月统计
            monthly_data = get_monthly_summary(date.today().year, date.today().month)
            
            if monthly_data:
                df = pd.DataFrame(monthly_data)
                total_calories = df['calories'].sum()
                total_steps = df['steps'].sum()
                total_distance = df['distance'].sum()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("本月总消耗", f"{total_calories:.0f}", "kcal")
                with col2:
                    st.metric("本月总步数", f"{total_steps:,}", "步")
                with col3:
                    st.metric("本月总距离", f"{total_distance:.2f}", "公里")
                
                st.divider()
                
                # 每日柱状图
                df['day'] = pd.to_datetime(df['date']).dt.day
                
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['day'],
                    y=df['calories'],
                    name='卡路里消耗',
                    marker_color='#F59E0B'
                ))
                fig.update_layout(
                    title="本月每日卡路里消耗",
                    xaxis_title="日期 (日)",
                    yaxis_title="卡路里 (kcal)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("本月暂无运动数据")
        
        else:
            # 年统计
            yearly_data = get_yearly_summary(date.today().year)
            
            if yearly_data:
                df = pd.DataFrame(yearly_data)
                df['month_name'] = df['month'].apply(lambda x: f"{int(x)}月")
                
                total_calories = df['calories'].sum()
                total_steps = df['steps'].sum()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("本年总消耗", f"{total_calories:.0f}", "kcal")
                with col2:
                    st.metric("本年总步数", f"{total_steps:,}", "步")
                
                st.divider()
                
                # 月度柱状图
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['month_name'],
                    y=df['calories'],
                    name='卡路里消耗',
                    marker_color='#8B5CF6'
                ))
                fig.update_layout(
                    title="本年月度卡路里消耗",
                    xaxis_title="月份",
                    yaxis_title="卡路里 (kcal)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("本年暂无运动数据")
    
    with tab3:
        st.markdown("#### 运动类型统计")
        
        # 选择运动类型查看详细统计（带 emoji）
        exercise_types_list = ["跑步", "走路", "骑行", "游泳"]
        exercise_types_options = [f"{EXERCISE_INFO.get(t, {}).get('emoji', '🏃')} {t}" for t in exercise_types_list]
        selected_with_emoji = st.selectbox("选择运动类型", exercise_types_options)
        selected_type = selected_with_emoji.split(' ', 1)[-1]
        
        # 显示运动类型描述
        exercise_info = EXERCISE_INFO.get(selected_type, {})
        if exercise_info.get('description'):
            st.info(f"💡 {exercise_info['description']}")
        
        stats = get_exercise_type_stats(selected_type, 30)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("总次数", f"{stats['count']}", "次")
        with col2:
            st.metric("总时长", f"{stats['total_duration']}", "分钟")
        with col3:
            st.metric("总距离", f"{stats['total_distance']:.2f}", "公里")
        with col4:
            if stats['avg_pace'] > 0:
                st.metric("平均配速", f"{stats['avg_pace']:.1f}", "min/km")
            else:
                st.metric("平均配速", "--", "min/km")
        
        st.divider()
        
        # 运动建议
        st.markdown("#### 💡 运动建议")
        tips = [
            "每周至少进行150分钟中等强度运动",
            "跑步前做好热身，避免运动损伤",
            "运动后及时补充水分和蛋白质",
            "游泳是全身运动，对关节压力小",
            "骑行可以锻炼心肺功能和腿部肌肉",
            "运动时注意心率，保持在适宜区间",
            "运动后拉伸有助于肌肉恢复",
            "循序渐进，不要过度运动"
        ]
        for tip in random.sample(tips, 3):
            st.info(tip)


def render_sleep_page():
    """渲染睡眠管理页面"""
    from modules.sleep.sleep_tracker import (
        SleepRecord, add_sleep_record, get_sleep_by_date, get_sleep_summary,
        get_weekly_sleep_summary, get_monthly_sleep_summary,
        get_average_sleep, get_average_quality, get_early_sleep_count,
        get_sleep_regularity_score, get_recommended_sleep, get_sleep_advice,
        SLEEP_TIPS, check_early_sleep
    )
    import plotly.graph_objects as go
    import plotly.express as px
    import pandas as pd
    import random
    
    st.title("😴 睡眠管理")
    
    # 获取用户年龄（用于建议睡眠时长）
    user_age = st.session_state.get("user_age", 25)
    recommended_sleep = get_recommended_sleep(user_age)
    
    # 今日睡眠汇总
    today_summary = get_sleep_summary(date.today().isoformat())
    
    # 顶部指标卡片
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("今日睡眠", f"{today_summary['duration']:.1f}", "小时")
    with col2:
        st.metric("建议时长", f"{recommended_sleep['min']}-{recommended_sleep['max']}", "小时")
    with col3:
        if today_summary['quality']:
            st.metric("睡眠质量", f"{today_summary['quality']}", "分")
        else:
            st.metric("睡眠质量", "--", "分")
    with col4:
        if today_summary['early_sleep']:
            st.metric("早睡打卡", "✅ 已打卡", "22:00前入睡")
        else:
            st.metric("早睡打卡", "❌ 未打卡", "22:00前入睡")
    
    st.divider()
    
    tab1, tab2, tab3, tab4 = st.tabs(["📝 记录", "📊 统计", "💡 建议", "🌙 小贴士"])
    
    with tab1:
        st.markdown("#### 睡眠记录")
        
        col1, col2 = st.columns(2)
        with col1:
            bedtime = st.time_input("入睡时间", value=None, key="bedtime_input", label_visibility="visible")
            wakeup_time = st.time_input("起床时间", value=None, key="wakeup_input", label_visibility="visible")
        
        with col2:
            deep_sleep = st.slider("深睡时长 (小时)", 0.0, 4.0, 1.5, 0.5)
            quality = st.slider("睡眠质量", 1, 5, 3)
            awakenings = st.number_input("醒来次数", min_value=0, value=0)
        
        notes = st.text_input("备注（可选）", placeholder="记录睡眠感受...")
        
        if st.button("➕ 记录睡眠", type="primary", use_container_width=True):
            if bedtime and wakeup_time:
                record = SleepRecord(
                    date=date.today().isoformat(),
                    bedtime=bedtime.strftime("%H:%M"),
                    wakeup_time=wakeup_time.strftime("%H:%M"),
                    deep_sleep=deep_sleep,
                    quality=quality,
                    awakenings=awakenings,
                    notes=notes
                )
                if add_sleep_record(record):
                    st.success("✅ 睡眠记录已添加！")
                    st.rerun()
                else:
                    st.error("❌ 添加失败，请重试")
            else:
                st.warning("请选择入睡时间和起床时间")
        
        st.divider()
        
        # 早睡打卡提示
        st.markdown("#### 🌙 早睡打卡")
        early_count = get_early_sleep_count(7)
        st.markdown(f"本周早睡打卡次数：**{early_count}/7**")
        
        # 检查今天是否已经早睡打卡
        today_record = get_sleep_by_date(date.today().isoformat())
        already_checked = False
        if today_record:
            already_checked = check_early_sleep(today_record.bedtime)
        
        if already_checked:
            st.success("✅ 今日已完成早睡打卡！")
        else:
            if st.button("⏰ 立即打卡（22:00前入睡）", type="secondary"):
                st.info("💡 提醒：请确保您在22:00前入睡，养成良好的作息习惯")
                st.warning("⚠️ 打卡记录将在您记录今日睡眠时自动验证")
        
        if early_count >= 5:
            st.success("🎉 本周早睡习惯良好！继续保持！")
        elif early_count >= 3:
            st.info("👍 本周早睡次数不错，继续努力！")
        else:
            st.warning("⚠️ 建议尝试22:00前入睡，养成早睡习惯")
    
    with tab2:
        st.markdown("#### 睡眠统计")
        
        # 统计周期选择
        period = st.selectbox("统计周期", ["本周", "本月"], key="sleep_period")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            avg_sleep = get_average_sleep(7 if period == "本周" else 30)
            st.metric("平均睡眠时长", f"{avg_sleep:.1f}", "小时")
        with col2:
            avg_quality = get_average_quality(7 if period == "本周" else 30)
            st.metric("平均睡眠质量", f"{avg_quality:.1f}", "分")
        with col3:
            regularity_score = get_sleep_regularity_score(7)
            st.metric("作息规律评分", f"{regularity_score:.0f}", "分")
        
        st.divider()
        
        if period == "本周":
            weekly_data = get_weekly_sleep_summary(date.today().isoformat())
            if weekly_data:
                df = pd.DataFrame(weekly_data)
                # 转换日期格式为星期几
                df['weekday'] = pd.to_datetime(df['date']).dt.day_name()
                
                # 睡眠时长柱状图
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['weekday'],
                    y=df['duration'],
                    name='睡眠时长',
                    marker_color='#8B5CF6'
                ))
                # 添加建议睡眠范围线
                fig.add_hrect(
                    y0=recommended_sleep['min'],
                    y1=recommended_sleep['max'],
                    fillcolor="#10B981",
                    opacity=0.2,
                    annotation_text="建议睡眠范围"
                )
                fig.update_layout(
                    title="本周睡眠时长统计",
                    xaxis_title="日期",
                    yaxis_title="时长 (小时)",
                    height=300
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # 睡眠质量折线图
                if 'quality' in df.columns and df['quality'].notna().any():
                    fig2 = go.Figure()
                    fig2.add_trace(go.Scatter(
                        x=df['weekday'],
                        y=df['quality'],
                        mode='lines+markers',
                        name='睡眠质量',
                        line=dict(color='#F59E0B', width=2)
                    ))
                    fig2.update_layout(
                        title="本周睡眠质量趋势",
                        xaxis_title="日期",
                        yaxis_title="质量评分",
                        height=250
                    )
                    st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("本周暂无睡眠数据")
        
        else:
            monthly_data = get_monthly_sleep_summary(date.today().year, date.today().month)
            if monthly_data:
                df = pd.DataFrame(monthly_data)
                
                total_sleep = df['duration'].sum()
                avg_monthly = df['duration'].mean()
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("本月总睡眠", f"{total_sleep:.1f}", "小时")
                with col2:
                    st.metric("本月日均", f"{avg_monthly:.1f}", "小时")
                
                st.divider()
                
                # 转换日期格式为日期数字（确保是整数）
                df['day'] = pd.to_datetime(df['date']).dt.day.astype(int)
                
                # 月度睡眠时长柱状图
                fig = go.Figure()
                fig.add_trace(go.Bar(
                    x=df['day'],
                    y=df['duration'],
                    name='睡眠时长',
                    marker_color='#3B82F6'
                ))
                fig.add_hrect(
                    y0=recommended_sleep['min'],
                    y1=recommended_sleep['max'],
                    fillcolor="#10B981",
                    opacity=0.2,
                    annotation_text="建议睡眠范围"
                )
                fig.update_layout(
                    title="本月睡眠时长统计",
                    xaxis_title="日期 (日)",
                    yaxis_title="时长 (小时)",
                    height=300,
                    xaxis=dict(
                        tickmode='array',
                        tickvals=df['day'],
                        ticktext=[f"{d}日" for d in df['day']]
                    )
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("本月暂无睡眠数据")
    
    with tab3:
        st.markdown("#### 睡眠建议")
        
        # 根据今日睡眠时长给出建议
        if today_summary['duration'] > 0:
            advice_list = get_sleep_advice(
                today_summary['duration'],
                recommended_sleep['min'],
                recommended_sleep['max']
            )
            
            if today_summary['duration'] < recommended_sleep['min']:
                st.warning(f"⚠️ 今日睡眠不足，建议睡眠 {recommended_sleep['min']}-{recommended_sleep['max']} 小时")
            elif today_summary['duration'] > recommended_sleep['max']:
                st.info(f"ℹ️ 今日睡眠偏长，建议睡眠 {recommended_sleep['min']}-{recommended_sleep['max']} 小时")
            else:
                st.success(f"✅ 今日睡眠时长理想，继续保持！")
            
            st.divider()
            
            st.markdown("##### 💡 改善建议")
            for advice in advice_list:
                st.markdown(f"- {advice}")
        else:
            st.info("请先记录今日睡眠，获取个性化建议")
        
        st.divider()
        
        # 作息规律建议
        regularity_score = get_sleep_regularity_score(7)
        st.markdown("##### 📊 作息规律分析")
        if regularity_score >= 80:
            st.success(f"作息规律评分：{regularity_score:.0f}分 - 非常规律，继续保持！")
        elif regularity_score >= 60:
            st.info(f"作息规律评分：{regularity_score:.0f}分 - 较为规律，可以进一步优化")
        elif regularity_score > 0:
            st.warning(f"作息规律评分：{regularity_score:.0f}分 - 作息不够规律，建议固定入睡时间")
        else:
            st.info("暂无足够数据计算作息规律评分")
    
    with tab4:
        st.markdown("#### 睡眠养生小贴士")
        
        # 随机显示3条小贴士
        selected_tips = random.sample(SLEEP_TIPS, 5)
        for i, tip in enumerate(selected_tips, 1):
            st.markdown(f"**{i}.** {tip}")
        
        st.divider()
        
        # 睡眠知识
        st.markdown("##### 📚 睡眠知识")
        knowledge = [
            "**深睡眠**：占总睡眠的20-25%，是身体恢复的关键阶段",
            "**浅睡眠**：占总睡眠的50-60%，是入睡和深睡眠的过渡",
            "**REM睡眠**：占总睡眠的20-25%，与记忆和情绪相关",
            "**睡眠周期**：每个周期约90分钟，一晚经历4-6个周期",
            "**最佳入睡时间**：22:00-23:00是最佳入睡时段"
        ]
        for k in knowledge:
            st.markdown(k)


def render_mood_page():
    """渲染情绪日记页面"""
    import random
    from datetime import datetime, timedelta
    import calendar
    from database import get_connection
    from modules.mood.emotion_model import MOOD_TYPES, get_mood_color, get_mood_emoji
    from utils.quotes import LIFE_QUOTES
    
    st.title("💭 情绪日记")
    
    # 显示每日名言
    quote = random.choice(LIFE_QUOTES)
    st.markdown(f"### ✨ {quote}")
    
    # 创建标签页
    tab1, tab2, tab3 = st.tabs(["📝 记录心情", "📅 情绪日历", "🎵 愉悦推荐"])
    
    with tab1:
        st.markdown("#### 今日心情")
        
        # 情绪选择
        mood_options = list(MOOD_TYPES.keys())
        selected_mood = st.selectbox("🎭 选择情绪", mood_options)
        
        # 显示选中情绪的emoji和描述
        mood_info = MOOD_TYPES[selected_mood]
        st.markdown(f"{mood_info['emoji']} *{mood_info['description']}*")
        
        # 情绪强度
        intensity = st.slider("📊 情绪强度", 1, 5, 3, 
                             help="1=很弱，5=很强")
        st.caption(f"当前强度: {'●' * intensity}{'○' * (5-intensity)}")
        
        # 触发因素
        triggers = st.multiselect("⚡ 可能的原因（可多选）", 
                                  ["💼 工作", "📚 学习", "👥 人际关系", "💪 健康", 
                                   "🏠 家庭", "❤️ 感情", "💰 经济", "😴 睡眠", "🌤️ 天气", "🔮 其他"])
        
        # 详细记录
        notes = st.text_area("💭 记录一下今天发生了什么（可选）", 
                            height=100,
                            placeholder="写下你的感受...")
        
        # 保存按钮
        if st.button("💾 保存心情", type="primary", use_container_width=True):
            today = datetime.now().strftime("%Y-%m-%d")
            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    # 检查今天是否已有记录
                    cursor.execute("SELECT id FROM mood_records WHERE date = ?", (today,))
                    existing = cursor.fetchone()
                    
                    if existing:
                        # 更新记录
                        cursor.execute("""
                            UPDATE mood_records 
                            SET mood = ?, intensity = ?, triggers = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                            WHERE date = ?
                        """, (selected_mood, intensity, ",".join(triggers), notes, today))
                    else:
                        # 新增记录
                        cursor.execute("""
                            INSERT INTO mood_records (date, mood, intensity, triggers, notes)
                            VALUES (?, ?, ?, ?, ?)
                        """, (today, selected_mood, intensity, ",".join(triggers), notes))
                    
                    conn.commit()
                    st.success(f"✅ 心情已保存！{mood_info['emoji']}")
                    st.balloons()
            except Exception as e:
                st.error(f"保存失败: {str(e)}")
    
    with tab2:
        st.markdown("#### 📅 情绪日历")
        
        # 选择月份
        col1, col2 = st.columns([1, 4])
        with col1:
            now = datetime.now()
            selected_year = st.selectbox("年份", range(now.year-2, now.year+1), index=0)
            selected_month = st.selectbox("月份", range(1, 13), index=now.month-1)
        
        # 获取该月的情绪记录
        month_start = f"{selected_year}-{selected_month:02d}-01"
        if selected_month == 12:
            month_end = f"{selected_year+1}-01-01"
        else:
            month_end = f"{selected_year}-{selected_month+1:02d}-01"
        
        try:
            with get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT date, mood, intensity 
                    FROM mood_records 
                    WHERE date >= ? AND date < ?
                    ORDER BY date
                """, (month_start, month_end))
                mood_data = {row[0]: {"mood": row[1], "intensity": row[2]} 
                           for row in cursor.fetchall()}
        except Exception as e:
            mood_data = {}
            st.error(f"读取数据失败: {str(e)}")
        
        # 绘制日历
        cal = calendar.Calendar(firstweekday=6)  # 周日开始
        month_days = cal.monthdayscalendar(selected_year, selected_month)
        
        # 显示星期标题
        week_cols = st.columns(7)
        weekdays = ["日", "一", "二", "三", "四", "五", "六"]
        for i, day in enumerate(weekdays):
            with week_cols[i]:
                st.markdown(f"**{day}**")
        
        # 显示日历格子
        mood_colors = {
            "开心": "#FFD700", "平静": "#90EE90", "兴奋": "#FF69B4",
            "疲惫": "#D3D3D3", "焦虑": "#FFA500", "悲伤": "#4682B4",
            "愤怒": "#FF4500", "迷茫": "#9370DB"
        }
        
        for week in month_days:
            cols = st.columns(7)
            for i, day in enumerate(week):
                with cols[i]:
                    if day == 0:
                        st.write("")
                    else:
                        date_str = f"{selected_year}-{selected_month:02d}-{day:02d}"
                        if date_str in mood_data:
                            mood = mood_data[date_str]["mood"]
                            intensity = mood_data[date_str]["intensity"]
                            color = mood_colors.get(mood, "#808080")
                            emoji = get_mood_emoji(mood)
                            
                            # 显示日期和情绪
                            st.markdown(
                                f"<div style='background-color: {color}; "
                                f"padding: 10px; border-radius: 10px; text-align: center; "
                                f"opacity: {0.5 + intensity*0.1}'>"
                                f"<div style='font-size: 24px;'>{emoji}</div>"
                                f"<div style='font-size: 12px;'>{day}</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                        else:
                            # 没有记录的日期
                            st.markdown(
                                f"<div style='border: 1px dashed #ccc; "
                                f"padding: 10px; border-radius: 10px; text-align: center;'>"
                                f"<div style='font-size: 14px; color: #999;'>{day}</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
        
        # 月度情绪统计
        st.markdown("#### 📊 月度情绪统计")
        
        if mood_data:
            # 统计各情绪天数
            mood_counts = {}
            for data in mood_data.values():
                mood = data["mood"]
                mood_counts[mood] = mood_counts.get(mood, 0) + 1
            
            # 显示统计
            cols = st.columns(len(mood_counts) if mood_counts else 1)
            for i, (mood, count) in enumerate(sorted(mood_counts.items(), key=lambda x: x[1], reverse=True)):
                with cols[i % len(cols)]:
                    emoji = get_mood_emoji(mood)
                    color = mood_colors.get(mood, "#808080")
                    st.markdown(
                        f"<div style='background-color: {color}20; padding: 15px; "
                        f"border-radius: 10px; border-left: 4px solid {color};'>"
                        f"<div style='font-size: 24px;'>{emoji} {mood}</div>"
                        f"<div style='font-size: 18px;'>记录 {count} 天</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
            
            # 平均情绪强度
            avg_intensity = sum(d["intensity"] for d in mood_data.values()) / len(mood_data)
            st.markdown(f"📈 平均情绪强度: {avg_intensity:.1f}/5.0")
        else:
            st.info("本月还没有记录哦，开始记录你的心情吧！")
    
    with tab3:
        st.markdown("#### 🎵 心情愉悦推荐")
        
        # 创建子标签页
        subtab1, subtab2 = st.tabs(["🎶 放松音乐", "🎬 治愈电影"])
        
        with subtab1:
            st.markdown("##### 🌿 放松音乐歌单")
            
            # 音乐推荐数据 - 覆盖所有情绪
            music_recommendations = [
                # 开心
                {"name": "River Flows In You", "artist": "Yiruma", 
                 "genre": "钢琴曲", "mood": "开心", "description": "你的心河，永不停息，温暖治愈"},
                {"name": "Summer", "artist": "Joe Hisaishi", 
                 "genre": "动漫配乐", "mood": "开心", "description": "菊次郎的夏天，轻快明亮"},
                {"name": "Home", "artist": "Michael Bublé", 
                 "genre": "爵士", "mood": "开心", "description": "回家的感觉真好，温馨动人"},
                {"name": "Happy", "artist": "Pharrell Williams", 
                 "genre": "流行", "mood": "开心", "description": "传递快乐能量的热门金曲"},
                
                # 平静
                {"name": "雨的轻喃", "artist": "Various Artists", 
                 "genre": "自然音乐", "mood": "平静", "description": "雨声与轻柔钢琴的完美融合"},
                {"name": "星空", "artist": "Bandari", 
                 "genre": "轻音乐", "mood": "平静", "description": "如星空般宁静美好的旋律"},
                {"name": "Canon in D", "artist": "Johann Pachelbel", 
                 "genre": "古典", "mood": "平静", "description": "经典的卡农，永恒的感动"},
                {"name": "Kiss The Rain", "artist": "Yiruma", 
                 "genre": "钢琴曲", "mood": "平静", "description": "如雨滴般轻柔的旋律"},
                
                # 兴奋
                {"name": "Eye of the Tiger", "artist": "Survivor", 
                 "genre": "摇滚", "mood": "兴奋", "description": "充满力量感，点燃激情"},
                {"name": "We Will Rock You", "artist": "Queen", 
                 "genre": "摇滚", "mood": "兴奋", "description": "振奋人心的经典摇滚"},
                {"name": "Can't Stop the Feeling", "artist": "Justin Timberlake", 
                 "genre": "流行", "mood": "兴奋", "description": "欢快节奏，忍不住想跳舞"},
                {"name": "Uptown Funk", "artist": "Bruno Mars", 
                 "genre": "放克", "mood": "兴奋", "description": "复古放克，活力满满"},
                
                # 疲惫
                {"name": "Weightless", "artist": "Marconi Union", 
                 "genre": "放松音乐", "mood": "疲惫", "description": "科学证明最放松的音乐"},
                {"name": "Clair de Lune", "artist": "Debussy", 
                 "genre": "古典", "mood": "疲惫", "description": "月光下的温柔旋律"},
                {"name": "Moon River", "artist": "Audrey Hepburn", 
                 "genre": "爵士", "mood": "疲惫", "description": "经典老歌，舒缓身心"},
                {"name": "Sleep Away", "artist": "Bob Acri", 
                 "genre": "轻音乐", "mood": "疲惫", "description": "温柔入眠曲"},
                
                # 焦虑
                {"name": "Mindfulness Meditation", "artist": "Meditation Music", 
                 "genre": "冥想音乐", "mood": "焦虑", "description": "正念冥想，平复焦虑"},
                {"name": "Om Shanti Om", "artist": "Deva Premal", 
                 "genre": "颂钵音乐", "mood": "焦虑", "description": "颂钵疗愈，静心安神"},
                {"name": "Deep Breathing", "artist": "Nature Sounds", 
                 "genre": "自然音效", "mood": "焦虑", "description": "深呼吸引导，放松身心"},
                {"name": "Solfeggio 528Hz", "artist": "Healing Frequency", 
                 "genre": "疗愈音乐", "mood": "焦虑", "description": "528Hz频率，修复DNA"},
                
                # 悲伤
                {"name": "Nothing Compares 2 U", "artist": "Sinéad O'Connor", 
                 "genre": "抒情", "mood": "悲伤", "description": "释放悲伤情绪的经典"},
                {"name": "Hurt", "artist": "Johnny Cash", 
                 "genre": "乡村", "mood": "悲伤", "description": "深沉沧桑，触动心灵"},
                {"name": "Someone Like You", "artist": "Adele", 
                 "genre": "抒情", "mood": "悲伤", "description": "失恋必听，释放情绪"},
                {"name": "The Night We Met", "artist": "Lord Huron", 
                 "genre": "独立民谣", "mood": "悲伤", "description": "凄美动人，适合独自聆听"},
                
                # 愤怒
                {"name": "Smells Like Teen Spirit", "artist": "Nirvana", 
                 "genre": "摇滚", "mood": "愤怒", "description": "释放青春怒火的摇滚经典"},
                {"name": "Enter Sandman", "artist": "Metallica", 
                 "genre": "重金属", "mood": "愤怒", "description": "激烈节奏，宣泄愤怒"},
                {"name": "Break Stuff", "artist": "Limp Bizkit", 
                 "genre": "新金属", "mood": "愤怒", "description": "暴力美学，释放压力"},
                {"name": "I Hate Myself for Loving You", "artist": "Joan Jett", 
                 "genre": "摇滚", "mood": "愤怒", "description": "爱恨交织的力量"},
                
                # 迷茫
                {"name": "Lost in the World", "artist": "Kanye West", 
                 "genre": "嘻哈", "mood": "迷茫", "description": "迷失中的寻找"},
                {"name": "The Sound of Silence", "artist": "Simon & Garfunkel", 
                 "genre": "民谣", "mood": "迷茫", "description": "寂静之声，思考人生"},
                {"name": "Hallelujah", "artist": "Leonard Cohen", 
                 "genre": "民谣", "mood": "迷茫", "description": "深刻哲思，寻找意义"},
                {"name": "Knockin' on Heaven's Door", "artist": "Bob Dylan", 
                 "genre": "民谣", "mood": "迷茫", "description": "叩问天堂之门"},
            ]
            
            # 按心情筛选
            filter_mood = st.selectbox("按心情筛选", ["全部"] + list(MOOD_TYPES.keys()))
            
            # 显示音乐列表
            if filter_mood == "全部":
                filtered_music = music_recommendations
            else:
                filtered_music = [m for m in music_recommendations if m["mood"] == filter_mood]
            
            for music in filtered_music:
                with st.expander(f"🎵 {music['name']} - {music['artist']}"):
                    st.markdown(f"**类型**: {music['genre']}")
                    st.markdown(f"**适合心情**: {get_mood_emoji(music['mood'])} {music['mood']}")
                    st.markdown(f"**描述**: {music['description']}")
                    if st.button(f"▶ 播放", key=f"play_{music['name']}"):
                        st.info(f"正在播放: {music['name']}")
        
        with subtab2:
            st.markdown("##### 🎥 治愈电影片单")
            
            # 电影推荐数据 - 覆盖所有情绪
            movie_recommendations = [
                # 开心
                {"name": "海蒂和爷爷", "year": 2019, 
                 "theme_color": "#4A90D9", "mood": "开心", 
                 "description": "阿尔卑斯山的清新与温暖，治愈人心"},
                {"name": "千与千寻", "year": 2001, 
                 "theme_color": "#FF69B4", "mood": "开心", 
                 "description": "宫崎骏的经典，勇气与成长的奇幻之旅"},
                {"name": "龙猫", "year": 1988, 
                 "theme_color": "#228B22", "mood": "开心", 
                 "description": "童心与想象力，森林里的温情治愈"},
                {"name": "帕丁顿熊2", "year": 2017, 
                 "theme_color": "#D41159", "mood": "开心", 
                 "description": "萌熊进城，伦敦冒险，笑中带泪"},
                
                # 平静
                {"name": "小森林 夏秋篇", "year": 2014, 
                 "theme_color": "#2E8B57", "mood": "平静", 
                 "description": "远离都市喧嚣，回归自然生活的美好"},
                {"name": "小森林 冬春篇", "year": 2014, 
                 "theme_color": "#4682B4", "mood": "平静", 
                 "description": "四季流转，用美食治愈心灵的孤独"},
                {"name": "深夜食堂", "year": 2009, 
                 "theme_color": "#3D3D3D", "mood": "平静", 
                 "description": "深夜的温暖，每个故事都触动人心"},
                {"name": "岁月神偷", "year": 2010, 
                 "theme_color": "#8B4513", "mood": "平静", 
                 "description": "香港岁月，平淡中的深情与成长"},
                
                # 兴奋
                {"name": "疯狂动物城", "year": 2016, 
                 "theme_color": "#006994", "mood": "兴奋", 
                 "description": "动物乌托邦的冒险，热血追梦"},
                {"name": "速度与激情7", "year": 2015, 
                 "theme_color": "#FF4444", "mood": "兴奋", 
                 "description": "极速狂飙，兄弟情谊，热血沸腾"},
                {"name": "复仇者联盟4", "year": 2019, 
                 "theme_color": "#0077B6", "mood": "兴奋", 
                 "description": "终局之战，英雄集结，史诗对决"},
                {"name": "头号玩家", "year": 2018, 
                 "theme_color": "#9D4EDD", "mood": "兴奋", 
                 "description": "虚拟现实冒险，彩蛋盛宴"},
                
                # 疲惫
                {"name": "海边的曼彻斯特", "year": 2016, 
                 "theme_color": "#5A6A7A", "mood": "疲惫", 
                 "description": "生活的沉重，学会与痛苦共处"},
                {"name": "暖暖内含光", "year": 2004, 
                 "theme_color": "#E63946", "mood": "疲惫", 
                 "description": "删除记忆后的重生与领悟"},
                {"name": "时时刻刻", "year": 2002, 
                 "theme_color": "#6B7280", "mood": "疲惫", 
                 "description": "三个时代女性的生命沉思"},
                {"name": "出租车司机", "year": 1976, 
                 "theme_color": "#2D3436", "mood": "疲惫", 
                 "description": "城市孤独者的灵魂救赎"},
                
                # 焦虑
                {"name": "心灵捕手", "year": 1997, 
                 "theme_color": "#1E90FF", "mood": "焦虑", 
                 "description": "天才少年的自我发现与疗愈"},
                {"name": "美丽心灵", "year": 2001, 
                 "theme_color": "#3CB371", "mood": "焦虑", 
                 "description": "数学家与精神疾病的抗争"},
                {"name": "海边卡夫卡", "year": 2004, 
                 "theme_color": "#7B68EE", "mood": "焦虑", 
                 "description": "村上春树式的青春迷失与寻找"},
                {"name": "黑天鹅", "year": 2010, 
                 "theme_color": "#1A1A2E", "mood": "焦虑", 
                 "description": "艺术追求与自我毁灭的边缘"},
                
                # 悲伤
                {"name": "泰坦尼克号", "year": 1997, 
                 "theme_color": "#1E3A5F", "mood": "悲伤", 
                 "description": "史诗爱情悲剧，永恒的承诺"},
                {"name": "霸王别姬", "year": 1993, 
                 "theme_color": "#8B0000", "mood": "悲伤", 
                 "description": "人生如戏，戏如人生的悲歌"},
                {"name": "活着", "year": 1994, 
                 "theme_color": "#654321", "mood": "悲伤", 
                 "description": "福贵的一生，苦难中的坚韧"},
                {"name": "熔炉", "year": 2011, 
                 "theme_color": "#2F4F4F", "mood": "悲伤", 
                 "description": "真实事件改编，黑暗中的微光"},
                
                # 愤怒
                {"name": "搏击俱乐部", "year": 1999, 
                 "theme_color": "#1A1A1A", "mood": "愤怒", 
                 "description": "消费主义时代的反叛与觉醒"},
                {"name": "七宗罪", "year": 1995, 
                 "theme_color": "#2D2D2D", "mood": "愤怒", 
                 "description": "人性阴暗面的深刻剖析"},
                {"name": "华尔街之狼", "year": 2013, 
                 "theme_color": "#DAA520", "mood": "愤怒", 
                 "description": "金钱与权力的疯狂追逐"},
                {"name": "发条橙", "year": 1971, 
                 "theme_color": "#FFD700", "mood": "愤怒", 
                 "description": "极端暴力与社会控制的反思"},
                
                # 迷茫
                {"name": "楚门的世界", "year": 1998, 
                 "theme_color": "#4682B4", "mood": "迷茫", 
                 "description": "真实与虚假的边界探索"},
                {"name": "黑客帝国", "year": 1999, 
                 "theme_color": "#00FF00", "mood": "迷茫", 
                 "description": "虚拟与现实的哲学思考"},
                {"name": "星际穿越", "year": 2014, 
                 "theme_color": "#001A33", "mood": "迷茫", 
                 "description": "爱与时间的终极命题"},
                {"name": "无问西东", "year": 2018, 
                 "theme_color": "#CD853F", "mood": "迷茫", 
                 "description": "四个时代的青春与选择"},
            ]
            
            # 按心情筛选
            filter_mood_movie = st.selectbox("按心情选择电影", ["全部"] + list(MOOD_TYPES.keys()), key="movie_filter")
            
            # 显示电影列表
            if filter_mood_movie == "全部":
                filtered_movies = movie_recommendations
            else:
                filtered_movies = [m for m in movie_recommendations if m["mood"] == filter_mood_movie]
            
            # 显示电影卡片
            cols = st.columns(2)
            for i, movie in enumerate(filtered_movies):
                with cols[i % 2]:
                    # 电影卡片 - 提高对比度
                    st.markdown(
                        f"<div style='background: linear-gradient(135deg, #FAFAFA, #F5F5F5); "
                        f"border-left: 6px solid {movie['theme_color']}; "
                        f"padding: 22px; border-radius: 12px; margin: 10px 0; box-shadow: 0 2px 8px rgba(0,0,0,0.08);'>"
                        f"<h4 style='color: #1a1a1a; margin-bottom: 8px; font-weight: 600;'>"
                        f"🎬 {movie['name']} <span style='font-size: 14px; color: #888; font-weight: normal;'>({movie['year']})</span></h4>"
                        f"<p style='color: #2d2d2d; margin: 10px 0; font-size: 14px; line-height: 1.5;'>{movie['description']}</p>"
                        f"<div style='display: flex; align-items: center; gap: 10px; margin-top: 12px;'>"
                        f"<span style='background-color: {movie['theme_color']}; padding: 5px 14px; "
                        f"border-radius: 20px; font-size: 13px; color: white; font-weight: 500;'>"
                        f"{get_mood_emoji(movie['mood'])} {movie['mood']}</span>"
                        f"</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                    
                    # 主题色显示
                    st.color_picker(f"主题色", movie['theme_color'], disabled=True, 
                                  label_visibility="collapsed",
                                  key=f"color_{movie['name']}")
                    st.markdown("---")


def render_ai_page():
    """渲染 AI 助手页面"""
    st.title("🤖 AI 生活助手")
    
    st.info("DeepSeek API 集成中...")
    
    # AI 功能选项
    ai_features = {
        "📋 每日简报": "生成今日生活总结",
        "💬 生活锐评": "获得今日点评",
        "🌳 心情树洞": "倾诉与陪伴",
        "💡 智能建议": "获取个性化建议"
    }
    
    for feature, desc in ai_features.items():
        with st.expander(feature):
            st.write(desc)
            if st.button(f"启动 {feature.split()[1]}", key=feature):
                st.warning("AI 功能开发中...")


def render_settings_page():
    """渲染设置页面"""
    st.title("⚙️ 设置")
    
    # 基础信息
    st.markdown("#### 👤 基础信息")
    
    # 初始化会话状态
    if "user_height" not in st.session_state:
        st.session_state.user_height = 170
    if "user_weight" not in st.session_state:
        st.session_state.user_weight = 65
    if "user_gender" not in st.session_state:
        st.session_state.user_gender = "男"
    if "user_age" not in st.session_state:
        st.session_state.user_age = 25
    
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.user_height = st.number_input("身高 (cm)", min_value=100, max_value=250, value=st.session_state.user_height)
        st.session_state.user_gender = st.selectbox("性别", ["男", "女"], index=0 if st.session_state.user_gender == "男" else 1)
    
    with col2:
        st.session_state.user_weight = st.number_input("体重 (kg)", min_value=30, max_value=200, value=st.session_state.user_weight)
        st.session_state.user_age = st.number_input("年龄", min_value=1, max_value=120, value=st.session_state.user_age)
    
    # BMI计算
    height_m = st.session_state.user_height / 100
    bmi = st.session_state.user_weight / (height_m ** 2) if height_m > 0 else 0
    
    # BMI分类
    bmi_category = ""
    bmi_color = ""
    if bmi < 18.5:
        bmi_category = "偏瘦"
        bmi_color = "#3B82F6"
    elif 18.5 <= bmi < 24:
        bmi_category = "正常"
        bmi_color = "#10B981"
    elif 24 <= bmi < 28:
        bmi_category = "超重"
        bmi_color = "#F59E0B"
    else:
        bmi_category = "肥胖"
        bmi_color = "#EF4444"
    
    # 显示BMI结果
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 20px; margin-top: 1rem; padding: 1rem; background: var(--bg-hover); border-radius: 12px;">
        <div style="text-align: center;">
            <div style="font-size: 3rem; font-weight: bold; color: {bmi_color};">{bmi:.1f}</div>
            <div style="font-size: 0.9rem; color: var(--text-secondary);">BMI</div>
        </div>
        <div style="flex: 1;">
            <div style="font-size: 1.2rem; font-weight: 600; color: {bmi_color};">{bmi_category}</div>
            <div style="font-size: 0.85rem; color: var(--text-muted);">
                偏瘦(&lt;18.5) | 正常(18.5-24) | 超重(24-28) | 肥胖(&gt;=28)
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 建议睡眠时长
    st.markdown("#### 😴 建议睡眠时长")
    
    def get_sleep_recommendation(age, gender):
        if age < 1:
            return "14-17小时"
        elif age < 3:
            return "12-14小时"
        elif age < 6:
            return "10-12小时"
        elif age < 13:
            return "9-11小时"
        elif age < 18:
            return "8-10小时"
        elif age < 65:
            return "7-9小时"
        else:
            return "7-8小时"
    
    sleep_rec = get_sleep_recommendation(st.session_state.user_age, st.session_state.user_gender)
    
    st.markdown(f"""
    <div style="padding: 1rem; background: var(--bg-hover); border-radius: 12px;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 2rem;">💤</span>
            <div>
                <div style="font-size: 1.1rem; font-weight: 600;">根据您的年龄 ({st.session_state.user_age}岁)，建议每日睡眠时长为：</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: var(--primary); margin-top: 0.5rem;">{sleep_rec}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    # 基本设置
    st.markdown("#### ⚙️ 基本设置")
    
    col1, col2 = st.columns(2)
    with col1:
        language = st.selectbox("语言", ["中文", "English"])
        notifications = st.checkbox("启用通知", value=True)
    
    with col2:
        dark_mode = st.checkbox("深色模式", value=False)
        anonymous = st.checkbox("匿名模式", value=False)
    
    st.divider()
    
    # 预算设置
    st.markdown("#### 💰 预算设置")
    
    budget_cols = st.columns(3)
    budgets = ["餐饮", "交通", "购物"]
    for col, budget in zip(budget_cols, budgets):
        with col:
            st.number_input(f"{budget}预算 (¥)", min_value=0, value=1000)
    
    st.divider()
    
    # 数据管理
    st.markdown("#### 📊 数据管理")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.button("📤 导出数据")
    with col2:
        st.button("📥 导入数据")
    with col3:
        st.button("☁️ 云备份")
    
    st.divider()
    
    if st.button("关于项目", use_container_width=True):
        st.markdown("""
        ### 🌟 你今天活得怎么样？
        
        全生活操作系统 - 第二大脑 + 私人生活教练
        
        **版本**: 1.0.0
        
        集饮食营养、消费理财、运动健康、睡眠管理、情绪日记于一体，
        依托数据洞察 + AI 人格化交互，帮助用户记录、理解、优化生活。
        """)


def render_quick_actions():
    """渲染底部快捷操作"""
    st.divider()
    
    quick_cols = st.columns(4)
    
    quick_actions = [
        ("🍽️ 记饮食", "diet"),
        ("💰 记支出", "expense"),
        ("🏃 记运动", "exercise"),
        ("😴 记睡眠", "sleep")
    ]
    
    for col, (label, page) in zip(quick_cols, quick_actions):
        with col:
            if st.button(label, use_container_width=True):
                st.session_state.current_page = page
                st.rerun()


if __name__ == "__main__":
    main()
