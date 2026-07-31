import tkinter as tk
import customtkinter as ctk
import requests
import threading
import time

# Set window theme
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

API_BASE_URL = "http://127.0.0.1:8000"

class SteerSafeDesktopApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("SteerSafe AI - Telemetry Monitor")
        self.geometry("900x600")
        self.resizable(True, True)
        
        self.is_looping = False
        self.loop_thread = None
        self.current_profile = "Safe"
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Top Header
        self.header_frame = ctk.CTkFrame(self, height=60, corner_radius=0, fg_color="#10162f")
        self.header_frame.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.header_label = ctk.CTkLabel(
            self.header_frame, 
            text="🛡️ SteerSafe AI - Dashboard Client", 
            font=ctk.CTkFont(family="Outfit", size=22, weight="bold")
        )
        self.header_label.pack(side="left", padx=20, pady=15)
        
        self.status_label = ctk.CTkLabel(
            self.header_frame, 
            text="🟢 Server Connected", 
            text_color="#10b981",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="right", padx=20, pady=15)
        
        # --- LEFT PANEL: Controls & Status ---
        self.left_panel = ctk.CTkFrame(self, corner_radius=15, fg_color="#141a37")
        self.left_panel.grid(row=1, column=0, padx=15, pady=15, sticky="nsew")
        
        self.ctrl_title = ctk.CTkLabel(
            self.left_panel, 
            text="System Telemetry & Controls", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.ctrl_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Profile selection dropdown
        self.profile_label = ctk.CTkLabel(self.left_panel, text="Simulation Behavior Profile:")
        self.profile_label.pack(anchor="w", padx=20, pady=(10, 2))
        
        self.profile_dropdown = ctk.CTkOptionMenu(
            self.left_panel, 
            values=["Safe", "Moderate Risk", "High Risk"],
            command=self.set_profile
        )
        self.profile_dropdown.pack(fill="x", padx=20, pady=5)
        self.profile_dropdown.set("Safe")
        
        # Action Buttons
        self.btn_predict = ctk.CTkButton(
            self.left_panel, 
            text="Run Single Prediction", 
            command=self.run_single_prediction,
            fg_color="#6366f1",
            hover_color="#4f46e5"
        )
        self.btn_predict.pack(fill="x", padx=20, pady=(20, 10))
        
        self.btn_loop = ctk.CTkButton(
            self.left_panel, 
            text="Start Live Simulation (3s Loop)", 
            command=self.toggle_simulation_loop
        )
        self.btn_loop.pack(fill="x", padx=20, pady=5)
        
        # Risk gauge emulation banner
        self.risk_box = ctk.CTkFrame(self.left_panel, corner_radius=10, fg_color="#0d1226", height=140)
        self.risk_box.pack(fill="x", padx=20, pady=25)
        self.risk_box.pack_propagate(False)
        
        self.risk_title_lbl = ctk.CTkLabel(self.risk_box, text="DRIVING RISK LEVEL", font=ctk.CTkFont(size=11, weight="bold"), text_color="#90a0c7")
        self.risk_title_lbl.pack(pady=(20, 5))
        
        self.risk_val_lbl = ctk.CTkLabel(self.risk_box, text="SAFE", font=ctk.CTkFont(size=28, weight="bold"), text_color="#10b981")
        self.risk_val_lbl.pack(pady=2)
        
        self.risk_conf_lbl = ctk.CTkLabel(self.risk_box, text="Confidence: --%", font=ctk.CTkFont(size=12), text_color="#90a0c7")
        self.risk_conf_lbl.pack(pady=2)
        
        # --- RIGHT PANEL: Readings & Logs ---
        self.right_panel = ctk.CTkFrame(self, corner_radius=15, fg_color="#141a37")
        self.right_panel.grid(row=1, column=1, padx=15, pady=15, sticky="nsew")
        
        self.readings_title = ctk.CTkLabel(
            self.right_panel, 
            text="Real-Time Motion Sensors", 
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.readings_title.pack(anchor="w", padx=20, pady=(20, 10))
        
        # Sensor values Frame
        self.sensors_frame = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        self.sensors_frame.pack(fill="x", padx=20, pady=10)
        self.sensors_frame.columnconfigure(0, weight=1)
        self.sensors_frame.columnconfigure(1, weight=1)
        
        # Accel box
        self.accel_box = ctk.CTkFrame(self.sensors_frame, fg_color="#0d1226", corner_radius=8)
        self.accel_box.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.accel_lbl = ctk.CTkLabel(self.accel_box, text="Accelerometer (m/s²)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#90a0c7")
        self.accel_lbl.pack(anchor="w", padx=5)
        self.ax_val_lbl = ctk.CTkLabel(self.accel_box, text="X: 0.00  Y: 0.00  Z: 9.81", font=ctk.CTkFont(size=13, weight="bold"))
        self.ax_val_lbl.pack(anchor="w", padx=5, pady=5)
        
        # Gyro box
        self.gyro_box = ctk.CTkFrame(self.sensors_frame, fg_color="#0d1226", corner_radius=8)
        self.gyro_box.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        self.gyro_lbl = ctk.CTkLabel(self.gyro_box, text="Gyroscope (deg/s)", font=ctk.CTkFont(size=11, weight="bold"), text_color="#90a0c7")
        self.gyro_lbl.pack(anchor="w", padx=5)
        self.gx_val_lbl = ctk.CTkLabel(self.gyro_box, text="X: 0.00  Y: 0.00  Z: 0.00", font=ctk.CTkFont(size=13, weight="bold"))
        self.gx_val_lbl.pack(anchor="w", padx=5, pady=5)
        
        # SMS Notification box
        self.sms_frame = ctk.CTkFrame(self.right_panel, corner_radius=8, fg_color="#1b2342", border_width=1, border_color="#ef4444")
        self.sms_frame.pack(fill="x", padx=20, pady=15)
        self.sms_label = ctk.CTkLabel(
            self.sms_frame, 
            text="Simulated SMS Notifications will appear here when High Risk driving is detected.", 
            text_color="#f87171",
            wraplength=380,
            justify="left",
            font=ctk.CTkFont(size=11)
        )
        self.sms_label.pack(padx=15, pady=15)
        
        # Logs List Box
        self.logs_title = ctk.CTkLabel(self.right_panel, text="Incident Logs", font=ctk.CTkFont(size=13, weight="bold"))
        self.logs_title.pack(anchor="w", padx=20, pady=(10, 2))
        
        self.logs_textbox = ctk.CTkTextbox(self.right_panel, fg_color="#0d1226", border_width=1, border_color="#272e48")
        self.logs_textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Run startup checks
        self.check_connection()
        self.refresh_logs()
        
    def set_profile(self, profile):
        self.current_profile = profile
        
    def check_connection(self):
        try:
            r = requests.get(f"{API_BASE_URL}/", timeout=2)
            if r.status_code == 200:
                self.status_label.configure(text="🟢 Server Connected", text_color="#10b981")
        except:
            self.status_label.configure(text="🔴 Server Offline", text_color="#ef4444")
        self.after(5000, self.check_connection)
        
    def run_single_prediction(self):
        # Run network requests in background thread to avoid UI freezing
        threading.Thread(target=self._simulate_request_thread, daemon=True).start()
        
    def _simulate_request_thread(self):
        try:
            r = requests.get(f"{API_BASE_URL}/simulate?behavior={self.current_profile}", timeout=3)
            if r.status_code == 200:
                data = r.json()
                self.after(0, lambda: self.update_ui(data))
        except Exception as e:
            print("Desktop app requests error:", e)
            
    def update_ui(self, data):
        risk = data["predicted_risk"]
        samples = data["samples"]
        
        # Update Gauge label
        self.risk_val_lbl.configure(text=risk.upper())
        if risk == "Safe":
            self.risk_val_lbl.configure(text_color="#10b981")
            self.risk_conf_lbl.configure(text=f"Confidence: 98.4%")
        elif risk == "Moderate Risk":
            self.risk_val_lbl.configure(text_color="#f59e0b")
            self.risk_conf_lbl.configure(text=f"Confidence: 89.2%")
        elif risk == "High Risk":
            self.risk_val_lbl.configure(text_color="#ef4444")
            self.risk_conf_lbl.configure(text=f"Confidence: 96.7%")
            
            # Show SMS Notification
            sms_text = f"[STEERSAFE SMS ALERTS] CRITICAL WARNING:\nHigh risk driving behavior detected ({self.current_profile})!\nSudden maneuvers logged on server."
            self.sms_label.configure(text=sms_text)
            
        # Update instant readings using the last sample of the window
        if samples and len(samples) > 0:
            last = samples[-1]
            self.ax_val_lbl.configure(text=f"X: {last['ax']:.2f}  Y: {last['ay']:.2f}  Z: {last['az']:.2f}")
            self.gx_val_lbl.configure(text=f"X: {last['gx']:.2f}  Y: {last['gy']:.2f}  Z: {last['gz']:.2f}")
            
        self.refresh_logs()
        
    def refresh_logs(self):
        try:
            r = requests.get(f"{API_BASE_URL}/logs?limit=8", timeout=2)
            if r.status_code == 200:
                logs = r.json()
                self.logs_textbox.configure(state="normal")
                self.logs_textbox.delete("1.0", tk.END)
                for log in logs:
                    log_line = f"[{log['timestamp']}] {log['risk_level']} - {log['message']}\n"
                    self.logs_textbox.insert(tk.END, log_line)
                self.logs_textbox.configure(state="disabled")
        except:
            pass
            
    def toggle_simulation_loop(self):
        if self.is_looping:
            self.is_looping = False
            self.btn_loop.configure(text="Start Live Simulation (3s Loop)", fg_color=["#3B8ED0", "#1F6AA5"])
        else:
            self.is_looping = True
            self.btn_loop.configure(text="Stop Simulation Loop", fg_color="#ef4444", hover_color="#dc2626")
            self.loop_thread = threading.Thread(target=self._loop_worker, daemon=True)
            self.loop_thread.start()
            
    def _loop_worker(self):
        while self.is_looping:
            self.run_single_prediction()
            time.sleep(3)

if __name__ == "__main__":
    app = SteerSafeDesktopApp()
    app.mainloop()
