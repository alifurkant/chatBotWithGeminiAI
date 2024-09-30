
# PDF Chat Application

This application allows users to upload PDF files and interact with them via a chat interface. The system integrates with an AI model to process PDF content and respond to user queries.

## Features

- Upload PDF files securely.
- Chat with an AI to extract and interact with the content of uploaded PDFs.
- Supports only PDF files to ensure file integrity.
- Simple error handling for common issues like duplicate files, missing API keys, and non-existing PDFs.

## Requirements

- Python 3.8+
- Docker & Docker Compose
- FastAPI for the web framework
- genAI for AI model integration
- `pytest` for running unit tests
- `PyPDF2` for extracting text of pdfs

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/alifurkant/chatBotWithGeminiAI
cd chatBotWithGeminiAI
```

### 2. Environment Variables

Create a `.env` file in the root of your project with the following content:

```env
API_KEY=your_genai_api_key
APP_ENVIRONMENT = 'DEVELOPMENT' or 'PRODUCTION' according to your choice
```

### 3. Run with Docker Compose

A `docker-compose.yml` file is included to simplify running the application with Docker.

To start the application, run:

```bash
docker-compose up --build
```

This will build the necessary Docker images and start the application in a containerized environment.

- The app will be accessible at `http://localhost:8000`
- The Swagger interface will be accessible at http://localhost:8000/docs# if the app is not built in 'PRODUCTION' mode.
- Uploaded files are stored in the `app/docs/` directory inside the container.

### 4. Running the Application Locally (Without Docker)

If you prefer to run the application locally without Docker, follow these steps:

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Run the FastAPI app:

```bash
uvicorn api:app --reload
```

The app will now be running locally at `http://localhost:8000`.

### 5. Testing

Unit tests are provided for the application using `pytest`. To run the tests:

```bash
pytest
```


Tests cover:

- PDF file upload (success, invalid file type, duplicate files)
- Chat functionality (missing API key, non-existent PDF, successful response)

## Endpoints

### 1. **Upload PDF**

- **Endpoint**: `POST /pdf/`
- **Description**: Uploads a PDF file, extracts text from the PDF, generates a unique identifier using an AI model (if extracted text exists), and saves the file metadata.
  
- **Request**:
  - **Content Type**: `multipart/form-data`
  - **Body Parameters**:
    - `file`: The PDF file to upload (only PDF files are allowed).
  
- **Response**: Returns the generated PDF ID.
  
  ```json
  {
    "pdf_id": "unique_pdf_identifier"
  }
  ```

- **Validation Rules**:
  - Only files with a content type of `application/pdf` are allowed.
  - The file size must not exceed **5 MB**.
  - A file with the same name cannot already exist in the upload directory.

- **Example Request**:

  ```bash
  curl -X 'POST'     'http://localhost:8000/pdf/'     -H 'accept: application/json'     -H 'Content-Type: multipart/form-data'     -F 'file=@/path/to/yourfile.pdf'
  ```

- **Example Response**:

  ```json
  {
    "pdf_id": "HitchhikersGuide"
  }
  ```

### 2. **Chat with PDF**

- **Endpoint**: `POST /chat/{pdf_id}`
- **Description**: Sends a question or message to interact with a previously uploaded PDF file by its unique `pdf_id`. The system uses the PDF file and the provided message to generate a response using an AI model.
  
- **Path Parameters**:
  - `pdf_id`: The unique identifier for the PDF file.
  
- **Request**:
  - **Body Parameters**:
    - `message`: The message or question to ask about the PDF file.
  
  ```json
  {
    "message": "Explain the first chapter of the document."
  }
  ```

- **Response**: Returns a response generated from the AI model based on the provided message and the PDF content.
  
  ```json
  {
    "response": "The first chapter of the document discusses..."
  }
  ```

- **Example Request**:

  ```bash
  curl -X 'POST'     'http://localhost:8000/chat/HitchhikersGuide'     -H 'accept: application/json'     -H 'Content-Type: application/json'     -d '{
    "message": "Summarize the introduction of this document."
  }'
  ```

- **Example Response**:

  ```json
  {
    "response": "The introduction of the document outlines the main ideas of..."
  }
  ```

### Error Handling:

- **400 Bad Request**: Invalid file type, file size too large, or file with the same name already exists.
  ```json
  {
    "detail": "Invalid file type. Only PDFs are allowed."
  }
  ```
  
- **404 Not Found**: If a PDF with the given `pdf_id` does not exist.
  ```json
  {
    "detail": "PDF with ID 'HitchhikersGuide' not found."
  }
  ```
  
- **500 Internal Server Error**: General server error or issues with the AI model.
  ```json
  {
    "detail": "Error generating unique PDF identifier."
  }
  ```

### File Structure

├── app
│   ├── controllers
│   │   └── chat_controller.py
│   ├── models
│   │   ├── ChatRequestModel.py
│   │   └── ErrorHandlingMiddleware.py
│   │   └── PdfReturnModel.py
│   └── docs
│       ├── metadata.json
├── .env
├── api.py
├── docker-compose.yml
├── Dockerfile
├── README.md
├── requirements.txt
├── test_chat.py
└── TestPdfs
