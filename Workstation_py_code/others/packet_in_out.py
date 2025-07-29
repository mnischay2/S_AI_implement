import socket
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import csv
from os.path import exists

# === CSV Setup ===
csv_filename = "packet_strength.csv"
if not exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([
            "PC Date", "PC Time",
            "in_temp", "in_pressure", "in_humidity",
            "out_temp", "out_pressure", "out_humidity"
        ])

# === GUI Setup ===
root = tk.Tk()
root.title("Smart Sensor Workstation")
root.geometry("640x360")
root.configure(bg="#1e1e1e")
root.resizable(False, False)
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
    "OUT": {}
}

# Row 0: PC Date and Time
for i, label in enumerate(["PC Date", "PC Time"]):
    ttk.Label(root, text=label + ":").grid(row=0, column=i * 2, padx=10, pady=8, sticky='e')
    entry = ttk.Entry(root, width=20, state='readonly', justify='center')
    entry.grid(row=0, column=i * 2 + 1, padx=10)
    entries[label] = entry  # shared entries

# Labels for IN and OUT headers
ttk.Label(root, text="IN Sensor", foreground="#00ff88", font=("Segoe UI", 11, "bold")).grid(row=1, column=1)
ttk.Label(root, text="OUT Sensor", foreground="#ffcc00", font=("Segoe UI", 11, "bold")).grid(row=1, column=3)

# Rows 2-4: Sensor Readings
for i, label in enumerate(labels[2:]):
    ttk.Label(root, text=label + ":").grid(row=i + 2, column=0, padx=10, pady=6, sticky='e')

    for j, sensor in enumerate(["IN", "OUT"]):
        entry = ttk.Entry(root, width=20, state='readonly', justify='center')
        entry.grid(row=i + 2, column=j * 2 + 1, padx=10)
        entries[sensor][label] = entry

# === Logging Control ===
logging_active = tk.BooleanVar(value=False)
row_buffer = {}

def update_fields(source, data):
    try:
        temp, pressure, humidity = data.strip().split(",")
        now = datetime.now()
        pc_date = now.strftime("%Y-%m-%d")
        pc_time = now.strftime("%H:%M:%S")
        timestamp = pc_date + " " + pc_time

        if logging_active.get():
            if timestamp not in row_buffer:
                row_buffer[timestamp] = {
                    "PC Date": pc_date,
                    "PC Time": pc_time
                }

            prefix = "in" if source == "IN" else "out"
            row_buffer[timestamp][f"{prefix}_temp"] = temp
            row_buffer[timestamp][f"{prefix}_pressure"] = pressure
            row_buffer[timestamp][f"{prefix}_humidity"] = humidity

            # Show common date & time
            entries["PC Date"].config(state='normal')
            entries["PC Date"].delete(0, tk.END)
            entries["PC Date"].insert(0, pc_date)
            entries["PC Date"].config(state='readonly')

            entries["PC Time"].config(state='normal')
            entries["PC Time"].delete(0, tk.END)
            entries["PC Time"].insert(0, pc_time)
            entries["PC Time"].config(state='readonly')

            # Show respective sensor values
            sensor_fields = entries[source]
            for label_text, value in zip(
                ["Temperature (°C)", "Pressure (hPa)", "Humidity (%)"],
                [temp, pressure, humidity]
            ):
                sensor_fields[label_text].config(state='normal')
                sensor_fields[label_text].delete(0, tk.END)
                sensor_fields[label_text].insert(0, value)
                sensor_fields[label_text].config(state='readonly')

            # Save to CSV only when both IN & OUT are available
            data_row = row_buffer[timestamp]
            if all(k in data_row for k in [
                "in_temp", "in_pressure", "in_humidity",
                "out_temp", "out_pressure", "out_humidity"
            ]):
                with open(csv_filename, mode='a', newline='') as file:
                    writer = csv.writer(file)
                    writer.writerow([
                        data_row["PC Date"], data_row["PC Time"],
                        data_row["in_temp"], data_row["in_pressure"], data_row["in_humidity"],
                        data_row["out_temp"], data_row["out_pressure"], data_row["out_humidity"]
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
            print(f"[{source}] Data: {data}")
            root.after(0, update_fields, source, data)
        client.close()

# === Toggle Logging Button ===
def toggle_logging():
    current = logging_active.get()
    logging_active.set(not current)
    status_label.config(text="🟢 Logging ON" if not current else "🔴 Logging OFF")
    toggle_button.config(text="Stop Logging" if not current else "Start Logging")

toggle_button = ttk.Button(root, text="Start Logging", command=toggle_logging)
toggle_button.grid(row=6, column=0, padx=10, pady=15)

status_label = ttk.Label(root, text="🔴 Logging OFF", font=("Segoe UI", 10, "bold"))
status_label.grid(row=6, column=1, columnspan=2, sticky='w')

# === Start Server Threads ===
threading.Thread(target=socket_server, args=(5000, "IN"), daemon=True).start()
threading.Thread(target=socket_server, args=(5001, "OUT"), daemon=True).start()

# Start GUI
root.mainloop()
