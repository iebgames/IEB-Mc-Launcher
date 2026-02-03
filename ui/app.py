import customtkinter as ctk
import os
from PIL import Image, ImageTk, ImageSequence
from .pages.home import HomePage
from .pages.mods import ModsPage
from .pages.settings import SettingsPage
from .pages.store import StorePage
from .pages.statistics import StatisticsPage
from .pages.console import ConsolePage
from .pages.profiles import ProfilesPage

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("IEB-MC-Launcher")
        self.geometry("1100x700")
        self.resizable(True, True)
        
        try:
            from PIL import Image, ImageTk
            # Use ImageTk for window icon (tkinter compatible)
            icon_img = ImageTk.PhotoImage(file="assets/logo.png")
            self.wm_iconphoto(False, icon_img)
        except Exception as e:
            print(f"Icon error: {e}")

        # Layout configuration
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Create sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(0, weight=1)
        
        # Sidebar Canvas (for BG and Layout)
        import tkinter as tk
        self.sidebar_canvas = tk.Canvas(self.sidebar_frame, width=200, highlightthickness=0, bg="#2b2b2b")
        self.sidebar_canvas.pack(fill="both", expand=True)
        
        # Background Image Item
        self.gif_bg_item = self.sidebar_canvas.create_image(0, 0, anchor="nw")
        
        # Logo & Text (Drawn on Canvas for transparency)
        try:
            logo_img = ctk.CTkImage(Image.open("assets/logo.png"), size=(60, 60))
            # Convert to TK for Canvas
            # We need a permanent reference to prevent GC
            self.logo_tk = ImageTk.PhotoImage(Image.open("assets/logo.png").resize((60, 60))) 
            self.logo_item = self.sidebar_canvas.create_image(100, 40, image=self.logo_tk, anchor="center")
        except:
            self.logo_item = None
            
        self.title_item = self.sidebar_canvas.create_text(100, 85, text="IEB Games", font=("Arial", 16, "bold"), fill="white")

        # Buttons (Embedded Windows)
        # Helper to add button
        self.sidebar_buttons = [] # To toggle visibility
        
        def add_sidebar_btn(text, cmd, y_pos, fg_color=None, hover_color=None):
            btn = ctk.CTkButton(self.sidebar_canvas, text=text, command=cmd, width=160, height=32)
            if fg_color: btn.configure(fg_color=fg_color)
            if hover_color: btn.configure(hover_color=hover_color)
            
            # Button BG fix: try to match or set transparent? 
            # CTk buttons don't support true transparent bg on Canvas easily, 
            # but they look better than labels.
            
            win_id = self.sidebar_canvas.create_window(100, y_pos, window=btn, anchor="center")
            self.sidebar_buttons.append(win_id)
            return btn

        # Instagram
        import webbrowser
        self.insta_button = add_sidebar_btn("Instagram", lambda: webbrowser.open("https://www.instagram.com/ieb_software/"), 130, fg_color="#E1306C", hover_color="#C13584")

        # Nav Buttons
        y_start = 180
        gap = 45
        
        self.home_button = add_sidebar_btn("Home", lambda: self.show_frame("Home"), y_start)
        self.store_button = add_sidebar_btn("Store", lambda: self.show_frame("Store"), y_start + gap, fg_color="#FFD700", hover_color="#B8860B")
        self.store_button.configure(text_color="black")
        
        self.mods_button = add_sidebar_btn("Mods", lambda: self.show_frame("Mods"), y_start + gap*2)
        self.settings_button = add_sidebar_btn("Settings", lambda: self.show_frame("Settings"), y_start + gap*3)
        self.profiles_button = add_sidebar_btn("Profiles", lambda: self.show_frame("Profiles"), y_start + gap*4)
        self.stats_button = add_sidebar_btn("Statistics", lambda: self.show_frame("Statistics"), y_start + gap*5)
        self.console_button = add_sidebar_btn("Console", lambda: self.show_frame("Console"), y_start + gap*6)
        
        # Hide/Show Toggle Button (Eye)
        # Position at bottom left
        self.sidebar_visible = True
        self.eye_btn = ctk.CTkButton(self.sidebar_canvas, text="👁", width=40, height=40, command=self.toggle_sidebar)
        self.eye_win = self.sidebar_canvas.create_window(30, 670, window=self.eye_btn, anchor="sw") 
        
        # GIF Toggle Button (X/O)
        self.gif_running = False # Initial state will be set to True in load_gif
        self.gif_btn = ctk.CTkButton(self.sidebar_canvas, text="X", width=40, height=40, command=self.toggle_gif, fg_color="#C0392B", hover_color="#E74C3C")
        self.gif_win = self.sidebar_canvas.create_window(80, 670, window=self.gif_btn, anchor="sw")

        # Bind resize for eye button position?
        self.sidebar_canvas.bind("<Configure>", self.on_sidebar_resize)

        # Load GIF logic
        self.load_gif()

    def on_sidebar_resize(self, event):
        # Keep buttons at bottom
        h = event.height
        self.sidebar_canvas.coords(self.eye_win, 30, h - 30)
        self.sidebar_canvas.coords(self.gif_win, 80, h - 30)

        # Main Content Area
        if not hasattr(self, 'main_frame'):
            self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
            self.main_frame.grid(row=0, column=1, sticky="nsew")
            self.main_frame.grid_rowconfigure(0, weight=1)
            self.main_frame.grid_columnconfigure(0, weight=1)
            
            # Pages
            self.pages = {}
            
            # Initialize Home Page
            self.pages["Home"] = HomePage(self.main_frame, self)
            self.pages["Home"].grid(row=0, column=0, sticky="nsew")
            
            # Initialize Mods Page
            self.pages["Mods"] = ModsPage(self.main_frame, self)
            self.pages["Mods"].grid(row=0, column=0, sticky="nsew")
            
            # Initialize Settings Page
            self.pages["Settings"] = SettingsPage(self.main_frame, self)
            self.pages["Settings"].grid(row=0, column=0, sticky="nsew")
            
            # Initialize Store Page
            self.pages["Store"] = StorePage(self.main_frame, self)
            self.pages["Store"].grid(row=0, column=0, sticky="nsew")
            
            # Initialize Statistics Page
            self.pages["Statistics"] = StatisticsPage(self.main_frame, self)
            self.pages["Statistics"].grid(row=0, column=0, sticky="nsew")
            
            # Initialize Console Page
            self.pages["Console"] = ConsolePage(self.main_frame, self)
            self.pages["Console"].grid(row=0, column=0, sticky="nsew")
            
            # Initialize Profiles Page
            self.pages["Profiles"] = ProfilesPage(self.main_frame, self)
            self.pages["Profiles"].grid(row=0, column=0, sticky="nsew")

    def toggle_sidebar(self):
        self.sidebar_visible = not self.sidebar_visible
        
        state = "normal" if self.sidebar_visible else "hidden"
        
        # Toggle Logo/Text
        if self.logo_item: self.sidebar_canvas.itemconfigure(self.logo_item, state=state)
        self.sidebar_canvas.itemconfigure(self.title_item, state=state)
        
        # Toggle Buttons
        for btn_id in self.sidebar_buttons:
             self.sidebar_canvas.itemconfigure(btn_id, state=state)
             
        # Change Eye Icon?
        self.eye_btn.configure(text="👁" if self.sidebar_visible else "🔒")

    def toggle_gif(self):
        self.gif_running = not self.gif_running
        
        if self.gif_running:
            # Enable
            self.gif_btn.configure(text="X", fg_color="#C0392B", hover_color="#E74C3C") # Red for Stop
            self.sidebar_canvas.itemconfigure(self.gif_bg_item, state="normal")
            if hasattr(self, 'gif_frames') and self.gif_frames:
                self.animate_gif()
        else:
            # Disable
            self.gif_btn.configure(text="O", fg_color="#27AE60", hover_color="#2ECC71") # Green for Play
            self.sidebar_canvas.itemconfigure(self.gif_bg_item, state="hidden")

    def load_gif(self):
        try:
             from PIL import ImageSequence
             # Create frames
             self.gif_frames = []
             if os.path.exists("assets/l_panel.gif"):
                 im = Image.open("assets/l_panel.gif")
                 print(f"GIF found. Frames: {getattr(im, 'n_frames', 1)}")
                 for frame in ImageSequence.Iterator(im):
                     # Resize to fill sidebar (fixed width 200)
                     # Height needs to be enough to cover. 1200 is safe.
                     frame = frame.convert("RGBA")
                     frame = frame.resize((200, 1200), Image.Resampling.LANCZOS) 
                     self.gif_frames.append(ImageTk.PhotoImage(frame)) # Use ImageTk for Canvas
                 
                 if self.gif_frames:
                     self.gif_idx = 0
                     print("Starting GIF animation...")
                     self.gif_running = True # Start running
                     self.animate_gif()
             else:
                 print("GIF not found (l_panel.gif), skipping.")
        except Exception as e:
             print(f"GIF Load Error: {e}")
             import traceback
             traceback.print_exc()

    def animate_gif(self):
        if hasattr(self, 'gif_frames') and self.gif_frames and self.gif_running:
            self.sidebar_canvas.itemconfig(self.gif_bg_item, image=self.gif_frames[self.gif_idx])
            self.gif_idx = (self.gif_idx + 1) % len(self.gif_frames)
            self.after(200, self.animate_gif)
            
    def show_frame(self, page_name):
        if page_name in self.pages:
            self.pages[page_name].tkraise()
        else:
            print(f"Page {page_name} not implemented yet.")
            
    def destroy(self):
        from utils.discord_rpc import rpc_client
        rpc_client.close()
        super().destroy()
