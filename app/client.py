# client.py
import streamlit as st
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from app.llm_compiler.agent import query_agent

load_dotenv()

# Set up the Streamlit app
st.set_page_config(layout="wide")
st.title("Personal Assistant Chat")

# Initialize session state for chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []


# Function to handle the chat interaction
def handle_chat(prompt):
    if prompt:
        # Add user message to chat history
        st.session_state.chat_history.append({"role": "user", "content": prompt})

        # Prepare inputs for the agent
        config = {"configurable": {"thread_id": "1"}}
        messages = [HumanMessage(content=prompt)]

        # Invoke the agent
        result = query_agent(query=prompt)

        # Extract the agent's response
        if result and isinstance(result, dict) and "messages" in result:
            if result["messages"]:
                last_message = result["messages"][-1]  # Select the last message
                if hasattr(last_message, "content"):
                    full_response = last_message.content
                else:
                    full_response = "I'm sorry, I couldn't process that. Can you please rephrase?"
            else:
                full_response = "I'm sorry, I didn't get a response. Can you try again?"
        else:
            full_response = "I'm sorry, something went wrong. Please try again."

        # Add agent response to chat history
        st.session_state.chat_history.append({"role": "assistant", "content": full_response})


# Display the chat interface
st.subheader("Chat with Your Personal Assistant")

# Display chat history
for message in st.session_state.chat_history:
    if message["role"] == "user":
        st.markdown(f"**You:** {message['content']}")
    else:
        st.markdown(f"**Assistant:** {message['content']}")

# Input area for new messages
user_input = st.text_input("Type your message here:", key="input", placeholder="Ask me anything...")

# Send button
if st.button("Send"):
    handle_chat(user_input)
    st.experimental_rerun()

# Optional: Add a reset button to clear chat history
if st.button("Reset Chat"):
    st.session_state.chat_history = []
    st.experimental_rerun()

# Optional: Add a greeting from the assistant if the chat is empty
if not st.session_state.chat_history:
    st.markdown("**Assistant:** Hi! I'm your personal assistant. How can I help you today?")
