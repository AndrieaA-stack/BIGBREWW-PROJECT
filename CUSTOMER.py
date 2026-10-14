import os
import subprocess
import tempfile
from datetime import datetime
import customtkinter as ctk
from PIL import Image
from db_helper import insert_order

SIZE_MODIFIERS = {
    "Large (22oz) [₱0.00]": 0.0,
    "Medium (16oz) [-₱5.00]": -5.0,
    "Jumbo (1L) [+₱20.00]": 20.0,
}

ADD_ONS = {
    "Extra Pearl": 10.0,
    "Cream Cheese": 10.0,
    "Nata de Coco": 10.0,
    "Crushed Oreos": 10.0,
}


class CustomerPortal(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.current_order = []
        self.selected_item_name = None
        self.selected_item_category = None
        self.selected_item_price = 0.0
        self.item_images_cache = {}

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        self._build_left_panel()
        self._build_right_panel()

    def _get_dynamic_categories(self):
        cats = ["Milk Tea", "Iced Coffee", "Fruit Tea"]
        for item in self.app.shared_menu_items:
            cat = item.get("category")
            if cat and cat not in cats:
                cats.append(cat)
        return cats

    def _build_left_panel(self):
        left_frame = ctk.CTkFrame(self, corner_radius=10)
        left_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        left_frame.grid_rowconfigure(2, weight=1)
        left_frame.grid_columnconfigure(0, weight=1)

        #Header bar
        header_box = ctk.CTkFrame(left_frame, fg_color="transparent")
        header_box.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="ew")

        ctk.CTkLabel(header_box, image=self.app.logo_ctk_image, text="").pack(side="left", padx=(0, 10))
        ctk.CTkLabel(header_box, text="BIGBREW POS", font=ctk.CTkFont(size=24, weight="bold"), text_color="#FFA500").pack(side="left")

        ctk.CTkButton(header_box, text="Switch User", width=80, fg_color="#333", command=self.app.show_auth_selection).pack(side="right")

        #Category Tabs
        self.tabview = ctk.CTkTabview(left_frame, command=self._on_tab_change)
        self.tabview.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        for category in self._get_dynamic_categories():
            self.tabview.add(category)

        #Scrollable Menu Items Container
        self.menu_scroll = ctk.CTkScrollableFrame(left_frame, label_text="Menu Items")
        self.menu_scroll.grid(row=2, column=0, padx=15, pady=5, sticky="nsew")
        self.menu_scroll.grid_columnconfigure((0, 1, 2), weight=1)

        #Customization Box
        custom_frame = ctk.CTkFrame(left_frame, fg_color="#1e1e1e", corner_radius=8)
        custom_frame.grid(row=3, column=0, padx=15, pady=15, sticky="ew")
        custom_frame.grid_columnconfigure((0, 1), weight=1)

        #Size Dropdown
        ctk.CTkLabel(custom_frame, text="Size Pricing:", font=ctk.CTkFont(weight="bold")).grid(row=0, column=0, padx=10, pady=(5, 0), sticky="w")
        self.size_var = ctk.StringVar(value="Large (22oz) [₱0.00]")
        self.size_dropdown = ctk.CTkOptionMenu(
            custom_frame,
            values=list(SIZE_MODIFIERS.keys()),
            variable=self.size_var,
            command=self._update_add_button_label
        )
        self.size_dropdown.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")

        #Add ons CheckboxeS
        ctk.CTkLabel(custom_frame, text="Add-ons (+₱10.00 each):", font=ctk.CTkFont(weight="bold")).grid(row=0, column=1, padx=10, pady=(5, 0), sticky="w")
        self.addon_vars = {}
        addon_subframe = ctk.CTkFrame(custom_frame, fg_color="transparent")
        addon_subframe.grid(row=1, column=1, padx=10, pady=(0, 10), sticky="w")

        for idx, (addon, price) in enumerate(ADD_ONS.items()):
            var = ctk.BooleanVar(value=False)
            self.addon_vars[addon] = var
            chk = ctk.CTkCheckBox(addon_subframe, text=f"{addon} (+₱{price:.0f})", variable=var, font=ctk.CTkFont(size=11))
            chk.grid(row=idx // 2, column=idx % 2, padx=5, pady=2, sticky="w")

        # Add to cart button
        self.add_btn = ctk.CTkButton(
            custom_frame,
            text="Select an Item First",
            state="disabled",
            fg_color="#FFA500",
            text_color="black",
            hover_color="#CC8400",
            font=ctk.CTkFont(weight="bold"),
            command=self._add_to_cart
        )
        self.add_btn.grid(row=2, column=0, columnspan=2, padx=10, pady=10, sticky="ew")

        self.RefreshMenu()

    def _build_right_panel(self):
        right_frame = ctk.CTkFrame(self, corner_radius=10)
        right_frame.grid(row=0, column=1, padx=(0, 15), pady=15, sticky="nsew")
        right_frame.grid_rowconfigure(1, weight=1)
        right_frame.grid_columnconfigure(0, weight=1)

        self.cart_title = ctk.CTkLabel(
            right_frame,
            text=f"Order Cart ({self.app.customer_name})",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.cart_title.grid(row=0, column=0, padx=15, pady=(15, 5), sticky="w")

        self.cart_scroll = ctk.CTkScrollableFrame(right_frame, label_text="Items")
        self.cart_scroll.grid(row=1, column=0, padx=15, pady=5, sticky="nsew")
        self.cart_scroll.grid_columnconfigure(0, weight=1)

        summary_frame = ctk.CTkFrame(right_frame, fg_color="#1e1e1e", corner_radius=8)
        summary_frame.grid(row=2, column=0, padx=15, pady=15, sticky="ew")

        self.total_label = ctk.CTkLabel(
            summary_frame,
            text="Total: ₱0.00",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#2ECC71"
        )
        self.total_label.pack(anchor="w", padx=15, pady=(10, 5))

        payment_box = ctk.CTkFrame(summary_frame, fg_color="transparent")
        payment_box.pack(fill="x", padx=15, pady=5)

        ctk.CTkLabel(payment_box, text="Cash Tendered: ₱").pack(side="left")
        self.cash_entry = ctk.CTkEntry(payment_box, width=100, placeholder_text="0.00")
        self.cash_entry.pack(side="left", padx=5)
        self.cash_entry.bind("<KeyRelease>", self._calculate_change)

        self.change_label = ctk.CTkLabel(summary_frame, text="Change: ₱0.00", font=ctk.CTkFont(size=14))
        self.change_label.pack(anchor="w", padx=15, pady=2)

        btn_box = ctk.CTkFrame(summary_frame, fg_color="transparent")
        btn_box.pack(fill="x", padx=15, pady=10)

        ctk.CTkButton(
            btn_box,
            text="Clear",
            fg_color="#E74C3C",
            hover_color="#C0392B",
            width=80,
            command=self._clear_cart
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            btn_box,
            text="Checkout & Pay",
            fg_color="#2ECC71",
            hover_color="#27AE60",
            font=ctk.CTkFont(weight="bold"),
            command=self._checkout
        ).pack(side="right", fill="x", expand=True)

    def _on_tab_change(self):
        category = self.tabview.get()
        self._populate_menu(category)

    def RefreshMenu(self):
        category = self.tabview.get() if hasattr(self, 'tabview') and self.tabview.get() else "Milk Tea"
        self._populate_menu(category)

    def _get_item_ctk_image(self, item):
        img_path = item.get("image")
        if img_path and os.path.exists(img_path):
            if img_path not in self.item_images_cache:
                try:
                    pil_img = Image.open(img_path)
                    self.item_images_cache[img_path] = ctk.CTkImage(
                        light_image=pil_img, dark_image=pil_img, size=(45, 45)
                    )
                except Exception:
                    return self.app.item_ctk_image
            return self.item_images_cache[img_path]
        return self.app.item_ctk_image

    def _populate_menu(self, category):
        for widget in self.menu_scroll.winfo_children():
            widget.destroy()

        category_items = [it for it in self.app.shared_menu_items if it.get("category") == category]

        row, col = 0, 0
        for item in category_items:
            item_name = item["name"]
            base_price = float(item["price"])
            img = self._get_item_ctk_image(item)

            btn = ctk.CTkButton(
                self.menu_scroll,
                text=f"{item_name}\n₱{base_price:.2f}",
                image=img,
                compound="top",
                height=90,
                fg_color="#2d2d2d",
                hover_color="#3d3d3d",
                command=lambda name=item_name, cat=category, p=base_price: self._select_item(name, cat, p)
            )
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            col += 1
            if col > 2:
                col = 0
                row += 1

    def _select_item(self, item_name, category, price):
        self.selected_item_name = item_name
        self.selected_item_category = category
        self.selected_item_price = price
        self.add_btn.configure(state="normal")
        self._update_add_button_label()

    def _update_add_button_label(self, choice=None):
        if not self.selected_item_name:
            return
        base_price = self.selected_item_price
        selected_size_key = self.size_var.get()
        size_adj = SIZE_MODIFIERS[selected_size_key]
        item_price = base_price + size_adj
        self.add_btn.configure(text=f"Add '{self.selected_item_name}' to Order (₱{item_price:.2f})")

    def _add_to_cart(self):
        if not self.selected_item_name:
            return

        base_price = self.selected_item_price
        selected_size_key = self.size_var.get()
        size_adj = SIZE_MODIFIERS[selected_size_key]

        selected_addons = [addon for addon, var in self.addon_vars.items() if var.get()]
        addons_total = len(selected_addons) * 10.0

        item_total = base_price + size_adj + addons_total
        clean_size_name = selected_size_key.split(" [")[0]

        cart_item = {
            "name": self.selected_item_name,
            "category": self.selected_item_category,
            "size": clean_size_name,
            "addons": selected_addons,
            "price": item_total
        }

        self.current_order.append(cart_item)
        self._render_cart()
        self._reset_customizer()

    def _reset_customizer(self):
        self.selected_item_name = None
        self.selected_item_category = None
        self.selected_item_price = 0.0
        self.add_btn.configure(state="disabled", text="Select an Item First")
        self.size_var.set("Large (22oz) [₱0.00]")
        for var in self.addon_vars.values():
            var.set(False)

    def _render_cart(self):
        for widget in self.cart_scroll.winfo_children():
            widget.destroy()

        for idx, item in enumerate(self.current_order):
            frame = ctk.CTkFrame(self.cart_scroll, fg_color="#2b2b2b")
            frame.pack(fill="x", pady=2, padx=2)

            text_details = f"{item['name']} ({item['size']})"
            if item['addons']:
                text_details += f"\n + {', '.join(item['addons'])}"

            lbl = ctk.CTkLabel(frame, text=text_details, justify="left", font=ctk.CTkFont(size=12))
            lbl.pack(side="left", padx=8, pady=5)

            price_lbl = ctk.CTkLabel(frame, text=f"₱{item['price']:.2f}", font=ctk.CTkFont(weight="bold"))
            price_lbl.pack(side="right", padx=8)

            del_btn = ctk.CTkButton(
                frame,
                text="✕",
                width=24,
                height=24,
                fg_color="#E74C3C",
                hover_color="#C0392B",
                command=lambda i=idx: self._remove_from_cart(i)
            )
            del_btn.pack(side="right", padx=2)

        self._update_totals()

    def _remove_from_cart(self, index):
        self.current_order.pop(index)
        self._render_cart()

    def _clear_cart(self):
        self.current_order = []
        self.cash_entry.delete(0, "end")
        self._render_cart()

    def _get_cart_total(self):
        return sum(item["price"] for item in self.current_order)

    def _update_totals(self):
        total = self._get_cart_total()
        self.total_label.configure(text=f"Total: ₱{total:.2f}")
        self._calculate_change()

    def _calculate_change(self, event=None):
        total = self._get_cart_total()
        try:
            cash = float(self.cash_entry.get())
            change = cash - total
            if change >= 0:
                self.change_label.configure(text=f"Change: ₱{change:.2f}", text_color="#2ECC71")
            else:
                self.change_label.configure(text="Change: Insufficient Cash", text_color="#E74C3C")
        except ValueError:
            self.change_label.configure(text="Change: ₱0.00", text_color="white")

    def _checkout(self):
        total = self._get_cart_total()
        if total == 0:
            return

        try:
            cash = float(self.cash_entry.get())
        except ValueError:
            cash = 0.0

        if cash < total:
            err_win = ctk.CTkToplevel(self)
            err_win.title("Error")
            err_win.geometry("300x120")
            err_win.attributes('-topmost', True)
            ctk.CTkLabel(err_win, text="Insufficient Cash Tendered!", font=ctk.CTkFont(weight="bold")).pack(pady=20)
            ctk.CTkButton(err_win, text="OK", command=err_win.destroy).pack()
            return

        change = cash - total
        order_snapshot = list(self.current_order)

        order_id = insert_order(
            customer_name=self.app.customer_name,
            total_amount=total,
            cash_tendered=cash,
            change_due=change,
            order_items=order_snapshot
        )

        self._show_clean_receipt_modal(order_id or "OFFLINE", total, cash, change, order_snapshot)
        self._clear_cart()

    def _show_clean_receipt_modal(self, order_id, total, cash, change, items):
        """Displays a centered receipt preview with silent, zero-prompt auto-printing."""
        receipt_win = ctk.CTkToplevel(self)
        receipt_win.title("Transaction Receipt")
        receipt_win.resizable(False, False)
        receipt_win.attributes('-topmost', True)

        #RECEIPT
        win_w, win_h = 380, 600
        screen_w = receipt_win.winfo_screenwidth()
        screen_h = receipt_win.winfo_screenheight()
        pos_x = (screen_w - win_w) // 2
        pos_y = (screen_h - win_h) // 2
        receipt_win.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")

        now_str = datetime.now().strftime("%Y-%m-%d %I:%M %p")
        receipt_num = f"INV-{order_id:05d}" if isinstance(order_id, int) else str(order_id)

        receipt_lines = [
            "========================================",
            "             BIGBREW POS               ",
            "         Order & Billing Receipt        ",
            "========================================",
            f"Date / Time : {now_str}",
            f"Receipt No. : {receipt_num}",
            f"Customer    : {self.app.customer_name}",
            f"Cashier     : Admin / Cashier",
            "----------------------------------------",
            f"{'ITEM / DESC':<26}{'PRICE':>14}",
            "----------------------------------------",
        ]

        for itm in items:
            line_title = f"{itm['name']} ({itm['size']})"
            receipt_lines.append(f"{line_title:<26} PHP {itm['price']:>7.2f}")
            if itm.get("addons"):
                for ad in itm["addons"]:
                    receipt_lines.append(f"  + {ad:<22} PHP   10.00")

        receipt_lines.extend([
            "----------------------------------------",
            f"{'TOTAL AMOUNT:':<26} PHP {total:>7.2f}",
            f"{'CASH TENDERED:':<26} PHP {cash:>7.2f}",
            f"{'CHANGE:':<26} PHP {change:>7.2f}",
            "========================================",
            "       Thank you for your order!        ",
            "========================================",
        ])

        full_receipt_text = "\n".join(receipt_lines)

        container = ctk.CTkFrame(receipt_win, corner_radius=10)
        container.pack(fill="both", expand=True, padx=12, pady=12)

        text_box = ctk.CTkTextbox(
            container,
            font=("Consolas", 12),
            wrap="none",
            activate_scrollbars=True
        )
        text_box.pack(fill="both", expand=True, padx=8, pady=(8, 12))
        text_box.insert("1.0", full_receipt_text)
        text_box.configure(state="disabled")

        def handle_print_direct():
            temp_dir = tempfile.gettempdir()
            file_path = os.path.join(temp_dir, f"receipt_{receipt_num}.txt")

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(full_receipt_text)

            ps_cmd = f'Get-Content -Path "{file_path}" -Raw | Out-Printer'
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                creationflags=subprocess.CREATE_NO_WINDOW
            )

        btn_row = ctk.CTkFrame(container, fg_color="transparent")
        btn_row.pack(fill="x", padx=8, pady=(0, 6))

        print_btn = ctk.CTkButton(
            btn_row,
            text="🖨️ Print Receipt",
            fg_color="#2ECC71",
            hover_color="#27AE60",
            text_color="black",
            font=ctk.CTkFont(weight="bold"),
            command=handle_print_direct
        )
        print_btn.pack(side="left", fill="x", expand=True, padx=(0, 4))

        close_btn = ctk.CTkButton(
            btn_row,
            text="Done",
            fg_color="#333333",
            hover_color="#444444",
            command=receipt_win.destroy
        )
        close_btn.pack(side="right", fill="x", expand=True, padx=(4, 0))