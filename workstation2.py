import socket
import threading
import tkinter as tk
from tkinter import ttk
from datetime import datetime

# CSV logging setup
import csv
from os.path import exists

# Create CSV file and header if it doesn't exist
csv_filename = "weather_log.csv"
if not exists(csv_filename):
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Temperature (°C)", "Pressure (hPa)", "Humidity (%)"])

# GUI Setup
root = tk.Tk()
root.title("Weather Station Monitor")
root.geometry("350x200")
root.resizable(False, False)

# Font style
font = ("Segoe UI", 12)

# Labels and Entries
fields = ["Timestamp", "Temperature (°C)", "Pressure (hPa)", "Humidity (%)"]
entries = {}

for i, field in enumerate(fields):
    tk.Label(root, text=field + ":", font=font).grid(row=i, column=0, padx=10, pady=5, sticky='e')
    entry = ttk.Entry(root, font=font, width=20, state='readonly', justify='center')
    entry.grid(row=i, column=1, padx=10, pady=5)
    entries[field] = entry

# Function to update GUI fields
def update_fields(data):
    try:
        timestamp, temp, pressure, humidity = data.strip().split(",")
        entries["Timestamp"].config(state='normal')
        entries["Temperature (°C)"].config(state='normal')
        entries["Pressure (hPa)"].config(state='normal')
        entries["Humidity (%)"].config(state='normal')

        entries["Timestamp"].delete(0, tk.END)
        entries["Temperature (°C)"].delete(0, tk.END)
        entries["Pressure (hPa)"].delete(0, tk.END)
        entries["Humidity (%)"].delete(0, tk.END)

        entries["Timestamp"].insert(0, timestamp)
        entries["Temperature (°C)"].insert(0, temp)
        entries["Pressure (hPa)"].insert(0, pressure)
        entries["Humidity (%)"].insert(0, humidity)

        entries["Timestamp"].config(state='readonly')
        entries["Temperature (°C)"].config(state='readonly')
        entries["Pressure (hPa)"].config(state='readonly')
        entries["Humidity (%)"].config(state='readonly')

        # Log to CSV
        with open(csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, temp, pressure, humidity])

    except Exception as e:
        print(f"Error updating fields: {e}")

# Socket Server Thread
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
            print(f"[DATA] {data}")
            root.after(0, update_fields, data)
        client.close()

# Run socket server in a background thread
threading.Thread(target=socket_server, daemon=True).start()

# Start the Tkinter event loop
root.mainloop()
