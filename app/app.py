import tkinter as tk
from tkinter import ttk
import os
from PIL import Image, ImageTk
import src.sensors_frame as SF
from src.config import SENSOR_CONFIG
import src.upload as upload

class Application(tk.Tk):
    # defining color codes 
    __green = "#589954"
    __black = "#000000"
    __white = "#ffffff"
    __grey = "#1e1e1e"
    bg_ = __black

    # fixing Color schemes
    nav_txt_ = __white

    # variables
    app_dim = "1920x1080"

    # navbar settings
    nav_bg_ = __black
    def __init__(self):
        super().__init__()

        # Configure window
        self.title("Smart Sensor Workstation")
        self.attributes("-fullscreen", True)
        self.configure(bg=self.bg_)
        self.geometry(self.app_dim)

        def toggle_fullscreen(event=None):
            self.attributes("-fullscreen", not self.attributes("-fullscreen"))

        self.bind("<F11>", toggle_fullscreen)
        self.create_navbar()

        self.home_screen()

    def create_navbar(self):
        # Create the navbar frame
        self.navbar = tk.Frame(self, bg=self.nav_bg_, height=100)
        self.navbar.pack(fill=tk.X)

        # Configure 3 equal columns so the center stays perfectly centered
        self.navbar.grid_columnconfigure(0, weight=1)
        self.navbar.grid_columnconfigure(1, weight=0)
        self.navbar.grid_columnconfigure(2, weight=1)

        # Left icon
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_img = Image.open(os.path.join(script_dir, "assets", "bodhi_cube.png")).resize((80, 80), Image.Resampling.LANCZOS)
            self.icon_photo = ImageTk.PhotoImage(icon_img)
            icon_label = tk.Label(self.navbar, image=self.icon_photo, bg=self.nav_bg_)
            icon_label.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(10, 0))
        except Exception as e:
            print(f"[WARNING] Couldn't load icon: {e}")

        # Title in the exact center
        title = tk.Label(self.navbar, text="Smart Sensor Workstation",
                        font=("segoe-ui", 24, "bold"),
                        bg=self.nav_bg_, fg=self.nav_txt_)
        title.grid(row=0, column=1, sticky="nsew")

        # Right logo
        try:
            logo_img = Image.open(os.path.join(script_dir, "assets", "bodh.png")).resize((120, 80), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            logo_label = tk.Label(self.navbar, image=self.logo_photo, bg=self.nav_bg_)
            logo_label.grid(row=0, column=2, sticky="e", padx=(0, 10), pady=(10, 0))
        except Exception as e:
            print(f"[WARNING] Couldn't load logo: {e}")
    #___________________________________________________________________

    def create_button_frame(self):
        """Create the frame with sensor buttons"""
        main_frame = tk.Frame(self, bg=self.bg_)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=50)

        button_frame = tk.Frame(main_frame, bg=self.nav_bg_)
        button_frame.pack()

        for i, sensor_config in enumerate(SENSOR_CONFIG):
            row = i // 2
            col = i % 2

            btn = tk.Button(button_frame, text=sensor_config["name"],
                           bg=self.__green, fg="white",
                           font=("Arial", 12, "bold"),
                           width=30, height=2,
                           command=lambda sc=sensor_config: self.show_sensor_screen(sc),
                           bd=0, cursor="hand2",
                           activebackground=self.__green,
                           activeforeground="white")
            btn.grid(row=row, column=col, padx=20, pady=15)
    #___________________________________________________________________

    def home_screen(self):
        self.create_button_frame()
    #___________________________________________________________________

    def clear_screen_except_navbar(self):
        for widget in self.winfo_children():
            if widget is self.navbar:
                continue
            widget.destroy()
    #___________________________________________________________________

    def show_sensor_screen(self, sensor_config):
        #Display the appropriate sensor screen
        self.clear_screen_except_navbar()
        # Pass the entire sensor_config to the frame
        sensor_frame_instance = SF.display(self, sensor_config)
        
        sensor_frame_instance.get_frame().pack(fill=tk.BOTH, expand=True)
    #___________________________________________________________________

if __name__ == "__main__":
    app = Application()
    app.mainloop()
    