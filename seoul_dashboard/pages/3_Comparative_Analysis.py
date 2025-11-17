# pages/3_Comparative_Analysis.py

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# app.py에서 정의한 load_data 함수를 import합니다.
from app import load_data 

# 데이터 로드
df = load_data("seoul.csv")

st.title("🔬 3. 심화 맞춤 비교 분석: 두 시장 비교하기")
st.markdown("사용자가 지정한 **두 시장 그룹(A와 B)**을 정의하고, 핵심 가격 지표를 비교하여 어떤 시장이 더 비싸고 효율적인지 쉽게 이해할 수 있습니다.")

# --- 1. 사이드바 그룹 정의 필터 ---

# 필터 옵션 준비
gu_options = sorted(df['자치구명'].unique())
type_options = ['전세', '월세', '전체']
building_options = sorted(df['건물용도'].unique())

# --- 그룹 A 정의 ---
st.sidebar.header("그룹 A 정의 (기준 시장)")
gu_A = st.sidebar.multiselect("A: 자치구", options=gu_options, default=gu_options[:2], key='gu_A')
type_A = st.sidebar.selectbox("A: 전월세 구분", options=type_options, index=2, key='type_A')
bld_A = st.sidebar.multiselect("A: 건물 용도", options=building_options, default=building_options[:2], key='bld_A')

st.sidebar.markdown("---")

# --- 그룹 B 정의 ---
st.sidebar.header("그룹 B 정의 (비교 대상)")
gu_B = st.sidebar.multiselect("B: 자치구", options=gu_options, default=gu_options[2:4], key='gu_B')
type_B = st.sidebar.selectbox("B: 전월세 구분", options=type_options, index=2, key='type_B')
bld_B = st.sidebar.multiselect("B: 건물 용도", options=building_options, default=building_options[2:4], key='bld_B')

# --- 데이터 필터링 함수 ---
def filter_group(df, gu_list, type_val, bld_list):
    df_filtered = df[df['자치구명'].isin(gu_list)]
    
    if type_val != '전체':
        df_filtered = df_filtered[df_filtered['전월세구분'] == type_val]
        
    if bld_list:
        df_filtered = df_filtered[df_filtered['건물용도'].isin(bld_list)]
        
    # 평당 보증금/임대료 효율 계산을 위해 0면적 제외
    df_filtered = df_filtered[df_filtered['임대면적'] > 0].copy()
    
    # 평당 가격 계산 (면적당 가격 효율)
    # 1㎡ 당 가격으로 쉽게 이해하도록 '면적당_가격'으로 컬럼명 변경
    df_filtered['면적당_보증금'] = df_filtered['보증금(만원)'] / df_filtered['임대면적']
    df_filtered['면적당_임대료'] = df_filtered['임대료(만원)'] / df_filtered['임대면적']
    
    return df_filtered

# --- 데이터 필터링 실행 ---
filtered_A_df = filter_group(df, gu_A, type_A, bld_A)
filtered_B_df = filter_group(df, gu_B, type_B, bld_B)


# --- 2. 비교 분석 KPI 및 통계 계산 ---

def calculate_kpis(data, name):
    if data.empty:
        return {'그룹': name, '총 계약 건수': 0, '평균 보증금(만원)': 0, '평균 월 임대료(만원)': 0, '평균 면적(㎡)': 0, '면적당 평균 보증금(만원/㎡)': 0}

    # 평균 보증금 (전세/월세 모두 포함)
    avg_deposit = data['보증금(만원)'].mean()
    # 평균 임대료 (월세가 아닌 경우 NaN 처리 후 0)
    avg_rent = data[data['전월세구분'] == '월세']['임대료(만원)'].mean()
    
    # 면적당 평균 보증금
    avg_pp_deposit = data['면적당_보증금'].mean()

    return {
        '그룹': name,
        '총 계약 건수': len(data),
        '평균 보증금(만원)': avg_deposit,
        '평균 월 임대료(만원)': avg_rent if not pd.isna(avg_rent) else 0,
        '평균 면적(㎡)': data['임대면적'].mean(),
        '면적당 평균 보증금(만원/㎡)': avg_pp_deposit
    }

kpi_A = calculate_kpis(filtered_A_df, 'Group A')
kpi_B = calculate_kpis(filtered_B_df, 'Group B')

comparison_df = pd.DataFrame([kpi_A, kpi_B]).set_index('그룹')

# --- 3. 비교 결과 시각화 및 표시 ---

st.header("1. 그룹별 핵심 지표 비교")
st.markdown("선택된 두 그룹의 **총 계약 건수, 평균 가격, 면적당 가격 효율성**을 나란히 비교합니다.")

if kpi_A['총 계약 건수'] == 0 and kpi_B['총 계약 건수'] == 0:
    st.warning("선택된 두 그룹 모두 데이터가 없습니다. 필터를 조정해 주세요.")
else:
    # 3-1. 비교 테이블 (숫자 포맷팅 개선 및 rename 오류 수정)
    st.subheader("통계 요약 테이블")
    
    # Styler 객체 생성 전에 rename을 먼저 적용하여 오류 해결
    df_for_display = comparison_df.T.rename(index={
        '평균 보증금(만원)': '평균 보증금 (만원)', 
        '평균 월 임대료(만원)': '평균 월 임대료 (만원)',
        '면적당 평균 보증금(만원/㎡)': '면적당 보증금 효율 (만원/㎡)' 
    })

    st.dataframe(df_for_display.style.format({
        'Group A': '{:,.0f}', 
        'Group B': '{:,.0f}'
    }))
    
    
    # 3-2. 핵심 지표 막대 그래프 (라벨 개선)
    st.subheader("평균 가격 및 면적 시각화")
    
    # 계약 건수는 크기가 달라서 분리
    df_plot = comparison_df.drop(columns=['총 계약 건수']).reset_index().melt(id_vars='그룹', var_name='지표', value_name='값')
    
    fig_comp = px.bar(
        df_plot,
        x='지표',
        y='값',
        color='그룹',
        barmode='group',
        title='그룹 A vs B 평균 지표 비교 (높을수록 비싸거나 넓음)',
        labels={'값': '수치 (만원 또는 ㎡)', '지표': '비교 지표'}, # 라벨 개선
        template='plotly_white'
    )
    st.plotly_chart(fig_comp, use_container_width=True)

st.markdown("---")

# --- 4. 가격 결정 요인 분석 (산점도) ---
st.header("2. 면적과 가격의 관계 (효율성 분석)")
st.markdown("**임대 면적**과 **가격**이 어떻게 변하는지 비교하여, 특정 면적 대비 비싸거나 효율적인 거래를 시각적으로 확인합니다. 회귀선이 가파를수록 면적당 가격 상승률이 높다는 의미입니다.")

# 모든 데이터를 그룹 A와 B로 구분하여 시각화할 데이터프레임 생성
plot_data = pd.concat([
    filtered_A_df.assign(Group='A'),
    filtered_B_df.assign(Group='B')
], ignore_index=True)

# 지표 선택 (보증금 또는 임대료)
price_metric = st.selectbox(
    "가격 지표 선택:",
    options=['보증금(만원)', '임대료(만원)'],
    index=0
)

if not plot_data.empty:
    fig_scatter = px.scatter(
        plot_data,
        x='임대면적',
        y=price_metric,
        color='Group',
        hover_data=['자치구명', '법정동명', '건물용도', '전월세구분'],
        trendline="ols", # 회귀선 추가 (최소자승법)
        title=f'임대 면적 (㎡)과 {price_metric}의 관계 (각 그룹의 회귀선 표시)',
        labels={'임대면적': '임대 면적 (㎡)', price_metric: price_metric},
        template='plotly_white'
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
else:
    st.warning("두 그룹 모두 선택된 조건에 맞는 데이터가 없어 산점도를 표시할 수 없습니다. 필터를 조정해 주세요.")