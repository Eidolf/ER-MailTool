import customtkinter as ctk
import threading
from src.network_tools import NetworkTools

class DKIMLookup(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        ctk.CTkLabel(self, text="DKIM Record Lookup", font=("Roboto", 20, "bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Input
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.input_frame, text="Selector:").grid(row=0, column=0, padx=10, pady=10)
        self.selector_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g., default, google")
        self.selector_entry.grid(row=0, column=1, padx=10, pady=10, sticky="ew")

        ctk.CTkLabel(self.input_frame, text="Domain:").grid(row=0, column=2, padx=10, pady=10)
        self.domain_entry = ctk.CTkEntry(self.input_frame, placeholder_text="e.g., example.com")
        self.domain_entry.grid(row=0, column=3, padx=10, pady=10, sticky="ew")
        
        self.lookup_btn = ctk.CTkButton(self.input_frame, text="Lookup", command=self.start_lookup)
        self.lookup_btn.grid(row=0, column=4, padx=10, pady=10)

        # Results
        self.result_box = ctk.CTkTextbox(self, font=("Consolas", 12), state="disabled")
        self.result_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

    def start_lookup(self):
        selector = self.selector_entry.get().strip()
        domain = self.domain_entry.get().strip()
        
        if not selector or not domain:
            return
        
        self.lookup_btn.configure(state="disabled", text="...")
        self.result_box.configure(state="normal")
        self.result_box.delete("0.0", "end")
        self.result_box.insert("end", f"Fetching DKIM for {selector}._domainkey.{domain}...\n\n")
        self.result_box.configure(state="disabled")
        
        threading.Thread(target=self.perform_lookup, args=(domain, selector), daemon=True).start()

    def perform_lookup(self, domain, selector):
        try:
            record = NetworkTools.get_dkim_record(domain, selector)
            self.result_box.configure(state="normal")
            
            # Formatting for very long keys
            formatted_record = str(record)
            if len(formatted_record) > 80:
                 # simple wrap attempt or just let CTKTextbox wrap
                 pass 

            self.result_box.insert("end", f"{formatted_record}\n")

        except Exception as e:
            self.result_box.configure(state="normal")
            self.result_box.insert("end", f"Error: {str(e)}\n")
        finally:
            self.result_box.configure(state="disabled")
            self.lookup_btn.configure(state="normal", text="Lookup")
