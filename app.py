import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io
import json

# 1. Supabase 연결
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase: Client = create_client(url, key)
except Exception as e:
    st.error("Secrets 설정(URL, KEY)을 확인해주세요.")
    st.stop()

st.set_page_config(page_title="S&C FABRIC FINDER", layout="wide")

# --- UI 스타일 설정 (EXE 느낌 재현) ---
st.markdown("""
    <style>
    .main { background-color: #FFFFFF; }
    .stButton>button { background-color: #2e39ff; color: white; width: 100%; border-radius: 5px; height: 3em; }
    .stButton>button:hover { background-color: #4a57ff; color: white; }
    div[data-testid="stExpander"] { border: 1px solid #2e39ff; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧵 S&C FABRIC FINDER (Web Version)")

# --- 사이드바 메뉴 ---
menu = st.sidebar.radio("메뉴 이동", ["🔍 원단 검색 및 조회", "➕ 개별 데이터 등록", "📥 대량 엑셀 업로드", "⚙️ 데이터 관리/수정"])

# --- 공통 함수: 데이터 불러오기 ---
def fetch_all_data():
    res = supabase.table("fabrics").select("*").order("id", desc=True).execute()
    return pd.DataFrame(res.data)

# --- 기능 1: 검색 및 조회 (기존 UI 느낌) ---
if menu == "🔍 원단 검색 및 조회":
    st.subheader("📋 전체 원단 목록")
    
    # 검색 영역
    with st.expander("🔍 검색 필터 열기", expanded=True):
        c1, c2 = st.columns([1, 3])
        with c1:
            search_col = st.selectbox("검색 기준", ["전체", "품명", "규격", "조직", "색상", "거래처", "비고"])
        with c2:
            keyword = st.text_input("검색어를 입력하고 엔터를 누르세요", placeholder="예: 면 100%...")

    df = fetch_all_data()

    if not df.empty:
        # 필터링 로직
        if keyword:
            if search_col == "전체":
                mask = df.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)
                display_df = df[mask]
            else:
                display_df = df[df[search_col].astype(str).str.contains(keyword, case=False)]
        else:
            display_df = df

        st.write(f"조회된 데이터: {len(display_df)} 건")
        
        # 테이블 표시 (기존 Treeview 느낌)
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # 엑셀 다운로드 (기존 추출 기능)
        towrite = io.BytesIO()
        display_df.to_excel(towrite, index=False, engine='openpyxl')
        st.download_button(label="📥 현재 결과 엑셀로 추출", data=towrite.getvalue(), file_name=f"fabric_search_{datetime.now().strftime('%Y%m%d')}.xlsx")
    else:
        st.info("데이터베이스에 등록된 정보가 없습니다.")

# --- 기능 2: 개별 등록 ---
elif menu == "➕ 개별 데이터 등록":
    st.subheader("🆕 신규 원단 정보 입력")
    with st.form("entry_form"):
        c1, c2 = st.columns(2)
        with c1:
            item_name = st.text_input("품명")
            spec = st.text_input("규격")
            org = st.text_input("조직")
            color = st.text_input("색상")
        with c2:
            vendor = st.text_input("거래처")
            price = st.text_input("단가")
            remark = st.text_area("비고")
        
        if st.form_submit_button("DB에 등록하기"):
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data = {
                "등록일자": now, "품명": item_name, "규격": spec, "조직": org,
                "색상": color, "거래처": vendor, "단가": price, "비고": remark, "수정일자": now
            }
            supabase.table("fabrics").insert(data).execute()
            st.success("새 데이터가 성공적으로 등록되었습니다!")

# --- 기능 3: 엑셀 업로드 (오류 수정됨) ---
elif menu == "📥 대량 엑셀 업로드":
    st.subheader("📁 엑셀 파일 한꺼번에 올리기")
    st.info("팁: 기존 엑셀의 컬럼명(품명, 규격, 조직 등)이 정확해야 합니다.")
    
    uploaded_file = st.file_uploader("엑셀 파일 선택", type=["xlsx", "xls"])
    
    if uploaded_file:
        df_up = pd.read_excel(uploaded_file)
        
        # 핵심 해결책: NaN(빈 칸)을 빈 문자열로 변환하고 모든 데이터를 문자열화함
        df_up = df_up.fillna("") 
        
        st.write("미리보기 (상위 5건):")
        st.table(df_up.head())
        
        if st.button("서버로 전송 시작"):
            # Pandas 데이터를 Supabase가 이해할 수 있는 JSON 리스트로 변환
            items = df_up.to_dict(orient='records')
            
            # 현재 시간 추가
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for item in items:
                if "등록일자" not in item or not item["등록일자"]:
                    item["등록일자"] = now
                item["수정일자"] = now

            try:
                supabase.table("fabrics").insert(items).execute()
                st.success(f"총 {len(items)}건의 데이터가 성공적으로 업로드되었습니다!")
            except Exception as e:
                st.error(f"업로드 중 오류 발생: {e}")

# --- 기능 4: 데이터 수정 및 삭제 ---
elif menu == "⚙️ 데이터 관리/수정":
    st.subheader("🛠️ 기존 데이터 수정 및 삭제")
    df_edit = fetch_all_data()
    
    if not df_edit.empty:
        selected_item = st.selectbox("수정/삭제할 항목 선택 (품명 기준)", df_edit["품명"].tolist())
        row = df_edit[df_edit["품명"] == selected_item].iloc[0]
        
        with st.form("edit_form"):
            u_id = row['id']
            st.write(f"데이터 번호: {u_id}")
            e_item = st.text_input("품명", value=row["품명"])
            e_spec = st.text_input("규격", value=row["규격"])
            e_org = st.text_input("조직", value=row["조직"])
            e_color = st.text_input("색상", value=row["색상"])
            e_vendor = st.text_input("거래처", value=row["거래처"])
            e_price = st.text_input("단가", value=row["단가"])
            e_remark = st.text_area("비고", value=row["비고"])
            
            col_b1, col_b2 = st.columns(2)
            if col_b1.form_submit_button("✅ 정보 수정"):
                updated_data = {
                    "품명": e_item, "규격": e_spec, "조직": e_org, "색상": e_color,
                    "거래처": e_vendor, "단가": e_price, "비고": e_remark,
                    "수정일자": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                supabase.table("fabrics").update(updated_data).eq("id", u_id).execute()
                st.success("수정되었습니다.")
                st.rerun()
                
            if col_b2.form_submit_button("❌ 데이터 삭제"):
                supabase.table("fabrics").delete().eq("id", u_id).execute()
                st.warning("삭제되었습니다.")
                st.rerun()
