import streamlit as st
import os
from io import BytesIO
import zipfile
from PIL import Image, ImageOps, ImageFilter

# PDF Libraries
from PyPDF2 import PdfReader, PdfWriter

# PPT Libraries
from pptx import Presentation

# PDF to Image (Requires Poppler installed on the system)
try:
    from pdf2image import convert_from_bytes
    HAS_PDF2IMAGE = True
except ImportError:
    HAS_PDF2IMAGE = False
except Exception:
    HAS_PDF2IMAGE = False

# Set Page Config
st.set_page_config(
    page_title="DocuMaster Pro",
    page_icon="📑",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for Better UI ---
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
        border: none;
    }
    .stButton>button:hover {
        background-color: #45a049;
        color: white;
    }
    h1 {
        color: #2c3e50;
        text-align: center;
        margin-bottom: 2rem;
    }
    h2, h3 {
        color: #34495e;
    }
    .stTab {
        background-color: white;
        padding: 10px;
        border-radius: 5px;
    }
    .css-1aumxhk {
        padding: 1rem;
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- Utility Functions ---

def get_image_download_link(img, filename, text):
    """Generates a link to download the PIL image"""
    buffered = BytesIO()
    img.save(buffered, format=os.path.splitext(filename)[1][1:].upper())
    return st.download_button(
        label=text,
        data=buffered.getvalue(),
        file_name=filename,
        mime=f"image/{os.path.splitext(filename)[1][1:]}"
    )

def create_zip(files_dict, zip_name):
    """Creates a zip file from a dictionary of filename:bytes"""
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zip_file:
        for file_name, data in files_dict.items():
            zip_file.writestr(file_name, data)
    return zip_buffer.getvalue()

# --- SIDEBAR ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2991/2991112.png", width=80)
    st.title("DocuMaster Pro")
    st.markdown("---")
    st.markdown("### 🛠️ Select Tool")
    
    # Using radio button with custom formatting for a cleaner sidebar look
    tool_choice = st.radio(
        "",
        ["PDF Tools", "Image Tools", "PowerPoint Tools"],
        index=0,
        format_func=lambda x: f"📄 {x}" if "PDF" in x else (f"🖼️ {x}" if "Image" in x else f"📊 {x}")
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** Use the tabs in the main window to switch between different operations.")
    st.caption("v1.0.0 | Built with Streamlit")

# --- MAIN APP UI ---

if tool_choice == "PDF Tools":
    st.title("📄 PDF Studio")
    
    # Use Tabs for better UX instead of dropdown
    tab1, tab2, tab3, tab4 = st.tabs(["🔗 Merge", "✂️ Split", "🖼️ Convert to Image", "📝 Extract Text"])

    # --- TAB 1: PDF MERGE ---
    with tab1:
        st.markdown("### Merge Multiple PDFs")
        st.write("Upload two or more PDF files to combine them into a single document.")
        
        uploaded_pdfs = st.file_uploader("Drop PDFs here", type="pdf", accept_multiple_files=True, key="merge_uploader")
        
        if uploaded_pdfs:
            st.success(f"✅ {len(uploaded_pdfs)} files ready to merge")
            if st.button("Merge Files", key="merge_btn"):
                with st.spinner("Merging..."):
                    merger = PdfWriter()
                    for pdf in uploaded_pdfs:
                        merger.append(pdf)
                    
                    output = BytesIO()
                    merger.write(output)
                    st.balloons()
                    st.download_button(
                        label="⬇️ Download Merged PDF",
                        data=output.getvalue(),
                        file_name="merged_document.pdf",
                        mime="application/pdf"
                    )

    # --- TAB 2: PDF SPLIT ---
    with tab2:
        st.markdown("### Split PDF Document")
        uploaded_pdf_split = st.file_uploader("Upload PDF to split", type="pdf", key="split_uploader")
        
        if uploaded_pdf_split:
            reader = PdfReader(uploaded_pdf_split)
            total_pages = len(reader.pages)
            st.info(f"📄 This document has **{total_pages} pages**.")
            
            col1, col2 = st.columns(2)
            with col1:
                split_mode = st.radio("Select Method", ["Extract Single Page", "Split All Pages"])
            
            if split_mode == "Extract Single Page":
                with col2:
                    page_num = st.number_input("Page Number", min_value=1, max_value=total_pages, value=1)
                
                if st.button("Extract Page", key="extract_btn"):
                    writer = PdfWriter()
                    writer.add_page(reader.pages[page_num-1])
                    output = BytesIO()
                    writer.write(output)
                    st.success("Page Extracted!")
                    st.download_button(label="⬇️ Download Page", data=output.getvalue(), file_name=f"page_{page_num}.pdf", mime="application/pdf")
            
            elif split_mode == "Split All Pages":
                st.warning("This will create a ZIP file containing every page as a separate PDF.")
                if st.button("Split All & Zip", key="split_all_btn"):
                    with st.spinner("Processing..."):
                        files_to_zip = {}
                        for i in range(total_pages):
                            writer = PdfWriter()
                            writer.add_page(reader.pages[i])
                            output = BytesIO()
                            writer.write(output)
                            files_to_zip[f"page_{i+1}.pdf"] = output.getvalue()
                        
                        zip_data = create_zip(files_to_zip, "split_pages.zip")
                        st.success("Done!")
                        st.download_button(label="⬇️ Download ZIP", data=zip_data, file_name="split_pages.zip", mime="application/zip")

    # --- TAB 3: PDF TO IMAGES ---
    with tab3:
        st.markdown("### PDF to Image Converter")
        if not HAS_PDF2IMAGE:
            st.error("⚠️ System dependency `poppler` missing. Images cannot be processed.")
        else:
            uploaded_pdf_img = st.file_uploader("Upload PDF", type="pdf", key="img_uploader")
            if uploaded_pdf_img:
                if st.button("Convert to Images", key="convert_img_btn"):
                    with st.spinner("Rendering pages..."):
                        try:
                            images = convert_from_bytes(uploaded_pdf_img.read())
                            files_to_zip = {}
                            
                            st.write(f"📸 Converted {len(images)} pages.")
                            
                            # Gallery view for first 4 pages
                            cols = st.columns(4)
                            for i, page_image in enumerate(images):
                                img_buffer = BytesIO()
                                page_image.save(img_buffer, format="JPEG")
                                files_to_zip[f"page_{i+1}.jpg"] = img_buffer.getvalue()
                                
                                if i < 4:
                                    with cols[i]:
                                        st.image(page_image, caption=f"Page {i+1}", use_column_width=True)

                            zip_data = create_zip(files_to_zip, "pdf_images.zip")
                            st.download_button("⬇️ Download All Images (ZIP)", data=zip_data, file_name="pdf_images.zip", mime="application/zip")
                        except Exception as e:
                            st.error(f"Error: {e}")

    # --- TAB 4: TEXT EXTRACT ---
    with tab4:
        st.markdown("### Extract Text & Metadata")
        uploaded_pdf_text = st.file_uploader("Upload PDF", type="pdf", key="text_uploader")
        
        if uploaded_pdf_text:
            reader = PdfReader(uploaded_pdf_text)
            info = reader.metadata
            
            with st.expander("See Metadata", expanded=True):
                col1, col2 = st.columns(2)
                col1.write(f"**Pages:** {len(reader.pages)}")
                col1.write(f"**Author:** {info.get('/Author', 'Unknown')}")
                col2.write(f"**Creator:** {info.get('/Creator', 'Unknown')}")
                col2.write(f"**Producer:** {info.get('/Producer', 'Unknown')}")
            
            if st.button("Extract Text Content", key="text_btn"):
                full_text = ""
                progress_bar = st.progress(0)
                for i, page in enumerate(reader.pages):
                    full_text += f"\n--- Page {i+1} ---\n"
                    full_text += page.extract_text() or ""
                    progress_bar.progress((i + 1) / len(reader.pages))
                
                st.text_area("Extracted Content", full_text, height=300)
                st.download_button("⬇️ Download Text (.txt)", data=full_text, file_name="extracted_text.txt", mime="text/plain")


# ==========================
# IMAGE TOOLS
# ==========================
elif tool_choice == "Image Tools":
    st.title("🖼️ Image Studio")
    tab1, tab2, tab3 = st.tabs(["🎨 Editor", "🔄 Converter", "📑 Images to PDF"])

    # --- TAB 1: EDITOR ---
    with tab1:
        st.markdown("### Advanced Image Editor")
        uploaded_img = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "bmp", "webp"], key="editor_uploader")
        
        if uploaded_img:
            image = Image.open(uploaded_img)
            
            col_orig, col_edit = st.columns([1, 1])
            with col_orig:
                st.image(image, caption="Original", use_column_width=True)
            
            with st.form("image_edit_form"):
                st.write("#### Edit Settings")
                c1, c2 = st.columns(2)
                with c1:
                    new_width = st.number_input("Width (px)", value=image.width)
                    rotate_angle = st.slider("Rotate (°)", 0, 360, 0)
                with c2:
                    new_height = st.number_input("Height (px)", value=image.height)
                    filter_type = st.selectbox("Filter", ["None", "Grayscale", "Blur", "Contour", "Detail", "Edge Enhance"])
                
                resize_toggle = st.checkbox("Apply Resize")
                submit = st.form_submit_button("Apply Changes")
            
            if submit:
                processed_img = image.copy()
                if resize_toggle:
                    processed_img = processed_img.resize((int(new_width), int(new_height)))
                if rotate_angle != 0:
                    processed_img = processed_img.rotate(rotate_angle, expand=True)
                
                if filter_type == "Grayscale": processed_img = ImageOps.grayscale(processed_img)
                elif filter_type == "Blur": processed_img = processed_img.filter(ImageFilter.BLUR)
                elif filter_type == "Contour": processed_img = processed_img.filter(ImageFilter.CONTOUR)
                elif filter_type == "Detail": processed_img = processed_img.filter(ImageFilter.DETAIL)
                elif filter_type == "Edge Enhance": processed_img = processed_img.filter(ImageFilter.EDGE_ENHANCE)
                
                with col_edit:
                    st.image(processed_img, caption="Result", use_column_width=True)
                    
                buf = BytesIO()
                processed_img.save(buf, format="PNG")
                st.download_button("⬇️ Download Result", data=buf.getvalue(), file_name="edited_image.png", mime="image/png")

    # --- TAB 2: CONVERT ---
    with tab2:
        st.markdown("### Format Converter")
        uploaded_conv_img = st.file_uploader("Upload Image", type=["png", "jpg", "jpeg", "webp", "bmp", "tiff"], key="conv_uploader")
        
        if uploaded_conv_img:
            image = Image.open(uploaded_conv_img)
            st.image(image, width=300)
            
            target_format = st.selectbox("Convert to:", ["PNG", "JPEG", "PDF", "WEBP", "BMP", "ICO"])
            
            if st.button(f"Convert to {target_format}", key="conv_btn"):
                buf = BytesIO()
                img_to_save = image.copy()
                if target_format == "JPEG" and img_to_save.mode in ("RGBA", "P"):
                    img_to_save = img_to_save.convert("RGB")
                
                img_to_save.save(buf, format=target_format)
                st.success("Conversion Successful!")
                
                mime_type = f"image/{target_format.lower()}"
                if target_format == "PDF": mime_type = "application/pdf"
                st.download_button(f"⬇️ Download {target_format}", data=buf.getvalue(), file_name=f"converted.{target_format.lower()}", mime=mime_type)

    # --- TAB 3: IMAGES TO PDF ---
    with tab3:
        st.markdown("### Combine Images to PDF")
        uploaded_imgs_pdf = st.file_uploader("Select Images", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="imgs_pdf_uploader")
        
        if uploaded_imgs_pdf:
            st.write(f"Selected {len(uploaded_imgs_pdf)} images.")
            if st.button("Generate PDF", key="gen_pdf_btn"):
                pil_images = []
                for img_file in uploaded_imgs_pdf:
                    img = Image.open(img_file)
                    if img.mode == "RGBA": img = img.convert("RGB")
                    pil_images.append(img)
                
                if pil_images:
                    pdf_buffer = BytesIO()
                    pil_images[0].save(pdf_buffer, "PDF", resolution=100.0, save_all=True, append_images=pil_images[1:])
                    st.success("PDF Ready!")
                    st.download_button("⬇️ Download PDF", data=pdf_buffer.getvalue(), file_name="images_merged.pdf", mime="application/pdf")

# ==========================
# POWERPOINT TOOLS
# ==========================
elif tool_choice == "PowerPoint Tools":
    st.title("📊 PowerPoint Studio")
    tab1, tab2 = st.tabs(["🔗 Merge PPTX", "📝 Extract Text"])

    # --- TAB 1: MERGE PPT ---
    with tab1:
        st.markdown("### Merge Presentations")
        st.info("ℹ️ This tool merges slides from multiple files. Note: Complex layouts or master slides might not preserve perfectly.")
        uploaded_ppts = st.file_uploader("Upload PPTX files", type="pptx", accept_multiple_files=True, key="ppt_uploader")
        
        if uploaded_ppts:
            if st.button("Merge Slides", key="ppt_merge_btn"):
                with st.spinner("Merging slides..."):
                    output_prs = Presentation()
                    # Remove default blank slide
                    xml_slides = output_prs.slides._sldIdLst
                    slides = list(xml_slides)
                    xml_slides.remove(slides[0])

                    for ppt_file in uploaded_ppts:
                        input_prs = Presentation(ppt_file)
                        for slide in input_prs.slides:
                            # Create new slide
                            layout = output_prs.slide_layouts[6] # Blank
                            dest_slide = output_prs.slides.add_slide(layout)
                            
                            # Attempt simple content copy
                            for shape in slide.shapes:
                                if hasattr(shape, "text"):
                                    try:
                                        txBox = dest_slide.shapes.add_textbox(shape.left, shape.top, shape.width, shape.height)
                                        txBox.text_frame.text = shape.text
                                    except: pass
                    
                    out_ppt = BytesIO()
                    output_prs.save(out_ppt)
                    st.success("Merged Successfully!")
                    st.download_button("⬇️ Download Merged PPTX", data=out_ppt.getvalue(), file_name="merged_presentation.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation")

    # --- TAB 2: PPT TEXT ---
    with tab2:
        st.markdown("### Extract Content")
        uploaded_ppt_text = st.file_uploader("Upload PPTX", type="pptx", key="ppt_text_uploader")
        
        if uploaded_ppt_text:
            prs = Presentation(uploaded_ppt_text)
            st.write(f"**Total Slides:** {len(prs.slides)}")
            
            if st.button("Get Text", key="ppt_text_btn"):
                text_content = []
                for i, slide in enumerate(prs.slides):
                    slide_text = []
                    for shape in slide.shapes:
                        if hasattr(shape, "text"):
                            slide_text.append(shape.text)
                    text_content.append(f"--- Slide {i+1} ---\n" + "\n".join(slide_text))
                
                full_text = "\n\n".join(text_content)
                st.text_area("Content Preview", full_text, height=300)
                st.download_button("⬇️ Download (.txt)", data=full_text, file_name="presentation_text.txt", mime="text/plain")