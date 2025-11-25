from flask import Flask, request, jsonify
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
import base64

app = Flask(__name__)

@app.route("/stamp", methods=["POST"])
def stamp_pdf():
    try:
        data = request.json
        pdf_base64 = data.get("pdf_base64")
        stamp_text = data.get("stamp_text", "APPROVED")
        x = data.get("x", 100)
        y = data.get("y", 100)

        # Decode the original PDF
        pdf_bytes = base64.b64decode(pdf_base64)
        original_pdf = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()

        # Create a stamp overlay
        stamp_buffer = io.BytesIO()
        c = canvas.Canvas(stamp_buffer, pagesize=letter)
        c.setFont("Helvetica-Bold", 36)
        c.setFillColorRGB(0, 0.7, 0)  # green color
        c.drawString(x, y, stamp_text)
        c.save()

        stamp_pdf = PdfReader(io.BytesIO(stamp_buffer.getvalue()))
        stamp_page = stamp_pdf.pages[0]

        # Merge stamp onto the first page
        first_page = original_pdf.pages[0]
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

        return jsonify({"output_pdf_base64": output_base64})

    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)