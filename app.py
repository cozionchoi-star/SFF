import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
from datetime import datetime

# 1. Supabase 연결 설정
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Streamlit Cloud의 Settings -> Secrets에 SUPABASE_URL과 SUPABASE_KEY를 입력해주세요.")
    st.stop()

st.set_page_config(page_title="S&C FABRIC FINDER", layout="wide")

# --- 설정: 22개 전체 컬럼 리스트 ---
ALL_COLUMNS = [
    "날짜", "브랜드 및 제안처", "스타일 넘버", "업체명", "제품명", "S&C 원단명",
    "혼용률", "원단스펙", "원단 무게", "원단 무게 (BW)", "원단 무게 (기타)",
    "폭(IN)", "제시 폭", "축률 경사", "축률 위사", "원가(YDS)", 
    "RMB(yds)", "RMB(M)", "전달가격", "마진(%)", "재고 및 running", "초반 가격"
]
LABEL_COLUMNS = ["제품명", "S&C 원단명", "원단스펙", "혼용률", "원단 무게", "폭(IN)"]

# --- UI 디자인 (파란색 버튼) ---
st.markdown("""
    <style>
    .stButton>button { background-color: #2e39ff; color: white; border-radius: 5px; font-weight: bold; width: 100%; height: 3.5rem; }
    .stButton>button:hover { background-color: #4a57ff; color: white; border: 1px solid white; }
    div[data-testid="stExpander"] { border: 1px solid #2e39ff; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧵 S&C FABRIC FINDER (Full Feature)")

menu = st.sidebar.radio("메뉴", ["🔍 검색 및 데이터 추출", "📥 엑셀 일괄 업로드", "⚙️ 데이터 관리"])

# --- 기능 1: 검색 및 선택 내보내기 ---
if menu == "🔍 검색 및 데이터 추출":
    st.subheader("📋 원단 조회 및 내보내기")
    
    with st.expander("🔍 검색 필터 열기", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            s_col = st.selectbox("검색 기준", ["전체"] + ALL_COLUMNS)
        with c2:
            s_key = st.text_input("검색어 입력")

    # DB에서 데이터 읽기
    res = supabase.table("fabrics").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # DB에 없는 컬럼이 있을 경우를 대비해 빈 칸으로 생성 (KeyError 방지)
        for col in ALL_COLUMNS:
            if col not in df.columns:
                df[col] = ""
        
        # 필터링
        if s_key:
            if s_col == "전체":
                mask = df[ALL_COLUMNS].astype(str).apply(lambda x: x.str.contains(s_key, case=False)).any(axis=1)
                df = df[mask]
            else:
                df = df[df[s_col].astype(str).str.contains(s_key, case=False)]

        st.write(f"✅ 조회 결과: {len(df)}건 (행을 클릭하여 선택한 후 하단 버튼을 누르세요)")
        
        # [핵심] 행 선택이 가능한 데이터프레임
        selection = st.dataframe(
            df[ALL_COLUMNS],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi_rows"
        )

        # 선택된 데이터 처리
        selected_rows = selection.selection.rows
        if selected_rows:
            export_df = df.iloc[selected_rows]
        else:
            export_df = df # 선택 안 하면 전체 대상

        st.divider()
        st.write(f"📦 **{len(export_df)}개** 항목이 추출 준비되었습니다.")

        btn1, btn2 = st.columns(2)
        with btn1:
            # 1. 전체 데이터 내보내기
            xlsx_all = io.BytesIO()
            export_df[ALL_COLUMNS].to_excel(xlsx_all, index=False, engine='openpyxl')
            st.download_button("📥 선택 항목 전체 엑셀 저장", xlsx_all.getvalue(), 
                               file_name=f"SFF_Data_{datetime.now().strftime('%m%d')}.xlsx")
        with btn2:
            # 2. 라벨용 데이터 내보내기
            xlsx_label = io.BytesIO()
            export_df[LABEL_COLUMNS].to_excel(xlsx_label, index=False, engine='openpyxl')
            st.download_button("🏷️ 라벨(6종) 데이터 추출", xlsx_label.getvalue(), 
                               file_name=f"SFF_Label_{datetime.now().strftime('%m%d')}.xlsx")
    else:
        st.info("DB에 데이터가 없습니다. 먼저 업로드해주세요.")

# --- 기능 2: 엑셀 업로드 ---
elif menu == "📥 엑셀 일괄 업로드":
    st.subheader("📁 엑셀 파일 DB 등록")
    up_file = st.file_uploader("엑셀 파일 선택", type=["xlsx", "xls"])
    if up_file:
        df_up = pd.read_excel(up_file).fillna("").astype(str)
        st.write("미리보기:")
        st.dataframe(df_up.head(3))
        
        if st.button("🚀 서버로 전송 시작"):
            rows = []
            for _, row in df_up.iterrows():
                # DB 컬럼명에 있는 데이터만 골라 담기
                item = {col: row[col] for col in ALL_COLUMNS if col in df_up.columns}
                
                # 자동계산 로직 (제시 폭)
                if "폭(IN)" in item and item["폭(IN)"] and not item.get("제시 폭"):
                    try:
                        w = float(item["폭(IN)"].replace("$",""))
                        item["제시 폭"] = str(int(round(w * 0.92)))
                    except: pass
                rows.append(item)
            
            try:
                for i in range(0, len(rows), 100):
                    supabase.table("fabrics").insert(rows[i:i+100]).execute()
                st.success(f"{len(rows)}건 업로드 완료!")
            except Exception as e:
                st.error(f"오류: {e}")

# --- 기능 3: 데이터 관리 ---
elif menu == "⚙️ 데이터 관리":
    st.subheader("데이터 초기화 및 관리")
    if st.button("🔥 전체 데이터 삭제"):
        if st.checkbox("정말로 초기화하시겠습니까?"):
            supabase.table("fabrics").delete().neq("id", 0).execute()
            st.success("초기화되었습니다.")
