"""설정 상수 — 색상 팔레트 및 컬럼 정의"""
import os
import sys

APP_VERSION = "2.1"

# ── 색상 팔레트 ──────────────────────────────────────────────
COLORS = {
    "PRIMARY_BLUE":        "#2e39ff",
    "DARK_BG":             "#FFFFFF",
    "LIGHTER_DARK_BG":     "#F0F0F0",
    "TEXT_LIGHT":          "#333333",
    "ACCENT_BLUE":         "#6a7bff",
    "BUTTON_HOVER":        "#4a57ff",
    "BUTTON_ACTIVE":       "#1a25d0",
    "TREEVIEW_HEADER_BG":  "#E0E0E0",
    "TREEVIEW_ROW_EVEN":   "#FFFFFF",
    "TREEVIEW_ROW_ODD":    "#F8F8F8",
    "TREEVIEW_SELECTED_BG":"#C0D9FF",
    "TREEVIEW_SELECTED_FG":"#000000",
}

# ── 컬럼 정의 ────────────────────────────────────────────────
COLUMNS = [
    "날짜", "시즌", "브랜드 및 제안처", "담당자", "스타일 넘버",
    "업체명", "제품명", "S&C 원단명",
    "혼용률", "원단스펙", "원단 무게",
    "폭(IN)", "제시 폭", "축률 경사", "축률 위사",
    "원가(YDS)", "RMB(yds)", "RMB(M)",
    "전달가격", "마진(%)",
    "재고 및 running",
]

# DB 컬럼명 ↔ UI 컬럼명 매핑 (key=DB명, value=UI명)
DB_UI_COL_MAP = {
    "원단 무게 (AW)": "원단 무게",
    "공장 가격(YDS)": "원가(YDS)",
    "인민폐(YD)":     "RMB(yds)",
    "인민폐(M)":      "RMB(M)",
    "이득률":         "마진(%)",
    "원단명":         "제품명",
}

# 숫자로 저장할 컬럼 (UI 컬럼명)
NUMERIC_COLS_FOR_STORAGE = [
    "원단 무게", "폭(IN)",
    "축률 경사", "축률 위사", "원가(YDS)",
    "RMB(yds)", "RMB(M)",
    "전달가격", "제시 폭",
]

# 소수점 표시 컬럼
NUMERIC_COLS_FOR_DECIMAL_DISPLAY = [
    "폭(IN)", "축률 경사", "축률 위사",
    "RMB(yds)", "RMB(M)", "원단 무게",
]

# 통화/퍼센트 표시 컬럼
CURRENCY_COLS_DISPLAY = ["원가(YDS)", "전달가격"]
PERCENT_COLS_DISPLAY  = ["마진(%)"]

# 항상 숨길 컬럼
ALWAYS_HIDDEN_COLS = ["축률 경사", "축률 위사"]

# 간략모드 토글 컬럼
COMPACT_MODE_TOGGLE_COLS = ["폭(IN)", "RMB(yds)", "RMB(M)"]

# 남은 공간 채울 컬럼
FLEXIBLE_COLUMN = "S&C 원단명"

# 컬럼별 최대 너비
MAX_COL_WIDTHS = {
    "날짜": 90, "시즌": 55, "담당자": 70, "스타일 넘버": 90,
    "업체명": 80, "원단 무게": 65, "폭(IN)": 60,
    "제시 폭": 60, "축률 경사": 60, "축률 위사": 60,
    "원가(YDS)": 80, "RMB(yds)": 75, "RMB(M)": 75,
    "전달가격": 80, "마진(%)": 85,
}


def get_db_path():
    """패키징 여부에 따라 DB 경로 반환"""
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "fabrics.db")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "fabrics.db")


def get_icon_path():
    """아이콘 경로 반환"""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "SFF.png")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "SFF.png")
