import customtkinter as ctk
from tkinter import simpledialog, messagebox
from utils.profiles import ProfileManager
import uuid

class ProfilesPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.title = ctk.CTkLabel(self, text="Profile Manager", font=ctk.CTkFont(size=30, weight="bold"))
        self.title.grid(row=0, column=0, pady=20)
        
        self.profiles_scroll = ctk.CTkScrollableFrame(self)
        self.profiles_scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=2, column=0, pady=20)
        
        ctk.CTkButton(self.controls_frame, text="Add Offline Profile", command=self.add_offline_profile).pack(side="left", padx=10)
        ctk.CTkButton(self.controls_frame, text="Add Ely.by Profile", command=self.add_elyby_profile).pack(side="left", padx=10)
        ctk.CTkButton(self.controls_frame, text="Refresh", command=self.refresh_profiles).pack(side="left", padx=10)
        
        self.refresh_profiles()

    def refresh_profiles(self):
        for widget in self.profiles_scroll.winfo_children():
            widget.destroy()
            
        current_id = ProfileManager.current_profile
        
        for profile in ProfileManager.profiles:
            self._create_profile_card(profile, profile["id"] == current_id)

    def _create_profile_card(self, profile, is_active):
        card = ctk.CTkFrame(self.profiles_scroll, border_width=2 if is_active else 0, border_color="green" if is_active else None)
        card.pack(fill="x", pady=5)
        
        name_label = ctk.CTkLabel(card, text=f"{profile['name']} ({profile['type']})", font=ctk.CTkFont(size=16, weight="bold" if is_active else "normal"))
        name_label.pack(side="left", padx=20, pady=10)
        
        if not is_active:
             ctk.CTkButton(card, text="Select", width=60, command=lambda p=profile: self.select_profile(p)).pack(side="right", padx=10)
        
        ctk.CTkButton(card, text="Delete", width=60, fg_color="red", hover_color="darkred", command=lambda p=profile: self.delete_profile(p)).pack(side="right", padx=10)

    def add_offline_profile(self):
        name = simpledialog.askstring("New Profile", "Enter username:")
        if name:
            ProfileManager.create_profile(name) # Defaults to offline
            self.refresh_profiles()

    def add_elyby_profile(self):
        """Add Ely.by profile using OAuth authentication"""
        try:
            from utils.ely_authenticator import ElyAuthenticator
            import threading
            
            # Show loading message
            loading_dialog = ctk.CTkToplevel(self)
            loading_dialog.title("Ely.by Login")
            loading_dialog.geometry("400x150")
            loading_dialog.transient(self)
            loading_dialog.grab_set()
            
            ctk.CTkLabel(loading_dialog, text="Opening browser for Ely.by login...", 
                        font=ctk.CTkFont(size=14)).pack(pady=20)
            ctk.CTkLabel(loading_dialog, text="Please login and authorize the launcher.", 
                        font=ctk.CTkFont(size=12)).pack(pady=10)
            
            progress = ctk.CTkProgressBar(loading_dialog, mode="indeterminate")
            progress.pack(pady=20, padx=40, fill="x")
            progress.start()
            
            def auth_thread():
                try:
                    # Perform OAuth authentication
                    auth_data = ElyAuthenticator.authenticate()
                    
                    # Create profile with real data
                    new_profile = {
                        "id": str(uuid.uuid4()),
                        "name": auth_data['username'],
                        "uuid": auth_data['uuid'],
                        "type": "elyby",
                        "access_token": auth_data['access_token'],
                        "refresh_token": auth_data.get('refresh_token')
                    }
                    
                    ProfileManager.profiles.append(new_profile)
                    ProfileManager.current_profile = new_profile["id"]
                    ProfileManager.save()
                    
                    # Close loading dialog and refresh
                    loading_dialog.destroy()
                    self.refresh_profiles()
                    messagebox.showinfo("Success", f"Logged in as {auth_data['username']}!")
                    
                except Exception as e:
                    loading_dialog.destroy()
                    messagebox.showerror("Login Failed", f"Failed to login with Ely.by:\n{str(e)}")
            
            threading.Thread(target=auth_thread, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to start Ely.by login:\n{str(e)}")

    def select_profile(self, profile):
        ProfileManager.current_profile = profile["id"]
        ProfileManager.save()
        self.refresh_profiles()
        messagebox.showinfo("Selected", f"Switched to {profile['name']}")

    def delete_profile(self, profile):
        if len(ProfileManager.profiles) <= 1:
            messagebox.showerror("Error", "Cannot delete the last profile.")
            return

        if messagebox.askyesno("Delete", f"Delete profile {profile['name']}?"):
             ProfileManager.profiles = [p for p in ProfileManager.profiles if p["id"] != profile["id"]]
             if ProfileManager.current_profile == profile["id"]:
                 ProfileManager.current_profile = ProfileManager.profiles[0]["id"]
             ProfileManager.save()
             self.refresh_profiles()
