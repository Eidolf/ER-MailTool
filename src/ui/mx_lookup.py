import customtkinter as ctk
import threading
from src.network_tools import NetworkTools

class MXLookup(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        ctk.CTkLabel(self, text="MX Lookup", font=("Roboto", 20, "bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Input
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.domain_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter Domain (e.g., google.com)")
        self.domain_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.domain_entry.bind("<Return>", lambda event: self.start_lookup())

        self.lookup_btn = ctk.CTkButton(self.input_frame, text="Lookup MX", command=self.start_lookup)
        self.lookup_btn.grid(row=0, column=1, padx=10, pady=10)

        # Results
        self.result_box = ctk.CTkTextbox(self, font=("Consolas", 12), state="disabled")
        self.result_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

    def start_lookup(self):
        domain = self.domain_entry.get().strip()
        if not domain:
            return
        
        self.lookup_btn.configure(state="disabled", text="Querying...")
        self.result_box.configure(state="normal")
        self.result_box.delete("0.0", "end")
        self.result_box.insert("end", f"Querying MX records for: {domain}...\n\n")
        self.result_box.configure(state="disabled")
        
        threading.Thread(target=self.perform_lookup, args=(domain,), daemon=True).start()

    def perform_lookup(self, domain):
        try:
            records = NetworkTools.get_mx_records(domain)
            self.result_box.configure(state="normal")
            
            if isinstance(records, list):
                self.result_box.insert("end", f"{'Preference':<10} {'Mail Exchanger':<40}\n")
                self.result_box.insert("end", "-"*60 + "\n")
                for exchange, pref in records:
                   self.result_box.insert("end", f"{pref:<10} {exchange:<40}\n")
            else:
                self.result_box.insert("end", f"Error: {records}\n")
                
        except Exception as e:
            self.result_box.configure(state="normal")
            self.result_box.insert("end", f"Critical Error: {str(e)}\n")
        finally:
            self.result_box.configure(state="disabled")
            self.lookup_btn.configure(state="normal", text="Lookup MX")
