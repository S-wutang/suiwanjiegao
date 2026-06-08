import streamlit as st
import uuid
from supabase import create_client, Client
from datetime import datetime, timezone, timedelta

# ================== 在这里粘贴你从 Supabase 复制的信息 ==================
SUPABASE_URL = "sb_publishable_XxTceqYdyIYDob6rsL3Q-Q_lBkGmu0S"
SUPABASE_ANON_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InludWRvZmxkcHR4andjdnFibWRuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODA5MDkwNDEsImV4cCI6MjA5NjQ4NTA0MX0.2eLe2pyeyPgqa93H2sDjMWcwBrihicmjj5HuIXpMNV0"
# ===================================================================

# 初始化 Supabase 客户端
supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ---------- 北京时间 ----------
def get_beijing_time():
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz).isoformat(timespec='seconds')

# ---------- 数据库操作（现在都是操作 Supabase 云数据库了）----------
def get_all_demands():
    """从 Supabase 获取所有需求，按时间倒序"""
    response = supabase.table('demands').select('*').order('created_at', desc=True).execute()
    return response.data

def add_demand(title, description, budget, contact):
    """向 Supabase 添加新需求"""
    new_demand = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "budget": budget,
        "contact": contact,
        "status": "open",
        "taker": None,
        "created_at": get_beijing_time()
    }
    supabase.table('demands').insert(new_demand).execute()

def take_demand(demand_id, taker_name):
    """更新 Supabase 中的需求状态和接稿人"""
    supabase.table('demands').update({
        "status": "taken",
        "taker": taker_name
    }).eq('id', demand_id).execute()

# ---------- 接稿对话框 ----------
@st.dialog("✍️ 接稿确认")
def take_demand_dialog(demand_id):
    st.write("请输入你的名字或昵称：")
    taker_name = st.text_input("接稿人名称", placeholder="例：小明 或 小明@email.com")
    if st.button("确认接稿"):
        if taker_name.strip():
            take_demand(demand_id, taker_name.strip())
            st.success("接稿成功！")
            st.rerun()
        else:
            st.error("请填写接稿人名称")

# ---------- Streamlit UI ----------
st.set_page_config(page_title="接稿小站", layout="wide")
st.title("📝 岁晚文社 · 接稿小站")

# 侧边栏导航
page = st.sidebar.radio("导航", ["接稿小站", "历史记录"])

if page == "接稿小站":
    # ---------- 发布表单 ----------
    with st.sidebar:
        st.header("➕ 发布新需求")
        with st.form("publish_form", clear_on_submit=True):
            title = st.text_input("需求标题 *")
            description = st.text_area("详细描述")
            budget = st.text_input("预算（选填）")
            contact = st.text_input("联系方式（选填）")
            submitted = st.form_submit_button("发布")
            if submitted and title.strip():
                add_demand(title, description, budget, contact)
                st.success("发布成功！")
                st.rerun()
            elif submitted:
                st.error("标题不能为空")

    # ---------- 需求列表 ----------
    st.header("📋 当前需求")
    demands = get_all_demands()
    if not demands:
        st.info("暂无需求，在左边发布第一个吧～")
    else:
        for demand in demands:
            with st.container():
                col1, col2 = st.columns([4, 1])
                with col1:
                    st.subheader(f"📌 {demand['title']}")
                    st.write(f"**描述**：{demand['description']}")
                    if demand.get('budget'):
                        st.write(f"**预算**：{demand['budget']}")
                    if demand.get('contact'):
                        st.write(f"**联系方式**：{demand['contact']}")
                    st.write(f"**发布时间**：{demand['created_at']}")
                    status = "🟢 待接稿" if demand['status'] == 'open' else "🔒 已接稿"
                    st.write(f"**状态**：{status}")
                    if demand.get('taker'):
                        st.write(f"**接稿人**：{demand['taker']}")
                with col2:
                    if demand['status'] == 'open':
                        if st.button("✍️ 接稿", key=f"btn_{demand['id']}"):
                            take_demand_dialog(demand['id'])
                    else:
                        st.button("已接", disabled=True, key=f"disabled_{demand['id']}")
                st.divider()

else:  # 数据管理页面
    st.header("🗄️ 历史记录")
    demands = get_all_demands()
    if demands:
        # 为了让表格更易读，我们只选择重要的列显示
        df = pd.DataFrame(demands)
        # 调整列的顺序，并选择要显示的列
        display_columns = ['id', 'title', 'description', 'budget', 'contact', 'status', 'taker', 'created_at']
        df = df[display_columns]
        st.dataframe(df, use_container_width=True)
        # 导出 CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 导出为 CSV", csv, "demands.csv", "text/csv")
    else:
        st.info("数据库为空")
