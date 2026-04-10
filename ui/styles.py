"""ttk 스타일 적용"""
from tkinter import ttk
import tkinter.font as tkFont
import config


def apply_style():
    """메인 창 및 전체 위젯 스타일 설정"""
    c = config.COLORS
    style = ttk.Style()
    style.theme_use("clam")

    style.configure(".",          background=c["DARK_BG"],        foreground=c["TEXT_LIGHT"])
    style.configure("TLabel",     background=c["DARK_BG"],        foreground=c["TEXT_LIGHT"])
    style.configure("TFrame",     background=c["DARK_BG"])
    style.configure("TLabelframe",
                    background=c["DARK_BG"], foreground=c["TEXT_LIGHT"])
    style.configure("TLabelframe.Label",
                    background=c["DARK_BG"], foreground=c["TEXT_LIGHT"])
    style.configure("TEntry",
                    fieldbackground=c["LIGHTER_DARK_BG"],
                    foreground=c["TEXT_LIGHT"], borderwidth=1, relief="solid")
    style.map("TEntry", fieldbackground=[("focus", c["LIGHTER_DARK_BG"])])
    style.configure("TCombobox",
                    fieldbackground=c["LIGHTER_DARK_BG"],
                    foreground=c["TEXT_LIGHT"],
                    selectbackground=c["LIGHTER_DARK_BG"],
                    selectforeground=c["TEXT_LIGHT"])
    style.map("TCombobox", fieldbackground=[("readonly", c["LIGHTER_DARK_BG"])])
    style.configure("TButton",
                    background=c["PRIMARY_BLUE"], foreground="white",
                    font=("맑은 고딕", 9, "bold"),
                    borderwidth=0, focusthickness=3, focuscolor=c["ACCENT_BLUE"])
    style.map("TButton",
              background=[("active", c["BUTTON_HOVER"]), ("pressed", c["BUTTON_ACTIVE"])],
              foreground=[("active", "white"),           ("pressed", "white")])
    style.configure("TCheckbutton",
                    background=c["DARK_BG"], foreground=c["TEXT_LIGHT"])
    style.map("TCheckbutton", background=[("active", c["DARK_BG"])])
    style.configure("Vertical.TScrollbar",
                    background=c["LIGHTER_DARK_BG"], troughcolor=c["DARK_BG"], borderwidth=0)
    style.map("Vertical.TScrollbar",   background=[("active", c["ACCENT_BLUE"])])
    style.configure("Horizontal.TScrollbar",
                    background=c["LIGHTER_DARK_BG"], troughcolor=c["DARK_BG"], borderwidth=0)
    style.map("Horizontal.TScrollbar", background=[("active", c["ACCENT_BLUE"])])
    style.configure("Treeview.Heading",
                    font=("맑은 고딕", 10, "bold"),
                    background=c["TREEVIEW_HEADER_BG"],
                    foreground=c["TEXT_LIGHT"], relief="flat")
    style.map("Treeview.Heading", background=[("active", c["ACCENT_BLUE"])])
    style.configure("Treeview",
                    font=("맑은 고딕", 9), rowheight=25,
                    background=c["TREEVIEW_ROW_EVEN"],
                    foreground=c["TEXT_LIGHT"],
                    fieldbackground=c["TREEVIEW_ROW_EVEN"],
                    borderwidth=0, relief="flat")
    style.map("Treeview",
              background=[("selected", c["TREEVIEW_SELECTED_BG"])],
              foreground=[("selected", c["TREEVIEW_SELECTED_FG"])])


def get_tree_fonts():
    """Treeview 너비 계산용 폰트 반환"""
    return (
        tkFont.Font(family="맑은 고딕", size=9),
        tkFont.Font(family="맑은 고딕", size=10, weight="bold"),
    )
