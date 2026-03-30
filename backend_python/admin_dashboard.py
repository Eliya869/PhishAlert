import tkinter as tk
from tkinter import scrolledtext
import requests
import threading
import time

class PhishAlertAdmin:
    def __init__(self, root):
        self.root = root
        self.root.title("PhishAlert Admin Panel")
        self.root.geometry("600x400")

        # Header
        self.label = tk.Label(root, text="PhishAlert Server Monitor", font=("Arial", 16, "bold"))
        self.label.pack(pady=10)

        # Status Indicator
        self.status_label = tk.Label(root, text="Status: Checking...", fg="orange", font=("Arial", 12))
        self.status_label.pack()

        # Log Display Area
        self.log_area = scrolledtext.ScrolledText(root, width=70, height=15)
        self.log_area.pack(pady=10)
        self.log_area.insert(tk.INSERT, "System initialized. Monitoring logs...\n")

        # Refresh Button
        self.refresh_btn = tk.Button(root, text="Check Server Status", command=self.check_server)
        self.refresh_btn.pack(pady=5)

        # Start monitoring in a background thread
        self.check_server()

    def check_server(self):
        """ Checks if the Flask API is responding """
        try:
            # We try to hit a simple heartbeat check or just the root
            response = requests.get("http://127.0.0.1:5000/")
            self.status_label.config(text="Status: ONLINE", fg="green")
            self.add_log("Health Check: Server is responding perfectly.")
        except:
            self.status_label.config(text="Status: OFFLINE", fg="red")
            self.add_log("ALERT: Server is not responding! Make sure app.py is running.")

    def add_log(self, message):
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)

if __name__ == "__main__":
    root = tk.Window() if 'Window' in dir(tk) else tk.Tk()
    app = PhishAlertAdmin(root)
    root.mainloop()