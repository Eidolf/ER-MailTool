import customtkinter as ctk
import threading
from src.network_tools import NetworkTools

class PortScanner(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        ctk.CTkLabel(self, text="Port Scanner", font=("Roboto", 20, "bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Input
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.host_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Host / IP Address")
        self.host_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.scan_btn = ctk.CTkButton(self.input_frame, text="Scan Common Ports", command=self.start_scan)
        self.scan_btn.grid(row=0, column=1, padx=10, pady=10)

        # Results
        self.result_box = ctk.CTkTextbox(self, font=("Consolas", 12), state="disabled")
        self.result_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

    def start_scan(self):
        host = self.host_entry.get().strip()
        if not host:
            return
        
        self.scan_btn.configure(state="disabled", text="Scanning...")
        self.result_box.configure(state="normal")
        self.result_box.delete("0.0", "end")
        self.result_box.insert("end", f"Scanning common mail ports on: {host}...\n\n")
        self.result_box.insert("end", f"{'Port':<10} {'Service':<15} {'Status':<10}\n")
        self.result_box.insert("end", "-"*40 +("\n"))
        self.result_box.configure(state="disabled")
        
        threading.Thread(target=self.perform_scan, args=(host,), daemon=True).start()

    def perform_scan(self, host):
        try:
            results = NetworkTools.scan_common_ports(host)
            self.result_box.configure(state="normal")
            
            # Sort by port number
            for port in sorted(results.keys()):
                service, is_open = results[port]
                status = "OPEN" if is_open else "CLOSED"
                color = "green" if is_open else "red" # (Console doesn't support color tags easily, sticking to text)
                
                line = f"{port:<10} {service:<15} {status:<10}\n"
                self.result_box.insert("end", line)
                
        except Exception as e:
            self.result_box.configure(state="normal")
            self.result_box.insert("end", f"Error: {str(e)}\n")
        finally:
            self.result_box.configure(state="disabled")
            self.scan_btn.configure(state="normal", text="Scan Common Ports")
