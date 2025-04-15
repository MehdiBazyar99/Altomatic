"""
main.py

Entry point for Altomatic – a tool to name and describe images using GPT-4.1-nano.
Features:
- Multiple harmonic themes (Light, Dark, BlueGray, Solarized, Pinky)
- Obfuscated API key storage in config
- Separate monitor window for logs
- Drag-and-drop for image/folder input
"""

import tkinter as tk
from tkinter import ttk, messagebox
from tkinterdnd2 import TkinterDnD
from config import load_config, save_config, reset_config
from ui_components import build_ui
from dragdrop import configure_drag_and_drop
from logic import process_images

# A set of harmonic themes for demonstration
HARMONIC_THEMES = {
    "Light": {
        "bg": "#f2f2f2",
        "fg": "#222",
        "notebook_bg": "#f9f9f9",
        "tab_bg": "#dddddd",
        "tab_fg": "#000",
        "button_bg": "#e0e0e0",
        "button_fg": "#000"
    },
    "Dark": {
        "bg": "#2b2b2b",
        "fg": "#cccccc",
        "notebook_bg": "#3b3b3b",
        "tab_bg": "#4b4b4b",
        "tab_fg": "#ccc",
        "button_bg": "#444",
        "button_fg": "#fff"
    },
    "BlueGray": {
        "bg": "#eceff1",
        "fg": "#263238",
        "notebook_bg": "#cfd8dc",
        "tab_bg": "#b0bec5",
        "tab_fg": "#263238",
        "button_bg": "#b0bec5",
        "button_fg": "#263238"
    },
    "Solarized": {
        "bg": "#fdf6e3",
        "fg": "#657b83",
        "notebook_bg": "#eee8d5",
        "tab_bg": "#eee8d5",
        "tab_fg": "#657b83",
        "button_bg": "#eee8d5",
        "button_fg": "#657b83"
    },
    "Pinky": {
        "bg": "#ffe4e1",
        "fg": "#6a3d3c",
        "notebook_bg": "#ffd5d0",
        "tab_bg": "#ffaeb9",
        "tab_fg": "#6a3d3c",
        "button_bg": "#ffaeb9",
        "button_fg": "#6a3d3c"
    }
}

def apply_theme(root: TkinterDnD.Tk, theme_name: str):
    """
    Applies one of the predefined harmonic themes to the entire UI.
    """
    style = ttk.Style(root)
    style.theme_use("clam")
    theme = HARMONIC_THEMES.get(theme_name, HARMONIC_THEMES["Light"])

    # Configure root background
    root.configure(bg=theme["bg"])

    # Configure styles
    style.configure(".", background=theme["bg"], foreground=theme["fg"], fieldbackground=theme["bg"])
    style.configure("TNotebook", background=theme["notebook_bg"])
    style.configure("TNotebook.Tab", background=theme["tab_bg"], foreground=theme["tab_fg"], padding=(12, 8))
    style.configure("TLabel", background=theme["bg"], foreground=theme["fg"], font=('Segoe UI', 10))
    style.configure("TButton", background=theme["button_bg"], foreground=theme["button_fg"], font=('Segoe UI', 10))

def main():
    """
    Main function that loads the config, applies the UI theme,
    builds the UI, configures drag-and-drop, and starts the main loop.
    """
    # 1) Load config
    user_config = load_config()

    # 2) Create the root window (with drag-and-drop)
    root = TkinterDnD.Tk()
    root.title("Altomatic")
    root.geometry(user_config.get('window_geometry', "900x600"))
    root.resizable(True, True)

    # 3) Apply the chosen theme
    current_theme = user_config.get('ui_theme', "Light")
    apply_theme(root, current_theme)

    # 4) Build UI
    state = build_ui(root, user_config)
    state['root'] = root  # for saving geometry, etc.

    # 5) Connect "Describe Images" button to logic.process_images
    state['process_button'].config(command=lambda: process_images(state))

    # 6) Enable drag-and-drop
    configure_drag_and_drop(root, state)

    # 7) A callback to reset config from the UI
    def on_reset_config():
        if messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings?"):
            reset_config()
            messagebox.showinfo("Reset", "Settings reset. Please restart the application.")
            root.destroy()
    state['reset_config_callback'] = on_reset_config

    # 8) On closing, save config
    def on_close():
        geometry = root.winfo_geometry().split('+')[0]  # e.g. '900x600'
        save_config(state, geometry)
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

if __name__ == "__main__":
    main()
