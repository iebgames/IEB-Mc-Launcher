import customtkinter as ctk
from tkinter import messagebox
from utils.config import Config
from utils.file_installer import FileInstaller

class SettingsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(5, weight=1) # Spacer
        
        self.title = ctk.CTkLabel(self, text="Settings", font=ctk.CTkFont(size=30, weight="bold"))
        self.title.grid(row=0, column=0, pady=20)
        
        # RAM Settings
        self.ram_val = ctk.IntVar(value=Config.get("ram", 2048))
        
        self.ram_label = ctk.CTkLabel(self, text=f"Allocated RAM: {self.ram_val.get()} MB")
        self.ram_label.grid(row=1, column=0, sticky="w", padx=20)
        
        self.ram_slider = ctk.CTkSlider(self, from_=1024, to=16384, number_of_steps=15, variable=self.ram_val, command=self.update_ram_label)
        self.ram_slider.grid(row=2, column=0, sticky="ew", padx=20, pady=10)

        # Advanced Settings
        self.adv_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.adv_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=5)
        
        self.fps_boost_var = ctk.BooleanVar(value=Config.get("fps_boost", False))
        self.fps_boost_check = ctk.CTkCheckBox(self.adv_frame, text="FPS Boost (Optimized JVM Args)", variable=self.fps_boost_var, command=self.save_extras)
        self.fps_boost_check.pack(side="left", padx=(0, 20))
        
        self.snap_var = ctk.BooleanVar(value=Config.get("show_snapshots", False))
        self.snap_check = ctk.CTkCheckBox(self.adv_frame, text="Show Snapshots", variable=self.snap_var, command=self.save_extras)
        self.snap_check.pack(side="left")
        
        # Java Path
        self.java_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.java_frame.grid(row=4, column=0, sticky="ew", padx=20, pady=5)
        
        self.java_label = ctk.CTkLabel(self.java_frame, text="Java Path:")
        self.java_label.pack(side="left", padx=(0, 10))
        
        self.java_entry = ctk.CTkEntry(self.java_frame, width=300)
        self.java_entry.insert(0, Config.get("java_path", "java"))
        self.java_entry.pack(side="left", padx=(0, 10))
        
        self.java_browse = ctk.CTkButton(self.java_frame, text="Browse", width=80, command=self.browse_java)
        self.java_browse.pack(side="left")

        # Theme Settings
        self.theme_label = ctk.CTkLabel(self, text="Theme:")
        self.theme_label.grid(row=5, column=0, sticky="w", padx=20, pady=(20, 5))
        
        self.theme_combo = ctk.CTkComboBox(self, values=["Dark", "Light", "System"], command=self.change_theme)
        self.theme_combo.set(Config.get("theme", "Dark"))
        self.theme_combo.grid(row=6, column=0, sticky="w", padx=20)
        
        # Clean up / Installers
        self.installer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.installer_frame.grid(row=7, column=0, sticky="ew", padx=20, pady=20)
        
        self.install_rp_btn = ctk.CTkButton(self.installer_frame, text="Install Resource Pack", command=self.install_rp)
        self.install_rp_btn.pack(side="left", padx=5)
        
        self.install_sp_btn = ctk.CTkButton(self.installer_frame, text="Install Shader Pack", command=self.install_sp)
        self.install_sp_btn.pack(side="left", padx=5)
        
        # Save Button
        self.save_btn = ctk.CTkButton(self, text="Save Settings", command=self.save_settings)
        self.save_btn.grid(row=6, column=0, pady=30)

    def update_ram_label(self, value):
        self.ram_label.configure(text=f"Allocated RAM: {int(value)} MB")

    def change_theme(self, new_theme):
        ctk.set_appearance_mode(new_theme)
        Config.set("theme", new_theme)

    def install_rp(self):
        count = FileInstaller.install_resource_pack()
        if count:
             messagebox.showinfo("Success", f"Installed {count} resource packs.")

    def install_sp(self):
        count = FileInstaller.install_shader_pack()
        if count:
             messagebox.showinfo("Success", f"Installed {count} shader packs.")

    def browse_java(self):
        filename = ctk.filedialog.askopenfilename(filetypes=[("Executables", "*.exe"), ("All Files", "*.*")])
        if filename:
            self.java_entry.delete(0, "end")
            self.java_entry.insert(0, filename)
            self.save_settings()

    def save_extras(self):
        # Auto-save for checkboxes
        self.save_settings()

    def save_settings(self):
        Config.set("ram", int(self.ram_slider.get()))
        Config.set("theme", self.theme_combo.get())
        Config.set("fps_boost", self.fps_boost_var.get())
        Config.set("show_snapshots", self.snap_var.get())
        Config.set("java_path", self.java_entry.get())
        print("Settings saved")
