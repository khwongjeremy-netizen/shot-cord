import tkinter as tk
from tkinter import filedialog

import cv2
from PIL import Image, ImageTk

# --- 1. THEME CONFIGURATION ---
COLOR_BG = "#0B0C10"
COLOR_ACCENT = "#45A29E"
COLOR_SUCCESS = "#66FCF1"
COLOR_TEXT = "#000000"
COLOR_TEXT_ = "#ffffff"
COLOR_TEXT_DIM = "#6B7A8F"
COLOR_SURFACE = "#1F2833"
COLOR_NAV_BTN = "#2C3940"

COLOR_BTN_TXT_LIGHT = "#ffffff"
COLOR_BTN_TXT_DARK = "#0B0C10"

COLOR_NAV_BTN_HOVER = "#45A29E"
COLOR_SUCCESS_HOVER = "#8AFFF5"
COLOR_SURFACE_HOVER = "#354656"
COLOR_INSET = "#121921"

# --- 2. TYPOGRAPHY CONFIGURATION ---
FONT_FAMILY = "Helvetica"
FONT_TITLE = (FONT_FAMILY, 26, "bold")
FONT_HEAD = (FONT_FAMILY, 14, "bold")
FONT_BOLD = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_MICRO = (FONT_FAMILY, 9, "bold")
FONT_BUTTON = (FONT_FAMILY, 12, "bold")
FONT_METRIC = (FONT_FAMILY, 40, "bold")
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


def _unbind_hover(widget: tk.Widget) -> None:
    widget.unbind("<Enter>")
    widget.unbind("<Leave>")


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
            tk.Frame(card, bg=COLOR_SUCCESS, height=3).pack(fill="x")

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
    def _hud_row(
        parent: tk.Widget,
        label: str,
        value: str,
        *,
        top_pad: int = 0,
    ) -> None:
        row = tk.Frame(parent, bg=COLOR_SURFACE)
        row.pack(fill="x", pady=(top_pad, 0), ipadx=2)

        tk.Label(
            row,
            text=label.upper(),
            font=FONT_MICRO,
            bg=COLOR_SURFACE,
            fg=COLOR_ACCENT,
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            row,
            text=value,
            font=FONT_BODY,
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_,
            justify="left",
            anchor="w",
            wraplength=520,
        ).pack(anchor="w", pady=(3, 12))

    @staticmethod
    def _flat_button(
        parent: tk.Widget,
        text: str,
        command,
        *,
        bg: str,
        fg: str,
        hover_bg: str,
        hover_fg: str | None = None,
        font=FONT_BUTTON,
        padx: int = 20,
        pady: int = 10,
        state: str = "normal",
        fill_x: bool = False,
        bind_hover: bool = True,
    ) -> tk.Button:
        if hover_fg is None:
            hover_fg = fg

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
            activeforeground=hover_fg,
            disabledforeground=COLOR_TEXT_DIM,
        )
        if fill_x:
            btn.pack(fill="x")
        if bind_hover and state != "disabled":
            _bind_hover(btn, bg, hover_bg, normal_fg=fg, hover_fg=hover_fg)
        return btn

    # ---------------------------------------------------------------- lifecycle
    def clear_screen(self) -> None:
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.btn_launch = None

    def reset_session(self) -> None:
        """Fully tear down prior analysis state before starting over."""
        cv2.destroyAllWindows()
        self.file_path_var.set("No file selected...")
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
        self._card_title(card, "Tactical HUD")

        self._hud_row(
            card,
            "Camera Lock",
            "Keep the camera stable on a tripod for consistent tracking.",
        )
        self._hud_row(
            card,
            "Asset Ingest",
            "Click Browse Files to load an MP4, MOV, or AVI video asset.",
            top_pad=4,
        )
        self._hud_row(
            card,
            "Target Lock",
            "Draw a box around the BALL first (Red), then the FOOT (Cyan). "
            "Press ENTER to lock each selection.",
            top_pad=4,
        )
        self._hud_row(
            card,
            "Live Telemetry",
            "View real-time, 3D perspective-corrected flight telemetry live.",
            top_pad=4,
        )

        tk.Frame(card, bg=COLOR_SURFACE, height=10).pack()

        tk.Label(
            card,
            text="TARGET REFERENCE GRID",
            font=FONT_MICRO,
            bg=COLOR_SURFACE,
            fg=COLOR_ACCENT,
        ).pack(anchor="w", pady=(0, 6))

        target_frame = tk.Frame(card, bg=COLOR_ACCENT, padx=2, pady=2)
        target_frame.pack(fill="x")

        image_well = tk.Frame(target_frame, bg=COLOR_INSET)
        image_well.pack(fill="x", padx=1, pady=1, ipadx=8, ipady=8)

        image_slot = tk.Label(image_well, bg=COLOR_INSET, fg=COLOR_TEXT_DIM)
        image_slot.pack(padx=10, pady=10)
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
            fg=COLOR_ACCENT,
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
            hover_fg=COLOR_BTN_TXT_DARK,
            padx=18,
            pady=10,
        ).pack(side="right")

        self.btn_launch = self._flat_button(
            card,
            "LAUNCH ANALYTICS",
            self.start_backend,
            bg=COLOR_INSET,
            fg=COLOR_TEXT_DIM,
            hover_bg=COLOR_INSET,
            hover_fg=COLOR_TEXT_DIM,
            font=(FONT_FAMILY, 13, "bold"),
            padx=20,
            pady=18,
            state="disabled",
            fill_x=True,
            bind_hover=False,
        )
        self.btn_launch.pack_configure(ipady=4)

    def _enable_launch_cta(self) -> None:
        if self.btn_launch is None:
            return

        _unbind_hover(self.btn_launch)
        self.btn_launch.config(
            state="normal",
            bg=COLOR_SUCCESS,
            fg=COLOR_BTN_TXT_DARK,
            activebackground=COLOR_SUCCESS_HOVER,
            activeforeground=COLOR_BTN_TXT_DARK,
            cursor="hand2",
        )
        _bind_hover(
            self.btn_launch,
            COLOR_SUCCESS,
            COLOR_SUCCESS_HOVER,
            normal_fg=COLOR_BTN_TXT_DARK,
            hover_fg=COLOR_BTN_TXT_DARK,
        )

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
            fg=COLOR_ACCENT,
        ).pack(pady=(48, 6))

        tk.Label(
            canvas,
            text="FLIGHT ANALYSIS",
            font=FONT_HEAD,
            bg=COLOR_BG,
            fg=COLOR_TEXT_,
        ).pack(pady=(0, 28))

        metric_card = self._card(
            canvas, padx=26, pady=24, outer_pady=(0, 0)
        )

        tk.Label(
            metric_card,
            text="DETECTED SHOT TYPE",
            font=FONT_METRIC_SUB,
            bg=COLOR_SURFACE,
            fg=COLOR_ACCENT,
        ).pack(pady=(0, 14))

        console_shell = tk.Frame(metric_card, bg=COLOR_SUCCESS, padx=2, pady=2)
        console_shell.pack(fill="x")

        console = tk.Frame(console_shell, bg=COLOR_INSET)
        console.pack(fill="x", ipadx=20, ipady=26)

        tk.Label(
            console,
            text="CLASSIFICATION OUTPUT",
            font=FONT_MICRO,
            bg=COLOR_INSET,
            fg=COLOR_TEXT_DIM,
        ).pack(pady=(0, 10))

        tk.Label(
            console,
            text=shot_type.upper(),
            font=FONT_METRIC,
            bg=COLOR_INSET,
            fg=COLOR_SUCCESS,
            wraplength=480,
            justify="center",
        ).pack(padx=12, pady=4)

        tk.Label(
            metric_card,
            text="Perspective-corrected 3D telemetry lock",
            font=FONT_BODY,
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_,
        ).pack(pady=(16, 0))

        action_row = tk.Frame(canvas, bg=COLOR_BG)
        action_row.pack(pady=(36, 40))

        self._flat_button(
            action_row,
            "ANALYZE ANOTHER",
            self.reset_session,
            bg=COLOR_NAV_BTN,
            fg=COLOR_TEXT_,
            hover_bg=COLOR_NAV_BTN_HOVER,
            hover_fg=COLOR_BTN_TXT_DARK,
            padx=36,
            pady=14,
        ).pack()


if __name__ == "__main__":
    root = tk.Tk()
    StrikerApp(root)
    root.mainloop()
