
import streamlit as st
import json
import csv
import os
from datetime import datetime
import uuid

# File paths
INVENTORY_JSON = "inventory.json"
INVENTORY_CSV = "inventory.csv"
INVOICE_DIR = "invoices"
os.makedirs(INVOICE_DIR, exist_ok=True)

# Load inventory
if os.path.exists(INVENTORY_JSON):
    with open(INVENTORY_JSON, "r") as f:
        inventory = json.load(f)
else:
    inventory = {}

# Save inventory to JSON and CSV
def save_inventory():
    with open(INVENTORY_JSON, "w") as f:
        json.dump(inventory, f, indent=2)
    with open(INVENTORY_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Name", "Color", "Category", "Quantity", "Price"])
        for item, details in inventory.items():
            writer.writerow([
                item,
                details.get("color", ""),
                details.get("category", ""),
                details.get("quantity", 0),
                details.get("price", "")
            ])

# Save invoice to file
def save_invoice(order_data):
    invoice_id = str(uuid.uuid4())[:8]
    filename = f"invoice_{invoice_id}.json"
    invoice_path = os.path.join(INVOICE_DIR, filename)
    invoice_data = {
        "invoice_id": invoice_id,
        "timestamp": datetime.now().isoformat(),
        "order": order_data
    }
    with open(invoice_path, "w") as f:
        json.dump(invoice_data, f, indent=2)
    return invoice_data

# Streamlit UI
st.title("📦 Inventory Agent")
st.write("Welcome to your inventory agent.")

command = st.text_input("Enter your command (e.g., 'add 5 red shirts'):").lower().strip()

# Forms and behavior
if command.startswith("add"):
    with st.form("add_form"):
        name = st.text_input("Name")
        color = st.text_input("Color")
        category = st.text_input("Category")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        price = st.text_input("Price")
        clear = st.form_submit_button("Clear Form")
        submitted = st.form_submit_button("Add Item")

        if clear:
            st.experimental_rerun()
        if submitted:
            if name:
                if name not in inventory:
                    inventory[name] = {}
                inventory[name].update({
                    "color": color,
                    "category": category,
                    "quantity": inventory[name].get("quantity", 0) + quantity,
                    "price": price
                })
                save_inventory()
                st.success(f"✅ Added {quantity} {name}(s) to inventory.")

elif command.startswith("delete"):
    with st.form("delete_form"):
        item_name = st.selectbox("Select item to delete", list(inventory.keys()))
        del_qty = st.number_input("Quantity to delete", min_value=1, step=1)
        submitted = st.form_submit_button("Delete Item")
        if submitted:
            if item_name in inventory:
                current_qty = inventory[item_name].get("quantity", 0)
                inventory[item_name]["quantity"] = max(0, current_qty - del_qty)
                save_inventory()
                st.success(f"❌ Deleted {del_qty} from {item_name}.")

elif command.startswith("restock"):
    with st.form("restock_form"):
        item_name = st.selectbox("Select item to restock", list(inventory.keys()))
        restock_qty = st.number_input("Quantity to restock", min_value=1, step=1)
        submitted = st.form_submit_button("Restock Item")
        if submitted:
            inventory[item_name]["quantity"] += restock_qty
            save_inventory()
            st.success(f"🔄 Restocked {restock_qty} of {item_name}.")

elif command.startswith("order"):
    with st.form("order_form"):
        item = st.selectbox("Item", list(inventory.keys()))
        brand = st.text_input("Brand")
        size = st.text_input("Size")
        quantity = st.number_input("Quantity", min_value=1, step=1)
        submitted = st.form_submit_button("Place Order")
        if submitted:
            if inventory[item]["quantity"] >= quantity:
                inventory[item]["quantity"] -= quantity
                save_inventory()
                invoice = save_invoice({
                    "item": item,
                    "brand": brand,
                    "size": size,
                    "quantity": quantity,
                    "price": inventory[item].get("price", "N/A")
                })
                st.success("🧾 Order placed and invoice generated!")
                st.json(invoice)
            else:
                st.error("❗ Not enough inventory to fulfill order.")

elif command.startswith("stop"):
    st.header("📋 Inventory Summary")
    for item, details in inventory.items():
        st.write(f"{item.title()}: {details['quantity']} (Color: {details.get('color')}, Category: {details.get('category')}, Price: {details.get('price')})")
    st.success("✅ Session ended. Inventory saved.")

elif command:
    st.warning("🤖 Sorry, I didn’t understand that command. Try 'add', 'delete', 'restock', 'order', or 'stop'.")

# Inventory display
st.divider()
st.subheader("📋 Inventory")
if not inventory:
    st.write("Inventory is empty.")
else:
    for item, details in inventory.items():
        st.write(f"- {item.title()} ({details['quantity']} units, Color: {details.get('color')}, Category: {details.get('category')}, Price: {details.get('price')})")
