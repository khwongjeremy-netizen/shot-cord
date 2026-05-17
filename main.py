import tkinter as tk
from tkinter import filedialog

import cv2
from PIL import Image, ImageTk

# --- 1. THEME CONFIGURATION ---
COLOR_BG = "#1e1e1e"
COLOR_ACCENT = "#0048FF"
COLOR_SUCCESS = "#0048FF"
COLOR_TEXT = "#000000"
COLOR_TEXT_ = "#ffffff"
COLOR_TEXT_DIM = "#888888"
COLOR_SURFACE = "#2d2d2d"
COLOR_NAV_BTN = "#444444"

COLOR_BTN_TXT_LIGHT = "#ffffff"
COLOR_BTN_TXT_DARK = "#1e1e1e"

# Hover states (derived from palette; not replacements)
COLOR_NAV_BTN_HOVER = "#525252"
COLOR_SUCCESS_HOVER = "#2260ff"
COLOR_SURFACE_HOVER = "#3a3a3a"
COLOR_INSET = "#252525"

# --- 2. TYPOGRAPHY CONFIGURATION ---
FONT_FAMILY = "Helvetica"
FONT_TITLE = (FONT_FAMILY, 26, "bold")
FONT_HEAD = (FONT_FAMILY, 14, "bold")
FONT_BOLD = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_MICRO = (FONT_FAMILY, 9, "bold")
FONT_BUTTON = (FONT_FAMILY, 12, "bold")
FONT_METRIC = (FONT_FAMILY, 38, "bold")
FONT_METRIC_SUB = (FONT_FAMILY, 11, "bold")

ANALYSIS_MODE = "Initial Launch"

# --- 3. BACKEND CONNECTION ---
try:
    from track_enigine import run_analysis
except ImportError:
    run_analysis = None
    print("Error: Could not find track_enigine.py.")


def _bind_hover(
    widget: tk.Widget,
    normal_bg: str,
    hover_bg: str,
    *,
    normal_fg: str | None = None,
    hover_fg: str | None = None,
) -> None:
    """Swap background (and optional foreground) on pointer enter/leave."""

    def _apply(bg: str, fg: str | None) -> None:
        if str(widget.cget("state")) == "disabled":
            return
        widget.config(bg=bg)
        if fg is not None:
            widget.config(fg=fg)

    widget.bind("<Enter>", lambda _e: _apply(hover_bg, hover_fg))
    widget.bind("<Leave>", lambda _e: _apply(normal_bg, normal_fg))


class StrikerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Striker Analytics v1.0")
        self.root.geometry("660x860")
        self.root.minsize(580, 760)
        self.root.configure(bg=COLOR_BG)

        self.file_path_var = tk.StringVar(value="No file selected...")
        self._ref_photo: ImageTk.PhotoImage | None = None
        self.btn_launch: tk.Button | None = None
        self._launch_hover_bound = False

        self.main_container = tk.Frame(self.root, bg=COLOR_BG)
        self.main_container.pack(expand=True, fill="both", padx=28, pady=24)

        self.show_dashboard()

    # ------------------------------------------------------------------ UI kit
    @staticmethod
    def _card(
        parent: tk.Widget,
        *,
        padx: int = 20,
        pady: int = 18,
        accent: bool = True,
        outer_pady: tuple[int, int] = (0, 16),
    ) -> tk.Frame:
        shell = tk.Frame(parent, bg=COLOR_BG)
        shell.pack(fill="x", pady=outer_pady)

        card = tk.Frame(shell, bg=COLOR_SURFACE, highlightthickness=0, bd=0)
        card.pack(fill="x", ipady=2)

        if accent:
            tk.Frame(card, bg=COLOR_ACCENT, height=3).pack(fill="x")

        body = tk.Frame(card, bg=COLOR_SURFACE)
        body.pack(fill="x", padx=padx, pady=pady)
        return body

    @staticmethod
    def _card_title(parent: tk.Widget, text: str) -> None:
        tk.Label(
            parent,
            text=text.upper(),
            font=FONT_MICRO,
            bg=COLOR_SURFACE,
            fg=COLOR_ACCENT,
            anchor="w",
        ).pack(anchor="w", pady=(0, 12))

    @staticmethod
    def _step_block(
        parent: tk.Widget,
        label: str,
        body: str,
        *,
        top_pad: int = 0,
    ) -> None:
        block = tk.Frame(parent, bg=COLOR_SURFACE)
        block.pack(fill="x", pady=(top_pad, 0))

        tk.Label(
            block,
            text=label,
            font=FONT_MICRO,
            bg=COLOR_SURFACE,
            fg=COLOR_ACCENT,
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            block,
            text=body,
            font=FONT_BODY,
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_,
            justify="left",
            anchor="w",
            wraplength=520,
        ).pack(anchor="w", pady=(4, 14), ipadx=2)

    @staticmethod
    def _flat_button(
        parent: tk.Widget,
        text: str,
        command,
        *,
        bg: str,
        fg: str,
        hover_bg: str,
        font=FONT_BUTTON,
        padx: int = 20,
        pady: int = 10,
        state: str = "normal",
        fill_x: bool = False,
    ) -> tk.Button:
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=bg,
            fg=fg,
            font=font,
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=padx,
            pady=pady,
            cursor="hand2",
            state=state,
            activebackground=hover_bg,
            activeforeground=fg,
        )
        if fill_x:
            btn.pack(fill="x")
        _bind_hover(btn, bg, hover_bg, normal_fg=fg, hover_fg=fg)
        return btn

    # ---------------------------------------------------------------- lifecycle
    def clear_screen(self) -> None:
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.btn_launch = None
        self._launch_hover_bound = False

    def reset_session(self) -> None:
        """Fully tear down prior analysis state before starting over."""
        cv2.destroyAllWindows()
        self.file_path_var.set("No file selected...")
        if self.btn_launch is not None:
            self.btn_launch.config(
                state="disabled",
                bg=COLOR_SURFACE,
                fg=COLOR_TEXT_DIM,
            )
        self.show_dashboard()

    def show_dashboard(self) -> None:
        self.clear_screen()

        header = tk.Frame(self.main_container, bg=COLOR_BG)
        header.pack(fill="x", pady=(0, 20))

        tk.Label(
            header,
            text="STRIKER",
            font=(FONT_FAMILY, 11, "bold"),
            bg=COLOR_BG,
            fg=COLOR_TEXT_DIM,
        ).pack(anchor="w")

        tk.Label(
            header,
            text="ANALYTICS",
            font=FONT_TITLE,
            bg=COLOR_BG,
            fg=COLOR_ACCENT,
        ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            header,
            text="Free-kick flight telemetry · perspective-corrected 3D",
            font=FONT_BODY,
            bg=COLOR_BG,
            fg=COLOR_TEXT_DIM,
        ).pack(anchor="w", pady=(6, 0))

        self._build_instructions_card()
        self._build_file_dashboard()

    def _build_instructions_card(self) -> None:
        card = self._card(self.main_container, padx=22, pady=20)
        self._card_title(card, "Workflow")

        self._step_block(
            card,
            "SETUP",
            "Keep the camera stable on a tripod for consistent tracking.",
        )
        self._step_block(
            card,
            "STEP 01",
            "Click Browse Files to load an MP4, MOV, or AVI video asset.",
            top_pad=4,
        )
        self._step_block(
            card,
            "STEP 02",
            "Draw a bounding box around the BALL first (Red), then the FOOT "
            "second (Cyan). Press ENTER to lock each selection.",
            top_pad=4,
        )
        self._step_block(
            card,
            "STEP 03",
            "View real-time, 3D perspective-corrected flight telemetry live.",
            top_pad=4,
        )

        tk.Frame(card, bg=COLOR_SURFACE, height=8).pack()

        image_frame = tk.Frame(card, bg=COLOR_INSET, highlightthickness=0)
        image_frame.pack(fill="x", ipady=10, ipadx=10)

        image_slot = tk.Label(image_frame, bg=COLOR_INSET, fg=COLOR_TEXT_DIM)
        image_slot.pack(padx=12, pady=12)
        self._load_reference_image(image_slot)

    def _load_reference_image(self, target: tk.Label) -> None:
        try:
            img = Image.open("freekick_ref.png")
            img = img.resize((320, 200), Image.Resampling.LANCZOS)
            self._ref_photo = ImageTk.PhotoImage(img)
            target.config(image=self._ref_photo, text="")
        except (FileNotFoundError, OSError):
            target.config(
                image="",
                text="Reference frame unavailable",
                font=FONT_BODY,
                fg=COLOR_TEXT_DIM,
            )

    def _build_file_dashboard(self) -> None:
        tk.Frame(self.main_container, bg=COLOR_BG, height=14).pack()

        card = self._card(
            self.main_container, padx=22, pady=20, outer_pady=(0, 0)
        )
        self._card_title(card, "Video Asset")

        path_shell = tk.Frame(card, bg=COLOR_INSET, highlightthickness=0)
        path_shell.pack(fill="x", pady=(0, 14), ipadx=12, ipady=12)

        tk.Label(
            path_shell,
            text="SELECTED FILE",
            font=FONT_MICRO,
            bg=COLOR_INSET,
            fg=COLOR_TEXT_DIM,
            anchor="w",
        ).pack(anchor="w", padx=14, pady=(10, 4))

        path_row = tk.Frame(path_shell, bg=COLOR_INSET)
        path_row.pack(fill="x", padx=14, pady=(0, 12))

        tk.Label(
            path_row,
            textvariable=self.file_path_var,
            bg=COLOR_INSET,
            fg=COLOR_TEXT_,
            font=FONT_BOLD,
            anchor="w",
            justify="left",
            wraplength=360,
        ).pack(side="left", fill="x", expand=True, padx=(0, 12))

        self._flat_button(
            path_row,
            "Browse Files",
            self.browse_files,
            bg=COLOR_NAV_BTN,
            fg=COLOR_TEXT_,
            hover_bg=COLOR_NAV_BTN_HOVER,
            padx=18,
            pady=10,
        ).pack(side="right")

        self.btn_launch = tk.Button(
            card,
            text="LAUNCH ANALYTICS",
            state="disabled",
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_DIM,
            font=(FONT_FAMILY, 13, "bold"),
            relief="flat",
            bd=0,
            highlightthickness=0,
            cursor="hand2",
            pady=18,
            command=self.start_backend,
            activebackground=COLOR_SUCCESS_HOVER,
            activeforeground=COLOR_BTN_TXT_DARK,
        )
        self.btn_launch.pack(fill="x", pady=(4, 0), ipady=4)

    def _enable_launch_cta(self) -> None:
        if self.btn_launch is None:
            return
        self.btn_launch.config(
            state="normal",
            bg=COLOR_SUCCESS,
            fg=COLOR_BTN_TXT_DARK,
            activebackground=COLOR_SUCCESS_HOVER,
            activeforeground=COLOR_BTN_TXT_DARK,
        )
        if not self._launch_hover_bound:
            _bind_hover(
                self.btn_launch,
                COLOR_SUCCESS,
                COLOR_SUCCESS_HOVER,
                normal_fg=COLOR_BTN_TXT_DARK,
                hover_fg=COLOR_BTN_TXT_DARK,
            )
            self._launch_hover_bound = True

    def browse_files(self) -> None:
        filename = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.mov *.avi")]
        )
        if not filename:
            return
        self.file_path_var.set(filename)
        self._enable_launch_cta()

    def start_backend(self) -> None:
        if run_analysis is None:
            return

        video_path = self.file_path_var.get()
        if not video_path or video_path == "No file selected...":
            return

        self.root.withdraw()
        try:
            analysis_result = run_analysis(video_path, mode=ANALYSIS_MODE)
        finally:
            cv2.destroyAllWindows()
            self.root.deiconify()

        self.show_results_screen(analysis_result)

    def show_results_screen(self, shot_type: str) -> None:
        self.clear_screen()

        canvas = tk.Frame(self.main_container, bg=COLOR_BG)
        canvas.pack(expand=True, fill="both")

        tk.Label(
            canvas,
            text="SESSION COMPLETE",
            font=FONT_MICRO,
            bg=COLOR_BG,
            fg=COLOR_TEXT_DIM,
        ).pack(pady=(48, 6))

        tk.Label(
            canvas,
            text="Flight Analysis",
            font=FONT_HEAD,
            bg=COLOR_BG,
            fg=COLOR_ACCENT,
        ).pack(pady=(0, 28))

        metric_card = self._card(
            canvas, padx=28, pady=28, outer_pady=(0, 0)
        )

        tk.Label(
            metric_card,
            text="DETECTED SHOT TYPE",
            font=FONT_METRIC_SUB,
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_DIM,
        ).pack(pady=(0, 16))

        inset = tk.Frame(metric_card, bg=COLOR_INSET, highlightthickness=0)
        inset.pack(fill="x", ipadx=24, ipady=28)

        tk.Label(
            inset,
            text=shot_type.upper(),
            font=FONT_METRIC,
            bg=COLOR_INSET,
            fg=COLOR_TEXT_,
            wraplength=480,
            justify="center",
        ).pack(padx=20, pady=8)

        tk.Label(
            metric_card,
            text="Perspective-corrected 3D classification",
            font=FONT_BODY,
            bg=COLOR_SURFACE,
            fg=COLOR_ACCENT,
        ).pack(pady=(18, 0))

        action_row = tk.Frame(canvas, bg=COLOR_BG)
        action_row.pack(pady=(36, 40))

        self._flat_button(
            action_row,
            "ANALYZE ANOTHER",
            self.reset_session,
            bg=COLOR_NAV_BTN,
            fg=COLOR_TEXT_,
            hover_bg=COLOR_NAV_BTN_HOVER,
            padx=36,
            pady=14,
        ).pack()


if __name__ == "__main__":
    root = tk.Tk()
    StrikerApp(root)
    root.mainloop()
