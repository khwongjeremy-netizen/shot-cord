import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

# --- 1. HIGH-CONTRAST CYBER-GLOW THEME ---
COLOR_BG = "#0A0B10"          # Obsidian Shadow Base
COLOR_SURFACE = "#151922"     # Deep Tactical Charcoal Card Surface
COLOR_INSET = "#0F1117"       # Recessed Matte Slate Terminal Box
COLOR_ACCENT = "#0048FF"      # The Core Electric Blue Cyber-Glow Highlight
COLOR_SUCCESS = "#3372FF"     # Kinetic Cobalt Neon Trigger Blue
COLOR_TEXT = "#FFFFFF"        # Pure white high-contrast text
COLOR_TEXT_DIM = "#7A8AB8"    # Soft neon-muted text
COLOR_BORDER = "#0C4BFF"      # Deeper accent border

# --- 2. HUD TYPOGRAPHY SYSTEM ---
FONT_FAMILY = "Helvetica"
FONT_TITLE = (FONT_FAMILY, 28, "bold")
FONT_HEAD = (FONT_FAMILY, 20, "bold")
FONT_BODY = (FONT_FAMILY, 12)
FONT_MICRO = (FONT_FAMILY, 9, "bold")
FONT_BUTTON = (FONT_FAMILY, 11, "bold")
FONT_METRIC = (FONT_FAMILY, 26, "bold")

# --- 3. BACKEND CONNECTION ---
try:
    from track_enigine import run_analysis
except ImportError:
    print("Error: Could not find track_enigine.py.")

class StrikerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Striker Analytics v1.0")
        self.root.geometry("640x580")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        self.analysis_mode = tk.StringVar(value="Initial Launch")
        self.file_path_var = tk.StringVar(value="NO VIDEO SELECTED")
        self.current_slide = 0
        self.slides = [
            "Welcome to Striker Analytics! This HUD tutorial prepares the launch pipeline.",
            "STEP 01: Verify the reference target frame then continue to asset upload.",
            "STEP 02: Select a valid video file and engage the engine with the launch CTA.",
        ]

        self.main_container = tk.Frame(self.root, bg=COLOR_BG)
        self.main_container.pack(expand=True, fill="both")
        self.show_welcome_screen()

    def clear_screen(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def _bind_hover(self, widget, normal_bg, hover_bg):
        widget.bind("<Enter>", lambda event: widget.config(bg=hover_bg))
        widget.bind("<Leave>", lambda event: widget.config(bg=normal_bg))

    def _enable_launch_cta(self):
        self.btn_launch.config(state="normal", bg=COLOR_SUCCESS, fg=COLOR_TEXT,
                               activebackground=COLOR_ACCENT,
                               activeforeground=COLOR_TEXT)
        self._bind_hover(self.btn_launch, COLOR_SUCCESS, COLOR_ACCENT)

    def show_welcome_screen(self):
        self.clear_screen()
        layout = tk.Frame(self.main_container, bg=COLOR_SURFACE,
                          highlightthickness=1, highlightbackground=COLOR_ACCENT,
                          bd=0, padx=24, pady=24)
        layout.pack(expand=True, fill="both", padx=24, pady=24)

        tk.Label(layout, text="STRIKER ANALYTICS", font=FONT_TITLE,
                 bg=COLOR_SURFACE, fg=COLOR_ACCENT).pack(anchor="w")

        tk.Label(layout,
                 text="A streamlined HUD workflow that moves you from reference review to engine launch.",
                 font=FONT_BODY, bg=COLOR_SURFACE, fg=COLOR_TEXT,
                 wraplength=560, justify="left").pack(anchor="w", pady=(8, 18))

        for idx, slide in enumerate(self.slides, start=1):
            card = tk.Frame(layout, bg=COLOR_INSET, bd=0, padx=14, pady=12)
            card.pack(fill="x", pady=(0, 12))
            tk.Label(card, text=f"STEP {idx:02d}", font=FONT_MICRO,
                     bg=COLOR_INSET, fg=COLOR_ACCENT).pack(anchor="w")
            tk.Label(card, text=slide, font=FONT_BODY,
                     bg=COLOR_INSET, fg=COLOR_TEXT,
                     wraplength=540, justify="left").pack(anchor="w", pady=(6, 0))

        reference_card = tk.Frame(layout, bg=COLOR_INSET, bd=1,
                                  highlightthickness=1, highlightbackground=COLOR_ACCENT)
        reference_card.pack(fill="both", expand=True, pady=(0, 18))

        self.image_label = tk.Label(reference_card, bg=COLOR_INSET,
                                    fg=COLOR_TEXT_DIM, width=62, height=14)
        self.image_label.pack(expand=True, fill="both", padx=12, pady=12)
        self.update_slide_image()

        continue_btn = tk.Button(layout, text="CONTINUE", font=FONT_BUTTON,
                                 bg=COLOR_SUCCESS, fg=COLOR_TEXT,
                                 relief="flat", padx=24, pady=12,
                                 cursor="hand2", command=self.show_upload_screen)
        continue_btn.pack(pady=(0, 0))
        self._bind_hover(continue_btn, COLOR_SUCCESS, COLOR_ACCENT)

    def update_slide_image(self):
        try:
            img = Image.open("freekick_ref.png")
            img.thumbnail((520, 0), Image.Resampling.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.image_label.config(image=self.photo, text="")
        except Exception:
            self.image_label.config(text="REFERENCE TRACKING ASSET NOT FOUND",
                                    fg=COLOR_TEXT_DIM)

    def show_upload_screen(self):
        self.clear_screen()
        container = tk.Frame(self.main_container, bg=COLOR_BG)
        container.pack(expand=True, fill="both", padx=24, pady=24)

        header = tk.Frame(container, bg=COLOR_BG)
        header.pack(fill="x", pady=(0, 18))

        back_btn = tk.Button(header, text="BACK TO INSTRUCTIONS", font=(FONT_FAMILY, 10, "bold"),
                             bg=COLOR_SURFACE, fg=COLOR_ACCENT,
                             relief="flat", padx=16, pady=8,
                             cursor="hand2", command=self.show_welcome_screen)
        back_btn.pack(side="left")
        self._bind_hover(back_btn, COLOR_SURFACE, COLOR_ACCENT)

        tk.Label(header, text="UPLOAD VIDEO VIEW", font=FONT_HEAD,
                 bg=COLOR_BG, fg=COLOR_ACCENT).pack(side="right")

        dashboard_card = tk.Frame(container, bg=COLOR_SURFACE,
                                  highlightthickness=1, highlightbackground=COLOR_ACCENT,
                                  bd=0, padx=24, pady=24)
        dashboard_card.pack(fill="both", expand=True)

        tk.Label(dashboard_card, text="STEP 02", font=FONT_MICRO,
                 bg=COLOR_SURFACE, fg=COLOR_ACCENT, anchor="w").pack(anchor="w")
        tk.Label(dashboard_card, text="Load your video asset and activate the launch CTA.",
                 font=FONT_BODY, bg=COLOR_SURFACE, fg=COLOR_TEXT,
                 wraplength=560, justify="left").pack(anchor="w", pady=(4, 18))

        mode_box = tk.LabelFrame(dashboard_card, text=" Result Capture Mode ",
                                 font=(FONT_FAMILY, 10, "bold"), bg=COLOR_SURFACE,
                                 fg=COLOR_TEXT, bd=0, highlightthickness=1,
                                 highlightbackground=COLOR_BORDER, padx=18, pady=16)
        mode_box.pack(fill="x", pady=(0, 20))

        tk.Radiobutton(mode_box, text="Initial Launch (Locks first result)",
                       variable=self.analysis_mode, value="Initial Launch",
                       bg=COLOR_SURFACE, fg=COLOR_TEXT, selectcolor=COLOR_INSET,
                       activebackground=COLOR_SURFACE, font=FONT_BODY,
                       anchor="w", justify="left").pack(anchor="w", pady=2)
        tk.Radiobutton(mode_box, text="Full Trajectory (End of video)",
                       variable=self.analysis_mode, value="Full Trajectory",
                       bg=COLOR_SURFACE, fg=COLOR_TEXT, selectcolor=COLOR_INSET,
                       activebackground=COLOR_SURFACE, font=FONT_BODY,
                       anchor="w", justify="left").pack(anchor="w", pady=2)

        file_display = tk.Label(dashboard_card, textvariable=self.file_path_var,
                                font=FONT_BODY, bg=COLOR_INSET, fg=COLOR_TEXT,
                                anchor="w", justify="left", wraplength=560,
                                padx=14, pady=14)
        file_display.pack(fill="x")

        controls = tk.Frame(dashboard_card, bg=COLOR_SURFACE)
        controls.pack(fill="x", pady=(18, 0))

        browse_button = tk.Button(controls, text="BROWSE FILES", font=FONT_BUTTON,
                                  bg=COLOR_ACCENT, fg=COLOR_ACCENT,
                                  relief="flat", padx=22, pady=10,
                                  cursor="hand2", command=self.browse_files)
        browse_button.pack(side="left")
        self._bind_hover(browse_button, COLOR_ACCENT, COLOR_SUCCESS)

        self.btn_launch = tk.Button(dashboard_card, text="LAUNCH ANALYTICS",
                                    state="disabled", bg=COLOR_INSET,
                                    fg=COLOR_TEXT_DIM, font=FONT_BUTTON,
                                    pady=14, width=34,
                                    command=self.start_backend,
                                    relief="flat", cursor="hand2")
        self.btn_launch.pack(pady=(24, 0))

    def browse_files(self):
        filename = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.avi")])
        if filename:
            self.file_path_var.set(filename)
            self._enable_launch_cta()

    def start_backend(self):
        video_path = self.file_path_var.get()
        selected_mode = self.analysis_mode.get()

        if video_path and video_path != "NO VIDEO SELECTED":
            self.root.withdraw()
            analysis_result = run_analysis(video_path, mode=selected_mode)
            self.root.deiconify()
            self.show_results_screen(analysis_result)

    def show_results_screen(self, shot_type):
        self.clear_screen()
        frame = tk.Frame(self.main_container, bg=COLOR_BG)
        frame.pack(expand=True, fill="both", padx=24, pady=24)

        tk.Label(frame, text="ANALYSIS COMPLETE", font=FONT_HEAD,
                 bg=COLOR_BG, fg=COLOR_ACCENT).pack(pady=(0, 18))

        result_card = tk.Frame(frame, bg=COLOR_INSET,
                               highlightthickness=1, highlightbackground=COLOR_ACCENT,
                               bd=0, padx=28, pady=24)
        result_card.pack(fill="both", expand=True)

        tk.Label(result_card, text="FINAL PAYLOAD SHEET", font=FONT_MICRO,
                 bg=COLOR_INSET, fg=COLOR_ACCENT, anchor="w").pack(anchor="w")
        tk.Label(result_card, text="Shot classification delivered as a real-time tactical HUD output.",
                 font=FONT_BODY, bg=COLOR_INSET, fg=COLOR_TEXT,
                 wraplength=560, justify="left").pack(anchor="w", pady=(4, 18))

        accent_bar = tk.Frame(result_card, bg=COLOR_ACCENT, height=3)
        accent_bar.pack(fill="x", pady=(0, 18))

        tk.Label(result_card, text=shot_type.upper(), font=FONT_METRIC,
                 bg=COLOR_INSET, fg=COLOR_SUCCESS,
                 wraplength=560, justify="center").pack(pady=(0, 18))

        tk.Label(result_card,
                 text="The detected shot classification is shown above in the core analysis console.",
                 font=FONT_BODY, bg=COLOR_INSET, fg=COLOR_TEXT_DIM,
                 wraplength=560, justify="center").pack(pady=(0, 14))

        analyze_again_btn = tk.Button(frame, text="ANALYZE ANOTHER", font=FONT_BUTTON,
                                      bg=COLOR_ACCENT, fg=COLOR_TEXT,
                                      relief="flat", padx=26, pady=12,
                                      cursor="hand2", command=self.show_welcome_screen)
        analyze_again_btn.pack(pady=(14, 0))
        self._bind_hover(analyze_again_btn, COLOR_ACCENT, COLOR_SUCCESS)

if __name__ == "__main__":
    root = tk.Tk()
    app = StrikerApp(root)
    root.mainloop()
