import customtkinter as ctk
from src.ui.smtp_tester import SMTPTester

# Theme Settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class ERMailToolGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("ER-MailTool - Offline MX Toolbox")
        self.geometry("1000x700")

        # Layout: Sidebar (Navigation) + Main Content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="ER-MailTool", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Nav Buttons
        self.btn_smtp = self.create_nav_button("SMTP Tester", 1, self.show_smtp)
        self.btn_mx = self.create_nav_button("MX Lookup", 2, self.show_mx)
        self.btn_dns = self.create_nav_button("DNS Check", 3, self.show_dns)
        
        # --- Main Content Area ---
        self.main_area = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew")
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)

        # -- Views --
        self.smtp_view = SMTPTester(self.main_area)
        self.mx_view = self.create_placeholder_view("MX Lookup Tool (Coming Soon)")
        self.dns_view = self.create_placeholder_view("DNS Check Tool (Coming Soon)")

        # Default View
        self.show_smtp()

    def create_nav_button(self, text, row, command):
        btn = ctk.CTkButton(self.sidebar_frame, text=text, command=command, fg_color="transparent", text_color=("gray10", "#DCE4EE"), hover_color=("gray70", "gray30"), anchor="w")
        btn.grid(row=row, column=0, padx=20, pady=10, sticky="ew")
        return btn

    def create_placeholder_view(self, text):
        frame = ctk.CTkFrame(self.main_area)
        label = ctk.CTkLabel(frame, text=text, font=ctk.CTkFont(size=20))
        label.place(relx=0.5, rely=0.5, anchor="center")
        return frame

    def show_view(self, view):
        # Hide all
        self.smtp_view.grid_forget()
        self.mx_view.grid_forget()
        self.dns_view.grid_forget()
        
        # Show selected
        view.grid(row=0, column=0, sticky="nsew")

    def show_smtp(self):
        self.show_view(self.smtp_view)

    def show_mx(self):
        self.show_view(self.mx_view)

    def show_dns(self):
        self.show_view(self.dns_view)

def run_gui():
    app = ERMailToolGUI()
    app.mainloop()
