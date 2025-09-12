import customtkinter as ctk
import tkinter as tk  # Utilisation du menu classique
from tkinter import messagebox, filedialog, colorchooser
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
        config = {"work_minutes": 25, "break_minutes": 5, "colors": DEFAULT_COLORS, "theme": "dark", "mini_alpha": 1.0}
    if "colors" not in config:
        config["colors"] = DEFAULT_COLORS.copy()
    if "theme" not in config:
        config["theme"] = "dark"
    if "mini_alpha" not in config:
        config["mini_alpha"] = 1.0
    return config

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

class DeepWorkTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Deep Work Timer")

        # Charger config
        self.config = load_config()

        # Appliquer le thème clair/sombre
        ctk.set_appearance_mode(self.config["theme"])

        # Variables
        self.work_minutes = ctk.IntVar(value=self.config["work_minutes"])
        self.break_minutes = ctk.IntVar(value=self.config["break_minutes"])
        self.remaining_time = 0
        self.total_time = 0
        self.is_running = False
        self.is_work_phase = True

        # Mini-widget
        self.mini_widget = None

        # Interface principale
        self.main_frame = ctk.CTkFrame(root, corner_radius=20)
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.label_title = ctk.CTkLabel(self.main_frame, text="Deep Work Timer", font=("Helvetica", 20, "bold"))
        self.label_title.pack(pady=10)

        self.entry_work = ctk.CTkEntry(self.main_frame, textvariable=self.work_minutes, placeholder_text="Temps de travail (min)")
        self.entry_work.pack(pady=5, fill="x", padx=20)

        self.entry_break = ctk.CTkEntry(self.main_frame, textvariable=self.break_minutes, placeholder_text="Temps de repos (min)")
        self.entry_break.pack(pady=5, fill="x", padx=20)

        # Canvas principal
        self.timer_canvas = tk.Canvas(self.main_frame, bg="white", highlightthickness=0)
        self.timer_canvas.pack(pady=20, expand=True, fill="both")
        self.timer_canvas.bind("<Configure>", self.resize_canvas)

        self.start_button = ctk.CTkButton(self.main_frame, text="Démarrer", command=self.start_timer)
        self.start_button.pack(pady=5, fill="x", padx=20)

        self.stop_button = ctk.CTkButton(self.main_frame, text="Stop", command=self.stop_timer)
        self.stop_button.pack(pady=5, fill="x", padx=20)

        self.stats_button = ctk.CTkButton(self.main_frame, text="Statistiques", command=self.show_stats)
        self.stats_button.pack(pady=5, fill="x", padx=20)

        self.fullscreen_button = ctk.CTkButton(self.main_frame, text="Plein écran", command=self.toggle_fullscreen)
        self.fullscreen_button.pack(pady=5, fill="x", padx=20)

        self.mini_button = ctk.CTkButton(self.main_frame, text="Mini-widget", command=self.open_mini_widget)
        self.mini_button.pack(pady=5, fill="x", padx=20)

        # Menu classique Tkinter
        self.menu = tk.Menu(root)
        root.config(menu=self.menu)

        file_menu = tk.Menu(self.menu, tearoff=0)
        file_menu.add_command(label="Quitter", command=self.root.quit)
        self.menu.add_cascade(label="Fichier", menu=file_menu)

        options_menu = tk.Menu(self.menu, tearoff=0)
        options_menu.add_command(label="Personnaliser couleurs", command=self.customize_colors)
        options_menu.add_command(label="Thème clair", command=lambda: self.change_theme("light"))
        options_menu.add_command(label="Thème sombre", command=lambda: self.change_theme("dark"))
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

        # Raccourcis clavier
        self.root.bind("<F11>", lambda e: self.toggle_fullscreen())
        self.root.bind("<Control-t>", lambda e: self.toggle_theme())

    def apply_theme(self):
        colors = self.config["colors"]
        if self.is_work_phase:
            bg_color = colors.get("work_bg", DEFAULT_COLORS["work_bg"])
            btn_color = colors.get("work_btn", DEFAULT_COLORS["work_btn"])
        else:
            bg_color = colors.get("break_bg", DEFAULT_COLORS["break_bg"])
            btn_color = "#444444"

        self.main_frame.configure(fg_color=bg_color)
        for b in [self.start_button, self.stop_button, self.stats_button, self.fullscreen_button, self.mini_button]:
            b.configure(fg_color=btn_color, text_color=colors.get("btn_text", "#ffffff"))

        self.timer_canvas.configure(bg=bg_color)

    def change_theme(self, mode):
        ctk.set_appearance_mode(mode)
        self.config["theme"] = mode
        save_config(self.config)
        self.apply_theme()
        # Mise à jour instantanée du mini-widget
        if self.mini_widget:
            if self.total_time > 0:
                percent = self.remaining_time / self.total_time
                mins, secs = divmod(self.remaining_time, 60)
                self.draw_mini_circle(percent, f"{mins:02d}:{secs:02d}")
            else:
                self.draw_mini_circle(0, "00:00")

    def toggle_theme(self):
        new_mode = "light" if self.config["theme"] == "dark" else "dark"
        self.change_theme(new_mode)

    def set_mini_alpha(self, value):
        self.config["mini_alpha"] = value
        save_config(self.config)
        if self.mini_widget:
            self.mini_widget.attributes("-alpha", value)

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            minutes = self.work_minutes.get() if self.is_work_phase else self.break_minutes.get()
            self.remaining_time = minutes * 60
            self.total_time = self.remaining_time
            self.config["work_minutes"] = self.work_minutes.get()
            self.config["break_minutes"] = self.break_minutes.get()
            save_config(self.config)
            self.update_timer()

    def stop_timer(self):
        self.is_running = False
        self.draw_circle(0)
        if self.mini_widget:
            self.draw_mini_circle(0)

    def update_timer(self):
        if self.is_running and self.remaining_time > 0:
            mins, secs = divmod(self.remaining_time, 60)
            percent = self.remaining_time / self.total_time
            self.draw_circle(percent, f"{mins:02d}:{secs:02d}")
            if self.mini_widget:
                self.draw_mini_circle(percent, f"{mins:02d}:{secs:02d}")
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

    def draw_circle(self, percent, time_str="00:00"):
        self.timer_canvas.delete("all")
        w = self.timer_canvas.winfo_width()
        h = self.timer_canvas.winfo_height()
        size = min(w, h) - 20
        x0, y0, x1, y1 = (w - size) / 2, (h - size) / 2, (w + size) / 2, (h + size) / 2

        self.timer_canvas.create_oval(x0, y0, x1, y1, outline="#cccccc", width=size*0.08)
        extent = percent * 360
        self.timer_canvas.create_arc(x0, y0, x1, y1, start=90, extent=-extent, outline="#ffffff", width=size*0.08, style="arc")
        font_size = max(12, size // 6)
        self.timer_canvas.create_text(w/2, h/2, text=time_str, font=("Helvetica", font_size, "bold"), fill="white")

    def resize_canvas(self, event):
        if self.total_time > 0:
            percent = self.remaining_time / self.total_time
        else:
            percent = 0
        mins, secs = divmod(self.remaining_time, 60)
        self.draw_circle(percent, f"{mins:02d}:{secs:02d}")

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
                if self.mini_widget:
                    self.draw_mini_circle(0, "00:00")

        win = ctk.CTkToplevel(self.root)
        win.title("Personnaliser les couleurs & transparence")

        ctk.CTkButton(win, text="Fond Travail", command=lambda: pick_color("work_bg")).pack(pady=5)
        ctk.CTkButton(win, text="Boutons Travail", command=lambda: pick_color("work_btn")).pack(pady=5)
        ctk.CTkButton(win, text="Fond Repos", command=lambda: pick_color("break_bg")).pack(pady=5)

        # Slider de transparence
        ctk.CTkLabel(win, text="Transparence mini-widget").pack(pady=5)
        alpha_slider = ctk.CTkSlider(win, from_=0.4, to=1.0, number_of_steps=6)
        alpha_slider.set(self.config.get("mini_alpha", 1.0))
        alpha_slider.pack(pady=5, fill="x", padx=20)

        def update_alpha(value):
            self.set_mini_alpha(float(value))

        alpha_slider.configure(command=update_alpha)

    def show_about(self):
        messagebox.showinfo("À propos", "Deep Work Timer\nAvec mini-widget flottant Play/Pause\nDéveloppé en Python")

    def toggle_fullscreen(self):
        self.root.attributes("-fullscreen", not self.root.attributes("-fullscreen"))

    # --------- Mini Widget ---------
    def open_mini_widget(self):
        if self.mini_widget:
            return
        self.mini_widget = ctk.CTkToplevel(self.root)
        self.mini_widget.title("Mini Timer")
        self.mini_widget.geometry("180x180")
        self.mini_widget.resizable(False, False)
        self.mini_widget.attributes("-topmost", True)
        self.mini_widget.attributes("-alpha", self.config.get("mini_alpha", 1.0))

        self.mini_canvas = tk.Canvas(self.mini_widget, bg="black", highlightthickness=0)
        self.mini_canvas.pack(expand=True, fill="both")

        self.mini_button_play = ctk.CTkButton(self.mini_widget, text="▶", width=40, height=40, command=self.toggle_play_pause)
        self.mini_button_play.place(relx=0.5, rely=0.5, anchor="center")

        self.mini_widget.protocol("WM_DELETE_WINDOW", self.close_mini_widget)

    def close_mini_widget(self):
        if self.mini_widget:
            self.mini_widget.destroy()
            self.mini_widget = None

    def draw_mini_circle(self, percent, time_str="00:00"):
        if not self.mini_widget:
            return
        self.mini_canvas.delete("all")
        w = self.mini_canvas.winfo_width()
        h = self.mini_canvas.winfo_height()
        size = min(w, h) - 20
        x0, y0, x1, y1 = (w - size) / 2, (h - size) / 2, (w + size) / 2, (h + size) / 2

        self.mini_canvas.create_oval(x0, y0, x1, y1, outline="#888888", width=8)
        extent = percent * 360
        self.mini_canvas.create_arc(x0, y0, x1, y1, start=90, extent=-extent, outline="#ffffff", width=8, style="arc")

        font_size = max(10, size // 6)
        self.mini_canvas.create_text(w/2, h/2, text=time_str, font=("Helvetica", font_size, "bold"), fill="white")

    def toggle_play_pause(self):
        if self.is_running:
            self.stop_timer()
            if self.mini_button_play:
                self.mini_button_play.configure(text="▶")
        else:
            self.start_timer()
            if self.mini_button_play:
                self.mini_button_play.configure(text="⏸")

if __name__ == "__main__":
    root = ctk.CTk()
    app = DeepWorkTimer(root)
    root.mainloop()