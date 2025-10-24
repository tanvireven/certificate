import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import io
import re
import os

# ====== PAGE CONFIG ======
st.set_page_config(page_title="Certificate Generator", page_icon="🎓", layout="wide")

# ====== CUSTOM STYLING ======
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {padding: 1rem;}
    .stTextInput, .stButton, .stDownloadButton {width: 100% !important;}
    img {max-width: 100%; height: auto; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);}
    
    /* Mobile-friendly sliders */
    @media (max-width: 768px) {
        h1, h2, h3 {font-size: 1.2rem !important;}
        [data-testid="stSidebar"] {padding: 0.5rem;}
        .stSlider > div > div { padding: 12px 0 !important; }
    }
    .success-message {color: #2e8b57; font-weight: bold;}
    .error-message {color: #b22222; font-weight: bold;}
    </style>
""", unsafe_allow_html=True)

st.title("🎓 Online Certificate Generator")
st.caption("Made by **Tanvir Even** | Works on both Mobile 📱 and PC 💻")

# ====== ADMIN SETTINGS ======
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "12345")  # Use env var in production
DEFAULT_NAME_X, DEFAULT_NAME_Y = 750, 704
DEFAULT_FONT_SIZE = 60
DEFAULT_FONT_COLOR = "#000000"

# ====== SESSION STATE INITIALIZATION ======
defaults = {
    "authenticated": False,
    "template_bytes": None,
    "font_file": None,
    "name_x": DEFAULT_NAME_X,
    "name_y": DEFAULT_NAME_Y,
    "font_size": DEFAULT_FONT_SIZE,
    "font_color": DEFAULT_FONT_COLOR,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# ====== SIDEBAR (ADMIN PANEL) ======
with st.sidebar:
    st.header("⚙️ Admin Panel")

    if not st.session_state.authenticated:
        password = st.text_input("Enter Admin Password", type="password")
        if st.button("🔓 Login"):
            if password == ADMIN_PASSWORD:
                st.session_state.authenticated = True
                st.success("✅ Logged in successfully!")
            else:
                st.error("❌ Incorrect password!")
    else:
        st.success("🔐 Admin Access Granted")

        # Template upload
        uploaded_template = st.file_uploader(
            "Upload Certificate Template (JPG/PNG)", 
            type=["jpg", "jpeg", "png"],
            key="template_uploader"
        )
        if uploaded_template:
            st.session_state.template_bytes = uploaded_template.read()
            st.success("✅ Template uploaded and stored!")

        # Show current template preview (if available)
        if st.session_state.template_bytes:
            st.image(st.session_state.template_bytes, caption="Current Template", use_column_width=True)

        # Font upload
        font_file = st.file_uploader("Upload Font (.ttf)", type=["ttf"], key="font_uploader")
        if font_file:
            st.session_state.font_file = font_file
            st.success("✅ Font uploaded!")

        # Text positioning
        st.markdown("### 📝 Text Positioning")
        st.session_state.name_x = st.slider("Name X Position", 0, 2000, st.session_state.name_x)
        st.session_state.name_y = st.slider("Name Y Position", 0, 2000, st.session_state.name_y)
        
        # Text styling
        st.markdown("### 🎨 Text Styling")
        st.session_state.font_size = st.slider("Font Size", 50, 500, st.session_state.font_size)
        st.session_state.font_color = st.color_picker("Font Color", st.session_state.font_color)

        # Reset button
        if st.button("🔄 Reset to Defaults"):
            st.session_state.name_x = DEFAULT_NAME_X
            st.session_state.name_y = DEFAULT_NAME_Y
            st.session_state.font_size = DEFAULT_FONT_SIZE
            st.session_state.font_color = DEFAULT_FONT_COLOR
            st.success("✅ Settings reset to defaults!")

        # Remove template
        if st.button("🗑️ Remove Uploaded Template"):
            st.session_state.template_bytes = None
            st.warning("❌ Template removed!")

        # Logout
        if st.button("🚪 Logout"):
            for key in defaults.keys():
                st.session_state[key] = defaults[key]
            st.info("✅ Logged out successfully!")

        st.markdown("---")
        st.caption("👨‍💻 Developed by **Tanvir Even**")

# ====== USER SECTION ======
if not st.session_state.template_bytes:
    st.warning("⚠️ No certificate template uploaded yet. Please ask the admin to upload one first.")
else:
    st.subheader("✏️ Generate Your Certificate")
    user_name = st.text_input("Enter Your Full Name")

    if st.button("✨ Generate Certificate"):
        if not user_name.strip():
            st.warning("Please enter your name!")
        else:
            try:
                # Load template
                template = Image.open(io.BytesIO(st.session_state.template_bytes))
                cert = template.copy()
                draw = ImageDraw.Draw(cert)

                # Load font
                if st.session_state.font_file:
                    font = ImageFont.truetype(st.session_state.font_file, st.session_state.font_size)
                else:
                    # Try system font first
                    try:
                        font = ImageFont.truetype("arial.ttf", st.session_state.font_size)
                    except OSError:
                        try:
                            # Common Linux/Mac fallback
                            font = ImageFont.truetype("DejaVuSans.ttf", st.session_state.font_size)
                        except OSError:
                            # Last resort: default (won't respect font_size well)
                            st.warning("⚠️ No scalable font available. Text may appear small.")
                            font = ImageFont.load_default()

                # Draw name
                draw.text(
                    (st.session_state.name_x, st.session_state.name_y),
                    user_name,
                    fill=st.session_state.font_color,
                    font=font
                )

                # Save to bytes
                img_bytes = io.BytesIO()
                cert.save(img_bytes, format="PNG")
                img_bytes.seek(0)

                # Display
                st.image(cert, caption=f"Certificate for {user_name}", use_column_width=True)

                # Sanitize filename
                safe_name = re.sub(r'[^\w\s-]', '', user_name).strip().replace(' ', '_')

                # Download options
                col1, col2 = st.columns(2)

                with col1:
                    # PDF
                    pdf_bytes = io.BytesIO()
                    cert_rgb = cert.convert("RGB")
                    cert_rgb.save(pdf_bytes, format="PDF")
                    pdf_bytes.seek(0)
                    st.download_button(
                        "📥 Download as PDF",
                        data=pdf_bytes,
                        file_name=f"{safe_name}_certificate.pdf",
                        mime="application/pdf"
                    )

                with col2:
                    # PNG
                    st.download_button(
                        "📥 Download as PNG",
                        data=img_bytes,
                        file_name=f"{safe_name}_certificate.png",
                        mime="image/png"
                    )

            except Exception as e:
                st.error(f"❌ An error occurred: {str(e)}")
                st.info("Please check the template and font files and try again.")
