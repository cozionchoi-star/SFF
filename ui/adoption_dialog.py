"""시즌 채택 현황 다이얼로그"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import config
import database
import utils


def open_adoption_viewer(master, db_path, df):
    """시즌별 채택 원단 현황 창"""
    c = config.COLORS

    win = tk.Toplevel(master)
    win.title("시즌 채택 현황")
    win.geometry("1200x650")
    win.configure(bg=c["DARK_BG"])
    win.transient(master)

    # 상단 필터
    filter_frame = ttk.Frame(win, padding="10 8 10 4")
    filter_frame.pack(fill="x")
    ttk.Label(filter_frame, text="시즌:", font=("맑은 고딕", 10, "bold")).pack(side="left", padx=(0, 5))

    season_list, manager_list = database.get_adoption_filter_lists(db_path)

    season_var = tk.StringVar(value="전체")
    season_cb  = ttk.Combobox(filter_frame, textvariable=season_var,
                               values=season_list, state="readonly", width=10)
    season_cb.pack(side="left", padx=(0, 15))

    ttk.Label(filter_frame, text="담당자:").pack(side="left", padx=(0, 5))
    manager_var = tk.StringVar(value="전체")
    manager_cb  = ttk.Combobox(filter_frame, textvariable=manager_var,
                                values=manager_list, state="readonly", width=10)
    manager_cb.pack(side="left", padx=(0, 15))

    count_label = ttk.Label(filter_frame, text="", font=("맑은 고딕", 9), foreground="#555555")
    count_label.pack(side="left", padx=10)

    # 트리뷰
    view_cols = ["시즌", "브랜드 및 제안처", "담당자", "업체명", "제품명",
                 "S&C 원단명", "혼용률", "원단스펙", "원단 무게",
                 "원가(YDS)", "전달가격", "마진(%)", "재고 및 running"]
    col_w = {
        "시즌": 55, "브랜드 및 제안처": 160, "담당자": 70, "업체명": 80,
        "제품명": 100, "S&C 원단명": 110, "혼용률": 100, "원단스펙": 130,
        "원단 무게": 65, "원가(YDS)": 80, "전달가격": 80, "마진(%)": 75,
        "재고 및 running": 120,
    }
    tree_frame = ttk.Frame(win, padding="10 0")
    tree_frame.pack(fill="both", expand=True)
    tree = ttk.Treeview(tree_frame, columns=view_cols, show="headings")
    for col in view_cols:
        tree.heading(col, text=col, anchor="center")
        tree.column(col, width=col_w.get(col, 100), anchor="center", minwidth=40)
    vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    ttk.Button(filter_frame, text="엑셀 내보내기",
               command=lambda: _export_to_excel(tree, view_cols)).pack(side="right", padx=5)

    def load_data():
        tree.delete(*tree.get_children())
        sel_season  = season_var.get()
        sel_manager = manager_var.get()

        adopted_ids = database.get_adopted_rowids(db_path)
        filtered = df[df["_rowid"].isin(adopted_ids)].copy()

        if sel_season != "전체":
            filtered = filtered[filtered["시즌"].astype(str).str.strip() == sel_season]
        if sel_manager != "전체":
            filtered = filtered[filtered["담당자"].astype(str).str.strip() == sel_manager]

        filtered = filtered.sort_values(by=["시즌", "브랜드 및 제안처"], na_position="last")

        for i, row in filtered.iterrows():
            vals = [utils.format_for_display(row.get(col), col) for col in view_cols]
            tag  = "even" if i % 2 == 0 else "odd"
            tree.insert("", "end", values=vals, tags=(tag,))

        tree.tag_configure("even", background=c["TREEVIEW_ROW_EVEN"])
        tree.tag_configure("odd",  background=c["TREEVIEW_ROW_ODD"])
        count_label.config(text=f"총 {len(filtered)}개 원단")

    season_cb.bind( "<<ComboboxSelected>>", lambda e: load_data())
    manager_cb.bind("<<ComboboxSelected>>", lambda e: load_data())
    load_data()


def _export_to_excel(tree, view_cols):
    """채택 현황 엑셀 내보내기"""
    rows = [tree.item(iid)["values"] for iid in tree.get_children()]
    if not rows:
        messagebox.showwarning("경고", "내보낼 데이터가 없습니다.")
        return
    df = pd.DataFrame(rows, columns=view_cols)
    path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Excel", "*.xlsx")],
        title="채택 현황 내보내기",
    )
    if path:
        try:
            df.to_excel(path, index=False)
            messagebox.showinfo("완료", f"저장되었습니다:\n{path}")
        except Exception as e:
            messagebox.showerror("오류", f"저장 오류: {e}")
