import streamlit as st
from PIL import Image

from exporter import ImageLabelExporter
from labelizer import get_task_response


st.set_page_config(
    page_title="Image Auto-Labeler",
    page_icon="🏷️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize session state
if "uploaded_images" not in st.session_state:
    st.session_state.uploaded_images = []
if "image_labels" not in st.session_state:
    st.session_state.image_labels = {}
if "labeling_all" not in st.session_state:
    st.session_state.labeling_all = False
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0
if "trigger_word" not in st.session_state:
    st.session_state.trigger_word = ""


def handle_file_upload(uploaded_files):
    if uploaded_files:
        images = []
        for uploaded_file in uploaded_files:
            try:
                image = Image.open(uploaded_file)
                images.append(
                    {"name": uploaded_file.name, "image": image, "file": uploaded_file}
                )
            except Exception as e:
                st.error(f"Error loading {uploaded_file.name}: {e}")

        st.session_state.uploaded_images = images
        st.session_state.image_labels = {img["name"]: "" for img in images}
        st.rerun()


# Sidebar with controls
with st.sidebar:
    st.title("🏷️ Image Auto-Labeler")
    st.markdown("Upload multiple images and generate labels automatically using AI.")

    st.subheader("📁 Import Images")
    uploaded_files = st.file_uploader(
        "Choose image files",
        type=["png", "jpg", "jpeg", "gif", "bmp", "webp"],
        accept_multiple_files=True,
        key=f"file_uploader_{st.session_state.uploader_key}",
    )

    if uploaded_files:
        if st.button("📥 Load Images", type="primary", width="stretch"):
            handle_file_upload(uploaded_files)

    # Show current status
    # Show current status
    if st.session_state.uploaded_images:
        st.success(f"✅ {len(st.session_state.uploaded_images)} images loaded")
        st.divider()

        # Trigger word input
        st.subheader("🎯 Trigger Word")
        trigger_word = st.text_input(
            "Optional trigger word to prepend to all labels:",
            value=st.session_state.trigger_word,
            placeholder="e.g., 'photo of', 'image of'",
            key="trigger_input",
        )
        st.session_state.trigger_word = trigger_word

        st.divider()
        if st.button("🏷️ Label All Images", type="primary", width="stretch"):
            st.session_state.labeling_all = True
            for img_data in st.session_state.uploaded_images:
                text_input_key = f"text_input_{img_data['name']}"
                st.session_state.image_labels[img_data["name"]] = "Labeling..."
                st.session_state[text_input_key] = "Labeling..."
            st.rerun()

        if st.button("🗑️ Clear All Images", width="stretch"):
            st.session_state.uploaded_images = []
            st.session_state.image_labels = {}
            # Clear all text input states
            keys_to_remove = [
                key
                for key in st.session_state.keys()
                if isinstance(key, str) and key.startswith("text_input_")
            ]
            for key in keys_to_remove:
                del st.session_state[key]
            # Clear file uploader cache by incrementing key
            st.session_state.uploader_key += 1
            # Clear any other cached data
            st.session_state.uploaded_files = None
            st.rerun()
    else:
        st.info("📭 No images loaded")

    if st.session_state.uploaded_images:
        st.divider()
        if st.button("📦 Export All", type="secondary", width="stretch"):
            if st.session_state.uploaded_images:
                exporter = ImageLabelExporter()
                zip_buffer = exporter.create_zip(
                    st.session_state.uploaded_images, st.session_state.image_labels
                )

                # Provide download button
                st.download_button(
                    label="💾 Download ZIP",
                    data=zip_buffer,
                    file_name=exporter.get_download_filename(),
                    mime="application/zip",
                    use_container_width=True,
                )


# Process all images if labeling_all flag is set
if st.session_state.get("labeling_all", False):
    # Show progress in sidebar
    with st.sidebar:
        st.subheader("🔄 Processing...")
        total_images = len(st.session_state.uploaded_images)
        progress_bar = st.progress(0, text="Labeling images...")
        status_text = st.empty()

        for i, img_data in enumerate(st.session_state.uploaded_images):
            text_input_key = f"text_input_{img_data['name']}"
            status_text.text(f"Processing {img_data['name']} ({i + 1}/{total_images})")

            try:
                label = get_task_response("<MORE_DETAILED_CAPTION>", img_data["image"])
                # Prepend trigger word if provided
                if st.session_state.trigger_word.strip():
                    label = f"{st.session_state.trigger_word.strip()} {label}"
                st.session_state.image_labels[img_data["name"]] = label
                st.session_state[text_input_key] = label
            except Exception as e:
                error_msg = f"Error: {str(e)}"
                st.session_state.image_labels[img_data["name"]] = error_msg
                st.session_state[text_input_key] = error_msg

            # Update progress
            progress = (i + 1) / total_images
            progress_bar.progress(
                progress, text=f"Labeled {i + 1}/{total_images} images"
            )

    # Clean up
    progress_bar.empty()
    status_text.empty()
    st.session_state.labeling_all = False
    st.rerun()

# Display images
if st.session_state.uploaded_images:
    st.subheader(f"🖼️ Images ({len(st.session_state.uploaded_images)})")

    cols_per_row = 4
    cols = st.columns(cols_per_row)

    for i, img_data in enumerate(st.session_state.uploaded_images):
        with cols[i % cols_per_row]:
            with st.container(border=True):
                st.image(
                    img_data["image"],
                    caption=img_data["name"],
                    width="stretch",
                    output_format="PNG",
                )

                # Initialize text input state if not exists
                text_input_key = f"text_input_{img_data['name']}"
                if text_input_key not in st.session_state:
                    st.session_state[text_input_key] = (
                        st.session_state.image_labels.get(img_data["name"], "")
                    )

                if st.button(
                    "🏷️ Label", key=f"btn_{img_data['name']}_{i}", width="stretch"
                ):
                    st.session_state.image_labels[img_data["name"]] = "Labeling..."
                    st.session_state[text_input_key] = "Labeling..."
                    try:
                        label = get_task_response(
                            "<MORE_DETAILED_CAPTION>", img_data["image"]
                        )
                        print("Generated label:", label)
                        # Prepend trigger word if provided
                        if st.session_state.trigger_word.strip():
                            label = f"{st.session_state.trigger_word.strip()} {label}"
                        st.session_state.image_labels[img_data["name"]] = label
                        st.session_state[text_input_key] = label
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.session_state.image_labels[img_data["name"]] = error_msg
                        st.session_state[text_input_key] = error_msg
                    st.rerun()

                new_label = st.text_area(
                    "Label:",
                    key=text_input_key,
                    placeholder="Enter label or use AI button",
                    label_visibility="collapsed",
                    height=200,
                )

                # Update session state with manual input
                st.session_state.image_labels[img_data["name"]] = new_label

                # Remove button for individual image
                if st.button(
                    "🗑️ Remove", key=f"remove_{img_data['name']}_{i}", width="stretch"
                ):
                    # Debug info
                    st.write(f"Removing image: {img_data['name']}")

                    # Remove image from uploaded_images
                    st.session_state.uploaded_images = [
                        img
                        for img in st.session_state.uploaded_images
                        if img["name"] != img_data["name"]
                    ]

                    # Remove label from image_labels
                    if img_data["name"] in st.session_state.image_labels:
                        del st.session_state.image_labels[img_data["name"]]

                    # Remove text input state
                    text_input_key = f"text_input_{img_data['name']}"
                    if text_input_key in st.session_state:
                        del st.session_state[text_input_key]

                    st.rerun()
else:
    st.markdown("""
    # 🏷️ Welcome to Image Auto-Labeler
    
    ## 📋 How to Use This App
    
    ### 1. **Upload Images**
    - Go to the left sidebar
    - Click "Choose image files" to select multiple images
    - Supported formats: PNG, JPG, JPEG, GIF, BMP, WebP
    - Click "📥 Load Images" to import them
    
    ### 2. **Configure Labels**
    - **Trigger Word** (Optional): Enter a prefix like "photo of" or "image of"
    - This will be added to the beginning of all AI-generated labels
    - Leave empty for standard labels
    
    ### 3. **Generate Labels**
    - **Individual**: Click "🏷️ Label" below any image
    - **Batch**: Click "🏷️ Label All Images" in sidebar
    - Progress will show in the sidebar during batch processing
    
    ### 4. **Edit & Manage**
    - Edit any label manually in the text areas
    - Remove individual images with the "🗑️ Remove" button
    - Clear all images with "🗑️ Clear All Images" in the sidebar
    
    ### 5. **Export Results**
    - Click "📦 Export All" in the sidebar
    - Download the ZIP file containing:
      - Original images
      - Text files with labels (same filename + .txt extension)
    
    ---
    👆 **Start by uploading images using the sidebar!**
    """)
