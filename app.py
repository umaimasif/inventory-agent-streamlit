
import streamlit as st
import json
import pandas as pd
import os
import datetime
import uuid
from reportlab.pdfgen import canvas
import lite_llm

# --- Groq API Setup ---
lite_llm.api_key = "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"
MODEL = "groq/llama3-70b-8192"

# --- Inventory File Paths ---
INVENTORY_FILE_JSON = "inventory.json"
INVENTORY_FILE_CSV = "inventory.csv"
INVOICE_FOLDER = "invoices"
os.makedirs(INVOICE_FOLDER, exist_ok=True)

# --- Load or initialize inventory ---
def load_inventory():
    if os.path.exists(INVENTORY_FILE_JSON):
        with open(INVENTORY_FILE_JSON, "r") as f:
            return json.load(f)
    return []

def save_inventory(inventory):
    with open(INVENTORY_FILE_JSON, "w") as f:
        json.dump(inventory, f, indent=2)
    df = pd.DataFrame(inventory)
    df.to_csv(INVENTORY_FILE_CSV, index=False)

inventory = load_inventory()

# --- Agent Natural Language Handler ---
def process_agent_command(command):
    prompt = f"""
    You are an inventory management agent.
    Supported actions: add, delete, restock, save, generate invoice, stop.
    
    Command: {command}

    Respond with JSON:
    {{
        "action": "add/delete/restock/save/invoice/stop",
        "item": "name of item",
        "color": "color",
        "category": "e.g., shirt, jeans",
        "quantity": 5,
        "price": 100
    }}

    If not enough info, say: "Please provide more details."
    """
    try:
        res = lite_llm.completion(model=MODEL, messages=[{"role": "user", "content": prompt}])
        content = res.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        return {"error": str(e)}

# --- Save Invoice ---
def generate_invoice(inventory):
    invoice_id = str(uuid.uuid4())[:8]
    filename_json = os.path.join(INVOICE_FOLDER, f"invoice_{invoice_id}.json")
    filename_pdf = os.path.join(INVOICE_FOLDER, f"invoice_{invoice_id}.pdf")

    with open(filename_json, "w") as f:
        json.dump(inventory, f, indent=2)

    c = canvas.Canvas(filename_pdf)
    c.drawString(100, 800, f"Invoice ID: {invoice_id}")
    c.drawString(100, 785, f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    y = 760
    for item in inventory:
        c.drawString(100, y, f"{item['quantity']}x {item['color']} {item['name']} ({item['category']}) - ${item['price']}")
        y -= 20
    c.save()
    return invoice_id

# --- Streamlit App Layout ---
st.set_page_config(page_title="📦 Inventory Agent", layout="wide")

st.title("📦 Inventory Agent")
st.caption("Welcome to your inventory agent.")

# --- Sidebar Agent Chat ---
with st.sidebar.expander("🧠 Chat Agent"):
    user_query = st.text_input("How can I help you?", key="agent_input")
    if user_query:
        result = process_agent_command(user_query)
        if "error" in result:
            st.error(result["error"])
        elif "action" in result:
            action = result.get("action", "").lower()
            if action == "add":
                inventory.append(result)
                save_inventory(inventory)
                st.success(f"✅ Added {result['quantity']} {result['color']} {result['name']}")
            elif action == "delete":
                inventory[:] = [i for i in inventory if not (i["name"] == result["name"] and i["color"] == result["color"])]
                save_inventory(inventory)
                st.warning(f"🗑️ Deleted {result['color']} {result['name']}")
            elif action == "restock":
                found = False
                for i in inventory:
                    if i["name"] == result["name"] and i["color"] == result["color"]:
                        i["quantity"] += result["quantity"]
                        found = True
                        break
                if found:
                    save_inventory(inventory)
                    st.success(f"🔁 Restocked {result['quantity']} {result['name']}")
                else:
                    st.warning("Item not found for restocking.")
            elif action == "save":
                save_inventory(inventory)
                st.success("💾 Inventory saved.")
            elif action == "invoice":
                invoice_id = generate_invoice(inventory)
                st.success(f"🧾 Invoice generated: {invoice_id}")
            elif action == "stop":
                st.info("👋 Agent session ended.")
            else:
                st.info("🤖 Unknown action.")
        else:
            st.warning("❓ Couldn't understand the command.")

# --- Inventory Input Form ---
with st.form("inventory_form"):
    st.subheader("Add Item")
    name = st.text_input("Name")
    color = st.text_input("Color")
    category = st.text_input("Category")
    quantity = st.number_input("Quantity", min_value=1, step=1, value=1)
    price = st.number_input("Price", min_value=0.0, step=1.0)
    col1, col2 = st.columns(2)
    with col1:
        submitted = st.form_submit_button("➕ Add")
    with col2:
        clear = st.form_submit_button("🧹 Clear Form")

    if submitted:
        item = {
            "name": name,
            "color": color,
            "category": category,
            "quantity": quantity,
            "price": price
        }
        inventory.append(item)
        save_inventory(inventory)
        st.success(f"✅ Added {quantity} {color} {name}(s)")

    if clear:
        st.experimental_rerun()

# --- Show Inventory Table ---
st.subheader("📋 Inventory")
if inventory:
    st.dataframe(pd.DataFrame(inventory))
else:
    st.info("Inventory is empty.")

# --- Orders Section ---
st.subheader("🧾 Orders")
if st.button("Generate Invoice"):
    invoice_id = generate_invoice(inventory)
    st.success(f"Invoice generated: {invoice_id}")
