
import streamlit as st
import requests
import json
import pandas as pd
import uuid

# --- Constants and Setup ---
GROQ_API_KEY = "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"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# --- Session State ---
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "orders" not in st.session_state:
    st.session_state.orders = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# --- Chatbot Function ---
def ask_assistant(prompt):
    st.session_state.chat_history.append({"role": "user", "content": prompt})
    payload = {
        "model": "llama3-8b-8192",
        "messages": st.session_state.chat_history,
        "temperature": 0.7
    }
    response = requests.post(GROQ_URL, headers=HEADERS, json=payload)
    result = response.json()
    reply = result["choices"][0]["message"]["content"]
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    return reply

# --- Inventory Functions ---
def add_item(name, category, size, price, quantity):
    st.session_state.inventory.append({
        "id": str(uuid.uuid4()),
        "name": name,
        "category": category,
        "size": size,
        "price": price,
        "quantity": quantity
    })

def delete_item(item_id):
    st.session_state.inventory = [item for item in st.session_state.inventory if item["id"] != item_id]

def save_inventory():
    df = pd.DataFrame(st.session_state.inventory)
    df.to_csv("inventory.csv", index=False)
    df.to_json("inventory.json", orient="records", indent=2)
    st.success("Inventory saved as CSV and JSON.")
import pandas as pd
import os

# Save CSV and show download button
def save_inventory_and_download(inventory):
    if not inventory:
        st.warning("No items to save.")
        return

    df = pd.DataFrame(inventory)
    csv_file = "inventory.csv"
    df.to_csv(csv_file, index=False)
    st.success(f"Items saved to {csv_file}")

    # Read back the CSV for download button
    with open(csv_file, "rb") as f:
        st.download_button(
            label="📥 Download Inventory CSV",
            data=f,
            file_name=csv_file,
            mime="text/csv"
        )

def restock_item(item_id, quantity):
    for item in st.session_state.inventory:
        if item["id"] == item_id:
            item["quantity"] += quantity
            break

def place_order(order_items):
    invoice = []
    for oid in order_items:
        for item in st.session_state.inventory:
            if item["id"] == oid and item["quantity"] > 0:
                item["quantity"] -= 1
                invoice.append(item)
    df = pd.DataFrame(invoice)
    df.to_csv("invoice.csv", index=False)
    st.success("Invoice generated and saved.")
    st.session_state.orders.append(invoice)

# --- Sidebar: Chatbot ---
st.sidebar.header("💬 Assistant")
prompt = st.sidebar.text_input("Ask something...")
if st.sidebar.button("Send"):
    if prompt:
        reply = ask_assistant(prompt)
        st.sidebar.markdown(f"**Assistant:** {reply}")

# --- Main Interface ---
st.title("🧠 Inventory Agent Dashboard")
tabs = st.tabs(["Add", "View", "Delete", "Order", "Restock", "Save", "Stop"])

# --- Tab 1: Add ---
with tabs[0]:
    st.header("Add Item")
    name = st.text_input("Item Name")
    category = st.text_input("Category")
    size = st.text_input("Size")
    price = st.number_input("Price", step=1.0)
    quantity = st.number_input("Quantity", step=1, min_value=0)
    if st.button("Submit Item"):
        add_item(name, category, size, price, quantity)
        st.success("Item added!")

# --- Tab 2: View ---
with tabs[1]:
    st.header("Current Inventory")
    if st.session_state.inventory:
        st.dataframe(pd.DataFrame(st.session_state.inventory))
    else:
        st.info("No items in inventory yet.")

# --- Tab 3: Delete ---
with tabs[2]:
    st.header("Delete Item")
    for item in st.session_state.inventory:
        if st.button(f"Delete {item['name']}"):
            delete_item(item["id"])
            st.success(f"Deleted {item['name']}")

# --- Tab 4: Order ---
with tabs[3]:
    st.header("Place Order")
    ids = [item["id"] for item in st.session_state.inventory if item["quantity"] > 0]
    labels = [f"{item['name']} ({item['quantity']} left)" for item in st.session_state.inventory if item["quantity"] > 0]
    selected_ids = st.multiselect("Select items to order:", ids, format_func=lambda x: dict(zip(ids, labels)).get(x, x))
    if st.button("Place Order"):
        place_order(selected_ids)

# --- Tab 5: Restock ---
with tabs[4]:
    st.header("Restock Items")
    for item in st.session_state.inventory:
        qty = st.number_input(f"Restock quantity for {item['name']}", key=item['id'], step=1, min_value=0)
        if st.button(f"Restock {item['name']}"):
            restock_item(item["id"], qty)
            st.success(f"Restocked {item['name']} by {qty}")

# --- Tab 6: Save ---
with tabs[5]:
    if st.button("Save Inventory"):
    save_inventory_and_download(st.session_state.inventory)


# --- Tab 7: Stop ---
with tabs[6]:
    st.header("Stop Agent")
    if st.button("Clear Session"):
        st.session_state.inventory = []
        st.session_state.orders = []
        st.success("Session cleared.")
