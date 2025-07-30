
import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime
from lite_llm import generate_response

# Initialize session states
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "agent_active" not in st.session_state:
    st.session_state.agent_active = False

# File paths
INVENTORY_FILE = "inventory.csv"
INVOICE_FILE = "invoice.csv"

# Helper functions
def save_inventory():
    df = pd.DataFrame(st.session_state.inventory)
    df.to_csv(INVENTORY_FILE, index=False)

def load_inventory():
    if os.path.exists(INVENTORY_FILE):
        df = pd.read_csv(INVENTORY_FILE)
        st.session_state.inventory = df.to_dict(orient="records")

# Load existing inventory
load_inventory()

# Agent interaction using Groq (LiteLLM style placeholder)
def talk_to_agent(message):
    return generate_response(f"Agent: {message}")

# Command parser
def handle_command(command):
    command = command.lower()
    response = ""

    if "add" in command:
        try:
            parts = command.split("add", 1)[1].strip().split()
            quantity = int(parts[0])
            name = " ".join(parts[1:])
            st.session_state.inventory.append({"name": name, "quantity": quantity})
            response = f"✅ Added {quantity} {name}"
            save_inventory()
        except:
            response = "❌ Invalid add command."

    elif "delete" in command:
        name = command.split("delete", 1)[1].strip()
        original_len = len(st.session_state.inventory)
        st.session_state.inventory = [item for item in st.session_state.inventory if item["name"] != name]
        save_inventory()
        if len(st.session_state.inventory) < original_len:
            response = f"🗑️ Deleted all '{name}' items."
        else:
            response = f"❌ No items named '{name}' found."

    elif "restock" in command:
        try:
            parts = command.split("restock", 1)[1].strip().split()
            quantity = int(parts[0])
            name = " ".join(parts[1:])
            updated = False
            for item in st.session_state.inventory:
                if item["name"] == name:
                    item["quantity"] += quantity
                    updated = True
                    break
            if updated:
                response = f"🔄 Restocked {quantity} of {name}"
                save_inventory()
            else:
                response = f"❌ Item '{name}' not found to restock."
        except:
            response = "❌ Invalid restock command."

    elif "save" in command:
        now = datetime.now()
        invoice_id = f"INV-{now.strftime('%Y%m%d%H%M%S')}"
        for item in st.session_state.inventory:
            item["invoice_id"] = invoice_id
            item["date"] = now.strftime("%Y-%m-%d")
        df = pd.DataFrame(st.session_state.inventory)
        df.to_csv(INVOICE_FILE, index=False)
        response = f"💾 Invoice saved as {INVOICE_FILE} with ID {invoice_id}"

    elif "stop" in command:
        st.session_state.agent_active = False
        response = "👋 Agent session ended."

    else:
        response = talk_to_agent(command)

    return response

# Streamlit UI
st.set_page_config(page_title="📦 Inventory Agent", layout="centered")
st.title("📦 Inventory Agent")

with st.sidebar:
    if st.button("🧠 Start Agent"):
        st.session_state.agent_active = True
    if st.button("📄 Show Inventory CSV"):
        if os.path.exists(INVENTORY_FILE):
            df = pd.read_csv(INVENTORY_FILE)
            st.dataframe(df)
        else:
            st.warning("No inventory file yet.")
    if st.button("🧾 Show Invoice CSV"):
        if os.path.exists(INVOICE_FILE):
            df = pd.read_csv(INVOICE_FILE)
            st.dataframe(df)
        else:
            st.warning("No invoice file yet.")
    if st.button("🧹 Clear Form"):
        st.session_state.inventory = []
        save_inventory()
        st.success("Inventory cleared!")

if st.session_state.agent_active:
    st.subheader("💬 Agent Console")
    user_command = st.text_input("Enter your command (e.g., 'add 5 red shirts'):")
    if user_command:
        response = handle_command(user_command)
        st.markdown(response)
else:
    st.info("Click '🧠 Start Agent' in sidebar to begin.")
    