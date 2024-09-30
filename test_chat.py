import pytest,os,json
from fastapi.testclient import TestClient
from api import app 
from unittest.mock import patch
from app.models.ChatRequestModel import ChatRequestModel

client = TestClient(app)

def test_upload_file_invalid_type():
    with open("test.txt", "wb") as f:
        f.write(b"This is not a PDF file.")
    
    with open("test.txt", "rb") as f:
        response = client.post("v1/pdf/", files={"file": ("test.txt", f, "text/plain")})
    
    os.remove('test.txt')
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid file type. Only PDFs are allowed."}

def test_upload_file_already_exists():
    file_name = "test.pdf"
    file_path = f"app/docs/{file_name}"

    with open(file_path, "wb") as f:
        f.write(b"PDF content.")

    with open(file_path, "rb") as f:
        response = client.post("v1/pdf/", files={"file": (file_name, f, "application/pdf")})

    assert response.status_code == 400
    assert response.json() == {"detail": f"File '{file_name}' already exists. Please choose a different name for your file."}
    os.remove(file_path)

@pytest.mark.parametrize("pdf_file", os.listdir('app/test_pdfs'))
def test_create_upload_file(pdf_file):
    test_pdf_path = os.path.join('app/test_pdfs', pdf_file)

    pdf_path=os.path.join('app/docs/', pdf_file)
    if os.path.exists(pdf_path):
        os.remove('app/docs/'+pdf_file)
    
    with open(test_pdf_path, "rb") as file:
        response = client.post("v1/pdf/", files={"file": (pdf_file, file, "application/pdf")})
    
    assert response.status_code == 200, f"Failed to upload {pdf_file}"
    data = response.json()
    assert "pdf_id" in data, f"Response missing 'pdf_id' for {pdf_file}"

    metadata = load_metadata()

    for data in metadata:
        if data['file_name']==pdf_file:
            metadata.remove(data)
    metadata_file_path = os.path.join('app/docs', "metadata.json")
    with open(metadata_file_path, "w") as metadata_file:
        json.dump(metadata, metadata_file, indent=4)
    
    if os.path.exists(pdf_path):
        os.remove('app/docs/'+pdf_file)
    
# @pytest.fixture(scope="module")
def load_metadata():
    metadata_file_path = os.path.join('app/docs', "metadata.json")
    if os.path.exists(metadata_file_path):
        with open(metadata_file_path, "r") as metadata_file:
            metadata = json.load(metadata_file)
    else:
        metadata = []
    return metadata

@pytest.mark.parametrize("data", load_metadata())
def test_chat(data):
    pdf_id = data['pdf_id']
    message = "what is this pdf about?"
    
    request_model = ChatRequestModel(message=message)
    
    response = client.post(f"/v1/chat/{pdf_id}", json=request_model.dict())
    
    assert response.status_code == 200, f"Failed to chat with PDF ID {pdf_id}"
    data = response.json()
    assert "response" in data, f"Chat response missing for PDF ID {pdf_id}"

@patch("google.generativeai.configure")
def test_chat_api_key_missing(mock_configure):
    with patch.dict(os.environ, {"API_KEY": ""}):
        pdf_id = "test"
        request_model = ChatRequestModel(message="Test message")

        response = client.post(f"v1/chat/{pdf_id}", json={"message": request_model.message})
        
        assert response.status_code == 500
        assert response.json() == {"detail": "API key is missing or not configured properly."}