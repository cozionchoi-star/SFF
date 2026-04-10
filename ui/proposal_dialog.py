"""제안 이력 관리 다이얼로그"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import config
import database


def open_proposal_manager(master, db_path, fabric_rowid, fabric_info):
    """
    선택된 원단의 제안 이력 추가/수정/삭제 창
    fabric_info: dict (UI 컬럼명 기준)
    """
    c = config.COLORS
    fabric_name = fabric_info.get("S&C 원단명", "") or ""
    brand       = fabric_info.get("브랜드 및 제안처", "") or ""

    win = tk.Toplevel(master)
    win.title(f"이력 관리 — {fabric_name}")
    win.geometry("940x540")
    win.configure(bg=c["DARK_BG"])
    win.transient(master)
    win.grab_set()

    # 아이콘
    try:
        from PIL import Image, ImageTk
        import os
        icon_path = config.get_icon_path()
        if os.path.exists(icon_path):
            img = ImageTk.PhotoImage(Image.open(icon_path).resize((32, 32)))
            win.wm_iconphoto(True, img)
    except Exception:
        pass

    # 원단 요약
    info_frame = ttk.Frame(win, padding="10 8 10 4")
    info_frame.pack(fill="x")
    ttk.Label(
        info_frame,
        text=f"원단명: {fabric_name}   |   브랜드: {brand}   |   혼용률: {fabric_info.get('혼용률', '')}",
        font=("맑은 고딕", 10, "bold"),
    ).pack(side="left")

    # 이력 목록
    list_frame = ttk.Frame(win, padding="10 0")
    list_frame.pack(fill="both", expand=True)

    hist_cols = ["날짜", "브랜드", "시즌", "전달가격", "담당자", "제안결과", "메모"]
    col_w     = {"날짜": 90, "브랜드": 130, "시즌": 70, "전달가격": 90,
                 "담당자": 80, "제안결과": 80, "메모": 230}
    hist_tree = ttk.Treeview(list_frame, columns=hist_cols, show="headings", height=8)
    for col in hist_cols:
        hist_tree.heading(col, text=col, anchor="center")
        hist_tree.column(col, width=col_w.get(col, 100), anchor="center")
    vsb = ttk.Scrollbar(list_frame, orient="vertical", command=hist_tree.yview)
    hist_tree.configure(yscrollcommand=vsb.set)
    hist_tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")

    # 입력 폼
    form_frame = ttk.LabelFrame(win, text="이력 입력 / 수정", padding="10 5")
    form_frame.pack(fill="x", padx=10, pady=5)

    FIELDS = ["날짜", "브랜드", "시즌", "전달가격", "담당자", "제안결과", "메모"]
    entries = {}
    for i, field in enumerate(FIELDS):
        ttk.Label(form_frame, text=field).grid(row=0, column=i * 2, padx=(8, 2), sticky="w")
        if field == "제안결과":
            w = ttk.Combobox(form_frame, values=["검토중", "채택", "미채택"],
                             state="readonly", width=8)
            w.set("검토중")
        else:
            w = ttk.Entry(form_frame,
                          width=10 if field in ("날짜", "시즌", "전달가격", "담당자") else 22)
        w.grid(row=0, column=i * 2 + 1, padx=(0, 5), pady=6)
        entries[field] = w

    entries["날짜"].insert(0, datetime.now().strftime("%Y-%m-%d"))
    entries["브랜드"].insert(0, brand)

    selected_id = [None]

    def load_list():
        hist_tree.delete(*hist_tree.get_children())
        # get_proposals returns: (id, 날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모)
        for r in database.get_proposals(db_path, fabric_rowid):
            result = r[6]  # 제안결과 (index 6)
            tag = "채택" if result == "채택" else ("미채택" if result == "미채택" else "")
            hist_tree.insert("", "end", iid=str(r[0]), values=r[1:], tags=(tag,))
        hist_tree.tag_configure("채택",   foreground="#1a7a1a")
        hist_tree.tag_configure("미채택", foreground="#aaaaaa")

    def on_select(event):
        sel = hist_tree.selection()
        if not sel:
            return
        selected_id[0] = int(sel[0])
        # get_proposal returns: (날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모)
        row = database.get_proposal(db_path, selected_id[0])
        if row:
            for i, field in enumerate(FIELDS):
                w = entries[field]
                if isinstance(w, ttk.Combobox):
                    w.set(row[i] or "검토중")
                else:
                    w.delete(0, tk.END)
                    w.insert(0, row[i] or "")

    hist_tree.bind("<<TreeviewSelect>>", on_select)

    def save():
        vals = {f: entries[f].get() for f in FIELDS}
        database.save_proposal(db_path, fabric_rowid, vals, selected_id[0])
        msg = "이력이 수정되었습니다." if selected_id[0] else "이력이 추가되었습니다."
        messagebox.showinfo("완료", msg, parent=win)
        selected_id[0] = None
        clear_form()
        load_list()

    def delete():
        if selected_id[0] is None:
            messagebox.showwarning("경고", "삭제할 이력을 목록에서 선택하세요.", parent=win)
            return
        if messagebox.askyesno("확인", "선택된 이력을 삭제하시겠습니까?", parent=win):
            database.delete_proposal(db_path, selected_id[0])
            selected_id[0] = None
            clear_form()
            load_list()

    def clear_form():
        selected_id[0] = None
        for field in FIELDS:
            w = entries[field]
            if isinstance(w, ttk.Combobox):
                w.set("검토중")
            else:
                w.delete(0, tk.END)
        entries["날짜"].insert(0, datetime.now().strftime("%Y-%m-%d"))
        entries["브랜드"].insert(0, brand)

    btn_frame = ttk.Frame(win, padding="10 0 10 10")
    btn_frame.pack(fill="x")
    ttk.Button(btn_frame, text="저장 / 수정", command=save).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="삭제",         command=delete).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="초기화",        command=clear_form).pack(side="left", padx=5)

    load_list()
