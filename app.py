"""Command-line interface for the Inventory & Order Management System."""
from decimal import Decimal, InvalidOperation

from mysql.connector import Error

from inventory.services import InventoryService, OrderService

inventory = InventoryService()
orders = OrderService()


def ask_int(prompt, minimum=0):
    while True:
        try:
            value = int(input(prompt).strip())
            if value < minimum:
                print(f"Enter a number greater than or equal to {minimum}.")
                continue
            return value
        except ValueError:
            print("Please enter a whole number.")


def ask_price(prompt):
    while True:
        try:
            value = Decimal(input(prompt).strip())
            if value < 0:
                print("Price cannot be negative.")
                continue
            return value
        except (InvalidOperation, ValueError):
            print("Enter a valid price, e.g. 499.99.")


def show_products(rows):
    if not rows:
        print("No products found.")
        return
    print("\n{:<5} {:<24} {:>10} {:>8} {:>10}".format("ID", "PRODUCT", "PRICE", "STOCK", "REORDER"))
    print("-" * 62)
    for p in rows:
        print("{:<5} {:<24} {:>10.2f} {:>8} {:>10}".format(
            p["product_id"], p["name"][:24], p["price"], p["stock_quantity"], p["reorder_level"]
        ))


def add_product():
    name = input("Product name: ")
    description = input("Description: ")
    price = ask_price("Unit price: ")
    quantity = ask_int("Opening stock quantity: ")
    reorder = ask_int("Low-stock alert level [5]: ") if input("Set custom alert level? (y/N): ").lower() == "y" else 5
    product_id = inventory.add_product(name, description, price, quantity, reorder)
    print(f"Product added successfully. Product ID: {product_id}")


def place_order():
    customer = input("Customer name: ")
    email = input("Customer email (optional): ")
    items = {}
    while True:
        product_id = ask_int("Product ID (0 to finish): ")
        if product_id == 0:
            break
        quantity = ask_int("Quantity: ", 1)
        items[product_id] = items.get(product_id, 0) + quantity
    order_id, total = orders.place_order(customer, email, items)
    print(f"Order #{order_id} placed successfully. Total: {total:.2f}")


def main():
    print("=" * 54)
    print("       INVENTORY & ORDER MANAGEMENT SYSTEM")
    print("=" * 54)
    while True:
        print("""
1. Add product
2. List all products
3. Search products
4. Update product details
5. Place customer order
6. View recent orders
7. View order details
8. Low-stock alerts
0. Exit
""")
        choice = input("Choose an option: ").strip()
        try:
            if choice == "1":
                add_product()
            elif choice == "2":
                show_products(inventory.list_products())
            elif choice == "3":
                show_products(inventory.list_products(input("Search text: ")))
            elif choice == "4":
                product_id = ask_int("Product ID: ", 1)
                name = input("New product name: ")
                description = input("New description: ")
                price = ask_price("New price: ")
                reorder = ask_int("New reorder level: ")
                if inventory.update_product(product_id, name, description, price, reorder):
                    print("Product updated.")
                else:
                    print("No product found with that ID.")
            elif choice == "5":
                place_order()
            elif choice == "6":
                rows = orders.list_orders()
                if not rows:
                    print("No orders found.")
                for o in rows:
                    print(f'#{o["order_id"]} | {o["customer_name"]} | {o["order_date"]} | '
                          f'{o["total_amount"]:.2f} | {o["status"]}')
            elif choice == "7":
                order_id = ask_int("Order ID: ", 1)
                rows = orders.order_details(order_id)
                if not rows:
                    print("No details found for that order ID.")
                else:
                    first = rows[0]
                    print(f'Order #{first["order_id"]} - {first["customer_name"]} '
                          f'({first["status"]}) Total: {first["total_amount"]:.2f}')
                    for row in rows:
                        print(f'  {row["product_name"]} x {row["quantity"]} @ '
                              f'{row["unit_price"]:.2f} = {row["line_total"]:.2f}')
            elif choice == "8":
                rows = inventory.low_stock()
                if not rows:
                    print("No low-stock products.")
                else:
                    print("\nLOW-STOCK ALERTS")
                    for p in rows:
                        print(f'#{p["product_id"]} {p["name"]}: stock {p["stock_quantity"]}, '
                              f'reorder level {p["reorder_level"]}')
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option. Choose from the menu.")
        except ValueError as exc:
            print(f"Could not complete request: {exc}")
        except Error as exc:
            print(f"MySQL error: {exc}")
            print("Check that MySQL is running, schema.sql was executed, and .env credentials are correct.")
        except Exception as exc:
            print(f"Unexpected error: {exc}")


if __name__ == "__main__":
    main()
