
import streamlit as st
import requests
import json
import pandas as pd
import uuid
import litellm
import os
import io

# ---------- FUNCTION DEFINITIONS ----------

def delete_item(item_id):
    st.session_state.inventory = [item for item in st.session_state.inventory if item["id"] != item_id]

def save_inventory_and_download(inventory):
    if not inventory:
        st.warning("No items to save.")
        return
    df = pd.DataFrame(inventory)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()  # ✅ ADD THIS LINE
    st.download_button(
        label="📥 Download Inventory CSV",
        data=csv_data,
        file_name="inventory.csv",
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

def ask_assistant(prompt):
    try:
        result = litellm.completion(
            model="groq/llama3-8b-8192",
            messages=[
                {"role": "system", "content": "You are a helpful inventory assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        if "choices" in result and result["choices"]:
            return result["choices"][0]["message"]["content"]
        else:
            return "❌ Assistant returned an unexpected response."
    except Exception as e:
        return f"⚠️ Error in assistant: {str(e)}"


# ---------- SESSION INITIALIZATION ----------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "inventory" not in st.session_state:
    st.session_state.inventory = []
if "orders" not in st.session_state:
    st.session_state.orders = []
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------- USER ACCOUNT MANAGEMENT ----------
USER_FILE = "user_data.json"
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

with open(USER_FILE, "r") as f:
    users = json.load(f)

def save_users():
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# ---------- LOGIN OR SIGNUP ----------
st.title("🧠 Inventory Agent App")
menu = st.sidebar.selectbox("Choose an option", ["Login", "Create Account"])

if menu == "Create Account":
    st.subheader("Create a New Account")
    name = st.text_input("Name")
    username = st.text_input("Username")
    email = st.text_input("Email")
    phone = st.text_input("Phone")
    password = st.text_input("Password", type="password")
    if st.button("Create Account"):
        if username in users:
            st.error("Username already exists.")
        elif not all([name, username, email, phone, password]):
            st.warning("Please fill all fields.")
        else:
            users[username] = {
                "name": name,
                "email": email,
                "phone": phone,
                "password": password
            }
            save_users()
            st.success("Account created successfully!")

elif menu == "Login":
    st.subheader("Login")
    login_user = st.text_input("Username")
    login_pass = st.text_input("Password", type="password")
    if st.button("Login"):
        if login_user in users and users[login_user]["password"] == login_pass:
            st.success(f"Welcome back, {users[login_user]['name']}!")
            st.session_state.logged_in = True
            st.session_state.current_user = login_user
        else:
            st.error("Invalid credentials.")

# ---------- MAIN APP AFTER LOGIN ----------
page = st.sidebar.selectbox("Choose a page:", ["Inventory", "Agent"])

if page == "Inventory":
    st.title("📦 Inventory Management System")

    # Sample inventory and order lists
    if "inventory" not in st.session_state:
        st.session_state.inventory = []
    if "orders" not in st.session_state:
        st.session_state.orders = []

    tabs = st.tabs(["Add", "View", "Delete", "Order", "Restock", "Save", "Stop"])

    # ---- ADD TAB ----
    with tabs[0]:
       st.header("➕ Add Item")
    
       name = st.text_input("Item Name").strip()
       quantity = st.number_input("Quantity", min_value=1, step=1)
       category = st.text_input("Category").strip()
       price = st.number_input("Price", min_value=0.0, step=0.1)
       size = st.text_input("Size (optional)").strip()
       st.caption("e.g., Small (for clothes) or 200ml (for shampoo/oil)")
       brand = st.text_input("Brand Name").strip()
       color = st.text_input("Color").strip()
       if st.button("Add Item"):
           item = {
            "name": name,
            "quantity": quantity,
            "category": category,
            "price": price,
            "size": size if size else "N/A", 
            "brand": brand,
            "color": color
        }
           if "inventory" not in st.session_state:
              st.session_state.inventory = []

           st.session_state.inventory.append(item)
           st.success(f"✅ Added {quantity} of {name} ({size if size else 'N/A'}, {color}, {brand}) to inventory.")

    with tabs[1]:
         st.header("📄 View Inventory")
         if st.session_state.inventory:
            df = pd.DataFrame(st.session_state.inventory)
            st.dataframe(df)
         else:
             st.info("Inventory is empty.")

    with tabs[2]:
        st.header("Delete Item")
        delete_index = st.number_input("Enter index to delete", min_value=1, step=1)
        if st.button("Delete"):
            try:
                removed = st.session_state.inventory.pop(delete_index - 1)
                st.success(f"Removed {removed.get('name', 'Unknown item')}")

            except IndexError:
                st.error("Invalid index.")

    with tabs[3]:
        st.header("Order Item")
        order_item = st.text_input("Order item name")
        order_qty = st.number_input("Order quantity", min_value=1, step=1)
        if st.button("Order"):
            st.session_state.orders.append({"item": order_item, "quantity": order_qty})
            st.success(f"Ordered {order_qty} x {order_item}")

    with tabs[4]:
        st.header("Restock")
        restock_item = st.text_input("Restock item name")
        restock_qty = st.number_input("Restock quantity", min_value=1, step=1)
        if st.button("Restock"):
            for entry in st.session_state.inventory:
                if entry["item"] == restock_item:
                    entry["quantity"] += restock_qty
                    st.success(f"Restocked {restock_qty} x {restock_item}")
                    break
            else:
                st.warning("Item not found in inventory.")

    with tabs[5]:
        st.header("Save Inventory")
        if st.button("Save"):
            # Replace with actual save logic
            st.success("Inventory saved.")

    with tabs[6]:
        st.header("Stop Agent")
        if st.button("Clear Session"):
            st.session_state.inventory = []
            st.session_state.orders = []
            st.success("Session cleared.")

elif page == "Agent":
    st.title("🧠 Inventory Agent Assistant")

    # Store chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    st.subheader("Ask the Assistant")
    prompt = st.text_input("Type your question here...")

    if st.button("Send"):
        if prompt.strip():
            try:
                reply = ask_assistant(prompt)
                st.session_state.chat_history.append(("user", prompt))
                st.session_state.chat_history.append(("assistant", reply))
            except Exception as e:
                st.error(f"❌ Error: {e}")
        else:
            st.warning("Please enter a prompt.")

    # Display chat history
    st.subheader("🗂️ Chat History")
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"👤 **You:** {message}")
        else:
            st.markdown(f"🤖 **Assistant:** {message}")
