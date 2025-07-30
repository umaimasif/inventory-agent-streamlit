
import streamlit as st
import pandas as pd
import os
import json
import uuid
from datetime import datetime
import requests

# Set your Groq API key here (or use st.secrets if deploying)
GROQ_API_KEY = "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"

# File paths
INVENTORY_FILE = "inventory.csv"
INVOICE_FILE = "invoice.csv"

# Initialize files
if not os.path.exists(INVENTORY_FILE):
    pd.DataFrame(columns=["Item", "Quantity", "Category", "Price"]).to_csv(INVENTORY_FILE, index=False)

if not os.path.exists(INVOICE_FILE):
    pd.DataFrame(columns=["Invoice ID", "Item", "Quantity", "Date"]).to_csv(INVOICE_FILE, index=False)


# 💬 LLM response generator (Groq)
def generate_response(prompt):
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "llama3-8b-8192",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"


# 🧠 Process command
def process_command(command):
    command = command.lower()

    if "add" in command:
        return handle_add(command)
    elif "delete" in command:
        return handle_delete(command)
    elif "save" in command:
        return handle_save()
    elif "restock" in command:
        return handle_restock(command)
    elif "stop" in command:
        return "Agent stopped."
    else:
        return generate_response(f"This is an inventory system. What should I do with: '{command}'?")


# 🟢 Add item
def handle_add(command):
    try:
        parts = command.split("add")[1].strip().split()
        quantity = int(parts[0])
        item = " ".join(parts[1:])
        df = pd.read_csv(INVENTORY_FILE)

        if item in df["Item"].values:
            df.loc[df["Item"] == item, "Quantity"] += quantity
        else:
            df = pd.concat([df, pd.DataFrame([{
                "Item": item,
                "Quantity": quantity,
                "Category": "General",
                "Price": 0.0
            }])], ignore_index=True)

        df.to_csv(INVENTORY_FILE, index=False)
        return f"✅ Added {quantity} {item}."
    except Exception as e:
        return f"❌ Error adding item: {e}"


# 🔴 Delete item
def handle_delete(command):
    try:
        item = command.split("delete")[1].strip()
        df = pd.read_csv(INVENTORY_FILE)

        if item in df["Item"].values:
            df = df[df["Item"] != item]
            df.to_csv(INVENTORY_FILE, index=False)
            return f"🗑️ Deleted {item}."
        else:
            return f"⚠️ {item} not found."
    except Exception as e:
        return f"❌ Error deleting item: {e}"


# 💾 Save invoice
def handle_save():
    try:
        df = pd.read_csv(INVENTORY_FILE)
        invoice_id = str(uuid.uuid4())[:8]
        date = datetime.now().strftime("%Y-%m-%d")

        invoice_df = pd.DataFrame([{
            "Invoice ID": invoice_id,
            "Item": row["Item"],
            "Quantity": row["Quantity"],
            "Date": date
        } for _, row in df.iterrows()])

        existing = pd.read_csv(INVOICE_FILE)
        combined = pd.concat([existing, invoice_df], ignore_index=True)
        combined.to_csv(INVOICE_FILE, index=False)

        return f"💰 Invoice `{invoice_id}` saved with {len(df)} items."
    except Exception as e:
        return f"❌ Error saving invoice: {e}"


# ♻️ Restock items
def handle_restock(command):
    try:
        parts = command.split("restock")[1].strip().split()
        quantity = int(parts[0])
        item = " ".join(parts[1:])
        df = pd.read_csv(INVENTORY_FILE)

        if item in df["Item"].values:
            df.loc[df["Item"] == item, "Quantity"] += quantity
            df.to_csv(INVENTORY_FILE, index=False)
            return f"🔁 Restocked {quantity} {item}."
        else:
            return f"⚠️ {item} not found to restock."
    except Exception as e:
        return f"❌ Error restocking: {e}"


# 📦 Streamlit UI
st.set_page_config(page_title="📦 Inventory Agent", layout="wide")
st.title("📦 Inventory Agent")
st.markdown("Welcome! Your assistant is ready. Ask anything like:\n- `add 5 blue jeans`\n- `delete red shirt`\n- `restock 10 black jackets`\n- `save`\n- `stop`")

# Sidebar options
with st.sidebar:
    st.header("👨‍💼 Agent Panel")
    show_agent = st.checkbox("Show Agent")
    show_inventory = st.checkbox("View Inventory CSV")
    show_invoice = st.checkbox("View Invoice CSV")

# Agent interaction
if show_agent:
    user_input = st.text_input("💬 How can I help you?", key="command_input")
    if user_input:
        result = process_command(user_input)
        st.success(result)

# CSV views
if show_inventory:
    st.subheader("📊 Inventory Data")
    df = pd.read_csv(INVENTORY_FILE)
    st.dataframe(df)

if show_invoice:
    st.subheader("🧾 Invoice Records")
    df = pd.read_csv(INVOICE_FILE)
    st.dataframe(df)
