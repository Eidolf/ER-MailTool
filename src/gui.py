import customtkinter as ctk
from src.ui.smtp_tester import SMTPTester
from src.ui.mx_lookup import MXLookup
from src.ui.dns_lookup import DNSLookup
from src.ui.port_scanner import PortScanner
from src.ui.blacklist_check import BlacklistCheck
from src.ui.whois_lookup import WhoisLookup

# Theme Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ERMailToolGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ER-MailTool - Offline MX Toolbox")
        self.geometry("1100x700")

        # Layout: Sidebar (Navigation) + Main Content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ER-MailTool", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Nav Buttons
        self.btn_smtp = self.create_nav_button("SMTP Tester", 1, self.show_smtp)
        self.btn_mx = self.create_nav_button("MX Lookup", 2, self.show_mx)
        self.btn_dns = self.create_nav_button("DNS Lookup", 3, self.show_dns)
        self.btn_port = self.create_nav_button("Port Scanner", 4, self.show_port)
        self.btn_rbl = self.create_nav_button("Blacklist Check", 5, self.show_rbl)
        self.btn_whois = self.create_nav_button("Whois Lookup", 6, self.show_whois)
        
        # --- Main Content Area ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

        # -- Views --
        self.views = {}
        self.views["smtp"] = SMTPTester(self.main_area)
        self.views["mx"] = MXLookup(self.main_area)
        self.views["dns"] = DNSLookup(self.main_area)
        self.views["port"] = PortScanner(self.main_area)
        self.views["rbl"] = BlacklistCheck(self.main_area)
        self.views["whois"] = WhoisLookup(self.main_area)
        
        # Default View
        self.show_smtp()

    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=command, fg_color="transparent", text_color=("gray10", "#DCE4EE"), hover_color=("gray70", "gray30"), anchor="w")
        btn.grid(row=row, column=0, padx=20, pady=10, sticky="ew")
        return btn

    def show_view(self, view_name):
        # Hide all
        for view in self.views.values():
            view.grid_forget()
        
        # Show selected
        self.views[view_name].grid(row=0, column=0, sticky="nsew")

    def show_smtp(self): self.show_view("smtp")
    def show_mx(self): self.show_view("mx")
    def show_dns(self): self.show_view("dns")
    def show_port(self): self.show_view("port")
    def show_rbl(self): self.show_view("rbl")
    def show_whois(self): self.show_view("whois")

def run_gui():
    app = ERMailToolGUI()
    app.mainloop()
