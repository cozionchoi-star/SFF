import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
import json

# 1. Supabase 연결
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Secrets 설정을 확인해주세요.")
    st.stop()

st.set_page_config(page_title="S&C FABRIC FINDER", layout="wide")

# 전체 컬럼 정의 (엑셀 파일 기반)
ALL_COLUMNS = [
    "날짜", "브랜드 및 제안처", "스타일 넘버", "업체명", "제품명", 
    "S&C 원단명", "혼용률", "원단스펙", "원단 무게", "폭(IN)", 
    "제시 폭", "원가(YDS)", "RMB(yds)", "RMB(M)", "전달가격", 
    "마진(%)", "재고 및 running"
]

st.title("🧵 S&C 원단 정보 파인더 (Web 최종)")

menu = st.sidebar.radio("메뉴", ["🔍 조회 및 검색", "📥 엑셀 업로드", "⚙️ 데이터 관리"])

# --- 기능 1: 조회 및 검색 ---
if menu == "🔍 조회 및 검색":
    st.subheader("원단 정보 검색")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        s_target = st.selectbox("검색 기준", ["전체"] + ALL_COLUMNS)
    with col2:
        s_keyword = st.text_input("검색어 입력")

    res = supabase.table("fabrics").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # 데이터 표시 (id 제외)
        df_display = df[ALL_COLUMNS]
        
        if s_keyword:
            if s_target == "전체":
                mask = df_display.astype(str).apply(lambda x: x.str.contains(s_keyword, case=False)).any(axis=1)
                df_display = df_display[mask]
            else:
                df_display = df_display[df_display[s_target].astype(str).str.contains(s_keyword, case=False)]

        st.info(f"검색 결과: {len(df_display)} 건")
        st.dataframe(df_display, use_container_width=True)
    else:
        st.write("데이터가 없습니다. 엑셀 업로드를 먼저 진행해주세요.")

# --- 기능 2: 엑셀 업로드 (ValueError 완벽 해결) ---
elif menu == "📥 엑셀 업로드":
    st.subheader("엑셀 데이터 일괄 등록")
    st.write("기존 엑셀 파일을 그대로 업로드하세요.")
    
    file = st.file_uploader("엑셀 파일 선택", type=["xlsx", "xls"])
    
    if file:
        df_up = pd.read_excel(file)
        
        # [핵심] 모든 에러 방지 처리
        df_up = df_up.fillna("") # 빈칸을 빈 문자로
        df_up = df_up.astype(str) # 모든 형식을 문자로 (JSON 에러 방지)
        
        st.write("업로드 데이터 미리보기:")
        st.dataframe(df_up.head())

        if st.button("서버로 전송하기"):
            data_list = []
            for _, row in df_up.iterrows():
                # DB 컬럼과 일치하는 데이터만 추출
                item = {col: row[col] for col in ALL_COLUMNS if col in df_up.columns}
                data_list.append(item)

            try:
                # 50개씩 끊어서 전송하여 안정성 확보
                for i in range(0, len(data_list), 50):
                    supabase.table("fabrics").insert(data_list[i:i+50]).execute()
                st.success(f"성공! {len(data_list)}건의 데이터가 업로드되었습니다.")
            except Exception as e:
                st.error(f"전송 실패: {e}")

# --- 기능 3: 데이터 관리 ---
elif menu == "⚙️ 데이터 관리":
    st.subheader("DB 초기화")
    if st.button("모든 데이터 삭제"):
        if st.checkbox("정말로 삭제하시겠습니까?"):
            supabase.table("fabrics").delete().neq("id", 0).execute()
            st.success("삭제 완료!")
