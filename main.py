import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk

# --- 1. THEME CONFIGURATION ---
COLOR_BG      = "#1e1e1e"  # Main background (Dark Grey)
COLOR_ACCENT  = "#0048FF"  # Primary headings (Blue)
COLOR_SUCCESS = "#0048FF"  # Success states & Main buttons (Blue)
COLOR_TEXT    = "#000000"  # Primary body text (Black)
COLOR_TEXT_   = "#ffffff"  # Secondary body text & High-contrast text (White)
COLOR_TEXT_DIM = "#888888" # Disabled button text (Lighter Grey for better contrast)
COLOR_SURFACE = "#2d2d2d"  # Card backgrounds (Lighter Grey)
COLOR_NAV_BTN = "#444444"  # Navigation button color

# Dedicated button text colors to ensure high contrast
COLOR_BTN_TXT_LIGHT = "#ffffff" # For dark buttons (Blue, Dark Grey)
COLOR_BTN_TXT_DARK  = "#1e1e1e" # For light buttons (if you add any later)

# --- 2. TYPOGRAPHY CONFIGURATION ---
FONT_FAMILY = "Helvetica"
FONT_TITLE  = (FONT_FAMILY, 28, "bold")
FONT_HEAD   = (FONT_FAMILY, 20, "bold")
FONT_BOLD   = (FONT_FAMILY, 14, "bold")
FONT_BUTTON = (FONT_FAMILY, 12, "bold")

# --- 3. BACKEND CONNECTION ---
try:
    from track_enigine import run_analysis 
except ImportError:
    print("Error: Could not find track_enigine.py.")

class StrikerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Striker Analytics v1.0")
        self.root.geometry("600x550")
        self.root.configure(bg=COLOR_BG)

        # NEW: State management for the Analysis Mode toggle
        self.analysis_mode = tk.StringVar(value="Initial Launch")

        self.slides = [
            "Welcome to Striker Analytics!\n\nThis tool helps you analyze the physics of your free kicks.",
            "STEP 1: Upload your video.\n\nMake sure the camera is stable and shows the full ball flight.",
            "EXAMPLE: ",
            "STEP 2: Selection.\n\nYou will draw a box around the BALL first (Red),\nthen the FOOT second (Blue).",
            "STEP 3: Analysis.\n\nThe AI will calculate launch angle and shot category.",
            "Ready to improve your game?\nSelect a video file to begin."
        ]
        self.current_slide = 0
        self.main_container = tk.Frame(self.root, bg=COLOR_BG)
        self.main_container.pack(expand=True, fill="both")
        
        self.show_welcome_screen()

    def clear_screen(self):
        """Clears the main container for fresh UI rendering."""
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_welcome_screen(self):
        self.clear_screen()
        frame = tk.Frame(self.main_container, bg=COLOR_BG)
        frame.pack(expand=True)
        
        tk.Label(frame, text="STRIKER ANALYTICS", font=FONT_TITLE, 
                 bg=COLOR_BG, fg=COLOR_ACCENT).pack(pady=20)
        
        # High-Contrast Start Button
        tk.Button(frame, text="START TUTORIAL", font=FONT_BUTTON, 
                  bg=COLOR_SUCCESS, fg=COLOR_BTN_TXT_DARK, 
                  padx=30, pady=12, command=self.show_slideshow, 
                  relief="flat", activebackground="#ffffff").pack()

    def update_slide_image(self):
        """Displays the reference image on the specific tutorial slide."""
        if self.current_slide == 2:
            try:
                img = Image.open("freekick_ref.png") 
                img = img.resize((300, 200), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                self.image_label.config(image=self.photo)
                self.image_label.image = self.photo 
            except:
                self.image_label.config(image='', text="[Image Not Found]")
        else:
            self.image_label.config(image='', text="")

    def show_slideshow(self):
        self.clear_screen()
        self.slide_frame = tk.Frame(self.main_container, bg=COLOR_BG)
        self.slide_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        self.image_label = tk.Label(self.slide_frame, bg=COLOR_BG, fg=COLOR_TEXT_DIM)
        self.image_label.pack(pady=10)
        
        self.instruction_label = tk.Label(self.slide_frame, text=self.slides[self.current_slide],
                                         font=FONT_BOLD, bg=COLOR_BG, fg=COLOR_TEXT_, 
                                         wraplength=500, justify="center")
        self.instruction_label.pack(expand=True)
        
        # Navigation Button
        self.btn_nav = tk.Button(self.slide_frame, text="NEXT →", command=self.next_slide,
                                bg=COLOR_NAV_BTN, fg=COLOR_TEXT, font=FONT_BUTTON, 
                                relief="flat", padx=20, pady=8)
        self.btn_nav.pack(side="bottom", pady=20)
        self.update_slide_image()

    def next_slide(self):
        self.current_slide += 1
        if self.current_slide < len(self.slides):
            self.instruction_label.config(text=self.slides[self.current_slide])
            self.update_slide_image()
        else:
            self.show_upload_screen()

    def show_upload_screen(self):
        self.clear_screen()
        frame = tk.Frame(self.main_container, bg=COLOR_BG)
        frame.pack(expand=True)

        tk.Label(frame, text="ANALYSIS SETTINGS", font=FONT_HEAD, 
                 bg=COLOR_BG, fg=COLOR_ACCENT).pack(pady=10)

        # MODE SELECTOR BOX (The Toggle Feature)
        mode_frame = tk.LabelFrame(frame, text=" Result Capture Mode ", font=FONT_BOLD, 
                                  bg=COLOR_BG, fg=COLOR_TEXT_, padx=20, pady=10)
        mode_frame.pack(pady=15)

        tk.Radiobutton(mode_frame, text="Initial Launch (Locks first result)", variable=self.analysis_mode, 
                       value="Initial Launch", bg=COLOR_BG, fg=COLOR_TEXT_, selectcolor=COLOR_SURFACE,
                       activebackground=COLOR_BG, font=FONT_BOLD).pack(anchor="w")
        
        tk.Radiobutton(mode_frame, text="Full Trajectory (End of video)", variable=self.analysis_mode, 
                       value="Full Trajectory", bg=COLOR_BG, fg=COLOR_TEXT_, selectcolor=COLOR_SURFACE,
                       activebackground=COLOR_BG, font=FONT_BOLD).pack(anchor="w")

        # FILE SELECTION
        self.file_path_var = tk.StringVar(value="No file selected...")
        tk.Label(frame, textvariable=self.file_path_var, bg=COLOR_SURFACE, 
                 fg=COLOR_TEXT_, font=FONT_BOLD, width=50, pady=5).pack(pady=10)
        
        tk.Button(frame, text="Browse Files", command=self.browse_files, 
                  bg=COLOR_NAV_BTN, fg=COLOR_TEXT, font=FONT_BUTTON, 
                  relief="flat", padx=15, pady=5).pack()
        
        self.btn_launch = tk.Button(frame, text="LAUNCH ANALYTICS", state="disabled", 
                                   bg=COLOR_SURFACE, fg=COLOR_TEXT_DIM, 
                                   font=FONT_BUTTON, pady=12, width=22, 
                                   command=self.start_backend, relief="flat")
        self.btn_launch.pack(pady=30)

    def browse_files(self):
        filename = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.avi")])
        if filename:
            self.file_path_var.set(filename)
            # Make the button turn "Active" Cyan with Dark Text
            self.btn_launch.config(state="normal", bg=COLOR_SUCCESS, fg=COLOR_BTN_TXT_DARK)

    def start_backend(self):
        video_path = self.file_path_var.get()
        selected_mode = self.analysis_mode.get() 
        
        if video_path and video_path != "No file selected...":
            self.root.withdraw() 
            # Passing both the file and the user-selected mode
            analysis_result = run_analysis(video_path, mode=selected_mode) 
            self.root.deiconify() 
            self.show_results_screen(analysis_result)

    def show_results_screen(self, shot_type):
        self.clear_screen()
        frame = tk.Frame(self.main_container, bg=COLOR_BG)
        frame.pack(expand=True)

        tk.Label(frame, text="ANALYSIS COMPLETE", font=FONT_HEAD, 
                 bg=COLOR_BG, fg=COLOR_ACCENT).pack(pady=10)
        
        result_card = tk.Frame(frame, bg=COLOR_SURFACE, padx=40, pady=30)
        result_card.pack(pady=20)
        
        tk.Label(result_card, text="DETECTED SHOT TYPE:", font=FONT_BOLD, 
                 bg=COLOR_SURFACE, fg=COLOR_TEXT_DIM).pack()
        
        tk.Label(result_card, text=shot_type.upper(), font=(FONT_FAMILY, 22, "bold"), 
                 bg=COLOR_SURFACE, fg=COLOR_SUCCESS).pack(pady=15)

        tk.Button(frame, text="ANALYZE ANOTHER", command=self.show_welcome_screen, 
                  bg=COLOR_NAV_BTN, fg=COLOR_TEXT, font=FONT_BUTTON, 
                  relief="flat", padx=25, pady=12).pack(pady=20)

if __name__ == "__main__":
    root = tk.Tk()
    app = StrikerApp(root)
    root.mainloop()