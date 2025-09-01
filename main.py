import streamlit as st
from minio import Minio
from minio.error import S3Error
import json
import time
import string
import random
import io

minio_client = Minio(
    "play.min.io",
    access_key="Q3AM3UQ867SPQQA43P2F",
    secret_key="zuf+tfteSlswRu7BJ86wekitnifILbZam1KYY3TG",
    secure=True
)

BUCKET_NAME = "group-chat-app"

def initialize_bucket():
    try:
        if not minio_client.bucket_exists(BUCKET_NAME):
            minio_client.make_bucket(BUCKET_NAME)
    except S3Error as e:
        print(f"Error occurred: {e}")

def create_group():
    group_id = ''.join(random.choices(string.ascii_uppercase, k=6))
    group_data = {
        'messages': [],
        'created_at': time.time()
    }
    save_group_data(group_id, group_data)
    return group_id

def join_group(group_id):
    try:
        # Check if the group file exists
        minio_client.stat_object(BUCKET_NAME, f"{group_id}.json")
        return True
    except S3Error:
        return False

def send_message(group_id, username, message):
    group_data = get_group_data(group_id)
    group_data['messages'].append({
        'username': username,
        'message': message,
        'timestamp': time.time()
    })
    save_group_data(group_id, group_data)

def get_messages(group_id):
    group_data = get_group_data(group_id)
    return group_data.get('messages', [])

def save_group_data(group_id, data):
    json_data = json.dumps(data).encode('utf-8')
    minio_client.put_object(
        BUCKET_NAME,
        f"{group_id}.json",
        io.BytesIO(json_data),
        len(json_data)
    )

def get_group_data(group_id):
    try:
        response = minio_client.get_object(BUCKET_NAME, f"{group_id}.json")
        return json.loads(response.read().decode('utf-8'))
    except S3Error:
        return {'messages': []} 


def _send_message_callback():
    if st.session_state.message_input:
        send_message(st.session_state.group_id, st.session_state.username, st.session_state.message_input)
        st.session_state.message_input = "" 

def main():
    st.set_page_config(page_title="PingPost", page_icon="💬", layout="centered")

    st.markdown("""
<style>
.stApp {
    background-color: #1a1a1a;
    color: #e0e0e0;
    font-family: 'Segoe UI', 'Roboto', 'Helvetica', sans-serif;
}
.stTextInput > div > div > input {
    background-color: #2c2c2c;
    color: #e0e0e0;
    border-radius: 10px;
    border: 1px solid #444444;
}
.stButton > button {
    background-color: #007bff;
    color: white;
    border-radius: 10px;
    border: none;
    padding: 10px 24px;
    transition: all 0.2s ease;
    font-weight: bold;
}
.stButton > button:hover {
    background-color: #0056b3;
}
h1, h2, h3 {
    color: #f0f0f0;
}
.chat-container {
    display: flex;
    flex-direction: column;
    gap: 10px;
}
.chat-message {
    padding: 12px 18px;
    border-radius: 20px;
    margin-bottom: 5px;
    max-width: 80%;
    word-wrap: break-word;
}
.user-message {
    background-color: #007bff;
    color: white;
    align-self: flex-end;
    float: right;
    margin-left: 20%;
}
.other-message {
    background-color: #333333;
    color: #f0f0f0;
    align-self: flex-start;
    float: left;
    margin-right: 20%;
}
</style>
""", unsafe_allow_html=True)

    st.title("PingPost 💬")

    # Initialize session state variables
    if 'username_set' not in st.session_state:
        st.session_state.username_set = False
    if 'username' not in st.session_state:
        st.session_state.username = ''
    if 'group_id' not in st.session_state:
        st.session_state.group_id = ''
    if 'message_input' not in st.session_state: 
        st.session_state.message_input = ""

    if not st.session_state.username_set:
        st.write("### Welcome! Set your username to get started.")
        username_input = st.text_input("Enter your username:", key="initial_username_input")
        if st.button("Set Username", key="set_username_button"):
            if username_input:
                st.session_state.username = username_input
                st.session_state.username_set = True
                st.rerun() 
            else:
                st.warning("Please enter a username.")
    else:
        st.write(f"Hello, **{st.session_state.username}**!")

        if not st.session_state.group_id:
            st.write("---")
            st.write("### Join or Create a Chat Group")
            
            # Text input above the buttons
            group_id_input = st.text_input("Enter group code to join:", key="group_code_input")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("Join Group", key="join_group_button"):
                    if group_id_input:
                        if join_group(group_id_input):
                            st.session_state.group_id = group_id_input
                            st.success(f"Joined group: **{group_id_input}**")
                            st.rerun()
                        else:
                            st.error("Invalid group code. Please try again.")
                    else:
                        st.warning("Please enter a group code.")
            with col2:
                if st.button("Create New Group", key="create_group_button"):
                    new_group_id = create_group()
                    st.session_state.group_id = new_group_id
                    st.success(f"New group created! Your group code is: **{new_group_id}**")
                    st.rerun()
        else:
            st.write("---")
            st.write(f"## Live Chat in Group: **{st.session_state.group_id}**")

            chat_container = st.container()
            with chat_container:
                messages = get_messages(st.session_state.group_id)
                for msg in messages:
                    if msg['username'] == st.session_state.username:
                        st.markdown(f"<div class='chat-message user-message'><b>{msg['username']}:</b> {msg['message']}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div class='chat-message other-message'><b>{msg['username']}:</b> {msg['message']}</div>", unsafe_allow_html=True)

            st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

            st.text_input(
                "Type your message:",
                key="message_input",
                on_change=_send_message_callback,
                value=st.session_state.message_input 
            )

            if st.button("Send", key="send_button"):
                _send_message_callback() 

            time.sleep(1) 
            st.rerun() 

if __name__ == "__main__":
    initialize_bucket()
    main()
