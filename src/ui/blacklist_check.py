import customtkinter as ctk
import threading
from src.network_tools import NetworkTools

class BlacklistCheck(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        ctk.CTkLabel(self, text="Blacklist Check (RBL)", font=("Roboto", 20, "bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Input
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.ip_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter IP Address")
        self.ip_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.check_btn = ctk.CTkButton(self.input_frame, text="Check Reputation", command=self.start_check)
        self.check_btn.grid(row=0, column=1, padx=10, pady=10)

        # Results
        self.result_box = ctk.CTkTextbox(self, font=("Consolas", 12), state="disabled")
        self.result_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

    def start_check(self):
        ip = self.ip_entry.get().strip()
        if not ip:
            return
        
        self.check_btn.configure(state="disabled", text="Checking...")
        self.result_box.configure(state="normal")
        self.result_box.delete("0.0", "end")
        self.result_box.insert("end", f"Checking IP reputation for: {ip}...\n\n")
        self.result_box.insert("end", f"{'RBL Provider':<30} {'Status':<10}\n")
        self.result_box.insert("end", "-"*40 + "\n")
        self.result_box.configure(state="disabled")
        
        threading.Thread(target=self.perform_check, args=(ip,), daemon=True).start()

    def perform_check(self, ip):
        try:
            results = NetworkTools.check_rbl(ip)
            self.result_box.configure(state="normal")
            
            if "Error" in results:
                 self.result_box.insert("end", f"Error: {results['Error']}\n")
            else:
                for rbl, listed in results.items():
                    status = "LISTED" if listed else "OK"
                    # status = "ERROR" if listed is None else status
                    if listed is None: status = "TIMEOUT"
                    
                    self.result_box.insert("end", f"{rbl:<30} {status:<10}\n")
                
        except Exception as e:
            self.result_box.configure(state="normal")
            self.result_box.insert("end", f"Error: {str(e)}\n")
        finally:
            self.result_box.configure(state="disabled")
            self.check_btn.configure(state="normal", text="Check Reputation")
