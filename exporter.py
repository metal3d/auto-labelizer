import io
import zipfile
from typing import Any, Dict, List


class ImageLabelExporter:
    """Export images and their labels to a zip file."""

    def __init__(self):
        pass

    def create_zip(
        self, images_data: List[Dict[str, Any]], labels: Dict[str, str]
    ) -> io.BytesIO:
        """
        Create a zip file containing images and their corresponding text labels.

        Args:
            images_data: List of dictionaries containing image data with 'name', 'image', and 'file'
            labels: Dictionary mapping image names to their labels

        Returns:
            io.BytesIO: Zip file as bytes
        """
        zip_buffer = io.BytesIO()

        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for img_data in images_data:
                img_name = img_data["name"]
                img_pil = img_data["image"]
                img_file = img_data["file"]

                # Add image to zip
                if hasattr(img_file, "read"):
                    # If it's a file-like object, read its content
                    img_file.seek(0)
                    zip_file.writestr(img_name, img_file.read())
                else:
                    # If it's a PIL Image, save it to bytes
                    img_bytes = io.BytesIO()
                    img_pil.save(img_bytes, format="PNG")
                    img_bytes.seek(0)
                    zip_file.writestr(img_name, img_bytes.read())

                # Create text file with label
                txt_name = self._get_txt_filename(img_name)
                label_text = labels.get(img_name, "")

                # Add text file to zip
                zip_file.writestr(txt_name, label_text.encode("utf-8"))

        zip_buffer.seek(0)
        return zip_buffer

    def _get_txt_filename(self, image_filename: str) -> str:
        """Convert image filename to text filename."""
        # Remove extension and add .txt
        name_without_ext = image_filename.rsplit(".", 1)[0]
        return f"{name_without_ext}.txt"

    def get_download_filename(self) -> str:
        """Generate a filename for the zip download."""
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"labeled_images_{timestamp}.zip"
