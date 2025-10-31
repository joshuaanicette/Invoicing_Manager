import json
import io
from flask import Flask, g, jsonify, request, send_file, render_template, make_response, redirect, url_for, session
import os
from io import BytesIO
from fpdf import FPDF
from datetime import datetime
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import logging
import sys
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Get database URL from environment variable
DATABASE_URL = os.environ.get('DATABASE_URL')

if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable is not set!")
    raise ValueError("DATABASE_URL environment variable is required")

# Fix for Heroku postgres URL (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    logger.info("Converted postgres:// to postgresql:// in DATABASE_URL")

logger.info("Starting Invoice Manager Application")

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max request size
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production-12345")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login_page"

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id, username, email, full_name, company_name, phone_number):
        self.id = id
        self.username = username
        self.email = email
        self.full_name = full_name
        self.company_name = company_name
        self.phone_number = phone_number

@login_manager.user_loader
def load_user(user_id):
    """Load user from database for Flask-Login"""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id, username, email, full_name, company_name, phone_number FROM users WHERE id=%s", (user_id,))
        row = cur.fetchone()
        if row:
            return User(row["id"], row["username"], row["email"], row["full_name"], row["company_name"], row["phone_number"])
    except Exception as e:
        logger.error(f"Error loading user: {e}")
    return None

def get_db():
    """Get database connection from application context"""
    db = getattr(g, "_database", None)
    if db is None:
        try:
            db = g._database = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
            logger.debug("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    return db

def init_db():
    """Initialize database tables if they don't exist"""
    try:
        db = get_db()
        cur = db.cursor()

        # users table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            company_name TEXT,
            phone_number TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # invoices table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id SERIAL PRIMARY KEY,
            invoice_number INTEGER,
            creation_date TEXT,
            company_name TEXT,
            company_address TEXT,
            company_email TEXT,
            total_amount REAL,
            user_id INTEGER,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            UNIQUE(user_id, invoice_number)
        );
        """)

        # Migration: Add user_id column if it doesn't exist
        cur.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name='invoices' AND column_name='user_id';
        """)
        if not cur.fetchone():
            logger.info("Adding user_id column to invoices table")
            cur.execute("""
            ALTER TABLE invoices ADD COLUMN user_id INTEGER;
            """)
            logger.info("user_id column added successfully")

        # Migration: Drop old unique constraint on invoice_number if it exists
        # and add composite unique constraint on (user_id, invoice_number)
        cur.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name='invoices' AND constraint_type='UNIQUE'
        AND constraint_name LIKE '%invoice_number%';
        """)
        old_constraint = cur.fetchone()
        if old_constraint:
            logger.info(f"Dropping old unique constraint: {old_constraint['constraint_name']}")
            cur.execute(f"""
            ALTER TABLE invoices DROP CONSTRAINT IF EXISTS {old_constraint['constraint_name']};
            """)

        # Add the new composite unique constraint if it doesn't exist
        cur.execute("""
        SELECT constraint_name
        FROM information_schema.table_constraints
        WHERE table_name='invoices' AND constraint_type='UNIQUE'
        AND constraint_name='invoices_user_id_invoice_number_key';
        """)
        if not cur.fetchone():
            logger.info("Adding composite unique constraint on (user_id, invoice_number)")
            cur.execute("""
            ALTER TABLE invoices ADD CONSTRAINT invoices_user_id_invoice_number_key UNIQUE (user_id, invoice_number);
            """)
            logger.info("Composite unique constraint added successfully")

        # customers table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS customers (
            id SERIAL PRIMARY KEY,
            invoice_id INTEGER,
            name TEXT,
            address TEXT,
            email TEXT,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );
        """)

        # items table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id SERIAL PRIMARY KEY,
            customer_id INTEGER,
            description TEXT,
            quantity INTEGER,
            unit_price REAL,
            FOREIGN KEY(customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );
        """)

        db.commit()
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

@app.teardown_appcontext
def close_connection(exception):
    """Close database connection at the end of request"""
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()
        logger.debug("Database connection closed")

def row_to_invoice(row):
    """Convert database row to invoice dictionary"""
    return {
        "id": row["id"],
        "invoice_number": row["invoice_number"],
        "creation_date": row["creation_date"],
        "company_name": row["company_name"],
        "company_address": row["company_address"],
        "company_email": row["company_email"],
        "total_amount": row["total_amount"]
    }

# ============ Error Handlers ============
@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle uncaught exceptions"""
    logger.error(f"Uncaught exception: {error}", exc_info=True)
    return jsonify({"error": "An unexpected error occurred"}), 500

# ============ Authentication Routes ============
@app.route("/login")
def login_page():
    """Render login page"""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("login.html")

@app.route("/register")
def register_page():
    """Render registration page"""
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    return render_template("register.html")

@app.route("/api/auth/register", methods=["POST"])
def register():
    """Register a new user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        username = data.get("username", "").strip()
        email = data.get("email", "").strip()
        password = data.get("password", "")
        full_name = data.get("full_name", "").strip()
        company_name = data.get("company_name", "").strip()
        phone_number = data.get("phone_number", "").strip()

        # Validate required fields
        if not username or not email or not password:
            return jsonify({"error": "Username, email, and password are required"}), 400

        # Check if user already exists
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM users WHERE username=%s OR email=%s", (username, email))
        if cur.fetchone():
            return jsonify({"error": "Username or email already exists"}), 400

        # Hash password and create user
        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (username, email, password_hash, full_name, company_name, phone_number) VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (username, email, password_hash, full_name, company_name, phone_number)
        )
        user_id = cur.fetchone()["id"]
        db.commit()

        logger.info(f"New user registered: {username}")
        return jsonify({"success": True, "message": "Registration successful"}), 201
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        if 'db' in locals():
            db.rollback()
        return jsonify({"error": "Failed to register user"}), 500

@app.route("/api/auth/login", methods=["POST"])
def login():
    """Login user"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON body"}), 400

        username = data.get("username", "").strip()
        password = data.get("password", "")

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        # Find user
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id, username, email, password_hash, full_name, company_name, phone_number FROM users WHERE username=%s", (username,))
        row = cur.fetchone()

        if not row or not check_password_hash(row["password_hash"], password):
            return jsonify({"error": "Invalid username or password"}), 401

        # Create user object and login
        user = User(row["id"], row["username"], row["email"], row["full_name"], row["company_name"], row["phone_number"])
        login_user(user)

        logger.info(f"User logged in: {username}")
        return jsonify({
            "success": True,
            "user": {
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "company_name": user.company_name,
                "phone_number": user.phone_number
            }
        }), 200
    except Exception as e:
        logger.error(f"Error logging in: {e}")
        return jsonify({"error": "Failed to login"}), 500

@app.route("/api/auth/logout", methods=["POST"])
@login_required
def logout():
    """Logout user"""
    username = current_user.username
    logout_user()
    logger.info(f"User logged out: {username}")
    return jsonify({"success": True, "message": "Logged out successfully"}), 200

@app.route("/api/auth/me", methods=["GET"])
@login_required
def get_current_user():
    """Get current logged in user info"""
    return jsonify({
        "username": current_user.username,
        "email": current_user.email,
        "full_name": current_user.full_name,
        "company_name": current_user.company_name,
        "phone_number": current_user.phone_number
    }), 200

# ============ Routes ============
@app.route("/")
@login_required
def index():
    """Render main page"""
    return render_template("index.html")

@app.route("/test")
def test():
    """Test page for debugging"""
    return render_template("test.html")

@app.route("/simple-test")
def simple_test():
    """Simple click test page"""
    return render_template("simple-test.html")

@app.route("/api/invoices", methods=["GET"])
@login_required
def list_invoices():
    """List all invoices with their customers and items for the current user"""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM invoices WHERE user_id=%s ORDER BY creation_date DESC", (current_user.id,))
        invoices = [row_to_invoice(dict(r)) for r in cur.fetchall()]

        # Attach customers and items
        for inv in invoices:
            cur.execute("SELECT * FROM customers WHERE invoice_id=%s", (inv["id"],))
            customers = []
            for c in cur.fetchall():
                c_dict = dict(c)
                cur.execute("SELECT description, quantity, unit_price FROM items WHERE customer_id=%s", (c_dict["id"],))
                items = [dict(x) for x in cur.fetchall()]
                customers.append({
                    "name": c_dict["name"],
                    "address": c_dict["address"],
                    "email": c_dict["email"],
                    "items": items
                })
            inv["customers"] = customers

        logger.info(f"Retrieved {len(invoices)} invoices")
        return jsonify(invoices)
    except Exception as e:
        logger.error(f"Error listing invoices: {e}")
        return jsonify({"error": "Failed to retrieve invoices"}), 500

@app.route("/api/invoices", methods=["POST"])
@login_required
def create_invoice():
    """Create a new invoice"""
    try:
        data = request.get_json()
        if not data:
            logger.error("No JSON body in create invoice request")
            return jsonify({"error": "No JSON body"}), 400

        logger.info(f"Creating invoice for user {current_user.id}: {current_user.username}")
        db = get_db()
        cur = db.cursor()

        # Determine invoice number (per user)
        invoice_number = data.get("invoice_number")
        if not invoice_number:
            cur.execute("SELECT MAX(invoice_number) as mx FROM invoices WHERE user_id=%s", (current_user.id,))
            result = cur.fetchone()
            mx = result["mx"] if result and result["mx"] else 999
            invoice_number = mx + 1

        logger.info(f"Generated invoice number: {invoice_number}")

        # Validate and parse total amount
        try:
            total_amount = float(data.get("total_amount", 0))
        except (ValueError, TypeError):
            total_amount = 0.0

        # Create invoice
        cur.execute(
            "INSERT INTO invoices (invoice_number, creation_date, company_name, company_address, company_email, total_amount, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (invoice_number, data.get("creation_date"), data.get("company_name"), data.get("company_address"), data.get("company_email"), total_amount, current_user.id)
        )
        invoice_id = cur.fetchone()["id"]
        logger.info(f"Created invoice with ID: {invoice_id}")

        # Add customers and items
        for c in data.get("customers", []):
            cur.execute("INSERT INTO customers (invoice_id, name, address, email) VALUES (%s, %s, %s, %s) RETURNING id",
                        (invoice_id, c.get("name"), c.get("address"), c.get("email")))
            customer_id = cur.fetchone()["id"]
            for it in c.get("items", []):
                cur.execute("INSERT INTO items (customer_id, description, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                            (customer_id, it.get("description"), int(it.get("quantity", 1)), float(it.get("unit_price", 0))))

        db.commit()
        logger.info(f"Created invoice #{invoice_number}")
        return jsonify({"success": True, "invoice_number": invoice_number}), 201
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        if 'db' in locals():
            db.rollback()
        return jsonify({"error": "Failed to create invoice"}), 500

@app.route("/api/invoices/<int:invoice_number>", methods=["PUT"])
@login_required
def modify_invoice(invoice_number):
    data = request.get_json()
    if not data:
        return jsonify({"error":"No JSON body"}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM invoices WHERE invoice_number=%s AND user_id=%s", (invoice_number, current_user.id))
    row = cur.fetchone()
    if not row:
        return jsonify({"error":"Invoice not found"}), 404
    inv_id = row["id"]
    
    # Update invoice header
    cur.execute("UPDATE invoices SET creation_date=%s, company_name=%s, company_address=%s, company_email=%s, total_amount=%s WHERE id=%s",
                (data.get("creation_date"), data.get("company_name"), data.get("company_address"), data.get("company_email"), float(data.get("total_amount",0)), inv_id))
    
    # Delete existing customers/items
    cur.execute("SELECT id FROM customers WHERE invoice_id=%s", (inv_id,))
    custs = [r["id"] for r in cur.fetchall()]
    for cid in custs:
        cur.execute("DELETE FROM items WHERE customer_id=%s", (cid,))
    cur.execute("DELETE FROM customers WHERE invoice_id=%s", (inv_id,))
    
    # Insert new customers/items
    for c in data.get("customers", []):
        cur.execute("INSERT INTO customers (invoice_id, name, address, email) VALUES (%s, %s, %s, %s) RETURNING id",
                    (inv_id, c.get("name"), c.get("address"), c.get("email")))
        cid = cur.fetchone()["id"]
        for it in c.get("items", []):
            cur.execute("INSERT INTO items (customer_id, description, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                        (cid, it.get("description"), int(it.get("quantity",1)), float(it.get("unit_price",0))))
    db.commit()
    return jsonify({"success": True})

@app.route("/api/invoices/<int:invoice_number>", methods=["DELETE"])
@login_required
def delete_invoice(invoice_number):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id FROM invoices WHERE invoice_number=%s AND user_id=%s", (invoice_number, current_user.id))
    row = cur.fetchone()
    if not row:
        return jsonify({"error":"Invoice not found"}), 404
    inv_id = row["id"]
    
    # delete items, customers, invoice
    cur.execute("SELECT id FROM customers WHERE invoice_id=%s", (inv_id,))
    custs = [r["id"] for r in cur.fetchall()]
    for cid in custs:
        cur.execute("DELETE FROM items WHERE customer_id=%s", (cid,))
    cur.execute("DELETE FROM customers WHERE invoice_id=%s", (inv_id,))
    cur.execute("DELETE FROM invoices WHERE id=%s", (inv_id,))
    db.commit()
    return jsonify({"success": True})

@app.route("/api/invoices/categorize")
@login_required
def categorize():
    period = request.args.get("period", "month")
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM invoices WHERE user_id=%s", (current_user.id,))
    invoices = [row_to_invoice(dict(r)) for r in cur.fetchall()]
    
    # Attach customers to each invoice (without items for this view)
    for inv in invoices:
        cur.execute("SELECT name FROM customers WHERE invoice_id=%s", (inv["id"],))
        customers = [{"name": c["name"]} for c in cur.fetchall()]
        inv["customers"] = customers
    
    categorized = {}
    for inv in invoices:
        try:
            d = datetime.strptime(inv["creation_date"], "%Y-%m-%d")
        except:
            # fallback: keep as-is
            key = inv["creation_date"]
        else:
            if period == "year":
                key = str(d.year)
            elif period == "day":
                key = d.strftime("%Y-%m-%d")
            else:
                key = d.strftime("%Y-%m")
        categorized.setdefault(key, []).append(inv)
    return jsonify(categorized)

@app.route("/api/invoices/reset", methods=["POST"])
@login_required
def reset_invoice_number():
    """Reset invoice counter (doesn't actually delete data, just returns current max)"""
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT MAX(invoice_number) as mx FROM invoices WHERE user_id=%s", (current_user.id,))
    result = cur.fetchone()
    mx = result["mx"] if result and result["mx"] else 999
    return jsonify({"success": True, "lastInvoiceNumber": mx})

@app.route("/api/invoices/<int:invoice_number>/pdf", methods=["GET"])
@login_required
def generate_pdf(invoice_number):
    db = get_db()
    cur = db.cursor()

    # Fetch invoice
    cur.execute("SELECT * FROM invoices WHERE invoice_number=%s AND user_id=%s", (invoice_number, current_user.id))
    row = cur.fetchone()
    
    if not row:
        return jsonify({"error": "Invoice not found"}), 404
    
    invoice = row_to_invoice(dict(row))
    
    # Fetch customers and items
    cur.execute("SELECT * FROM customers WHERE invoice_id=%s", (invoice["id"],))
    customers = []
    for c in cur.fetchall():
        c_dict = dict(c)
        cur.execute("SELECT description, quantity, unit_price FROM items WHERE customer_id=%s", (c_dict["id"],))
        items = [dict(x) for x in cur.fetchall()]
        customers.append({
            "name": c_dict["name"],
            "address": c_dict["address"],
            "email": c_dict["email"],
            "items": items
        })
    
    invoice["customers"] = customers

    # ---- PDF Generation with fpdf2 ----
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header - Invoice Title (Blue background)
    pdf.set_fill_color(51, 51, 153)  # RGB for dark blue
    pdf.set_text_color(255, 255, 255)  # White text
    pdf.set_font("Arial", "B", 24)
    pdf.cell(0, 12, f"INVOICE #{invoice['invoice_number']}", 0, 1, "L", 1)

    # Reset text color
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # Company Information and Date on same line
    pdf.set_font("Arial", "B", 12)
    pdf.cell(100, 6, "From:", 0, 0, "L")
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, f"Date: {invoice.get('creation_date', 'N/A')}", 0, 1, "R")

    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, invoice.get('company_name', 'N/A'), 0, 1, "L")
    if invoice.get('company_address'):
        pdf.cell(0, 5, invoice['company_address'], 0, 1, "L")
    if invoice.get('company_email'):
        pdf.cell(0, 5, invoice['company_email'], 0, 1, "L")

    pdf.ln(5)

    # Horizontal line
    pdf.set_draw_color(180, 180, 180)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(8)

    # Customers Section
    for idx, cust in enumerate(invoice.get("customers", [])):
        # Customer Header
        pdf.set_font("Arial", "B", 12)
        pdf.set_text_color(77, 77, 77)
        pdf.cell(0, 6, f"Bill To: {cust.get('name', 'N/A')}", 0, 1, "L")
        pdf.set_text_color(0, 0, 0)

        pdf.set_font("Arial", "", 9)
        if cust.get('address'):
            pdf.cell(0, 5, cust['address'], 0, 1, "L")
        if cust.get('email'):
            pdf.cell(0, 5, cust['email'], 0, 1, "L")

        pdf.ln(3)

        # Items Table
        if cust.get('items'):
            # Table header
            pdf.set_fill_color(230, 230, 230)
            pdf.set_font("Arial", "B", 9)
            pdf.cell(90, 6, "Description", 1, 0, "L", 1)
            pdf.cell(20, 6, "Qty", 1, 0, "C", 1)
            pdf.cell(30, 6, "Unit Price", 1, 0, "R", 1)
            pdf.cell(30, 6, "Total", 1, 1, "R", 1)

            pdf.set_font("Arial", "", 9)
            subtotal = 0

            for item in cust['items']:
                qty = item.get('quantity', 0)
                unit_price = item.get('unit_price', 0)
                total = qty * unit_price
                subtotal += total

                desc = item.get('description', '')
                if len(desc) > 45:
                    desc = desc[:42] + "..."

                # Alternate row background
                pdf.set_fill_color(250, 250, 250)
                pdf.cell(90, 6, desc, 1, 0, "L", 1)
                pdf.cell(20, 6, str(qty), 1, 0, "C", 1)
                pdf.cell(30, 6, f"${unit_price:.2f}", 1, 0, "R", 1)
                pdf.cell(30, 6, f"${total:.2f}", 1, 1, "R", 1)

            # Subtotal for this customer
            pdf.set_font("Arial", "B", 10)
            pdf.cell(140, 6, "Subtotal:", 0, 0, "R")
            pdf.cell(30, 6, f"${subtotal:.2f}", 0, 1, "R")
            pdf.ln(5)

        # Divider between customers
        if idx < len(invoice.get("customers", [])) - 1:
            pdf.set_draw_color(200, 200, 200)
            pdf.line(10, pdf.get_y(), 200, pdf.get_y())
            pdf.ln(5)

    pdf.ln(5)

    # Total Amount (Blue background)
    pdf.set_fill_color(51, 51, 153)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(140, 10, "TOTAL AMOUNT:", 0, 0, "R", 1)
    pdf.cell(30, 10, f"${invoice.get('total_amount', 0):.2f}", 0, 1, "R", 1)

    # Footer
    pdf.set_y(-30)
    pdf.set_text_color(128, 128, 128)
    pdf.set_font("Arial", "", 8)
    pdf.cell(0, 10, "Thank you for your business!", 0, 0, "C")

    # Output PDF to buffer
    buffer = BytesIO()
    buffer.write(pdf.output())
    buffer.seek(0)

    return send_file(
        buffer,
        as_attachment=False,
        download_name=f"invoice_{invoice_number}.pdf",
        mimetype="application/pdf"
    )

# Initialize database on startup
try:
    with app.app_context():
        init_db()
        logger.info("Application initialized successfully")
except Exception as e:
    logger.error(f"Database initialization failed: {e}")
    # Don't exit - let Vercel/production handle the error
    # For development, this will still allow the app to start

# Health check endpoint
@app.route("/health")
def health():
    """Health check endpoint for monitoring"""
    try:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT 1")
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "unhealthy", "error": str(e)}), 500

# For local development and production
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    logger.info(f"Starting server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)
