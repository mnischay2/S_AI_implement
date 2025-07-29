import socket
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
import csv
import os
from os.path import exists
from PIL import Image, ImageTk

# === CSV Setup ===
os.makedirs("csv_data", exist_ok=True)
csv_filename = os.path.join("csv_data", "packet_strength.csv")
if not exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "PC Date", "PC Time",
            "in_temp", "in_pressure", "in_humidity",
            "out_temp", "out_pressure", "out_humidity",
            "Logging Duration (hh:mm:ss)"
        ])

# === GUI Setup ===
root = tk.Tk()
root.title("Smart Sensor Workstation")
root.attributes("-fullscreen", True)

def toggle_fullscreen(event=None):
    root.attributes("-fullscreen", not root.attributes("-fullscreen"))

root.bind("<F11>", toggle_fullscreen)
root.bind("<Escape>", lambda e: root.attributes("-fullscreen", False))
root.configure(bg="#1e1e1e")

# === Fonts and Styles ===
font = ("Segoe UI", 11)

style = ttk.Style(root)
style.theme_use("clam")
style.configure("TLabel", background="#1e1e1e", foreground="#f0f0f0", font=font)
style.configure("TButton", font=font, padding=6)
style.configure("TEntry", font=font)

# === Header Section ===
top_frame = tk.Frame(root, bg="#1e1e1e")
top_frame.grid(row=0, column=0, columnspan=4, sticky="ew", pady=10)

try:
    #bodhi cube logo
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "assets", "bodhi_icon.png")
    icon_img = Image.open(icon_path).resize((80, 80), Image.Resampling.LANCZOS)
    icon_photo = ImageTk.PhotoImage(icon_img)
    tk.Label(top_frame, image=icon_photo, bg="#1e1e1e").pack(side="left", padx=10)
    #bodh scientifc logo
    logo_path = os.path.join(script_dir, "assets", "bodh.png")
    logo_img = Image.open(logo_path).resize((120, 80), Image.Resampling.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_img)
    tk.Label(top_frame, image=logo_photo, bg="#1e1e1e").pack(side="right", padx=10)
except Exception as e:
    print(f"[WARNING] Couldn't load icon: {e}")

tk.Label(top_frame, text="Smart Sensor Workstation", font=("Segoe UI", 16, "bold"), fg="#ffffff", bg="#1e1e1e").pack(side="left", expand=True)

# === Fields Layout ===
labels = [
    "PC Date", "PC Time",
    "Temperature (°C)", "Pressure (hPa)", "Humidity (%)"
]

entries = {
    "IN": {},
    "OUT": {},
    "DURATION": {}
}

# Row 1: PC Date and Time
for i, label in enumerate(["PC Date", "PC Time"]):
    ttk.Label(root, text=label + ":").grid(row=1, column=i * 2, padx=10, pady=6, sticky='e')
    entry = ttk.Entry(root, width=20, state='readonly', justify='center')
    entry.grid(row=1, column=i * 2 + 1, padx=10)
    entries[label] = entry

# Row 2: Duration and Logging Status
ttk.Label(root, text="Logging Duration:").grid(row=2, column=0, padx=10, pady=6, sticky='e')
duration_entry = ttk.Entry(root, width=20, state='readonly', justify='center')
duration_entry.grid(row=2, column=1, padx=10)
entries["DURATION"]["formatted"] = duration_entry

ttk.Label(root, text="Logging Status:").grid(row=2, column=2, padx=10, pady=6, sticky='e')
status_entry = ttk.Entry(root, width=20, state='readonly', justify='center')
status_entry.grid(row=2, column=3, padx=10)
entries["DURATION"]["status"] = status_entry

# Row 3: Sensor Labels
ttk.Label(root, text="IN Sensor", foreground="#00ff88", font=("Segoe UI", 11, "bold")).grid(row=3, column=1)
ttk.Label(root, text="OUT Sensor", foreground="#ffcc00", font=("Segoe UI", 11, "bold")).grid(row=3, column=3)

# Rows 4-6: Sensor Readings
for i, field_label in enumerate(labels[2:]):
    ttk.Label(root, text=field_label + ":").grid(row=i + 4, column=0, padx=10, pady=6, sticky='e')
    for j, sensor in enumerate(["IN", "OUT"]):
        entry = ttk.Entry(root, width=20, state='readonly', justify='center')
        entry.grid(row=i + 4, column=j * 2 + 1, padx=10)
        entries[sensor][field_label] = entry

# === Logging State and Buffer ===
logging_active = tk.BooleanVar(value=False)
row_buffer = {}
logging_start_time = None

def update_logging_duration():
    if logging_active.get() and logging_start_time:
        elapsed = datetime.now() - logging_start_time
        formatted = str(elapsed).split('.')[0]  # hh:mm:ss
        duration_entry.config(state='normal')
        duration_entry.delete(0, tk.END)
        duration_entry.insert(0, formatted)
        duration_entry.config(state='readonly')
        status_entry.config(state='normal')
        status_entry.delete(0, tk.END)
        status_entry.insert(0, "Logging")
        status_entry.config(state='readonly')
    else:
        status_entry.config(state='normal')
        status_entry.delete(0, tk.END)
        status_entry.insert(0, "Not Logging")
        status_entry.config(state='readonly')

    root.after(1000, update_logging_duration)

def update_fields(source, data):
    global logging_start_time
    try:
        temp, pressure, humidity = data.strip().split(",")
        now = datetime.now()
        pc_date = now.strftime("%Y-%m-%d")
        pc_time = now.strftime("%H:%M:%S")
        timestamp = pc_date + " " + pc_time

        if logging_active.get():
            duration = str((now - logging_start_time)).split('.')[0]

            if timestamp not in row_buffer:
                row_buffer[timestamp] = {
                    "PC Date": pc_date,
                    "PC Time": pc_time,
                    "Duration": duration
                }

            prefix = "in" if source == "IN" else "out"
            row_buffer[timestamp][f"{prefix}_temp"] = temp
            row_buffer[timestamp][f"{prefix}_pressure"] = pressure
            row_buffer[timestamp][f"{prefix}_humidity"] = humidity

            entries["PC Date"].config(state='normal')
            entries["PC Date"].delete(0, tk.END)
            entries["PC Date"].insert(0, pc_date)
            entries["PC Date"].config(state='readonly')

            entries["PC Time"].config(state='normal')
            entries["PC Time"].delete(0, tk.END)
            entries["PC Time"].insert(0, pc_time)
            entries["PC Time"].config(state='readonly')

            for label_text, value in zip(
                ["Temperature (°C)", "Pressure (hPa)", "Humidity (%)"],
                [temp, pressure, humidity]
            ):
                e = entries[source][label_text]
                e.config(state='normal')
                e.delete(0, tk.END)
                e.insert(0, value)
                e.config(state='readonly')

            data_row = row_buffer[timestamp]
            required_keys = [
                "in_temp", "in_pressure", "in_humidity",
                "out_temp", "out_pressure", "out_humidity"
            ]
            if all(k in data_row for k in required_keys):
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        data_row["PC Date"], data_row["PC Time"],
                        data_row["in_temp"], data_row["in_pressure"], data_row["in_humidity"],
                        data_row["out_temp"], data_row["out_pressure"], data_row["out_humidity"],
                        data_row["Duration"]
                    ])
                del row_buffer[timestamp]

    except Exception as e:
        print(f"[ERROR] {source} update failed: {e}")

# === Socket Servers ===
def socket_server(port, source):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen(5)
    print(f"[{source}] Listening on port {port}")
    while True:
        client, addr = server.accept()
        data = client.recv(1024).decode().strip()
        if data:
            root.after(0, update_fields, source, data)
        client.close()

# === Logging Button Setup ===
resample_mode = Image.Resampling.LANCZOS
try:
    start_img = Image.open(os.path.join("assets", "start.png")).resize((100, 100), resample=resample_mode)
    stop_img = Image.open(os.path.join("assets", "stop.png")).resize((100, 100), resample=resample_mode)
    start_photo = ImageTk.PhotoImage(start_img)
    stop_photo = ImageTk.PhotoImage(stop_img)
except Exception as e:
    print(f"[ERROR] Could not load start/stop icons: {e}")
    start_photo = stop_photo = None

def toggle_logging(event=None):
    global logging_start_time
    current = logging_active.get()
    logging_active.set(not current)
    if not current:
        logging_start_time = datetime.now()
        logging_icon_label.config(image=stop_photo)
    else:
        logging_start_time = None
        logging_icon_label.config(image=start_photo)
        duration_entry.config(state='normal')
        duration_entry.delete(0, tk.END)
        duration_entry.config(state='readonly')

logging_icon_label = tk.Label(root, image=start_photo, bg="#1e1e1e", cursor="hand2")
logging_icon_label.grid(row=7, column=0, padx=10, pady=15)
logging_icon_label.bind("<Button-1>", toggle_logging)

# === Start Threads and GUI Loop ===
threading.Thread(target=socket_server, args=(5000, "IN"), daemon=True).start()
threading.Thread(target=socket_server, args=(5001, "OUT"), daemon=True).start()
update_logging_duration()

root.mainloop()
