import sqlite3
from config import Config

class Database:

    @staticmethod
    def init_db():
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        CUIN TEXT,
        CN_No TEXT,
        CN_Date TEXT,
        Invoice_No TEXT,
        Buyers_PIN_No TEXT,
        Company_PIN TEXT,
        file_path TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        ''')  

        # Create the products table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS products
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        invoice_id INTEGER,
        Product_Code TEXT,
        Description TEXT,
        Qty INTEGER,
        Amount_Incl_Tax_USD REAL,
        Amount_Incl_Tax_KES REAL,
        FOREIGN KEY(invoice_id) REFERENCES invoices(id))
        ''')  
        # Create the failed_files table if it doesn't exist
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS failed_files
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT,
        error TEXT,
        processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
        ''')

        conn.commit()
        conn.close()

    @staticmethod
    def insert_invoice(invoice_data, processed_path):
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
    

        cursor.execute('''
        INSERT INTO invoices (CUIN, CN_No, CN_Date, Invoice_No, Buyers_PIN_No, Company_PIN, file_path)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (invoice_data['CUIN'], invoice_data['CN_No'], invoice_data['CN_Date'], 
              invoice_data['Invoice_No'], invoice_data['Buyers_PIN_No'], 
              invoice_data['Companys_PIN'], processed_path))
        
        invoice_id = cursor.lastrowid

        # Insert product data
        for product in invoice_data['products']:
            cursor.execute('''
            INSERT INTO products (invoice_id, Product_Code, Description, Qty, Amount_Incl_Tax_USD, Amount_Incl_Tax_KES)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (invoice_id, product['Product_Code'], product['Description'], product['Qty'], 
                  product['Amount_Incl_Tax_USD'], product['Amount_Incl_Tax_KES']))
        
        conn.commit()
        conn.close()
        return invoice_id

    @staticmethod
    def insert_failed_file(failed_path, error):
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO failed_files (file_path, error)
        VALUES (?, ?)
        ''', (failed_path, str(error)))
        
        conn.commit()
        conn.close()

    @staticmethod
    def get_failed_invoices():
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT file_path, error, processed_at FROM failed_files
        ''')
        rows = cursor.fetchall()
        conn.close()
        
        return [{"file_path": row[0], "error": row[1], "processed_at": row[2]} for row in rows]

    @staticmethod
    def get_all_invoices_with_products():

        invoices = []
        conn = sqlite3.connect(Config.DB_PATH)
        cursor = conn.cursor()
        # Fetch all invoices
        cursor.execute("SELECT * FROM invoices")
        invoice_rows = cursor.fetchall()

        for invoice_row in invoice_rows:
            invoice = {
                "id": invoice_row[0],
                "CUIN": invoice_row[1],
                "CN_No": invoice_row[2],
                "CN_Date": invoice_row[3],
                "Invoice_No": invoice_row[4],
                "Buyers_PIN_No": invoice_row[5],
                "Company_PIN": invoice_row[6],
                "file_path": invoice_row[7],
                "processed_at": invoice_row[8],
                "products": []
            }

            # Fetch products for the current invoice
            cursor.execute("SELECT * FROM products WHERE invoice_id=?", (invoice["id"],))
            products = cursor.fetchall()
            invoice["products"] = [
                {
                    "id": product[0],
                    "invoice_id": product[1],
                    "Product_Code": product[2],
                    "Description": product[3],
                    "Qty": product[4],
                    "Amount_Incl_Tax_USD": product[5],
                    "Amount_Incl_Tax_KES": product[6]
                } for product in products
            ]

            invoices.append(invoice)

        conn.close()
        return invoices  # Assuming you've built this list as in your original code
