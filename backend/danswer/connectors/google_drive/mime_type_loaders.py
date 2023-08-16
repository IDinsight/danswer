import io
import tempfile

import docx2txt
from googleapiclient import discovery  # type: ignore
from PyPDF2 import PdfReader

MIME_TYPE_LOADERS = {}


def mimetype_loader(mimetype: str):
    def decorator(func):
        MIME_TYPE_LOADERS[mimetype] = func
        return func

    return decorator


@mimetype_loader("application/vnd.google-apps.document")
def load_google_doc(file_id: str, service: discovery.Resource) -> str:
    return (
        service.files()
        .export(fileId=file_id, mimeType="text/plain")
        .execute()
        .decode("utf-8")
    )


@mimetype_loader("application/vnd.google-apps.spreadsheet")
def load_google_sheet(file_id: str, service: discovery.Resource) -> str:
    return (
        service.files()
        .export(fileId=file_id, mimeType="text/csv")
        .execute()
        .decode("utf-8")
    )


@mimetype_loader("application/pdf")
def load_pdf(file_id: str, service: discovery.Resource) -> str:
    response = service.files().get_media(fileId=file_id).execute()
    pdf_stream = io.BytesIO(response)
    pdf_reader = PdfReader(pdf_stream)
    return "\n".join(page.extract_text() for page in pdf_reader.pages)


@mimetype_loader(
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
)
def load_docx(file_id: str, service: discovery.Resource) -> str:
    response = service.files().get_media(fileId=file_id).execute()
    word_stream = io.BytesIO(response)
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp.write(word_stream.getvalue())
        temp_path = temp.name
    return docx2txt.process(temp_path)
