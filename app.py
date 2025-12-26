import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import re

# 1. Supabase 연결
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Secrets 설정을 확인해주세요.")
    st.stop()

st.set_page_config(page_title="S&C FABRIC FINDER", layout="wide")

# --- 설정 상수 (EXE 파일과 동일) ---
UI_COLUMNS = [
    "날짜", "브랜드 및 제안처", "스타일 넘버", "업체명", "제품명", "S&C 원단명",
    "혼용률", "원단스펙", "원단 무게", "원단 무게 (BW)", "원단 무게 (기타)",
    "폭(IN)", "제시 폭", "축률 경사", "축률 위사", "원가(YDS)", 
    "RMB(yds)", "RMB(M)", "전달가격", "마진(%)", "재고 및 running", "초반 가격"
]

# DB 컬럼명 <-> UI 컬럼명 매핑
DB_UI_MAP = {
    "원단명": "제품명",
    "원단 무게 (AW)": "원단 무게",
    "공장 가격(YDS)": "원가(YDS)",
    "인민폐(YD)": "RMB(yds)",
    "인민폐(M)": "RMB(M)",
    "이득률": "마진(%)"
}
REVERSE_MAP = {v: k for k, v in DB_UI_MAP.items()}

# --- 공통 함수 ---
def clean_numeric(val):
    if pd.isna(val) or val == "": return 0.0
    cleaned = re.sub(r'[^\d.\-]+', '', str(val))
    try: return float(cleaned)
    except: return 0.0

def calculate_values(row):
    # 제시 폭 계산: 폭(IN) * 0.92
    width_in = clean_numeric(row.get("폭(IN)", 0))
    if not row.get("제시 폭"):
        row["제시 폭"] = str(int(round(width_in * 0.92))) if width_in > 0 else ""
    
    # 마진율 계산: ((전달가격 / 원가 - 1) * 100)
    cost = clean_numeric(row.get("원가(YDS)", 0))
    price = clean_numeric(row.get("전달가격", 0))
    if cost > 0 and not row.get("마진(%)"):
        row["마진(%)"] = f"{((price / cost) - 1) * 100:.2f}%"
    return row

# --- UI 스타일 ---
st.markdown("""
    <style>
    .stButton>button { background-color: #2e39ff; color: white; border-radius: 5px; }
    .stDataFrame { border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧵 S&C FABRIC FINDER (Web)")

menu = st.sidebar.radio("메뉴", ["🔍 검색 및 조회", "➕ 단일 등록", "📥 엑셀 업로드", "⚙️ 데이터 관리"])

# --- 기능 1: 검색 및 조회 ---
if menu == "🔍 검색 및 조회":
    st.subheader("원단 정보 검색")
    col1, col2 = st.columns([1, 3])
    with col1:
        s_target = st.selectbox("검색 기준", ["전체"] + UI_COLUMNS)
    with col2:
        s_key = st.text_input("검색어 입력")

    res = supabase.table("fabrics").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # DB 컬럼명을 UI 명칭으로 변경
        df = df.rename(columns=DB_UI_MAP)
        # 컬럼 순서 재정렬
        df = df[UI_COLUMNS + ["id"]]
        
        if s_key:
            if s_target == "전체":
                mask = df.astype(str).apply(lambda x: x.str.contains(s_key, case=False)).any(axis=1)
                df = df[mask]
            else:
                df = df[df[s_target].astype(str).str.contains(s_key, case=False)]
        
        st.write(f"검색 결과: {len(df)}건")
        st.dataframe(df.drop(columns=['id']), use_container_width=True)
        
        # 엑셀 다운로드
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        st.download_button("📥 결과 엑셀 저장", output.getvalue(), "search_result.xlsx")

# --- 기능 2: 단일 등록 ---
elif menu == "➕ 단일 등록":
    st.subheader("신규 원단 등록")
    with st.form("add_form"):
        data = {}
        cols = st.columns(3)
        for i, col_name in enumerate(UI_COLUMNS):
            with cols[i % 3]:
                if col_name == "날짜":
                    data[col_name] = st.text_input(col_name, datetime.now().strftime("%Y-%m-%d"))
                else:
                    data[col_name] = st.text_input(col_name)
        
        if st.form_submit_button("저장하기"):
            data = calculate_values(data)
            # DB 컬럼명으로 변환하여 저장
            db_data = {REVERSE_MAP.get(k, k): v for k, v in data.items()}
            supabase.table("fabrics").insert(db_data).execute()
            st.success("등록 완료!")

# --- 기능 3: 엑셀 업로드 (에러 수정판) ---
elif menu == "📥 엑셀 업로드":
    st.subheader("대량 엑셀 업로드")
    st.warning("엑셀의 컬럼명이 프로그램의 컬럼명과 일치해야 합니다.")
    
    file = st.file_uploader("파일 선택", type=["xlsx", "xls"])
    if file:
        df_up = pd.read_excel(file)
        # 핵심 해결책: NaN 처리 및 전체 문자열화 (JSON 에러 방지)
        df_up = df_up.fillna("").astype(str)
        
        if st.button("DB로 전송"):
            items = []
            for _, row in df_up.iterrows():
                row_dict = row.to_dict()
                row_dict = calculate_values(row_dict)
                # 매핑 적용
                final_row = {REVERSE_MAP.get(k, k): v for k, v in row_dict.items() if k in UI_COLUMNS}
                items.append(final_row)
            
            try:
                # 50개씩 끊어서 업로드 (안정성)
                for i in range(0, len(items), 50):
                    supabase.table("fabrics").insert(items[i:i+50]).execute()
                st.success(f"{len(items)}건 업로드 성공!")
            except Exception as e:
                st.error(f"오류 발생: {e}")

# --- 기능 4: 데이터 관리 ---
elif menu == "⚙️ 데이터 관리":
    st.subheader("데이터 수정 및 삭제")
    res = supabase.table("fabrics").select("id, 원단명, 스타일 넘버").execute()
    df_list = pd.DataFrame(res.data)
    
    if not df_list.empty:
        target = st.selectbox("항목 선택", df_list.apply(lambda x: f"ID:{x['id']} | {x['원단명']} ({x['스타일 넘버']})", axis=1))
        t_id = target.split("|")[0].split(":")[1].strip()
        
        if st.button("🗑️ 선택 항목 삭제"):
            supabase.table("fabrics").delete().eq("id", t_id).execute()
            st.warning("삭제되었습니다.")
            st.rerun()
