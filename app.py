import streamlit as st
import sqlite3
import uuid
import pandas as pd
from datetime import datetime, timezone, timedelta

# ---------- 北京时间 ----------
def get_beijing_time():
    beijing_tz = timezone(timedelta(hours=8))
    return datetime.now(beijing_tz).isoformat(timespec='seconds')

# ---------- 数据库初始化 ----------
def init_db():
    conn = sqlite3.connect('demands.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS demands (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            budget TEXT,
            contact TEXT,
            status TEXT,
            taker TEXT,
            created_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

# ---------- 数据库操作 ----------
def get_all_demands():
    conn = sqlite3.connect('demands.db')
    c = conn.cursor()
    c.execute("SELECT * FROM demands ORDER BY created_at DESC")
    rows = c.fetchall()
    conn.close()
    demands = []
    for row in rows:
        demands.append({
            "id": row[0],
            "title": row[1],
            "description": row[2],
            "budget": row[3],
            "contact": row[4],
            "status": row[5],
            "taker": row[6],
            "created_at": row[7],
        })
    return demands

def add_demand(title, description, budget, contact):
    conn = sqlite3.connect('demands.db')
    c = conn.cursor()
    new_id = str(uuid.uuid4())
    created_at = get_beijing_time()
    c.execute('''
        INSERT INTO demands (id, title, description, budget, contact, status, taker, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (new_id, title, description, budget, contact, 'open', None, created_at))
    conn.commit()
    conn.close()

def take_demand(demand_id, taker_name):
    conn = sqlite3.connect('demands.db')
    c = conn.cursor()
    c.execute('UPDATE demands SET status = ?, taker = ? WHERE id = ?', ('taken', taker_name, demand_id))
    conn.commit()
    conn.close()

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

init_db()

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
                    if demand['budget']:
                        st.write(f"**预算**：{demand['budget']}")
                    if demand['contact']:
                        st.write(f"**联系方式**：{demand['contact']}")
                    st.write(f"**发布时间**：{demand['created_at']}")
                    status = "🟢 待接稿" if demand['status'] == 'open' else "🔒 已接稿"
                    st.write(f"**状态**：{status}")
                    if demand['taker']:
                        st.write(f"**接稿人**：{demand['taker']}")
                with col2:
                    if demand['status'] == 'open':
                        if st.button("✍️ 接稿", key=f"btn_{demand['id']}"):
                            take_demand_dialog(demand['id'])
                    else:
                        st.button("已接", disabled=True, key=f"disabled_{demand['id']}")
                st.divider()

else:  # 数据管理页面
    st.header("🗄️ 数据库管理")
    demands = get_all_demands()
    if demands:
        # 显示表格
        df = pd.DataFrame(demands)
        st.dataframe(df, use_container_width=True)
        # 导出 CSV
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 导出为 CSV", csv, "demands.csv", "text/csv")
    else:
        st.info("数据库为空")
