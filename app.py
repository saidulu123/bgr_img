import streamlit as st
from rembg import remove
from PIL import Image, UnidentifiedImageError
import tempfile
import os

# Constants
MAX_IMAGE_SIZE_MB = 5  # Maximum allowed file size in MB
MAX_IMAGE_DIMENSION = 1024  # Maximum dimension for compression
ALLOWED_IMAGE_FORMATS = ["png", "jpg", "jpeg", "bmp", "tiff"]  # Supported image formats

# Get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set Streamlit configuration
st.set_page_config(page_title="Image Processor", layout="centered")

# Load custom CSS if available
css_path = os.path.join(BASE_DIR, "style.css")
if os.path.exists(css_path):
    with open(css_path, "r") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Title and description
st.markdown("""
<div class="container">
    <h1>Image Background Replacement Tool</h1>
    <p>Upload a foreground and background image to create a composite image.</p>
</div>
""", unsafe_allow_html=True)

# File upload widgets
foreground_file = st.file_uploader("Upload Foreground Image", type=ALLOWED_IMAGE_FORMATS)
background_file = st.file_uploader("Upload Background Image", type=ALLOWED_IMAGE_FORMATS)

def validate_file(file, file_type):
    """ Validate file format and size """
    if file:
        file_size_mb = file.size / (1024 * 1024)  # Convert bytes to MB
        file_ext = file.name.split(".")[-1].lower()
        
        if file_ext not in ALLOWED_IMAGE_FORMATS:
            st.error(f"❌ {file_type} file format not supported! Please upload an image in {ALLOWED_IMAGE_FORMATS}.")
            return False
        
        if file_size_mb > MAX_IMAGE_SIZE_MB:
            st.error(f"❌ {file_type} file size exceeds {MAX_IMAGE_SIZE_MB}MB! Please upload a smaller image.")
            return False
        
        return True
    return False

def compress_image(image: Image.Image, max_dimension: int) -> Image.Image:
    """Resize the image while maintaining aspect ratio if necessary."""
    if max(image.size) > max_dimension:
        image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return image

# Validate both files
valid_foreground = validate_file(foreground_file, "Foreground")
valid_background = validate_file(background_file, "Background")

# Process the images when both are valid
if valid_foreground and valid_background:
    with st.spinner("⏳ Processing images..."):
        try:
            # Load images
            foreground_img = Image.open(foreground_file)
            background_img = Image.open(background_file)

            # Log original image sizes
            st.write(f"📏 Original Foreground Size: {foreground_img.size}")
            st.write(f"📏 Original Background Size: {background_img.size}")

            # Compress images if necessary
            foreground_img = compress_image(foreground_img, MAX_IMAGE_DIMENSION)
            background_img = compress_image(background_img, MAX_IMAGE_DIMENSION)

            # Log compressed image sizes
            st.write(f"📏 Compressed Foreground Size: {foreground_img.size}")
            st.write(f"📏 Compressed Background Size: {background_img.size}")

            # Create a temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                foreground_path = os.path.join(temp_dir, 'foreground.png')
                processed_foreground_path = os.path.join(temp_dir, 'processed_foreground.png')

                # Save foreground temporarily
                foreground_img.save(foreground_path)

                # Process foreground to remove background
                with open(foreground_path, 'rb') as input_file, open(processed_foreground_path, 'wb') as output_file:
                    output_file.write(remove(input_file.read(), alpha_matting=True))

                # Load the processed foreground image
                processed_foreground = Image.open(processed_foreground_path)

                # Resize background if dimensions don't match
                if processed_foreground.size != background_img.size:
                    background_img = background_img.resize(processed_foreground.size)

                # Ensure both images are in RGBA mode
                processed_foreground = processed_foreground.convert("RGBA")
                background_img = background_img.convert("RGBA")

                # Composite the images
                output_img = Image.alpha_composite(background_img, processed_foreground)

                # Display the result
                st.image(output_img, caption="🎨 Final Output Image", use_column_width=True)
                st.success("✅ Image processing completed successfully!")

                # Save output image for download
                output_img_path = os.path.join(temp_dir, "output.png")
                output_img.save(output_img_path)

                # Provide download button
                with open(output_img_path, "rb") as img_file:
                    st.download_button(
                        label="⬇️ Download Output Image",
                        data=img_file,
                        file_name="output.png",
                        mime="image/png"
                    )
        except UnidentifiedImageError:
            st.error("❌ One of the uploaded files is not a valid image. Please try again.")
        except Exception as e:
            st.error(f"❌ An unexpected error occurred: {e}")
else:
    st.info("📢 Please upload both foreground and background images to proceed.")
