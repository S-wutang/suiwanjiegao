import streamlit as st
import sqlite3
import uuid
from datetime import datetime, timezone, timedelta   # 正确导入

# ---------- 北京时间工具函数 ----------
def get_beijing_time():
    """返回当前北京时间（ISO格式字符串，不带微秒）"""
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
    created_at = get_beijing_time()   # 使用北京时间
    c.execute('''
        INSERT INTO demands (id, title, description, budget, contact, status, taker, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (new_id, title, description, budget, contact, 'open', None, created_at))
    conn.commit()
    conn.close()

def take_demand(demand_id, taker_name="接稿人 (暂未留名)"):
    conn = sqlite3.connect('demands.db')
    c = conn.cursor()
    c.execute('UPDATE demands SET status = ?, taker = ? WHERE id = ?', ('taken', taker_name, demand_id))
    conn.commit()
    conn.close()

# ---------- Streamlit UI ----------
st.set_page_config(page_title="接稿平台", layout="wide")
st.title("📝 接稿平台 · 发布需求 | 接稿接单")

# 初始化数据库
init_db()

# 侧边栏发布表单
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

# 主区域展示需求
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
                # 显示北京时间（直接显示存储的字符串）
                st.write(f"**发布时间**：{demand['created_at']}")
                status = "🟢 待接稿" if demand['status'] == 'open' else "🔒 已接稿"
                st.write(f"**状态**：{status}")
                if demand['taker']:
                    st.write(f"**接稿人**：{demand['taker']}")
            with col2:
                if demand['status'] == 'open':
                    if st.button("✍️ 接稿", key=f"btn_{demand['id']}"):
                        take_demand(demand['id'])
                        st.success("接稿成功！")
                        st.rerun()
                else:
                    st.button("已接", disabled=True, key=f"disabled_{demand['id']}")
            st.divider()
