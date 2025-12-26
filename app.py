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
    st.error("Secrets 설정(URL, KEY)을 확인해주세요.")
    st.stop()

st.set_page_config(page_title="S&C FABRIC FINDER", layout="wide")

# --- 기존 프로그램 기반 컬럼 설정 ---
ALL_COLUMNS = [
    "날짜", "브랜드 및 제안처", "스타일 넘버", "업체명", "제품명", 
    "S&C 원단명", "혼용률", "원단스펙", "원단 무게", "폭(IN)", 
    "제시 폭", "원가(YDS)", "RMB(yds)", "RMB(M)", "전달가격", 
    "마진(%)", "재고 및 running"
]

LABEL_COLUMNS = ["제품명", "S&C 원단명", "원단스펙", "혼용률", "원단 무게", "폭(IN)"]

# --- CSS: 파란색 버튼 및 UI 재현 ---
st.markdown("""
    <style>
    .stButton>button { background-color: #2e39ff; color: white; border-radius: 5px; font-weight: bold; width: 100%; height: 3rem; }
    .stButton>button:hover { background-color: #4a57ff; color: white; border: 1px solid white; }
    div[data-testid="stExpander"] { border: 1px solid #2e39ff; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧵 S&C FABRIC FINDER (Web v3)")

# 사이드바 메뉴
menu = st.sidebar.radio("📋 메뉴 선택", ["🔍 조회 및 내보내기", "📥 데이터 업로드", "⚙️ 데이터 관리"])

# --- 기능 1: 조회 및 선택 내보내기 ---
if menu == "🔍 조회 및 내보내기":
    st.subheader("원단 정보 검색")
    
    with st.expander("🔍 검색 필터", expanded=True):
        c1, c2 = st.columns([1, 2])
        with c1:
            s_target = st.selectbox("검색 기준", ["전체"] + ALL_COLUMNS)
        with c2:
            s_key = st.text_input("검색어 입력")

    # 데이터 로드
    res = supabase.table("fabrics").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        df = df.fillna("")
        # 검색 필터링
        if s_key:
            if s_target == "전체":
                mask = df[ALL_COLUMNS].astype(str).apply(lambda x: x.str.contains(s_key, case=False)).any(axis=1)
                df = df[mask]
            else:
                df = df[df[s_target].astype(str).str.contains(s_key, case=False)]

        st.write(f"✅ 조회 결과: {len(df)}건 (좌측 체크박스로 내보낼 항목을 선택하세요)")
        
        # [핵심] 선택 기능이 포함된 데이터프레임
        selection = st.dataframe(
            df[ALL_COLUMNS],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi_rows"
        )

        # 선택된 행 데이터 추출
        selected_indices = selection.selection.rows
        if selected_indices:
            export_df = df.iloc[selected_indices]
        else:
            export_df = df # 선택 없으면 전체

        st.divider()
        st.write(f"📦 현재 {len(export_df)}개 항목이 내보내기 대상으로 준비되었습니다.")

        # 내보내기 버튼 배치
        btn1, btn2 = st.columns(2)
        
        with btn1:
            # 1. 전체 데이터 내보내기
            xlsx_all = io.BytesIO()
            export_df[ALL_COLUMNS].to_excel(xlsx_all, index=False, engine='openpyxl')
            st.download_button(
                label="📥 선택 항목 전체 엑셀 저장",
                data=xlsx_all.getvalue(),
                file_name=f"SFF_Full_{datetime.now().strftime('%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        with btn2:
            # 2. 라벨 데이터 내보내기
            xlsx_label = io.BytesIO()
            export_df[LABEL_COLUMNS].to_excel(xlsx_label, index=False, engine='openpyxl')
            st.download_button(
                label="🏷️ 라벨용(6종) 데이터 추출",
                data=xlsx_label.getvalue(),
                file_name=f"SFF_Label_{datetime.now().strftime('%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    else:
        st.info("DB에 데이터가 없습니다. 업로드를 먼저 진행해주세요.")

# --- 기능 2: 데이터 업로드 (ValueError 해결) ---
elif menu == "📥 데이터 업로드":
    st.subheader("엑셀 파일 일괄 등록")
    st.info("엑셀의 컬럼명이 '제품명', '원단명' 등과 일치해야 합니다.")
    
    up_file = st.file_uploader("엑셀 파일 선택", type=["xlsx", "xls"])
    
    if up_file:
        df_raw = pd.read_excel(up_file)
        
        # [에러 방지] 1. NaN 제거 2. 모든 데이터를 문자열로 강제 변환
        df_clean = df_raw.fillna("").astype(str)
        
        st.write("미리보기 (상위 3건):")
        st.dataframe(df_clean.head(3))

        if st.button("서버로 데이터 전송 시작"):
            # DB 컬럼에 맞는 데이터만 추출
            data_to_send = []
            for _, row in df_clean.iterrows():
                item = {col: row[col] for col in ALL_COLUMNS if col in df_clean.columns}
                
                # 기존 py의 자동계산 로직 재현 (제시 폭)
                if item.get("폭(IN)") and not item.get("제시 폭"):
                    try:
                        w = float(item["폭(IN)"].replace("$",""))
                        item["제시 폭"] = str(int(round(w * 0.92)))
                    except: pass
                data_to_send.append(item)

            try:
                # 100개씩 끊어서 안정적으로 업로드
                for i in range(0, len(data_to_send), 100):
                    supabase.table("fabrics").insert(data_to_send[i:i+100]).execute()
                st.success(f"🚀 {len(data_to_send)}건 업로드 완료!")
            except Exception as e:
                st.error(f"전송 중 오류 발생: {e}")

# --- 기능 3: 데이터 관리 ---
elif menu == "⚙️ 데이터 관리":
    st.subheader("데이터베이스 초기화")
    st.warning("이 작업은 복구할 수 없습니다.")
    if st.button("🔥 전체 데이터 삭제"):
        if st.checkbox("정말로 삭제하시겠습니까?"):
            supabase.table("fabrics").delete().neq("id", 0).execute()
            st.success("데이터가 초기화되었습니다.")
