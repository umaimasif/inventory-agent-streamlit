
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
if st.session_state.logged_in:
    page = st.sidebar.selectbox("Choose a page:", ["Inventory", "Agent"])

    if page == "Inventory":
        st.title("Inventory Management System")
        tabs = st.tabs(["Add", "View", "Delete", "Order", "Restock", "Save", "Stop"])

        # --- Add ---
        with tabs[0]:
            st.header("Add Item")
            name = st.text_input("Item Name")
            category = st.text_input("Category")
            size = st.selectbox("Size", ["XS", "S", "M", "L", "XL", "XXL"])
            brand = st.text_input("Brand Name")
            color = st.text_input("Color")
            price = st.number_input("Price", min_value=0.0, format="%.2f")
            quantity = st.number_input("Quantity", min_value=1, step=1)
            if st.button("Submit Item"):
                item = {
                    "id": str(uuid.uuid4()),
                    "name": name,
                    "category": category,
                    "size": size,
                    "brand": brand,
                    "color": color,
                    "price": price,
                    "quantity": quantity
                }
                st.session_state.inventory.append(item)
                st.success(f"Added {name} to inventory.")

        # --- View ---
        with tabs[1]:
            st.header("Current Inventory")
            if st.session_state.inventory:
                st.dataframe(pd.DataFrame(st.session_state.inventory))
            else:
                st.info("Inventory is empty.")

        # --- Delete ---
        with tabs[2]:
            st.header("Delete Item")
            for item in st.session_state.inventory:
                if st.button(f"Delete {item['name']}"):
                    delete_item(item["id"])
                    st.success(f"Deleted {item['name']}")

        # --- Order ---
        with tabs[3]:
            st.header("Place Order")
            ids = [item["id"] for item in st.session_state.inventory if item["quantity"] > 0]
            labels = [f"{item['name']} ({item['quantity']} left)" for item in st.session_state.inventory if item["quantity"] > 0]
            selected_ids = st.multiselect("Select items to order", ids, format_func=lambda x: dict(zip(ids, labels))[x])
            if st.button("Place Order"):
                place_order(selected_ids)

        # --- Restock ---
        with tabs[4]:
            st.header("Restock Items")
            for item in st.session_state.inventory:
                qty = st.number_input(f"Restock for {item['name']}", min_value=0, key=item['id'])
                if st.button(f"Restock {item['name']}"):
                    restock_item(item["id"], qty)
                    st.success(f"Restocked {item['name']} by {qty}")

        # --- Save ---
        with tabs[5]:
            st.header("Save Inventory")
            if st.button("Save Inventory"):
                save_inventory_and_download(st.session_state.inventory)

        # --- Stop ---
        with tabs[6]:
            st.header("Stop Agent")
            if st.button("Clear Session"):
                st.session_state.inventory = []
                st.session_state.orders = []
                st.success("Session cleared.")

    elif page == "Agent":
       st.title("Inventory Agent Assistant 💬")
       st.sidebar.header("💬 Assistant")

    # Store chat history in session state
       if "chat_history" not in st.session_state:
           st.session_state.chat_history = []

       prompt = st.sidebar.text_input("Ask something...")

       if st.sidebar.button("Send"):
           if prompt.strip():
              try:
                 reply = ask_assistant(prompt)
                 st.session_state.chat_history.append(("user", prompt))
                 st.session_state.chat_history.append(("assistant", reply))
              except Exception as e:
                 st.sidebar.error(f"❌ Error: {e}")
           else:
              st.sidebar.warning("Please enter a prompt.")

    # Display chat history
       st.subheader("Chat History")
       for role, message in st.session_state.chat_history:
           if role == "user":
               st.markdown(f"👤 **You:** {message}")
           else:
              st.markdown(f"🤖 **Assistant:** {message}")
