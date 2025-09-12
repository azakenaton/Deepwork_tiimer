import customtkinter as ctk
from tkinter import messagebox, filedialog, colorchooser
import tkinter as tk
import time
import csv
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pygame

LOG_FILE = "deepwork_log.csv"
CONFIG_FILE = "config.json"

# Couleurs par défaut
DEFAULT_COLORS = {
    "work_bg": "#924040",   # Rouge
    "work_btn": "#556027",  # Vert
    "break_bg": "#3713af",  # Bleu
    "btn_text": "#ffffff"
}

# Charger ou créer config
def load_config():
    try:
        with open(CONFIG_FILE, "r") as f:
            config = json.load(f)
    except FileNotFoundError:
        config = {"work_minutes": 25, "break_minutes": 5, "colors": DEFAULT_COLORS}
    if "colors" not in config:
        config["colors"] = DEFAULT_COLORS.copy()
    return config

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

class DeepWorkTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Deep Work Timer")
        self.root.geometry("500x400")

        # Charger config
        self.config = load_config()

        # Variables
        self.work_minutes = ctk.IntVar(value=self.config["work_minutes"])
        self.break_minutes = ctk.IntVar(value=self.config["break_minutes"])
        self.remaining_time = 0
        self.is_running = False
        self.is_work_phase = True

        # Interface principale
        self.main_frame = ctk.CTkFrame(root, corner_radius=20)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.label_title = ctk.CTkLabel(self.main_frame, text="Deep Work Timer", font=("Helvetica", 20, "bold"))
        self.label_title.pack(pady=10)

        self.entry_work = ctk.CTkEntry(self.main_frame, textvariable=self.work_minutes, placeholder_text="Temps de travail (min)")
        self.entry_work.pack(pady=5)

        self.entry_break = ctk.CTkEntry(self.main_frame, textvariable=self.break_minutes, placeholder_text="Temps de repos (min)")
        self.entry_break.pack(pady=5)

        self.timer_label = ctk.CTkLabel(self.main_frame, text="00:00", font=("Helvetica", 40, "bold"))
        self.timer_label.pack(pady=20)

        self.start_button = ctk.CTkButton(self.main_frame, text="Démarrer", command=self.start_timer)
        self.start_button.pack(pady=5)

        self.stop_button = ctk.CTkButton(self.main_frame, text="Stop", command=self.stop_timer)
        self.stop_button.pack(pady=5)

        self.stats_button = ctk.CTkButton(self.main_frame, text="Statistiques", command=self.show_stats)
        self.stats_button.pack(pady=5)

        self.fullscreen_button = ctk.CTkButton(self.main_frame, text="Plein écran", command=self.toggle_fullscreen)
        self.fullscreen_button.pack(pady=5)

        # Menu
        self.menu = tk.Menu(root)
        root.config(menu=self.menu)

        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Quitter", command=self.root.quit)
        self.menu.add_cascade(label="Fichier", menu=file_menu)

        options_menu = tk.Menu(self.menu, tearoff=0)
        options_menu.add_command(label="Personnaliser couleurs", command=self.customize_colors)
        self.menu.add_cascade(label="Options", menu=options_menu)

        help_menu = tk.Menu(self.menu, tearoff=0)
        help_menu.add_command(label="À propos", command=self.show_about)
        self.menu.add_cascade(label="Aide", menu=help_menu)

        # Sons
        pygame.mixer.init()
        self.work_end_sound = "break_end.wav"  # fin du travail → repos
        self.break_end_sound = "work_end.wav"  # fin du repos → travail

        # Appliquer le thème initial (travail)
        self.apply_theme()

    def apply_theme(self):
        colors = self.config["colors"]
        if self.is_work_phase:
            bg_color = colors.get("work_bg", DEFAULT_COLORS["work_bg"])
            btn_color = colors.get("work_btn", DEFAULT_COLORS["work_btn"])
        else:
            bg_color = colors.get("break_bg", DEFAULT_COLORS["break_bg"])
            btn_color = "#444444"

        self.main_frame.configure(fg_color=bg_color)
        self.start_button.configure(fg_color=btn_color, text_color=colors.get("btn_text", "#ffffff"))
        self.stop_button.configure(fg_color=btn_color, text_color=colors.get("btn_text", "#ffffff"))
        self.stats_button.configure(fg_color=btn_color, text_color=colors.get("btn_text", "#ffffff"))
        self.fullscreen_button.configure(fg_color=btn_color, text_color=colors.get("btn_text", "#ffffff"))

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            minutes = self.work_minutes.get() if self.is_work_phase else self.break_minutes.get()
            self.remaining_time = minutes * 60
            self.config["work_minutes"] = self.work_minutes.get()
            self.config["break_minutes"] = self.break_minutes.get()
            save_config(self.config)
            self.update_timer()

    def stop_timer(self):
        self.is_running = False
        self.timer_label.configure(text="00:00")

    def update_timer(self):
        if self.is_running and self.remaining_time > 0:
            mins, secs = divmod(self.remaining_time, 60)
            self.timer_label.configure(text=f"{mins:02d}:{secs:02d}")
            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
        elif self.is_running:
            self.log_session()
            if self.is_work_phase:
                pygame.mixer.Sound(self.work_end_sound).play()
            else:
                pygame.mixer.Sound(self.break_end_sound).play()
            self.is_work_phase = not self.is_work_phase
            self.apply_theme()
            phase = "Travail" if self.is_work_phase else "Repos"
            messagebox.showinfo("Fin de session", f"Session terminée ! Passez en mode {phase}.")
            self.is_running = False
            self.start_timer()

    def log_session(self):
        phase = "Travail" if self.is_work_phase else "Repos"
        duration = self.work_minutes.get() if self.is_work_phase else self.break_minutes.get()
        with open(LOG_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), phase, duration])

    def show_stats(self):
        try:
            with open(LOG_FILE, "r") as f:
                reader = csv.reader(f)
                data = list(reader)
        except FileNotFoundError:
            messagebox.showinfo("Statistiques", "Aucune donnée disponible.")
            return

        if not data:
            messagebox.showinfo("Statistiques", "Aucune donnée disponible.")
            return

        labels = [row[1] for row in data]
        durations = [int(row[2]) for row in data]

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(range(len(durations)), durations, tick_label=labels)
        ax.set_ylabel("Durée (min)")
        ax.set_title("Historique Deep Work")

        stats_win = ctk.CTkToplevel(self.root)
        stats_win.title("Statistiques")
        canvas = FigureCanvasTkAgg(fig, master=stats_win)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        export_button = ctk.CTkButton(stats_win, text="Exporter", command=lambda: self.export_data(data))
        export_button.pack(pady=10)

    def export_data(self, data):
        filetypes = [("CSV files", "*.csv"), ("JSON files", "*.json")]
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=filetypes)
        if not filepath:
            return

        if filepath.endswith(".csv"):
            with open(filepath, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(data)
            messagebox.showinfo("Export réussi", f"Données exportées en CSV : {filepath}")

        elif filepath.endswith(".json"):
            json_data = [{"datetime": row[0], "phase": row[1], "duration": int(row[2])} for row in data]
            with open(filepath, "w") as f:
                json.dump(json_data, f, indent=4)
            messagebox.showinfo("Export réussi", f"Données exportées en JSON : {filepath}")

    def customize_colors(self):
        def pick_color(key):
            color = colorchooser.askcolor(title=f"Choisir couleur pour {key}")[1]
            if color:
                self.config["colors"][key] = color
                save_config(self.config)
                self.apply_theme()

        win = ctk.CTkToplevel(self.root)
        win.title("Personnaliser les couleurs")

        ctk.CTkButton(win, text="Fond Travail", command=lambda: pick_color("work_bg")).pack(pady=5)
        ctk.CTkButton(win, text="Boutons Travail", command=lambda: pick_color("work_btn")).pack(pady=5)
        ctk.CTkButton(win, text="Fond Repos", command=lambda: pick_color("break_bg")).pack(pady=5)

    def show_about(self):
        messagebox.showinfo("À propos", "Deep Work Timer\nVersion améliorée avec CustomTkinter\nDéveloppé en Python")

    def toggle_fullscreen(self):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    root = ctk.CTk()
    app = DeepWorkTimer(root)
    root.mainloop()