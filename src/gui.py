import customtkinter as ctk

from src.ui.anonymous_smtp import AnonymousSMTPTester
from src.ui.authenticated_smtp import AuthenticatedSMTPTester
from src.ui.blacklist_check import BlacklistCheck
from src.ui.dkim_lookup import DKIMLookup
from src.ui.dmarc_analyzer import DMARCAnalyzer
from src.ui.dns_lookup import DNSLookup
from src.ui.mx_lookup import MXLookup
from src.ui.oauth_tester import OAuthTesterView
from src.ui.port_scanner import PortScanner
from src.ui.spf_analyzer import SPFAnalyzer
from src.ui.whois_lookup import WhoisLookup

# Theme Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ERMailToolGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ER-MailTool")
        self.geometry("1100x800")

        # Layout: Sidebar (Navigation) + Main Content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(16, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ER-MailTool", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Nav Buttons
        # Connect & Test
        self.create_nav_label("Connectivity", 1)
        self.btn_auth_smtp = self.create_nav_button("Authenticated SMTP", 2, self.show_auth_smtp)
        self.btn_anon_smtp = self.create_nav_button("Anonymous SMTP", 3, self.show_anon_smtp)
        self.btn_port = self.create_nav_button("Port Scanner", 4, self.show_port)
        
        # DNS & Network
        self.create_nav_label("Network / DNS", 5)
        self.btn_mx = self.create_nav_button("MX Lookup", 6, self.show_mx)
        self.btn_dns = self.create_nav_button("DNS Lookup", 7, self.show_dns)
        self.btn_whois = self.create_nav_button("Whois Lookup", 8, self.show_whois)
        
        # Security / Auth
        self.create_nav_label("Security / Auth", 9)
        self.btn_oauth = self.create_nav_button("OAuth 2.0 Auth Test", 10, self.show_oauth)
        self.btn_spf = self.create_nav_button("SPF Analyzer", 11, self.show_spf)
        self.btn_dmarc = self.create_nav_button("DMARC Analyzer", 12, self.show_dmarc)
        self.btn_dkim = self.create_nav_button("DKIM Lookup", 13, self.show_dkim)
        self.btn_rbl = self.create_nav_button("Blacklist Check", 14, self.show_rbl)

        # --- Main Content Area ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

        # -- Views --
        self.views = {}
        self.views["auth_smtp"] = AuthenticatedSMTPTester(self.main_area)
        self.views["anon_smtp"] = AnonymousSMTPTester(self.main_area)
        self.views["mx"] = MXLookup(self.main_area)
        self.views["dns"] = DNSLookup(self.main_area)
        self.views["port"] = PortScanner(self.main_area)
        self.views["rbl"] = BlacklistCheck(self.main_area)
        self.views["whois"] = WhoisLookup(self.main_area)
        self.views["oauth"] = OAuthTesterView(self.main_area)
        self.views["spf"] = SPFAnalyzer(self.main_area)
        self.views["dmarc"] = DMARCAnalyzer(self.main_area)
        self.views["dkim"] = DKIMLookup(self.main_area)
        
        # Default View
        self.show_auth_smtp()

    def create_nav_label(self, text, row):
        lbl = ctk.CTkLabel(self.sidebar_frame, text=text, text_color="gray70", anchor="w", font=ctk.CTkFont(size=12, weight="bold"))
        lbl.grid(row=row, column=0, padx=20, pady=(15, 0), sticky="ew")

    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=command, fg_color="transparent", text_color=("gray10", "#DCE4EE"), hover_color=("gray70", "gray30"), anchor="w")
        btn.grid(row=row, column=0, padx=20, pady=2, sticky="ew")
        return btn

    def show_view(self, view_name):
        for view in self.views.values():
            view.grid_forget()
        self.views[view_name].grid(row=0, column=0, sticky="nsew")

    def show_auth_smtp(self): self.show_view("auth_smtp")
    def show_anon_smtp(self): self.show_view("anon_smtp")
    def show_mx(self): self.show_view("mx")
    def show_dns(self): self.show_view("dns")
    def show_port(self): self.show_view("port")
    def show_rbl(self): self.show_view("rbl")
    def show_whois(self): self.show_view("whois")
    def show_oauth(self): self.show_view("oauth")
    def show_spf(self): self.show_view("spf")
    def show_dmarc(self): self.show_view("dmarc")
    def show_dkim(self): self.show_view("dkim")

def run_gui():
    app = ERMailToolGUI()
    app.mainloop()
