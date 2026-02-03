import os
import sys
import customtkinter as ctk
from ui.app import App
from utils.config import Config

# Set up the environment
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SplashScreen(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.overrideredirect(True)
        
        # Center the splash screen
        width = 400
        height = 300
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
        
        self.frame = ctk.CTkFrame(self, width=width, height=height, corner_radius=10)
        self.frame.pack(fill="both", expand=True)

        try:
             from PIL import Image
             img = ctk.CTkImage(Image.open("assets/logo.png"), size=(100, 100))
             self.label = ctk.CTkLabel(self.frame, image=img, text="")
        except Exception as e:
             print(f"Error loading logo: {e}")
             self.label = ctk.CTkLabel(self.frame, text="IEB Games", font=ctk.CTkFont(size=40, weight="bold"))
             
        self.label.pack(pady=(50, 20))
        
        self.sub_label = ctk.CTkLabel(self.frame, text="Loading Launcher...", font=ctk.CTkFont(size=14))
        self.sub_label.pack(pady=10)

        self.progress = ctk.CTkProgressBar(self.frame, width=300)
        self.progress.pack(pady=20)
        self.progress.set(0)
        
        self.step = 0
        self.after(50, self.animate_progress)

    def animate_progress(self):
        self.step += 0.02
        self.progress.set(self.step)
        if self.step < 1.0:
            self.after(30, self.animate_progress)
        else:
            self.destroy()

def main():
    # Ensure working directory is correct
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Initialize Config
    Config.load()
    
    # Show Splash Screen
    splash = SplashScreen()
    splash.mainloop()
    
    # Launch Main App
    app = App()
    app.mainloop()

if __name__ == "__main__":
    main()
