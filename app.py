from flask import Flask, render_template, request, redirect, send_file
import sqlite3
import pandas as pd

app = Flask(__name__)
app.secret_key = 'mysecretkey123'

# ------------------ DATABASE INIT ------------------

def init_db():
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            product TEXT,
            category TEXT,
            quantity INTEGER,
            price REAL,
            cost REAL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ------------------ HOME ------------------

@app.route('/')
def home():
    return render_template("index.html")

# ------------------ DASHBOARD ------------------

# ------------------ DASHBOARD ROUTE ------------------

@app.route('/dashboard')
def dashboard():
    from flask import session

    simulation = session.pop('simulation', False)
    new_profit = session.pop('new_profit', None)
    new_margin = session.pop('new_margin', None)
    old_profit = session.pop('old_profit', None)
    old_margin = session.pop('old_margin', None)
    profit_change = ((new_profit - old_profit) / old_profit) * 100 if old_profit else 0
    # Connect to SQLite database
    conn = sqlite3.connect('sales.db')
    
    # Read full sales table into Pandas DataFrame
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    
    # Close connection
    conn.close()



    # ------------------ IF DATABASE IS EMPTY ------------------
    if df.empty:
        
        total_sales = 0
        total_profit = 0

        # Category chart data
        labels = []
        values = []

        # Top products table
        top_products_data = []

        # Monthly trend chart
        month_labels = []
        month_values = []
        all_data = []
    # ------------------ IF DATA EXISTS ------------------
    else:
        
        # Create new calculated columns
        # Clean numeric columns properly
        df['quantity'] = pd.to_numeric(df['quantity'].astype(str).str.replace(',', '').str.strip(), errors='coerce')
        df['price'] = pd.to_numeric(df['price'].astype(str).str.replace(',', '').str.strip(), errors='coerce')
        df['cost'] = pd.to_numeric(df['cost'].astype(str).str.replace(',', '').str.strip(), errors='coerce')

        # Now safe to calculate
        print(df.dtypes)
        df['sales'] = df['quantity'] * df['price']
        df['profit'] = df['sales'] - df['cost']
        df['sales'] = df['quantity'] * df['price']
        df['profit'] = df['sales'] - df['cost']
# ------------------ SMART INSIGHTS ------------------

        insights = []

        # Clean category
        df['category'] = df['category'].astype(str).str.strip().str.title()

        # Low profit category
        low_profit = df.groupby('category')['profit'].sum().idxmin()
        insights.append(f"⚠️ Low profit in category: {low_profit}")

        # Top product
        top_product = df.groupby('product')['sales'].sum().idxmax()
        insights.append(f"🔥 Top selling product: {top_product}")

        # Loss detection
        if (df['profit'] < 0).any():
            insights.append("🚨 Some products are making loss")

        # High sales category
        top_category = df.groupby('category')['sales'].sum().idxmax()
        insights.append(f"📈 Highest sales in: {top_category}")

        # Profit margin insight (NEW 🔥)
        profit_margin = (df['profit'].sum() / df['sales'].sum()) * 100
        insights.append(f"💡 Overall profit margin: {profit_margin:.2f}%")

        # ------------------ RECOMMENDED ACTIONS ------------------

        recommendations = []

        profit_margin = (df['profit'].sum() / df['sales'].sum()) * 100

        # Low margin
        if profit_margin < 10:
            recommendations.append("⚠️ Increase prices or reduce costs (low profit margin)")

        # Loss products
        if (df['profit'] < 0).any():
            loss_product = df[df['profit'] < 0]['product'].iloc[0]
            recommendations.append(f"❌ Consider removing or fixing pricing of: {loss_product}")

        # Top category focus
        top_category = df.groupby('category')['sales'].sum().idxmax()
        recommendations.append(f"📈 Focus marketing on: {top_category}")

        # Low performing category
        low_category = df.groupby('category')['profit'].sum().idxmin()
        recommendations.append(f"⚠️ Improve or rethink strategy for: {low_category}")

        # ------------------ BUSINESS HEALTH SCORE ------------------

        score = 100

        if profit_margin < 10:
            score -= 30

        if (df['profit'] < 0).any():
            score -= 20

        if len(df['category'].unique()) < 2:
            score -= 10

        # Clamp score
        score = max(0, min(100, score))





        # Convert columns to numeric
        df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['cost'] = pd.to_numeric(df['cost'], errors='coerce')

        # ------------------ KPI CALCULATIONS ------------------
        total_sales = df['sales'].sum()
        total_profit = df['profit'].sum()

        # ------------------ CATEGORY-WISE SALES (BAR CHART) ------------------
        df['category'] = df['category'].astype(str).str.strip()
        
        category_summary = (
            df.groupby('category')['sales']
            .sum()
            .reset_index()
        )

        labels = category_summary['category'].tolist()
        values = [float(x) for x in category_summary['sales']]

        # ------------------ TOP 5 PRODUCTS (TABLE) ------------------
        top_products = (
            df.groupby('product')['sales']
            .sum()
            .sort_values(ascending=False)
            .head(5)
            .reset_index()
        )

        top_products_data = top_products.values.tolist()

        # ------------------ MONTHLY SALES TREND (LINE CHART) ------------------
        # Convert date column to datetime
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')

        monthly_summary = (
            df.groupby(df['date'].dt.to_period('M'))['sales']
            .sum()
            .reset_index()
        )

        # Convert period to string (for chart labels)
        monthly_summary['date'] = monthly_summary['date'].astype(str)

        month_labels = monthly_summary['date'].tolist()
        month_values = monthly_summary['sales'].tolist()



        
        all_data = df[['id','date', 'product', 'category', 'quantity', 'price', 'cost', 'sales', 'profit']].values.tolist()
    # ------------------ SEND ALL DATA TO FRONTEND ------------------
    profit_change = 0
    if new_profit and old_profit:
        profit_change = ((new_profit - old_profit) / old_profit) * 100
    
    return render_template(
    "dashboard.html",
    total_sales=total_sales,
    total_profit=total_profit,
    labels=labels,
    values=values,
    insights=insights,
    top_products=top_products_data,
    all_data=all_data,
    recommendations=recommendations,
    score=score,
    simulation=simulation,
    new_profit=new_profit,
    new_margin=new_margin,
    old_profit=old_profit,
    old_margin=old_margin,
    profit_change=profit_change
)
    



# ------------------ UPLOAD CSV ------------------

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']

        if file:
            df = pd.read_csv(file)
            # ------------------ CSV VALIDATION ------------------

        required_cols = ['Order Date', 'Product Name', 'Category', 'Quantity', 'Sales', 'Profit']

        for col in required_cols:
            if col not in df.columns:
                return "❌ Invalid CSV format. Please upload correct file with required columns."

            # Rename Superstore columns to match our database
            df = df.rename(columns={
                'Order Date': 'date',
                'Product Name': 'product',
                'Category': 'category',
                'Quantity': 'quantity',
                'Sales': 'price',
                'Profit': 'profit'
            })

            # Convert date format (DD-MM-YYYY)
            df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')

            # Convert numeric columns safely
            df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
            df['profit'] = pd.to_numeric(df['profit'], errors='coerce')

            # Calculate cost from sales and profit
            df['cost'] = df['price'] - df['profit']

            # Keep only required columns
            df = df[['date', 'product', 'category', 'quantity', 'price', 'cost']]

            # Drop rows with invalid data
            df = df.dropna()

            conn = sqlite3.connect('sales.db')
            df.to_sql('sales', conn, if_exists='append', index=False)
            conn.close()

            return redirect('/dashboard')

    return render_template('upload.html')
    # ------------------ DELETE SALE ------------------

@app.route('/delete/<int:id>')
def delete_sale(id):
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute("DELETE FROM sales WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect('/dashboard')
    
    



# ------------------ EXPORT CSV ------------------

@app.route('/export')
def export_data():
    conn = sqlite3.connect('sales.db')
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()

    if df.empty:
        return redirect('/dashboard')

    # Convert numeric safely
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce')

    df['sales'] = df['quantity'] * df['price']
    df['profit'] = df['sales'] - df['cost']

    file_path = "sales_report.csv"
    df.to_csv(file_path, index=False)

    return send_file(
        file_path,
        as_attachment=True
    )


# ------------------ CLEAR DATABASE ------------------

@app.route('/clear')
def clear_database():
    conn = sqlite3.connect('sales.db')
    c = conn.cursor()
    c.execute("DELETE FROM sales")
    conn.commit()
    conn.close()

    return redirect('/dashboard')


# ------------------ WHAT-IF SIMULATOR ------------------

@app.route('/simulate', methods=['POST'])
def simulate():
    price_change = float(request.form.get('price_change', 0))
    cost_change = float(request.form.get('cost_change', 0))

    conn = sqlite3.connect('sales.db')
    df = pd.read_sql_query("SELECT * FROM sales", conn)
    conn.close()

    if df.empty:
        return redirect('/dashboard')

    # Ensure numeric
    df['quantity'] = pd.to_numeric(df['quantity'], errors='coerce')
    df['price'] = pd.to_numeric(df['price'], errors='coerce')
    df['cost'] = pd.to_numeric(df['cost'], errors='coerce')

    # Apply simulation
    df['new_price'] = df['price'] * (1 + price_change / 100)
    df['new_cost'] = df['cost'] * (1 - cost_change / 100)


    # OLD VALUES
    old_profit = df['price'].mul(df['quantity']).sum() - df['cost'].sum()
    old_sales = df['price'].mul(df['quantity']).sum()
    old_margin = (old_profit / old_sales) * 100


    df['new_sales'] = df['new_price'] * df['quantity']
    df['new_profit'] = df['new_sales'] - df['new_cost']

    total_new_profit = df['new_profit'].sum()
    total_new_sales = df['new_sales'].sum()

    new_margin = (total_new_profit / total_new_sales) * 100

    from flask import session
    session['simulation'] = True
    session['new_profit'] = round(total_new_profit, 2)
    session['new_margin'] = round(new_margin, 2)
    session['old_profit'] = round(old_profit, 2)
    session['old_margin'] = round(old_margin, 2)

    return redirect('/dashboard')

# ------------------ RUN APP ------------------
# ------------------ ADD MANUAL SALE ------------------

@app.route('/add', methods=['GET', 'POST'])
def add_sale():
    if request.method == 'POST':
        data = (
            request.form['date'],
            request.form['product'],
            request.form['category'],
            int(request.form['quantity']),
            float(request.form['price']),
            float(request.form['cost'])
        )

        conn = sqlite3.connect('sales.db')
        c = conn.cursor()
        c.execute("""
            INSERT INTO sales
            (date, product, category, quantity, price, cost)
            VALUES (?, ?, ?, ?, ?, ?)
        """, data)

        conn.commit()
        conn.close()

        return redirect('/dashboard')

    return render_template('add_sales.html')


if __name__ == '__main__':
    app.run(debug=True)