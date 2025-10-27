import streamlit as st
import random
import csv
import os
from datetime import datetime
import time
# 页面配置
st.set_page_config(page_title="Energy Monitor System", layout="wide")

# 初始化 session_state
if "monitoring" not in st.session_state:
    st.session_state.monitoring = False
if "power" not in st.session_state:
    st.session_state.power = 0
if "energy" not in st.session_state:
    st.session_state.energy = 0.0
if "cost_rate" not in st.session_state:
    st.session_state.cost_rate = 0.12
if "records" not in st.session_state:
    st.session_state.records = []
if "power_data" not in st.session_state:
    st.session_state.power_data = []
if "time_data" not in st.session_state:
    st.session_state.time_data = []
if "start_time" not in st.session_state:
    st.session_state.start_time = None

# 标题
st.title("Energy Monitor System")

# 当前时间（含毫秒）
current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
st.write(f"**Current Time:** {current_time}")

# 能耗数据展示
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current Power", f"{st.session_state.power} W")
with col2:
    st.metric("Total Energy", f"{st.session_state.energy:.4f} kWh")
with col3:
    cost = st.session_state.energy * st.session_state.cost_rate
    st.metric("Estimated Cost", f"${cost:.2f}")

# 控制按钮
start_col, stop_col = st.columns(2)
with start_col:
    if st.button("Start Monitor", disabled=st.session_state.monitoring):
        st.session_state.monitoring = True
        st.session_state.records.clear()
        st.session_state.power_data.clear()
        st.session_state.time_data.clear()
        st.session_state.start_time = datetime.now()
with stop_col:
    if st.button("Stop Monitor", disabled=not st.session_state.monitoring):
        st.session_state.monitoring = False
        if st.session_state.records:
            # 生成默认文件名
            end_time = datetime.now()
            default_name = f"{st.session_state.start_time.strftime('%Y%m%d_%H%M%S')}_to_{end_time.strftime('%Y%m%d_%H%M%S')}_energy_data.csv"
            st.download_button(
                label="Download CSV",
                data="\n".join([",".join(map(str, row)) for row in [["时间", "功率(W)", "累计能耗(kWh)", "预估费用($)"]] + st.session_state.records]),
                file_name=default_name,
                mime="text/csv"
            )

# 实时更新逻辑：使用占位符 + 自动刷新避免 rerun
placeholder = st.empty()
if st.session_state.monitoring:
    # 模拟实时功率
    st.session_state.power = random.randint(200, 5000)
    # 累加能耗（100ms 间隔）
    st.session_state.energy += st.session_state.power / 1000.0 / 3600.0 / 10.0
    # 记录数据
    record_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    cost = st.session_state.energy * st.session_state.cost_rate
    st.session_state.records.append([record_time, st.session_state.power, round(st.session_state.energy, 4), round(cost, 2)])
    # 更新图表数据
    st.session_state.power_data.append(st.session_state.power)
    st.session_state.time_data.append(record_time)
    # 限制最近500个点
    if len(st.session_state.power_data) > 500:
        st.session_state.power_data.pop(0)
        st.session_state.time_data.pop(0)
    # 使用占位符更新图表，无需 rerun
    with placeholder.container():
        chart_data = {"Time": st.session_state.time_data, "Power (W)": st.session_state.power_data}
        st.line_chart(chart_data, x="Time", y="Power (W)", use_container_width=True)
    # 使用 time.sleep 实现自动刷新，避免手动 rerun
    time.sleep(0.1)
    st.rerun()
else:
    # 非监控状态绘制图表或提示
    if st.session_state.power_data:
        with placeholder.container():
            chart_data = {"Time": st.session_state.time_data, "Power (W)": st.session_state.power_data}
            st.line_chart(chart_data, x="Time", y="Power (W)", use_container_width=True)
    else:
        placeholder.info("Start monitoring to see real-time chart.")

