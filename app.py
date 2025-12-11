import streamlit as st
import os
from io import BytesIO
import zipfile
from PIL import Image, ImageOps, ImageFilter

# PDF Libraries
from PyPDF2 import PdfReader, PdfWriter

# PPT Libraries
from pptx import Presentation

# PDF to Image
try:
    from pdf2image import convert_from_bytes
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False
except Exception:
    HAS_PDF2IMAGE = False

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(
    page_title="DocMint - Pro Workspace",
    page_icon="🍃",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. SESSION STATE ---
if 'current_tool' not in st.session_state:
    st.session_state['current_tool'] = "Resize Image" # Default to the coolest tool

# --- 3. CUSTOM CSS (Layout & Styling) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #1e293b;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #f8fafc;
        border-right: 1px solid #e2e8f0;
    }

    /* Logo Area in Sidebar */
    .sidebar-logo {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 1rem 0;
        margin-bottom: 1rem;
        border-bottom: 1px solid #e2e8f0;
    }
    
    .sidebar-title {
        font-size: 1.5rem;
        font-weight: 800;
        color: #0f172a;
    }

    /* Custom Button Styling for Nav */
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        border: 1px solid transparent;
        background-color: transparent;
        color: #475569;
        text-align: left;
        padding: 0.5rem 1rem;
        transition: all 0.2s;
    }
    
    div.stButton > button:hover {
        background-color: #e2e8f0;
        color: #0f172a;
    }

    /* Active Tool Styling (Simulated via session state logic in python, 
       but we style the generic primary buttons here) */
    .primary-btn {
        background-color: #007AFF !important;
        color: white !important;
    }

    /* Main Area Styling */
    .block-container {
        padding-top: 2rem;
    }

    /* Preview Area Card */
    .preview-card {
        background: white;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 2rem;
        text-align: center;
        min-height: 500px;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    
    /* Control Panel Styling */
    .control-panel {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
    }
    
    /* Headers */
    h3 { font-size: 1.2rem; font-weight: 700; margin-bottom: 1rem; }
    h4 { font-size: 1rem; font-weight: 600; margin-top: 1rem; margin-bottom: 0.5rem; color: #334155; }

</style>
""", unsafe_allow_html=True)

# --- 4. HELPER FUNCTIONS ---
def create_zip(files_dict, zip_name):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, data in files_dict.items():
            zip_file.writestr(file_name, data)
    return zip_buffer.getvalue()

def get_size_format(b, factor=1024, suffix="B"):
    for unit in ["", "K", "M", "G", "T", "P"]:
        if b < factor: return f"{b:.2f} {unit}{suffix}"
        b /= factor
    return f"{b:.2f} Y{suffix}"

# --- 5. SIDEBAR NAVIGATION ---
def render_sidebar():
    with st.sidebar:
        # Logo Section
        logo_url = "https://github.com/nitesh4004/Ni30-pdflover/blob/main/docmint.png?raw=true"
        st.markdown(f"""
        <div class="sidebar-logo">
            <img src="{logo_url}" style="height: 40px; border-radius: 6px;">
            <div class="sidebar-title">DocMint</div>
        </div>
        """, unsafe_allow_html=True)

        st.caption("IMAGE TOOLS")
        if st.button("📐 Resize Image", use_container_width=True): st.session_state['current_tool'] = "Resize Image"
        if st.button("🎨 Image Editor", use_container_width=True): st.session_state['current_tool'] = "Image Editor"
        if st.button("🔄 Convert Format", use_container_width=True): st.session_state['current_tool'] = "Convert Format"
        if st.button("📑 JPG to PDF", use_container_width=True): st.session_state['current_tool'] = "JPG to PDF"

        st.write("")
        st.caption("PDF TOOLS")
        if st.button("🔗 Merge PDF", use_container_width=True): st.session_state['current_tool'] = "Merge PDF"
        if st.button("✂️ Split PDF", use_container_width=True): st.session_state['current_tool'] = "Split PDF"
        if st.button("🖼️ PDF to JPG", use_container_width=True): st.session_state['current_tool'] = "PDF to JPG"
        if st.button("📝 PDF Text", use_container_width=True): st.session_state['current_tool'] = "PDF Text"
        
        st.write("")
        st.caption("OFFICE TOOLS")
        if st.button("📊 Merge PPTX", use_container_width=True): st.session_state['current_tool'] = "Merge PPTX"

# --- 6. TOOL LOGIC (SPLIT LAYOUT) ---

def tool_resize_image():
    st.markdown(f"### 📐 {st.session_state['current_tool']}")
    
    # 2-Column Layout: Left (Controls), Right (Preview)
    col_controls, col_preview = st.columns([1, 2], gap="large")
    
    with col_controls:
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        st.markdown("#### 1. Upload")
        uploaded = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp"], key="resize_upl")
        
        img = None
        if uploaded:
            img = Image.open(uploaded)
            st.success(f"Loaded: {img.width}x{img.height} px")
            
            st.markdown("#### 2. Dimensions")
            unit = st.radio("Unit", ["Pixels", "Percent"], horizontal=True)
            lock = st.checkbox("Lock Aspect Ratio", value=True)
            
            if unit == "Pixels":
                w = st.number_input("Width", value=img.width, step=1)
                if lock:
                    ratio = img.height / img.width
                    h = int(w * ratio)
                    st.number_input("Height", value=h, disabled=True)
                else:
                    h = st.number_input("Height", value=img.height, step=1)
            else:
                pct = st.slider("Percentage", 1, 200, 100)
                w = int(img.width * (pct/100))
                h = int(img.height * (pct/100))
                st.caption(f"New Output: {w} x {h} px")

            st.markdown("#### 3. Export Settings")
            fmt = st.selectbox("Format", ["JPG", "PNG", "WEBP"], index=0)
            qual = st.slider("Quality", 10, 100, 90)
            dpi = st.number_input("DPI", 72, 600, 72)
            
            process_btn = st.button("⚡ Process Image", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_preview:
        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
        if img:
            st.image(img, caption="Original Preview", use_container_width=False, width=400)
            
            if 'process_btn' in locals() and process_btn:
                # Processing Logic
                new_img = img.resize((w, h), Image.Resampling.LANCZOS)
                b = BytesIO()
                save_fmt = "JPEG" if fmt == "JPG" else fmt
                if save_fmt == "JPEG" and new_img.mode in ("RGBA", "P"):
                    new_img = new_img.convert("RGB")
                
                new_img.save(b, format=save_fmt, dpi=(dpi, dpi), quality=qual)
                
                st.markdown("---")
                st.image(new_img, caption=f"Result: {w}x{h} px", use_container_width=False, width=400)
                st.download_button(
                    f"⬇️ Download {fmt}", 
                    data=b.getvalue(), 
                    file_name=f"resized.{save_fmt.lower()}", 
                    mime=f"image/{save_fmt.lower()}", 
                    type="primary"
                )
        else:
            st.info("Upload an image on the left to see the preview here.")
        st.markdown('</div>', unsafe_allow_html=True)

def tool_img_editor():
    st.markdown(f"### 🎨 {st.session_state['current_tool']}")
    col_controls, col_preview = st.columns([1, 2], gap="large")
    
    with col_controls:
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        uploaded = st.file_uploader("Upload", type=["png", "jpg"], key="edit_upl")
        
        img = None
        if uploaded:
            img = Image.open(uploaded)
            st.markdown("#### Adjustments")
            angle = st.slider("Rotation", 0, 360, 0)
            filt = st.selectbox("Filter", ["None", "Grayscale", "Blur", "Sharpen", "Contour"])
            apply_btn = st.button("Apply Filters", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

    with col_preview:
        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
        if img:
            # Live Preview Logic
            processed = img.copy()
            if angle: processed = processed.rotate(angle, expand=True)
            if filt == "Grayscale": processed = ImageOps.grayscale(processed)
            elif filt == "Blur": processed = processed.filter(ImageFilter.BLUR)
            elif filt == "Sharpen": processed = processed.filter(ImageFilter.SHARPEN)
            elif filt == "Contour": processed = processed.filter(ImageFilter.CONTOUR)
            
            st.image(processed, caption="Live Preview", use_container_width=False, width=450)
            
            b = BytesIO()
            fmt = img.format if img.format else "PNG"
            processed.save(b, format=fmt)
            st.download_button("⬇️ Download Result", b.getvalue(), f"edited.{fmt.lower()}", f"image/{fmt.lower()}")
        else:
            st.write("Waiting for image...")
        st.markdown('</div>', unsafe_allow_html=True)

def tool_merge_pdf():
    st.markdown(f"### 🔗 {st.session_state['current_tool']}")
    col_controls, col_preview = st.columns([1, 2], gap="large")
    
    with col_controls:
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        files = st.file_uploader("Select PDFs", type="pdf", accept_multiple_files=True)
        file_map = {}
        if files:
            file_map = {f.name: f for f in files}
            st.markdown("#### Order Files")
            order = st.multiselect("Drag to reorder", list(file_map.keys()), default=list(file_map.keys()))
            merge_btn = st.button("Merge PDFs", type="primary", use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
    with col_preview:
        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
        if files and 'order' in locals() and order:
            st.write("#### Document Structure")
            for i, name in enumerate(order):
                st.markdown(f"**{i+1}.** 📄 {name}")
            
            if 'merge_btn' in locals() and merge_btn:
                merger = PdfWriter()
                for name in order: merger.append(file_map[name])
                out = BytesIO()
                merger.write(out)
                st.success("Merged successfully!")
                st.download_button("⬇️ Download PDF", out.getvalue(), "docmint_merged.pdf", "application/pdf")
        else:
            st.info("Upload PDFs on the left to start.")
        st.markdown('</div>', unsafe_allow_html=True)

def tool_split_pdf():
    st.markdown(f"### ✂️ {st.session_state['current_tool']}")
    col_controls, col_preview = st.columns([1, 2], gap="large")
    
    with col_controls:
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        f = st.file_uploader("Upload PDF", type="pdf")
        if f:
            reader = PdfReader(f)
            total = len(reader.pages)
            st.write(f"Detected **{total}** pages.")
            mode = st.radio("Mode", ["Extract One", "Split All"])
            if mode == "Extract One":
                p_num = st.number_input("Page #", 1, total, 1)
            btn = st.button("Process PDF", type="primary")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_preview:
        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
        if f and 'btn' in locals() and btn:
            if mode == "Extract One":
                w = PdfWriter()
                w.add_page(reader.pages[p_num-1])
                o = BytesIO()
                w.write(o)
                st.write(f"✅ Ready: Page {p_num}")
                st.download_button("Download Page", o.getvalue(), f"page_{p_num}.pdf", "application/pdf")
            else:
                files = {}
                for i in range(total):
                    w = PdfWriter()
                    w.add_page(reader.pages[i])
                    o = BytesIO()
                    w.write(o)
                    files[f"page_{i+1}.pdf"] = o.getvalue()
                st.write(f"✅ Ready: {total} files zipped")
                st.download_button("Download ZIP", create_zip(files, "split.zip"), "split.zip", "application/zip")
        else:
            st.write("Upload PDF to view options.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 7. DISPATCHER & MAIN ---

render_sidebar()

# Main Content Area
tool = st.session_state['current_tool']

if tool == "Resize Image": tool_resize_image()
elif tool == "Image Editor": tool_img_editor()
elif tool == "Merge PDF": tool_merge_pdf()
elif tool == "Split PDF": tool_split_pdf()
elif tool == "Convert Format": 
    # Quick implementation of Convert using split layout
    st.markdown(f"### 🔄 {tool}")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.markdown('<div class="control-panel">', unsafe_allow_html=True)
        u = st.file_uploader("Upload", type=["png", "jpg", "webp"])
        t = st.selectbox("Target", ["PNG", "JPEG", "PDF", "WEBP"])
        if u: st.button("Convert", type="primary", key="conv_btn")
        st.markdown('</div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="preview-card">', unsafe_allow_html=True)
        if u:
            i = Image.open(u)
            st.image(i, width=300)
            if st.session_state.get("conv_btn"):
                if t == "JPEG" and i.mode == "RGBA": i = i.convert("RGB")
                b = BytesIO()
                i.save(b, format=t)
                mime = "application/pdf" if t == "PDF" else f"image/{t.lower()}"
                st.download_button("Download", b.getvalue(), f"conv.{t.lower()}", mime)
        else: st.write("Waiting for upload...")
        st.markdown('</div>', unsafe_allow_html=True)

else:
    st.info("Select a tool from the sidebar to get started.")

st.markdown("---")
st.markdown("<div style='text-align:center; color:#94a3b8; font-size:0.8rem;'>© 2024 DocMint by Nitesh Kumar</div>", unsafe_allow_html=True)
