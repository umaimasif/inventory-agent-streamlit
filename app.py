
import streamlit as st
import json
import csv
import os
import requests

# ========== CONFIG ==========
GROQ_API_KEY = "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"  
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
HEADERS = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}

# ========== MEMORY ==========
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ========== UTILITY FUNCTIONS ==========
def add_item(item):
    st.session_state.inventory.append(item)

def delete_item(name):
    st.session_state.inventory = [i for i in st.session_state.inventory if i["name"] != name]

def save_inventory():
    with open("inventory.json", "w") as f:
        json.dump(st.session_state.inventory, f)
    with open("inventory.csv", "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["name", "category", "brand", "quantity", "size", "price"])
        writer.writeheader()
        writer.writerows(st.session_state.inventory)

def generate_response(user_input):
    messages = [{"role": "system", "content": "You are a helpful fashion store assistant."}]
    for chat in st.session_state.chat_history:
        messages.append(chat)
    messages.append({"role": "user", "content": user_input})

    payload = {
        "model": "llama3-8b-8192",
        "messages": messages,
        "temperature": 0.7
    }
    response = requests.post(GROQ_URL, headers=HEADERS, json=payload)
    reply = response.json()["choices"][0]["message"]["content"]
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    st.session_state.chat_history.append({"role": "assistant", "content": reply})
    return reply

# ========== SIDEBAR ==========
st.sidebar.title("🧠 Inventory Agent")

if st.sidebar.button("➕ Add Item"):
    with st.form("add_form", clear_on_submit=True):
        name = st.text_input("Item Name")
        category = st.text_input("Category")
        brand = st.text_input("Brand")
        quantity = st.number_input("Quantity", min_value=1)
        size = st.selectbox("Size", ["XS", "S", "M", "L", "XL"])
        price = st.number_input("Price", min_value=0.0, format="%.2f")
        submitted = st.form_submit_button("Submit")
        if submitted:
            add_item({"name": name, "category": category, "brand": brand, "quantity": quantity, "size": size, "price": price})
            st.success(f"✅ Added {quantity} {name}(s) to inventory.")

if st.sidebar.button("❌ Delete Item"):
    name = st.text_input("Enter item name to delete")
    if name:
        delete_item(name)
        st.sidebar.success(f"Deleted {name} from inventory.")

if st.sidebar.button("💾 Save Inventory"):
    save_inventory()
    st.sidebar.success("📦 Inventory saved to inventory.json & inventory.csv")

if st.sidebar.button("🛑 Stop Agent"):
    st.stop()

# ========== MAIN CHAT AREA ==========
st.title("🛍️ Inventory Assistant Chat")

with st.chat_message("assistant"):
    st.markdown("Hi! I’m your fashion assistant. Ask me anything about inventory or placing orders.")

user_query = st.chat_input("Ask something like 'Do we have Zara medium shirts?' or 'Help with my order'")
if user_query:
    with st.chat_message("user"):
        st.markdown(user_query)
    response = generate_response(user_query)
    with st.chat_message("assistant"):
        st.markdown(response)

# Optional: View current inventory
st.subheader("📋 Current Inventory")
if st.session_state.inventory:
    st.table(st.session_state.inventory)
else:
    st.info("No items in inventory yet.")
