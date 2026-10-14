import os
import shutil
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image
from db_helper import (
    insert_menu_item,
    update_menu_item_db,
    delete_menu_item_db,
    fetch_all_orders
)

IMAGE_ASSETS_DIR = "menu_images"
os.makedirs(IMAGE_ASSETS_DIR, exist_ok=True)


class AdminPortal(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        self.selected_item = None
        self.selected_image_path = None
        self.preview_image_ctk = None

        # Build dynamic category list from existing items, keeping defaults
        self.categories = ["Milk Tea", "Iced Coffee", "Fruit Tea"]
        for itm in self.app.shared_menu_items:
            cat = itm.get("category")
            if cat and cat not in self.categories:
                self.categories.append(cat)

        self._build_dashboard()

    def _build_dashboard(self):
        top_bar = ctk.CTkFrame(self, height=55, fg_color="#181818", corner_radius=0)
        top_bar.pack(fill="x", padx=0, pady=0)

        ctk.CTkLabel(
            top_bar,
            text="ADMIN MANAGEMENT DASHBOARD",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#FFA500"
        ).pack(side="left", padx=20, pady=12)

        ctk.CTkButton(
            top_bar,
            text="Logout",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=85,
            command=self.app.show_auth_selection
        ).pack(side="right", padx=20)

        self.tabview = ctk.CTkTabview(self, command=self._on_tab_change)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)

        self.tab_sales = self.tabview.add("Sales History")
        self.tab_admin = self.tabview.add("ADMIN MANAGEMENT")
        self.tabview.set("ADMIN MANAGEMENT")

        self._build_sales_history_tab(self.tab_sales)
        self._build_item_management_tab(self.tab_admin)

    def _on_tab_change(self):
        if self.tabview.get() == "Sales History":
            self._load_sales_history()

    #SALES HISTORY TAB
    def _build_sales_history_tab(self, parent_tab):
        parent_tab.grid_columnconfigure(0, weight=1)
        parent_tab.grid_rowconfigure(1, weight=1)

        stats_frame = ctk.CTkFrame(parent_tab, fg_color="transparent")
        stats_frame.grid(row=0, column=0, padx=10, pady=(10, 10), sticky="ew")

        self.total_revenue_lbl = ctk.CTkLabel(
            stats_frame,
            text="Total Revenue: ₱0.00",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#2ECC71"
        )
        self.total_revenue_lbl.pack(side="left", padx=10)

        self.total_orders_lbl = ctk.CTkLabel(
            stats_frame,
            text="Total Orders: 0",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFA500"
        )
        self.total_orders_lbl.pack(side="left", padx=20)

        ctk.CTkButton(
            stats_frame,
            text="Refresh History",
            width=120,
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=self._load_sales_history
        ).pack(side="right", padx=10)

        table_container = ctk.CTkFrame(parent_tab, corner_radius=10)
        table_container.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        header_frame = ctk.CTkFrame(table_container, fg_color="#2B2B2B", height=38, corner_radius=6)
        header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        columns = [
            ("Order ID", 90),
            ("Customer Name", 180),
            ("Date & Time", 180),
            ("Total Amount", 120),
            ("Cash Tendered", 120),
            ("Change", 100),
        ]

        for col_name, width in columns:
            ctk.CTkLabel(
                header_frame,
                text=col_name,
                width=width,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="center"
            ).pack(side="left", padx=4, pady=6)

        self.orders_scroll = ctk.CTkScrollableFrame(table_container)
        self.orders_scroll.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        self.orders_scroll.grid_columnconfigure(0, weight=1)

        self._load_sales_history()

    def _load_sales_history(self):
        for widget in self.orders_scroll.winfo_children():
            widget.destroy()

        orders = fetch_all_orders()

        if not orders:
            ctk.CTkLabel(
                self.orders_scroll,
                text="No transaction records found in database.",
                font=ctk.CTkFont(size=14),
                text_color="#888888"
            ).pack(pady=40)
            self.total_revenue_lbl.configure(text="Total Revenue: ₱0.00")
            self.total_orders_lbl.configure(text="Total Orders: 0")
            return

        total_rev = 0.0

        for idx, ord_row in enumerate(orders):
            bg_col = "#202020" if idx % 2 == 0 else "#262626"
            row_frame = ctk.CTkFrame(self.orders_scroll, fg_color=bg_col, corner_radius=4)
            row_frame.pack(fill="x", pady=2, padx=2)

            total_val = float(ord_row.get("total_amount", 0.0))
            cash_val = float(ord_row.get("cash_tendered", 0.0))
            change_val = float(ord_row.get("change_due", 0.0))
            total_rev += total_val

            raw_time = ord_row.get("timestamp")
            time_str = raw_time.strftime("%Y-%m-%d %H:%M:%S") if hasattr(raw_time, "strftime") else str(raw_time)

            row_data = [
                (f"#{ord_row.get('order_id')}", 90, "white"),
                (str(ord_row.get("customer_name", "Guest")), 180, "#FFA500"),
                (time_str, 180, "#AAAAAA"),
                (f"₱{total_val:.2f}", 120, "#2ECC71"),
                (f"₱{cash_val:.2f}", 120, "white"),
                (f"₱{change_val:.2f}", 100, "#3498DB"),
            ]

            for val, width, col in row_data:
                ctk.CTkLabel(
                    row_frame,
                    text=val,
                    width=width,
                    text_color=col,
                    font=ctk.CTkFont(size=12),
                    anchor="center"
                ).pack(side="left", padx=4, pady=8)

        self.total_revenue_lbl.configure(text=f"Total Revenue: ₱{total_rev:,.2f}")
        self.total_orders_lbl.configure(text=f"Total Orders: {len(orders)}")

    #ITEM MANAGEMENT TAB
    def _build_item_management_tab(self, parent_tab):
        parent_tab.grid_columnconfigure(0, weight=3)
        parent_tab.grid_columnconfigure(1, weight=2)
        parent_tab.grid_rowconfigure(0, weight=1)

        left_box = ctk.CTkFrame(parent_tab, corner_radius=10)
        left_box.grid(row=0, column=0, padx=(10, 10), pady=10, sticky="nsew")
        left_box.grid_rowconfigure(1, weight=1)
        left_box.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            left_box,
            text="Current Menu Items",
            font=ctk.CTkFont(size=16, weight="bold")
        ).grid(row=0, column=0, padx=15, pady=15, sticky="w")

        self.items_scroll = ctk.CTkScrollableFrame(left_box)
        self.items_scroll.grid(row=1, column=0, padx=15, pady=(0, 15), sticky="nsew")
        self.items_scroll.grid_columnconfigure(0, weight=1)

        right_box = ctk.CTkFrame(parent_tab, corner_radius=10)
        right_box.grid(row=0, column=1, padx=(10, 10), pady=10, sticky="nsew")

        ctk.CTkLabel(
            right_box,
            text="Item Management Form",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#FFA500"
        ).pack(pady=(15, 10))

        form_frame = ctk.CTkFrame(right_box, fg_color="transparent")
        form_frame.pack(fill="both", expand=True, padx=25, pady=5)

        # 1. Item Name
        ctk.CTkLabel(form_frame, text="Item Name:", anchor="w").pack(fill="x", pady=(2, 2))
        self.name_entry = ctk.CTkEntry(form_frame, placeholder_text="e.g. Dark Chocolate")
        self.name_entry.pack(fill="x", pady=(0, 6))

        # 2. Price
        ctk.CTkLabel(form_frame, text="Price (₱):", anchor="w").pack(fill="x", pady=(2, 2))
        self.price_entry = ctk.CTkEntry(form_frame, placeholder_text="29.00")
        self.price_entry.pack(fill="x", pady=(0, 6))

        # 3. Category + Add Category Button
        ctk.CTkLabel(form_frame, text="Category:", anchor="w").pack(fill="x", pady=(2, 2))
        cat_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        cat_row.pack(fill="x", pady=(0, 6))

        self.cat_menu = ctk.CTkOptionMenu(cat_row, values=self.categories)
        self.cat_menu.pack(side="left", fill="x", expand=True, padx=(0, 6))

        ctk.CTkButton(
            cat_row,
            text="➕ New Category",
            width=115,
            fg_color="#3498DB",
            hover_color="#2980B9",
            command=self._prompt_new_category
        ).pack(side="right")

        # 4. Item Image
        ctk.CTkLabel(form_frame, text="Item Image (Required):", anchor="w", font=ctk.CTkFont(weight="bold")).pack(fill="x", pady=(2, 2))

        img_picker_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        img_picker_row.pack(fill="x", pady=(0, 4))

        self.choose_img_btn = ctk.CTkButton(
            img_picker_row,
            text="📁 Browse Image...",
            fg_color="#3A3A3A",
            hover_color="#505050",
            width=130,
            command=self._browse_image
        )
        self.choose_img_btn.pack(side="left")

        self.img_path_label = ctk.CTkLabel(img_picker_row, text="No image selected", text_color="#888888", anchor="w")
        self.img_path_label.pack(side="left", padx=10, fill="x", expand=True)

        self.preview_box = ctk.CTkLabel(form_frame, text="[No Preview]", width=65, height=65, fg_color="#222222", corner_radius=6)
        self.preview_box.pack(pady=(0, 6))

        self.status_label = ctk.CTkLabel(form_frame, text="", text_color="#E74C3C", font=ctk.CTkFont(size=12))
        self.status_label.pack(pady=1)

        # Buttons
        ctk.CTkButton(
            form_frame,
            text="Add New",
            fg_color="#2ECC71",
            hover_color="#27AE60",
            text_color="black",
            font=ctk.CTkFont(weight="bold"),
            height=34,
            command=self._add_item
        ).pack(fill="x", pady=3)

        ctk.CTkButton(
            form_frame,
            text="Update Selected",
            fg_color="#FFA500",
            hover_color="#CC8400",
            text_color="black",
            font=ctk.CTkFont(weight="bold"),
            height=34,
            command=self._update_item
        ).pack(fill="x", pady=3)

        ctk.CTkButton(
            form_frame,
            text="Delete Selected",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            font=ctk.CTkFont(weight="bold"),
            height=34,
            command=self._delete_item
        ).pack(fill="x", pady=3)

        ctk.CTkButton(
            form_frame,
            text="Clear Selection",
            fg_color="#333333",
            hover_color="#444444",
            height=30,
            command=self._clear_form
        ).pack(fill="x", pady=(3, 6))

        self._refresh_items_list()

    def _prompt_new_category(self):
        """Dialog to create a brand new category."""
        dialog = ctk.CTkInputDialog(text="Enter new category name:", title="Add New Category")
        new_cat = dialog.get_input()
        if new_cat:
            new_cat = new_cat.strip()
            if new_cat and new_cat not in self.categories:
                self.categories.append(new_cat)
                self.cat_menu.configure(values=self.categories)
                self.cat_menu.set(new_cat)
                self.status_label.configure(text=f"Added category '{new_cat}'!", text_color="#2ECC71")

    def _browse_image(self):
        file_selected = filedialog.askopenfilename(
            title="Select Item Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.webp")]
        )
        if file_selected:
            self._set_selected_image(file_selected)

    def _set_selected_image(self, file_path):
        self.selected_image_path = file_path
        filename = os.path.basename(file_path)
        self.img_path_label.configure(text=filename, text_color="white")

        try:
            pil_img = Image.open(file_path)
            self.preview_image_ctk = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(55, 55))
            self.preview_box.configure(image=self.preview_image_ctk, text="")
        except Exception:
            self.preview_box.configure(image=None, text="[Error loading image]")

    def _refresh_items_list(self):
        for widget in self.items_scroll.winfo_children():
            widget.destroy()

        for idx, item in enumerate(self.app.shared_menu_items):
            row_frame = ctk.CTkFrame(self.items_scroll, fg_color="#242424", corner_radius=6)
            row_frame.pack(fill="x", pady=3, padx=2)

            info_text = f"[{item['category']}] {item['name']} - ₱{item['price']:.2f}"
            if item.get("image"):
                info_text += " 📷"

            lbl = ctk.CTkLabel(row_frame, text=info_text, font=ctk.CTkFont(size=13))
            lbl.pack(side="left", padx=12, pady=8)

            btn = ctk.CTkButton(
                row_frame,
                text="Select",
                width=65,
                height=26,
                fg_color="#3498DB",
                hover_color="#2980B9",
                command=lambda i=idx: self._select_item_for_edit(i)
            )
            btn.pack(side="right", padx=10, pady=8)

    def _select_item_for_edit(self, index):
        self.selected_item = self.app.shared_menu_items[index]
        self.name_entry.delete(0, "end")
        self.name_entry.insert(0, self.selected_item["name"])

        self.price_entry.delete(0, "end")
        self.price_entry.insert(0, f"{self.selected_item['price']:.2f}")

        cat = self.selected_item["category"]
        if cat not in self.categories:
            self.categories.append(cat)
            self.cat_menu.configure(values=self.categories)
        self.cat_menu.set(cat)

        if self.selected_item.get("image") and os.path.exists(self.selected_item["image"]):
            self._set_selected_image(self.selected_item["image"])
        else:
            self.selected_image_path = None
            self.img_path_label.configure(text="No image", text_color="#888888")
            self.preview_box.configure(image=None, text="[No Preview]")

        self.status_label.configure(text=f"Selected: {self.selected_item['name']}", text_color="#3498DB")

    def _add_item(self):
        name = self.name_entry.get().strip()
        price_str = self.price_entry.get().strip()
        category = self.cat_menu.get()

        if not name or not price_str:
            self.status_label.configure(text="Please fill in all fields!", text_color="#E74C3C")
            return

        if not self.selected_image_path or not os.path.exists(self.selected_image_path):
            self.status_label.configure(text="Please choose an image for this item!", text_color="#E74C3C")
            messagebox.showwarning("Image Required", "Every menu item must have an uploaded image!")
            return

        try:
            price = float(price_str)
        except ValueError:
            self.status_label.configure(text="Price must be a valid number!", text_color="#E74C3C")
            return

        inserted_id = insert_menu_item(name, price, category)
        if not inserted_id:
            self.status_label.configure(text="Database error: Could not insert item!", text_color="#E74C3C")
            return

        dest_filename = f"{inserted_id}_{name.lower().replace(' ', '_')}_{os.path.basename(self.selected_image_path)}"
        dest_path = os.path.join(IMAGE_ASSETS_DIR, dest_filename)
        shutil.copy(self.selected_image_path, dest_path)

        new_item = {
            "id": inserted_id,
            "name": name,
            "category": category,
            "price": price,
            "image": dest_path
        }
        self.app.shared_menu_items.append(new_item)

        self._refresh_items_list()
        self._clear_form()
        self.status_label.configure(text=f"Saved '{name}' to Database!", text_color="#2ECC71")

    def _update_item(self):
        if not self.selected_item:
            self.status_label.configure(text="Select an item from the list first!", text_color="#E74C3C")
            return

        name = self.name_entry.get().strip()
        price_str = self.price_entry.get().strip()
        category = self.cat_menu.get()

        if not name or not price_str:
            self.status_label.configure(text="Fields cannot be empty!", text_color="#E74C3C")
            return

        #REQUIRE IMAGE
        has_new_image = self.selected_image_path and os.path.exists(self.selected_image_path)
        has_existing_image = self.selected_item.get("image") and os.path.exists(self.selected_item.get("image"))

        if not has_new_image and not has_existing_image:
            self.status_label.configure(text="An image is required to update this item!", text_color="#E74C3C")
            messagebox.showwarning("Image Required", "You must select or provide an image to update this item!")
            return

        try:
            price = float(price_str)
        except ValueError:
            self.status_label.configure(text="Invalid price value!", text_color="#E74C3C")
            return

        item_id = self.selected_item.get("id")
        if item_id:
            update_menu_item_db(item_id, name, price, category)

        if has_new_image and self.selected_image_path != self.selected_item.get("image"):
            dest_filename = f"{item_id}_{name.lower().replace(' ', '_')}_{os.path.basename(self.selected_image_path)}"
            dest_path = os.path.join(IMAGE_ASSETS_DIR, dest_filename)
            shutil.copy(self.selected_image_path, dest_path)
            self.selected_item["image"] = dest_path

        self.selected_item["name"] = name
        self.selected_item["category"] = category
        self.selected_item["price"] = price

        self._refresh_items_list()
        self.status_label.configure(text=f"Updated '{name}' in Database!", text_color="#FFA500")

    def _delete_item(self):
        if not self.selected_item:
            self.status_label.configure(text="Select an item to delete!", text_color="#E74C3C")
            return

        item_id = self.selected_item.get("id")
        deleted_name = self.selected_item["name"]

        if item_id:
            delete_menu_item_db(item_id)

        self.app.shared_menu_items.remove(self.selected_item)
        self._refresh_items_list()
        self._clear_form()
        self.status_label.configure(text=f"Deleted '{deleted_name}' from Database!", text_color="#E74C3C")

    def _clear_form(self):
        self.selected_item = None
        self.selected_image_path = None
        self.name_entry.delete(0, "end")
        self.price_entry.delete(0, "end")
        self.price_entry.insert(0, "29.00")
        self.cat_menu.set(self.categories[0])
        self.img_path_label.configure(text="No image selected", text_color="#888888")
        self.preview_box.configure(image=None, text="[No Preview]")
        self.status_label.configure(text="")