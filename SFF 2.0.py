import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import sqlite3
import os
from datetime import datetime
import shutil
import re
import sys 
from PIL import Image, ImageTk 
import tkinter.font as tkFont # 폰트 측정용 모듈 임포트

class FabricApp:
    def __init__(self, master):
        self.master = master
        master.title("S&C FABRIC FINDER") 
        master.geometry("1300x750")
        
        # --- 화이트 모드 컨셉 색상 팔레트 ---
        self.GEMINI_COLORS = {
            "PRIMARY_BLUE": "#2e39ff",       # 요청하신 버튼 색상
            "DARK_BG": "#FFFFFF",            # 흰색 배경
            "LIGHTER_DARK_BG": "#F0F0F0",    # 입력 필드 등 약간 어두운 흰색
            "TEXT_LIGHT": "#333333",         # 어두운 회색 텍스트
            "ACCENT_BLUE": "#6a7bff",        # 악센트 색상 (밝은 파랑)
            "BUTTON_HOVER": "#4a57ff",       # 버튼 호버 색상
            "BUTTON_ACTIVE": "#1a25d0",      # 버튼 활성화 색상
            "TREEVIEW_HEADER_BG": "#E0E0E0", # 트리뷰 헤더 배경
            "TREEVIEW_ROW_EVEN": "#FFFFFF",  # 트리뷰 짝수 행 배경
            "TREEVIEW_ROW_ODD": "#F8F8F8",   # 트리뷰 홀수 행 배경
            "TREEVIEW_SELECTED_BG": "#C0D9FF", # 트리뷰 선택된 행 배경 (밝은 파랑)
            "TREEVIEW_SELECTED_FG": "#000000", # 트리뷰 선택된 행 텍스트 (검정)
        }

        master.configure(bg=self.GEMINI_COLORS["DARK_BG"]) # 메인 창 배경색을 밝은 톤으로 설정

        # --- 시각적 테마 적용 ---
        style = ttk.Style()
        style.theme_use('clam') 
        
        # 기본 위젯 스타일 설정
        style.configure('.', background=self.GEMINI_COLORS["DARK_BG"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
        style.configure('TLabel', background=self.GEMINI_COLORS["DARK_BG"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
        style.configure('TFrame', background=self.GEMINI_COLORS["DARK_BG"])
        style.configure('TLabelframe', background=self.GEMINI_COLORS["DARK_BG"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
        style.configure('TLabelframe.Label', background=self.GEMINI_COLORS["DARK_BG"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
        style.configure('TEntry', fieldbackground=self.GEMINI_COLORS["LIGHTER_DARK_BG"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"], borderwidth=1, relief="solid")
        style.map('TEntry', fieldbackground=[('focus', self.GEMINI_COLORS["LIGHTER_DARK_BG"])]) # 포커스 시 배경색 유지
        style.configure('TCombobox', fieldbackground=self.GEMINI_COLORS["LIGHTER_DARK_BG"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"], selectbackground=self.GEMINI_COLORS["LIGHTER_DARK_BG"], selectforeground=self.GEMINI_COLORS["TEXT_LIGHT"])
        style.map('TCombobox', fieldbackground=[('readonly', self.GEMINI_COLORS["LIGHTER_DARK_BG"])])
        
        # 버튼 스타일
        style.configure('TButton', 
                        background=self.GEMINI_COLORS["PRIMARY_BLUE"], 
                        foreground='white', 
                        font=('맑은 고딕', 9, 'bold'),
                        borderwidth=0,
                        focusthickness=3,
                        focuscolor=self.GEMINI_COLORS["ACCENT_BLUE"])
        style.map('TButton', 
                  background=[('active', self.GEMINI_COLORS["BUTTON_HOVER"]), 
                              ('pressed', self.GEMINI_COLORS["BUTTON_ACTIVE"])],
                  foreground=[('active', 'white'), ('pressed', 'white')])

        # 체크버튼 스타일
        style.configure('TCheckbutton', background=self.GEMINI_COLORS["DARK_BG"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
        style.map('TCheckbutton', background=[('active', self.GEMINI_COLORS["DARK_BG"])]) # 활성화 시 배경색 유지

        # 스크롤바 스타일 (선택적으로 조정)
        style.configure('Vertical.TScrollbar', background=self.GEMINI_COLORS["LIGHTER_DARK_BG"], troughcolor=self.GEMINI_COLORS["DARK_BG"], borderwidth=0)
        style.map('Vertical.TScrollbar', background=[('active', self.GEMINI_COLORS["ACCENT_BLUE"])])
        style.configure('Horizontal.TScrollbar', background=self.GEMINI_COLORS["LIGHTER_DARK_BG"], troughcolor=self.GEMINI_COLORS["DARK_BG"], borderwidth=0)
        style.map('Horizontal.TScrollbar', background=[('active', self.GEMINI_COLORS["ACCENT_BLUE"])])

        # Treeview 스타일
        style.configure("Treeview.Heading", 
                        font=('맑은 고딕', 10, 'bold'), 
                        background=self.GEMINI_COLORS["TREEVIEW_HEADER_BG"], 
                        foreground=self.GEMINI_COLORS["TEXT_LIGHT"],
                        relief="flat") # 헤더 배경색 및 텍스트 색상
        style.map("Treeview.Heading", 
                  background=[('active', self.GEMINI_COLORS["ACCENT_BLUE"])]) # 헤더 활성화 시 색상

        style.configure("Treeview", 
                        font=('맑은 고딕', 9), 
                        rowheight=25,
                        background=self.GEMINI_COLORS["TREEVIEW_ROW_EVEN"], # 기본 배경색
                        foreground=self.GEMINI_COLORS["TEXT_LIGHT"], # 기본 텍스트 색상
                        fieldbackground=self.GEMINI_COLORS["TREEVIEW_ROW_EVEN"], # 필드 배경색
                        borderwidth=0,
                        relief="flat")
        style.map("Treeview", 
                  background=[('selected', self.GEMINI_COLORS["TREEVIEW_SELECTED_BG"])], # 선택된 행 배경색
                  foreground=[('selected', self.GEMINI_COLORS["TREEVIEW_SELECTED_FG"])]) # 선택된 행 텍스트 색상
        
        # Treeview 행 별 색상 설정 (alternating row colors)
        self.main_tree_tag_config_set = False # 태그 설정 여부 플래그
        self.selected_tree_tag_config_set = False # 태그 설정 여부 플래그

        # Treeview 폰트 객체 가져오기 (너비 계산용)
        self.treeview_font = tkFont.Font(family='맑은 고딕', size=9)
        self.treeview_heading_font = tkFont.Font(family='맑은 고딕', size=10, weight='bold')

        # --- 설정 상수 ---
        self.SETTINGS = {
            # DB 경로 설정: 패키징 여부에 따라 경로를 다르게 설정
            "DB_PATH": os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fabrics.db') if not getattr(sys, 'frozen', False) else os.path.join(os.path.dirname(sys.executable), 'fabrics.db'),
            "COLUMNS": [ # UI에 표시될 컬럼명 (순서 포함)
                "날짜", "시즌", "브랜드 및 제안처", "담당자", "스타일 넘버", "업체명", "제품명", "S&C 원단명",
                "혼용률", "원단스펙", "원단 무게", 
                "폭(IN)", "제시 폭", "축률 경사", "축률 위사", "원가(YDS)", 
                "RMB(yds)", 
                "RMB(M)", 
                "전달가격", "마진(%)", 
                "재고 및 running"
            ],
            # 실제 DB 컬럼명과 UI 컬럼명 매핑 (DB에서 로드 후 DataFrame 컬럼명 변경용)
            # key: 실제 DB 컬럼명, value: UI에 표시될 컬럼명
            "DB_UI_COL_MAP": {
                "원단 무게 (AW)": "원단 무게",
                "공장 가격(YDS)": "원가(YDS)",
                "인민폐(YD)": "RMB(yds)",
                "인민폐(M)": "RMB(M)",
                "이득률": "마진(%)",
                "원단명": "제품명" # '제품명' UI 컬럼에 대한 DB 컬럼명 매핑 추가
            },
            # 이 리스트의 컬럼명은 UI 컬럼명입니다.
            "NUMERIC_COLS_FOR_STORAGE": [
                "원단 무게", "폭(IN)",
                "축률 경사", "축률 위사", "원가(YDS)", 
                "RMB(yds)", "RMB(M)", 
                "전달가격", "제시 폭"
            ],
            "NUMERIC_COLS_FOR_DECIMAL_DISPLAY": [
                "폭(IN)", "축률 경사", "축률 위사", "RMB(yds)", "RMB(M)", 
                "원단 무게"
            ],
            "CURRENCY_COLS_DISPLAY": ["원가(YDS)", "전달가격"], 
            "PERCENT_COLS_DISPLAY": ["마진(%)"], 
            
            "ALWAYS_HIDDEN_COLS": [
                "축률 경사", "축률 위사"
            ],
            "COMPACT_MODE_TOGGLE_COLS": [
                "폭(IN)", "RMB(yds)", "RMB(M)" 
            ],
            "FLEXIBLE_COLUMN_FOR_STRETCH": "S&C 원단명" # 화면이 남을 때 늘어날 컬럼
        }

        self.df = None 
        self.current_displayed_df = None 
        self.selected_rows_original_data = [] 
        self.compact_mode_var = tk.BooleanVar(value=False) 
        self.resize_timer = None # Debounce 타이머 초기화
        self.last_exchange_rate = 0.145  # 마지막 사용 환율 기본값

        self._initialize_db()
        self._create_widgets()
        self._load_data()
        self._toggle_compact_mode()
        self._auto_backup_to_onedrive()  # 첫 실행 시 OneDrive 자동 백업

    def _initialize_db(self):
        db_dir = os.path.dirname(self.SETTINGS["DB_PATH"])
        os.makedirs(db_dir, exist_ok=True)
        conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
        try:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS proposals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fabric_rowid INTEGER,
                    날짜 TEXT,
                    브랜드 TEXT,
                    시즌 TEXT,
                    전달가격 TEXT,
                    담당자 TEXT,
                    제안결과 TEXT,
                    메모 TEXT
                )
            ''')
            # 새로 추가된 컬럼 자동 안전장치
            cur = conn.cursor()
            cur.execute('PRAGMA table_info(fabrics)')
            existing = [r[1] for r in cur.fetchall()]
            for col in ['담당자', '시즌', '채택여부']:
                if col not in existing:
                    cur.execute(f'ALTER TABLE fabrics ADD COLUMN "{col}" TEXT DEFAULT ""')
            conn.commit()
        finally:
            conn.close()

    def _create_widgets(self):
        # 검색 프레임
        search_frame = ttk.Frame(self.master, padding="10 10 10 0") 
        search_frame.pack(fill="x")
        self.search_column = ttk.Combobox(
            search_frame, values=["전체"] + self.SETTINGS["COLUMNS"],
            state="readonly", width=15
        )
        self.search_column.set("전체")
        self.search_column.grid(row=0, column=0, padx=5, pady=5)

        self.search_entry = ttk.Entry(search_frame, width=40)
        self.search_entry.grid(row=0, column=1, padx=5, pady=5)
        self.search_entry.bind("<Return>", self._search_data)
        self.search_entry.bind("<KeyRelease>", self._on_key_release)

        ttk.Button(search_frame, text="검색", command=self._search_data).grid(
            row=0, column=2, padx=5, pady=5
        )
        self.realtime_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            search_frame, text="실시간 검색", variable=self.realtime_var
        ).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Checkbutton(
            search_frame, text="간략 모드", variable=self.compact_mode_var,
            command=self._toggle_compact_mode
        ).grid(row=0, column=4, padx=5, pady=5)

        # 시즌 필터
        ttk.Label(search_frame, text="시즌:").grid(row=0, column=5, padx=(15,2), pady=5)
        self.season_var = tk.StringVar(value="전체")
        self.season_combo = ttk.Combobox(
            search_frame, textvariable=self.season_var,
            values=["전체"],
            state="readonly", width=8
        )
        self.season_combo.grid(row=0, column=6, padx=5, pady=5)
        self.season_combo.bind("<<ComboboxSelected>>", self._search_data)
        ttk.Button(search_frame, text="필터 초기화", command=self._reset_filters).grid(
            row=0, column=7, padx=5, pady=5
        )

        # 상단 버튼 (핵심 기능만)
        top_button_frame = ttk.Frame(self.master, padding="10 0") 
        top_button_frame.pack(fill="x")
        ttk.Button(top_button_frame, text="신규 제안", command=self._open_form_for_proposal).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(top_button_frame, text="단일 추가", command=lambda: self._open_form("add")).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(top_button_frame, text="엑셀 가져오기", command=self._import_excel).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(top_button_frame, text="시즌 채택 현황", command=self._open_adoption_viewer).grid(row=0, column=3, padx=5, pady=5)
        ttk.Label(top_button_frame, text="※ 수정 · 삭제 · 채택은 우클릭",
                  foreground="#888888", font=('맑은 고딕', 8)).grid(row=0, column=4, padx=15)

        # ── 메인 콘텐츠 ──
        content_frame = ttk.Frame(self.master)
        content_frame.pack(expand=True, fill="both", padx=5)

        # 메인 트리뷰
        main_tree_frame = ttk.Frame(content_frame, padding="5 5 5 0")
        main_tree_frame.pack(expand=True, fill="both")
        self.main_tree = ttk.Treeview(main_tree_frame, columns=self.SETTINGS["COLUMNS"], show="headings")
        self.main_tree.pack(side="left", expand=True, fill="both")
        vsb = ttk.Scrollbar(main_tree_frame, orient="vertical", command=self.main_tree.yview)
        vsb.pack(side="right", fill="y")
        self.main_tree.configure(yscrollcommand=vsb.set)
        
        for col in self.SETTINGS["COLUMNS"]:
            self.main_tree.heading(col, text=col, anchor="center", 
                                   command=lambda c=col: self._sort_treeview(self.main_tree, c)) 
            self.main_tree.column(col, width=100, anchor="center", stretch=False, minwidth=50) 

        self.main_tree.bind("<Double-1>", self._add_to_selected)
        self.main_tree.bind("<Button-3>", self._show_context_menu)
        self.main_tree.bind("<Configure>", lambda e: self._on_treeview_configure(e.widget))

        # 선택된 데이터 트리뷰
        selected_frame = ttk.LabelFrame(content_frame, text="선택된 데이터 목록", padding="5")
        selected_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        self.selected_tree = ttk.Treeview(selected_frame, columns=self.SETTINGS["COLUMNS"], show="headings")
        self.selected_tree.pack(side="left", expand=True, fill="both")
        sel_vsb = ttk.Scrollbar(selected_frame, orient="vertical", command=self.selected_tree.yview)
        sel_vsb.pack(side="right", fill="y")
        self.selected_tree.configure(yscrollcommand=sel_vsb.set)

        for col in self.SETTINGS["COLUMNS"]:
            self.selected_tree.heading(col, text=col, anchor="center")
            self.selected_tree.column(col, width=100, anchor="center", stretch=False, minwidth=50) 

        self.selected_tree.bind("<Double-1>", self._remove_from_selected)
        self.selected_tree.bind("<Configure>", lambda e: self._on_treeview_configure(e.widget))

        # 하단 버튼
        bottom_button_frame = ttk.Frame(content_frame, padding="0 0 5 8")
        bottom_button_frame.pack(fill="x")
        ttk.Button(bottom_button_frame, text="선택 엑셀 저장", command=self._save_selected_to_excel).grid(row=0, column=0, padx=5, pady=5)
        ttk.Button(bottom_button_frame, text="라벨 저장", command=self._save_label).grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(bottom_button_frame, text="선택 해제", command=self._clear_selected).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(bottom_button_frame, text="DB 백업", command=self._backup_db).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(bottom_button_frame, text="원단 정보 내보내기", command=self._export_all_selected_data_to_excel).grid(row=0, column=4, padx=5, pady=5)
        ttk.Button(bottom_button_frame, text="전체 원단 정보 내보내기", command=self._export_all_displayed_data_to_excel).grid(row=0, column=5, padx=5, pady=5)

    def _on_treeview_configure(self, treeview_widget):
        """
        Treeview의 Configure 이벤트를 디바운스하여 _adjust_treeview_column_widths를 호출합니다.
        """
        # 기존 타이머가 있다면 취소
        if self.resize_timer:
            self.master.after_cancel(self.resize_timer)
        
        # 100ms 후에 _adjust_treeview_column_widths 호출을 예약
        # 어떤 Treeview가 이벤트를 발생시켰는지 확인하여 적절한 데이터를 전달
        if treeview_widget == self.main_tree:
            data_to_pass = self.current_displayed_df
        elif treeview_widget == self.selected_tree:
            data_to_pass = pd.DataFrame(self.selected_rows_original_data)
        else:
            data_to_pass = pd.DataFrame() # Fallback

        self.resize_timer = self.master.after(100, lambda: self._adjust_treeview_column_widths(treeview_widget, data_to_pass))

    def _adjust_treeview_column_widths(self, treeview, df_data):
        """
        Treeview의 컬럼 너비를 헤더 텍스트와 데이터 내용에 맞춰 동적으로 조정합니다.
        화면이 남을 경우 특정 컬럼을 늘려 빈 공간을 채웁니다.
        """
        # 데이터가 없거나 비어있을 경우, 기본 너비로 설정하고 stretch=True로 공간을 채움
        if df_data is None or df_data.empty: 
            for col_name in self.SETTINGS["COLUMNS"]:
                treeview.column(col_name, width=100, stretch=True, minwidth=50) 
            # self._toggle_column_visibility(treeview) # 숨김 컬럼 다시 적용 - REMOVED
            return

        padding = 20 # 여백 추가
        calculated_widths = {}
        total_optimal_width = 0

        # 컬럼별 최대 너비 제한 (좁게 고정할 컬럼)
        MAX_WIDTHS = {
            "날짜":         90,
            "시즌":         55,
            "담당자":       70,
            "스타일 넘버":  90,
            "업체명":       80,
            "원단 무게":    65,
            "폭(IN)":       60,
            "제시 폭":      60,
            "축률 경사":    60,
            "축률 위사":    60,
            "원가(YDS)":    80,
            "RMB(yds)":     75,
            "RMB(M)":       75,
            "전달가격":     80,
            "마진(%)":      85,
        }

        # 1. 각 컬럼의 최적 너비 계산 (stretch=False 가정)
        for col_name in self.SETTINGS["COLUMNS"]:
            header_width = self.treeview_heading_font.measure(col_name)
            max_content_width = 0
            
            # df_data는 UI 컬럼명을 가집니다.
            if col_name in df_data.columns: 
                # 데이터프레임이 비어있지 않은 경우에만 데이터 내용 너비 계산
                if not df_data.empty:
                    for item in df_data[col_name]: 
                        formatted_item = self._format_data_for_display(item, col_name) 
                        content_width = self.treeview_font.measure(formatted_item)
                        if content_width > max_content_width:
                            max_content_width = content_width
            
            optimal_width = max(header_width, max_content_width) + padding
            # 최대 너비 제한 적용
            if col_name in MAX_WIDTHS:
                final_width = min(optimal_width, MAX_WIDTHS[col_name])
                final_width = max(final_width, 50)
            else:
                final_width = max(optimal_width, 50)

            calculated_widths[col_name] = final_width
            total_optimal_width += final_width
        
        # 2. Treeview의 실제 가시 영역 너비 가져오기
        # winfo_width()는 위젯이 실제로 화면에 차지하는 픽셀 너비를 반환합니다.
        # Treeview가 아직 렌더링되지 않아 너비가 1로 나올 수 있으므로, 부모 프레임 너비를 참조하거나 기본값 사용
        treeview_actual_width = treeview.winfo_width()
        if treeview_actual_width <= 1: 
            # 부모 프레임의 너비를 참조하여 초기 너비를 추정 (오차를 위해 여백 고려)
            parent_width = treeview.master.winfo_width()
            if parent_width > 1:
                treeview_actual_width = parent_width - 20 # 프레임 패딩 고려
            else: # 부모 프레임도 작으면 임의의 적절한 기본값
                treeview_actual_width = 1200 

        # 3. 컬럼 너비 적용 및 공간 채우기 로직
        if total_optimal_width < treeview_actual_width:
            # 컬럼들의 총 너비가 Treeview의 실제 너비보다 작으면, 빈 공간이 생김
            remaining_space = treeview_actual_width - total_optimal_width
            
            # 유연하게 늘어날 컬럼 지정
            flexible_col = self.SETTINGS["FLEXIBLE_COLUMN_FOR_STRETCH"]
            
            # 유연한 컬럼이 존재하고, 숨김 컬럼이 아닌 경우에만 늘려줌
            if flexible_col in calculated_widths and flexible_col not in self.SETTINGS["ALWAYS_HIDDEN_COLS"] and \
               not (self.compact_mode_var.get() and flexible_col in self.SETTINGS["COMPACT_MODE_TOGGLE_COLS"]):
                
                # 유연한 컬럼에 남은 공간을 추가하고 stretch=True
                treeview.column(flexible_col, width=calculated_widths[flexible_col] + remaining_space, stretch=True, minwidth=50)
                # 나머지 컬럼들은 계산된 너비로 stretch=False
                for col_name in self.SETTINGS["COLUMNS"]:
                    if col_name != flexible_col:
                        treeview.column(col_name, width=calculated_widths[col_name], stretch=False, minwidth=50)
            else: # 유연한 컬럼이 없거나 숨겨져야 하는 경우, 모든 컬럼을 stretch=True로 하여 공간을 채움 (최후의 수단)
                for col_name in self.SETTINGS["COLUMNS"]:
                    treeview.column(col_name, width=calculated_widths[col_name], stretch=True, minwidth=50)
        else:
            # 컬럼들의 총 너비가 Treeview의 실제 너비보다 크거나 같으면, stretch=False로 고정하고 스크롤바 사용
            for col_name in self.SETTINGS["COLUMNS"]:
                treeview.column(col_name, width=calculated_widths[col_name], stretch=False, minwidth=50)
        
        # 간략 모드에 따라 숨겨야 할 컬럼은 다시 숨김 처리 (너비 조절 후 가시성만 조정)
        # self._toggle_column_visibility(treeview) # 이 부분은 _toggle_compact_mode에서 직접 처리하거나,
                                                # _populate_selected_tree에서 간접적으로 처리되므로 제거

    def _get_db_col_name(self, ui_col_name):
        """
        UI 컬럼명에 해당하는 실제 DB 컬럼명을 반환합니다.
        매핑에 없으면 UI 컬럼명과 DB 컬럼명이 동일하다고 가정합니다.
        """
        # DB_UI_COL_MAP은 {실제 DB 컬럼명: UI에 표시될 컬럼명} 형태입니다.
        # 따라서 value(UI 컬럼명)를 찾아서 key(DB 컬럼명)를 반환해야 합니다.
        for db_name, ui_name in self.SETTINGS["DB_UI_COL_MAP"].items():
            if ui_name == ui_col_name:
                return db_name
        return ui_col_name # 매핑에 없으면 UI 컬럼명 자체가 DB 컬럼명임

    # 숫자만 추출해서 float 반환
    def _clean_numeric_string(self, s):
        if s is None or pd.isna(s):
            return None
        s_str = str(s).strip()
        if not s_str:
            return None
        cleaned = re.sub(r'[^\d.\-]+', '', s_str)
        if cleaned.count('-') > 1 or (cleaned.count('-') == 1 and not cleaned.startswith('-')):
            return None
        if cleaned.count('.') > 1 or cleaned in {'.', '-'}:
            return None
        try:
            return float(cleaned)
        except:
            return None

    def _compute_proposal(self, width_in_val, raw_prop_val):
        val = self._clean_numeric_string(raw_prop_val)
        if val is not None:
            return val
        w = self._clean_numeric_string(width_in_val)
        return (w * 0.92) if w is not None else None

    def _compute_margin(self, trans_price_val, factory_price_val, raw_margin_val):
        m = self._clean_numeric_string(str(raw_margin_val).replace('%',''))
        if m is not None:
            return m
        t = self._clean_numeric_string(trans_price_val)
        f = self._clean_numeric_string(factory_price_val)
        # 판매가 대비 마진율: (1 - 원가 / 전달가격) × 100
        return ((1 - f / t) * 100) if t not in (None, 0) and f is not None else 0.0

    def _format_data_for_display(self, value, column_name):
        if value is None or pd.isna(value) or (isinstance(value, str) and not value.strip()):
            return ""
        if column_name == "날짜":
            return str(value)
        num = self._clean_numeric_string(value)
        if num is None:
            return str(value)
        if column_name in self.SETTINGS["CURRENCY_COLS_DISPLAY"]:
            return f"${num:.2f}"
        if column_name in self.SETTINGS["PERCENT_COLS_DISPLAY"]:
            if num < 23:
                return f"⚠️ {num:.2f}%"
            elif num > 40:
                return f"✅ {num:.2f}%"
            return f"{num:.2f}%"
        if column_name == "제시 폭":
            return str(int(round(num)))
        if column_name in self.SETTINGS["NUMERIC_COLS_FOR_DECIMAL_DISPLAY"]:
            return f"{num:.2f}"
        return str(value)

    def _process_dataframe_for_storage(self, df_to_process):
        """
        데이터프레임의 컬럼명을 DB 컬럼명 기준으로 처리하고,
        숫자 변환 및 계산을 수행합니다.
        이 함수에 전달되는 df_to_process는 이미 DB 컬럼명을 가지고 있어야 합니다.
        """
        df = df_to_process.copy()
        
        # 모든 값을 None 또는 빈 문자열 처리
        for col in df.columns:
            df[col] = df[col].apply(lambda x: None if pd.isna(x) or (isinstance(x,str) and not x.strip()) else x)
        
        # 날짜 형식 변환 (DB 컬럼명은 '날짜'로 가정)
        if '날짜' in df.columns:
            df['날짜'] = df['날짜'].apply(
                lambda x: None if x is None else pd.to_datetime(x,errors='coerce').strftime('%Y-%m-%d') 
                                 if pd.notna(pd.to_datetime(x,errors='coerce')) else None
            )

        # 숫자형 컬럼 처리 (DB 컬럼명 기준으로)
        for ui_col in self.SETTINGS["NUMERIC_COLS_FOR_STORAGE"]:
            db_col = self._get_db_col_name(ui_col)
            if db_col in df.columns:
                df[db_col] = df[db_col].map(self._clean_numeric_string)
        
        # 제시 폭 계산 로직 (DB 컬럼명 기준으로)
        db_폭_in = self._get_db_col_name("폭(IN)")
        db_제시_폭 = self._get_db_col_name("제시 폭")
        if db_제시_폭 in df.columns and db_폭_in in df.columns:
            df[db_제시_폭] = df.apply(
                lambda r: (str(int(round(self._compute_proposal(r.get(db_폭_in), r.get(db_제시_폭)))))
                           if self._compute_proposal(r.get(db_폭_in), r.get(db_제시_폭)) is not None else None),
                axis=1
            )

        # 마진(%) 계산 로직 (DB 컬럼명 기준으로)
        db_전달가격 = self._get_db_col_name("전달가격")
        db_원가_yds = self._get_db_col_name("원가(YDS)")
        db_마진_percent = self._get_db_col_name("마진(%)")
        
        if db_마진_percent in df.columns and db_전달가격 in df.columns and db_원가_yds in df.columns:
            df[db_마진_percent] = df.apply(
                lambda r: (f"{self._compute_margin(r.get(db_전달가격), r.get(db_원가_yds), r.get(db_마진_percent)):.2f}%" 
                           if (r.get(db_전달가격) is not None and r.get(db_원가_yds) is not None and r.get(db_원가_yds) != 0) or \
                              (r.get(db_마진_percent) is not None and str(r.get(db_마진_percent)).strip())
                           else None),
                axis=1
            )

        # '재고 및 running' 컬럼 처리 (DB 컬럼명은 UI와 동일하다고 가정)
        if '재고 및 running' in df.columns:
            df['재고 및 running'] = df['재고 및 running'].apply(
                lambda x: None if (x is None or (isinstance(x, float) and pd.isna(x)) 
                                   or str(x).strip().lower() in ('none', 'nan', '')) else str(x).strip()
            )
        return df

    def _load_data(self):
        db = self.SETTINGS["DB_PATH"]
        if not os.path.exists(db):
            messagebox.showwarning("DB 없음", f"데이터베이스 파일을 찾을 수 없습니다:\n{db}")
            self.df = pd.DataFrame(columns=["_rowid"]+self.SETTINGS["COLUMNS"])
            conn = sqlite3.connect(db)
            try:
                # DB에 저장될 컬럼명 목록을 생성합니다.
                db_cols_for_table_create = [self._get_db_col_name(c) for c in self.SETTINGS["COLUMNS"]]
                cols_sql = ", ".join(f'"{c}" TEXT' for c in db_cols_for_table_create)
                conn.execute(f'CREATE TABLE IF NOT EXISTS fabrics ({cols_sql})')
                conn.commit()
                messagebox.showinfo("DB 생성", f"새로운 데이터베이스 파일이 생성되었습니다:\n{db}")
            except Exception as e:
                messagebox.showerror("DB 생성 오류", f"데이터베이스 테이블 생성 중 오류 발생: {e}")
            finally:
                conn.close()
            self._populate_main_tree(self.df)
            self.current_displayed_df = self.df.copy() 
            return

        conn = sqlite3.connect(db)
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(fabrics)")
            columns_info = cursor.fetchall()
            existing_col_names = [col[1] for col in columns_info]

            old_col_name_style = "원단 번호" # 이전 UI 컬럼명 (DB에 있을 수 있는 이름)
            new_col_name_style = "스타일 넘버" # 현재 UI 컬럼명
            old_db_name_style = self._get_db_col_name(old_col_name_style) # 실제 DB에 있을 수 있는 이름 (예: "원단 번호")
            new_db_name_style = self._get_db_col_name(new_col_name_style) # 실제 DB에 저장될 이름 (예: "스타일 넘버")

            # DB에 '원단 번호' 컬럼이 있고 '스타일 넘버' 컬럼이 없을 때만 이름 변경 시도
            if old_db_name_style in existing_col_names and new_db_name_style not in existing_col_names:
                try:
                    cursor.execute(f'ALTER TABLE fabrics RENAME COLUMN "{old_db_name_style}" TO "{new_db_name_style}"')
                    conn.commit()
                    messagebox.showinfo("DB 업데이트", f"데이터베이스 컬럼 '{old_db_name_style}'이(가) '{new_db_name_style}'(으)로 성공적으로 변경되었습니다.")
                except sqlite3.OperationalError as e:
                    messagebox.showerror("DB 컬럼 변경 오류", f"데이터베이스 컬럼 이름 변경 중 오류 발생: {e}\n"
                                                           "데이터베이스 파일이 잠겨있거나 다른 프로세스에서 사용 중일 수 있습니다.")
                    pass 
            
            df = pd.read_sql("SELECT rowid AS _rowid, * FROM fabrics", conn)
            
            # 로드된 DataFrame의 컬럼명을 UI 표시용 컬럼명으로 변경
            # DB_UI_COL_MAP을 사용하여 실제 DB 컬럼명(key)을 UI 컬럼명(value)으로 변경
            df.rename(columns=self.SETTINGS["DB_UI_COL_MAP"], inplace=True)
            
            # 모든 예상 UI 컬럼이 존재하도록 재인덱싱하고, 없는 컬럼은 None으로 채웁니다.
            # 이는 DB에 없던 새로운 컬럼이 UI에 추가되었을 때를 대비합니다.
            df = df.reindex(columns=["_rowid"] + self.SETTINGS["COLUMNS"], fill_value=None)

        except pd.io.sql.DatabaseError as e:
            messagebox.showerror("DB 읽기 오류", f"데이터베이스에서 데이터를 읽는 중 오류 발생: {e}\n"
                                               "데이터베이스 파일이 손상되었거나 테이블 구조가 올바르지 않을 수 있습니다.")
            self.df = pd.DataFrame(columns=["_rowid"] + self.SETTINGS["COLUMNS"])
            self._populate_main_tree(self.df)
            self.current_displayed_df = self.df.copy()
            return
        finally:
            conn.close()

        df['_rowid'] = df['_rowid'].astype(int)
        self.df = df

        # 로드된 데이터프레임 (현재 UI 컬럼명)을 DB 컬럼명으로 다시 변환하여 _process_dataframe_for_storage에 전달
        # _process_dataframe_for_storage는 DB 컬럼명으로 작동해야 합니다.
        temp_df_for_processing = self.df.copy()
        reverse_map = {v: k for k, v in self.SETTINGS["DB_UI_COL_MAP"].items()}
        temp_df_for_processing.rename(columns=reverse_map, inplace=True)
        
        # db_cols_ordered_for_processing: _process_dataframe_for_storage가 기대하는 DB 컬럼명의 순서
        db_cols_ordered_for_processing = [self._get_db_col_name(c) for c in self.SETTINGS["COLUMNS"]]
        temp_df_for_processing = temp_df_for_processing.reindex(columns=["_rowid"] + db_cols_ordered_for_processing, fill_value=None)

        # _process_dataframe_for_storage를 호출하여 데이터 정제 및 재계산
        processed_df_db_names = self._process_dataframe_for_storage(temp_df_for_processing)

        # 처리된 데이터프레임을 다시 UI 컬럼명으로 변경하여 self.df에 저장
        processed_df_db_names.rename(columns=self.SETTINGS["DB_UI_COL_MAP"], inplace=True)
        self.df = processed_df_db_names.reindex(columns=["_rowid"] + self.SETTINGS["COLUMNS"], fill_value=None)


        self._reload_treeviews()

    def _refresh_season_list(self):
        """시즌 컬럼에서 값을 추출해 오름차순으로 정렬"""
        if self.df is None or self.df.empty:
            return
        seasons = sorted(set(
            v.strip() for v in self.df["시즌"].dropna().astype(str)
            if v.strip() and v.strip().lower() != 'none'
        ))
        self.season_combo["values"] = ["전체"] + seasons

    def _reload_treeviews(self):
        self._refresh_season_list()
        self._search_data() 
        self._populate_selected_tree() 
        self._toggle_compact_mode() 

    def _populate_main_tree(self, df_to_display):
        self.main_tree.delete(*self.main_tree.get_children())

        # 채택여부 DB에서 직접 읽기
        adopted_ids = set()
        try:
            conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
            rows_adopted = conn.execute('SELECT rowid FROM fabrics WHERE 채택여부="채택"').fetchall()
            adopted_ids = {r[0] for r in rows_adopted}
            conn.close()
        except:
            pass

        for i, row in df_to_display.iterrows():
            iid = str(row['_rowid'])
            vals = [self._format_data_for_display(row[c], c) for c in self.SETTINGS["COLUMNS"]]
            if int(row['_rowid']) in adopted_ids:
                tag = 'adopted'
            else:
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.main_tree.insert("", "end", iid=iid, values=vals, tags=(tag,))

        if not self.main_tree_tag_config_set:
            self.main_tree.tag_configure('evenrow', background=self.GEMINI_COLORS["TREEVIEW_ROW_EVEN"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
            self.main_tree.tag_configure('oddrow', background=self.GEMINI_COLORS["TREEVIEW_ROW_ODD"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
            self.main_tree_tag_config_set = True

        self.main_tree.tag_configure('adopted', background='#d4edda', foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
        self.current_displayed_df = df_to_display.copy()
        # _adjust_treeview_column_widths는 _on_treeview_configure에서 디바운스되어 호출되므로 여기서 직접 호출하지 않음
        # self._adjust_treeview_column_widths(self.main_tree, self.current_displayed_df) 

    def _populate_selected_tree(self):
        self.selected_tree.delete(*self.selected_tree.get_children())
        
        # 선택된 트리뷰의 컬럼 헤더 가시성을 먼저 업데이트
        self._update_selected_tree_headers_visibility()

        last_iid = None 
        for i, row_data_dict in enumerate(self.selected_rows_original_data):
            vals = []
            # 모든 컬럼에 대해 값을 준비하되, 숨겨진 컬럼의 값도 포함
            # Treeview는 width=0으로 설정된 컬럼의 값을 자동으로 숨김 처리함
            for col_name in self.SETTINGS["COLUMNS"]: 
                vals.append(self._format_data_for_display(row_data_dict.get(col_name), col_name))
            
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            last_iid = self.selected_tree.insert("", "end", values=vals, tags=(tag,)) 
        
        if not self.selected_tree_tag_config_set:
            self.selected_tree.tag_configure('evenrow', background=self.GEMINI_COLORS["TREEVIEW_ROW_EVEN"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
            self.selected_tree.tag_configure('oddrow', background=self.GEMINI_COLORS["TREEVIEW_ROW_ODD"], foreground=self.GEMINI_COLORS["TEXT_LIGHT"])
            self.selected_tree_tag_config_set = True

        if last_iid:
            self.selected_tree.see(last_iid)
        
        # _adjust_treeview_column_widths는 _on_treeview_configure에서 디바운스되어 호출되므로 여기서 직접 호출하지 않음
        # self._adjust_treeview_column_widths(self.selected_tree, pd.DataFrame(self.selected_rows_original_data)) 

    def _update_selected_tree_headers_visibility(self):
        """선택된 데이터 트리뷰의 헤더 가시성을 업데이트합니다."""
        is_compact = self.compact_mode_var.get()
        
        # 모든 헤더의 가시성을 설정
        for col_name in self.SETTINGS["COLUMNS"]:
            if col_name in self.SETTINGS["ALWAYS_HIDDEN_COLS"]:
                self.selected_tree.column(col_name, width=0, stretch=False)
            elif col_name in self.SETTINGS["COMPACT_MODE_TOGGLE_COLS"]:
                if is_compact:
                    self.selected_tree.column(col_name, width=0, stretch=False)
                else:
                    self.selected_tree.column(col_name, width=100, stretch=True) # 간략 모드 해제 시 보이게
            else:
                self.selected_tree.column(col_name, width=100, stretch=True) # 기본적으로 보이게

    def _search_data(self, event=None):
        kw = self.search_entry.get().strip().lower()
        col = self.search_column.get()
        season = self.season_var.get()
        df_f = self.df.copy() if self.df is not None else pd.DataFrame(columns=self.SETTINGS["COLUMNS"])

        # 키워드 검색
        if kw:
            if col == "전체":
                mask = pd.Series(False, index=df_f.index)
                for c in self.SETTINGS["COLUMNS"]:
                    mask |= df_f[c].astype(str).fillna('').str.contains(kw, case=False, na=False)
                df_f = df_f[mask]
            else:
                df_f = df_f[df_f[col].astype(str).fillna('').str.contains(kw, case=False, na=False)]

        # 시즌 필터 (시즌 컬럼 직접 비교)
        if season != "전체":
            df_f = df_f[df_f["시즌"].astype(str).str.strip() == season]

        self._populate_main_tree(df_f)

    def _reset_filters(self):
        """검색 및 시즌 필터 초기화"""
        self.search_entry.delete(0, tk.END)
        self.search_column.set("전체")
        self.season_var.set("전체")
        self._search_data()

    def _on_key_release(self, event):
        if self.realtime_var.get():
            self._search_data()

    def _open_form(self, mode, row_id=None, initial_data=None):
        win = tk.Toplevel(self.master)
        titles = {"add":"단일 추가","edit":"데이터 수정","proposal":"신규 제안"}
        win.title(titles[mode])
        win.configure(bg=self.GEMINI_COLORS["DARK_BG"]) # Toplevel 창 배경색
        
        # Toplevel 창의 아이콘 설정 (메인 창과 동일하게)
        try:
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
                icon_path = os.path.join(sys._MEIPASS, 'SFF.png')
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                icon_path = os.path.join(script_dir, 'SFF.png')
            
            if os.path.exists(icon_path):
                original_image = Image.open(icon_path)
                resized_image = original_image.resize((32, 32), Image.Resampling.LANCZOS)
                photo_image = ImageTk.PhotoImage(resized_image)
                win.wm_iconphoto(True, photo_image)
            else:
                print(f"경고: 아이콘 파일 '{icon_path}'을(를) 찾을 수 없습니다. Toplevel 창 아이콘이 설정되지 않습니다.")
        except Exception as e:
            print(f"Toplevel 창 아이콘 설정 중 오류 발생: {e}")

        win.transient(self.master) 
        win.grab_set() 
        win.focus_set() 
        
        entries={}
        memo_text = None  # Text 위젯 (메모 전용)
        for i, col in enumerate(self.SETTINGS["COLUMNS"]):
            tk.Label(win,text=col, bg=self.GEMINI_COLORS["DARK_BG"], fg=self.GEMINI_COLORS["TEXT_LIGHT"]).grid(row=i,column=0,sticky="nw",padx=5,pady=2)
            if col == "메모":
                t = tk.Text(win, width=40, height=4, bg=self.GEMINI_COLORS["LIGHTER_DARK_BG"],
                            fg=self.GEMINI_COLORS["TEXT_LIGHT"], insertbackground=self.GEMINI_COLORS["TEXT_LIGHT"],
                            relief="flat", wrap="word")
                t.grid(row=i, column=1, padx=5, pady=2)
                memo_text = t
                if initial_data and col in initial_data and initial_data[col]:
                    t.insert("1.0", initial_data[col])
            else:
                e=tk.Entry(win,width=40, bg=self.GEMINI_COLORS["LIGHTER_DARK_BG"], fg=self.GEMINI_COLORS["TEXT_LIGHT"], insertbackground=self.GEMINI_COLORS["TEXT_LIGHT"]); e.grid(row=i,column=1,padx=5,pady=2)
                entries[col]=e

                if (mode=="add" or mode=="proposal") and col=="날짜":
                    e.insert(0,datetime.now().strftime('%Y-%m-%d'))
                elif initial_data and col in initial_data:
                    disp=self._format_data_for_display(initial_data[col],col)
                    if not(mode=="proposal" and col in("제시 폭","마진(%)")):
                        e.insert(0,disp)

        # ── 환율 입력란 ──
        exr_row = len(self.SETTINGS["COLUMNS"])
        tk.Label(win, text="환율 (RMB→USD)", bg=self.GEMINI_COLORS["DARK_BG"],
                 fg=self.GEMINI_COLORS["ACCENT_BLUE"], font=('맑은 고딕', 9, 'bold')).grid(
                 row=exr_row, column=0, sticky="w", padx=5, pady=(8,2))
        exr_entry = tk.Entry(win, width=40, bg=self.GEMINI_COLORS["LIGHTER_DARK_BG"],
                             fg=self.GEMINI_COLORS["ACCENT_BLUE"],
                             insertbackground=self.GEMINI_COLORS["TEXT_LIGHT"])
        exr_entry.grid(row=exr_row, column=1, padx=5, pady=(8,2))
        exr_entry.insert(0, str(self.last_exchange_rate))  # 마지막 사용값 기본 적용

        # ── 자동 계산 힌트 라벨 ──
        hint_row = len(self.SETTINGS["COLUMNS"]) + 1
        hint_label = tk.Label(win, text="", bg=self.GEMINI_COLORS["DARK_BG"],
                              fg=self.GEMINI_COLORS["ACCENT_BLUE"], font=('맑은 고딕', 9))
        hint_label.grid(row=hint_row, column=0, columnspan=2, pady=(2, 0))

        def _try_auto_calc(changed_field):
            """환율 체인 자동계산 + 전달가격/마진 역산"""
            RMB_M_TO_YDS = 0.9144
            try:
                # 환율 입력란에서 동적으로 읽기
                exr_str = exr_entry.get().strip()
                RMB_TO_USD = float(exr_str) if exr_str else self.last_exchange_rate

                def get(field):
                    return entries[field].get().replace("$","").replace(",","").replace("%","").strip()
                def setval(field, val):
                    entries[field].delete(0, tk.END)
                    entries[field].insert(0, val)

                rmb_m   = float(get("RMB(M)"))   if get("RMB(M)")   else None
                rmb_yds = float(get("RMB(yds)")) if get("RMB(yds)") else None
                cost    = float(get("원가(YDS)")) if get("원가(YDS)") else None
                price   = float(get("전달가격"))  if get("전달가격")  else None
                margin  = float(get("마진(%)"))   if get("마진(%)")   else None

                hints = []

                # ── RMB(M) 입력 시 ──
                if changed_field == "RMB(M)" and rmb_m:
                    calc_yds = rmb_m * RMB_M_TO_YDS
                    setval("RMB(yds)", f"{calc_yds:.4f}")
                    rmb_yds = calc_yds
                    hints.append(f"RMB(yds) = {rmb_m} × {RMB_M_TO_YDS} = {calc_yds:.4f}")

                # ── RMB(yds) → 원가(YDS) ──
                if changed_field in ("RMB(M)", "RMB(yds)", "환율") and rmb_yds:
                    calc_cost = rmb_yds * RMB_TO_USD
                    setval("원가(YDS)", f"{calc_cost:.2f}")
                    cost = calc_cost
                    hints.append(f"원가(YDS) = {rmb_yds:.4f} × {RMB_TO_USD} = ${calc_cost:.2f}")

                # ── 원가 + 마진 → 전달가격 ──
                if changed_field in ("RMB(M)", "RMB(yds)", "환율", "원가(YDS)", "마진(%)"):
                    if cost and margin is not None and 0 <= margin < 100:
                        calc_price = cost / (1 - margin / 100)
                        setval("전달가격", f"{calc_price:.2f}")
                        hints.append(f"전달가격 = ${cost:.2f} / (1 - {margin:.1f}%) = ${calc_price:.2f}")

                # ── 전달가격 입력 시 → 마진 계산 ──
                elif changed_field == "전달가격":
                    if cost and price and price > 0:
                        calc_margin = (1 - cost / price) * 100
                        setval("마진(%)", f"{calc_margin:.2f}")
                        hints.append(f"마진 = (1 - ${cost:.2f}/${price:.2f}) × 100 = {calc_margin:.2f}%")

                hint_label.config(text="  →  ".join(hints) if hints else "")

            except (ValueError, ZeroDivisionError):
                hint_label.config(text="")

        # 자동계산 바인딩 (환율 포함)
        for field in ("RMB(M)", "RMB(yds)", "원가(YDS)", "마진(%)", "전달가격"):
            entries[field].bind("<FocusOut>", lambda e, f=field: _try_auto_calc(f))
            entries[field].bind("<Return>",   lambda e, f=field: _try_auto_calc(f))
        exr_entry.bind("<FocusOut>", lambda e: _try_auto_calc("환율"))
        exr_entry.bind("<Return>",   lambda e: _try_auto_calc("환율"))


        def save_data():
            # 환율 기억
            try:
                exr_val = float(exr_entry.get().strip())
                self.last_exchange_rate = exr_val
            except:
                pass

            raw_ui_names = {c: entries[c].get() for c in self.SETTINGS["COLUMNS"] if c != "메모"}
            raw_ui_names["메모"] = memo_text.get("1.0", "end-1c").strip() if memo_text else ""
            
            # UI 컬럼명 데이터를 DB 컬럼명 데이터로 변환
            data_for_db = {}
            for ui_col, value in raw_ui_names.items():
                db_col = self._get_db_col_name(ui_col) 
                data_for_db[db_col] = value
            
            # DB 컬럼명으로 구성된 DataFrame 생성
            temp_df_db_names = pd.DataFrame([data_for_db])
            
            # DB 컬럼명으로 DataFrame 처리
            proc = self._process_dataframe_for_storage(temp_df_db_names)
            
            # DB에 저장될 컬럼명의 순서를 UI 컬럼명 순서에 맞춰서 다시 구성
            db_cols_for_storage_ordered = [self._get_db_col_name(c) for c in self.SETTINGS["COLUMNS"]]
            
            # proc DataFrame에서 DB에 저장될 순서대로 값 추출
            vals = [proc.iloc[0][c] for c in db_cols_for_storage_ordered] 
            
            conn=sqlite3.connect(self.SETTINGS["DB_PATH"]); cur=conn.cursor()
            try:
                if mode=="edit" and row_id:
                    clause=",".join(f'"{c}"=?' for c in db_cols_for_storage_ordered) 
                    cur.execute(f'UPDATE fabrics SET {clause} WHERE rowid=?',(*vals,int(row_id)))
                else:
                    cols_sql=",".join(f'"{c}"' for c in db_cols_for_storage_ordered) 
                    ph=",".join("?" for _ in db_cols_for_storage_ordered)
                    cur.execute(f'INSERT INTO fabrics ({cols_sql}) VALUES ({ph})',vals)
                conn.commit()
                messagebox.showinfo("완료","데이터가 저장되었습니다.")
                win.destroy()
                self._load_data()
            except Exception as e:
                messagebox.showerror("오류",f"저장 중 오류: {e}")
            finally:
                conn.close()

        ttk.Button(win,text="저장",command=save_data).grid(row=len(self.SETTINGS["COLUMNS"])+2,columnspan=2,pady=10)

    def _open_form_for_proposal(self):
        sel=self.main_tree.selection()
        if not sel:
            messagebox.showwarning("경고","신규 제안할 항목을 선택하세요.")
            return
        rid=int(sel[0])
        # self.df는 UI 컬럼명을 가지고 있으므로 그대로 전달
        data=self.df[self.df['_rowid']==rid].iloc[0].drop('_rowid').to_dict()
        self._open_form("proposal",initial_data=data)

    def _update_selected_entry(self):
        sel=self.main_tree.selection()
        if not sel:
            messagebox.showwarning("경고","수정할 항목을 선택하세요.")
            return
        rid=int(sel[0])
        # self.df는 UI 컬럼명을 가지고 있으므로 그대로 전달
        data=self.df[self.df['_rowid']==rid].iloc[0].drop('_rowid').to_dict()
        self._open_form("edit",row_id=rid,initial_data=data)

    def _import_excel(self):
        path=filedialog.askopenfilename(filetypes=[("Excel","*.xlsx;*.xls")])
        if not path: return
        engine='openpyxl' if path.lower().endswith('.xlsx') else 'xlrd'
        try:
            df_ex=pd.read_excel(path,dtype=str,engine=engine)
            
            # 이력 컬럼 미리 분리 (원단 데이터 처리 전에 보관)
            PROPOSAL_COLS = ["시즌", "담당자", "제안결과", "메모"]
            proposal_data = {}
            for col in PROPOSAL_COLS:
                if col in df_ex.columns:
                    proposal_data[col] = df_ex[col].tolist()

            # 엑셀 파일 컬럼명을 DB 컬럼명으로 변환하기 위한 역매핑
            reverse_map_for_excel_to_db = {v: k for k, v in self.SETTINGS["DB_UI_COL_MAP"].items()}
            df_ex.rename(columns=reverse_map_for_excel_to_db, inplace=True)

            # DB에 저장될 실제 DB 컬럼명 목록 (UI 컬럼명 순서에 맞춰)
            db_cols_for_reindex = [self._get_db_col_name(c) for c in self.SETTINGS["COLUMNS"]]

            # 모든 예상 DB 컬럼이 존재하도록 재인덱싱하고, 없는 컬럼은 빈 값으로 채웁니다.
            df_ex = df_ex.reindex(columns=db_cols_for_reindex, fill_value="")
            
            missing=[c for c in db_cols_for_reindex if c not in df_ex.columns]
            if missing:
                messagebox.showwarning("경고",f"엑셀 파일에 다음 컬럼이 누락되었습니다: {', '.join(missing)}\n"
                                           "누락된 컬럼은 빈 값으로 처리됩니다.")
        except Exception as e:
            messagebox.showerror("오류",f"엑셀 읽기 실패: {e}")
            return
        
        # df_ex는 이제 DB 컬럼명을 가지고 있으므로 _process_dataframe_for_storage에 바로 전달
        proc=self._process_dataframe_for_storage(df_ex)
        
        conn=sqlite3.connect(self.SETTINGS["DB_PATH"])
        try:
            # 테이블이 없으면 생성 (DB 컬럼명 기준으로)
            db_cols_for_table_create = [self._get_db_col_name(c) for c in self.SETTINGS["COLUMNS"]]
            cols_sql = ", ".join(f'"{c}" TEXT' for c in db_cols_for_table_create)
            conn.execute(f'CREATE TABLE IF NOT EXISTS fabrics ({cols_sql})')
            
            # proc DataFrame의 컬럼이 DB 테이블 컬럼명과 일치하도록 다시 정렬
            proc = proc.reindex(columns=db_cols_for_table_create)

            cur = conn.cursor()
            # 행별로 INSERT해서 rowid를 얻고 이력도 함께 저장
            inserted_rowids = []
            cols_sql2 = ",".join(f'"{c}"' for c in db_cols_for_table_create)
            ph = ",".join("?" for _ in db_cols_for_table_create)
            for _, row in proc.iterrows():
                cur.execute(f'INSERT INTO fabrics ({cols_sql2}) VALUES ({ph})', list(row))
                inserted_rowids.append(cur.lastrowid)

            # 이력 컬럼이 있으면 proposals 테이블에도 저장
            if proposal_data:
                # 브랜드 및 날짜 컬럼명 (DB 기준)
                db_brand_col = self._get_db_col_name("브랜드 및 제안처")
                db_date_col = "날짜"
                for i, rowid in enumerate(inserted_rowids):
                    row_brand = proc.iloc[i].get(db_brand_col, "") or ""
                    row_date  = proc.iloc[i].get(db_date_col, "") or ""
                    시즌     = proposal_data.get("시즌",     [""] * len(inserted_rowids))[i] or ""
                    전달가격 = str(proc.iloc[i].get(self._get_db_col_name("전달가격"), "") or "")
                    담당자   = proposal_data.get("담당자",   [""] * len(inserted_rowids))[i] or ""
                    제안결과 = proposal_data.get("제안결과", [""] * len(inserted_rowids))[i] or ""
                    메모     = proposal_data.get("메모",     [""] * len(inserted_rowids))[i] or ""
                    # 이력 필드 중 하나라도 값이 있을 때만 저장
                    if any([시즌, 담당자, 제안결과, 메모, row_brand]):
                        cur.execute('''
                            INSERT INTO proposals (fabric_rowid, 날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        ''', (rowid, row_date, row_brand, 시즌, 전달가격, 담당자, 제안결과, 메모))

            conn.commit()
            msg = "엑셀 데이터가 성공적으로 추가되었습니다."
            if proposal_data:
                msg += f"\n이력 컬럼({', '.join(proposal_data.keys())})도 함께 저장되었습니다."
            messagebox.showinfo("완료", msg)
            self._load_data()
        except Exception as e:
            messagebox.showerror("오류",f"DB 추가 실패: {e}")
        finally: 
            conn.close()

    def _delete_row(self):
        sel=self.main_tree.selection()
        if not sel:
            messagebox.showwarning("경고","삭제할 항목을 선택하세요.")
            return
        if messagebox.askyesno("확인","선택된 항목을 정말 삭제하시겠습니까?"):
            conn=sqlite3.connect(self.SETTINGS["DB_PATH"]); cur=conn.cursor()
            try:
                cur.execute("DELETE FROM fabrics WHERE rowid=?", (int(sel[0]),))
                conn.commit()
                messagebox.showinfo("완료","선택된 항목이 삭제되었습니다.")
                self._load_data()
            except Exception as e:
                messagebox.showerror("오류",f"삭제 오류: {e}")
            finally:
                conn.close()

    def _add_to_selected(self, event=None):
        for iid in self.main_tree.selection():
            try:
                rid=int(iid)
            except ValueError: 
                continue
            
            if any(r.get('_rowid') == rid for r in self.selected_rows_original_data):
                continue 

            row_data = self.df[self.df['_rowid']==rid].iloc[0].drop('_rowid').to_dict()
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
        if messagebox.askyesno("확인","선택된 모든 데이터를 목록에서 제거하시겠습니까?"):
            self.selected_rows_original_data.clear()
            self._populate_selected_tree()

    def _save_selected_to_excel(self):
        if not self.selected_rows_original_data:
            messagebox.showwarning("경고","선택된 데이터가 없습니다.")
            return
        
        export_cols = [
            "날짜", "제품명", "혼용률", "원단스펙", 
            "원단 무게", 
            "제시 폭", "전달가격", "재고 및 running"
        ]
        
        rows_for_export = []
        for r_dict in self.selected_rows_original_data:
            formatted_row = {}
            for col_name in export_cols:
                if col_name == "제품명": 
                    formatted_row[col_name] = self._format_data_for_display(r_dict.get('S&C 원단명'), 'S&C 원단명')
                else:
                    formatted_row[col_name] = self._format_data_for_display(r_dict.get(col_name), col_name)
            rows_for_export.append(formatted_row)

        df_sel=pd.DataFrame(rows_for_export)
        df_sel.rename(columns={"제시 폭":"원단 폭","전달가격":"원단가"},inplace=True)
        path=filedialog.asksaveasfilename(defaultextension=".xlsx",filetypes=[("Excel","*.xlsx")])
        if path:
            try:
                df_sel.to_excel(path,index=False)
                messagebox.showinfo("완료","선택된 데이터가 엑셀 파일로 저장되었습니다.")
            except Exception as e:
                messagebox.showerror("오류",f"저장 오류: {e}")

    def _save_label(self):
        if not self.selected_rows_original_data:
            messagebox.showwarning("경고","선택된 데이터가 없습니다.")
            return
        
        rows_for_label = []
        for r_dict in self.selected_rows_original_data:
            rows_for_label.append({
                "ART NO.":f"ART NO. : {self._format_data_for_display(r_dict.get('S&C 원단명'),'S&C 원단명')}",
                "COMPOSITION":f"COMPOSITION : {self._format_data_for_display(r_dict.get('혼용률'),'혼용률')}",
                "WEIGHT":f"WEIGHT : {self._format_data_for_display(r_dict.get('원단 무게'),'원단 무게')}", 
                "MOQ":f"MOQ : {self._format_data_for_display(r_dict.get('재고 및 running'),'재고 및 running')}"
            })
        df_lab=pd.DataFrame(rows_for_label)
        path=filedialog.asksaveasfilename(defaultextension=".xlsx",filetypes=[("Excel","*.xlsx")])
        if path:
            try:
                df_lab.to_excel(path,index=False)
                messagebox.showinfo("완료","라벨 데이터가 엑셀 파일로 저장되었습니다.")
            except Exception as e:
                messagebox.showerror("오류",f"저장 오류: {e}")

    def _backup_db(self):
        now=datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_dir=os.path.dirname(self.SETTINGS["DB_PATH"])
        
        os.makedirs(backup_dir, exist_ok=True)

        bp=os.path.join(backup_dir,f"fabrics_backup_{now}.db")
        try:
            shutil.copy(self.SETTINGS["DB_PATH"],bp)
            messagebox.showinfo("완료",f"데이터베이스 백업이 완료되었습니다:\n{bp}")
        except FileNotFoundError:
            messagebox.showerror("오류","원본 DB 파일이 존재하지 않습니다. 백업할 파일이 없습니다.")
        except Exception as e:
            messagebox.showerror("오류",f"백업 실패: {e}")

    def _export_all_selected_data_to_excel(self):
        """
        선택된 데이터 목록의 모든 컬럼을 엑셀 파일로 내보냅니다.
        """
        if not self.selected_rows_original_data:
            messagebox.showwarning("경고", "선택된 데이터가 없습니다.")
            return

        # 내보낼 컬럼명 목록을 현재 UI의 가시성 설정에 맞춰 생성
        export_cols_order = []
        is_compact = self.compact_mode_var.get()
        for col_name in self.SETTINGS["COLUMNS"]:
            if col_name in self.SETTINGS["ALWAYS_HIDDEN_COLS"] or \
               (is_compact and col_name in self.SETTINGS["COMPACT_MODE_TOGGLE_COLS"]):
                continue
            export_cols_order.append(col_name)

        rows_for_export = []
        for r_dict in self.selected_rows_original_data:
            formatted_row = {}
            for col_name in export_cols_order: # 가시성 설정에 맞춰 필터링된 컬럼만 사용
                if col_name == "제품명": 
                    formatted_row[col_name] = self._format_data_for_display(r_dict.get('S&C 원단명'), 'S&C 원단명')
                else:
                    formatted_row[col_name] = self._format_data_for_display(r_dict.get(col_name), col_name)
            rows_for_export.append(formatted_row)

        df_all_selected = pd.DataFrame(rows_for_export, columns=export_cols_order) # 컬럼 순서 지정

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="선택된 모든 원단 정보 내보내기"
        )

        if path:
            try:
                df_all_selected.to_excel(path, index=False)
                messagebox.showinfo("완료", f"선택된 모든 원단 정보가 엑셀 파일로 저장되었습니다:\n{path}")
            except Exception as e:
                messagebox.showerror("오류",f"엑셀 저장 중 오류가 발생했습니다: {e}")

    def _export_all_displayed_data_to_excel(self):
        """
        현재 메인 트리뷰에 표시되는 (검색/필터링된) 모든 데이터를 엑셀 파일로 내보냅니다.
        """
        if self.current_displayed_df is None or self.current_displayed_df.empty:
            messagebox.showwarning("경고", "내보낼 데이터가 없습니다. 먼저 데이터를 로드하거나 검색하세요.")
            return

        # 내보낼 컬럼명 목록을 현재 UI의 가시성 설정에 맞춰 생성
        export_cols_order = []
        is_compact = self.compact_mode_var.get()
        for col_name in self.SETTINGS["COLUMNS"]:
            if col_name in self.SETTINGS["ALWAYS_HIDDEN_COLS"] or \
               (is_compact and col_name in self.SETTINGS["COMPACT_MODE_TOGGLE_COLS"]):
                continue
            export_cols_order.append(col_name)

        rows_for_export = []
        for r_idx, row_data in self.current_displayed_df.iterrows():
            formatted_row = {}
            for col_name in export_cols_order: # 가시성 설정에 맞춰 필터링된 컬럼만 사용
                if col_name == "제품명": 
                    formatted_row[col_name] = self._format_data_for_display(row_data.get('S&C 원단명'), 'S&C 원단명')
                else:
                    formatted_row[col_name] = self._format_data_for_display(row_data.get(col_name), col_name)
            rows_for_export.append(formatted_row)

        df_to_export = pd.DataFrame(rows_for_export, columns=export_cols_order) # 컬럼 순서 지정

        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="현재 표시된 전체 원단 정보 내보내기"
        )

        if path:
            try:
                df_to_export.to_excel(path, index=False)
                messagebox.showinfo("완료", f"현재 표시된 전체 원단 정보가 엑셀 파일로 저장되었습니다:\n{path}")
            except Exception as e:
                messagebox.showerror("오류",f"엑셀 저장 중 오류가 발생했습니다: {e}")

    def _toggle_compact_mode(self): # apply_adjust_widths 매개변수 제거
        is_compact = self.compact_mode_var.get()
        
        # 메인 트리뷰 컬럼 가시성 조정
        for col_name in self.SETTINGS["COLUMNS"]:
            if col_name in self.SETTINGS["ALWAYS_HIDDEN_COLS"]:
                self.main_tree.column(col_name, width=0, stretch=False)
            elif col_name in self.SETTINGS["COMPACT_MODE_TOGGLE_COLS"]:
                if is_compact:
                    self.main_tree.column(col_name, width=0, stretch=False)
                else:
                    self.main_tree.column(col_name, width=100, stretch=True) # 간략 모드 해제 시 보이게
            else:
                self.main_tree.column(col_name, width=100, stretch=True) # 기본적으로 보이게

        # 선택된 데이터 트리뷰 컬럼 가시성 조정 및 데이터 재로드
        self._populate_selected_tree() # 선택된 데이터 목록을 다시 채워서 컬럼 가시성 및 데이터 일치

        # _adjust_treeview_column_widths는 _on_treeview_configure에서 디바운스되어 호출되므로 여기서 직접 호출하지 않음
        # 이 함수는 이제 컬럼 가시성만 조정하고, 너비 조정은 Configure 이벤트에 의해 처리됩니다.

    # ───────────────────────────────────────────────
    # 제안 이력 관련 메서드
    # ───────────────────────────────────────────────

    def _get_selected_rowid(self):
        sel = self.main_tree.selection()
        if not sel:
            messagebox.showwarning("경고", "원단을 먼저 선택하세요.")
            return None
        return int(sel[0])

    def _open_proposal_manager(self):
        """선택된 원단의 제안 이력 추가/수정/삭제 창"""
        rid = self._get_selected_rowid()
        if rid is None:
            return
        fabric_row = self.df[self.df['_rowid'] == rid]
        if fabric_row.empty:
            messagebox.showerror("오류", "원단 정보를 찾을 수 없습니다.")
            return
        fabric_info = fabric_row.iloc[0]
        fabric_name = fabric_info.get('S&C 원단명', '') or ''
        brand       = fabric_info.get('브랜드 및 제안처', '') or ''

        win = tk.Toplevel(self.master)
        win.title(f"이력 관리 — {fabric_name}")
        win.geometry("940x540")
        win.configure(bg=self.GEMINI_COLORS["DARK_BG"])
        win.transient(self.master)
        win.grab_set()

        # 원단 요약
        info_frame = ttk.Frame(win, padding="10 8 10 4")
        info_frame.pack(fill="x")
        ttk.Label(info_frame,
                  text=f"원단명: {fabric_name}   |   브랜드: {brand}   |   혼용률: {fabric_info.get('혼용률','')}",
                  font=('맑은 고딕', 10, 'bold')).pack(side="left")

        # 이력 목록
        list_frame = ttk.Frame(win, padding="10 0")
        list_frame.pack(fill="both", expand=True)

        hist_cols = ["날짜", "브랜드", "시즌", "전달가격", "담당자", "제안결과", "메모"]
        col_w     = {"날짜":90, "브랜드":130, "시즌":70, "전달가격":90, "담당자":80, "제안결과":80, "메모":230}
        hist_tree = ttk.Treeview(list_frame, columns=hist_cols, show="headings", height=8)
        for c in hist_cols:
            hist_tree.heading(c, text=c, anchor="center")
            hist_tree.column(c, width=col_w.get(c, 100), anchor="center")
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
            ttk.Label(form_frame, text=field).grid(row=0, column=i*2, padx=(8,2), sticky="w")
            if field == "제안결과":
                w = ttk.Combobox(form_frame, values=["검토중","채택","미채택"], state="readonly", width=8)
                w.set("검토중")
            else:
                w = ttk.Entry(form_frame, width=10 if field in ("날짜","시즌","전달가격","담당자") else 22)
            w.grid(row=0, column=i*2+1, padx=(0,5), pady=6)
            entries[field] = w

        entries["날짜"].insert(0, datetime.now().strftime('%Y-%m-%d'))
        entries["브랜드"].insert(0, brand)

        selected_id = [None]

        def load_list():
            hist_tree.delete(*hist_tree.get_children())
            conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
            try:
                rows = conn.execute(
                    'SELECT id, 날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모 '
                    'FROM proposals WHERE fabric_rowid=? ORDER BY 날짜 DESC',
                    (rid,)
                ).fetchall()
            finally:
                conn.close()
            for r in rows:
                tag = '채택' if r[7] == '채택' else ('미채택' if r[7] == '미채택' else '')
                hist_tree.insert("", "end", iid=str(r[0]), values=r[1:], tags=(tag,))
            hist_tree.tag_configure('채택',   foreground='#1a7a1a')
            hist_tree.tag_configure('미채택', foreground='#aaaaaa')

        def on_select(event):
            sel = hist_tree.selection()
            if not sel:
                return
            selected_id[0] = int(sel[0])
            conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
            try:
                row = conn.execute(
                    'SELECT 날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모 FROM proposals WHERE id=?',
                    (selected_id[0],)
                ).fetchone()
            finally:
                conn.close()
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
            conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
            try:
                if selected_id[0] is not None:
                    conn.execute(
                        'UPDATE proposals SET 날짜=?, 브랜드=?, 시즌=?, 전달가격=?, 담당자=?, 제안결과=?, 메모=? WHERE id=?',
                        (*[vals[f] for f in FIELDS], selected_id[0])
                    )
                    msg = "이력이 수정되었습니다."
                else:
                    conn.execute(
                        'INSERT INTO proposals (fabric_rowid, 날짜, 브랜드, 시즌, 전달가격, 담당자, 제안결과, 메모) '
                        'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                        (rid, *[vals[f] for f in FIELDS])
                    )
                    msg = "이력이 추가되었습니다."
                conn.commit()
            finally:
                conn.close()
            messagebox.showinfo("완료", msg)
            selected_id[0] = None
            clear_form()
            load_list()

        def delete():
            if selected_id[0] is None:
                messagebox.showwarning("경고", "삭제할 이력을 목록에서 선택하세요.")
                return
            if messagebox.askyesno("확인", "선택된 이력을 삭제하시겠습니까?"):
                conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
                try:
                    conn.execute('DELETE FROM proposals WHERE id=?', (selected_id[0],))
                    conn.commit()
                finally:
                    conn.close()
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
            entries["날짜"].insert(0, datetime.now().strftime('%Y-%m-%d'))
            entries["브랜드"].insert(0, brand)

        btn_frame = ttk.Frame(win, padding="10 0 10 10")
        btn_frame.pack(fill="x")
        ttk.Button(btn_frame, text="저장 / 수정", command=save).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="삭제",         command=delete).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="초기화",        command=clear_form).pack(side="left", padx=5)

        load_list()

    def _show_context_menu(self, event):
        """우클릭 컨텍스트 메뉴"""
        iid = self.main_tree.identify_row(event.y)
        if not iid:
            return
        self.main_tree.selection_set(iid)

        # 채택 여부 확인해서 메뉴 텍스트 변경
        rid = int(iid)
        conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
        try:
            row = conn.execute('SELECT 채택여부 FROM fabrics WHERE rowid=?', (rid,)).fetchone()
            is_adopted = row and row[0] == '채택'
        finally:
            conn.close()

        menu = tk.Menu(self.master, tearoff=0)
        menu.add_command(label="✅ 채택 해제" if is_adopted else "✅ 채택",
                         command=self._toggle_adoption)
        menu.add_separator()
        menu.add_command(label="✏️  수정", command=self._update_selected_entry)
        menu.add_command(label="🗑️  삭제", command=self._delete_row)
        menu.tk_popup(event.x_root, event.y_root)

    def _toggle_adoption(self):
        """선택된 원단의 채택여부를 토글 — 현재 화면 상태 유지"""
        sel = self.main_tree.selection()
        if not sel:
            messagebox.showwarning("경고", "채택할 원단을 선택하세요.")
            return

        conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
        try:
            cur = conn.cursor()
            for iid in sel:
                rid = int(iid)
                cur.execute('SELECT 채택여부 FROM fabrics WHERE rowid=?', (rid,))
                row = cur.fetchone()
                current = row[0] if row and row[0] else ""
                new_val = "" if current == "채택" else "채택"
                cur.execute('UPDATE fabrics SET 채택여부=? WHERE rowid=?', (new_val, rid))
            conn.commit()
        finally:
            conn.close()

        # 현재 검색/필터 상태 저장
        kw     = self.search_entry.get()
        col    = self.search_column.get()
        season = self.season_var.get()

        # df만 새로 로드하고 화면은 현재 상태 유지
        self._load_data_silent()

        # 저장된 상태 복원
        self.search_entry.delete(0, tk.END)
        self.search_entry.insert(0, kw)
        self.search_column.set(col)
        self.season_var.set(season)
        self._search_data()

    def _load_data_silent(self):
        """화면 갱신 없이 DB 데이터만 다시 로드"""
        db = self.SETTINGS["DB_PATH"]
        if not os.path.exists(db):
            return
        conn = sqlite3.connect(db)
        try:
            df = pd.read_sql("SELECT rowid AS _rowid, * FROM fabrics", conn)
            df.rename(columns=self.SETTINGS["DB_UI_COL_MAP"], inplace=True)
            df = df.reindex(columns=["_rowid"] + self.SETTINGS["COLUMNS"], fill_value=None)
        except:
            return
        finally:
            conn.close()
        df['_rowid'] = df['_rowid'].astype(int)
        self.df = df

    def _open_adoption_viewer(self):
        """시즌별 채택 원단 현황 창"""
        win = tk.Toplevel(self.master)
        win.title("시즌 채택 현황")
        win.geometry("1200x650")
        win.configure(bg=self.GEMINI_COLORS["DARK_BG"])
        win.transient(self.master)

        # 상단 필터
        filter_frame = ttk.Frame(win, padding="10 8 10 4")
        filter_frame.pack(fill="x")
        ttk.Label(filter_frame, text="시즌:", font=('맑은 고딕', 10, 'bold')).pack(side="left", padx=(0,5))

        # 시즌 목록 동적 로드
        conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
        try:
            seasons = conn.execute('''
                SELECT DISTINCT 시즌 FROM fabrics
                WHERE 채택여부 = '채택' AND 시즌 IS NOT NULL AND 시즌 != ''
                ORDER BY 시즌
            ''').fetchall()
        finally:
            conn.close()
        season_list = ["전체"] + [s[0] for s in seasons]

        season_var = tk.StringVar(value="전체")
        season_cb = ttk.Combobox(filter_frame, textvariable=season_var,
                                 values=season_list, state="readonly", width=10)
        season_cb.pack(side="left", padx=(0,15))

        # 담당자 필터
        ttk.Label(filter_frame, text="담당자:").pack(side="left", padx=(0,5))
        conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
        try:
            managers = conn.execute('''
                SELECT DISTINCT 담당자 FROM fabrics
                WHERE 채택여부 = '채택' AND 담당자 IS NOT NULL AND 담당자 != ''
                ORDER BY 담당자
            ''').fetchall()
        finally:
            conn.close()
        manager_list = ["전체"] + [m[0] for m in managers]
        manager_var = tk.StringVar(value="전체")
        manager_cb = ttk.Combobox(filter_frame, textvariable=manager_var,
                                  values=manager_list, state="readonly", width=10)
        manager_cb.pack(side="left", padx=(0,15))

        # 카운트 라벨
        count_label = ttk.Label(filter_frame, text="", font=('맑은 고딕', 9), foreground="#555555")
        count_label.pack(side="left", padx=10)

        # 엑셀 내보내기 버튼
        ttk.Button(filter_frame, text="엑셀 내보내기",
                   command=lambda: self._export_adoption_to_excel(tree)).pack(side="right", padx=5)

        # 트리뷰
        view_cols = ["시즌", "브랜드 및 제안처", "담당자", "업체명", "제품명",
                     "S&C 원단명", "혼용률", "원단스펙", "원단 무게",
                     "원가(YDS)", "전달가격", "마진(%)", "재고 및 running"]
        col_w = {
            "시즌": 55, "브랜드 및 제안처": 160, "담당자": 70, "업체명": 80,
            "제품명": 100, "S&C 원단명": 110, "혼용률": 100, "원단스펙": 130,
            "원단 무게": 65, "원가(YDS)": 80, "전달가격": 80, "마진(%)": 75,
            "재고 및 running": 120
        }
        tree_frame = ttk.Frame(win, padding="10 0")
        tree_frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(tree_frame, columns=view_cols, show="headings")
        for c in view_cols:
            tree.heading(c, text=c, anchor="center")
            tree.column(c, width=col_w.get(c, 100), anchor="center", minwidth=40)
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        def load_data():
            tree.delete(*tree.get_children())
            sel_season  = season_var.get()
            sel_manager = manager_var.get()

            df = self.df[self.df.get('채택여부', '') == '채택'].copy() \
                if '채택여부' in self.df.columns else pd.DataFrame()
            # 채택여부 컬럼 직접 DB에서 읽기
            conn = sqlite3.connect(self.SETTINGS["DB_PATH"])
            try:
                adopted = conn.execute(
                    'SELECT rowid FROM fabrics WHERE 채택여부 = "채택"'
                ).fetchall()
                adopted_ids = {r[0] for r in adopted}
            finally:
                conn.close()

            df = self.df[self.df['_rowid'].isin(adopted_ids)].copy()

            if sel_season != "전체":
                df = df[df["시즌"].astype(str).str.strip() == sel_season]
            if sel_manager != "전체":
                df = df[df["담당자"].astype(str).str.strip() == sel_manager]

            df = df.sort_values(by=["시즌", "브랜드 및 제안처"], na_position='last')

            for i, row in df.iterrows():
                vals = [self._format_data_for_display(row.get(c), c) for c in view_cols]
                tag = 'even' if i % 2 == 0 else 'odd'
                tree.insert("", "end", values=vals, tags=(tag,))

            tree.tag_configure('even', background=self.GEMINI_COLORS["TREEVIEW_ROW_EVEN"])
            tree.tag_configure('odd',  background=self.GEMINI_COLORS["TREEVIEW_ROW_ODD"])
            count_label.config(text=f"총 {len(df)}개 원단")

        season_cb.bind("<<ComboboxSelected>>",  lambda e: load_data())
        manager_cb.bind("<<ComboboxSelected>>", lambda e: load_data())
        load_data()

    def _export_adoption_to_excel(self, tree):
        """채택 현황 엑셀 내보내기"""
        rows = [tree.item(iid)["values"] for iid in tree.get_children()]
        if not rows:
            messagebox.showwarning("경고", "내보낼 데이터가 없습니다.")
            return
        cols = ["시즌", "브랜드 및 제안처", "담당자", "업체명", "제품명",
                "S&C 원단명", "혼용률", "원단스펙", "원단 무게",
                "원가(YDS)", "전달가격", "마진(%)", "재고 및 running"]
        import pandas as pd
        df = pd.DataFrame(rows, columns=cols)
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")],
            title="채택 현황 내보내기"
        )
        if path:
            try:
                df.to_excel(path, index=False)
                messagebox.showinfo("완료", f"저장되었습니다:\n{path}")
            except Exception as e:
                messagebox.showerror("오류", f"저장 오류: {e}")

    def _auto_backup_to_onedrive(self):
        """하루 1회 실행 파일 옆 backup 폴더에 자동 백업 (OneDrive 경로 자동 인식)"""
        try:
            # 실행 파일(또는 .py 파일) 기준으로 backup 폴더 생성
            if getattr(sys, 'frozen', False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(os.path.abspath(__file__))

            backup_dir = os.path.join(base_dir, "backup")
            os.makedirs(backup_dir, exist_ok=True)

            # 오늘 이미 백업했는지 확인
            today = datetime.now().strftime('%Y%m%d')
            backup_file = os.path.join(backup_dir, f"fabrics_backup_{today}.db")

            if os.path.exists(backup_file):
                return  # 오늘 이미 백업됨

            # 백업 실행
            src = self.SETTINGS["DB_PATH"]
            if os.path.exists(src):
                shutil.copy(src, backup_file)
                # 최근 30개만 보관
                backups = sorted([
                    f for f in os.listdir(backup_dir)
                    if f.startswith("fabrics_backup_") and f.endswith(".db")
                ])
                for old in backups[:-30]:
                    os.remove(os.path.join(backup_dir, old))
        except Exception as e:
            print(f"자동 백업 실패 (무시): {e}")

    def _sort_treeview(self, tree, col):
        l = [(tree.set(k, col), k) for k in tree.get_children('')]
        
        if col in self.SETTINGS["NUMERIC_COLS_FOR_STORAGE"] or \
           col in self.SETTINGS["NUMERIC_COLS_FOR_DECIMAL_DISPLAY"] or \
           col in self.SETTINGS["CURRENCY_COLS_DISPLAY"] or \
           col in self.SETTINGS["PERCENT_COLS_DISPLAY"]:
            def numeric_sort_key(item_value):
                cleaned = re.sub(r'[^\d.\-]+', '', str(item_value))
                try:
                    return float(cleaned)
                except ValueError:
                    return float('-inf') 
            l.sort(key=lambda x: numeric_sort_key(x[0]))
        else:
            l.sort(key=lambda x: x[0])

        if not hasattr(tree, 'sort_direction'):
            tree.sort_direction = {}
        
        if col not in tree.sort_direction:
            tree.sort_direction[col] = False 
        
        reverse_sort = tree.sort_direction[col]
        if reverse_sort:
            l.reverse()
        
        for index, (val, k) in enumerate(l):
            tree.move(k, '', index)
        
        tree.sort_direction[col] = not reverse_sort


if __name__ == "__main__":
    root=tk.Tk()
    app=FabricApp(root)
    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            icon_path = os.path.join(sys._MEIPASS, 'SFF.png') 
        else:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, 'SFF.png')
        
        if os.path.exists(icon_path):
            original_image = Image.open(icon_path)
            resized_image = original_image.resize((32, 32), Image.Resampling.LANCZOS) 
            photo_image = ImageTk.PhotoImage(resized_image)
            root.wm_iconphoto(True, photo_image) 
        else:
            print(f"경고: 아이콘 파일 '{icon_path}'을(를) 찾을 수 없습니다. 창 아이콘이 설정되지 않습니다.")
    except Exception as e:
        print(f"아이콘 설정 중 오류 발생: {e}")
    
    root.mainloop()
