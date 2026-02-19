import customtkinter as ctk
import threading
from src.network_tools import NetworkTools

class DNSLookup(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        ctk.CTkLabel(self, text="DNS Lookup", font=("Roboto", 20, "bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Input
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.domain_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Domain (e.g., example.com)")
        self.domain_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        self.record_type = ctk.CTkComboBox(self.input_frame, values=["A", "AAAA", "CNAME", "TXT", "NS", "PTR", "SOA"])
        self.record_type.grid(row=0, column=1, padx=10, pady=10)
        self.record_type.set("A")

        self.lookup_btn = ctk.CTkButton(self.input_frame, text="Query", command=self.start_lookup)
        self.lookup_btn.grid(row=0, column=2, padx=10, pady=10)

        # Results
        self.result_box = ctk.CTkTextbox(self, font=("Consolas", 12), state="disabled")
        self.result_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

    def start_lookup(self):
        domain = self.domain_entry.get().strip()
        rtype = self.record_type.get()
        if not domain:
            return
        
        self.lookup_btn.configure(state="disabled", text="...")
        self.result_box.configure(state="normal")
        self.result_box.delete("0.0", "end")
        self.result_box.insert("end", f"Querying {rtype} records for: {domain}...\n\n")
        self.result_box.configure(state="disabled")
        
        threading.Thread(target=self.perform_lookup, args=(domain, rtype), daemon=True).start()

    def perform_lookup(self, domain, rtype):
        try:
            records = NetworkTools.get_dns_records(domain, rtype)
            self.result_box.configure(state="normal")
            
            if records and isinstance(records, list):
                for r in records:
                   self.result_box.insert("end", f"{r}\n")
            else:
                 self.result_box.insert("end", "No records found or query failed.\n")

        except Exception as e:
            self.result_box.configure(state="normal")
            self.result_box.insert("end", f"Error: {str(e)}\n")
        finally:
            self.result_box.configure(state="disabled")
            self.lookup_btn.configure(state="normal", text="Query")
