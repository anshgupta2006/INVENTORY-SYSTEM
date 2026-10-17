"""Business logic for product inventory and order processing."""
from decimal import Decimal, InvalidOperation

from mysql.connector import Error

from inventory.database import Database


class InventoryService:
    def add_product(self, name, description, price, quantity, reorder_level):
        name = name.strip()
        if not name:
            raise ValueError("Product name cannot be empty.")
        try:
            price = Decimal(str(price))
        except InvalidOperation:
            raise ValueError("Price must be a valid number.") from None
        if price < 0 or quantity < 0 or reorder_level < 0:
            raise ValueError("Price, quantity, and reorder level cannot be negative.")

        with Database.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO products (name, description, price, stock_quantity, reorder_level)
                   VALUES (%s, %s, %s, %s, %s)""",
                (name, description.strip(), price, int(quantity), int(reorder_level)),
            )
            conn.commit()
            product_id = cursor.lastrowid
            cursor.close()
            return product_id

    def list_products(self, search=""):
        with Database.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            if search.strip():
                cursor.execute(
                    """SELECT product_id, name, description, price, stock_quantity, reorder_level
                       FROM products WHERE name LIKE %s OR description LIKE %s
                       ORDER BY name""",
                    (f"%{search.strip()}%", f"%{search.strip()}%"),
                )
            else:
                cursor.execute(
                    """SELECT product_id, name, description, price, stock_quantity, reorder_level
                       FROM products ORDER BY name"""
                )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def update_product(self, product_id, name, description, price, reorder_level):
        if not name.strip():
            raise ValueError("Product name cannot be empty.")
        price = Decimal(str(price))
        if price < 0 or int(reorder_level) < 0:
            raise ValueError("Price and reorder level cannot be negative.")
        with Database.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """UPDATE products SET name=%s, description=%s, price=%s, reorder_level=%s
                   WHERE product_id=%s""",
                (name.strip(), description.strip(), price, int(reorder_level), int(product_id)),
            )
            conn.commit()
            changed = cursor.rowcount
            cursor.close()
            return changed > 0

    def low_stock(self):
        with Database.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT product_id, name, stock_quantity, reorder_level
                   FROM products WHERE stock_quantity <= reorder_level
                   ORDER BY stock_quantity, name"""
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows


class OrderService:
    def place_order(self, customer_name, customer_email, items):
        """Create order and deduct stock atomically. items is {product_id: quantity}."""
        if not customer_name.strip():
            raise ValueError("Customer name cannot be empty.")
        cleaned = {}
        for product_id, quantity in items.items():
            product_id, quantity = int(product_id), int(quantity)
            if quantity <= 0:
                raise ValueError("Order quantities must be greater than zero.")
            cleaned[product_id] = cleaned.get(product_id, 0) + quantity
        if not cleaned:
            raise ValueError("Add at least one product to the order.")

        conn = Database.connect()
        cursor = conn.cursor(dictionary=True)
        try:
            conn.start_transaction()
            locked_products = {}
            # Lock products in sorted order to reduce deadlock risk.
            for product_id in sorted(cleaned):
                cursor.execute(
                    """SELECT product_id, name, price, stock_quantity
                       FROM products WHERE product_id=%s FOR UPDATE""",
                    (product_id,),
                )
                product = cursor.fetchone()
                if not product:
                    raise ValueError(f"Product ID {product_id} does not exist.")
                if product["stock_quantity"] < cleaned[product_id]:
                    raise ValueError(
                        f"Not enough stock for {product['name']}. "
                        f"Available: {product['stock_quantity']}."
                    )
                locked_products[product_id] = product

            total = Decimal("0.00")
            for product_id, quantity in cleaned.items():
                total += Decimal(locked_products[product_id]["price"]) * quantity

            cursor.execute(
                "INSERT INTO orders (customer_name, customer_email, total_amount) VALUES (%s, %s, %s)",
                (customer_name.strip(), customer_email.strip(), total),
            )
            order_id = cursor.lastrowid
            for product_id, quantity in cleaned.items():
                product = locked_products[product_id]
                unit_price = Decimal(product["price"])
                line_total = unit_price * quantity
                cursor.execute(
                    """INSERT INTO order_items (order_id, product_id, quantity, unit_price, line_total)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (order_id, product_id, quantity, unit_price, line_total),
                )
                cursor.execute(
                    "UPDATE products SET stock_quantity = stock_quantity - %s WHERE product_id=%s",
                    (quantity, product_id),
                )
            conn.commit()
            return order_id, total
        except Exception:
            conn.rollback()
            raise
        finally:
            cursor.close()
            conn.close()

    def list_orders(self, limit=50):
        with Database.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT order_id, customer_name, customer_email, order_date, total_amount, status
                   FROM orders ORDER BY order_date DESC LIMIT %s""",
                (int(limit),),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows

    def order_details(self, order_id):
        with Database.connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(
                """SELECT o.order_id, o.customer_name, o.customer_email, o.order_date,
                          o.total_amount, o.status, oi.product_id, p.name AS product_name,
                          oi.quantity, oi.unit_price, oi.line_total
                   FROM orders o JOIN order_items oi ON o.order_id=oi.order_id
                   JOIN products p ON p.product_id=oi.product_id
                   WHERE o.order_id=%s ORDER BY oi.order_item_id""",
                (int(order_id),),
            )
            rows = cursor.fetchall()
            cursor.close()
            return rows
