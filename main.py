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

# --- 2. TYPOGRAPHY CONFIGURATION ---
FONT_FAMILY = "Helvetica"
FONT_TITLE = (FONT_FAMILY, 24, "bold")
FONT_HEAD = (FONT_FAMILY, 16, "bold")
FONT_BOLD = (FONT_FAMILY, 12, "bold")
FONT_BODY = (FONT_FAMILY, 11)
FONT_BUTTON = (FONT_FAMILY, 12, "bold")

ANALYSIS_MODE = "Initial Launch"

# --- 3. BACKEND CONNECTION ---
try:
    from track_enigine import run_analysis
except ImportError:
    run_analysis = None
    print("Error: Could not find track_enigine.py.")


class StrikerApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Striker Analytics v1.0")
        self.root.geometry("640x820")
        self.root.minsize(560, 720)
        self.root.configure(bg=COLOR_BG)

        self.file_path_var = tk.StringVar(value="No file selected...")
        self._ref_photo: ImageTk.PhotoImage | None = None
        self.btn_launch: tk.Button | None = None

        self.main_container = tk.Frame(self.root, bg=COLOR_BG)
        self.main_container.pack(expand=True, fill="both", padx=24, pady=20)

        self.show_dashboard()

    def clear_screen(self) -> None:
        for widget in self.main_container.winfo_children():
            widget.destroy()
        self.btn_launch = None

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

        tk.Label(
            self.main_container,
            text="STRIKER ANALYTICS",
            font=FONT_TITLE,
            bg=COLOR_BG,
            fg=COLOR_ACCENT,
        ).pack(pady=(0, 16))

        self._build_instructions_card()
        self._build_file_dashboard()

    def _build_instructions_card(self) -> None:
        card = tk.LabelFrame(
            self.main_container,
            text=" Instructions ",
            font=FONT_BOLD,
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_,
            padx=16,
            pady=12,
            labelanchor="n",
        )
        card.pack(fill="x", pady=(0, 16))

        instructions = (
            "Welcome & Setup\n"
            "Keep the camera stable on a tripod.\n\n"
            "Step 1\n"
            "Click 'Browse Files' to load an MP4, MOV, or AVI video asset.\n\n"
            "Step 2\n"
            "Draw a bounding box around the BALL first (Red), then the FOOT "
            "second (Cyan), and press ENTER to lock each.\n\n"
            "Step 3\n"
            "View real-time, 3D perspective-corrected flight telemetry live."
        )
        tk.Label(
            card,
            text=instructions,
            font=FONT_BODY,
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_,
            justify="left",
            anchor="w",
            wraplength=540,
        ).pack(fill="x", pady=(0, 10))

        image_slot = tk.Label(card, bg=COLOR_SURFACE, fg=COLOR_TEXT_DIM)
        image_slot.pack(pady=(4, 0))
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
                text="[Reference image not found: freekick_ref.png]",
                font=FONT_BODY,
            )

    def _build_file_dashboard(self) -> None:
        section = tk.Frame(self.main_container, bg=COLOR_BG)
        section.pack(fill="x")

        tk.Label(
            section,
            text="VIDEO ASSET",
            font=FONT_HEAD,
            bg=COLOR_BG,
            fg=COLOR_ACCENT,
        ).pack(anchor="w", pady=(0, 8))

        path_row = tk.Frame(section, bg=COLOR_BG)
        path_row.pack(fill="x", pady=(0, 10))

        tk.Label(
            path_row,
            textvariable=self.file_path_var,
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_,
            font=FONT_BOLD,
            anchor="w",
            padx=10,
            pady=8,
            wraplength=480,
        ).pack(side="left", fill="x", expand=True, padx=(0, 10))

        tk.Button(
            path_row,
            text="Browse Files",
            command=self.browse_files,
            bg=COLOR_NAV_BTN,
            fg=COLOR_BTN_TXT_LIGHT,
            font=FONT_BUTTON,
            relief="flat",
            padx=14,
            pady=6,
            activebackground=COLOR_NAV_BTN,
            activeforeground=COLOR_BTN_TXT_LIGHT,
        ).pack(side="right")

        self.btn_launch = tk.Button(
            section,
            text="LAUNCH ANALYTICS",
            state="disabled",
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_DIM,
            font=FONT_BUTTON,
            pady=14,
            command=self.start_backend,
            relief="flat",
            activebackground=COLOR_SUCCESS,
        )
        self.btn_launch.pack(fill="x", pady=(18, 0))

    def browse_files(self) -> None:
        filename = filedialog.askopenfilename(
            filetypes=[("Video files", "*.mp4 *.mov *.avi")]
        )
        if not filename or self.btn_launch is None:
            return
        self.file_path_var.set(filename)
        self.btn_launch.config(
            state="normal",
            bg=COLOR_SUCCESS,
            fg=COLOR_BTN_TXT_DARK,
            activeforeground=COLOR_BTN_TXT_DARK,
        )

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

        frame = tk.Frame(self.main_container, bg=COLOR_BG)
        frame.pack(expand=True, fill="both")

        tk.Label(
            frame,
            text="ANALYSIS COMPLETE",
            font=FONT_HEAD,
            bg=COLOR_BG,
            fg=COLOR_ACCENT,
        ).pack(pady=(40, 10))

        result_card = tk.Frame(frame, bg=COLOR_SURFACE, padx=40, pady=30)
        result_card.pack(pady=20, fill="x")

        tk.Label(
            result_card,
            text="DETECTED SHOT TYPE:",
            font=FONT_BOLD,
            bg=COLOR_SURFACE,
            fg=COLOR_TEXT_DIM,
        ).pack()

        tk.Label(
            result_card,
            text=shot_type.upper(),
            font=(FONT_FAMILY, 22, "bold"),
            bg=COLOR_SURFACE,
            fg=COLOR_SUCCESS,
        ).pack(pady=15)

        tk.Button(
            frame,
            text="ANALYZE ANOTHER",
            command=self.reset_session,
            bg=COLOR_NAV_BTN,
            fg=COLOR_BTN_TXT_LIGHT,
            font=FONT_BUTTON,
            relief="flat",
            padx=25,
            pady=12,
            activebackground=COLOR_NAV_BTN,
            activeforeground=COLOR_BTN_TXT_LIGHT,
        ).pack(pady=20)


if __name__ == "__main__":
    root = tk.Tk()
    StrikerApp(root)
    root.mainloop()
