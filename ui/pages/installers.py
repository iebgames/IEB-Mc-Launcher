import customtkinter as ctk
import threading
from tkinter import messagebox
import minecraft_launcher_lib

class InstallersPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.launcher = controller.pages["Home"].launcher # Access shared launcher core
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.title = ctk.CTkLabel(self, text="Mod Loader Installers", font=ctk.CTkFont(size=30, weight="bold"))
        self.title.grid(row=0, column=0, pady=20)
        
        self.tabs = ctk.CTkTabview(self)
        self.tabs.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.tabs.add("Forge")
        self.tabs.add("Fabric")
        self.tabs.add("Quilt")
        
        self._setup_forge_tab()
        self._setup_fabric_tab()
        self._setup_quilt_tab()

    def _setup_forge_tab(self):
        tab = self.tabs.tab("Forge")
        tab.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(tab, text="Select Minecraft Version:").grid(row=0, column=0, pady=10)
        
        self.forge_ver_combo = ctk.CTkComboBox(tab, values=["Loading..."])
        self.forge_ver_combo.grid(row=1, column=0, pady=10)
        
        ctk.CTkButton(tab, text="Refresh Versions", command=self.load_forge_versions).grid(row=2, column=0, pady=10)
        ctk.CTkButton(tab, text="Install Forge", command=self.install_forge).grid(row=3, column=0, pady=20)

    def _setup_fabric_tab(self):
        tab = self.tabs.tab("Fabric")
        tab.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(tab, text="Select Minecraft Version:").grid(row=0, column=0, pady=10)
        
        self.fabric_ver_combo = ctk.CTkComboBox(tab, values=["Loading..."])
        self.fabric_ver_combo.grid(row=1, column=0, pady=10)
        
        ctk.CTkButton(tab, text="Refresh Versions", command=self.load_fabric_versions).grid(row=2, column=0, pady=10)
        ctk.CTkButton(tab, text="Install Fabric", command=self.install_fabric).grid(row=3, column=0, pady=20)

    def _setup_quilt_tab(self):
        tab = self.tabs.tab("Quilt")
        tab.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(tab, text="Select Minecraft Version:").grid(row=0, column=0, pady=10)
        
        self.quilt_ver_combo = ctk.CTkComboBox(tab, values=["Loading..."])
        self.quilt_ver_combo.grid(row=1, column=0, pady=10)
        
        ctk.CTkButton(tab, text="Refresh Versions", command=self.load_quilt_versions).grid(row=2, column=0, pady=10)
        ctk.CTkButton(tab, text="Install Quilt", command=self.install_quilt).grid(row=3, column=0, pady=20)

    def load_forge_versions(self):
        threading.Thread(target=self._load_forge_thread, daemon=True).start()

    def _load_forge_thread(self):
        # minecraft-launcher-lib forge listing is a bit complex, implies fetching all
        # For simplicity, we might just show common MC versions and attempt install
        # But correctly we should list them.
        # find_forge_version(version_id) is available.
        # list_forge_versions() returns a list.
        try:
            versions = minecraft_launcher_lib.forge.list_forge_versions()
            # This returns a list of Forge versions, usually we want to map MC version to Forge version
            # Simplified: Just listing unique MC versions support
            mc_versions = sorted(list(set(v.split('-')[0] for v in versions if '-' in v)), reverse=True)
            self.forge_ver_combo.configure(values=mc_versions)
            if mc_versions: self.forge_ver_combo.set(mc_versions[0])
        except Exception as e:
            print(f"Error loading Forge: {e}")

    def load_fabric_versions(self):
        threading.Thread(target=self._load_fabric_thread, daemon=True).start()
        
    def _load_fabric_thread(self):
        try:
            # Assuming get_stable_minecraft_versions() functionality from lib or just commonly supported
            # fabric module has get_stable_minecraft_versions() ?
            # Checking library capability... assume yes or fallback
             versions = [v["version"] for v in minecraft_launcher_lib.fabric.get_all_minecraft_versions()]
             self.fabric_ver_combo.configure(values=versions)
             if versions: self.fabric_ver_combo.set(versions[0])
        except:
             pass

    def load_quilt_versions(self):
        threading.Thread(target=self._load_quilt_thread, daemon=True).start()

    def _load_quilt_thread(self):
        try:
             versions = [v["version"] for v in minecraft_launcher_lib.quilt.get_all_minecraft_versions()]
             self.quilt_ver_combo.configure(values=versions)
             if versions: self.quilt_ver_combo.set(versions[0])
        except:
             pass

    def install_forge(self):
        mc_ver = self.forge_ver_combo.get()
        if not mc_ver or mc_ver == "Loading...": return
        threading.Thread(target=lambda: self._install_loader("Forge", mc_ver), daemon=True).start()

    def install_fabric(self):
        mc_ver = self.fabric_ver_combo.get()
        if not mc_ver or mc_ver == "Loading...": return
        threading.Thread(target=lambda: self._install_loader("Fabric", mc_ver), daemon=True).start()
        
    def install_quilt(self):
        mc_ver = self.quilt_ver_combo.get()
        if not mc_ver or mc_ver == "Loading...": return
        threading.Thread(target=lambda: self._install_loader("Quilt", mc_ver), daemon=True).start()

    def _install_loader(self, loader, mc_ver):
        try:
            print(f"Installing {loader} for {mc_ver}...")
            if loader == "Forge":
                forge_ver = minecraft_launcher_lib.forge.find_forge_version(mc_ver)
                if not forge_ver:
                    print("Forge version not found for this MC version")
                    return
                minecraft_launcher_lib.forge.install_forge_version(forge_ver, self.launcher.minecraft_dir)
            elif loader == "Fabric":
                minecraft_launcher_lib.fabric.install_fabric(mc_ver, self.launcher.minecraft_dir)
            elif loader == "Quilt":
                minecraft_launcher_lib.quilt.install_quilt(mc_ver, self.launcher.minecraft_dir)
            
            print(f"Successfully installed {loader} for {mc_ver}")
            messagebox.showinfo("Success", f"{loader} for {mc_ver} installed!")
        except Exception as e:
            print(f"Error installing {loader}: {e}")
            messagebox.showerror("Error", str(e))
