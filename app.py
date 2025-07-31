
import streamlit as st
import requests
import json
import pandas as pd
import uuid
import litellm
import os

USER_FILE = "user_data.json"

# Load or initialize user data
if not os.path.exists(USER_FILE):
    with open(USER_FILE, "w") as f:
        json.dump({}, f)

with open(USER_FILE, "r") as f:
    users = json.load(f)

# Helper to save users
def save_users():
    with open(USER_FILE, "w") as f:
        json.dump(users, f)

# Session state initialization
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""

# Login or Signup Page
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
            st.error("Username already exists. Try another.")
        elif not (name and username and email and phone and password):
            st.warning("Please fill all fields.")
        else:
            users[username] = {
                "name": name,
                "email": email,
                "phone": phone,
                "password": password
            }
            save_users()
            st.success("Account created successfully! Now you can login.")

elif menu == "Login":
    st.subheader("Login")

    login_user = st.text_input("Username")
    login_pass = st.text_input("Password", type="password")

    if st.button("Login"):
        if login_user in users and users[login_user]["password"] == login_pass:
            st.success(f"Welcome back, {users[login_user]['name']}! 🎉")
            st.session_state.logged_in = True
            st.session_state.username = login_user
        else:
            st.error("Invalid username or password")

# After Login
if st.session_state.logged_in:
    st.sidebar.success(f"Logged in as {users[st.session_state.username]['name']}")
    option = st.radio("Choose a page", ["Agent", "Inventory"])

    if option == "Agent":
        with st.expander("🤖 Talk to the Agent"):
            st.write("This is where the agent chat will go.")

    elif option == "Inventory":
        with st.expander("📦 Inventory Manager"):
            st.write("This is where the inventory tools go.")
# --- Constants and Setup ---

# Load the key from Streamlit secrets
os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]
if not os.getenv("GROQ_API_KEY"):
    os.environ["GROQ_API_KEY"] = st.secrets["GROQ_API_KEY"]

GROQ_API_KEY ="GROQ_API_KEY"
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

# --- Inventory Functions ---



def delete_item(item_id):
    st.session_state.inventory = [item for item in st.session_state.inventory if item["id"] != item_id]

def save_inventory():
    df = pd.DataFrame(st.session_state.inventory)
    df.to_csv("inventory.csv", index=False)
    df.to_json("inventory.json", orient="records", indent=2)
    st.success("Inventory saved as CSV and JSON.")
import pandas as pd
import streamlit as st
import io

def save_inventory_and_download(inventory):
    if not inventory:
        st.warning("No items to save.")
        return

    df = pd.DataFrame(inventory)

    # Convert DataFrame to CSV in memory
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_data = csv_buffer.getvalue()

    # Show download button
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
    size = st.selectbox("Size", ["XS", "S", "M", "L", "XL", "XXL"])
    brand = st.text_input("Brand Name")
    color = st.text_input("Color")
    price = st.number_input("Price", min_value=0.0, format="%.2f")
    quantity = st.number_input("Quantity", min_value=1, step=1)

    if st.button("Submit Item"):
        new_item = {
            "id": str(uuid.uuid4()),
            "name": name,
            "category": category,
            "size": size,
            "brand": brand,
            "color": color,
            "price": price,
            "quantity": quantity
        }

        if "inventory" not in st.session_state:
            st.session_state.inventory = []

        st.session_state.inventory.append(new_item)
        st.success(f"✅ '{name}' added to inventory!")


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
