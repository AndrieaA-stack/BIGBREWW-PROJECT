import os
import customtkinter as ctk
from PIL import Image, ImageDraw
from CUSTOMER import CustomerPortal
from ADMIN import AdminPortal
from db_helper import fetch_all_menu_items

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("dark-blue")

LOGO_FILE_PATH = "LOGO.png"


def create_placeholder_pil_image(color_hex="#FFA500", size=(80, 80)):
    img = Image.new("RGBA", size, color=color_hex)
    draw = ImageDraw.Draw(img)
    draw.rectangle([2, 2, size[0] - 3, size[1] - 3], outline="white", width=2)
    return img


def load_custom_image(file_path, default_color="#FF8C00", size=(50, 50)):
    if os.path.exists(file_path):
        try:
            return Image.open(file_path).convert("RGBA")
        except Exception:
            return create_placeholder_pil_image(default_color, size)
    return create_placeholder_pil_image(default_color, size)


class BigBrewApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BigBrew POS & Order System")
        self.geometry("1100x720")
        self.minsize(950, 600)

        # Load menu items directly from MySQL database with safe fallback
        db_items = fetch_all_menu_items()
        if db_items:
            self.shared_menu_items = db_items
        else:
            self.shared_menu_items = [
                {"id": 1, "name": "Classic Milk Tea", "category": "Milk Tea", "price": 29.00, "image": None},
                {"id": 2, "name": "Wintermelon", "category": "Milk Tea", "price": 29.00, "image": None},
                {"id": 3, "name": "Okinawa", "category": "Milk Tea", "price": 29.00, "image": None},
                {"id": 4, "name": "Taro", "category": "Milk Tea", "price": 29.00, "image": None},
                {"id": 5, "name": "Brewed Coffee", "category": "Iced Coffee", "price": 29.00, "image": None},
                {"id": 6, "name": "Caramel Macchiato", "category": "Iced Coffee", "price": 29.00, "image": None},
                {"id": 7, "name": "Green Apple", "category": "Fruit Tea", "price": 29.00, "image": None},
                {"id": 8, "name": "Lychee", "category": "Fruit Tea", "price": 29.00, "image": None},
            ]

        self._init_image_assets()

        self.user_role = None
        self.customer_name = "Guest"

        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True)

        self.show_auth_selection()

    def _init_image_assets(self):
        pil_logo = load_custom_image(LOGO_FILE_PATH, default_color="#FF8C00", size=(80, 80))
        self.logo_ctk_image = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(50, 50))

        pil_item = create_placeholder_pil_image("#D2B48C", size=(60, 60))
        self.item_ctk_image = ctk.CTkImage(light_image=pil_item, dark_image=pil_item, size=(45, 45))

    def _clear_container(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()

    def show_auth_selection(self):
        self._clear_container()

        card = ctk.CTkFrame(self.main_container, corner_radius=15, width=400, height=450)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, image=self.logo_ctk_image, text="").pack(pady=(25, 5))
        ctk.CTkLabel(
            card,
            text="WELCOME TO BIGBREW",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#FFA500"
        ).pack(pady=5)
        ctk.CTkLabel(card, text="Please select your portal to continue", font=ctk.CTkFont(size=12)).pack(pady=(0, 25))

        ctk.CTkButton(
            card,
            text="🛒 Customer Ordering",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            width=260,
            fg_color="#FFA500",
            hover_color="#CC8400",
            text_color="black",
            command=self.show_customer_login
        ).pack(pady=10)

        ctk.CTkButton(
            card,
            text="🔐 Admin Management",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=45,
            width=260,
            fg_color="#333333",
            hover_color="#444444",
            command=self.show_admin_login
        ).pack(pady=10)

    def show_customer_login(self):
        self._clear_container()

        card = ctk.CTkFrame(self.main_container, corner_radius=15, width=400, height=450)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, image=self.logo_ctk_image, text="").pack(pady=(20, 5))
        ctk.CTkLabel(card, text="Customer Portal", font=ctk.CTkFont(size=22, weight="bold"), text_color="#FFA500").pack(pady=(5, 5))
        ctk.CTkLabel(card, text="Enter your name to personalize your order receipt:").pack(pady=5)

        name_entry = ctk.CTkEntry(card, width=280)
        name_entry.pack(pady=15)

        def proceed_as_customer():
            val = name_entry.get().strip()
            self.customer_name = val if val else "Guest Customer"
            self.user_role = "Customer"
            self.build_pos_interface()

        ctk.CTkButton(
            card,
            text="Start Ordering",
            fg_color="#FFA500",
            hover_color="#CC8400",
            text_color="black",
            font=ctk.CTkFont(weight="bold"),
            width=280,
            height=40,
            command=proceed_as_customer
        ).pack(pady=10)

        ctk.CTkButton(card, text="← Back", fg_color="transparent", width=100, command=self.show_auth_selection).pack(pady=5)

    def show_admin_login(self):
        self._clear_container()

        card = ctk.CTkFrame(self.main_container, corner_radius=15, width=400, height=450)
        card.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, image=self.logo_ctk_image, text="").pack(pady=(20, 5))
        ctk.CTkLabel(card, text="Admin Login", font=ctk.CTkFont(size=22, weight="bold")).pack(pady=(5, 5))

        pass_entry = ctk.CTkEntry(card, width=280, show="*")
        pass_entry.pack(pady=15)

        err_label = ctk.CTkLabel(card, text="", text_color="#E74C3C")
        err_label.pack(pady=2)

        def verify_admin():
            if pass_entry.get() == "BIGBREW":
                self.user_role = "Admin"
                self.build_admin_dashboard()
            else:
                err_label.configure(text="Invalid Password!")

        ctk.CTkButton(
            card,
            text="Login as Admin",
            fg_color="#2ECC71",
            hover_color="#27AE60",
            font=ctk.CTkFont(weight="bold"),
            width=280,
            height=40,
            command=verify_admin
        ).pack(pady=10)

        ctk.CTkButton(card, text="← Back", fg_color="transparent", width=100, command=self.show_auth_selection).pack(pady=5)

    def build_admin_dashboard(self):
        self._clear_container()
        admin_portal = AdminPortal(self.main_container, self)
        admin_portal.pack(fill="both", expand=True)

    def build_pos_interface(self):
        self._clear_container()
        customer_portal = CustomerPortal(self.main_container, self)
        customer_portal.pack(fill="both", expand=True)


if __name__ == "__main__":
    app = BigBrewApp()
    app.mainloop()