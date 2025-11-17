import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- 1. 설정 및 데이터 로드 (모든 페이지에서 공유) ---
st.set_page_config(
    page_title="서울 부동산 대시보드",
    page_icon="🏠",
    layout="wide"
)

@st.cache_data
def load_data(file_path):
    """CSV 파일을 로드하고 전처리합니다."""
    try:
        data = pd.read_csv(file_path, encoding='utf-8')
    except UnicodeDecodeError:
        data = pd.read_csv(file_path, encoding='euc-kr') # 다른 인코딩 시도

    # 컬럼명 정리 및 전처리
    data.columns = [
        '접수년도', '자치구코드', '자치구명', '법정동코드', '법정동명', '지번구분코드', '지번구분', '본번',
        '부번', '층', '계약일', '전월세구분', '임대면적', '보증금(만원)', '임대료(만원)', '건물명',
        '건축년도', '건물용도', '계약기간', '신규계약구분', '갱신청구권사용', '종전보증금', '종전임대료'
    ]
    # 숫자로 변환 (오류 발생 시 NaN 처리 후 0으로 채움)
    data['보증금(만원)'] = pd.to_numeric(data['보증금(만원)'], errors='coerce').fillna(0)
    data['임대료(만원)'] = pd.to_numeric(data['임대료(만원)'], errors='coerce').fillna(0)
    data = data[data['전월세구분'].isin(['전세', '월세'])]
    
    # 총 거래 금액 (전세는 보증금, 월세는 보증금 + 임대료*12개월로 단순 합산하여 최고/최저를 찾기 위한 임시 지표)
    data['총거래금액_임시'] = data['보증금(만원)'] + data['임대료(만원)'] * 12
    
    return data

# 데이터를 로드하여 모든 페이지에서 사용
FILE_PATH = "seoul.csv"
df = load_data(FILE_PATH)

# --- 2. 홈 화면 구성 ---
st.title("🏡 서울 부동산 임대차 데이터 분석 대시보드")
st.markdown("### 서울시 전월세 계약 데이터를 한 눈에 확인하세요.")

st.markdown("""
이 앱은 사용자님이 제공하신 `seoul.csv` 파일을 분석하여 서울 부동산 임대차 시장의 **핵심 지표**와 **자치구별 상세 분석**을 제공합니다.
왼쪽 사이드바에서 다른 분석 페이지로 이동할 수 있습니다.
""")

st.markdown("---")

# --- 3. 핵심 지표 (KPI) 섹션 (전체 데이터 기준) ---
st.header("✨ 주요 시장 지표 요약 (전체 데이터)")

total_contracts = len(df)
avg_jeonse = df[df['전월세구분'] == '전세']['보증금(만원)'].mean()
avg_monthly_deposit = df[df['전월세구분'] == '월세']['보증금(만원)'].mean()
avg_monthly_rent = df[df['전월세구분'] == '월세']['임대료(만원)'].mean()

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(label="**총 계약 건수**", value=f"{total_contracts:,.0f} 건")
    
with col2:
    st.metric(label="**평균 전세 보증금**", value=f"{avg_jeonse:,.0f} 만원")

with col3:
    st.metric(label="**평균 월세 보증금**", value=f"{avg_monthly_deposit:,.0f} 만원")

with col4:
    st.metric(label="**평균 월세 임대료**", value=f"{avg_monthly_rent:,.0f} 만원")

st.markdown("---")

# --- 4. 구별 통계 및 최고/최저가 대시보드 ---
st.header("📍 자치구별 시장 현황")

# 4-1. 구별 계약 건수 테이블
gu_summary = df.groupby('자치구명').agg(
    계약건수=('자치구명', 'size'),
    평균_보증금=('보증금(만원)', 'mean'),
    평균_임대료=('임대료(만원)', 'mean')
).reset_index()

gu_summary['평균_보증금'] = gu_summary['평균_보증금'].round(0).astype(int)
gu_summary['평균_임대료'] = gu_summary['평균_임대료'].round(0).astype(int)
gu_summary = gu_summary.sort_values(by='계약건수', ascending=False)
gu_summary.columns = ['자치구명', '계약 건수', '평균 보증금(만원)', '평균 임대료(만원)']


col_table, col_chart = st.columns([1, 1.5])

with col_table:
    st.subheader("계약 건수 및 평균 가격")
    st.dataframe(gu_summary.set_index('자치구명'), use_container_width=True)

with col_chart:
    st.subheader("계약 건수 Top 5 자치구")
    top_5_gu = gu_summary.head(5)
    fig_gu_count = px.bar(
        top_5_gu,
        x='자치구명',
        y='계약 건수',
        color='계약 건수',
        title="거래가 가장 활발한 자치구",
        template='plotly_white'
    )
    st.plotly_chart(fig_gu_count, use_container_width=True)

st.markdown("---")

# 4-2. 가장 비싼/싼 부동산 거래 찾기 (전세/월세 구분 없음, 임시 총거래금액 기준)
st.header("💎 최고가 vs. 최저가 거래 (총거래금액_임시 기준)")

# 최고가 거래
highest_price = df['총거래금액_임시'].max()
highest_row = df[df['총거래금액_임시'] == highest_price].iloc[0]

# 최저가 거래
lowest_price = df['총거래금액_임시'].min()
lowest_row = df[df['총거래금액_임시'] == lowest_price].iloc[0]

# 정보를 표시하는 사용자 정의 함수
def display_transaction_card(row, title, icon, color):
    """최고/최저가 거래 정보를 카드 형태로 표시"""
    if row.empty:
        st.error("데이터를 찾을 수 없습니다.")
        return

    st.markdown(
        f"<div style='background-color: {color}; padding: 15px; border-radius: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1);'>"
        f"<h4>{icon} {title}</h4>"
        f"<h3>{row['자치구명']} {row['법정동명']}</h3>"
        f"<ul>"
        f"<li><strong>거래 유형:</strong> {row['전월세구분']}</li>"
        f"<li><strong>보증금:</strong> {row['보증금(만원)']:,.0f} 만원</li>"
        f"<li><strong>임대료 (월):</strong> {row['임대료(만원)']:,.0f} 만원</li>"
        f"<li><strong>면적:</strong> {row['임대면적']}㎡</li>"
        f"</ul>"
        f"</div>", 
        unsafe_allow_html=True
    )

col_high, col_low = st.columns(2)

with col_high:
    display_transaction_card(highest_row, "가장 비싼 거래", "💰", "#F0EAD6")
    
with col_low:
    display_transaction_card(lowest_row, "가장 싼 거래", "💵", "#E0F7FA")


st.markdown("---")
st.info("데이터 출처: 사용자 제공 `seoul.csv` 파일")