import os
import zipfile
from flask import Flask, render_template_string, request, send_file, redirect, url_for
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
OUTPUT_FOLDER = os.path.join(BASE_DIR, "converted")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Simple HTML Template with download button
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>JPEG to PNG Converter</title>
</head>
<body style="font-family: Arial; text-align: center; margin-top: 50px;">
    <h2>JPEG to PNG Converter</h2>
    <form method="POST" action="/convert" enctype="multipart/form-data">
        <input type="file" name="images" multiple accept=".jpg,.jpeg" required><br><br>
        <button type="submit">Convert</button>
    </form>
    {% if download_link %}
        <br><br>
        <a href="{{ download_link }}">
            <button>Download Converted Images</button>
        </a>
    {% endif %}
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE, download_link=None)

@app.route("/convert", methods=["POST"])
def convert():
    files = request.files.getlist("images")
    if not files:
        return "No files selected", 400

    # Clear old files
    for f in os.listdir(OUTPUT_FOLDER):
        os.remove(os.path.join(OUTPUT_FOLDER, f))

    def convert_image(file):
        try:
            filename = os.path.splitext(file.filename)[0]
            save_path = os.path.join(OUTPUT_FOLDER, f"{filename}.png")
            img = Image.open(file.stream)
            img.save(save_path, "PNG")
        except Exception as e:
            print(f"Error converting {file.filename}: {e}")

    # Parallel conversion
    with ThreadPoolExecutor() as executor:
        executor.map(convert_image, files)

    # Create zip file
    zip_path = os.path.join(OUTPUT_FOLDER, "converted_images.zip")
    with zipfile.ZipFile(zip_path, "w") as zipf:
        for f in os.listdir(OUTPUT_FOLDER):
            if f.endswith(".png"):
                zipf.write(os.path.join(OUTPUT_FOLDER, f), f)

    return render_template_string(HTML_TEMPLATE, download_link=url_for("download_zip"))

@app.route("/download")
def download_zip():
    zip_path = os.path.join(OUTPUT_FOLDER, "converted_images.zip")
    return send_file(zip_path, as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)
