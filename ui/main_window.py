"""메인 창 — FabricApp"""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import os
import re

import config
import database
import utils
from ui import form_dialog, proposal_dialog, adoption_dialog


class FabricApp:
    def __init__(self, master):
        self.master = master
        self._db_path = config.get_db_path()
        self._last_exr = [0.145]   # list so form_dialog can mutate it

        master.title(f"S&C FABRIC FINDER  v{config.APP_VERSION}")
        master.geometry("1300x750")
        master.configure(bg=config.COLORS["DARK_BG"])

        from ui.styles import apply_style, get_tree_fonts
        apply_style()
        self._tree_font, self._tree_heading_font = get_tree_fonts()

        self.df = None
        self.current_displayed_df = None
        self.selected_rows_original_data = []
        self.compact_mode_var = tk.BooleanVar(value=False)
        self._resize_timer       = None
        self._main_tree_tags_set = False
        self._sel_tree_tags_set  = False

        database.init_db(self._db_path)
        database.create_fabrics_table(self._db_path)
        self._create_widgets()
        self._load_data()
        self._toggle_compact_mode()
        database.auto_backup(self._db_path)

    # ─── UI 구성 ────────────────────────────────────────────────────────────

    def _create_widgets(self):
        # 검색 프레임
        sf = ttk.Frame(self.master, padding="10 10 10 0")
        sf.pack(fill="x")

        self.search_column = ttk.Combobox(
            sf, values=["전체"] + config.COLUMNS, state="readonly", width=15)
        self.search_column.set("전체")
        self.search_column.grid(row=0, column=0, padx=5, pady=5)

        self.search_entry = ttk.Entry(sf, width=40)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        self.search_entry.bind("<Return>",    self._search_data)
        self.search_entry.bind("<KeyRelease>", self._on_key_release)

        ttk.Button(sf, text="검색", command=self._search_data).grid(
            row=0, column=2, padx=5, pady=5)

        self.realtime_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sf, text="실시간 검색", variable=self.realtime_var).grid(
            row=0, column=3, padx=5, pady=5)
        ttk.Checkbutton(sf, text="간략 모드", variable=self.compact_mode_var,
                        command=self._toggle_compact_mode).grid(
            row=0, column=4, padx=5, pady=5)

        ttk.Label(sf, text="시즌:").grid(row=0, column=5, padx=(15, 2), pady=5)
        self.season_var = tk.StringVar(value="전체")
        self.season_combo = ttk.Combobox(
            sf, textvariable=self.season_var, values=["전체"],
            state="readonly", width=8)
        self.season_combo.grid(row=0, column=6, padx=5, pady=5)
        self.season_combo.bind("<<ComboboxSelected>>", self._search_data)
        ttk.Button(sf, text="필터 초기화", command=self._reset_filters).grid(
            row=0, column=7, padx=5, pady=5)

        # 상단 버튼
        tbf = ttk.Frame(self.master, padding="10 0")
        tbf.pack(fill="x")
        ttk.Button(tbf, text="신규 제안",      command=self._open_form_for_proposal).grid(
            row=0, column=0, padx=5, pady=5)
        ttk.Button(tbf, text="단일 추가",      command=lambda: self._open_form("add")).grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Button(tbf, text="엑셀 가져오기",  command=self._import_excel).grid(
            row=0, column=2, padx=5, pady=5)
        ttk.Button(tbf, text="시즌 채택 현황", command=self._open_adoption_viewer).grid(
            row=0, column=3, padx=5, pady=5)
        ttk.Label(tbf, text="※ 수정 · 삭제 · 채택은 우클릭",
                  foreground="#888888", font=("맑은 고딕", 8)).grid(
            row=0, column=4, padx=15)

        # 메인 콘텐츠
        cf = ttk.Frame(self.master)
        cf.pack(expand=True, fill="both", padx=5)

        # 메인 트리뷰
        mtf = ttk.Frame(cf, padding="5 5 5 0")
        mtf.pack(expand=True, fill="both")
        self.main_tree = ttk.Treeview(mtf, columns=config.COLUMNS, show="headings")
        self.main_tree.pack(side="left", expand=True, fill="both")
        vsb = ttk.Scrollbar(mtf, orient="vertical", command=self.main_tree.yview)
        vsb.pack(side="right", fill="y")
        self.main_tree.configure(yscrollcommand=vsb.set)
        for col in config.COLUMNS:
            self.main_tree.heading(col, text=col, anchor="center",
                                   command=lambda c=col: self._sort_treeview(self.main_tree, c))
            self.main_tree.column(col, width=100, anchor="center", stretch=False, minwidth=50)
        self.main_tree.bind("<Double-1>",  self._add_to_selected)
        self.main_tree.bind("<Button-3>",  self._show_context_menu)
        self.main_tree.bind("<Configure>", lambda e: self._on_treeview_configure(e.widget))

        # 선택된 데이터 트리뷰
        stf = ttk.LabelFrame(cf, text="선택된 데이터 목록", padding="5")
        stf.pack(fill="both", expand=True, padx=5, pady=5)
        self.selected_tree = ttk.Treeview(stf, columns=config.COLUMNS, show="headings")
        self.selected_tree.pack(side="left", expand=True, fill="both")
        sel_vsb = ttk.Scrollbar(stf, orient="vertical", command=self.selected_tree.yview)
        sel_vsb.pack(side="right", fill="y")
        self.selected_tree.configure(yscrollcommand=sel_vsb.set)
        for col in config.COLUMNS:
            self.selected_tree.heading(col, text=col, anchor="center")
            self.selected_tree.column(col, width=100, anchor="center", stretch=False, minwidth=50)
        self.selected_tree.bind("<Double-1>",  self._remove_from_selected)
        self.selected_tree.bind("<Configure>", lambda e: self._on_treeview_configure(e.widget))

        # 하단 버튼
        bbf = ttk.Frame(cf, padding="0 0 5 8")
        bbf.pack(fill="x")
        ttk.Button(bbf, text="선택 엑셀 저장",         command=self._save_selected_to_excel).grid(
            row=0, column=0, padx=5, pady=5)
        ttk.Button(bbf, text="라벨 저장",               command=self._save_label).grid(
            row=0, column=1, padx=5, pady=5)
        ttk.Button(bbf, text="선택 해제",               command=self._clear_selected).grid(
            row=0, column=2, padx=5, pady=5)
        ttk.Button(bbf, text="DB 백업",                 command=self._backup_db).grid(
            row=0, column=3, padx=5, pady=5)
        ttk.Button(bbf, text="원단 정보 내보내기",       command=self._export_all_selected_data_to_excel).grid(
            row=0, column=4, padx=5, pady=5)
        ttk.Button(bbf, text="전체 원단 정보 내보내기",  command=self._export_all_displayed_data_to_excel).grid(
            row=0, column=5, padx=5, pady=5)

    # ─── 컬럼 너비 조절 ─────────────────────────────────────────────────────

    def _on_treeview_configure(self, widget):
        if self._resize_timer:
            self.master.after_cancel(self._resize_timer)
        data = (self.current_displayed_df if widget == self.main_tree
                else pd.DataFrame(self.selected_rows_original_data))
        self._resize_timer = self.master.after(
            100, lambda: self._adjust_column_widths(widget, data))

    def _adjust_column_widths(self, treeview, df_data):
        if df_data is None or df_data.empty:
            for col in config.COLUMNS:
                treeview.column(col, width=100, stretch=True, minwidth=50)
            return

        padding = 20
        widths = {}
        total  = 0
        for col in config.COLUMNS:
            hw = self._tree_heading_font.measure(col)
            cw = 0
            if col in df_data.columns and not df_data.empty:
                for val in df_data[col]:
                    w = self._tree_font.measure(utils.format_for_display(val, col))
                    if w > cw:
                        cw = w
            optimal = max(hw, cw) + padding
            max_w   = config.MAX_COL_WIDTHS.get(col)
            final   = min(optimal, max_w) if max_w else optimal
            final   = max(final, 50)
            widths[col] = final
            total      += final

        actual_w = treeview.winfo_width()
        if actual_w <= 1:
            pw = treeview.master.winfo_width()
            actual_w = (pw - 20) if pw > 1 else 1200

        flex       = config.FLEXIBLE_COLUMN
        is_compact = self.compact_mode_var.get()
        flex_hidden = (flex in config.ALWAYS_HIDDEN_COLS or
                       (is_compact and flex in config.COMPACT_MODE_TOGGLE_COLS))

        if total < actual_w:
            remaining = actual_w - total
            if not flex_hidden and flex in widths:
                treeview.column(flex, width=widths[flex] + remaining, stretch=True, minwidth=50)
                for col in config.COLUMNS:
                    if col != flex:
                        treeview.column(col, width=widths[col], stretch=False, minwidth=50)
            else:
                for col in config.COLUMNS:
                    treeview.column(col, width=widths[col], stretch=True, minwidth=50)
        else:
            for col in config.COLUMNS:
                treeview.column(col, width=widths[col], stretch=False, minwidth=50)

    # ─── 데이터 로드 ────────────────────────────────────────────────────────

    def _load_data(self):
        self.df = database.load_fabrics(self._db_path)
        self._reload_treeviews()

    def _load_data_silent(self):
        """화면 갱신 없이 df만 다시 로드"""
        self.df = database.load_fabrics(self._db_path)

    def _refresh_season_list(self):
        if self.df is None or self.df.empty:
            return
        seasons = sorted(set(
            v.strip() for v in self.df["시즌"].dropna().astype(str)
            if v.strip() and v.strip().lower() != "none"
        ))
        self.season_combo["values"] = ["전체"] + seasons

    def _reload_treeviews(self):
        self._refresh_season_list()
        self._search_data()
        self._populate_selected_tree()
        self._toggle_compact_mode()

    # ─── 트리뷰 채우기 ──────────────────────────────────────────────────────

    def _populate_main_tree(self, df_to_display):
        self.main_tree.delete(*self.main_tree.get_children())
        c           = config.COLORS
        adopted_ids = database.get_adopted_rowids(self._db_path)

        for i, row in df_to_display.iterrows():
            iid  = str(row["_rowid"])
            vals = [utils.format_for_display(row[col], col) for col in config.COLUMNS]
            tag  = ("adopted" if int(row["_rowid"]) in adopted_ids
                    else ("evenrow" if i % 2 == 0 else "oddrow"))
            self.main_tree.insert("", "end", iid=iid, values=vals, tags=(tag,))

        if not self._main_tree_tags_set:
            self.main_tree.tag_configure("evenrow", background=c["TREEVIEW_ROW_EVEN"],
                                         foreground=c["TEXT_LIGHT"])
            self.main_tree.tag_configure("oddrow",  background=c["TREEVIEW_ROW_ODD"],
                                         foreground=c["TEXT_LIGHT"])
            self._main_tree_tags_set = True
        self.main_tree.tag_configure("adopted", background="#d4edda",
                                     foreground=c["TEXT_LIGHT"])
        self.current_displayed_df = df_to_display.copy()

    def _populate_selected_tree(self):
        self.selected_tree.delete(*self.selected_tree.get_children())
        self._update_selected_tree_visibility()
        c        = config.COLORS
        last_iid = None
        for i, row_dict in enumerate(self.selected_rows_original_data):
            vals     = [utils.format_for_display(row_dict.get(col), col) for col in config.COLUMNS]
            tag      = "evenrow" if i % 2 == 0 else "oddrow"
            last_iid = self.selected_tree.insert("", "end", values=vals, tags=(tag,))
        if not self._sel_tree_tags_set:
            self.selected_tree.tag_configure("evenrow", background=c["TREEVIEW_ROW_EVEN"],
                                             foreground=c["TEXT_LIGHT"])
            self.selected_tree.tag_configure("oddrow",  background=c["TREEVIEW_ROW_ODD"],
                                             foreground=c["TEXT_LIGHT"])
            self._sel_tree_tags_set = True
        if last_iid:
            self.selected_tree.see(last_iid)

    def _update_selected_tree_visibility(self):
        is_compact = self.compact_mode_var.get()
        for col in config.COLUMNS:
            if col in config.ALWAYS_HIDDEN_COLS:
                self.selected_tree.column(col, width=0, stretch=False)
            elif col in config.COMPACT_MODE_TOGGLE_COLS:
                if is_compact:
                    self.selected_tree.column(col, width=0, stretch=False)
                else:
                    self.selected_tree.column(col, width=100, stretch=True)
            else:
                self.selected_tree.column(col, width=100, stretch=True)

    # ─── 검색 / 필터 ────────────────────────────────────────────────────────

    def _search_data(self, event=None):
        kw     = self.search_entry.get().strip().lower()
        col    = self.search_column.get()
        season = self.season_var.get()
        df_f   = (self.df.copy() if self.df is not None
                  else pd.DataFrame(columns=config.COLUMNS))

        if kw:
            if col == "전체":
                mask = pd.Series(False, index=df_f.index)
                for c in config.COLUMNS:
                    mask |= df_f[c].astype(str).fillna("").str.contains(kw, case=False, na=False)
                df_f = df_f[mask]
            else:
                df_f = df_f[df_f[col].astype(str).fillna("").str.contains(kw, case=False, na=False)]

        if season != "전체":
            df_f = df_f[df_f["시즌"].astype(str).str.strip() == season]

        self._populate_main_tree(df_f)

    def _reset_filters(self):
        self.search_entry.delete(0, tk.END)
        self.search_column.set("전체")
        self.season_var.set("전체")
        self._search_data()

    def _on_key_release(self, event):
        if self.realtime_var.get():
            self._search_data()

    # ─── 폼 열기 ────────────────────────────────────────────────────────────

    def _open_form(self, mode, row_id=None, initial_data=None):
        form_dialog.open_form(
            self.master, mode, self._db_path,
            row_id=row_id, initial_data=initial_data,
            on_save=self._load_data,
            last_exchange_rate=self._last_exr,
        )

    def _open_form_for_proposal(self):
        sel = self.main_tree.selection()
        if not sel:
            messagebox.showwarning("경고", "신규 제안할 항목을 선택하세요.")
            return
        rid  = int(sel[0])
        data = self.df[self.df["_rowid"] == rid].iloc[0].drop("_rowid").to_dict()
        self._open_form("proposal", initial_data=data)

    def _get_selected_rowid(self):
        sel = self.main_tree.selection()
        if not sel:
            messagebox.showwarning("경고", "원단을 먼저 선택하세요.")
            return None
        return int(sel[0])

    def _update_selected_entry(self):
        rid = self._get_selected_rowid()
        if rid is None:
            return
        data = self.df[self.df["_rowid"] == rid].iloc[0].drop("_rowid").to_dict()
        self._open_form("edit", row_id=rid, initial_data=data)

    def _open_proposal_manager(self):
        rid = self._get_selected_rowid()
        if rid is None:
            return
        fabric_row = self.df[self.df["_rowid"] == rid]
        if fabric_row.empty:
            messagebox.showerror("오류", "원단 정보를 찾을 수 없습니다.")
            return
        proposal_dialog.open_proposal_manager(
            self.master, self._db_path, rid, fabric_row.iloc[0].to_dict())

    def _open_adoption_viewer(self):
        adoption_dialog.open_adoption_viewer(self.master, self._db_path, self.df)

    # ─── 데이터 조작 ────────────────────────────────────────────────────────

    def _import_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xls")])
        if not path:
            return
        engine = "openpyxl" if path.lower().endswith(".xlsx") else "xlrd"
        try:
            df_ex = pd.read_excel(path, dtype=str, engine=engine)

            PROPOSAL_COLS = ["시즌", "담당자", "제안결과", "메모"]
            proposal_data = {col: df_ex[col].tolist()
                             for col in PROPOSAL_COLS if col in df_ex.columns}

            reverse_map = {v: k for k, v in config.DB_UI_COL_MAP.items()}
            df_ex.rename(columns=reverse_map, inplace=True)
            db_cols = [utils.get_db_col_name(c) for c in config.COLUMNS]
            df_ex   = df_ex.reindex(columns=db_cols, fill_value="")

            missing = [c for c in db_cols if c not in df_ex.columns]
            if missing:
                messagebox.showwarning("경고",
                    f"엑셀 파일에 다음 컬럼이 누락되었습니다: {', '.join(missing)}\n"
                    "누락된 컬럼은 빈 값으로 처리됩니다.")
        except Exception as e:
            messagebox.showerror("오류", f"엑셀 읽기 실패: {e}")
            return

        try:
            n = database.import_fabrics(
                self._db_path,
                utils.process_df_for_storage(df_ex),
                proposal_data or None,
            )
            msg = f"엑셀 데이터가 성공적으로 추가되었습니다. ({n}건)"
            if proposal_data:
                msg += f"\n이력 컬럼({', '.join(proposal_data.keys())})도 함께 저장되었습니다."
            messagebox.showinfo("완료", msg)
            self._load_data()
        except Exception as e:
            messagebox.showerror("오류", f"DB 추가 실패: {e}")

    def _delete_row(self):
        sel = self.main_tree.selection()
        if not sel:
            messagebox.showwarning("경고", "삭제할 항목을 선택하세요.")
            return
        if messagebox.askyesno("확인", "선택된 항목을 정말 삭제하시겠습니까?"):
            try:
                database.delete_fabric(self._db_path, int(sel[0]))
                messagebox.showinfo("완료", "선택된 항목이 삭제되었습니다.")
                self._load_data()
            except Exception as e:
                messagebox.showerror("오류", f"삭제 오류: {e}")

    def _add_to_selected(self, event=None):
        for iid in self.main_tree.selection():
            try:
                rid = int(iid)
            except ValueError:
                continue
            if any(r.get("_rowid") == rid for r in self.selected_rows_original_data):
                continue
            row_data = self.df[self.df["_rowid"] == rid].iloc[0].drop("_rowid").to_dict()
            self.selected_rows_original_data.append(row_data)
        self._populate_selected_tree()

    def _remove_from_selected(self, event):
        iid = self.selected_tree.identify_row(event.y)
        if not iid:
            return
        idx = self.selected_tree.index(iid)
        if 0 <= idx < len(self.selected_rows_original_data):
            self.selected_rows_original_data.pop(idx)
        self._populate_selected_tree()

    def _clear_selected(self):
        if messagebox.askyesno("확인", "선택된 모든 데이터를 목록에서 제거하시겠습니까?"):
            self.selected_rows_original_data.clear()
            self._populate_selected_tree()

    # ─── 컬럼 가시성 / 컨텍스트 메뉴 ───────────────────────────────────────

    def _toggle_compact_mode(self):
        is_compact = self.compact_mode_var.get()
        for col in config.COLUMNS:
            if col in config.ALWAYS_HIDDEN_COLS:
                self.main_tree.column(col, width=0, stretch=False)
            elif col in config.COMPACT_MODE_TOGGLE_COLS:
                if is_compact:
                    self.main_tree.column(col, width=0, stretch=False)
                else:
                    self.main_tree.column(col, width=100, stretch=True)
            else:
                self.main_tree.column(col, width=100, stretch=True)
        self._populate_selected_tree()

    def _show_context_menu(self, event):
        iid = self.main_tree.identify_row(event.y)
        if not iid:
            return
        self.main_tree.selection_set(iid)
        rid        = int(iid)
        is_adopted = rid in database.get_adopted_rowids(self._db_path)

        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(
            label="✅ 채택 해제" if is_adopted else "✅ 채택",
            command=self._toggle_adoption)
        menu.add_separator()
        menu.add_command(label="✏️  수정",     command=self._update_selected_entry)
        menu.add_command(label="📋  이력 관리", command=self._open_proposal_manager)
        menu.add_command(label="🗑️  삭제",      command=self._delete_row)
        menu.tk_popup(event.x_root, event.y_root)

    def _toggle_adoption(self):
        sel = self.main_tree.selection()
        if not sel:
            messagebox.showwarning("경고", "채택할 원단을 선택하세요.")
            return
        database.toggle_adoption(self._db_path, [int(iid) for iid in sel])

        kw     = self.search_entry.get()
        col    = self.search_column.get()
        season = self.season_var.get()

        self._load_data_silent()
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, kw)
        self.search_column.set(col)
        self.season_var.set(season)
        self._search_data()

    # ─── 내보내기 ───────────────────────────────────────────────────────────

    def _visible_columns(self):
        is_compact = self.compact_mode_var.get()
        return [c for c in config.COLUMNS
                if c not in config.ALWAYS_HIDDEN_COLS
                and not (is_compact and c in config.COMPACT_MODE_TOGGLE_COLS)]

    def _save_selected_to_excel(self):
        if not self.selected_rows_original_data:
            messagebox.showwarning("경고", "선택된 데이터가 없습니다.")
            return
        export_cols = ["날짜", "제품명", "혼용률", "원단스펙", "원단 무게",
                       "제시 폭", "전달가격", "재고 및 running"]
        rows = []
        for r in self.selected_rows_original_data:
            row = {}
            for col in export_cols:
                src = "S&C 원단명" if col == "제품명" else col
                row[col] = utils.format_for_display(r.get(src), src)
            rows.append(row)
        df = pd.DataFrame(rows)
        df.rename(columns={"제시 폭": "원단 폭", "전달가격": "원단가"}, inplace=True)
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel", "*.xlsx")])
        if path:
            try:
                df.to_excel(path, index=False)
                messagebox.showinfo("완료", "선택된 데이터가 엑셀 파일로 저장되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"저장 오류: {e}")

    def _save_label(self):
        if not self.selected_rows_original_data:
            messagebox.showwarning("경고", "선택된 데이터가 없습니다.")
            return
        rows = []
        for r in self.selected_rows_original_data:
            rows.append({
                "ART NO.":     f"ART NO. : {utils.format_for_display(r.get('S&C 원단명'), 'S&C 원단명')}",
                "COMPOSITION": f"COMPOSITION : {utils.format_for_display(r.get('혼용률'), '혼용률')}",
                "WEIGHT":      f"WEIGHT : {utils.format_for_display(r.get('원단 무게'), '원단 무게')}",
                "MOQ":         f"MOQ : {utils.format_for_display(r.get('재고 및 running'), '재고 및 running')}",
            })
        df   = pd.DataFrame(rows)
        path = filedialog.asksaveasfilename(defaultextension=".xlsx",
                                            filetypes=[("Excel", "*.xlsx")])
        if path:
            try:
                df.to_excel(path, index=False)
                messagebox.showinfo("완료", "라벨 데이터가 엑셀 파일로 저장되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", f"저장 오류: {e}")

    def _backup_db(self):
        from datetime import datetime
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        bp  = os.path.join(os.path.dirname(self._db_path), f"fabrics_backup_{now}.db")
        try:
            database.backup_db(self._db_path, bp)
            messagebox.showinfo("완료", f"데이터베이스 백업이 완료되었습니다:\n{bp}")
        except FileNotFoundError:
            messagebox.showerror("오류", "원본 DB 파일이 존재하지 않습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"백업 실패: {e}")

    def _export_all_selected_data_to_excel(self):
        if not self.selected_rows_original_data:
            messagebox.showwarning("경고", "선택된 데이터가 없습니다.")
            return
        cols = self._visible_columns()
        rows = []
        for r in self.selected_rows_original_data:
            rows.append({col: utils.format_for_display(
                r.get("S&C 원단명" if col == "제품명" else col),
                "S&C 원단명" if col == "제품명" else col)
                for col in cols})
        df   = pd.DataFrame(rows, columns=cols)
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")],
            title="선택된 모든 원단 정보 내보내기")
        if path:
            try:
                df.to_excel(path, index=False)
                messagebox.showinfo("완료", f"저장되었습니다:\n{path}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 오류: {e}")

    def _export_all_displayed_data_to_excel(self):
        if self.current_displayed_df is None or self.current_displayed_df.empty:
            messagebox.showwarning("경고", "내보낼 데이터가 없습니다.")
            return
        cols = self._visible_columns()
        rows = []
        for _, row in self.current_displayed_df.iterrows():
            rows.append({col: utils.format_for_display(
                row.get("S&C 원단명" if col == "제품명" else col),
                "S&C 원단명" if col == "제품명" else col)
                for col in cols})
        df   = pd.DataFrame(rows, columns=cols)
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")],
            title="현재 표시된 전체 원단 정보 내보내기")
        if path:
            try:
                df.to_excel(path, index=False)
                messagebox.showinfo("완료", f"저장되었습니다:\n{path}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 오류: {e}")

    # ─── 정렬 ───────────────────────────────────────────────────────────────

    def _sort_treeview(self, tree, col):
        items   = [(tree.set(k, col), k) for k in tree.get_children("")]
        numeric = (col in config.NUMERIC_COLS_FOR_STORAGE or
                   col in config.NUMERIC_COLS_FOR_DECIMAL_DISPLAY or
                   col in config.CURRENCY_COLS_DISPLAY or
                   col in config.PERCENT_COLS_DISPLAY)
        if numeric:
            def key(v):
                cleaned = re.sub(r"[^\d.\-]+", "", str(v))
                try:
                    return float(cleaned)
                except ValueError:
                    return float("-inf")
            items.sort(key=lambda x: key(x[0]))
        else:
            items.sort(key=lambda x: x[0])

        if not hasattr(tree, "sort_direction"):
            tree.sort_direction = {}
        reverse = tree.sort_direction.get(col, False)
        if reverse:
            items.reverse()
        for idx, (_, k) in enumerate(items):
            tree.move(k, "", idx)
        tree.sort_direction[col] = not reverse
