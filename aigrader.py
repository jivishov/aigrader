import base64
import streamlit as st
from typing import List, Tuple
from io import IOBase
from anthropic import Anthropic
from PIL import Image
import io
from fpdf import FPDF

st.set_page_config(page_title="AI Grader", page_icon="📚", layout="wide")

# def get_uploaded_images(uploaded_files: List[IOBase]) -> List[str]:
#     """Convert uploaded files to base64 encoded images"""
#     image_list = []
#     for file in uploaded_files:
#         image = Image.open(file)
#         buffered = io.BytesIO()
#         image.save(buffered, format="JPEG")
#         image_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
#         image_list.append(image_base64)
#     return image_list

# def process_uploaded_files() -> Tuple[List[IOBase], List[str]]:
#     """Process the uploaded files from session state"""
#     uploaded_files = []
#     mime_types = []
    
#     for i in range(4):
#         file = st.session_state.get(f"upload_{i+1}")
#         if file is not None:
#             mime_type = "image/jpeg" #mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
#             uploaded_files.append(file)
#             mime_types.append(mime_type)
    
#     return uploaded_files, mime_types


# def az_file_uploader(container, index):
#     tempfile = container.file_uploader(
#         f"Upload page #: {index}",
#         key=f"upload_{index}",
#         accept_multiple_files=False,
#         label_visibility="visible"
#     )
    
#     if tempfile:
#         # Create image container below the uploader
#         img_container = container.container()
#         img_container.image(tempfile, use_container_width=True)
#         img_container.divider()

def process_uploaded_pdf_files() -> List[str]:
    """Process the uploaded PDF files from session state and convert to base64"""
    pdf_base64_list = []
    
    for i in range(4):
        file = st.session_state.get(f"upload_{i+1}")
        if file is not None:
            # Read PDF file bytes
            pdf_bytes = file.read()
            # Convert to base64
            pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
            pdf_base64_list.append(pdf_base64)
    
    return pdf_base64_list

def save_and_download_pdf(claude_response, fullname):
    import re
    class PDF(FPDF):
        def __init__(self):
            super().__init__()
            self.set_auto_page_break(auto=True, margin=15)
            
        def header(self):
            self.set_font('Arial', 'B', 12)
            self.cell(0, 10, 'AI Grader Report', 0, 1, 'C')

        def footer(self):
            self.set_y(-15)
            self.set_font('Arial', 'I', 8)
            self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    # Create PDF object
    pdf = PDF()
    pdf.add_page()
    
    # Add title
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, f"Grading Report for {fullname}", 0, 1, 'L')
    pdf.ln(5)
    
    # Add content with proper encoding
    pdf.set_font('Arial', '', 12)
    # Split text into paragraphs and encode properly
    paragraphs = claude_response.split('\n')
    for para in paragraphs:
        if para.strip():
            # Replace chemical formula patterns
            para = para.replace('→', '→')  # Arrow
            para = para.replace('↔', '⇌')  # Equilibrium arrow
            # Handle subscripts
            para = re.sub(r'(\d+)', r'_\1', para)  # Convert numbers to subscripts
            
            # Encode special characters
            encoded_text = para.encode('latin-1', 'replace').decode('latin-1')
            pdf.multi_cell(0, 10, encoded_text)
            pdf.ln(5)

    # Generate safe filename
    safe_name = ''.join(c for c in fullname if c.isalnum() or c in (' ','-','_')).strip()
    pdf_output = f"grading_report_{safe_name}.pdf"
    
    try:
        # Save PDF to memory
        pdf_data = pdf.output(dest='S').encode('latin-1')
        
        # Create download button
        st.download_button(
            label="Download Grading Report",
            data=pdf_data,
            file_name=pdf_output,
            mime="application/pdf"
        )

        # Display formatted markdown with proper chemical formulas
        formatted_response = claude_response
        # Convert chemical formulas for markdown display
        formatted_response = formatted_response.replace('→', '→')
        formatted_response = formatted_response.replace('↔', '⇌')
        formatted_response = re.sub(r'(\d+)', r'<sub>\1</sub>', formatted_response)
        
        # Add markdown formatting
        formatted_response = formatted_response.replace('QUESTION #', '## Question #')
        formatted_response = formatted_response.replace('Chemistry Concepts Tested:', '### Chemistry Concepts Tested:')
        formatted_response = formatted_response.replace('Expected Solution:', '### Expected Solution:')
        formatted_response = formatted_response.replace('Student Response Analysis:', '### Student Response Analysis:')
        formatted_response = formatted_response.replace('Point Breakdown:', '### Point Breakdown:')
        formatted_response = formatted_response.replace('Total Score:', '## Total Score:')
        
        # st.markdown(formatted_response, unsafe_allow_html=True)
        
    except Exception as e:
        st.error(f"Error generating report: {str(e)}")

# def anthropic_grader_norubric_image(image_list):
#     client = Anthropic(api_key=st.secrets["CLAUDE_API_KEY"],)
#     image_prompt="""Attached are student responses to FRQ in AP Chemistry.
#     First, read a question, then provide solution. 
#     Second, read student response and evaluate it based on your solution and justify it. 
#     Third, assign a score for the response with justification.
#     After finishing whole grading provide total score with percentage.
#     And at last, provide feedback on the response and suggestions for improvement."""

#     messages = [
#         {"role": "user",
#             "content": [
#                 {
#                     "type": "image",
#                     "source": {
#                         "type": "base64",
#                         "media_type": "image/jpeg",
#                         "data": f"{image}",
#                     },
#                 }
#                 for image in image_list
#             ] + [
#                 {
#                     "type": "text",
#                     "text": image_prompt,
#                 }
#             ],
#         }
#     ]

#     claude_response = client.messages.create(
#         model="claude-3-7-sonnet-20250219",
#         max_tokens=8192,
#         messages=messages,
#     )
#     claude_response=claude_response.content[0].text

#     return claude_response


def pdf_file_uploader(container, index):
    from streamlit_pdf_viewer import pdf_viewer
    
    # Initialize session state for this uploader if not exists
    if f'pdf_ref_{index}' not in st.session_state:
        st.session_state[f'pdf_ref_{index}'] = None

    # File uploader
    tempfile = container.file_uploader(
        f"Upload your file:", #{index}",
        key=f"upload_{index}",
        type=["pdf"],
        accept_multiple_files=False,
        label_visibility="visible"
    )
    
    # Save reference when new file is uploaded
    if tempfile:
        st.session_state[f'pdf_ref_{index}'] = tempfile

    # Create container and display PDF if we have a reference
    if st.session_state[f'pdf_ref_{index}']:
        pdf_container = container.container()
        pdf_file = st.session_state[f'pdf_ref_{index}']
        
        # Display file info
        pdf_container.write(f"File: {pdf_file.name}")
        pdf_container.write(f"Size: {pdf_file.size/1024:.1f} KB")
        
        # Preview button 
        if pdf_container.button("Preview PDF", key=f"preview_{index}"):
            pdf_container.write("PDF Preview:")
            bytes_data = pdf_file.read()
            pdf_viewer(bytes_data)
            pdf_file.seek(0)  # Reset file pointer after reading
        
        pdf_container.divider()


def anthropic_grader_norubric_pdf(pdf_base64_list):
    client = Anthropic(api_key=st.secrets["CLAUDE_API_KEY"],)
    # image_prompt="""You are AP Chemistry teacher AND exam grader. 
    # You will grade student responses to Free Response Questions (FRQ) in AP Chemistry.
    # Attached are student responses to a FRQ in AP Chemistry. GRADE THE RESPONSES ALL AT ONCE. 
    # I DON'T HAVE CHANCE TO CONFIRM YOUR NEXT STEPS BECAUSE I DON'T HAVE ACCESS UI TO CONFIRM YOUR NEXT STEPS.
    # Prepare an OFFICIAL EVALUATION REPORT AT ONCE by following the TASKS below.  
    # YOUR TASKS AND OUTPUT FORMAT FOR EACH QUESTION TO ENSURE TRANSPARENT AND FAIR GRADING:
    # 1. TRANSCRIBE/OCR (!) a question, with all its subquestions (e.g. a, b, c or i, ii, iii, etc) then provide their individual solution. If the question has image then analyze image. 
    # 2. TRANSCRIBE/OCR (!) student response with all its subanswers to ensure TRANSPARENT AND FAIR GRADING. If the student responded on an image per requirement then evaluate their answer to be fair. 
    # 3. Evaluate student response based on your solution and justify it. 
    # 4. Assign a score for the response with justification.
    # 5. After finishing reading and grading EVERY PAGE AND EVERY QUESTION provide total score with percentage.
    # 6. Provide feedback on the response and suggestions for improvement.
    # Complete grading for all pages and questions before submitting the final grade.
    # DO NOT ASK TO CONTINUE GRADING AFTER EACH QUESTION, JUST CONTINUE GRADING UNTIL YOU FINISH ALL QUESTIONS.
    # REMEMBER: IF YOU DON'T TRANSCRIBE ALL QUESTIONS AND ANSWERS YOUR GRADING WILL ACCEPTED AS AND WILL BE INCOMPLETE, UNFAIR AND INACCURATE!"""
    image_prompt="""You are an experienced AP Chemistry teacher and certified AP exam grader with extensive experience in evaluating student responses to Free Response Questions (FRQs). 
    Your task is to provide comprehensive evaluation following the College Board's AP Chemistry scoring guidelines.

    EVALUATION PROTOCOL:

1. Chemistry Question Analysis
   A. For Each Question/Subpart:
      - Transcribe question text exactly
      - Identify chemistry concepts being tested:
        * Chemical equations/balancing
        * Stoichiometry
        * Equilibrium
        * Thermodynamics
        * Acid-base chemistry
        * Electrochemistry
        * Kinetics
        * Molecular structure
      - Note required mathematical calculations
      - Document specific point values per component
   
   B. For Visual Elements:
      - Analyze chemical equations
      - Interpret graphs/charts (pH curves, rate laws, etc.)
      - Evaluate molecular diagrams
      - Assess particulate-level drawings

2. Student Response Analysis
   A. Written Components:
      - Transcribe all chemical equations
      - Document mathematical work step-by-step
      - Note chemical terminology usage
      - Record unit conversions
      - Identify significant figures handling

   B. Visual Components:
      - Evaluate chemical diagrams/drawings
      - Assess graph interpretations
      - Check molecular representations
      - Note particle-level drawings

3. Chemistry-Specific Scoring
   Award points for:
   - Correct chemical equations (1 point typically)
   - Proper stoichiometric relationships
   - Accurate calculations with units
   - Valid chemical reasoning
   - Correct significant figures
   - Proper ion charges
   - Phase labels (s, l, g, aq)
   - Balanced equations
   - Correct mathematical setup even with calculation errors

   Deduct points for:
   - Incorrect chemical formulas
   - Wrong ion charges
   - Missing phase labels
   - Unbalanced equations
   - Wrong stoichiometric ratios
   - Missing units
   - Fundamental chemistry misconceptions

4. Documentation Format. Output for a Streamlit page.

AP Chemistry Grading Report: <Title_on_the_student_page> # HTML h3 tag level markdown

Question #[X]:  # HTML h5 tag level markdown
Original Question: [Exact transcription]

Chemistry Concepts Tested: # HTML h5 tag level markdown
- [List specific concepts]
- [Note required skills]

Expected Solution:  # HTML h5 tag level markdown
[Complete solution with:
- Balanced equations
- Step-by-step calculations
- Units and significant figures
- Alternative valid approaches]

Student Response Analysis:  # HTML h5 tag level markdown
A. Chemical Equations:
   - Correctness of formulas
   - Balance check
   - Phase labels
   - Ion charges

B. Calculations:
   - Mathematical setup
   - Unit conversions
   - Significant figures
   - Final answer accuracy

C. Conceptual Understanding:
   - Chemical reasoning
   - Terminology usage
   - Process explanation

Point Breakdown:  # HTML h5 tag level markdown
[Subpart]: [Points earned]/[Points possible]
- [Specific justification for each point]

5. Comprehensive Chemistry Feedback # HTML h5 tag level markdown
   A. Strengths:  # HTML h5 tag level markdown
      - Note correct chemical principles
      - Highlight proper equation writing
      - Acknowledge valid problem-solving

   B. Areas for Improvement: # HTML h5 tag level markdown
      - Identify specific chemistry concepts needing review
      - Point out equation balancing issues
      - Note unit conversion errors
      - Address significant figure usage
      - Suggest practice with specific types of problems

   C. Study Recommendations: # HTML h5 tag level markdown
      - Specific textbook chapters
      - Practice problem types
      - Lab concepts to review
      - Chemical equation writing practice

Total Score: [X]/[Y] ([Z]%) # HTML h5 tag level markdown

Chemistry Concept Mastery Summary: # HTML h5 tag level markdown
[List each major concept and level of understanding demonstrated]

SPECIAL INSTRUCTIONS:
1. Grade all questions and subparts at once without asking for confirmation
2. Maintain AP Chemistry standards for equation writing and calculations
3. Consider multiple valid approaches to solutions
4. Evaluate mathematical and conceptual components separately
5. Check for consistency in chemical formula writing
6. Note proper use of significant figures throughout
7. Assess understanding of underlying chemical principles
8. Look for patterns in conceptual misunderstandings
Complete grading for all pages and questions before submitting the final grade.
DO NOT ASK TO CONTINUE GRADING AFTER EACH QUESTION, JUST CONTINUE GRADING UNTIL YOU FINISH ALL QUESTIONS.
REMEMBER: IF YOU DON'T TRANSCRIBE ALL QUESTIONS AND ANSWERS YOUR GRADING WILL ACCEPTED AS AND WILL BE INCOMPLETE, UNFAIR AND INACCURATE!
"""



    # Create content list with all PDFs
    content = []
    for pdf_base64 in pdf_base64_list:
        content.append({
            "type": "document",
            "source": {
                "type": "base64",
                "media_type": "application/pdf",
                "data": pdf_base64
            }
        })
    
    # Add the prompt text
    content.append({
        "type": "text",
        "text": image_prompt
    })

    messages = [
        {
            "role": "user",
            "content": content
        }
    ]

    # claude_response = client.messages.create(
    #     model="claude-3-7-sonnet-20250219",
    #     max_tokens=8192,
    #     messages=messages,
    # )
    full_response = ""
    response_container = st.empty()
    with client.messages.stream(
    max_tokens=8192,
    messages=messages,
    model="claude-3-7-sonnet-20250219",
        ) as stream:
        for text in stream.text_stream:
            full_response+=text
            response_container.empty()
            response_container.write(full_response)

    return  full_response #claude_response.content[0].text



with st.container(key="main_form"):
    # Upload Section
    # with st.container(key="fullname_section"):
    #     st.write("Enter your full name")
    #     fullname = st.text_input("Full Name", key="fullname_input")

    with st.container(key="upload_section"):
        st.write("##### Upload your pdf file here")
        # Create two rows of containers with fixed height
        row1 = st.columns(1)
        #row2 = st.columns(3)
        
        # Create fixed-height tiles for each uploader
        for i, col in enumerate(row1):
            tile = col.container(height=300)  # Adjust height as needed
            pdf_file_uploader(tile, i+1)

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
        with st.spinner("Grading your papers..."):
            #uploaded_files, mime_types = process_uploaded_pdf_files()
            pdf_list = process_uploaded_pdf_files()

            if not pdf_list: #uploaded_files:
                st.toast("#### Please upload a pdf file with scanned papers of a student start grading.",icon=":material/warning:")
                st.stop()
            try:
                #image_list = get_uploaded_images(uploaded_files)
                
                claude_response = anthropic_grader_norubric_pdf(pdf_list)
            
                save_and_download_pdf(claude_response, fullname)
                
            except Exception as e:
                st.error(f"An error occurred: {e}")
                st.stop()
        