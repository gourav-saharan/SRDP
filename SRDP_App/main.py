import os
import sys

os.environ.setdefault("MPLBACKEND", "TkAgg")


def configure_tcl_tk_runtime():
    if getattr(sys, "frozen", False):
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        tcl_candidates = [
            os.path.join(base_dir, "_tcl_data"),
            os.path.join(base_dir, "tcl", "tcl8.6"),
        ]
        tk_candidates = [
            os.path.join(base_dir, "_tk_data"),
            os.path.join(base_dir, "tcl", "tk8.6"),
        ]
    else:
        base_dir = sys.base_prefix
        tcl_candidates = [os.path.join(base_dir, "tcl", "tcl8.6")]
        tk_candidates = [os.path.join(base_dir, "tcl", "tk8.6")]

    for tcl_library in tcl_candidates:
        if os.path.exists(os.path.join(tcl_library, "init.tcl")):
            os.environ.setdefault("TCL_LIBRARY", tcl_library)
            break

    for tk_library in tk_candidates:
        if os.path.exists(os.path.join(tk_library, "tk.tcl")):
            os.environ.setdefault("TK_LIBRARY", tk_library)
            break


configure_tcl_tk_runtime()

import tkinter as tk

def show_splash():
    # Simple text splash for instant feedback
    splash = tk.Tk()
    splash.title("SRDP")
    w, h = 300, 150
    sw = splash.winfo_screenwidth()
    sh = splash.winfo_screenheight()
    splash.geometry(f"{w}x{h}+{int((sw-w)/2)}+{int((sh-h)/2)}")
    splash.overrideredirect(True) 
    splash.configure(bg="#0A192F")
    
    lbl = tk.Label(splash, text="SRDP", font=("Arial", 40, "bold"), fg="white", bg="#0A192F")
    lbl.pack(expand=True)
    ctk_lbl = tk.Label(splash, text="Loading Professional Workspaces...", font=("Arial", 10), fg="#cbd5e1", bg="#0A192F")
    ctk_lbl.pack(pady=(0, 20))
    splash.update()
    return splash

if __name__ == "__main__":
    splash = show_splash()
    
    
    import customtkinter as ctk
    from ui.app_window import AppWindow

    # The splash screen is a temporary Tk root. Destroy it before creating the
    # real CustomTkinter root so later widgets/fonts have a valid default root.
    splash.destroy()
    app = AppWindow()
    app.mainloop()
