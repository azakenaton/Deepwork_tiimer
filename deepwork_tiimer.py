import tkinter as tk
from tkinter import messagebox
import time
import csv
from datetime import datetime

LOG_FILE = "deepwork_log.csv"

class DeepWorkTimer:
    def __init__(self, root):
        self.root = root
        self.root.title("Deep Work Timer")
        self.root.geometry("400x250")

        # Variables
        self.work_minutes = tk.IntVar(value=25)
        self.break_minutes = tk.IntVar(value=5)
        self.remaining_time = 0
        self.is_running = False
        self.is_work_phase = True

        # UI
        tk.Label(root, text="Temps de travail (min):").pack()
        tk.Entry(root, textvariable=self.work_minutes).pack()

        tk.Label(root, text="Temps de repos (min):").pack()
        tk.Entry(root, textvariable=self.break_minutes).pack()

        self.timer_label = tk.Label(root, text="00:00", font=("Helvetica", 32))
        self.timer_label.pack(pady=20)

        self.start_button = tk.Button(root, text="Démarrer", command=self.start_timer)
        self.start_button.pack()

        self.stop_button = tk.Button(root, text="Stop", command=self.stop_timer)
        self.stop_button.pack()

    def start_timer(self):
        if not self.is_running:
            self.is_running = True
            minutes = self.work_minutes.get() if self.is_work_phase else self.break_minutes.get()
            self.remaining_time = minutes * 60
            self.update_timer()

    def stop_timer(self):
        self.is_running = False
        self.timer_label.config(text="00:00")

    def update_timer(self):
        if self.is_running and self.remaining_time > 0:
            mins, secs = divmod(self.remaining_time, 60)
            self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
            self.remaining_time -= 1
            self.root.after(1000, self.update_timer)
        elif self.is_running:
            # Sauvegarde
            self.log_session()
            # Basculer travail/repos
            self.is_work_phase = not self.is_work_phase
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

if __name__ == "__main__":
    root = tk.Tk()
    app = DeepWorkTimer(root)
    root.mainloop()
