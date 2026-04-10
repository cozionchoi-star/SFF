"""원단 추가 / 수정 / 신규 제안 다이얼로그"""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import config
import database
import utils


def open_form(master, mode, db_path, row_id=None, initial_data=None,
              on_save=None, last_exchange_rate=None):
    """
    mode: "add" | "edit" | "proposal"
    on_save: 저장 완료 후 콜백 (인자 없음)
    last_exchange_rate: [float] 공유 참조 (리스트 1원소)
    """
    c = config.COLORS
    titles = {"add": "단일 추가", "edit": "데이터 수정", "proposal": "신규 제안"}
    win = tk.Toplevel(master)
    win.title(titles[mode])
    win.configure(bg=c["DARK_BG"])
    win.transient(master)
    win.grab_set()
    win.focus_set()

    # 아이콘
    try:
        from PIL import Image, ImageTk
        icon_path = config.get_icon_path()
        import os
        if os.path.exists(icon_path):
            img = ImageTk.PhotoImage(Image.open(icon_path).resize((32, 32)))
            win.wm_iconphoto(True, img)
    except Exception:
        pass

    entries = {}
    for i, col in enumerate(config.COLUMNS):
        tk.Label(win, text=col, bg=c["DARK_BG"], fg=c["TEXT_LIGHT"]).grid(
            row=i, column=0, sticky="w", padx=5, pady=2)
        e = tk.Entry(win, width=40, bg=c["LIGHTER_DARK_BG"],
                     fg=c["TEXT_LIGHT"], insertbackground=c["TEXT_LIGHT"])
        e.grid(row=i, column=1, padx=5, pady=2)
        entries[col] = e

        if (mode in ("add", "proposal")) and col == "날짜":
            e.insert(0, datetime.now().strftime("%Y-%m-%d"))
        elif initial_data and col in initial_data:
            disp = utils.format_for_display(initial_data[col], col)
            if not (mode == "proposal" and col in ("제시 폭", "마진(%)")):
                e.insert(0, disp)

    # 환율 입력
    exr_row = len(config.COLUMNS)
    tk.Label(win, text="환율 (RMB→USD)", bg=c["DARK_BG"], fg=c["ACCENT_BLUE"],
             font=("맑은 고딕", 9, "bold")).grid(row=exr_row, column=0, sticky="w", padx=5, pady=(8, 2))
    exr_entry = tk.Entry(win, width=40, bg=c["LIGHTER_DARK_BG"],
                         fg=c["ACCENT_BLUE"], insertbackground=c["TEXT_LIGHT"])
    exr_entry.grid(row=exr_row, column=1, padx=5, pady=(8, 2))
    default_rate = last_exchange_rate[0] if last_exchange_rate else 0.145
    exr_entry.insert(0, str(default_rate))

    # 자동 계산 힌트 라벨
    hint_label = tk.Label(win, text="", bg=c["DARK_BG"], fg=c["ACCENT_BLUE"],
                          font=("맑은 고딕", 9))
    hint_label.grid(row=exr_row + 1, column=0, columnspan=2, pady=(2, 0))

    def _try_auto_calc(changed_field):
        RMB_M_TO_YDS = 0.9144
        try:
            exr_str = exr_entry.get().strip()
            RMB_TO_USD = float(exr_str) if exr_str else default_rate

            def get(field):
                return entries[field].get().replace("$", "").replace(",", "").replace("%", "").strip()

            def setval(field, val):
                entries[field].delete(0, tk.END)
                entries[field].insert(0, val)

            rmb_m   = float(get("RMB(M)"))   if get("RMB(M)")   else None
            rmb_yds = float(get("RMB(yds)")) if get("RMB(yds)") else None
            cost    = float(get("원가(YDS)")) if get("원가(YDS)") else None
            price   = float(get("전달가격"))  if get("전달가격")  else None
            margin  = float(get("마진(%)"))   if get("마진(%)")   else None
            hints   = []

            if changed_field == "RMB(M)" and rmb_m:
                calc_yds = rmb_m * RMB_M_TO_YDS
                setval("RMB(yds)", f"{calc_yds:.4f}")
                rmb_yds = calc_yds
                hints.append(f"RMB(yds) = {rmb_m} × {RMB_M_TO_YDS} = {calc_yds:.4f}")

            if changed_field in ("RMB(M)", "RMB(yds)", "환율") and rmb_yds:
                calc_cost = rmb_yds * RMB_TO_USD
                setval("원가(YDS)", f"{calc_cost:.2f}")
                cost = calc_cost
                hints.append(f"원가(YDS) = {rmb_yds:.4f} × {RMB_TO_USD} = ${calc_cost:.2f}")

            if changed_field in ("RMB(M)", "RMB(yds)", "환율", "원가(YDS)", "마진(%)"):
                if cost and margin is not None and 0 <= margin < 100:
                    calc_price = cost / (1 - margin / 100)
                    setval("전달가격", f"{calc_price:.2f}")
                    hints.append(f"전달가격 = ${cost:.2f} / (1 - {margin:.1f}%) = ${calc_price:.2f}")
            elif changed_field == "전달가격":
                if cost and price and price > 0:
                    calc_margin = (1 - cost / price) * 100
                    setval("마진(%)", f"{calc_margin:.2f}")
                    hints.append(f"마진 = (1 - ${cost:.2f}/${price:.2f}) × 100 = {calc_margin:.2f}%")

            hint_label.config(text="  →  ".join(hints) if hints else "")
        except (ValueError, ZeroDivisionError):
            hint_label.config(text="")

    for field in ("RMB(M)", "RMB(yds)", "원가(YDS)", "마진(%)", "전달가격"):
        entries[field].bind("<FocusOut>", lambda e, f=field: _try_auto_calc(f))
        entries[field].bind("<Return>",   lambda e, f=field: _try_auto_calc(f))
    exr_entry.bind("<FocusOut>", lambda e: _try_auto_calc("환율"))
    exr_entry.bind("<Return>",   lambda e: _try_auto_calc("환율"))

    def _save():
        try:
            exr_val = float(exr_entry.get().strip())
            if last_exchange_rate is not None:
                last_exchange_rate[0] = exr_val
        except ValueError:
            pass

        ui_data = {col: entries[col].get() for col in config.COLUMNS}
        try:
            database.save_fabric(db_path, ui_data, row_id if mode == "edit" else None)
            messagebox.showinfo("완료", "데이터가 저장되었습니다.", parent=win)
            win.destroy()
            if on_save:
                on_save()
        except Exception as e:
            messagebox.showerror("오류", f"저장 중 오류: {e}", parent=win)

    ttk.Button(win, text="저장", command=_save).grid(
        row=exr_row + 2, columnspan=2, pady=10)
