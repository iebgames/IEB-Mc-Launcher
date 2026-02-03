import customtkinter as ctk
import threading
from tkinter import messagebox, filedialog, simpledialog
import os
import requests
from utils.modrinth_api import ModrinthAPI
from utils.config import Config
from utils.file_installer import FileInstaller
from utils.content_manager import ContentManager
from utils.instance_manager import InstanceManager

class ModsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Row 2 is tabview
        
        # --- Instance Management Section ---
        self.active_instance = None # Dict with name, path, version, loader
        
        instance_frame = ctk.CTkFrame(self)
        instance_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(instance_frame, text="Active Version:").pack(side="left", padx=10)
        
        self.instance_combo = ctk.CTkComboBox(instance_frame, width=200, command=self.on_instance_change)
        self.instance_combo.pack(side="left", padx=5)
        
        btn_create = ctk.CTkButton(instance_frame, text="Create Version", width=120, fg_color="#F39C12", hover_color="#D68910", command=self.create_version_dialog)
        btn_create.pack(side="left", padx=10)
        
        btn_refresh = ctk.CTkButton(instance_frame, text="Refresh", width=80, command=self.load_instances)
        btn_refresh.pack(side="right", padx=5)

        btn_delete = ctk.CTkButton(instance_frame, text="🗑", width=40, fg_color="#C0392B", hover_color="#E74C3C", command=self.delete_version)
        btn_delete.pack(side="right", padx=5)

        # --- Warning/Info ---
        self.info_label = ctk.CTkLabel(self, text="Select or Create a Version to manage mods.", text_color="gray")
        self.info_label.grid(row=1, column=0, pady=5)
        
        # --- Tabs ---
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=2, column=0, sticky="nsew", padx=10, pady=5)
        
        self.tabs = {
            "Mods": "mod",
            "Texture Packs": "resourcepack", 
            "Shader Packs": "shader",
            "Modpacks": "modpack"
        }
        
        self.tab_controllers = {} # Store refs to tab functions
        
        for tab_name, type_key in self.tabs.items():
            self.tabview.add(tab_name)
            self._setup_tab(self.tabview.tab(tab_name), type_key)
            
        # Initial Load
        self.load_instances()

    def load_instances(self):
        instances = InstanceManager.load_instances()
        names = list(instances.keys())
        if names:
            self.instance_combo.configure(values=names)
            if not self.active_instance or self.active_instance["name"] not in names:
                self.instance_combo.set(names[0])
                self.on_instance_change(names[0])
        else:
            self.instance_combo.configure(values=["No Versions"])
            self.instance_combo.set("No Versions")
            self.active_instance = None
            self.update_info()

    def on_instance_change(self, name):
         instance = InstanceManager.get_instance(name)
         if instance:
             self.active_instance = instance
             self.update_info()
             # Refresh current tab list
             # Ideally trigger refresh of 'Installed' lists in standard tabs
             
    def update_info(self):
        if self.active_instance:
            v = self.active_instance['version']
            l = self.active_instance['loader']
            self.info_label.configure(text=f"Selected: {self.active_instance['name']} (MC {v} - {l})", text_color="white")
        else:
            self.info_label.configure(text="Please create a version first.", text_color="orange")

    def create_version_dialog(self):
        # Custom Dialog for Version Creation
        dialog = ctk.CTkToplevel(self)
        dialog.title("Create New Version")
        dialog.geometry("400x350")
        
        ctk.CTkLabel(dialog, text="Version Name:").pack(pady=5)
        entry_name = ctk.CTkEntry(dialog)
        entry_name.pack(pady=5)
        
        ctk.CTkLabel(dialog, text="Game Version:").pack(pady=5)
        
        # Dynamic Version Fetching
        ver_values = ["Loading..."]
        combo_ver = ctk.CTkComboBox(dialog, values=ver_values, state="readonly")
        combo_ver.pack(pady=5)
        
        def fetch_versions():
            try:
                # Access LauncherCore through controller or instantiate temp
                # ui/app.py doesn't expose self.launcher publicly clearly, but we can try instantiating a helper
                # or better, check if app has it. 
                # If App doesn't store it, we instantiate one temporarily.
                from launcher_core import LauncherCore
                core = LauncherCore()
                versions = core.get_available_versions() # Returns list of dicts
                
                # Filter Releases
                releases = [v["id"] for v in versions if v["type"] == "release"]
                # Releases usually returned sorted latest first by API, but let's ensure
                combo_ver.configure(values=releases)
                if releases:
                    combo_ver.set(releases[0])
            except Exception as e:
                print(f"Version Fetch Error: {e}")
                combo_ver.configure(values=["Error"])
                
        threading.Thread(target=fetch_versions, daemon=True).start()
        
        ctk.CTkLabel(dialog, text="Mod Loader:").pack(pady=5)
        combo_loader = ctk.CTkComboBox(dialog, values=["Fabric", "Forge", "Quilt", "NeoForge", "None"])
        combo_loader.pack(pady=5)
        
        def save():
            name = entry_name.get()
            ver = combo_ver.get()
            loader = combo_loader.get()
            
            if not name: return
            
            InstanceManager.create_instance(name, ver, loader)
            self.load_instances()
            # Auto select new
            self.instance_combo.set(name)
            self.on_instance_change(name)
            dialog.destroy()
            messagebox.showinfo("Success", f"Version '{name}' created!")

        ctk.CTkButton(dialog, text="Create", command=save).pack(pady=20)

    def delete_version(self):
        if not self.active_instance:
             messagebox.showerror("Error", "No version selected.")
             return
             
        name = self.active_instance["name"]
        
        if messagebox.askyesno("Delete Version", f"Are you sure you want to delete '{name}'?\nThis will remove all installed mods and configs for this version.\nThis cannot be undone."):
            if InstanceManager.delete_instance(name):
                messagebox.showinfo("Deleted", f"Version '{name}' has been deleted.")
                self.load_instances() # Reload list
            else:
                messagebox.showerror("Error", "Failed to delete version.")


    # --- Tab Logic ---
    def _setup_tab(self, parent, type_key):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)
        
        # Top Bar
        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        
        view_var = ctk.StringVar(value="Browse")
        
        def toggle_view(value):
            if value == "Browse":
                browse_frame.grid(row=1, column=0, sticky="nsew")
                installed_frame.grid_forget()
            else:
                browse_frame.grid_forget()
                installed_frame.grid(row=1, column=0, sticky="nsew")
                refresh_installed()

        toggle = ctk.CTkSegmentedButton(top_frame, values=["Browse", "Installed"], command=toggle_view, variable=view_var)
        toggle.pack(side="left")
        
        if type_key != "modpack": 
             ctk.CTkButton(top_frame, text="Manual Install", width=100, fg_color="green", 
                           command=lambda: self.manual_install(type_key, refresh_installed)).pack(side="right")
        
        # 1. Browse Area
        browse_frame = ctk.CTkFrame(parent, fg_color="transparent")
        browse_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        browse_frame.grid_columnconfigure(0, weight=1)
        browse_frame.grid_rowconfigure(1, weight=1)
        
        search_f = ctk.CTkFrame(browse_frame, fg_color="transparent")
        search_f.grid(row=0, column=0, sticky="ew", pady=5)
        
        entry = ctk.CTkEntry(search_f, placeholder_text=f"Search {type_key}s...", width=300)
        entry.pack(side="left", padx=5)
        
        results_area = ctk.CTkScrollableFrame(browse_frame, label_text="Results")
        results_area.grid(row=1, column=0, sticky="nsew")
        results_area.grid_columnconfigure(0, weight=1)

        def perform_search():
            query = entry.get()
            if not query: return
            
            # Filters
            v_filter = [self.active_instance['version']] if self.active_instance else None
            l_filter = [self.active_instance['loader']] if self.active_instance and self.active_instance['loader'] != "None" else None
            
            # If Modpack tab, we might not want to filter by loader strictly? 
            # Or if modpack, creating it makes a NEW instance, so search should probably be generic?
            # User said: "modpaketlerinde iste indirdiğimiz zaman mod paketinin ismi neyse öyle bir versiyon oluştursun"
            # So for Modpacks, do NOT filter by current instance versions
            if type_key == "modpack":
                v_filter = None
                l_filter = None
            
            for w in results_area.winfo_children(): w.destroy()
            btn_search.configure(state="disabled", text="...")
            
            def search_thread():
                results = ModrinthAPI.search_mods(query, project_type=type_key, versions=v_filter, loaders=l_filter)
                self.after(0, lambda: display_results(results))
                
            threading.Thread(target=search_thread, daemon=True).start()
            
        def display_results(results):
            btn_search.configure(state="normal", text="Search")
            if not results:
                ctk.CTkLabel(results_area, text="No results found matching current version.").pack(pady=20)
                return
            for res in results:
                self._create_card(results_area, res, type_key)

        btn_search = ctk.CTkButton(search_f, text="Search", command=perform_search, width=80)
        btn_search.pack(side="left", padx=5)
        
        # 2. Installed Area
        installed_frame = ctk.CTkFrame(parent, fg_color="transparent")
        installed_frame.grid_columnconfigure(0, weight=1)
        installed_frame.grid_rowconfigure(0, weight=1)
        
        installed_scroll = ctk.CTkScrollableFrame(installed_frame, label_text="Installed Files")
        installed_scroll.grid(row=0, column=0, sticky="nsew")
        installed_scroll.grid_columnconfigure(0, weight=1)
        
        def refresh_installed():
            if not self.active_instance and type_key != "modpack":
                 for w in installed_scroll.winfo_children(): w.destroy()
                 ctk.CTkLabel(installed_scroll, text="Select a version first.").pack(pady=20)
                 return
                 
            for w in installed_scroll.winfo_children(): w.destroy()
            
            # If modpack, checking "installed modpacks" is harder (it's instances)
            if type_key == "modpack":
                # List instances maybe?
                return

            path = self.active_instance['path']
            files = ContentManager.list_content(type_key, instance_path=path)
            
            if not files:
                ctk.CTkLabel(installed_scroll, text="No installed files found.").pack(pady=20)
                return
                
            for f in files:
                row = ctk.CTkFrame(installed_scroll, fg_color="transparent")
                row.pack(fill="x", pady=2, padx=5)
                ctk.CTkLabel(row, text="📄", width=30).pack(side="left")
                ctk.CTkLabel(row, text=f, font=("Arial", 12, "bold")).pack(side="left", padx=5)
                ctk.CTkButton(row, text="🗑", width=40, fg_color="#C0392B", command=lambda fn=f, r=row: delete_file(fn, r)).pack(side="right")
                
        def delete_file(filename, row_widget):
            if messagebox.askyesno("Delete", f"Delete {filename}?"):
                if ContentManager.delete_content(type_key, filename, self.active_instance['path']):
                    row_widget.destroy()

    def _create_card(self, parent, mod, type_key):
        card = ctk.CTkFrame(parent)
        card.pack(fill="x", pady=5, padx=5)
        
        info = ctk.CTkFrame(card, fg_color="transparent")
        info.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        
        ctk.CTkLabel(info, text=mod["title"], font=("Arial", 14, "bold"), anchor="w").pack(fill="x")
        ctk.CTkLabel(info, text=mod.get("description", "")[:80]+"...", text_color="gray", anchor="w", font=("Arial", 12)).pack(fill="x")

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.pack(side="right", padx=10)
        
        if type_key == "modpack":
             ctk.CTkButton(actions, text="Install Pack", width=100, command=lambda: self.install_modpack(mod)).pack()
        else:
             ctk.CTkButton(actions, text="Download", width=100, command=lambda: self.install_item(mod, type_key)).pack()
             
        # Bind Click for Details
        def on_click(event):
            self.show_details(mod, type_key)
            
        card.bind("<Button-1>", on_click)
        info.bind("<Button-1>", on_click)
        # Bind labels too
        for child in info.winfo_children():
            child.bind("<Button-1>", on_click)

    def show_details(self, mod_search_data, type_key):
        # Create Toplevel
        top = ctk.CTkToplevel(self)
        top.title(mod_search_data["title"])
        top.geometry("600x500")
        
        # Grid layout
        top.grid_columnconfigure(0, weight=1)
        top.grid_rowconfigure(1, weight=1)
        
        # Header
        header = ctk.CTkFrame(top)
        header.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        # Icon (if we had it), Title, Author
        ctk.CTkLabel(header, text=mod_search_data["title"], font=("Arial", 20, "bold")).pack(anchor="w", padx=10)
        ctk.CTkLabel(header, text=f"Author: {mod_search_data.get('author', 'Unknown')}", text_color="gray").pack(anchor="w", padx=10)
        
        # Download Button in header
        if type_key == "modpack":
             ctk.CTkButton(header, text="Install Pack", width=120, command=lambda: self.install_modpack(mod_search_data)).pack(anchor="e", padx=10, pady=5)
        else:
             ctk.CTkButton(header, text="Download", width=120, command=lambda: self.install_item(mod_search_data, type_key)).pack(anchor="e", padx=10, pady=5)

        # Content (Description)
        content = ctk.CTkScrollableFrame(top, label_text="Description")
        content.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        
        lbl_loading = ctk.CTkLabel(content, text="Loading details...")
        lbl_loading.pack(pady=20)
        
        # Fetch full details in thread
        def fetch_details():
            project_id = mod_search_data["project_id"] # Search hits have project_id or slug? Modrinth search hits use 'project_id' usually slug.
            # search hit has 'project_id' usually.
            # let's verify key
            pid = mod_search_data.get("project_id") or mod_search_data.get("slug")
            
            details = ModrinthAPI.get_project(pid)
            if details:
                self.after(0, lambda: display_details(details))
            else:
                self.after(0, lambda: lbl_loading.configure(text="Failed to load details."))
                
        def display_details(details):
            if not lbl_loading.winfo_exists(): return
            lbl_loading.destroy()
            
            # Body text (Markdown ideally, but we'll strip or show raw for now)
            body = details.get("body", "No description available.")
            
            # Simple Text widget
            desc_Box = ctk.CTkTextbox(content, width=500, height=300)
            desc_Box.pack(fill="both", expand=True)
            desc_Box.insert("0.0", body)
            desc_Box.configure(state="disabled") # Readonly
            
            # Additional Info
            meta_frame = ctk.CTkFrame(content)
            meta_frame.pack(fill="x", pady=10)
            
            ctk.CTkLabel(meta_frame, text=f"Downloads: {details.get('downloads', 0)}").pack(side="left", padx=10)
            ctk.CTkLabel(meta_frame, text=f"Updated: {details.get('updated', '')[:10]}").pack(side="left", padx=10)

        threading.Thread(target=fetch_details, daemon=True).start()

    def manual_install(self, type_key, callback):
        # NOT implemented fully for instances in FileInstaller yet, need updating FileInstaller passed path
        # Simple shim:
        if not self.active_instance:
             messagebox.showerror("Error", "Select a version first.")
             return
             
        # We need to open dialog but target specific dir.
        # FileInstaller needs update to support arguments. 
        # For now reusing logic but we need to ensure it copies to right place.
        # Implementation left as 'TODO' update FileInstaller.
        # But we can use ContentManager.
        
        messagebox.showinfo("Manual Install", "Manual install for specific instances coming in next update. \n(Use global import for now or drag drop manually)")

    def install_item(self, mod_data, type_key):
        if not self.active_instance:
            messagebox.showerror("Error", "Please create/select a version first.")
            return
            
        print(f"Downloading {mod_data['title']} to {self.active_instance['path']}")
        # Logic: Get file URL -> Download to get_dir(type, instance['path'])
        
        def download():
            # Mock
            import time
            time.sleep(1)
            # Create a fake file
            target = ContentManager.get_dir(type_key, self.active_instance['path'])
            with open(os.path.join(target, f"{mod_data['slug']}.jar"), 'w') as f:
                f.write("mock content")
            messagebox.showinfo("Done", f"Downloaded {mod_data['title']}")
            
        threading.Thread(target=download).start()

    def install_modpack(self, mod_data):
        # Create new instance from modpack
        name = mod_data['title']
        # Ask user for version/loader? Or Modpack metadata usually dictates this.
        # For now simplified:
        
        if messagebox.askyesno("Install Modpack", f"Create new version for '{name}'?"):
            # Mock parsing metdata
            loader = "Fabric" if "fabric" in mod_data['categories'] else "Forge" 
            # We need to find valid game version?
            # Assuming 1.20.1 for demo
            
            new_inst = InstanceManager.create_instance(name, "1.20.1", loader)
            self.load_instances()
            self.instance_combo.set(name)
            self.on_instance_change(name)
            messagebox.showinfo("Success", f"Created version '{name}'.\n(Mod downloading would happen here recursively)")
