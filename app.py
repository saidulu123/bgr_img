import streamlit as st
from rembg import remove
from PIL import Image, UnidentifiedImageError
import tempfile
import os
import io

# Constants
MAX_IMAGE_DIMENSION = 1024  # Maximum dimension for compression

# Get the directory of the current script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Set Streamlit configuration
st.set_page_config(page_title="Image Processor", layout="centered")

# Load custom CSS
css_path = os.path.join(BASE_DIR, "style.css")
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
foreground_file = st.file_uploader("Upload Foreground Image (JPEG/PNG)", type=["jpg", "jpeg", "png"])
background_file = st.file_uploader("Upload Background Image (JPEG/PNG)", type=["jpg", "jpeg", "png"])

# Function to compress an image
def compress_image(image: Image.Image, max_dimension: int) -> Image.Image:
    """Resize the image while maintaining aspect ratio."""
    image.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)
    return image

# Process the images when both are uploaded
if foreground_file and background_file:
    with st.spinner("Processing images..."):
        try:
            # Load and validate images
            foreground_img = Image.open(foreground_file)
            background_img = Image.open(background_file)
            
            st.write(f"Original Foreground Size: {foreground_img.size}")
            st.write(f"Original Background Size: {background_img.size}")

            # Compress images to ensure consistent processing
            foreground_img = compress_image(foreground_img, MAX_IMAGE_DIMENSION)
            background_img = compress_image(background_img, MAX_IMAGE_DIMENSION)

            st.write(f"Compressed Foreground Size: {foreground_img.size}")
            st.write(f"Compressed Background Size: {background_img.size}")

            # Create a temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Save the foreground image temporarily
                foreground_path = os.path.join(temp_dir, 'foreground.png')
                foreground_img.save(foreground_path)

                # Process the foreground image to remove the background
                processed_foreground_path = os.path.join(temp_dir, 'processed_foreground.png')
                with open(processed_foreground_path, 'wb') as f:
                    input_data = open(foreground_path, 'rb').read()
                    output_data = remove(input_data, alpha_matting=True)
                    f.write(output_data)

                # Load the processed foreground image
                processed_foreground = Image.open(processed_foreground_path)

                # Resize the background image to match the foreground dimensions
                background_resized = background_img.resize(processed_foreground.size)

                # Ensure both images are in RGBA mode
                if processed_foreground.mode != "RGBA":
                    processed_foreground = processed_foreground.convert("RGBA")
                if background_resized.mode != "RGBA":
                    background_resized = background_resized.convert("RGBA")

                # Composite the foreground and background images
                output_img = Image.alpha_composite(background_resized, processed_foreground)

                # Display the result
                st.image(output_img, caption="Final Output Image", use_container_width=True)
                st.success("Image processing completed!")

                # Download button for the output image
                output_img_path = os.path.join(temp_dir, "output.png")
                output_img.save(output_img_path)
                with open(output_img_path, "rb") as img_file:
                    st.download_button(
                        label="Download Output Image",
                        data=img_file,
                        file_name="output.png",
                        mime="image/png"
                    )
        except UnidentifiedImageError:
            st.error("One of the uploaded files is not a valid image. Please try again.")
        except Exception as e:
            st.error(f"An unexpected error occurred: {e}")
else:
    st.info("Please upload both foreground and background images to proceed.")
#pil  issue