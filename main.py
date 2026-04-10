"""SFF 2.0 — Entry point"""
import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import configparser
import subprocess

import config
from ui.main_window import FabricApp

APP_VERSION = config.APP_VERSION

PATCH_NOTES = {
    "2.0": [
        "코드 구조 개편: config / utils / database / ui 모듈 분리",
        "자동 계산: RMB(M) → RMB(yds) → 원가(YDS) → 전달가격 체인",
        "컨텍스트 메뉴에 이력 관리 추가",
        "시즌 채택 현황 및 엑셀 내보내기",
        "하루 1회 자동 DB 백업 (최근 30개 보관)",
    ],
    "2.1": [
        "헤더에 버전 표시 추가",
        "자동 업데이트 알림 기능 추가",
    ],
}


def _get_version_txt_path():
    """version.txt 경로 — exe 옆 폴더"""
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), "version.txt")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "version.txt")


def _check_update(root):
    """version.txt와 현재 버전 비교 → 새 버전이 있으면 알림"""
    try:
        vpath = _get_version_txt_path()
        if not os.path.exists(vpath):
            return
        with open(vpath, "r", encoding="utf-8") as f:
            latest = f.read().strip()
        if not latest or latest == APP_VERSION:
            return

        answer = messagebox.askyesno(
            "업데이트 알림",
            f"새 버전 v{latest}이(가) 있습니다.\n"
            f"현재 버전: v{APP_VERSION}\n\n"
            "앱을 닫고 최신 버전을 다시 실행하면 업데이트됩니다.\n"
            "지금 SFF 폴더를 여시겠습니까?",
            parent=root,
        )
        if answer:
            folder = os.path.dirname(_get_version_txt_path())
            subprocess.Popen(f'explorer "{folder}"')
    except Exception:
        pass


def _show_patch_notes(root):
    cfg_dir  = os.path.dirname(config.get_db_path())
    cfg_path = os.path.join(cfg_dir, "sff_config.ini")
    cfg      = configparser.ConfigParser()
    cfg.read(cfg_path, encoding="utf-8")
    last_seen = cfg.get("app", "last_seen_version", fallback="")
    if last_seen == APP_VERSION:
        return
    notes = PATCH_NOTES.get(APP_VERSION, [])
    if not notes:
        return

    c   = config.COLORS
    win = tk.Toplevel(root)
    win.title(f"v{APP_VERSION} 패치 노트")
    win.configure(bg=c["DARK_BG"])
    win.transient(root)
    win.grab_set()
    win.resizable(False, False)

    tk.Label(win, text=f"✦  v{APP_VERSION} 업데이트 내역",
             bg=c["DARK_BG"], fg=c["PRIMARY_BLUE"],
             font=("맑은 고딕", 13, "bold")).pack(padx=24, pady=(18, 8))
    for note in notes:
        tk.Label(win, text=f"•  {note}",
                 bg=c["DARK_BG"], fg=c["TEXT_LIGHT"],
                 font=("맑은 고딕", 10), anchor="w").pack(fill="x", padx=32, pady=2)
    ttk.Button(win, text="확인", command=win.destroy).pack(pady=18)
    root.wait_window(win)

    os.makedirs(cfg_dir, exist_ok=True)
    if "app" not in cfg:
        cfg["app"] = {}
    cfg["app"]["last_seen_version"] = APP_VERSION
    with open(cfg_path, "w", encoding="utf-8") as f:
        cfg.write(f)


def main():
    root = tk.Tk()
    app  = FabricApp(root)   # noqa: F841

    # 아이콘
    try:
        from PIL import Image, ImageTk
        icon_path = config.get_icon_path()
        if os.path.exists(icon_path):
            img = ImageTk.PhotoImage(Image.open(icon_path).resize((32, 32)))
            root.wm_iconphoto(True, img)
    except Exception:
        pass

    _check_update(root)
    _show_patch_notes(root)
    root.mainloop()


if __name__ == "__main__":
    main()
