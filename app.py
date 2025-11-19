import streamlit as st
import os
from io import BytesIO
import zipfile
from PIL import Image, ImageOps, ImageFilter

# PDF Libraries
from PyPDF2 import PdfReader, PdfWriter

# PPT Libraries
from pptx import Presentation

# PDF to Image (Requires Poppler System Dependency)
try:
    from pdf2image import convert_from_bytes
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False
except Exception:
    HAS_PDF2IMAGE = False

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="iLoveDocs - Free Document Tools",
    page_icon="❤",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. SESSION STATE MANAGEMENT ---
# This handles the "Single Page App" feel without reloading the script from scratch
if 'current_tool' not in st.session_state:
    st.session_state['current_tool'] = "Home"

def navigate_to(tool_name):
    st.session_state['current_tool'] = tool_name

def go_home():
    st.session_state['current_tool'] = "Home"

# --- 3. CUSTOM CSS (BRANDING) ---
st.markdown("""
<style>
    /* Main Background */
    .stApp {
        background-color: #f3f4f6;
    }
    
    /* Red Navbar */
    .nav-container {
        background-color: #E53935;
        padding: 1rem 2rem;
        color: white;
        border-radius: 0 0 10px 10px;
        margin-bottom: 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Tool Cards (Buttons) */
    div.stButton > button {
        background-color: white;
        color: #333;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 25px 10px;
        height: 100%;
        width: 100%;
        transition: all 0.3s ease;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        min-height: 150px;
    }
    
    /* Hover Effect for Cards */
    div.stButton > button:hover {
        border-color: #E53935;
        transform: translateY(-5px);
        box-shadow: 0 10px 20px rgba(229, 57, 53, 0.15);
        color: #E53935;
    }
    
    /* Paragraph text inside buttons (description) */
    div.stButton > button p {
        font-size: 0.9rem;
        color: #666;
        margin-top: 5px;
    }
    
    /* Action Buttons (Upload/Download) - Make them Red */
    div.stDownloadButton > button, div.stFormSubmitButton > button {
        background-color: #E53935 !important;
        color: white !important;
        border: none !important;
        font-weight: bold;
        width: 100%;
    }

    /* Back Button */
    .back-btn {
        background: none;
        border: 1px solid white;
        color: white;
        padding: 5px 15px;
        border-radius: 5px;
        cursor: pointer;
        text-decoration: none;
    }

    /* Hide Default Streamlit Sidebar elements */
    [data-testid="stSidebarNav"] {display: none;}
</style>
""", unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
def create_zip(files_dict, zip_name):
    """Packs a dictionary of filename:bytes into a zip file"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, data in files_dict.items():
            zip_file.writestr(file_name, data)
    return zip_buffer.getvalue()

# --- 5. UI RENDERERS ---

def render_header():
    """Renders the Red Navbar with Back button logic"""
    col1, col2 = st.columns([1, 10])
    with col1:
        if st.session_state['current_tool'] != "Home":
            if st.button("⬅ Home", key="home_btn"):
                go_home()
                st.rerun()
    with col2:
        tool_display = st.session_state['current_tool'] if st.session_state['current_tool'] != "Home" else "Every tool you need"
        st.markdown(f"<div style='font-size:2rem; font-weight:800; color:#E53935;'>❤ iLoveDocs <span style='font-size:1.2rem; color:#666; font-weight:400;'>| {tool_display}</span></div>", unsafe_allow_html=True)
    st.markdown("---")

def render_home():
    """Renders the Dashboard Grid"""
    st.markdown("<h3 style='text-align: center; color: #555; margin-bottom: 40px;'>Select a tool to begin processing your documents</h3>", unsafe_allow_html=True)
    
    # Tool Definitions
    tools = [
        {"name": "Merge PDF", "icon": "🔗", "desc": "Combine PDFs in the order you want.", "id": "merge_pdf"},
        {"name": "Split PDF", "icon": "✂️", "desc": "Separate one page or a whole set.", "id": "split_pdf"},
        {"name": "PDF to JPG", "icon": "🖼️", "desc": "Convert each PDF page to an image.", "id": "pdf_to_img"},
        {"name": "PDF Text", "icon": "📝", "desc": "Extract text and data from PDF.", "id": "pdf_text"},
        {"name": "Image Editor", "icon": "🎨", "desc": "Crop, resize and apply filters.", "id": "img_editor"},
        {"name": "Img Convert", "icon": "🔄", "desc": "Convert to PNG, JPG, BMP, etc.", "id": "img_convert"},
        {"name": "JPG to PDF", "icon": "📑", "desc": "Turn your images into a PDF.", "id": "img_to_pdf"},
        {"name": "Merge PPTX", "icon": "📊", "desc": "Combine PowerPoint slides.", "id": "merge_pptx"},
        {"name": "PPTX Text", "icon": "📄", "desc": "Read text from presentations.", "id": "pptx_text"},
    ]

    # Dynamic Grid Layout (3 columns)
    cols = st.columns(3)
    for i, tool in enumerate(tools):
        with cols[i % 3]:
            # Button content with icon and text
            label = f"{tool['icon']}\n\n**{tool['name']}**\n\n{tool['desc']}"
            if st.button(label, key=tool['id'], use_container_width=True):
                navigate_to(tool['name'])
                st.rerun()

# --- 6. TOOL LOGIC ---

def tool_merge_pdf():
    st.info("Select multiple PDF files to combine them into one document.")
    uploaded_pdfs = st.file_uploader("Upload PDFs", type="pdf", accept_multiple_files=True)
    
    if uploaded_pdfs:
        st.success(f"✅ {len(uploaded_pdfs)} files selected")
        if st.button("Merge PDFs"):
            with st.spinner("Merging..."):
                merger = PdfWriter()
                for pdf in uploaded_pdfs:
                    merger.append(pdf)
                output = BytesIO()
                merger.write(output)
                st.balloons()
                st.download_button("Download Merged PDF", output.getvalue(), "ilovedocs_merged.pdf", "application/pdf")

def tool_split_pdf():
    st.info("Split a PDF into single pages or extract specific pages.")
    uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_pdf:
        reader = PdfReader(uploaded_pdf)
        st.write(f"**Total Pages:** {len(reader.pages)}")
        
        mode = st.radio("Split Mode", ["Extract Specific Page", "Split All Pages"])
        
        if mode == "Extract Specific Page":
            page_num = st.number_input("Page Number", 1, len(reader.pages), 1)
            if st.button("Extract Page"):
                writer = PdfWriter()
                writer.add_page(reader.pages[page_num-1])
                out = BytesIO()
                writer.write(out)
                st.download_button(f"Download Page {page_num}", out.getvalue(), f"page_{page_num}.pdf", "application/pdf")
        else:
            if st.button("Split All & Zip"):
                files = {}
                for i in range(len(reader.pages)):
                    w = PdfWriter()
                    w.add_page(reader.pages[i])
                    o = BytesIO()
                    w.write(o)
                    files[f"page_{i+1}.pdf"] = o.getvalue()
                zip_data = create_zip(files, "split_files.zip")
                st.download_button("Download ZIP", zip_data, "split_files.zip", "application/zip")

def tool_pdf_to_img():
    if not HAS_PDF2IMAGE:
        st.error("⚠️ This feature requires the 'Poppler' system library, which is not installed.")
        st.write("If running locally: Install Poppler. If on Cloud: Add `poppler-utils` to packages.txt.")
        return
        
    st.info("Convert PDF pages into high-quality JPG images.")
    uploaded_pdf = st.file_uploader("Upload PDF", type="pdf")
    if uploaded_pdf:
        if st.button("Convert to JPG"):
            with st.spinner("Converting..."):
                try:
                    images = convert_from_bytes(uploaded_pdf.read())
                    files = {}
                    for i, img in enumerate(images):
                        b = BytesIO()
                        img.save(b, format="JPEG")
                        files[f"page_{i+1}.jpg"] = b.getvalue()
                        if i < 3: st.image(img, width=200, caption=f"Page {i+1}")
                    
                    zip_data = create_zip(files, "pdf_images.zip")
                    st.success(f"Converted {len(images)} pages.")
                    st.download_button("Download Images (ZIP)", zip_data, "pdf_images.zip", "application/zip")
                except Exception as e:
                    st.error(f"Error: {e}")

def tool_img_editor():
    st.info("Upload an image to rotate, resize, or apply filters.")
    uploaded = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg"])
    if uploaded:
        img = Image.open(uploaded)
        st.image(img, width=300, caption="Original")
        
        with st.form("edit_form"):
            c1, c2 = st.columns(2)
            with c1:
                angle = st.slider("Rotate", 0, 360, 0)
                filter_t = st.selectbox("Filter", ["None", "Grayscale", "Blur", "Detail", "Contour"])
            with c2:
                width = st.number_input("Width (px)", value=img.width)
                height = st.number_input("Height (px)", value=img.height)
            
            resize = st.checkbox("Apply Resize")
            submitted = st.form_submit_button("Apply & Process")
            
        if submitted:
            processed = img.copy()
            if resize:
                processed = processed.resize((int(width), int(height)))
            if angle != 0:
                processed = processed.rotate(angle, expand=True)
            
            if filter_t == "Grayscale": processed = ImageOps.grayscale(processed)
            elif filter_t == "Blur": processed = processed.filter(ImageFilter.BLUR)
            elif filter_t == "Detail": processed = processed.filter(ImageFilter.DETAIL)
            elif filter_t == "Contour": processed = processed.filter(ImageFilter.CONTOUR)
            
            st.image(processed, width=300, caption="Result")
            b = BytesIO()
            processed.save(b, format="PNG")
            st.download_button("Download Result", b.getvalue(), "edited_image.png", "image/png")

def tool_img_convert():
    st.info("Convert image formats (e.g., PNG to JPG, WEBP to PNG).")
    uploaded = st.file_uploader("Upload Image", type=["png", "jpg", "tiff", "bmp", "webp"])
    if uploaded:
        img = Image.open(uploaded)
        st.write(f"Original Format: **{img.format}**")
        target = st.selectbox("Convert to", ["PNG", "JPEG", "PDF", "WEBP", "ICO"])
        
        if st.button("Convert"):
            b = BytesIO()
            img_s = img.copy()
            # JPEGs don't support transparency (RGBA), convert to RGB
            if target == "JPEG" and img_s.mode in ("RGBA", "P"): 
                img_s = img_s.convert("RGB")
            
            img_s.save(b, format=target)
            mime = "application/pdf" if target == "PDF" else f"image/{target.lower()}"
            st.download_button(f"Download {target}", b.getvalue(), f"converted.{target.lower()}", mime)

def tool_img_to_pdf():
    st.info("Select multiple images to create a single PDF document.")
    uploads = st.file_uploader("Select Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
    if uploads:
        if st.button("Generate PDF"):
            imgs = []
            for f in uploads:
                i = Image.open(f)
                if i.mode == "RGBA": i = i.convert("RGB")
                imgs.append(i)
            
            if imgs:
                b = BytesIO()
                imgs[0].save(b, "PDF", save_all=True, append_images=imgs[1:])
                st.success("PDF generated successfully!")
                st.download_button("Download PDF", b.getvalue(), "images_merged.pdf", "application/pdf")

def tool_merge_pptx():
    st.info("Merge slides from multiple PowerPoint files. (Note: Complex formatting may vary)")
    uploads = st.file_uploader("Select PPTX files", type="pptx", accept_multiple_files=True)
    if uploads:
        if st.button("Merge Presentations"):
            try:
                out_prs = Presentation()
                # Clear the default blank slide
                xml = out_prs.slides._sldIdLst
                sl = list(xml)
                xml.remove(sl[0])
                
                for f in uploads:
                    in_prs = Presentation(f)
                    for s in in_prs.slides:
                        # Create a blank slide in output
                        layout = out_prs.slide_layouts[6] # 6 is usually blank
                        dest = out_prs.slides.add_slide(layout)
                        # Simple Text Box Copying (Robust method)
                        for sh in s.shapes:
                            if hasattr(sh, "text"):
                                try:
                                    tb = dest.shapes.add_textbox(sh.left, sh.top, sh.width, sh.height)
                                    tb.text_frame.text = sh.text
                                except: pass
                b = BytesIO()
                out_prs.save(b)
                st.success("Merged!")
                st.download_button("Download PPTX", b.getvalue(), "merged.pptx", "application/vnd.openxmlformats-officedocument.presentationml.presentation")
            except Exception as e:
                st.error(f"Merge Error: {e}")

def tool_pdf_text():
    st.info("Extract raw text and metadata from PDF.")
    f = st.file_uploader("Select PDF", type="pdf")
    if f:
        r = PdfReader(f)
        st.write(f"**Metadata:** {r.metadata}")
        if st.button("Extract Text"):
            text = ""
            for i, p in enumerate(r.pages):
                text += f"--- Page {i+1} ---\n{p.extract_text()}\n\n"
            st.text_area("Content", text, height=300)
            st.download_button("Download .txt", text, "extracted.txt", "text/plain")

def tool_pptx_text():
    st.info("Extract raw text from PowerPoint slides.")
    f = st.file_uploader("Select PPTX", type="pptx")
    if f:
        if st.button("Extract Text"):
            p = Presentation(f)
            text = []
            for i, s in enumerate(p.slides):
                t = [sh.text for sh in s.shapes if hasattr(sh, "text")]
                text.append(f"--- Slide {i+1} ---\n" + "\n".join(t))
            full = "\n\n".join(text)
            st.text_area("Content", full, height=300)
            st.download_button("Download .txt", full, "slides.txt", "text/plain")

# --- 7. MAIN APP ROUTING ---

render_header()

# Dispatcher
tool = st.session_state['current_tool']

if tool == "Home":
    render_home()
elif tool == "Merge PDF":
    tool_merge_pdf()
elif tool == "Split PDF":
    tool_split_pdf()
elif tool == "PDF to JPG":
    tool_pdf_to_img()
elif tool == "PDF Text":
    tool_pdf_text()
elif tool == "Image Editor":
    tool_img_editor()
elif tool == "Img Convert":
    tool_img_convert()
elif tool == "JPG to PDF":
    tool_img_to_pdf()
elif tool == "Merge PPTX":
    tool_merge_pptx()
elif tool == "PPTX Text":
    tool_pptx_text()

# Footer
st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8rem;'>© 2024 iLoveDocs Clone | Securely processed in your browser session. No files are stored.</div>", unsafe_allow_html=True)
