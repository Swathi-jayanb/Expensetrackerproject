from flask import Flask, render_template, request, redirect, flash
import sqlite3
import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# --- Initialize DB ---
def init_db():
    with sqlite3.connect('expenses.db') as conn:
        cur = conn.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                description TEXT,
                amount REAL,
                category TEXT,
                date TEXT
            )
        ''')
        cur.execute('''
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                amount REAL,
                month TEXT
            )
        ''')
        conn.commit()

# --- Home Route (Redirect to Report) ---
@app.route('/')
def home():
    return redirect('/report')

# --- Add & View Expenses ---
@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    conn = sqlite3.connect('expenses.db')
    c = conn.cursor()

    if request.method == 'POST':
        description = request.form['description']
        amount = float(request.form['amount'])
        category = request.form['category']
        date = request.form['date']

        c.execute('INSERT INTO expenses (description, amount, category, date) VALUES (?, ?, ?, ?)',
                  (description, amount, category, date))
        conn.commit()
        flash('Expense added!', 'success')
        return redirect('/expenses')

    c.execute('SELECT * FROM expenses ORDER BY date DESC')
    all_expenses = c.fetchall()
    conn.close()
    return render_template('expenses.html', expenses=all_expenses)

# --- Set Monthly Budget ---
@app.route('/set-budget', methods=['POST'])
def set_budget():
    category = request.form['budget_category']
    amount = float(request.form['budget_amount'])
    month = datetime.date.today().strftime('%Y-%m')

    with sqlite3.connect('expenses.db') as conn:
        cur = conn.cursor()
        cur.execute('REPLACE INTO budgets (category, amount, month) VALUES (?, ?, ?)',
                    (category, amount, month))
        conn.commit()

    flash('Budget set successfully!', 'info')
    return redirect('/report')

# --- Monthly Report ---
@app.route('/report')
def report():
    month = datetime.date.today().strftime('%Y-%m')

    with sqlite3.connect('expenses.db') as conn:
        cur = conn.cursor()

        # Total spending by category
        cur.execute('''
            SELECT category, SUM(amount)
            FROM expenses
            WHERE strftime('%Y-%m', date) = ?
            GROUP BY category
        ''', (month,))
        category_totals = cur.fetchall()

        # Monthly budgets
        cur.execute('SELECT category, amount FROM budgets WHERE month = ?', (month,))
        budgets = dict(cur.fetchall())

    report_data = []
    total_monthly_spending = 0

    for category, spent in category_totals:
        budget = budgets.get(category, 0)
        percent_used = round((spent / budget) * 100, 2) if budget else None
        total_monthly_spending += spent

        alert = None
        if budget:
            if percent_used >= 100:
                alert = "Budget Exceeded!"
            elif percent_used >= 90:
                alert = "Only 10% left!"

        report_data.append({
            'category': category,
            'spent': spent,
            'budget': budget,
            'percent_used': percent_used,
            'alert': alert
        })

    return render_template('report.html', report=report_data, total=total_monthly_spending, month=month)

# --- Run App ---
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
