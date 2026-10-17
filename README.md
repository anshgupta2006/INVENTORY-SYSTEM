# Inventory & Order Management System

A Python + MySQL command-line project for managing products, customer orders, and stock availability.

## Features
- Add, list, and search products
- Update product details and prices
- Process customer orders with stock validation
- Automatically reduce stock after a successful order
- Low-stock alerts
- View recent orders and order items
- MySQL transactions with rollback on failure
- Object-oriented design (`Database`, `Product`, `InventoryService`, `OrderService`)

## Tech stack
Python 3.10+, MySQL 8+, `mysql-connector-python`, OOP, SQL, Git/GitHub.

## 1. Set up MySQL
Create a database and tables by running the SQL file:

```bash
mysql -u root -p < database/schema.sql
```

Or open `database/schema.sql` in MySQL Workbench and execute it.

## 2. Set up the Python environment

Windows PowerShell:
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Configure database credentials
Copy `.env.example` to `.env` and fill in your local MySQL settings.

Windows:
```powershell
copy .env.example .env
```

macOS/Linux:
```bash
cp .env.example .env
```

Edit `.env`:
```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=inventory_management
```

Never commit `.env` or real passwords to GitHub. The application reads these variables and uses safe defaults for host, port, user, and database name.

## 4. Run the app
```bash
python app.py
```

Choose an option from the menu. Add a product first, then use its product ID to place an order.

## Example workflow
1. Add a product such as `Wireless Mouse`, price `599.00`, quantity `20`, reorder level `5`.
2. Search for `Mouse` to confirm the product is available.
3. Place an order using the product ID and quantity.
4. View orders and low-stock alerts.

## Database design
- `products`: product name, description, price, stock quantity, reorder level
- `orders`: customer details, order timestamp, total amount, status
- `order_items`: product, quantity, and price captured at the time of ordering

`order_items.unit_price` preserves the price at order time, even if the product price changes later.

## Notes
- The project uses parameterized SQL queries to reduce SQL injection risk.
- Order creation uses a transaction and row-level locking (`FOR UPDATE`) so stock validation and deduction happen together.
- This is an educational CLI project, not a production deployment. For production, add authentication/authorization, migrations, automated tests, logging, and a web API/UI.
