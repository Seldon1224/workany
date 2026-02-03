import csv
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime

# Read ledger data
ledger_file = 'ledger.csv'
transactions = []

try:
    with open(ledger_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            row['Amount'] = float(row['Amount'])
            transactions.append(row)
except FileNotFoundError:
    print(f"Error: {ledger_file} not found.")
    exit(1)

# Analysis
total_income = 0
total_expense = 0
category_expenses = defaultdict(float)

for t in transactions:
    if t['Type'] == 'Income':
        total_income += t['Amount']
    elif t['Type'] == 'Expense':
        total_expense += t['Amount']
        category_expenses[t['Category']] += t['Amount']

balance = total_income - total_expense

# Print Summary
print("--- Ledger Analysis Summary ---")
print(f"Total Income: ${total_income:.2f}")
print(f"Total Expense: ${total_expense:.2f}")
print(f"Net Balance: ${balance:.2f}")
print("\n--- Expense by Category ---")
for cat, amount in category_expenses.items():
    print(f"{cat}: ${amount:.2f}")

# Chart Generation
categories = list(category_expenses.keys())
amounts = list(category_expenses.values())

if categories:
    plt.figure(figsize=(10, 6))
    plt.bar(categories, amounts, color='skyblue')
    plt.xlabel('Category')
    plt.ylabel('Amount ($)')
    plt.title('Expenses by Category')
    plt.savefig('expense_chart.png')
    print("\n[Chart Generated] expense_chart.png")
else:
    print("\n[No Expenses to Chart]")
