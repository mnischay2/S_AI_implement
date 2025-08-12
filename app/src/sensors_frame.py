# SF_full_rewrite.py
"""
Full rewrite of DynamicSensorFrame with:
- Fullscreen-friendly, centered, monospace key-value layout (one column per port)
- Per-port socket servers (one thread per port)
- Robust data_slice handling
- Port labels mapping (Port_Labels) — supports list-of-lists or single list
- CSV logging that places each port's values into the correct columns (based on Port_Labels or csv_columns)
- Upload button (calls src.upload.upload_csv)
- Status banner (green if ALL ports connected, red otherwise)
- If the overall status is Disconnected, logging cannot start and will be stopped immediately
- Graceful shutdown

Usage: called the same way as the original module:
    import src.sensors_frame as SF
    sensor_frame_instance = SF.display(parent, sensor_config)
    sensor_frame_instance.get_frame().pack(fill=tk.BOTH, expand=True)

"""

import socket
import threading
import tkinter as tk
from tkinter import ttk
import csv
import os
import time
from datetime import datetime, timedelta

# optional PIL imports for images (if you have Pillow installed)
try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except Exception:
    PIL_AVAILABLE = False

# keep upload import compatible with your project layout
try:
    import src.upload as upload
except Exception:
    # graceful fallback if import path differs during testing
    try:
        import upload
    except Exception:
        upload = None


class DynamicSensorFrame:
    def __init__(self, parent, config):
        """parent: root/app (must have .after and optionally .home_screen)
           config: sensor configuration dict (see SENSOR_CONFIG)
        """
        self.parent = parent
        self.config = config
        self.frame = tk.Frame(parent, bg="#000000")
        self.title = config.get("name", config.get("id", "Sensor"))

        # CSV config
        self.csv_dir = config.get("csv_dir", "csv_data")
        os.makedirs(self.csv_dir, exist_ok=True)
        self.csv_filename = config.get("csv_file", f"{config.get('id','sensor')}.csv")
        self.csv_path = os.path.join(self.csv_dir, self.csv_filename)
        # csv_columns if provided (flattened order across ports). We'll fallback to Port_Labels if not provided.
        self.csv_columns = config.get("csv_columns", [])

        # ports / labels / slice
        self.ports = list(config.get("ports", []))
        # flexible keys for labels: "Port_Labels", "port_labels", "Port_Labels"
        self.port_labels = config.get("Port_Labels") or config.get("port_labels") or config.get("Port_Labels") or config.get("Port_Labels")
        # normalize port_labels to list of lists (one sublist per port)
        if self.port_labels is None:
            # try single-port label set from older configs
            single = config.get("Port_Labels") or config.get("Port_1_Labels") or config.get("port_1_Labels") or config.get("Port_1_Labels")
            if single:
                # if single is a list (labels for a single port) and only one port configured, wrap
                if isinstance(single, list) and len(self.ports) == 1:
                    self.port_labels = [single]
                else:
                    # fallback: create blank labels sized to data_slice or csv_columns
                    self.port_labels = [[f"V{j+1}" for j in range( max(1, len(self.csv_columns)) )] for _ in self.ports]
            else:
                self.port_labels = [[f"V{j+1}" for j in range(1)] for _ in self.ports]
        else:
            # If supplied as flat list for a single port, ensure nested
            if isinstance(self.port_labels, list) and len(self.ports) == 1 and self.port_labels and not any(isinstance(x, list) for x in self.port_labels):
                self.port_labels = [self.port_labels]

        # data_slice defines how many values to take per port. Allow: [n] (single int apply to all) or list-of-ints per port
        self.data_slice = config.get("data_slice", [])

        # ensure port_labels length == number of ports
        if len(self.port_labels) != len(self.ports):
            # try to handle cases where user passed one set of labels per port using keys like Port_1_Labels etc.
            tmp = []
            for i in range(len(self.ports)):
                key = f"Port_{i+1}_Labels"
                if key in config:
                    tmp.append(config.get(key, []))
            if tmp and len(tmp) == len(self.ports):
                self.port_labels = tmp
            else:
                # fallback: if single label list and multiple ports, duplicate it
                if len(self.port_labels) == 1 and len(self.ports) > 1:
                    self.port_labels = [self.port_labels[0] for _ in self.ports]
                else:
                    # final fallback: make empty label lists matching expected slice counts
                    self.port_labels = [self.port_labels[i] if i < len(self.port_labels) else [f"V{j+1}" for j in range(1)] for i in range(len(self.ports))]

        # Pre-compute per-port label counts and total columns
        self.per_port_counts = [len(lst) for lst in self.port_labels]
        self.total_columns = sum(self.per_port_counts)
        # if csv_columns not provided or mismatched, create from port_labels
        if not self.csv_columns or len(self.csv_columns) != self.total_columns:
            flattened = []
            for pl in self.port_labels:
                flattened.extend(pl)
            self.csv_columns = flattened

        # state
        self.logging_active = tk.BooleanVar(value=False)
        self.logging_start_time = None
        self.after_ids = []
        self.running = True

        # sockets
        self.server_sockets = []
        self.last_received = {p: None for p in self.ports}
        self.port_to_index = {p: i for i, p in enumerate(self.ports)}

        # UI holders
        self.value_vars = []  # list of list of StringVar per port
        self.key_labels = []
        self.value_labels = []

        # images
        self.start_photo = None
        self.stop_photo = None
        self.upload_photo = None
        self.uploaded_photo = None
        self.upload_f_photo = None

        # setup csv and UI
        self.setup_csv()
        self.create_widgets()

        # start servers and periodic updates
        self.start_socket_servers()
        self.start_periodic_updates()

    # ---------- CSV ----------
    def setup_csv(self):
        if not os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["PC_DATE", "PC_TIME"] + self.csv_columns + ["Duration"])
            except Exception as e:
                print(f"[WARNING] Could not create CSV {self.csv_path}: {e}")

    # ---------- Images ----------
    def load_images(self):
        if not PIL_AVAILABLE:
            return False
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            candidates = [
                os.path.join(script_dir, "..", "assets"),
                os.path.join(script_dir, "assets"),
                os.path.join(os.getcwd(), "assets"),
            ]
            assets_dir = None
            for c in candidates:
                if os.path.isdir(c):
                    assets_dir = c
                    break
            if not assets_dir:
                return False

            resample_mode = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS

            def load(name, size):
                p = os.path.join(assets_dir, name)
                return ImageTk.PhotoImage(Image.open(p).resize(size, resample_mode))

            try:
                self.start_photo = load("start.png", (120, 120))
                self.stop_photo = load("stop.png", (120, 120))
                self.upload_photo = load("upload.png", (270, 80))
                self.uploaded_photo = load("uploaded.png", (270, 80))
                self.upload_f_photo = load("upload_f.png", (270, 80))
            except Exception:
                pass
            return True
        except Exception as e:
            print(f"[WARNING] Couldn't load images: {e}")
            return False

    # ---------- UI ----------
    def create_widgets(self):
        # Header/title
        top_frame = tk.Frame(self.frame, bg="#1e1e1e")
        top_frame.pack(fill="x", pady=(6, 8))
        tk.Label(top_frame, text=self.title, font=("Segoe UI", 18, "bold"), fg="#ffffff", bg="#1e1e1e").pack(side="left", padx=12)

        # Status / PC Date/Time / Duration area
        info_frame = tk.Frame(self.frame, bg="#000000")
        info_frame.pack(fill="x", padx=12, pady=(4, 8))

        # Create 4 columns inside info_frame for PC Date, PC Time, Duration, Logging State
        lbl_date = ttk.Label(info_frame, text="PC Date:", background="#000000", foreground="white")
        lbl_date.grid(row=0, column=0, padx=6, sticky="e")
        self.pc_date_entry = ttk.Entry(info_frame, width=18, state='readonly', justify='center')
        self.pc_date_entry.grid(row=0, column=1, padx=6)

        lbl_time = ttk.Label(info_frame, text="PC Time:", background="#000000", foreground="white")
        lbl_time.grid(row=0, column=2, padx=6, sticky="e")
        self.pc_time_entry = ttk.Entry(info_frame, width=18, state='readonly', justify='center')
        self.pc_time_entry.grid(row=0, column=3, padx=6)

        lbl_duration = ttk.Label(info_frame, text="Logging Duration:", background="#000000", foreground="white")
        lbl_duration.grid(row=0, column=4, padx=6, sticky="e")
        self.duration_entry = ttk.Entry(info_frame, width=18, state='readonly', justify='center')
        self.duration_entry.grid(row=0, column=5, padx=6)

        # Status banner (color changes based on ALL ports connected)
        self.status_banner = tk.Label(self.frame, text="Status: Disconnected", font=("Segoe UI", 20, "bold"), bg="#8b0000", fg="white", height=1)
        self.status_banner.pack(fill="x", padx=12, pady=(4, 8))

        # Centered ports container
        ports_outer = tk.Frame(self.frame, bg="#000000")
        ports_outer.pack(expand=True, fill="both")

        # Create an inner frame that will be centered and contain columns
        self.ports_frame = tk.Frame(ports_outer, bg="#000000")
        self.ports_frame.place(relx=0.5, rely=0.5, anchor='center')

        # compute fonts based on screen height to keep readability on 1920x1080
        try:
            screen_h = self.parent.winfo_screenheight() or 1080
        except Exception:
            screen_h = 1080
        self.status_font = ("Segoe UI", max(18, int(screen_h * 0.028)), "bold")
        self.key_font = ("Consolas", max(14, int(screen_h * 0.018)))
        self.value_font = ("Consolas", max(16, int(screen_h * 0.024)), "bold")

        # build a column per port: key-value pairs stacked vertically
        self.value_vars = []
        for p_index, p in enumerate(self.ports):
            col = tk.Frame(self.ports_frame, bg="#000000")
            col.grid(row=0, column=p_index, padx=40, pady=10, sticky='n')

            # header for the port (Port #: portnumber)
            header_text = f"Port {p_index+1} ({p})"
            tk.Label(col, text=header_text, font=("Segoe UI", 16, "bold"), bg="#000000", fg="#ffffff").pack(pady=(0, 6))

            port_value_vars = []
            for lbl in self.port_labels[p_index]:
                rowf = tk.Frame(col, bg="#000000")
                rowf.pack(anchor='w', pady=8)
                key_lbl = tk.Label(rowf, text=f"{lbl}:", font=self.key_font, bg="#000000", fg="#cccccc", anchor='w')
                key_lbl.pack(side='left')
                var = tk.StringVar(value="--")
                val_lbl = tk.Label(rowf, textvariable=var, font=self.value_font, bg="#000000", fg="#ffffff", anchor='w')
                val_lbl.pack(side='left', padx=(8, 0))
                port_value_vars.append(var)
            self.value_vars.append(port_value_vars)

        # controls area (start/stop/upload/back)
        ctrl_frame = tk.Frame(self.frame, bg="#000000")
        ctrl_frame.pack(fill='x', padx=20, pady=(8, 12))

        # try load images
        self.load_images()

        if self.start_photo and self.stop_photo:
            self.logging_icon_label = tk.Label(ctrl_frame, image=self.start_photo, bg="#000000", cursor="hand2")
        else:
            self.logging_icon_label = tk.Label(ctrl_frame, text="Start Logging", bg="#1e1e1e", fg="white", cursor="hand2", font=("Segoe UI", 12, "bold"), padx=10, pady=6)
        self.logging_icon_label.pack(side='left')
        self.logging_icon_label.bind("<Button-1>", self.toggle_logging)

        # upload button
        if self.upload_photo:
            self.upload_label = tk.Label(ctrl_frame, image=self.upload_photo, bg="#000000", cursor="hand2")
        else:
            self.upload_label = tk.Label(ctrl_frame, text="Upload to Bodhi", bg="#1e1e1e", fg="white", cursor="hand2", font=("Segoe UI", 12), padx=10, pady=6)
        self.upload_label.pack(side='right')
        self.upload_label.bind("<Button-1>", self.try_upload)

        # alert label
        self.alert_label = tk.Label(self.frame, text="", fg="red", bg="#000000", font=("Segoe UI", 10, "bold"))
        self.alert_label.pack(pady=(4, 0))

        # back button
        back_btn = tk.Button(self.frame, text="Back to Home", command=self.go_back, bg="#e74c3c", fg="white", font=("Segoe UI", 12), padx=20, pady=8)
        back_btn.pack(pady=(12, 8))

        # bottom status bar per-port connection summary
        self.bottom_status = tk.Label(self.frame, text=self._initial_bottom_text(), bg="#222", fg="white", font=("Segoe UI", 10))
        self.bottom_status.pack(fill='x', pady=(6, 0))

    def _initial_bottom_text(self):
        return " | ".join([f"{p}:Checking..." for p in self.ports])

    # ---------- alerts / upload ----------
    def show_alert(self, msg):
        self.alert_label.config(text=msg)
        aid = self.parent.after(5000, lambda: self.alert_label.config(text=""))
        self.after_ids.append(aid)

    def try_upload(self, event=None):
        if upload is None:
            self.show_alert("Upload module not available")
            return
        result = upload.upload_csv(self.csv_filename)
        if result == "done":
            if self.uploaded_photo:
                self.upload_label.config(image=self.uploaded_photo)
                self.parent.after(3000, lambda: self.upload_label.config(image=self.upload_photo if self.upload_photo else None))
            else:
                self.show_alert("Upload done")
        else:
            if self.upload_f_photo:
                self.upload_label.config(image=self.upload_f_photo)
                self.parent.after(3000, lambda: self.upload_label.config(image=self.upload_photo if self.upload_photo else None))
            self.show_alert(str(result))

    # ---------- logging controls ----------
    def toggle_logging(self, event=None):
        current = self.logging_active.get()
        if not current:
            # try to start
            if not self._all_ports_connected():
                self.show_alert("Cannot start logging: Not all ports are connected")
                return
            self.logging_start_time = datetime.now()
            self.logging_active.set(True)
            if self.stop_photo:
                self.logging_icon_label.config(image=self.stop_photo)
            else:
                self.logging_icon_label.config(text="Stop Logging")
        else:
            # stop
            self.logging_start_time = None
            self.logging_active.set(False)
            if self.start_photo:
                self.logging_icon_label.config(image=self.start_photo)
            else:
                self.logging_icon_label.config(text="Start Logging")
            self.duration_entry.config(state='normal'); self.duration_entry.delete(0, tk.END); self.duration_entry.config(state='readonly')
        self.update_upload_visibility()

    def update_upload_visibility(self):
        if self.logging_active.get():
            self.upload_label.pack_forget()
        else:
            self.upload_label.pack(side='right')

    # ---------- sockets ----------
    def start_socket_servers(self):
        for p in self.ports:
            t = threading.Thread(target=self.socket_server, args=(p,), daemon=True)
            t.start()

    def socket_server(self, port):
        try:
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind(("0.0.0.0", port))
            server.listen(5)
            server.settimeout(1.0)
            self.server_sockets.append(server)
            print(f"[{self.title}] Listening on port {port}")
            while self.running:
                try:
                    client, addr = server.accept()
                    client.settimeout(None)
                    print(f"[{self.title}] Connection from {addr} on port {port}")
                    th = threading.Thread(target=self.handle_client, args=(client, addr, port), daemon=True)
                    th.start()
                except socket.timeout:
                    continue
                except OSError:
                    break
        except Exception as e:
            print(f"[{self.title}] Socket server error on port {port}: {e}")

    def handle_client(self, client_socket, client_address, port):
        with client_socket:
            try:
                buffer = b""
                while self.running:
                    chunk = client_socket.recv(4096)
                    if not chunk:
                        break
                    buffer += chunk
                    while b"\n" in buffer:
                        line, buffer = buffer.split(b"\n", 1)
                        try:
                            text = line.decode("utf-8").strip()
                        except Exception:
                            text = line.decode("latin-1").strip()
                        if text:
                            self.last_received[port] = time.time()
                            # schedule processing on GUI thread
                            self.parent.after(0, self._handle_incoming, port, text)
            except Exception as e:
                print(f"[{self.title}] Client error: {e}")

    def _handle_incoming(self, port, raw_text):
        # parse and update UI + csv
        parts = [p.strip() for p in raw_text.split(",")]
        p_idx = self.port_to_index.get(port, None)
        if p_idx is None:
            return

        # determine number of values to take for this port
        n = self._slice_count_for_port(p_idx)
        if n is None or n <= 0:
            n = len(self.port_labels[p_idx])

        selected = parts[:n]
        # pad/truncate
        if len(selected) < len(self.port_labels[p_idx]):
            selected += ["--"] * (len(self.port_labels[p_idx]) - len(selected))
        if len(selected) > len(self.port_labels[p_idx]):
            selected = selected[: len(self.port_labels[p_idx])]

        # update UI values
        for i, val in enumerate(selected):
            try:
                self.value_vars[p_idx][i].set(val)
            except Exception:
                pass

        # update PC date/time
        now = datetime.now()
        pc_date = now.strftime("%Y-%m-%d")
        pc_time = now.strftime("%H:%M:%S")
        self.pc_date_entry.config(state='normal'); self.pc_date_entry.delete(0, tk.END); self.pc_date_entry.insert(0, pc_date); self.pc_date_entry.config(state='readonly')
        self.pc_time_entry.config(state='normal'); self.pc_time_entry.delete(0, tk.END); self.pc_time_entry.insert(0, pc_time); self.pc_time_entry.config(state='readonly')

        # write a CSV row if logging is active
        if self.logging_active.get() and self.logging_start_time:
            # stop logging if overall disconnected for safety
            if not self._all_ports_connected():
                self.show_alert("A port disconnected. Stopping logging.")
                self._force_stop_logging()
                return

            duration = str(timedelta(seconds=int((now - self.logging_start_time).total_seconds())))
            # prepare flattened row with values placed at correct offset for this port
            row_values = [""] * self.total_columns
            offset = sum(self.per_port_counts[:p_idx])
            for i, v in enumerate(selected):
                if offset + i < len(row_values):
                    row_values[offset + i] = v
            # ensure length matches csv_columns
            if len(row_values) < len(self.csv_columns):
                row_values += [""] * (len(self.csv_columns) - len(row_values))
            if len(row_values) > len(self.csv_columns):
                row_values = row_values[: len(self.csv_columns)]

            try:
                with open(self.csv_path, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([pc_date, pc_time] + row_values + [duration])
            except Exception as e:
                print(f"[{self.title}] CSV write failed: {e}")

    def _slice_count_for_port(self, port_index):
        # data_slice can be:
        # - [] -> fall back to labels length
        # - [n] -> use n for all ports
        # - list of ints length == number of ports -> use per-port values
        if not self.data_slice:
            return None
        if isinstance(self.data_slice, list):
            if len(self.data_slice) == 1 and isinstance(self.data_slice[0], int):
                return self.data_slice[0]
            if len(self.data_slice) == len(self.ports) and isinstance(self.data_slice[port_index], int):
                return self.data_slice[port_index]
        # otherwise None
        return None

    # ---------- periodic updates / status ----------
    def update_logging_duration(self):
        now = datetime.now()
        if self.logging_active.get() and self.logging_start_time:
            elapsed = now - self.logging_start_time
            formatted = str(timedelta(seconds=int(elapsed.total_seconds())))
            self.duration_entry.config(state='normal'); self.duration_entry.delete(0, tk.END); self.duration_entry.insert(0, formatted); self.duration_entry.config(state='readonly')
        else:
            self.duration_entry.config(state='normal'); self.duration_entry.delete(0, tk.END); self.duration_entry.insert(0, ""); self.duration_entry.config(state='readonly')
        if self.running:
            aid = self.parent.after(1000, self.update_logging_duration)
            self.after_ids.append(aid)

    def update_status_bar(self):
        now = time.time()
        parts = []
        all_connected = True
        for p in self.ports:
            last = self.last_received.get(p)
            status = "Connected" if last and (now - last) <= 2.0 else "Disconnected"
            if status == "Disconnected":
                all_connected = False
            parts.append(f"{p}:{status}")
        # bottom status text
        self.bottom_status.config(text=" | ".join(parts))

        # update banner color based on all_connected
        if all_connected:
            self.status_banner.config(text="Status: Connected", bg="#2e8b57")
        else:
            prev = self.status_banner.cget("text")
            self.status_banner.config(text="Status: Disconnected", bg="#8b0000")
            # if we just discovered a disconnect while logging, stop logging
            if self.logging_active.get():
                self.show_alert("Port disconnected. Stopping logging.")
                self._force_stop_logging()

        if self.running:
            aid = self.parent.after(500, self.update_status_bar)
            self.after_ids.append(aid)

    def _all_ports_connected(self):
        now = time.time()
        for p in self.ports:
            last = self.last_received.get(p)
            if not last or (now - last) > 2.0:
                return False
        return True

    def start_periodic_updates(self):
        self.update_logging_duration()
        self.update_status_bar()

    # ---------- navigation ----------
    def go_back(self):
        self.destroy()
        try:
            self.parent.home_screen()
        except Exception:
            pass

    # ---------- forced stop (internal) ----------
    def _force_stop_logging(self):
        self.logging_start_time = None
        self.logging_active.set(False)
        if self.start_photo:
            try:
                self.logging_icon_label.config(image=self.start_photo)
            except Exception:
                self.logging_icon_label.config(text="Start Logging")
        else:
            self.logging_icon_label.config(text="Start Logging")
        self.update_upload_visibility()

    # ---------- shutdown ----------
    def shutdown(self):
        self.running = False
        # close server sockets
        for s in list(self.server_sockets):
            try:
                s.close()
            except Exception:
                pass
        # cancel scheduled after callbacks
        for aid in list(self.after_ids):
            try:
                self.parent.after_cancel(aid)
            except Exception:
                pass

    def destroy(self):
        self.shutdown()
        try:
            self.frame.destroy()
        except Exception:
            pass

    def get_frame(self):
        return self.frame


# top-level factory function used by your show_sensor_screen
def display(parent, sensor_config):
    return DynamicSensorFrame(parent, sensor_config)
