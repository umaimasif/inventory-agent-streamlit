import streamlit as st
import json
import csv
import os
from datetime import datetime

# ---------- File Paths ----------
JSON_FILE = "inventory.json"
CSV_FILE = "inventory.csv"
ORDER_FILE = "orders.json"
INVOICE_FILE = "invoice.txt"

# ---------- Load or Init Inventory ----------
def load_inventory():
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, "r") as f:
            return json.load(f)
    return {}

def save_inventory(inventory):
    with open(JSON_FILE, "w") as f:
        json.dump(inventory, f, indent=2)
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Color", "Category", "Quantity", "Price"])
        for key, value in inventory.items():
            writer.writerow([key, *value.values()])

def load_orders():
    if os.path.exists(ORDER_FILE):
        with open(ORDER_FILE, "r") as f:
            return json.load(f)
    return []

def save_orders(orders):
    with open(ORDER_FILE, "w") as f:
        json.dump(orders, f, indent=2)

def save_invoice(order):
    with open(INVOICE_FILE, "w") as f:
        f.write("\n--- INVOICE ---\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        total = 0
        for item in order:
            line = f"{item['quantity']} x {item['name']} ({item['color']}) - ${item['price']}\n"
            f.write(line)
            total += item['quantity'] * item['price']
        f.write(f"Total: ${total}\n")

# ---------- UI ----------
st.title("📦 Inventory Agent")
st.subheader("Welcome to your inventory agent.")

command = st.text_input("Enter your command (e.g., 'add 5 red shirts'):")

inventory = load_inventory()
orders = load_orders()

# ---------- Command Handler ----------
if command.lower().startswith("add"):
    st.markdown("### ➕ Add Item")
    with st.form("add_form"):
        name = st.text_input("Name")
        color = st.text_input("Color")
        category = st.text_input("Category")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price = st.number_input("Price", min_value=0.0, step=0.01)
        submitted = st.form_submit_button("Add")
        clear = st.form_submit_button("Clear Form")

        if submitted and name:
            inventory[name] = {
                "color": color,
                "category": category,
                "quantity": quantity,
                "price": price
            }
            save_inventory(inventory)
            st.success(f"{quantity} {name}(s) added.")

elif command.lower().startswith("delete"):
    st.markdown("### 🗑️ Delete Item")
    if inventory:
        with st.form("delete_form"):
            item = st.selectbox("Select item to delete", list(inventory.keys()))
            quantity = st.number_input("Quantity to delete", min_value=1, step=1)
            delete_btn = st.form_submit_button("Delete")
            if delete_btn:
                if quantity >= inventory[item]["quantity"]:
                    del inventory[item]
                else:
                    inventory[item]["quantity"] -= quantity
                save_inventory(inventory)
                st.success(f"Deleted {quantity} of {item}")
    else:
        st.warning("Inventory is empty.")

elif command.lower().startswith("order"):
    st.markdown("### 🛒 Take Order")
    if inventory:
        with st.form("order_form"):
            item = st.selectbox("Select item", list(inventory.keys()))
            quantity = st.number_input("Quantity", min_value=1, step=1)
            order_btn = st.form_submit_button("Order")
            if order_btn:
                if quantity > inventory[item]["quantity"]:
                    st.error("Not enough stock.")
                else:
                    inventory[item]["quantity"] -= quantity
                    ordered = {
                        "name": item,
                        "color": inventory[item]["color"],
                        "quantity": quantity,
                        "price": inventory[item]["price"]
                    }
                    orders.append(ordered)
                    save_inventory(inventory)
                    save_orders(orders)
                    save_invoice(orders)
                    st.success(f"Ordered {quantity} of {item}")
    else:
        st.warning("Inventory is empty.")

elif command.lower().startswith("stop"):
    st.markdown("### 🔚 Inventory Summary")
    if inventory:
        for item, details in inventory.items():
            st.write(f"{item}: {details['quantity']} left")
    else:
        st.write("Inventory is empty.")
    if orders:
        st.markdown("### 🧾 Final Invoice")
        with open(INVOICE_FILE, "r") as f:
            st.text(f.read())
        orders.clear()
        save_orders(orders)

# ---------- Sidebar Inventory Viewer ----------
st.sidebar.header("📋 Inventory")
if inventory:
    for name, details in inventory.items():
        st.sidebar.write(f"{name} | {details['quantity']} pcs | ${details['price']}")
else:
    st.sidebar.write("Inventory is empty.")

st.sidebar.header("🧾 Orders")
if orders:
    for order in orders:
        st.sidebar.write(f"{order['quantity']} x {order['name']} (${order['price']})")
else:
    st.sidebar.write("No orders yet.")
