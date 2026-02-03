import customtkinter as ctk
import tkinter as tk
import threading
from PIL import Image, ImageTk, ImageFilter
from launcher_core import LauncherCore
from utils.profiles import ProfileManager
from utils.config import Config
from utils.discord_rpc import rpc_client

from utils.instance_manager import InstanceManager
import os

class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        
        # Initialize Core components
        self.launcher = LauncherCore()
        ProfileManager.load()
        
        # Setup Canvas
        self.canvas = tk.Canvas(self, highlightthickness=0, bg="#2b2b2b")
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Load Image Data (keep original for resizing)
        try:
             self.raw_bg_image = Image.open("assets/bg.jpg")
             # Blur radius reduced to 2 as requested
             self.raw_bg_image = self.raw_bg_image.filter(ImageFilter.GaussianBlur(radius=2))
        except Exception as e:
             print(f"BG Load Error: {e}")
             self.raw_bg_image = Image.new("RGB", (1920, 1080), "#2b2b2b")

        self.bg_photo = None
        self.bg_item = self.canvas.create_image(0, 0, anchor="nw")
        
        # Create Widgets (we don't pack/grid them, we use create_window later)
        
        # Profile
        self.profile_var = ctk.StringVar(value=ProfileManager.get_current_profile_data()["name"])
        self.profile_combo = ctk.CTkComboBox(self, variable=self.profile_var, values=[p["name"] for p in ProfileManager.profiles], command=self.on_profile_change, width=200)
        
        # Version
        self.version_combo = ctk.CTkComboBox(self, values=["Loading..."], width=200, command=self.on_version_change)
        
        # Loader
        self.loader_type = ctk.StringVar(value="None")
        self.loader_combo = ctk.CTkComboBox(self, variable=self.loader_type, values=["None", "Forge", "Fabric", "Quilt", "NeoForge", "OptiFine"], width=150)
        
        # Play
        self.play_button = ctk.CTkButton(self, text="PLAY", width=200, height=50, font=ctk.CTkFont(size=20, weight="bold"), command=self.launch_game)
        
        # Progress Bar
        self.progress_bar = ctk.CTkProgressBar(self, width=400)
        self.progress_bar.set(0)
        
        # Canvas Items (Text)
        self.text_ids = {}
        
        # Start fetch
        self.mojang_versions = [] # Cache
        threading.Thread(target=self.load_versions, daemon=True).start()
        
        # Bind Resize
        self.canvas.bind('<Configure>', self.on_resize)
        
        # Bind Visibility (Refresh instances when returning to Home)
        self.bind('<Map>', self.on_show)

    def on_show(self, event):
        # Refresh the list to catch new instances
        # We don't need to re-fetch Mojang versions every time, just instances
        self.refresh_version_list()

    def on_resize(self, event):
        w, h = event.width, event.height
        if w < 100 or h < 100: return # Ignore small inits
        
        # Resize Image
        try:
            # Resize image to cover (basic scaling for now)
            # Use resize NOT thumbnail to fill
            resized = self.raw_bg_image.resize((w, h), Image.Resampling.LANCZOS)
            self.bg_photo = ImageTk.PhotoImage(resized)
            self.canvas.itemconfig(self.bg_item, image=self.bg_photo)
        except Exception as e:
            print(f"Resize Error: {e}")

        # Clear old windows/text to redraw (or just move them? moving is better but recreation is easier for clean layout)
        # Actually proper way is coords update.
        
        # Center X
        cx = w / 2
        cy = h / 2
        
        # Layout Config
        title_y = cy - 150
        row1_y = cy - 50 # Profile
        row2_y = cy # Version/Loader
        btn_y = cy + 80
        status_y = cy + 130
        prog_y = cy + 160
        
        # Helper to create/move text
        def update_text(tag, x, y, text, font=("Arial", 20, "bold"), fill="white", anchor="center"):
            if tag not in self.text_ids:
                self.text_ids[tag] = self.canvas.create_text(x, y, text=text, font=font, fill=fill, anchor=anchor)
            else:
                self.canvas.coords(self.text_ids[tag], x, y)
                self.canvas.itemconfig(self.text_ids[tag], text=text, font=font, fill=fill)
        
        # Helper to create/move window
        def update_window(tag, widget, x, y, anchor="center"):
            if tag not in self.text_ids: # reusing text_ids dict for window ids logic for simplicity
                self.text_ids[tag] = self.canvas.create_window(x, y, window=widget, anchor=anchor)
            else:
                self.canvas.coords(self.text_ids[tag], x, y)

        # Draw UI
        
        # Title
        update_text("title", cx, title_y, "IEB-MC-Launcher", font=("Arial", 40, "bold"))
        
        # Profile Row
        update_text("lbl_profile", cx - 120, row1_y, "Profile:", font=("Arial", 14), anchor="e")
        update_window("win_profile", self.profile_combo, cx - 110, row1_y, anchor="w")
        
        # Version/Loader Row
        # Layout: Refresh | Version Label | Version Combo | Loader Label | Loader Combo
        # Revised for better spacing:
        # Btn(30) | Gap(15) | Lbl(75) | Gap(10) | Cmb(200) | Gap(80!) | Lbl(70) | Gap(10) | Cmb(150)
        # Total: 640
        start_x = cx - 320
        
        # Refresh Button
        self.btn_refresh = ctk.CTkButton(self, text="↻", width=30, height=28, 
                                         font=("Arial", 16, "bold"), fg_color="#333", hover_color="#555",
                                         command=lambda: threading.Thread(target=self.load_versions, daemon=True).start())
        update_window("win_refresh", self.btn_refresh, start_x, row2_y, anchor="w")
        
        update_text("lbl_ver", start_x + 45, row2_y, "Version:", font=("Arial", 14), anchor="w")
        update_window("win_ver", self.version_combo, start_x + 130, row2_y, anchor="w")
        
        # Increased gap to +410 (was 370)
        update_text("lbl_loader", start_x + 410, row2_y, "Loader:", font=("Arial", 14), anchor="w")
        update_window("win_loader", self.loader_combo, start_x + 480, row2_y, anchor="w")
        
        # Play Button
        update_window("win_play", self.play_button, cx, btn_y)
        
        if not hasattr(self, "prog_win_id"):
             self.prog_win_id = self.canvas.create_window(cx, prog_y, window=self.progress_bar, state="hidden")
        else:
             self.canvas.coords(self.prog_win_id, cx, prog_y)

    def update_status(self, text):
        # Update Canvas Text
        cx = self.winfo_width() / 2
        cy = self.winfo_height() / 2
        # Fixed offset from center calculation in on_resize
        status_y = cy + 130
        
        if "status" not in self.text_ids:
             self.text_ids["status"] = self.canvas.create_text(cx, status_y, text=text, font=("Arial", 12), fill="white")
        else:
             self.canvas.itemconfig(self.text_ids["status"], text=text)
             # Update coords in case resize happened
             self.canvas.coords(self.text_ids["status"], cx, status_y)

    def load_versions(self):
        try:
             self.update_status("Loading versions...")
             
             # Fetch Mojang Versions (Slow)
             versions = self.launcher.get_available_versions()
             show_snapshots = Config.get("show_snapshots", False)
             
             self.mojang_versions = []
             for v in versions:
                 if v["type"] == "release":
                     self.mojang_versions.append(v["id"])
                 elif show_snapshots and v["type"] == "snapshot":
                     self.mojang_versions.append(v["id"])
             
             self.refresh_version_list()
             self.update_status("Ready")
        except Exception as e:
             self.update_status(f"Error loading versions: {e}")
             import traceback
             traceback.print_exc()

    def refresh_version_list(self):
        try:
             # Load Instances (Fast)
             self.instances = InstanceManager.load_instances()
             instance_names = [f"[Instance] {name}" for name in self.instances.keys()]
             
             # Combine
             final_list = instance_names + self.mojang_versions
             
             current = self.version_combo.get()
             self.version_combo.configure(values=final_list)
             
             # If current selection still valid, keep it. Else select first.
             if current in final_list:
                 self.version_combo.set(current)
             elif final_list:
                 self.version_combo.set(final_list[0])
                 self.on_version_change(final_list[0])
                 
        except Exception as e:
             print(f"Refresh Error: {e}")

    def on_profile_change(self, choice):
        pass
        
    def on_version_change(self, choice):
        # If instance selected, lock loader combo
        if choice.startswith("[Instance] "):
            real_name = choice.replace("[Instance] ", "")
            inst = self.instances.get(real_name)
            if inst:
                self.loader_type.set(inst["loader"])
                self.loader_combo.configure(state="disabled")
        else:
            self.loader_combo.configure(state="normal")
            if self.loader_type.get() in ["Forge", "Fabric", "Quilt"] and choice not in ["None"]:
                 pass # keep selection
            else:
                 self.loader_type.set("None") # Default reset

    def launch_game(self):
        version_selection = self.version_combo.get()
        profile = ProfileManager.get_current_profile_data()
        
        if not version_selection or version_selection == "Loading...":
            return

        self.play_button.configure(state="disabled", text="Launching...")
        # Show progress
        self.canvas.itemconfigure(self.prog_win_id, state="normal")
        self.progress_bar.set(0)
        
        threading.Thread(target=self._launch_thread, args=(version_selection, profile)).start()

    def _launch_thread(self, version_selection, profile):
        try:
            self.update_status("Preparing...")
            
            callbacks = {
                "setStatus": lambda t: self.update_status(t),
                "setProgress": lambda v: self.progress_bar.set(v/100) if v else None,
                "setMax": lambda m: None
            }
            
            # Check if Instance or Standard
            if version_selection.startswith("[Instance] "):
                real_name = version_selection.replace("[Instance] ", "")
                inst = self.instances.get(real_name)
                
                if not inst: raise Exception("Instance data not found")
                
                version = inst["version"]
                loader = inst["loader"]
                game_dir = inst["path"] # Use isolated game dir
            else:
                loader = self.loader_type.get()
                version = version_selection
                game_dir = None # Default
                
            launch_ver_id = self.launcher.install_and_get_version(version, loader, callbacks, game_dir=game_dir)
            
            self.update_status("Launching Game...")
            rpc_client.update_presence("In Game", f"Playing {version} ({loader})")
            
            self.launcher.launch_game(launch_ver_id, profile["name"], profile.get("type", "offline"), game_dir=game_dir)
            
            self.update_status("Game Launched!")
            rpc_client.update_presence("In Launcher", "Idle")
        except Exception as e:
             self.update_status(f"Error: {e}")
             import traceback
             traceback.print_exc()
        finally:
            self.play_button.configure(state="normal", text="PLAY")
            self.canvas.itemconfigure(self.prog_win_id, state="hidden")
