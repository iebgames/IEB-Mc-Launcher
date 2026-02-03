import customtkinter as ctk

class ConsolePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.title = ctk.CTkLabel(self, text="Debug Console / Logs", font=ctk.CTkFont(size=20, weight="bold"))
        self.title.grid(row=0, column=0, pady=10)
        
        self.log_area = ctk.CTkTextbox(self, width=800, height=500, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_area.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        
        self.log("Launcher initialized.")
        self.log("Ready to launch Minecraft.")

    def log(self, message):
        self.log_area.insert("end", f"> {message}\n")
        self.log_area.see("end")
