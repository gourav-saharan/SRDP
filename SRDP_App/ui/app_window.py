import customtkinter as ctk
from .upload_frame import UploadFrame
from .config_frame import ConfigFrame
from .graph_frame import GraphFrame
from .settings_frame import SettingsFrame
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.data_manager import DataManager
from core.settings_manager import SettingsManager

class AppWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("SRDP")
        self.geometry("1400x800")
        
        self.settings_manager = SettingsManager()
        self.data_manager = DataManager()
        
        ctk.set_appearance_mode("Light") 
        
        # Grid layout: 2 rows (TopBar, Main), 2 cols (Sidebar, MainContent)
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(1, weight=1)
        
        # --- Top Bar (Full Width) ---
        self.top_bar = ctk.CTkFrame(self, height=70, corner_radius=0, fg_color="#0A192F")
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="new")
        self.top_bar.grid_propagate(False)
        
        self.logo_label = ctk.CTkLabel(self.top_bar, text=" SRDP", 
                                       font=ctk.CTkFont(size=26, weight="bold"), text_color="white")
        self.logo_label.pack(side="left", padx=20, pady=15)
        
        # --- Left Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=120, corner_radius=0, fg_color="#f1f5f9")
        self.sidebar_frame.grid(row=1, column=0, sticky="nsew")
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(5, weight=1)
        
        self.nav_buttons = {}
        
        def create_sbar_btn(icon, text, page_name):
            btn_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
            btn_frame.pack(fill="x", padx=10, pady=5)
            
            btn = ctk.CTkButton(btn_frame, text=icon, width=60, height=45,
                                 fg_color="transparent", text_color="#1E293B", hover_color="#cbd5e1",
                                 corner_radius=8, font=ctk.CTkFont(size=24))
            btn.configure(command=lambda: self.show_frame(page_name))
            btn.pack(pady=(5, 0))
            
            lbl = ctk.CTkLabel(btn_frame, text=text, font=ctk.CTkFont(size=11, weight="bold"), text_color="#1E293B")
            lbl.pack(pady=(0, 5))
            
            self.nav_buttons[page_name] = (btn, lbl)
            return btn, lbl
        
        create_sbar_btn("🏠", "Home", "UploadFrame")
        create_sbar_btn("⚙️", "Config", "ConfigFrame")
        create_sbar_btn("📈", "Graph", "GraphFrame")
        create_sbar_btn("🔧", "Settings", "SettingsFrame")
        
        # --- Main View ---
        self.main_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="#F4F7FB")
        self.main_frame.grid(row=1, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        for F in (UploadFrame, ConfigFrame, GraphFrame, SettingsFrame):
            page_name = F.__name__
            frame = F(parent=self.main_frame, controller=self)
            frame.configure(fg_color="transparent")
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
            
        self.show_frame("UploadFrame")
        
    def show_frame(self, page_name):
        for name, item in self.nav_buttons.items():
            btn, lbl = item
            if name == page_name:
                btn.configure(fg_color="#2563EB", text_color="white")
                lbl.configure(text_color="#2563EB")
            else:
                btn.configure(fg_color="transparent", text_color="#1E293B")
                lbl.configure(text_color="#1E293B")
                
        frame = self.frames[page_name]
        if hasattr(frame, "on_show"):
            frame.on_show() 
        frame.tkraise()
