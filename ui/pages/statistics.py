import customtkinter as ctk
from utils.config import Config
import random

class StatisticsPage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        self.title = ctk.CTkLabel(self, text="Statistics", font=ctk.CTkFont(size=30, weight="bold"))
        self.title.grid(row=0, column=0, columnspan=2, pady=20)
        
        # Mock Data
        playtime = Config.get("total_playtime", 0)
        launches = Config.get("total_launches", 0)
        
        self._create_stat_card("Total Playtime", f"{playtime} Hours", 0, 0)
        self._create_stat_card("Total Launches", f"{launches}", 0, 1)
        self._create_stat_card("Last Playing", "2 days ago", 1, 0)
        self._create_stat_card("Favorite Version", "1.8.9", 1, 1)

    def _create_stat_card(self, title, value, row, col):
        card = ctk.CTkFrame(self)
        card.grid(row=row+1, column=col, padx=20, pady=20, sticky="ew")
        
        t_label = ctk.CTkLabel(card, text=title, font=ctk.CTkFont(size=14))
        t_label.pack(pady=(10, 5))
        
        v_label = ctk.CTkLabel(card, text=value, font=ctk.CTkFont(size=24, weight="bold"))
        v_label.pack(pady=(0, 10))
