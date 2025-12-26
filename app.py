import streamlit as st
import pandas as pd
from supabase import create_client, Client
import io
from datetime import datetime

# 1. Supabase 연결
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except:
    st.error("Secrets 설정을 확인해주세요.")
    st.stop()

st.set_page_config(page_title="S&C FABRIC FINDER", layout="wide")

# --- 기존 프로그램 기반 전체 컬럼 (22개) ---
DISPLAY_COLS = [
    "날짜", "브랜드 및 제안처", "스타일 넘버", "업체명", "제품명", "S&C 원단명",
    "혼용률", "원단스펙", "원단 무게", "원단 무게 (BW)", "원단 무게 (기타)",
    "폭(IN)", "제시 폭", "축률 경사", "축률 위사", "원가(YDS)", 
    "RMB(yds)", "RMB(M)", "전달가격", "마진(%)", "재고 및 running", "초반 가격"
]
# 라벨용 6종 컬럼
LABEL_COLS = ["제품명", "S&C 원단명", "원단스펙", "혼용률", "원단 무게", "폭(IN)"]

# --- UI 스타일 (버튼 색상 등) ---
st.markdown("""
    <style>
    .stButton>button { background-color: #2e39ff; color: white; border-radius: 5px; font-weight: bold; width: 100%; height: 3.5rem; }
    .stButton>button:hover { background-color: #4a57ff; color: white; border: 1px solid white; }
    div[data-testid="stExpander"] { border: 1px solid #2e39ff; border-radius: 8px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧵 S&C FABRIC FINDER (Full Feature)")

menu = st.sidebar.radio("📋 메뉴 이동", ["🔍 조회 및 데이터 추출", "📥 엑셀 일괄 업로드", "⚙️ 데이터 관리"])

# --- 기능 1: 조회 및 선택 내보내기 ---
if menu == "🔍 조회 및 데이터 추출":
    st.subheader("원단 정보 검색 및 선택 추출")
    
    with st.expander("🔍 검색 필터", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            s_target = st.selectbox("검색 기준", ["전체"] + DISPLAY_COLS)
        with c2:
            s_key = st.text_input("검색어 입력")

    # DB 데이터 호출
    res = supabase.table("fabrics").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        # DB 컬럼 누락 방지 (KeyError 대책)
        for c in DISPLAY_COLS:
            if c not in df.columns: df[c] = ""
            
        # 검색 필터링
        if s_key:
            if s_target == "전체":
                mask = df[DISPLAY_COLS].astype(str).apply(lambda x: x.str.contains(s_key, case=False)).any(axis=1)
                df = df[mask]
            else:
                df = df[df[s_target].astype(str).str.contains(s_key, case=False)]

        st.write(f"✅ 조회 결과: {len(df)}건 (좌측 체크박스로 내보낼 항목을 선택하세요)")
        
        # [수정 포인트] selection_mode="multi-row"로 수정 (에러 해결)
        selection = st.dataframe(
            df[DISPLAY_COLS],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row"
        )

        # 선택된 행 추출
        selected_rows = selection.selection.rows
        export_df = df.iloc[selected_rows] if selected_rows else df

        st.divider()
        st.write(f"📦 **{len(export_df)}개** 항목이 추출 대기 중입니다.")

        btn1, btn2 = st.columns(2)
        with btn1:
            xlsx_all = io.BytesIO()
            export_df[DISPLAY_COLS].to_excel(xlsx_all, index=False, engine='openpyxl')
            st.download_button(label="📥 선택 항목 전체 엑셀 저장", data=xlsx_all.getvalue(), 
                               file_name=f"SFF_Full_{datetime.now().strftime('%m%d')}.xlsx")
        with btn2:
            xlsx_label = io.BytesIO()
            # 라벨 컬럼 존재 확인 후 추출
            l_cols = [c for c in LABEL_COLS if c in export_df.columns]
            export_df[l_cols].to_excel(xlsx_label, index=False, engine='openpyxl')
            st.download_button(label="🏷️ 라벨용(6종) 데이터 추출", data=xlsx_label.getvalue(), 
                               file_name=f"SFF_Label_{datetime.now().strftime('%m%d')}.xlsx")
    else:
        st.info("DB에 데이터가 없습니다.")

# --- 기능 2: 엑셀 데이터 업로드 ---
elif menu == "📥 엑셀 일괄 업로드":
    st.subheader("📁 엑셀 업로드 (ValueError 해결 버전)")
    up_file = st.file_uploader("엑셀 파일 선택", type=["xlsx", "xls"])
    
    if up_file:
        df_up = pd.read_excel(up_file).fillna("").astype(str)
        st.dataframe(df_up.head(3))
        
        if st.button("서버에 저장"):
            rows = []
            for _, r in df_up.iterrows():
                item = {col: r[col] for col in DISPLAY_COLS if col in df_up.columns}
                
                # 자동 계산 (제시 폭)
                if item.get("폭(IN)") and not item.get("제시 폭"):
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
    st.subheader("데이터 초기화")
    if st.button("🔥 전체 삭제"):
        if st.checkbox("정말로 삭제하시겠습니까?"):
            supabase.table("fabrics").delete().neq("id", 0).execute()
            st.success("삭제되었습니다.")
