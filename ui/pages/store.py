import customtkinter as ctk

class StorePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        self.title = ctk.CTkLabel(self, text="IEB Global Store", font=ctk.CTkFont(size=30, weight="bold"), text_color="#FFD700")
        self.title.grid(row=0, column=0, pady=20)
        
        self.scroll = ctk.CTkScrollableFrame(self)
        self.scroll.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.scroll.grid_columnconfigure((0, 1, 2), weight=1)
        
        items = [
            {"name": "Coin Pack", "price": "$4.99", "color": "#FFA500"},
            {"name": "Premium Cape", "price": "$9.99", "color": "#800080"},
            {"name": "Ultra Rank", "price": "$19.99", "color": "#00FFFF"},
            {"name": "XP Booster", "price": "$2.99", "color": "#00FF00"},
            {"name": "Mystery Box", "price": "$0.99", "color": "#FFC0CB"},
            {"name": "Server Pass", "price": "$14.99", "color": "#4169E1"},
        ]
        
        for i, item in enumerate(items):
            self._create_item_card(i, item)

    def _create_item_card(self, index, item):
        row = index // 3
        col = index % 3
        
        card = ctk.CTkFrame(self.scroll, fg_color="#2B2B2B", border_width=2, border_color=item["color"])
        card.grid(row=row, column=col, padx=10, pady=10, sticky="ew")
        
        name = ctk.CTkLabel(card, text=item["name"], font=ctk.CTkFont(size=16, weight="bold"))
        name.pack(pady=(10, 5))
        
        price = ctk.CTkLabel(card, text=item["price"], font=ctk.CTkFont(size=14))
        price.pack(pady=5)
        
        buy_btn = ctk.CTkButton(card, text="Buy Now", fg_color=item["color"], text_color_disabled="white")
        buy_btn.pack(pady=(5, 10))
