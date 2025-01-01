# client.py
import json

import pyperclip
from PIL import Image as PILImage
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from graph import graph

load_dotenv()

import streamlit as st

st.set_page_config(layout="wide")

# Set the title of the app
st.title("Form Generator")

# Create two columns with custom widths
col1, col2 = st.columns([6, 6])  # Adjusted columns for wider display areas

# Left column: Big input area and 'Query' button
with col1:
    st.subheader("Input Requirements")

    # Big input area for text
    user_input = st.text_area(
        "Enter your design requirements:", height=400
    )  # Large input area

    prompt = user_input

    print(prompt)

    import streamlit as st

    # Query button
    if st.button("Generate"):
        if user_input:
            # Prepare inputs for the graph

            # Specify a thread
            config = {"configurable": {"thread_id": "1"}}

            messages = [HumanMessage(content=prompt)]

            # Invoke the graph
            result = graph.invoke({"messages": messages}, config)

            # Debug: Print the result
            print(result)

            # Extract the last message content
            if result and isinstance(result, dict) and "messages" in result:
                # Ensure the messages list is not empty
                if result["messages"]:
                    last_message = result["messages"][-1]  # Select the last message
                    if hasattr(last_message, "content"):
                        full_response = last_message.content
                    else:
                        full_response = "No content in the last message."
                else:
                    full_response = "No messages found in the result."
            else:
                full_response = "No 'messages' key found in the result."

            # Save the result to session state
            st.session_state.query_result = full_response
            st.success("Query processed!")
        else:
            st.warning("Please enter some text in the input area.")

# Right column: Editable display area with 'Edit' and 'Save' buttons
with col2:
    st.subheader("Form Renderer JSON")

    # Check if query result exists in session state, otherwise set default message
    display_text = st.session_state.get("query_result", "No query result yet.")

    # A session state variable to track the editable state
    if "editable_mode" not in st.session_state:
        st.session_state.editable_mode = False  # Default is non-editable

    # Show the text area (editable if in editable mode)
    editable_display = st.text_area(
        "Edit the generated form definition:",
        value=display_text,
        height=400,
        disabled=not st.session_state.editable_mode,
    )

    st.markdown(
        """
        <style>
            .custom-container {
                width: 80%;  /* Adjust this to set the width of the entire row */
                margin: 0 auto;  /* Center the row */
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # Rest of the code remains the same (Edit, Save Locally, Save to Database buttons)
    # Buttons layout: both Edit and Save buttons together at the bottom
    button_col1, button_col2, button_col3, button_col4 = st.columns([1, 1, 1, 1])

    # Edit button (sets the editable_mode to True)
    with button_col1:
        if st.button("Edit"):
            st.session_state.editable_mode = True  # Enable editing mode

        # Add Copy to Clipboard button
    with button_col2:
        if st.button("Copy to Clipboard"):
            pyperclip.copy(editable_display)  # Copy the text area content to clipboard
            st.success("Copied to clipboard!")

    # Save button (saves the text when clicked)
    with button_col3:
        if st.button("Save Locally"):
            try:
                # Validate if the content is valid JSON
                json_data = json.loads(editable_display)

                # Save the validated JSON content to a file
                with open("../resources/form_generated.json", "w") as json_file:
                    json.dump(
                        json_data, json_file, indent=4
                    )  # Save with pretty formatting
                st.success("Valid JSON saved successfully!")

                # Disable editing after saving
                st.session_state.editable_mode = False
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON format: {e}")

# Display the graph only once after it's created
if "graph_displayed" not in st.session_state:
    st.session_state.graph_displayed = False

if not st.session_state.graph_displayed:
    # Display the graph image
    img = PILImage.open("../resources/graph.png")
    img.show()
    st.session_state.graph_displayed = True
