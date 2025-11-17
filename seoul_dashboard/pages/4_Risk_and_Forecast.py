# pages/4_Risk_and_Forecast.py

import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
from datetime import datetime

# app.py에서 정의한 load_data 함수를 import합니다.
from app import load_data 

# 데이터 로드
df = load_data("seoul.csv")

st.title("🚨 4. 리스크 및 노후도 분석")
st.markdown("특정 지역의 가격 분포를 분석하여 **이상 거래**를 탐색하고, **건물 노후도**에 따른 리스크를 평가합니다.")

# --- 1. 데이터 전처리 ---
# 현재 연도 설정 (노후도 계산용)
CURRENT_YEAR = datetime.now().year

# '건축년도' NaN 값 처리 및 '건물 나이' 계산
df['건축년도'] = pd.to_numeric(df['건축년도'], errors='coerce')
df['건물 나이'] = CURRENT_YEAR - df['건축년도']


# --- 2. 사이드바 필터 ---
st.sidebar.header("🔍 분석 필터 설정")

# 자치구 선택 필터 (이상치 분석용)
selected_gu_risk = st.sidebar.selectbox(
    "**분석할 자치구 선택:**",
    options=df['자치구명'].unique(),
    index=0 
)
# 임대 유형 선택 필터
selected_type_risk = st.sidebar.selectbox(
    "**가격 분석 유형:**",
    options=['전세', '월세'],
    index=0
)

# --- 3. 가격 분포 및 이상치 탐색 ---
st.header("1. 가격 분포 및 이상치(Outlier) 탐색")
st.markdown(f"**{selected_gu_risk}**의 **{selected_type_risk}** 가격 분포를 확인하여, 통계적으로 **매우 비싼 거래**를 탐색합니다.")

# 필터링
risk_df = df[
    (df['자치구명'] == selected_gu_risk) & 
    (df['전월세구분'] == selected_type_risk)
].copy()

price_col = '보증금(만원)'
title_suffix = '보증금'

if not risk_df.empty and len(risk_df) > 10:
    
    # B. 박스 플롯 (이상치)
    fig_box = px.box(
        risk_df,
        y=price_col,
        title='가격 이상치 (Outlier) 시각화',
        labels={price_col: f'{title_suffix} (만원)'},
        template='plotly_white'
    )
    st.plotly_chart(fig_box, use_container_width=True)

    # C. 이상치 거래 목록 (IQR 기반)
    Q1 = risk_df[price_col].quantile(0.25)
    Q3 = risk_df[price_col].quantile(0.75)
    IQR = Q3 - Q1
    
    # 상한 이상치: Q3 + 1.5 * IQR 보다 비싼 거래
    outliers = risk_df[risk_df[price_col] > Q3 + 1.5 * IQR].sort_values(by=price_col, ascending=False)
    
    if not outliers.empty:
        st.subheader("🚨 위험 거래 경고 (통계적 이상치 Top 5)")
        st.warning("경고: 해당 거래는 시장 평균 대비 **매우 높은 가격**에 형성된 것으로 보입니다. 가격 리스크를 확인하세요.")
        st.dataframe(outliers[['법정동명', '임대면적', price_col, '임대료(만원)', '건물용도', '건축년도']].head(5))
    else:
        st.info("해당 지역에서는 통계적으로 유의미한 가격 이상 거래가 발견되지 않았습니다.")
        
else:
    st.info("선택된 조건에 맞는 데이터가 부족하여 이상치 분석을 수행할 수 없습니다.")

st.markdown("---")

# --- 4. 건물 노후도 분석 (새로운 기능) ---
st.header("2. 건물 노후도 분석")
st.markdown("건축년도를 기준으로 건물의 나이를 계산하여 **노후 건물 거래 비중**과 **가격 영향**을 분석합니다.")

# 노후도 분류 기준 (예시)
def classify_age(age):
    if pd.isna(age):
        return '정보 없음'
    elif age <= 5:
        return '신축급 (5년 이하)'
    elif age <= 10:
        return '준신축 (6~10년)'
    elif age <= 20:
        return '중간 (11~20년)'
    else:
        return '노후 (20년 초과)'

df['노후도 분류'] = df['건물 나이'].apply(classify_age) 

# A. 노후도별 거래 비중
st.subheader("건물 노후도별 거래 비중")
age_counts = df.groupby('노후도 분류', observed=True).size().reset_index(name='계약 건수')

fig_age_pie = px.pie(
    age_counts,
    values='계약 건수',
    names='노후도 분류',
    title='전체 계약에서 노후도 분류별 비중',
    template='plotly_white',
    hole=.3
)
st.plotly_chart(fig_age_pie, use_container_width=True)


# B. 노후도에 따른 가격 비교
st.subheader(f"노후도별 평균 {selected_type_risk} 가격 비교")

# 노후도와 선택된 유형에 따른 평균 보증금 계산
avg_price_by_age = df[df['전월세구분'] == selected_type_risk].groupby('노후도 분류', observed=True)['보증금(만원)'].mean().reset_index(name='평균 보증금')

fig_age_price = px.bar(
    avg_price_by_age,
    x='노후도 분류',
    y='평균 보증금',
    color='평균 보증금',
    title=f'건물 노후도에 따른 평균 {selected_type_risk} 보증금 (만원)',
    labels={'평균 보증금': '평균 보증금 (만원)'},
    template='plotly_white'
)
st.plotly_chart(fig_age_price, use_container_width=True)

st.info("건물 나이가 많을수록 **보수 및 시설 하자** 위험이 높아질 수 있습니다.")