import socket
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime
import csv
from os.path import exists

# === CSV Setup ===
csv_filename = "in_packet_sensor.csv"
if not exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["PC Date", "PC Time", "Temperature (°C)", "Pressure (hPa)", "Humidity (%)"])

# === GUI Setup ===
root = tk.Tk()
root.title("Weather Station Monitor")
root.geometry("400x300")
root.resizable(False, False)
font = ("Segoe UI", 12)

# Fields: PC Date, PC Time, Sensor Values
fields = ["PC Date", "PC Time", "Temperature (°C)", "Pressure (hPa)", "Humidity (%)"]
entries = {}

for i, field in enumerate(fields):
    tk.Label(root, text=field + ":", font=font).grid(row=i, column=0, padx=10, pady=5, sticky='e')
    entry = ttk.Entry(root, font=font, width=25, state='readonly', justify='center')
    entry.grid(row=i, column=1, padx=10, pady=5)
    entries[field] = entry

# Logging state flag
logging_active = tk.BooleanVar(value=False)

# === Function to Update GUI & Log CSV ===
def update_fields(data):
    try:
        temp, pressure, humidity = data.strip().split(",")

        now = datetime.now()
        pc_date = now.strftime("%Y-%m-%d")
        pc_time = now.strftime("%H:%M:%S")

        values = {
            "PC Date": pc_date,
            "PC Time": pc_time,
            "Temperature (°C)": temp,
            "Pressure (hPa)": pressure,
            "Humidity (%)": humidity
        }

        if logging_active.get():
            # Update GUI fields
            for field in fields:
                entries[field].config(state='normal')
                entries[field].delete(0, tk.END)
                entries[field].insert(0, values[field])
                entries[field].config(state='readonly')

            # Append to CSV
            with open(csv_filename, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([pc_date, pc_time, temp, pressure, humidity])

    except Exception as e:
        print(f"[ERROR] Failed to update fields: {e}")

# === Socket Server Thread ===
def socket_server():
    HOST = "0.0.0.0"
    PORT = 5000

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[SERVER] Listening on port {PORT}...")

    while True:
        client, addr = server.accept()
        data = client.recv(1024).decode().strip()
        if data:
            print(f"[DATA RECEIVED] {data}")
            root.after(0, update_fields, data)
        client.close()

# === Start/Stop Button Functions ===
def toggle_logging():
    current = logging_active.get()
    logging_active.set(not current)
    status_label.config(text="🟢 Logging ON" if not current else "🔴 Logging OFF")
    toggle_button.config(text="Stop Logging" if not current else "Start Logging")

# Start/Stop Button
toggle_button = ttk.Button(root, text="Start Logging", command=toggle_logging)
toggle_button.grid(row=len(fields), column=0, pady=10, padx=10)

# Status Label
status_label = ttk.Label(root, text="🔴 Logging OFF", font=("Segoe UI", 10, "bold"))
status_label.grid(row=len(fields), column=1, pady=10)

# Start server in background thread
threading.Thread(target=socket_server, daemon=True).start()

# Run the GUI event loop
root.mainloop()
