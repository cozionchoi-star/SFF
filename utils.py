"""계산 및 포맷 유틸리티"""
import re
import pandas as pd
import config


def get_db_col_name(ui_col):
    """UI 컬럼명 → DB 컬럼명 변환. 매핑 없으면 그대로 반환."""
    for db_name, ui_name in config.DB_UI_COL_MAP.items():
        if ui_name == ui_col:
            return db_name
    return ui_col


def clean_numeric_string(s):
    """문자열에서 숫자만 추출해 float 반환. 실패 시 None."""
    if s is None or (isinstance(s, float) and pd.isna(s)):
        return None
    s_str = str(s).strip()
    if not s_str:
        return None
    cleaned = re.sub(r"[^\d.\-]+", "", s_str)
    if cleaned.count("-") > 1 or (cleaned.count("-") == 1 and not cleaned.startswith("-")):
        return None
    if cleaned.count(".") > 1 or cleaned in {".", "-"}:
        return None
    try:
        return float(cleaned)
    except ValueError:
        return None


def compute_proposal(width_in_val, raw_prop_val):
    """제시 폭 계산: 명시값 우선, 없으면 폭(IN) × 0.92"""
    val = clean_numeric_string(raw_prop_val)
    if val is not None:
        return val
    w = clean_numeric_string(width_in_val)
    return (w * 0.92) if w is not None else None


def compute_margin(trans_price_val, factory_price_val, raw_margin_val):
    """마진(%) 계산: 명시값 우선, 없으면 (1 - 원가/전달가격) × 100"""
    m = clean_numeric_string(str(raw_margin_val).replace("%", ""))
    if m is not None:
        return m
    t = clean_numeric_string(trans_price_val)
    f = clean_numeric_string(factory_price_val)
    return ((1 - f / t) * 100) if t not in (None, 0) and f is not None else 0.0


def format_for_display(value, column_name):
    """Treeview 표시용 값 포맷"""
    if value is None or (isinstance(value, float) and pd.isna(value)) \
            or (isinstance(value, str) and not value.strip()):
        return ""
    if column_name == "날짜":
        return str(value)
    num = clean_numeric_string(value)
    if num is None:
        return str(value)
    if column_name in config.CURRENCY_COLS_DISPLAY:
        return f"${num:.2f}"
    if column_name in config.PERCENT_COLS_DISPLAY:
        if num < 23:
            return f"⚠️ {num:.2f}%"
        if num > 40:
            return f"✅ {num:.2f}%"
        return f"{num:.2f}%"
    if column_name == "제시 폭":
        return str(int(round(num)))
    if column_name in config.NUMERIC_COLS_FOR_DECIMAL_DISPLAY:
        return f"{num:.2f}"
    return str(value)


def process_df_for_storage(df_db_names):
    """
    DB 컬럼명을 가진 DataFrame을 받아 숫자 변환/계산 수행 후 반환.
    """
    df = df_db_names.copy()

    # None/빈 값 정규화
    for col in df.columns:
        df[col] = df[col].apply(
            lambda x: None if (pd.isna(x) if isinstance(x, float) else False)
                      or (isinstance(x, str) and not x.strip()) else x
        )

    # 날짜
    if "날짜" in df.columns:
        df["날짜"] = df["날짜"].apply(
            lambda x: None if x is None else (
                pd.to_datetime(x, errors="coerce").strftime("%Y-%m-%d")
                if pd.notna(pd.to_datetime(x, errors="coerce")) else None
            )
        )

    # 숫자형 컬럼 정제
    for ui_col in config.NUMERIC_COLS_FOR_STORAGE:
        db_col = get_db_col_name(ui_col)
        if db_col in df.columns:
            df[db_col] = df[db_col].map(clean_numeric_string)

    # 제시 폭 계산
    db_폭_in   = get_db_col_name("폭(IN)")
    db_제시_폭 = get_db_col_name("제시 폭")
    if db_제시_폭 in df.columns and db_폭_in in df.columns:
        df[db_제시_폭] = df.apply(
            lambda r: (
                str(int(round(compute_proposal(r.get(db_폭_in), r.get(db_제시_폭)))))
                if compute_proposal(r.get(db_폭_in), r.get(db_제시_폭)) is not None else None
            ),
            axis=1,
        )

    # 마진(%) 계산
    db_전달가격 = get_db_col_name("전달가격")
    db_원가_yds = get_db_col_name("원가(YDS)")
    db_마진     = get_db_col_name("마진(%)")
    if all(c in df.columns for c in (db_마진, db_전달가격, db_원가_yds)):
        df[db_마진] = df.apply(
            lambda r: (
                f"{compute_margin(r.get(db_전달가격), r.get(db_원가_yds), r.get(db_마진)):.2f}%"
                if (r.get(db_전달가격) is not None and r.get(db_원가_yds) is not None
                    and r.get(db_원가_yds) != 0)
                   or (r.get(db_마진) is not None and str(r.get(db_마진)).strip())
                else None
            ),
            axis=1,
        )

    # 재고 및 running
    if "재고 및 running" in df.columns:
        df["재고 및 running"] = df["재고 및 running"].apply(
            lambda x: None
            if (x is None or (isinstance(x, float) and pd.isna(x))
                or str(x).strip().lower() in ("none", "nan", ""))
            else str(x).strip()
        )

    return df
