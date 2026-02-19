import customtkinter as ctk
import threading
from src.network_tools import NetworkTools

class SPFAnalyzer(ctk.CTkFrame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # Header
        ctk.CTkLabel(self, text="SPF Record Analyzer", font=("Roboto", 20, "bold")).grid(row=0, column=0, padx=20, pady=(20, 10), sticky="w")

        # Input
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.grid(row=1, column=0, padx=20, pady=10, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        self.domain_entry = ctk.CTkEntry(self.input_frame, placeholder_text="Enter Domain (e.g., google.com)")
        self.domain_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        self.domain_entry.bind("<Return>", lambda event: self.start_analysis())

        self.analyze_btn = ctk.CTkButton(self.input_frame, text="Analyze SPF", command=self.start_analysis)
        self.analyze_btn.grid(row=0, column=1, padx=10, pady=10)

        # Results
        self.result_box = ctk.CTkTextbox(self, font=("Consolas", 12), state="disabled")
        self.result_box.grid(row=2, column=0, padx=20, pady=10, sticky="nsew")

    def start_analysis(self):
        domain = self.domain_entry.get().strip()
        if not domain:
            return
        
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.result_box.configure(state="normal")
        self.result_box.delete("0.0", "end")
        self.result_box.insert("end", f"Fetching SPF record for: {domain}...\n\n")
        self.result_box.configure(state="disabled")
        
        threading.Thread(target=self.perform_analysis, args=(domain,), daemon=True).start()

    def perform_analysis(self, domain):
        try:
            record = NetworkTools.get_spf_record(domain)
            self.result_box.configure(state="normal")
            self.result_box.insert("end", f"Record:\n{record}\n")
            
            # Simple Breakdown (if valid record)
            if "v=spf1" in record:
                 self.result_box.insert("end", "\n--- Breakdown ---\n")
                 parts = record.split()
                 for part in parts:
                     self.result_box.insert("end", f"- {part}\n")

        except Exception as e:
            self.result_box.configure(state="normal")
            self.result_box.insert("end", f"Error: {str(e)}\n")
        finally:
            self.result_box.configure(state="disabled")
            self.analyze_btn.configure(state="normal", text="Analyze SPF")
