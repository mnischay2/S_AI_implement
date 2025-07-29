import socket
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
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
            "Logging Duration (s)"
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

# === Icon Setup ===
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    icon_path = os.path.join(script_dir, "assets", "bodhi_icon.png")
    icon_img = Image.open(icon_path)
    icon_photo = ImageTk.PhotoImage(icon_img)
    root.iconphoto(False, icon_photo)
except Exception as e:
    print(f"[WARNING] Couldn't load icon: {e}")

font = ("Segoe UI", 11)

style = ttk.Style(root)
style.theme_use("clam")
style.configure("TLabel", background="#1e1e1e", foreground="#f0f0f0", font=font)
style.configure("TButton", font=font, padding=6)
style.configure("TEntry", font=font)

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

# Row 0: PC Date and Time
for i, label in enumerate(["PC Date", "PC Time"]):
    ttk.Label(root, text=label + ":").grid(row=0, column=i * 2, padx=10, pady=8, sticky='e')
    entry = ttk.Entry(root, width=20, state='readonly', justify='center')
    entry.grid(row=0, column=i * 2 + 1, padx=10)
    entries[label] = entry

# Headers
ttk.Label(root, text="IN Sensor", foreground="#00ff88", font=("Segoe UI", 11, "bold")).grid(row=1, column=1)
ttk.Label(root, text="OUT Sensor", foreground="#ffcc00", font=("Segoe UI", 11, "bold")).grid(row=1, column=3)

# Rows 2-4: Sensor Readings
for i, field_label in enumerate(labels[2:]):
    ttk.Label(root, text=field_label + ":").grid(row=i + 2, column=0, padx=10, pady=6, sticky='e')
    for j, sensor in enumerate(["IN", "OUT"]):
        entry = ttk.Entry(root, width=20, state='readonly', justify='center')
        entry.grid(row=i + 2, column=j * 2 + 1, padx=10)
        entries[sensor][field_label] = entry

# Row 5 Column 1: Logging Duration and logging status
ttk.Label(root, text="Logging Duration (s):").grid(row=5, column=0, padx=10, pady=6, sticky='e')
duration_entry = ttk.Entry(root, width=20, state='readonly', justify='center')
duration_entry.grid(row=5, column=1, padx=10)
entries["DURATION"]["seconds"] = duration_entry
# Row 5 Column 2: logging status
ttk.Label(root, text="Logging Status:").grid(row=5, column=2, padx=10, pady=6, sticky='e')
logging_status = ttk.Entry(root, width=20, state='readonly', justify='center')
logging_status.grid(row=5, column=3, padx=10)
entries["DURATION"]["seconds"] = logging_status


# === Logging Control ===
logging_active = tk.BooleanVar(value=False)
row_buffer = {}
logging_start_time = None

def update_logging_duration():
    if logging_active.get() and logging_start_time:
        duration = int((datetime.now() - logging_start_time).total_seconds())
        duration_entry.config(state='normal')
        duration_entry.delete(0, tk.END)
        duration_entry.insert(0, str(duration))
        duration_entry.config(state='readonly')
        logging_status.config(state='normal')
        logging_status.delete(0, tk.END)
        logging_status.insert(0, "Logging...")
        logging_status.config(state='readonly')
    else:
        logging_status.config(state='normal')
        logging_status.delete(0, tk.END)
        logging_status.insert(0, "Not Logging")
        logging_status.config(state='readonly')
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
            duration = int((now - logging_start_time).total_seconds())

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

            # Update time fields
            entries["PC Date"].config(state='normal')
            entries["PC Date"].delete(0, tk.END)
            entries["PC Date"].insert(0, pc_date)
            entries["PC Date"].config(state='readonly')

            entries["PC Time"].config(state='normal')
            entries["PC Time"].delete(0, tk.END)
            entries["PC Time"].insert(0, pc_time)
            entries["PC Time"].config(state='readonly')

            # Update sensor entries
            for label_text, value in zip(
                ["Temperature (°C)", "Pressure (hPa)", "Humidity (%)"],
                [temp, pressure, humidity]
            ):
                e = entries[source][label_text]
                e.config(state='normal')
                e.delete(0, tk.END)
                e.insert(0, value)
                e.config(state='readonly')

            # Save if both in and out data are available
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

# === Toggle Logging Button ===
def toggle_logging():
    global logging_start_time
    current = logging_active.get()
    logging_active.set(not current)
    if not current:
        logging_start_time = datetime.now()
        toggle_button.config(text="Stop Logging")
    else:
        logging_start_time = None
        toggle_button.config(text="Start Logging")
        duration_entry.config(state='normal')
        duration_entry.delete(0, tk.END)
        duration_entry.config(state='readonly')

toggle_button = ttk.Button(root, text="Start Logging", command=toggle_logging)
toggle_button.grid(row=6, column=0, padx=10, pady=15)


# === Start Servers and Duration Clock ===
threading.Thread(target=socket_server, args=(5000, "IN"), daemon=True).start()
threading.Thread(target=socket_server, args=(5001, "OUT"), daemon=True).start()
update_logging_duration()

root.mainloop()
