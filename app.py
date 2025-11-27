from flask import Flask, request, jsonify
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import base64
import os

app = Flask(__name__)

# Optional: API key (set in Render environment variables)
API_KEY = os.getenv("API_KEY", None)

@app.route("/stamp", methods=["POST"])
def stamp_pdf():
    try:
        # --- Simple API key check (optional but recommended) ---
        if API_KEY:
            header_key = request.headers.get("x-api-key")
            if header_key != API_KEY:
                return jsonify({"error": "Unauthorized"}), 401

        data = request.json or {}
        pdf_base64 = data.get("pdf_base64")
        if not pdf_base64:
            return jsonify({"error": "pdf_base64 is required"}), 400

        stamp_text = data.get("stamp_text", "APPROVED")
        x = int(data.get("x", 100))
        y = int(data.get("y", 100))
        original_file_name = data.get("file_name", "document.pdf")

        # Decode the original PDF
        pdf_bytes = base64.b64decode(pdf_base64)
        original_pdf = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()

        # Get original first page size (instead of fixed letter)
        first_page = original_pdf.pages[0]
        page_width = float(first_page.mediabox.width)
        page_height = float(first_page.mediabox.height)

        # Create a stamp overlay with same size as original page
        stamp_buffer = io.BytesIO()
        c = canvas.Canvas(stamp_buffer, pagesize=(page_width, page_height))
        c.setFont("Helvetica-Bold", 36)
        c.setFillColorRGB(0, 0.7, 0)  # green color
        c.drawString(x, y, stamp_text)
        c.save()

        stamp_pdf = PdfReader(io.BytesIO(stamp_buffer.getvalue()))
        stamp_page = stamp_pdf.pages[0]

        # Merge stamp onto the first page
        first_page.merge_page(stamp_page)
        writer.add_page(first_page)

        # Add other pages unchanged
        for i in range(1, len(original_pdf.pages)):
            writer.add_page(original_pdf.pages[i])

        # Output final PDF
        output_buffer = io.BytesIO()
        writer.write(output_buffer)
        output_bytes = output_buffer.getvalue()
        output_base64 = base64.b64encode(output_bytes).decode("utf-8")

        # Generate signed file name
        if original_file_name.lower().endswith(".pdf"):
            signed_name = original_file_name[:-4] + "_signed.pdf"
        else:
            signed_name = original_file_name + "_signed.pdf"

        # Return a response convenient for Power Automate
        return jsonify({
            "fileName": signed_name,
            "fileContent": output_base64
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    # For local test; on Render you’ll usually use gunicorn
    app.run(host="0.0.0.0", port=10000)
