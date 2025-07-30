import streamlit as st

st.set_page_config(page_title="Inventory Agent App", page_icon="📦")

st.title("Inventory Agent App 🧠📦")
st.write("Welcome to your inventory agent.")

# Temporary static interface – update later with real logic
st.subheader("Commands")
user_input = st.text_input("Enter your command (e.g., 'add 5 red shirts'):")

if st.button("Submit"):
    st.success(f"✅ Command received: '{user_input}'")
