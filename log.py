import psutil
import time
import threading
import csv
import json
from collections import defaultdict
from datetime import timedelta, datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# Exclude system apps
EXCLUDE_NAMES = {
    "System Idle Process", "System", "smss.exe", "csrss.exe", "wininit.exe",
    "services.exe", "lsass.exe", "svchost.exe", "explorer.exe", "SearchIndexer.exe",
    "RuntimeBroker.exe", "spoolsv.exe", "winlogon.exe", "dllhost.exe", "taskhostw.exe"
}
EXCLUDE_PATH_KEYWORDS = [
    r"C:\Windows", r"C:\ProgramData", r"C:\$Recycle.Bin"
]

def is_user_app(proc):
    try:
        name = proc.info['name']
        exe = proc.info.get('exe') or ""
        if not name or name in EXCLUDE_NAMES:
            return False
        exe = exe.lower()
        for path_keyword in EXCLUDE_PATH_KEYWORDS:
            if path_keyword.lower() in exe:
                return False
        return True
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False

def format_duration(seconds):
    return str(timedelta(seconds=seconds))

class AppTrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("LogMyApp - Usage Tracker")
        self.root.configure(bg="#f9f9f7")
        self.app_usage = defaultdict(int)
        self.tracking = True
        self.check_interval = 5
        self.start_time = datetime.now()

        style = ttk.Style()
        style.theme_use('default')
        style.configure('Treeview.Heading', font=('Poppins', 10, 'bold'), background='#223A66', foreground='white')
        style.configure('Treeview', font=('Poppins', 9), rowheight=25, background="white", fieldbackground="white")
        
        title = tk.Label(root, text="📊 LogMyApp Dashboard", font=("Poppins", 16, "bold"), fg="#223A66", bg="#f9f9f7")
        title.pack(pady=10)

        # Treeview
        self.tree = ttk.Treeview(root, columns=('App', 'Time'), show='headings')
        self.tree.heading('App', text='Application')
        self.tree.heading('Time', text='Usage Time')
        self.tree.pack(padx=15, pady=5, fill='x')

        # Buttons
        button_frame = tk.Frame(root, bg="#f9f9f7")
        button_frame.pack(pady=10)

        self.stop_button = tk.Button(button_frame, text="⏹ Stop Tracking", command=self.stop_tracking, bg="#223A66", fg="white", font=("Poppins", 10), padx=10, pady=5)
        self.stop_button.grid(row=0, column=0, padx=8)

        self.export_button = tk.Button(button_frame, text="💾 Export to CSV", command=self.export_to_csv, bg="#223A66", fg="white", font=("Poppins", 10), padx=10, pady=5)
        self.export_button.grid(row=0, column=1, padx=8)

        self.view_all_button = tk.Button(button_frame, text="📋 View All Apps", command=self.show_all_apps, bg="#223A66", fg="white", font=("Poppins", 10), padx=10, pady=5)
        self.view_all_button.grid(row=0, column=2, padx=8)

        # Chart placeholder
        self.chart_frame = tk.Frame(root, bg="#f9f9f7")
        self.chart_frame.pack(padx=15, pady=10, fill='both', expand=True)

        # Start tracking
        self.thread = threading.Thread(target=self.track_apps, daemon=True)
        self.thread.start()
        self.update_gui()

    def track_apps(self):
        while self.tracking:
            for proc in psutil.process_iter(['name', 'exe']):
                if is_user_app(proc):
                    app_name = proc.info['name']
                    self.app_usage[app_name] += self.check_interval
            time.sleep(self.check_interval)

    def update_gui(self):
        # Window title
        session_duration = format_duration((datetime.now() - self.start_time).seconds)
        self.root.title(f"LogMyApp - Session Time: {session_duration}")

        # Update tree
        for item in self.tree.get_children():
            self.tree.delete(item)
        top_apps = sorted(self.app_usage.items(), key=lambda x: -x[1])[:5]
        for app, duration in top_apps:
            self.tree.insert('', 'end', values=(app, format_duration(duration)))

        # Update chart
        for widget in self.chart_frame.winfo_children():
            widget.destroy()

        if top_apps:
            fig, ax = plt.subplots(figsize=(4, 3), dpi=100)
            labels = [app for app, _ in top_apps]
            sizes = [sec for _, sec in top_apps]
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90, colors=['#223A66', '#4a5e91', '#6d7cae', '#8f9bcc', '#b1bbe9'])
            ax.axis('equal')

            pie = FigureCanvasTkAgg(fig, master=self.chart_frame)
            pie.draw()
            pie.get_tk_widget().pack()

        if self.tracking:
            self.root.after(1000, self.update_gui)

    def stop_tracking(self):
        self.tracking = False
        self.stop_button.config(state='disabled')

    def export_to_csv(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                 filetypes=[("CSV files", "*.csv")],
                                                 title="Save App Usage Data")
        if not file_path:
            return
        try:
            with open(file_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Application", "Usage Time (HH:MM:SS)"])
                for app, seconds in sorted(self.app_usage.items(), key=lambda x: -x[1]):
                    writer.writerow([app, format_duration(seconds)])
            messagebox.showinfo("Success", f"Data exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export:\n{e}")

    def show_all_apps(self):
        window = tk.Toplevel(self.root)
        window.title("All Tracked Apps")
        window.geometry("400x400")
        tree = ttk.Treeview(window, columns=('App', 'Time'), show='headings')
        tree.heading('App', text='Application')
        tree.heading('Time', text='Usage Time')
        tree.pack(expand=True, fill='both', padx=10, pady=10)
        for app, seconds in sorted(self.app_usage.items(), key=lambda x: -x[1]):
            tree.insert('', 'end', values=(app, format_duration(seconds)))

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = AppTrackerGUI(root)
    root.mainloop()
