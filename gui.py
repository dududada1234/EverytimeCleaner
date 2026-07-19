import json
import queue
import threading
import traceback
import time

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

import utils
from cleaner import EverytimeCleaner


# ── 테마 ─────────────────────────────────
BG     = "#16181d"
PANEL  = "#1e2128"
CARD   = "#252932"
FG     = "#e6e8eb"
MUTED  = "#8a919e"
ACCENT = "#5b8def"
OK     = "#3fb950"
WARN   = "#d29922"
ERR    = "#f85149"
BORDER = "#2d323c"

FONT     = ("Malgun Gothic", 10)
FONT_B   = ("Malgun Gothic", 10, "bold")
FONT_TTL = ("Malgun Gothic", 16, "bold")
FONT_MON = ("Consolas", 9)


class CleanerGUI:
    def __init__(self, root):
        self.root = root
        self.log_queue = queue.Queue()
        self.worker = None
        self.stop_flag = threading.Event()
        self.bot = None
        self.start_time = None

        # 마스코트 상태
        self._m_label = None
        self._m_frames = None
        self._m_delays = None
        self._m_idx = 0

        self.config_path = utils.get_resource_path("config.json")
        self.config = self._load_config()

        self._build_ui()
        self._pump_logs()

    # ── 설정 ─────────────────────────────
    def _load_config(self):
        cfg = {"MIN_DELAY": 1.5, "MAX_DELAY": 3.0, "HEADLESS": False}
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception:
            pass
        return cfg

    def _save_config(self):
        try:
            self.config["MIN_DELAY"] = float(self.min_delay.get())
            self.config["MAX_DELAY"] = float(self.max_delay.get())
            self.config["HEADLESS"] = bool(self.headless.get())
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            self.log("설정을 저장했습니다.", "ok")
        except ValueError:
            messagebox.showerror("오류", "지연 시간은 숫자여야 합니다.")
        except Exception as e:
            messagebox.showerror("오류", f"설정 저장 실패: {e}")

    # ── UI ───────────────────────────────
    def _build_ui(self):
        r = self.root
        r.title("Everytime Cleaner")
        r.geometry("980x760")
        r.minsize(860, 680)
        r.configure(bg=BG)

        try:
            r.iconbitmap(utils.get_resource_path("icon.ico"))
        except Exception:
            pass

        st = ttk.Style()
        st.theme_use("clam")
        st.configure("TFrame", background=BG)
        st.configure("TLabel", background=BG, foreground=FG, font=FONT)
        st.configure("Title.TLabel", background=BG, foreground=FG, font=FONT_TTL)
        st.configure("Sub.TLabel", background=BG, foreground=MUTED, font=FONT)
        st.configure("TCheckbutton", background=CARD, foreground=FG, font=FONT)
        st.map("TCheckbutton", background=[("active", CARD)])
        st.configure("Bar.Horizontal.TProgressbar", background=ACCENT,
                     troughcolor=PANEL, bordercolor=PANEL,
                     lightcolor=ACCENT, darkcolor=ACCENT)

        # 헤더
        head = ttk.Frame(r, padding=(20, 16, 20, 8))
        head.pack(fill="x")

        logo = utils.load_image("logo.png", (44, 44))
        if logo:
            lb = tk.Label(head, image=logo, bg=BG)
            lb.image = logo
            lb.pack(side="left", padx=(0, 12))

        txt = ttk.Frame(head)
        txt.pack(side="left")
        ttk.Label(txt, text="Everytime Cleaner", style="Title.TLabel").pack(anchor="w")
        ttk.Label(txt, text="내 글 · 댓글 자동 삭제 도구", style="Sub.TLabel").pack(anchor="w")

        body = ttk.Frame(r, padding=(20, 4, 20, 20))
        body.pack(fill="both", expand=True)
        body.columnconfigure(0, weight=0, minsize=280)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # ── 왼쪽 패널 ─────────────────────
        left = tk.Frame(body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))

        pad = tk.Frame(left, bg=CARD)
        pad.pack(fill="both", expand=True, padx=16, pady=16)

        tk.Label(pad, text="설정", bg=CARD, fg=FG, font=FONT_B).pack(anchor="w", pady=(0, 10))

        tk.Label(pad, text="최소 지연 (초)", bg=CARD, fg=MUTED, font=FONT).pack(anchor="w")
        self.min_delay = tk.StringVar(value=str(self.config["MIN_DELAY"]))
        self._entry(pad, self.min_delay).pack(fill="x", ipady=4, pady=(2, 10))

        tk.Label(pad, text="최대 지연 (초)", bg=CARD, fg=MUTED, font=FONT).pack(anchor="w")
        self.max_delay = tk.StringVar(value=str(self.config["MAX_DELAY"]))
        self._entry(pad, self.max_delay).pack(fill="x", ipady=4, pady=(2, 12))

        self.headless = tk.BooleanVar(value=self.config["HEADLESS"])
        ttk.Checkbutton(pad, text="헤드리스 모드", variable=self.headless).pack(anchor="w")
        tk.Label(pad, text="로그인 인증이 필요하므로\n켜두면 로그인이 안 됩니다.",
                 bg=CARD, fg=MUTED, font=("Malgun Gothic", 8),
                 justify="left").pack(anchor="w", pady=(2, 12))

        self._btn(pad, "설정 저장", self._save_config, PANEL, FG).pack(fill="x", pady=(0, 14))

        tk.Frame(pad, bg=BORDER, height=1).pack(fill="x", pady=(0, 14))

        self.start_btn = self._btn(pad, "▶  삭제 시작", self.start, ACCENT, "#ffffff")
        self.start_btn.pack(fill="x", pady=(0, 8))

        self.stop_btn = self._btn(pad, "■  중지", self.stop, PANEL, ERR)
        self.stop_btn.pack(fill="x")
        self.stop_btn.configure(state="disabled")

        # 통계
        tk.Frame(pad, bg=BORDER, height=1).pack(fill="x", pady=14)
        self.v_ok = tk.StringVar(value="0")
        self.v_ng = tk.StringVar(value="0")
        self.v_el = tk.StringVar(value="00:00")
        for label, var, color in (("성공", self.v_ok, OK),
                                  ("실패", self.v_ng, ERR),
                                  ("경과", self.v_el, MUTED)):
            row = tk.Frame(pad, bg=CARD)
            row.pack(fill="x", pady=3)
            tk.Label(row, text=label, bg=CARD, fg=MUTED, font=FONT).pack(side="left")
            tk.Label(row, textvariable=var, bg=CARD, fg=color, font=FONT_B).pack(side="right")

        # 마스코트 (assets/mascot.gif)
        self._setup_mascot(pad)

        # ── 오른쪽 로그 ───────────────────
        right = tk.Frame(body, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        right.grid(row=0, column=1, sticky="nsew")
        right.rowconfigure(2, weight=1)
        right.columnconfigure(0, weight=1)

        bar = tk.Frame(right, bg=CARD)
        bar.grid(row=0, column=0, sticky="ew", padx=16, pady=(14, 8))
        tk.Label(bar, text="실행 로그", bg=CARD, fg=FG, font=FONT_B).pack(side="left")
        self.status = tk.StringVar(value="대기 중")
        tk.Label(bar, textvariable=self.status, bg=CARD, fg=MUTED,
                 font=FONT).pack(side="left", padx=(10, 0))

        for text, cmd in (("지우기", self._clear_log), ("저장", self._export_log)):
            tk.Button(bar, text=text, command=cmd, bg=PANEL, fg=MUTED,
                      font=("Malgun Gothic", 8), relief="flat", bd=0,
                      activebackground=BORDER, activeforeground=FG,
                      cursor="hand2", padx=10, pady=3).pack(side="right", padx=(6, 0))

        self.pbar = ttk.Progressbar(right, style="Bar.Horizontal.TProgressbar",
                                    mode="determinate", maximum=100)
        self.pbar.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 10))

        wrap = tk.Frame(right, bg=PANEL)
        wrap.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 16))
        wrap.rowconfigure(0, weight=1)
        wrap.columnconfigure(0, weight=1)

        self.log_box = tk.Text(wrap, bg=PANEL, fg=FG, font=FONT_MON,
                               relief="flat", bd=0, wrap="word",
                               padx=12, pady=10, state="disabled",
                               insertbackground=FG, spacing1=1, spacing3=1)
        self.log_box.grid(row=0, column=0, sticky="nsew")

        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.log_box.yview)
        sb.grid(row=0, column=1, sticky="ns")
        self.log_box.configure(yscrollcommand=sb.set)

        for tag, color in (("info", FG), ("ok", OK), ("warn", WARN),
                           ("error", ERR), ("step", ACCENT), ("time", MUTED)):
            self.log_box.tag_configure(tag, foreground=color)

        self.log("준비 완료. '삭제 시작'을 누르면 브라우저가 열립니다.", "step")
        r.protocol("WM_DELETE_WINDOW", self._on_close)

    def _entry(self, parent, var):
        return tk.Entry(parent, textvariable=var, bg=PANEL, fg=FG, font=FONT,
                        relief="flat", insertbackground=FG,
                        highlightthickness=1, highlightbackground=BORDER,
                        highlightcolor=ACCENT)

    def _btn(self, parent, text, cmd, bg, fg):
        return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                         font=FONT_B, relief="flat", bd=0, cursor="hand2",
                         activebackground=BORDER, activeforeground=fg, pady=9)

    # ── 마스코트 ─────────────────────────
    def _setup_mascot(self, parent):
        frames, delays = utils.load_gif_frames("mascot.gif", (220, 220))
        if not frames:
            print("[mascot] GIF 로드 실패 — assets/mascot.gif 와 Pillow 확인")
            return

        self._m_frames = frames
        self._m_delays = delays
        self._m_idx = 0

        tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", pady=(14, 10))

        lbl = tk.Label(parent, image=frames[0], bg=CARD, bd=0)
        lbl.pack(pady=(0, 4))          # side="bottom" 제거
        lbl.image = frames[0]
        self._m_label = lbl

        self._animate_mascot()

    def _animate_mascot(self):
        if not self._m_label or not self._m_frames:
            return
        self._m_idx = (self._m_idx + 1) % len(self._m_frames)
        try:
            self._m_label.configure(image=self._m_frames[self._m_idx])
        except tk.TclError:
            return   # 창이 닫힘
        self.root.after(self._m_delays[self._m_idx], self._animate_mascot)

    # ── 로그 ─────────────────────────────
    def log(self, msg, level="info"):
        self.log_queue.put((msg, level))

    def _pump_logs(self):
        """워커 스레드 → UI. 위젯 조작은 메인 스레드에서만."""
        try:
            while True:
                msg, level = self.log_queue.get_nowait()
                self.log_box.configure(state="normal")
                self.log_box.insert("end", time.strftime("%H:%M:%S  "), "time")
                self.log_box.insert("end", f"{msg}\n", level)
                self.log_box.see("end")
                self.log_box.configure(state="disabled")
        except queue.Empty:
            pass

        if self.bot:
            self.v_ok.set(str(self.bot.deleted_count))
            self.v_ng.set(str(self.bot.failed_count))
            if self.bot.total_targets:
                self.pbar["value"] = (self.bot.processed / self.bot.total_targets) * 100

        if self.start_time and self.worker and self.worker.is_alive():
            el = int(time.time() - self.start_time)
            self.v_el.set(f"{el // 60:02d}:{el % 60:02d}")

        self.root.after(120, self._pump_logs)

    def _clear_log(self):
        self.log_box.configure(state="normal")
        self.log_box.delete("1.0", "end")
        self.log_box.configure(state="disabled")

    def _export_log(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("텍스트 파일", "*.txt")],
            initialfile=f"cleaner_log_{time.strftime('%Y%m%d_%H%M%S')}.txt")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.log_box.get("1.0", "end"))
            self.log(f"로그를 저장했습니다: {path}", "ok")
        except Exception as e:
            messagebox.showerror("오류", f"저장 실패: {e}")

    # ── 실행 ─────────────────────────────
    def start(self):
        if self.worker and self.worker.is_alive():
            return
        try:
            self.config["MIN_DELAY"] = float(self.min_delay.get())
            self.config["MAX_DELAY"] = float(self.max_delay.get())
            self.config["HEADLESS"] = bool(self.headless.get())
        except ValueError:
            messagebox.showerror("오류", "지연 시간은 숫자여야 합니다.")
            return

        self.stop_flag.clear()
        self.start_time = time.time()
        self.pbar["value"] = 0
        self.start_btn.configure(state="disabled", bg=PANEL, fg=MUTED)
        self.stop_btn.configure(state="normal")
        self.status.set("실행 중")

        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    def _run(self):
        try:
            self.log("드라이버를 초기화합니다...", "step")
            self.bot = EverytimeCleaner(self.config,
                                        logger=self.log,
                                        stop_flag=self.stop_flag)
            self.log("에브리타임에 접속합니다.", "step")
            self.bot.login()
            self.log("삭제 작업을 시작합니다.", "step")
            self.bot.clean_all()

            if self.stop_flag.is_set():
                self.log("사용자 요청으로 중지되었습니다.", "warn")
            else:
                self.log(f"작업 완료 — 성공 {self.bot.deleted_count} / "
                         f"실패 {self.bot.failed_count}", "ok")
        except Exception as e:
            self.log(f"오류: {e}", "error")
            self.log(traceback.format_exc(), "error")
        finally:
            if self.bot:
                self.bot.close()
            self.root.after(0, self._finish)

    def _finish(self):
        self.start_btn.configure(state="normal", bg=ACCENT, fg="#ffffff")
        self.stop_btn.configure(state="disabled")
        self.status.set("완료")
        self.pbar["value"] = 100

    def stop(self):
        self.stop_flag.set()
        self.status.set("중지 요청 중...")
        self.log("중지를 요청했습니다. 현재 작업이 끝나면 멈춥니다.", "warn")

    def _on_close(self):
        if self.worker and self.worker.is_alive():
            if not messagebox.askokcancel("종료", "작업이 진행 중입니다. 정말 종료할까요?"):
                return
            self.stop_flag.set()
            if self.bot:
                self.bot.close()
        self._m_label = None   # 애니메이션 루프 중단
        self.root.destroy()


def run():
    root = tk.Tk()
    CleanerGUI(root)
    root.mainloop()
