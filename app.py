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

# --- UI 스타일 및 설정 ---
st.markdown("""
    <style>
    .stButton>button { background-color: #2e39ff; color: white; border-radius: 5px; width: 100%; }
    .stDataFrame { border: 1px solid #e6e9ef; }
    </style>
    """, unsafe_allow_html=True)

# 원본 컬럼 리스트 (수정/삭제 관리를 위해 ID 포함)
DISPLAY_COLS = [
    "날짜", "브랜드 및 제안처", "스타일 넘버", "업체명", "제품명", "S&C 원단명",
    "혼용률", "원단스펙", "원단 무게", "원단 무게 (BW)", "원단 무게 (기타)",
    "폭(IN)", "제시 폭", "축률 경사", "축률 위사", "원가(YDS)", 
    "RMB(yds)", "RMB(M)", "전달가격", "마진(%)", "재고 및 running", "초반 가격"
]

# --- 핵심 함수: 자동 계산 로직 (기존 py 로직 이식) ---
def auto_calculate(data_dict):
    try:
        # 제시 폭 계산: 폭(IN) * 0.92
        width_in = str(data_dict.get("폭(IN)", "0")).replace("$", "").strip()
        if width_in and float(width_in) > 0 and not data_dict.get("제시 폭"):
            data_dict["제시 폭"] = str(int(round(float(width_in) * 0.92)))
        
        # 마진율 계산: ((전달가격 / 원가) - 1) * 100
        cost = str(data_dict.get("원가(YDS)", "0")).replace("$", "").replace(",", "").strip()
        price = str(data_dict.get("전달가격", "0")).replace("$", "").replace(",", "").strip()
        
        if cost and price and float(cost) > 0:
            margin = ((float(price) / float(cost)) - 1) * 100
            data_dict["마진(%)"] = f"{margin:.2f}%"
    except:
        pass
    return data_dict

st.title("🧵 S&C FABRIC FINDER (Full Version)")

menu = st.sidebar.radio("메뉴 이동", ["🔍 검색 및 내보내기", "📥 데이터 업로드", "⚙️ 데이터 관리"])

# --- 기능 1: 검색 및 선택 내보내기 ---
if menu == "🔍 검색 및 내보내기":
    st.subheader("📋 원단 목록 및 내보내기")
    
    # 검색 영역
    c1, c2 = st.columns([1, 3])
    with c1:
        s_col = st.selectbox("검색 기준", ["전체"] + DISPLAY_COLS)
    with c2:
        s_key = st.text_input("검색어 입력 (입력 시 자동 필터링)")

    # 데이터 가져오기
    res = supabase.table("fabrics").select("*").execute()
    df = pd.DataFrame(res.data)

    if not df.empty:
        df = df.fillna("")
        if s_key:
            if s_col == "전체":
                mask = df.astype(str).apply(lambda x: x.str.contains(s_key, case=False)).any(axis=1)
                df = df[mask]
            else:
                df = df[df[s_col].astype(str).str.contains(s_key, case=False)]

        # [강력 기능] 데이터 선택 모드
        st.write(f"조회 결과: {len(df)}건 (좌측 체크박스로 내보낼 항목을 선택하세요)")
        event = st.dataframe(
            df[DISPLAY_COLS], 
            use_container_width=True, 
            hide_index=True,
            on_select="rerun",
            selection_mode="multi_rows"
        )

        selected_rows = event.selection.rows
        
        # 하단 내보내기 버튼들
        st.write("---")
        btn_c1, btn_c2, btn_c3 = st.columns(3)
        
        # 선택된 데이터 추출
        target_df = df.iloc[selected_rows] if selected_rows else df

        with btn_c1:
            # 1. 엑셀 내보내기
            output = io.BytesIO()
            target_df[DISPLAY_COLS].to_excel(output, index=False, engine='openpyxl')
            st.download_button(
                f"📥 엑셀 내보내기 ({len(target_df)}건)", 
                output.getvalue(), 
                "fabric_export.xlsx",
                help="선택한 항목만 엑셀로 저장합니다. 선택이 없으면 전체를 저장합니다."
            )

        with btn_c2:
            # 2. 라벨용 데이터 내보내기 (기존 py 기능)
            label_cols = ["제품명", "S&C 원단명", "원단스펙", "혼용률", "원단 무게", "폭(IN)"]
            label_output = io.BytesIO()
            target_df[label_cols].to_excel(label_output, index=False, engine='openpyxl')
            st.download_button(
                f"🏷️ 라벨 데이터 추출", 
                label_output.getvalue(), 
                "label_data.xlsx",
                help="라벨(QR) 출력용 6개 핵심 컬럼만 추출합니다."
            )

# --- 기능 2: 데이터 업로드 (ValueError 해결) ---
elif menu == "📥 데이터 업로드":
    st.subheader("📁 대량 엑셀 업로드")
    file = st.file_uploader("엑셀 파일 선택", type=["xlsx", "xls"])
    
    if file:
        df_up = pd.read_excel(file).fillna("").astype(str)
        st.dataframe(df_up.head(3))
        
        if st.button("DB 저장 시작"):
            rows = []
            for _, r in df_up.iterrows():
                # 자동 계산 적용 후 리스트 추가
                row_data = auto_calculate(r.to_dict())
                clean_row = {k: str(v) for k, v in row_data.items() if k in DISPLAY_COLS}
                rows.append(clean_row)
            
            try:
                for i in range(0, len(rows), 50):
                    supabase.table("fabrics").insert(rows[i:i+50]).execute()
                st.success("업로드 완료!")
            except Exception as e:
                st.error(f"오류: {e}")

# --- 기능 3: 데이터 관리 (수정/삭제) ---
elif menu == "⚙️ 데이터 관리":
    st.subheader("🛠️ 데이터 수정 및 삭제")
    res = supabase.table("fabrics").select("*").execute()
    df_manage = pd.DataFrame(res.data)
    
    if not df_manage.empty:
        target_idx = st.selectbox("수정/삭제할 원단 선택", df_manage.index, 
                                  format_func=lambda x: f"{df_manage.loc[x, '제품명']} ({df_manage.loc[x, '스타일 넘버']})")
        
        with st.form("edit_form"):
            selected_data = df_manage.loc[target_idx]
            new_values = {}
            cols = st.columns(3)
            for i, c_name in enumerate(DISPLAY_COLS):
                with cols[i % 3]:
                    new_values[c_name] = st.text_input(c_name, value=str(selected_data[c_name]))
            
            c_btn1, c_btn2 = st.columns(2)
            if c_btn1.form_submit_button("✅ 정보 업데이트"):
                new_values = auto_calculate(new_values)
                supabase.table("fabrics").update(new_values).eq("id", selected_data['id']).execute()
                st.success("수정되었습니다.")
                st.rerun()
            
            if c_btn2.form_submit_button("❌ 데이터 삭제"):
                supabase.table("fabrics").delete().eq("id", selected_data['id']).execute()
                st.warning("삭제되었습니다.")
                st.rerun()
