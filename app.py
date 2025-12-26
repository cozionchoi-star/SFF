import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime
import io

# 1. Supabase 연결 설정 (Streamlit Secrets 사용 권장)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.set_page_config(page_title="S&C 원단 정보 파인더", layout="wide")

# --- CSS: 버튼 색상 커스텀 (요청하신 파란색 반영) ---
st.markdown("""
    <style>
    .stButton>button { background-color: #2e39ff; color: white; border-radius: 5px; }
    .stButton>button:hover { background-color: #4a57ff; color: white; }
    </style>
    """, unsafe_allow_html=True)

st.title("🧵 S&C 원단 정보 파인더 (Cloud)")

# --- 메뉴 선택 ---
menu = st.sidebar.selectbox("메뉴 선택", ["🔍 원단 검색", "➕ 새 원단 등록", "📥 엑셀 업로드", "⚙️ 데이터 관리"])

# --- 기능 1: 원단 검색 ---
if menu == "🔍 원단 검색":
    st.subheader("원단 검색 및 조회")
    
    col1, col2 = st.columns([1, 3])
    with col1:
        search_col = st.selectbox("검색 기준", ["전체", "item_name", "spec", "composition", "color", "supplier"])
    with col2:
        keyword = st.text_input("검색어 입력")

    # 데이터 가져오기
    response = supabase.table("fabrics").select("*").execute()
    df = pd.DataFrame(response.data)

    if not df.empty:
        if keyword:
            if search_col == "전체":
                mask = df.astype(str).apply(lambda x: x.str.contains(keyword, case=False)).any(axis=1)
                df = df[mask]
            else:
                df = df[df[search_col].astype(str).str.contains(keyword, case=False)]
        
        st.write(f"검색 결과: {len(df)}건")
        st.dataframe(df, use_container_width=True)
        
        # 엑셀 다운로드
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False, engine='openpyxl')
        st.download_button(label="📥 현재 결과 엑셀 다운로드", data=towrite.getvalue(), file_name="search_results.xlsx")
    else:
        st.info("등록된 데이터가 없습니다.")

# --- 기능 2: 새 원단 등록 ---
elif menu == "➕ 새 원단 등록":
    st.subheader("새로운 원단 정보 입력")
    with st.form("add_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            item_name = st.text_input("품명")
            spec = st.text_input("규격")
            composition = st.text_input("조직")
            color = st.text_input("색상")
        with c2:
            supplier = st.text_input("거래처")
            price = st.text_input("가격")
            remark = st.text_area("비고")
        
        if st.form_submit_button("등록하기"):
            new_data = {
                "reg_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "item_name": item_name,
                "spec": spec,
                "composition": composition,
                "color": color,
                "supplier": supplier,
                "price": price,
                "remark": remark,
                "update_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            supabase.table("fabrics").insert(new_data).execute()
            st.success("등록 완료!")

# --- 기능 3: 엑셀 업로드 (대량 등록) ---
elif menu == "📥 엑셀 업로드":
    st.subheader("엑셀 파일로 한꺼번에 등록")
    uploaded_file = st.file_uploader("엑셀 파일을 선택하세요", type=["xlsx", "xls"])
    if uploaded_file:
        df_upload = pd.read_excel(uploaded_file)
        if st.button("DB에 저장하기"):
            data_dict = df_upload.to_dict(orient='records')
            supabase.table("fabrics").insert(data_dict).execute()
            st.success(f"{len(data_dict)}건의 데이터가 성공적으로 저장되었습니다.")

# --- 기능 4: 데이터 관리 (삭제 및 수정) ---
elif menu == "⚙️ 데이터 관리":
    st.subheader("데이터 삭제 및 관리")
    response = supabase.table("fabrics").select("*").execute()
    df = pd.DataFrame(response.data)
    
    if not df.empty:
        selected_id = st.selectbox("삭제할 데이터 ID 선택", df['id'].tolist())
        if st.button("선택한 데이터 삭제", help="복구가 불가능하니 주의하세요!"):
            supabase.table("fabrics").delete().eq("id", selected_id).execute()
            st.success(f"ID {selected_id} 데이터가 삭제되었습니다.")
            st.rerun()
