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
        
        # 检查数据库连接
        if not check_connection():
            init_db()
        
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
    
    # 初始化减肥模式
    if "weight_loss_mode" not in st.session_state:
        st.session_state.weight_loss_mode = False
    
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
    
    tab1, tab2, tab3 = st.tabs(["记录", "统计", "导入"])
    
    with tab1:
        st.markdown("#### 快速记账")
        
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("金额 (¥)", min_value=0.0, value=0.0)
            category = st.selectbox("分类", ["餐饮", "交通", "购物", "娱乐", "医疗", "居住", "通讯", "服饰", "投资", "其他"])
        
        with col2:
            description = st.text_input("描述")
            payment_method = st.selectbox("支付方式", ["微信", "支付宝", "现金", "银行卡"])
        
        if st.button("记一笔", type="primary"):
            st.success("记账成功！")
    
    with tab2:
        st.markdown("#### 消费统计")
        st.info("统计图表开发中...")
    
    with tab3:
        st.markdown("#### 导入账单")
        st.file_uploader("上传 CSV 文件", type=["csv"])
        st.caption("支持微信/支付宝标准格式导出账单")


def render_exercise_page():
    """渲染运动健康页面"""
    st.title("🏃 运动健康")
    
    tab1, tab2, tab3 = st.tabs(["记录", "统计", "挑战"])
    
    with tab1:
        st.markdown("#### 运动记录")
        
        col1, col2 = st.columns(2)
        with col1:
            exercise_type = st.selectbox("运动类型", ["散步", "跑步", "骑行", "游泳", "瑜伽", "力量训练", "其他"])
            duration = st.number_input("时长 (分钟)", min_value=0, value=30)
        
        with col2:
            calories = st.number_input("消耗热量 (kcal)", min_value=0, value=0)
            steps = st.number_input("步数", min_value=0, value=0)
        
        if st.button("记录运动", type="primary"):
            st.success("运动记录已添加！")
    
    with tab2:
        st.markdown("#### 运动统计")
        st.info("热力图和柱状图开发中...")
    
    with tab3:
        st.markdown("#### 运动挑战")
        st.info("挑战系统开发中...")


def render_sleep_page():
    """渲染睡眠管理页面"""
    st.title("😴 睡眠管理")
    
    st.markdown("#### 睡眠记录")
    
    col1, col2 = st.columns(2)
    with col1:
        bedtime = st.time_input("入睡时间", value=None)
        wakeup_time = st.time_input("起床时间", value=None)
    
    with col2:
        deep_sleep = st.slider("深睡时长 (小时)", 0.0, 4.0, 1.5, 0.5)
        quality = st.slider("睡眠质量", 1, 5, 3)
    
    if st.button("记录睡眠", type="primary"):
        st.success("睡眠记录已添加！")
    
    st.divider()
    
    st.markdown("#### 作息规律评分")
    st.metric("7天规律得分", "--", "--")
    st.caption("得分 = 100 - 7天就寝时间标准差 × 10")


def render_mood_page():
    """渲染情绪日记页面"""
    st.title("💭 情绪日记")
    
    st.markdown("#### 今日心情")
    
    moods = ["😊 开心", "😌 平静", "😫 疲惫", "😰 焦虑", "😢 悲伤", "😠 愤怒", "🤩 兴奋", "😕 迷茫"]
    
    selected_mood = st.selectbox("选择情绪", moods)
    intensity = st.slider("情绪强度", 1, 5, 3)
    notes = st.text_area("记录一下 (可选)", height=100)
    
    if st.button("保存心情", type="primary"):
        st.success("心情已记录！")
    
    st.divider()
    
    st.markdown("#### 情绪统计")
    st.info("情绪趋势图开发中...")


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
