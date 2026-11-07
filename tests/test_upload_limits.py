from fastapi.testclient import TestClient
from app import main

client = TestClient(main.app)

# A tiny, valid 1-page PDF written by hand (no real file needed)
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]>>endobj\n"
    b"trailer<</Root 1 0 R>>\n"
    b"%%EOF"
)

def upload(content):
    return client.post(
        "/upload",
        files={"file":("test.pdf",content,"application/pdf")},
    )

def test_rejects_file_that_is_too_large(monkeypatch):
    monkeypatch.setattr(main,"MAX_UPLOAD_MB", 1)  # set max upload size to 1 MB for this test
    too_big = b"0" * (1024 * 1024 + 1) # 1 byte over 1 MB

    response = upload(too_big)

    assert response.status_code == 413
    assert "too large" in response.json()["detail"]


def test_rejects_pdf_with_too_many_pages(monkeypatch):
    monkeypatch.setattr(main,"MAX_PAGES", 0)  # even 1 page is too many

    response = upload(MINIMAL_PDF)

    assert response.status_code == 413
    assert "pages" in response.json()["detail"]

def test_rejects_damaged_pdf():
    response = upload(b"this is not a real pdf")

    assert response.status_code == 400
    assert "Could not read" in response.json()["detail"]
