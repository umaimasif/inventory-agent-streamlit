import streamlit as st
import json
import pandas as pd
from typing import List, Dict

# ====== Inventory Data ======
inventory = []
orders = []
RESTOCK_THRESHOLD = 5

# ====== Core Functions ======
def add_item(name, color, category, quantity, price, brand=None, size=None):
    item = {
        "name": name,
        "color": color,
        "category": category,
        "quantity": quantity,
        "price": price,
        "brand": brand,
        "size": size,
    }
    inventory.append(item)
    return f"✅ Added {quantity} {color} {name}(s) in {category} at price {price}"

def delete_item(name, color):
    global inventory
    filtered = [item for item in inventory if not (item['name'] == name and item['color'] == color)]
    if len(filtered) == len(inventory):
        return f"❌ No item named {color} {name} found"
    inventory = filtered
    return f"🗑️ Deleted items with name {color} {name}"

def order_item(name, color, quantity, category, price, brand, size):
    order = {
        "name": name.lower(), "color": color.lower(), "quantity": quantity,
        "category": category.lower(), "price": price, "brand": brand.lower(), "size": size.lower()
    }
    inventory.append(order)
    orders.append(order)
    return f"🛍️ Ordered {quantity} {color} {name}(s) from brand {brand}, size {size}, category {category}, at price {price}"

def restock_alert_tool():
    alerts = [
        f"⚠️ Low stock: {item['quantity']} {item['color']} {item['name']}(s) in {item['category']}. Consider restocking."
        for item in inventory if item["quantity"] < RESTOCK_THRESHOLD
    ]
    return alerts or ["✅ All items are sufficiently stocked."]

def generate_invoice():
    invoice_lines = []
    total_amount = 0
    for order in orders:
        line = f"- {order['quantity']} {order['size']} {order['name']}(s) of brand {order['brand']} at Rs.{order['price']} each → Rs.{order['price'] * order['quantity']}"
        invoice_lines.append(line)
        total_amount += order["price"] * order["quantity"]
    invoice_lines.append(f"\n🧾 Total: Rs.{total_amount}")
    return "\n".join(invoice_lines)

def save_inventory():
    with open("inventory.json", "w") as f:
        json.dump(inventory, f, indent=4)
    df = pd.DataFrame(inventory)
    df.to_csv("inventory.csv", index=False)
    return "💾 Inventory saved to inventory.json and inventory.csv"

def stop_agent():
    summary = {}
    for item in inventory:
        key = f"{item['color']} {item['name']}"
        summary[key] = summary.get(key, 0) + item["quantity"]
    summary_str = "\n".join([f"🧾 You added {v} {k}(s)" for k, v in summary.items()])
    return f"🛑 Agent stopped.\n{summary_str}"

# ====== Streamlit App ======
st.set_page_config(page_title="Inventory Agent App 🧠📦")
st.title("📦 Inventory Agent")
st.subheader("Welcome to your inventory agent.")

# --- Command Input ---
command = st.text_input("Enter your command (e.g., 'add 5 red shirts'):")

if st.button("Run Command") and command:
    command = command.lower()
    output = ""

    try:
        if command.startswith("add"):
            st.subheader("Add Item")
            name = st.text_input("Name")
            color = st.text_input("Color")
            category = st.text_input("Category")
            quantity = st.number_input("Quantity", min_value=1)
            price = st.number_input("Price", min_value=0.0)
            brand = st.text_input("Brand")
            size = st.text_input("Size")
            if st.button("Add"):
                output = add_item(name, color, category, int(quantity), float(price), brand, size)

        elif command.startswith("delete"):
            st.subheader("Delete Item")
            name = st.text_input("Name to Delete")
            color = st.text_input("Color to Delete")
            if st.button("Delete"):
                output = delete_item(name, color)

        elif command.startswith("order"):
            st.subheader("Order Item")
            name = st.text_input("Order Name")
            color = st.text_input("Order Color")
            category = st.text_input("Order Category")
            quantity = st.number_input("Order Quantity", min_value=1)
            price = st.number_input("Order Price", min_value=0.0)
            brand = st.text_input("Order Brand")
            size = st.text_input("Order Size")
            if st.button("Order"):
                output = order_item(name, color, int(quantity), category, int(price), brand, size)

        elif "restock" in command:
            output = "\n".join(restock_alert_tool())

        elif "save" in command:
            output = save_inventory()

        elif "stop" in command:
            output = stop_agent()

        else:
            output = "❓ Unknown command"

        st.success(output)

    except Exception as e:
        st.error(f"⚠️ Error: {str(e)}")

# Show current inventory
tab1, tab2 = st.tabs(["📋 Inventory", "🧾 Orders"])

with tab1:
    if inventory:
        st.dataframe(pd.DataFrame(inventory))
    else:
        st.info("Inventory is empty.")

with tab2:
    if orders:
        st.dataframe(pd.DataFrame(orders))
        st.markdown("---")
        st.text(generate_invoice())
    else:
        st.info("No orders yet.")
