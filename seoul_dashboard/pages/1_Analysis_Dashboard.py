# pages/1_Analysis_Dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# app.py에서 정의한 load_data 함수를 import하여 데이터를 가져옵니다.
from app import load_data 

# 데이터 로드
df = load_data("seoul.csv")

# --- 1. 페이지 제목 및 필터 ---
st.title("📊 1. 자치구별 상세 분석 대시보드")
st.markdown("전세/월세 평균 계약 정보 및 주택 분포, 가격 효율성을 확인하세요.")

# 사이드바 필터
st.sidebar.header("🔍 대시보드 필터 설정")

# 자치구 선택 필터
selected_gu = st.sidebar.multiselect(
    "**분석할 자치구 선택:**",
    options=df['자치구명'].unique(),
    default=df['자치구명'].unique()[:5]
)

# 데이터 필터링
filtered_df = df[
    (df['자치구명'].isin(selected_gu))
]

# 필터링된 데이터가 없는 경우 처리
if filtered_df.empty:
    st.warning("선택하신 자치구에 해당하는 데이터가 없습니다. 필터를 변경해주세요.")
    st.stop()


st.markdown("---")

# --- 2. 전세/월세 평균 및 계약 건수 분석 ---
st.header("1. 전세/월세 계약 건수 및 평균 가격")
st.markdown("선택된 자치구의 전세와 월세 계약 현황을 비교합니다.")

# 전세 및 월세 데이터 분리
df_jeonse = filtered_df[filtered_df['전월세구분'] == '전세']
df_wolse = filtered_df[filtered_df['전월세구분'] == '월세']

# 2-1. 구별 전세 통계
jeonse_summary = df_jeonse.groupby('자치구명').agg(
    전세_계약_건수=('자치구명', 'size'),
    전세_평균_보증금=('보증금(만원)', 'mean')
).reset_index()
jeonse_summary['전세_평균_보증금'] = jeonse_summary['전세_평균_보증금'].round(0).astype(int)

# 2-2. 구별 월세 통계
wolse_summary = df_wolse.groupby('자치구명').agg(
    월세_계약_건수=('자치구명', 'size'),
    월세_평균_보증금=('보증금(만원)', 'mean'),
    월세_평균_임대료=('임대료(만원)', 'mean')
).reset_index()
wolse_summary['월세_평균_보증금'] = wolse_summary['월세_평균_보증금'].round(0).astype(int)
wolse_summary['월세_평균_임대료'] = wolse_summary['월세_평균_임대료'].round(0).astype(int)

# 전세와 월세 통계를 병합
analysis_df = pd.merge(jeonse_summary, wolse_summary, on='자치구명', how='outer').fillna(0)

# 시각화 (전세/월세 계약 건수 비교)
st.subheader("계약 건수 비교 (전세 vs 월세)")
fig_count_comp = go.Figure(data=[
    go.Bar(name='전세 계약 건수', x=analysis_df['자치구명'], y=analysis_df['전세_계약_건수'], marker_color='skyblue'),
    go.Bar(name='월세 계약 건수', x=analysis_df['자치구명'], y=analysis_df['월세_계약_건수'], marker_color='orange')
])
fig_count_comp.update_layout(
    title='자치구별 전세 vs 월세 계약 건수',
    xaxis_title='자치구명',
    yaxis_title='계약 건수',
    template='plotly_white'
)
st.plotly_chart(fig_count_comp, use_container_width=True)

# 데이터 테이블 (요약)
st.subheader("계약 현황 요약 테이블")
st.dataframe(analysis_df.set_index('자치구명').style.format({
    '전세_평균_보증금': '{:,.0f}', 
    '월세_평균_보증금': '{:,.0f}',
    '월세_평균_임대료': '{:,.0f}'
}))

st.markdown("---")

# --- 3. 주택 수 (자치구별 & 동별) 및 건물 유형 분석 ---
st.header("2. 주택 분포 및 건물 유형 분석")

# 3-1. 자치구별 총 계약 건수 (주택 수 대체 지표)
st.subheader("자치구별 총 계약 건수 비중")
gu_total_count = filtered_df.groupby('자치구명').size().reset_index(name='총 계약 건수')

fig_gu_total = px.pie(
    gu_total_count,
    values='총 계약 건수',
    names='자치구명',
    title='선택된 자치구의 계약 건수 비중',
    hole=.4,
    template='plotly_white'
)
st.plotly_chart(fig_gu_total, use_container_width=True)

# 3-2. 동별 주택 수 (계약 건수 기준)
st.subheader("동별 계약 건수 (상위 10개 동)")

dong_count = filtered_df.groupby(['자치구명', '법정동명']).size().reset_index(name='계약 건수')
dong_count = dong_count.sort_values(by='계약 건수', ascending=False).head(10)

fig_dong_count = px.bar(
    dong_count,
    x='법정동명',
    y='계약 건수',
    color='자치구명',
    title='동별 계약 건수 Top 10',
    template='plotly_white'
)
st.plotly_chart(fig_dong_count, use_container_width=True)

# 3-3. 건물 유형별 계약 건수
st.subheader("건물 유형별 계약 건수")
building_count = filtered_df.groupby('건물용도').size().reset_index(name='계약 건수')
building_count = building_count.sort_values(by='계약 건수', ascending=False)

fig_bld_count = px.bar(
    building_count,
    x='건물용도',
    y='계약 건수',
    color='건물용도',
    title='선택된 자치구의 건물 유형별 계약 건수',
    template='plotly_white'
)
st.plotly_chart(fig_bld_count, use_container_width=True)

st.markdown("---")

# ----------------------------------------------------
# -------------------- 🌟 4. 가격 효율 분석 --------------------
# ----------------------------------------------------

st.header("3. 가격 효율 분석 (면적당 가격)")
st.markdown("임대 면적 1㎡당 보증금 및 임대료를 계산하여 자치구별 가격 효율성을 비교합니다.")

# 데이터 준비: 평당 가격 계산
# 0으로 나누는 오류 방지를 위해 임대면적 0인 행은 제외
efficiency_df = filtered_df[filtered_df['임대면적'] > 0].copy()

# 평당 (1㎡당) 보증금
efficiency_df['평당_보증금'] = efficiency_df['보증금(만원)'] / efficiency_df['임대면적']

# 평당 (1㎡당) 임대료
efficiency_df['평당_임대료'] = efficiency_df['임대료(만원)'] / efficiency_df['임대면적']


# 분석할 지표 선택 (사이드바에 추가됨)
st.sidebar.subheader("효율 분석 지표 선택")
selected_efficiency_metric = st.sidebar.selectbox(
    "분석 지표:",
    options=['전세 평당 보증금 (만원/㎡)', '월세 평당 임대료 (만원/㎡)', '월세 평당 보증금 (만원/㎡)']
)

# 4-1. 자치구별 평균 평당 가격 비교
st.subheader(f"자치구별 평균 {selected_efficiency_metric} 비교")

if selected_efficiency_metric == '전세 평당 보증금 (만원/㎡)':
    plot_df = efficiency_df[efficiency_df['전월세구분'] == '전세']
    agg_col = '평당_보증금'
    y_title = '평균 평당 보증금 (만원/㎡)'
    
elif selected_efficiency_metric == '월세 평당 임대료 (만원/㎡)':
    plot_df = efficiency_df[efficiency_df['전월세구분'] == '월세']
    agg_col = '평당_임대료'
    y_title = '평균 평당 임대료 (만원/㎡)'
    
else: # '월세 평당 보증금 (만원/㎡)'
    plot_df = efficiency_df[efficiency_df['전월세구분'] == '월세']
    agg_col = '평당_보증금'
    y_title = '평균 평당 보증금 (만원/㎡)'

# 자치구별 평균 계산
avg_efficiency = plot_df.groupby('자치구명')[agg_col].mean().reset_index(name='평균_효율_값')
avg_efficiency['평균_효율_값'] = avg_efficiency['평균_효율_값'].round(2)


fig_efficiency = px.bar(
    avg_efficiency.sort_values(by='평균_효율_값', ascending=False),
    x='자치구명',
    y='평균_효율_값',
    color='평균_효율_값',
    title=f'자치구별 {selected_efficiency_metric} 분포',
    template='plotly_white'
)
fig_efficiency.update_yaxes(title=y_title)
st.plotly_chart(fig_efficiency, use_container_width=True)

st.markdown("---")

# 4-2. 가장 효율적인 거래 vs 비효율적인 거래
st.subheader(f"{selected_efficiency_metric} 기준, 효율성 Top 3 거래")

if not plot_df.empty:
    
    # 평당 가격이 높은 거래 (가장 비싼/비효율적인)
    most_expensive = plot_df.sort_values(by=agg_col, ascending=False).head(3)
    
    # 평당 가격이 낮은 거래 (가장 싼/효율적인)
    most_efficient = plot_df.sort_values(by=agg_col, ascending=True).head(3)

    col_exp, col_eff = st.columns(2)
    
    with col_exp:
        st.info(f"🚨 면적 대비 비싼 거래 (평당 가격 Top 3)")
        display_cols = ['자치구명', '법정동명', '전월세구분', agg_col, '임대면적', '보증금(만원)', '임대료(만원)']
        st.dataframe(most_expensive[display_cols].rename(columns={agg_col: '평당 가격'})
                      .set_index('자치구명').style.format({'평당 가격': '{:,.2f}'}))
        
    with col_eff:
        st.success(f"✅ 면적 대비 효율적인 거래 (평당 가격 Bottom 3)")
        st.dataframe(most_efficient[display_cols].rename(columns={agg_col: '평당 가격'})
                      .set_index('자치구명').style.format({'평당 가격': '{:,.2f}'}))
        
else:
    st.warning("선택하신 지표에 해당하는 데이터가 없어 효율성 순위를 표시할 수 없습니다.")