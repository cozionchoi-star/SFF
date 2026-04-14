"""DB 접근 전담 모듈"""
import sqlite3
import os
import shutil
import pandas as pd
from datetime import datetime
import config
import utils


def _conn(db_path):
    return sqlite3.connect(db_path)


def init_db(db_path):
    """테이블 생성 및 마이그레이션"""
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    # fabrics 테이블 먼저 보장
    create_fabrics_table(db_path)
    with _conn(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proposals (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                fabric_rowid INTEGER,
                날짜          TEXT,
                브랜드         TEXT,
                시즌           TEXT,
                전달가격        TEXT,
                담당자         TEXT,
                제안결과        TEXT,
                메모           TEXT
            )
        """)
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(fabrics)")
        existing = [r[1] for r in cur.fetchall()]
        for col in ("담당자", "시즌", "채택여부", "메모"):
            if col not in existing:
                cur.execute(f'ALTER TABLE fabrics ADD COLUMN "{col}" TEXT DEFAULT ""')
        conn.commit()


def load_fabrics(db_path):
    """
    DB에서 전체 원단 로드 → UI 컬럼명 DataFrame 반환.
    DB 없으면 빈 DataFrame 반환.
    """
    if not os.path.exists(db_path):
        return pd.DataFrame(columns=["_rowid"] + config.COLUMNS)

    with _conn(db_path) as conn:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(fabrics)")
        cols_info = cur.fetchall()
        existing = [c[1] for c in cols_info]

        # 구버전 컬럼명 마이그레이션 (원단 번호 → 스타일 넘버)
        old = utils.get_db_col_name("원단 번호")
        new = utils.get_db_col_name("스타일 넘버")
        if old in existing and new not in existing:
            try:
                cur.execute(f'ALTER TABLE fabrics RENAME COLUMN "{old}" TO "{new}"')
                conn.commit()
            except sqlite3.OperationalError:
                pass

        try:
            df = pd.read_sql("SELECT rowid AS _rowid, * FROM fabrics", conn)
        except Exception:
            return pd.DataFrame(columns=["_rowid"] + config.COLUMNS)

    # DB명 → UI명 변환
    df.rename(columns=config.DB_UI_COL_MAP, inplace=True)
    df = df.reindex(columns=["_rowid"] + config.COLUMNS, fill_value=None)
    df["_rowid"] = df["_rowid"].astype(int)

    # 데이터 정제/재계산
    reverse_map = {v: k for k, v in config.DB_UI_COL_MAP.items()}
    db_cols = [utils.get_db_col_name(c) for c in config.COLUMNS]
    tmp = df.copy()
    tmp.rename(columns=reverse_map, inplace=True)
    tmp = tmp.reindex(columns=["_rowid"] + db_cols, fill_value=None)
    processed = utils.process_df_for_storage(tmp)
    processed.rename(columns=config.DB_UI_COL_MAP, inplace=True)
    df = processed.reindex(columns=["_rowid"] + config.COLUMNS, fill_value=None)

    return df


def create_fabrics_table(db_path):
    """fabrics 테이블 없을 때 생성"""
    db_cols = [utils.get_db_col_name(c) for c in config.COLUMNS]
    cols_sql = ", ".join(f'"{c}" TEXT' for c in db_cols)
    with _conn(db_path) as conn:
        conn.execute(f"CREATE TABLE IF NOT EXISTS fabrics ({cols_sql})")
        conn.commit()


def save_fabric(db_path, ui_data_dict, row_id=None):
    """단일 원단 저장 (추가 or 수정). ui_data_dict = {UI컬럼명: 값}"""
    db_data = {utils.get_db_col_name(k): v for k, v in ui_data_dict.items()}
    tmp = pd.DataFrame([db_data])
    proc = utils.process_df_for_storage(tmp)
    db_cols = [utils.get_db_col_name(c) for c in config.COLUMNS]
    vals = [proc.iloc[0].get(c) for c in db_cols]

    with _conn(db_path) as conn:
        cur = conn.cursor()
        if row_id:
            clause = ", ".join(f'"{c}"=?' for c in db_cols)
            cur.execute(f"UPDATE fabrics SET {clause} WHERE rowid=?", (*vals, int(row_id)))
        else:
            cols_sql = ", ".join(f'"{c}"' for c in db_cols)
            ph = ", ".join("?" for _ in db_cols)
            cur.execute(f"INSERT INTO fabrics ({cols_sql}) VALUES ({ph})", vals)
        conn.commit()


def delete_fabric(db_path, row_id):
    with _conn(db_path) as conn:
        conn.execute("DELETE FROM fabrics WHERE rowid=?", (int(row_id),))
        conn.commit()


def import_fabrics(db_path, proc_df, proposal_data=None):
    """
    이미 처리된 DB컬럼명 DataFrame을 bulk insert.
    proposal_data: {"시즌": [...], "담당자": [...], ...}
    """
    db_cols = [utils.get_db_col_name(c) for c in config.COLUMNS]
    create_fabrics_table(db_path)
    proc_df = proc_df.reindex(columns=db_cols)

    with _conn(db_path) as conn:
        cur = conn.cursor()
        cols_sql = ", ".join(f'"{c}"' for c in db_cols)
        ph = ", ".join("?" for _ in db_cols)
        inserted_rowids = []
        for _, row in proc_df.iterrows():
            cur.execute(f"INSERT INTO fabrics ({cols_sql}) VALUES ({ph})", list(row))
            inserted_rowids.append(cur.lastrowid)

        if proposal_data:
            db_brand = utils.get_db_col_name("브랜드 및 제안처")
            for i, rowid in enumerate(inserted_rowids):
                row_brand  = proc_df.iloc[i].get(db_brand, "") or ""
                row_date   = proc_df.iloc[i].get("날짜", "") or ""
                시즌    = (proposal_data.get("시즌",     [""] * len(inserted_rowids))[i] or "")
                전달가격 = str(proc_df.iloc[i].get(utils.get_db_col_name("전달가격"), "") or "")
                담당자  = (proposal_data.get("담당자",   [""] * len(inserted_rowids))[i] or "")
                제안결과 = (proposal_data.get("제안결과", [""] * len(inserted_rowids))[i] or "")
                메모    = (proposal_data.get("메모",     [""] * len(inserted_rowids))[i] or "")
                if any([시즌, 담당자, 제안결과, 메모, row_brand]):
                    cur.execute(
                        "INSERT INTO proposals (fabric_rowid, 날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                        (rowid, row_date, row_brand, 시즌, 전달가격, 담당자, 제안결과, 메모),
                    )
        conn.commit()
    return len(inserted_rowids)


def get_proposals(db_path, fabric_rowid):
    with _conn(db_path) as conn:
        rows = conn.execute(
            "SELECT id, 날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모 "
            "FROM proposals WHERE fabric_rowid=? ORDER BY 날짜 DESC",
            (fabric_rowid,),
        ).fetchall()
    return rows


def get_proposal(db_path, proposal_id):
    with _conn(db_path) as conn:
        return conn.execute(
            "SELECT 날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모 FROM proposals WHERE id=?",
            (proposal_id,),
        ).fetchone()


def save_proposal(db_path, fabric_rowid, vals_dict, proposal_id=None):
    fields = ["날짜", "브랜드", "시즌", "전달가격", "담당자", "제안결과", "메모"]
    vals = [vals_dict[f] for f in fields]
    with _conn(db_path) as conn:
        if proposal_id:
            conn.execute(
                "UPDATE proposals SET 날짜=?, 브랜드=?, 시즌=?, 전달가격=?, 담당자=?, 제안결과=?, 메모=? WHERE id=?",
                (*vals, proposal_id),
            )
        else:
            conn.execute(
                "INSERT INTO proposals (fabric_rowid, 날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (fabric_rowid, *vals),
            )
        conn.commit()


def delete_proposal(db_path, proposal_id):
    with _conn(db_path) as conn:
        conn.execute("DELETE FROM proposals WHERE id=?", (proposal_id,))
        conn.commit()


def toggle_adoption(db_path, row_ids):
    """row_ids 리스트의 채택 여부 토글"""
    with _conn(db_path) as conn:
        cur = conn.cursor()
        for rid in row_ids:
            cur.execute("SELECT 채택여부 FROM fabrics WHERE rowid=?", (rid,))
            row = cur.fetchone()
            current = row[0] if row and row[0] else ""
            new_val = "" if current == "채택" else "채택"
            cur.execute("UPDATE fabrics SET 채택여부=? WHERE rowid=?", (new_val, rid))
        conn.commit()


def get_adopted_rowids(db_path):
    try:
        with _conn(db_path) as conn:
            rows = conn.execute('SELECT rowid FROM fabrics WHERE 채택여부="채택"').fetchall()
        return {r[0] for r in rows}
    except Exception:
        return set()


def get_adoption_filter_lists(db_path):
    """시즌 채택 현황 필터용 시즌/담당자 목록"""
    with _conn(db_path) as conn:
        seasons = conn.execute(
            "SELECT DISTINCT 시즌 FROM fabrics WHERE 채택여부='채택' AND 시즌 IS NOT NULL AND 시즌!='' ORDER BY 시즌"
        ).fetchall()
        managers = conn.execute(
            "SELECT DISTINCT 담당자 FROM fabrics WHERE 채택여부='채택' AND 담당자 IS NOT NULL AND 담당자!='' ORDER BY 담당자"
        ).fetchall()
    return (["전체"] + [s[0] for s in seasons],
            ["전체"] + [m[0] for m in managers])


def backup_db(db_path, dest_path):
    shutil.copy(db_path, dest_path)


def auto_backup(db_path):
    """실행 파일 옆 backup/ 폴더에 하루 1회 자동 백업 (최근 30개 유지)"""
    try:
        import sys
        base_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) \
                   else os.path.dirname(os.path.abspath(__file__))
        backup_dir = os.path.join(base_dir, "backup")
        os.makedirs(backup_dir, exist_ok=True)
        today = datetime.now().strftime("%Y%m%d")
        backup_file = os.path.join(backup_dir, f"fabrics_backup_{today}.db")
        if os.path.exists(backup_file):
            return
        if os.path.exists(db_path):
            shutil.copy(db_path, backup_file)
            backups = sorted(
                f for f in os.listdir(backup_dir)
                if f.startswith("fabrics_backup_") and f.endswith(".db")
            )
            for old in backups[:-30]:
                os.remove(os.path.join(backup_dir, old))
    except Exception as e:
        print(f"자동 백업 실패 (무시): {e}")
