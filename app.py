import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io

# 1. Supabase 연결
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Streamlit Cloud의 Secrets 설정을 확인해주세요 (URL, KEY 누락).")
    st.stop()

st.set_page_config(page_title="S&C FABRIC FINDER", layout="wide")

# 기존 프로그램의 모든 컬럼 리스트 (업로드해주신 엑셀 기준)
ALL_COLUMNS = [
    "날짜", "브랜드 및 제안처", "스타일 넘버", "업체명", "제품명", 
    "S&C 원단명", "혼용률", "원단스펙", "원단 무게", "폭(IN)", 
    "제시 폭", "원가(YDS)", "RMB(yds)", "RMB(M)", "전달가격", 
    "마진(%)", "재고 및 running"
]

st.title("🧵 S&C 원단 정보 파인더 (Web v2)")

menu = st.sidebar.radio("메뉴", ["🔍 조회 및 검색", "📥 엑셀 데이터 업로드", "⚙️ 데이터 관리"])

# --- 기능 1: 조회 및 검색 ---
if menu == "🔍 조회 및 검색":
    st.subheader("원단 정보 검색")
    
    # 검색 필터
    col1, col2 = st.columns([1, 2])
    with col1:
        s_target = st.selectbox("검색 기준", ["전체"] + ALL_COLUMNS)
    with col2:
        s_keyword = st.text_input("검색어 입력")

    # 데이터 가져오기
    res = supabase.table("fabrics").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # 컬럼 순서 고정 (id 제외)
        df_display = df[ALL_COLUMNS]
        
        if s_keyword:
            if s_target == "전체":
                mask = df_display.astype(str).apply(lambda x: x.str.contains(s_keyword, case=False)).any(axis=1)
                df_display = df_display[mask]
            else:
                df_display = df_display[df_display[s_target].astype(str).str.contains(s_keyword, case=False)]

        st.info(f"총 {len(df_display)}개의 데이터가 검색되었습니다.")
        st.dataframe(df_display, use_container_width=True)
        
        # 엑셀 다운로드
        towrite = io.BytesIO()
        df_display.to_excel(towrite, index=False, engine='openpyxl')
        st.download_button("📥 현재 결과 엑셀 저장", towrite.getvalue(), "fabric_list.xlsx")
    else:
        st.write("등록된 데이터가 없습니다.")

# --- 기능 2: 엑셀 데이터 업로드 (ValueError 해결 버전) ---
elif menu == "📥 엑셀 데이터 업로드":
    st.subheader("대량 데이터 업로드")
    st.write("엑셀 파일을 선택하면 Supabase 클라우드 DB에 바로 저장됩니다.")
    
    file = st.file_uploader("엑셀 파일 선택", type=["xlsx", "xls"])
    
    if file:
        df_up = pd.read_excel(file)
        
        # [ValueError 해결 코드] 
        # 1. 엑셀의 NaN(빈칸)을 빈 문자열("")로 변경
        # 2. 모든 데이터를 문자열로 변환하여 JSON 에러 방지
        df_up = df_up.fillna("").astype(str)
        
        st.write("미리보기 (상위 5개):")
        st.dataframe(df_up.head())

        if st.button("서버에 업로드 시작"):
            # 엑셀 컬럼이 DB 컬럼과 일치하는 것만 필터링
            data_to_insert = []
            for _, row in df_up.iterrows():
                # DB 컬럼에 존재하는 항목만 딕셔너리로 생성
                clean_row = {col: row[col] for col in ALL_COLUMNS if col in df_up.columns}
                data_to_insert.append(clean_row)

            try:
                # 데이터가 너무 많을 경우를 대비해 100개씩 끊어서 전송
                for i in range(0, len(data_to_insert), 100):
                    supabase.table("fabrics").insert(data_to_insert[i:i+100]).execute()
                st.success(f"성공적으로 {len(data_to_insert)}건의 데이터를 업로드했습니다!")
            except Exception as e:
                st.error(f"업로드 실패: {e}")

# --- 기능 3: 데이터 관리 (삭제) ---
elif menu == "⚙️ 데이터 관리":
    st.subheader("데이터 초기화")
    if st.button("🔥 전체 데이터 삭제"):
        if st.checkbox("정말로 모든 데이터를 삭제하시겠습니까?"):
            supabase.table("fabrics").delete().neq("id", 0).execute()
            st.success("데이터베이스가 초기화되었습니다.")
