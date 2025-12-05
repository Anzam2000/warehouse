import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import os
import sys


class WarehouseApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Система управления складом")
        self.root.geometry("800x500")

        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))

        db_path = os.path.join(application_path, 'warehouse.db')

        self.conn = sqlite3.connect(db_path)

        self.create_widgets()
        self.load_products()

    def create_widgets(self):
        # Основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)

        title_label = ttk.Label(main_frame, text="Система управления складом",
                                font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))

        form_frame = ttk.LabelFrame(main_frame, text="Добавить/Обновить товар", padding="10")
        form_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))

        ttk.Label(form_frame, text="Название:*").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_entry = ttk.Entry(form_frame, width=20)
        self.name_entry.grid(row=0, column=1, pady=5, padx=(5, 0))

        ttk.Label(form_frame, text="Количество:*").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.quantity_entry = ttk.Entry(form_frame, width=20)
        self.quantity_entry.insert(0, "0")
        self.quantity_entry.grid(row=1, column=1, pady=5, padx=(5, 0))

        ttk.Label(form_frame, text="Цена:*").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.price_entry = ttk.Entry(form_frame, width=20)
        self.price_entry.insert(0, "0.0")
        self.price_entry.grid(row=2, column=1, pady=5, padx=(5, 0))

        button_frame = ttk.Frame(form_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)

        ttk.Button(button_frame, text="Добавить",
                   command=self.add_product).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Обновить",
                   command=self.update_product).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить",
                   command=self.clear_form).pack(side=tk.LEFT, padx=5)

        operations_frame = ttk.LabelFrame(main_frame, text="Операции", padding="10")
        operations_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=(0, 10), pady=10)

        ttk.Button(operations_frame, text="Приход",
                   command=lambda: self.show_transaction_dialog("incoming")).pack(side=tk.LEFT, padx=5)
        ttk.Button(operations_frame, text="Расход",
                   command=lambda: self.show_transaction_dialog("outgoing")).pack(side=tk.LEFT, padx=5)
        ttk.Button(operations_frame, text="Удалить",
                   command=self.delete_product).pack(side=tk.LEFT, padx=5)

        table_frame = ttk.LabelFrame(main_frame, text="Товары на складе", padding="10")
        table_frame.grid(row=1, column=1, rowspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("ID", "Название", "Количество", "Цена")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)

        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120)

        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))

        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        search_frame = ttk.Frame(main_frame)
        search_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.bind('<KeyRelease>', self.search_products)

        ttk.Button(search_frame, text="Обновить",
                   command=self.load_products).pack(side=tk.LEFT, padx=5)

    def add_product(self):
        try:
            name = self.name_entry.get().strip()
            quantity_str = self.quantity_entry.get().strip()
            price_str = self.price_entry.get().strip()

            if not name:
                messagebox.showerror("Ошибка", "Введите название товара")
                return

            if not quantity_str:
                messagebox.showerror("Ошибка", "Введите количество")
                return

            if not price_str:
                messagebox.showerror("Ошибка", "Введите цену")
                return

            quantity = int(quantity_str)
            price = float(price_str)

            if quantity < 0:
                messagebox.showerror("Ошибка", "Количество не может быть отрицательным")
                return

            if price < 0:
                messagebox.showerror("Ошибка", "Цена не может быть отрицательной")
                return

            cursor = self.conn.cursor()
            cursor.execute('''
                INSERT INTO products (name, quantity, price)
                VALUES (?, ?, ?)
            ''', (name, quantity, price))

            product_id = cursor.lastrowid
            if product_id:
                cursor.execute('''
                    INSERT INTO transactions (product_id, type, quantity, notes)
                    VALUES (?, 'initial', ?, 'Начальный остаток')
                ''', (product_id, quantity))

            self.conn.commit()
            self.load_products()
            self.clear_form()
            messagebox.showinfo("Успех", "Товар успешно добавлен")

        except ValueError as e:
            messagebox.showerror("Ошибка", "Проверьте правильность данных:\n- Количество - целое число\n- Цена - число")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении: {str(e)}")

    def update_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите товар для обновления")
            return

        try:
            product_id = self.tree.item(selected[0])['values'][0]
            name = self.name_entry.get().strip()
            quantity_str = self.quantity_entry.get().strip()
            price_str = self.price_entry.get().strip()

            if not name:
                messagebox.showerror("Ошибка", "Введите название товара")
                return

            if not quantity_str:
                messagebox.showerror("Ошибка", "Введите количество")
                return

            if not price_str:
                messagebox.showerror("Ошибка", "Введите цену")
                return

            quantity = int(quantity_str)
            price = float(price_str)

            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE products 
                SET name=?, quantity=?, price=?
                WHERE id=?
            ''', (name, quantity, price, product_id))

            self.conn.commit()
            self.load_products()
            messagebox.showinfo("Успех", "Товар успешно обновлен")

        except ValueError:
            messagebox.showerror("Ошибка", "Проверьте правильность данных")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обновлении: {str(e)}")

    def delete_product(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите товар для удаления")
            return

        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить этот товар?"):
            product_id = self.tree.item(selected[0])['values'][0]

            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM transactions WHERE product_id=?', (product_id,))
            cursor.execute('DELETE FROM products WHERE id=?', (product_id,))

            self.conn.commit()
            self.load_products()
            self.clear_form()
            messagebox.showinfo("Успех", "Товар успешно удален")

    def show_transaction_dialog(self, transaction_type):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Предупреждение", "Выберите товар для операции")
            return

        product_id = self.tree.item(selected[0])['values'][0]
        product_name = self.tree.item(selected[0])['values'][1]
        current_qty = self.tree.item(selected[0])['values'][2]

        dialog = tk.Toplevel(self.root)
        dialog.title("Приход товара" if transaction_type == "incoming" else "Расход товара")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text=f"Товар: {product_name}").pack(pady=10)
        ttk.Label(dialog, text=f"Текущее количество: {current_qty}").pack(pady=5)

        ttk.Label(dialog, text="Количество:").pack(pady=5)
        qty_var = tk.StringVar()
        qty_entry = ttk.Entry(dialog, textvariable=qty_var, width=10)
        qty_entry.pack(pady=5)

        def process_transaction():
            try:
                quantity_str = qty_var.get().strip()
                if not quantity_str:
                    messagebox.showerror("Ошибка", "Введите количество")
                    return

                quantity = int(quantity_str)

                if quantity <= 0:
                    messagebox.showerror("Ошибка", "Количество должно быть положительным")
                    return

                cursor = self.conn.cursor()

                if transaction_type == "incoming":
                    cursor.execute('''
                        UPDATE products SET quantity = quantity + ? WHERE id = ?
                    ''', (quantity, product_id))
                    notes = "Приход товара"
                else:
                    cursor.execute('SELECT quantity FROM products WHERE id = ?', (product_id,))
                    available_qty = cursor.fetchone()[0]

                    if available_qty < quantity:
                        messagebox.showerror("Ошибка", "Недостаточно товара на складе")
                        return

                    cursor.execute('''
                        UPDATE products SET quantity = quantity - ? WHERE id = ?
                    ''', (quantity, product_id))
                    notes = "Расход товара"

                cursor.execute('''
                    INSERT INTO transactions (product_id, type, quantity, notes)
                    VALUES (?, ?, ?, ?)
                ''', (product_id, transaction_type, quantity, notes))

                self.conn.commit()
                self.load_products()
                dialog.destroy()
                messagebox.showinfo("Успех", "Операция выполнена успешно")

            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректное количество")

        ttk.Button(dialog, text="Выполнить",
                   command=process_transaction).pack(pady=10)

    def load_products(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT id, name, quantity, price 
            FROM products 
            ORDER BY id
        ''')

        for row in cursor.fetchall():
            self.tree.insert('', 'end', values=row)

    def search_products(self, event=None):
        search_term = self.search_entry.get().lower()

        for item in self.tree.get_children():
            values = [str(v).lower() for v in self.tree.item(item)['values']]
            if any(search_term in value for value in values):
                self.tree.item(item, tags=())
            else:
                self.tree.detach(item)

    def on_select(self, event):
        selected = self.tree.selection()
        if selected:
            values = self.tree.item(selected[0])['values']
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, values[1])
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.insert(0, values[2])
            self.price_entry.delete(0, tk.END)
            self.price_entry.insert(0, values[3])

    def clear_form(self):
        self.name_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.quantity_entry.insert(0, "0")
        self.price_entry.delete(0, tk.END)
        self.price_entry.insert(0, "0.0")
        self.tree.selection_remove(self.tree.selection())

    def __del__(self):
        if hasattr(self, 'conn'):
            self.conn.close()


def main():
    root = tk.Tk()
    app = WarehouseApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
