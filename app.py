
# app.py 开头部分
import streamlit as st
import sqlite3

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

# 这一行必须在所有数据库操作之前
init_db()

# Helper functions for database operations
def get_db_connection():
    conn = sqlite3.connect('demands.db')
    conn.row_factory = sqlite3.Row  # This allows access to columns by name
    return conn

def insert_demand(demand):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Ensure 'created_at' is included in the insert statement
    cursor.execute(
        "INSERT INTO demands (id, title, description, budget, contact, status, taker, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (demand['id'], demand['title'], demand['description'], demand['budget'],
         demand['contact'], demand['status'], demand['taker'], demand['created_at'])
    )
    conn.commit()
    conn.close()

def get_all_demands():
    try:
        conn = sqlite3.connect('demands.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM demands ORDER BY created_at DESC")
        rows = cursor.fetchall()
        conn.close()
        # 转换成字典列表
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
                "created_at": row[7]
            })
        return demands
    except Exception as e:
        st.error(f"数据库查询失败: {e}")
        return []

def update_demand_status_and_taker(demand_id, taker_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE demands SET status = ?, taker = ? WHERE id = ?",
        ('taken', taker_name, demand_id)
    )
    conn.commit()
    conn.close()

# Initialize session state for handling job taking
if 'current_taking_demand_id' not in st.session_state:
    st.session_state.current_taking_demand_id = None

st.set_page_config(page_title="岁晚文社·接稿小站", layout="wide")
st.title("📝 岁晚文社·接稿小站 · 发布需求 | 接稿接单")

# ---------- 侧边栏：发布需求 ----------
with st.sidebar:
    st.header("➕ 发布新需求")
    with st.form("publish_form", clear_on_submit=True):
        title = st.text_input("需求标题 *")
        description = st.text_area("详细描述")
        budget = st.text_input("预算（选填）")
        contact = st.text_input("联系方式（选填）")
        submitted = st.form_submit_button("发布")
        if submitted and title.strip():
            new_demand = {
                "id": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "budget": budget,
                "contact": contact,
                "status": "open",
                "taker": None,
                "created_at": datetime.now().isoformat() # Add timestamp here
            }
            insert_demand(new_demand) # Insert into DB
            st.success("发布成功！")
            st.rerun()
        elif submitted:
            st.error("标题不能为空")

# ---------- 主区域：需求列表 ----------
st.header("📋 当前需求")

demands_from_db = get_all_demands() # Load demands from database

if not demands_from_db:
    st.info("暂无需求，在左边发布第一个吧～")
else:
    for demand in demands_from_db:
        with st.container():
            col1, col2 = st.columns([4, 1])
            with col1:
                st.subheader(f"📌 {demand['title']}")
                st.write(f"**描述**：{demand['description']}")
                if demand['budget']:
                    st.write(f"**预算**：{demand['budget']}")
                if demand['contact']:
                    st.write(f"**联系方式**：{demand['contact']}")
                status = "🟢 待接稿" if demand['status'] == 'open' else "🔒 已接稿"
                st.write(f"**状态**：{status}")
                if demand['taker']:
                    st.write(f"**接稿人**：{demand['taker']}")
                if demand['created_at']:
                    # Format the timestamp for better readability
                    dt_object = datetime.fromisoformat(demand['created_at'])
                    st.write(f"**发布时间**：{dt_object.strftime('%Y-%m-%d %H:%M:%S')}")
            with col2:
                if demand['status'] == 'open':
                    if st.session_state.current_taking_demand_id == demand['id']:
                        with st.form(key=f"take_form_{demand['id']}", clear_on_submit=False):
                            taker_name = st.text_input("你的名字或昵称", key=f"taker_name_input_{demand['id']}")
                            col_confirm, col_cancel = st.columns([1, 1])
                            with col_confirm:
                                if st.form_submit_button("确认接稿"):
                                    if taker_name.strip():
                                        update_demand_status_and_taker(demand['id'], taker_name.strip()) # Update DB
                                        st.session_state.current_taking_demand_id = None
                                        st.success("接稿成功！")
                                        st.rerun()
                                    else:
                                        st.error("请填写你的名字或昵称")
                            with col_cancel:
                                if st.form_submit_button("取消", help="取消接稿", type="secondary"):
                                    st.session_state.current_taking_demand_id = None
                                    st.rerun()
                    elif st.button("✍️ 接稿", key=f"btn_{demand['id']}"):
                        st.session_state.current_taking_demand_id = demand['id']
                        st.rerun()
                else:
                    st.button("已接", disabled=True, key=f"disabled_{demand['id']}")
            st.divider()
