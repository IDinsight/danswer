# This script converts all PDFs in a folder to text files using OCR. The final files are
# named based on what GPT-4 determines their title is. The first page of the PDF is used for this.

import pandas as pd
import io
import json
import os

import fitz  # PyMuPDF
import openai
import pytesseract
from PIL import Image

# Replace 'path_to_your_folder' with the path to your folder containing PDF files
folder_path = os.environ.get("FOLDER_PATH")
output_path = os.environ.get("OUTPUT_PATH")

SYSTEM = """
You will be given the text from the 1st page of a PDF file.

Identify the following -
- Title of the PDF file
- Date of publishing of the PDF file. Just respond with the year if you find nothing else.

Respond in the following json format -
{
    "title": "Infer the tile of the PDF based on text.",
    "date": "Date of file publishing (format - DD - 3 letter month-YYYY. Example - '01-Jan-2024'). If date is not available, respond with 'None'."
}
"""


def infer_name(text: str):
    # Infer the name of the PDF file using GPT4 based on data from the first page
    response = openai.chat.completions.create(
        model="gpt-4-1106-preview",
        temperature=0,
        messages=[
            {"role": "system", "content": SYSTEM},
            {"role": "user", "content": f"Text from the first page: '{text}'"},
        ],
        response_format={"type": "json_object"},
    )
    return response.choices[0].message.content


# Function to extract text from PDF
def extract_text_from_pdf(pdf_path, zoom_factor=4):
    pdf_document = fitz.open(pdf_path)
    extracted_text = ""

    # Loop through each page in the PDF
    n = 0
    for page_number in range(len(pdf_document)):
        n += 1
        print(n)
        # Get the page
        page = pdf_document[page_number]

        if n == 1:
            mat = fitz.Matrix(1, 1)
        else:
            mat = fitz.Matrix(zoom_factor, zoom_factor)

        # Render the page to a pixmap (image) with the zoom factor
        pix = page.get_pixmap(matrix=mat)

        img_data = pix.tobytes("png")
        image = Image.open(io.BytesIO(img_data))

        # Use pytesseract to do OCR on the image
        text = pytesseract.image_to_string(image, lang="eng")

        if n == 1:
            # Infer the name of the PDF file using GPT4 based on data from the first page
            inferred = json.loads(infer_name(text))
            inferred_name = inferred["title"]
            print(inferred_name)
            inferred_date = inferred["date"]
            print(inferred_date)

            # Add inferred date at the start of the text

            if inferred_date != "None":
                text = (
                    f'#DANSWER_METADATA={{"doc_updated_at": "{inferred_date}"}}'
                    + "\n"
                    + text
                )

        extracted_text += text
        break

    pdf_document.close()
    return {"text": extracted_text, "title": inferred_name, "date": inferred_date}


if __name__ == "__main__":
    file_names_list = []
    n = 0
    # Loop through each file in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            n += 1
            # Extract text from the PDF
            extracted = extract_text_from_pdf(
                os.path.join(folder_path, filename), zoom_factor=4
            )
            text = extracted["text"]
            title = extracted["title"]
            date = extracted["date"]

            file_names_list.append(
                {"file_name": filename, "inferred_name": title, "date": date}
            )
            print(file_names_list)

            output_file_path = os.path.join(output_path, f"{title}.txt")
            with open(output_file_path, "w") as file:
                file.write(text)

    # Create DF to save stuff in
    file_names = pd.DataFrame(columns=["file_name", "inferred_name", "date"])
    file_names = file_names.from_records(file_names_list)
    file_names.to_csv(os.path.join(output_path, "file_names.csv"))
