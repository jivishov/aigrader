import base64
import streamlit as st
from typing import List, Tuple
from io import IOBase
from anthropic import Anthropic
from PIL import Image
import io


st.set_page_config(page_title="AI Grader", page_icon="📚", layout="wide")



def get_uploaded_images(uploaded_files: List[IOBase]) -> List[str]:
    """Convert uploaded files to base64 encoded images"""
    image_list = []
    for file in uploaded_files:
        image = Image.open(file)
        buffered = io.BytesIO()
        image.save(buffered, format="JPEG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        image_list.append(image_base64)
    return image_list

def process_uploaded_files() -> Tuple[List[IOBase], List[str]]:
    """Process the uploaded files from session state"""
    uploaded_files = []
    mime_types = []
    
    for i in range(4):
        file = st.session_state.get(f"upload_{i+1}")
        if file is not None:
            mime_type = "image/jpeg" #mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
            uploaded_files.append(file)
            mime_types.append(mime_type)
    
    return uploaded_files, mime_types

def az_file_uploader(container, index):
    tempfile = container.file_uploader(
        f"Upload page #: {index}",
        key=f"upload_{index}",
        accept_multiple_files=False,
        label_visibility="visible"
    )
    
    if tempfile:
        # Create image container below the uploader
        img_container = container.container()
        img_container.image(tempfile, use_container_width=True)
        img_container.divider()

def anthropic_grader_norubric(image_list):
    client = Anthropic(api_key=st.secrets["CLAUDE_API_KEY"],)
    image_prompt="Attached are student responses to FRQ in AP Chemistry. Please evaluate the responses, assign a score based on the rubric with justification."

    messages = [
        {"role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": "image/jpeg",
                        "data": f"{image}",
                    },
                }
                for image in image_list
            ] + [
                {
                    "type": "text",
                    "text": image_prompt,
                }
            ],
        }
    ]

    claude_response = client.messages.create(
        model="claude-3-5-sonnet-20241022",
        max_tokens=8192,
        messages=messages,
    )
    claude_response=claude_response.content[0].text

    return claude_response

with st.container(key="main_form"):
    # Upload Section
    with st.container(key="fullname_section"):
        st.subheader("Enter your full name")
        fullname = st.text_input("Full Name", key="fullname_input")

    with st.container(key="upload_section"):
        st.subheader("Upload your images here")
        # Create two rows of containers with fixed height
        row1 = st.columns(4)
        #row2 = st.columns(3)
        
        # Create fixed-height tiles for each uploader
        for i, col in enumerate(row1):
            tile = col.container(height=300)  # Adjust height as needed
            az_file_uploader(tile, i+1)
    # Analyze Button
    col1, col2, col3 = st.columns([1, 3, 1])
    with col2:
        grading_clicked = st.button(
            "Grade my papers", 
            icon=":material/grading:", 
            type="primary",
            key="grading_button",
            use_container_width=True
        )
    
    if grading_clicked:
        uploaded_files, mime_types = process_uploaded_files()
        if not uploaded_files:
            st.toast("#### Please upload at least one image of your paper to start grading.",icon=":material/warning:")
            st.stop()
        try:
            image_list = get_uploaded_images(uploaded_files)
            claude_response = anthropic_grader_norubric(image_list)
            st.write(claude_response)
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.stop()
        