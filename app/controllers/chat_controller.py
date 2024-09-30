from fastapi import UploadFile,HTTPException,APIRouter
from fastapi.responses import RedirectResponse
import google.generativeai as genai
import os,json
from app.models.ChatRequestModel import ChatRequestModel
import logging
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from datetime import datetime
from app.models.PdfReturnModel import PdfReturnModel

load_dotenv()

if os.environ.get("APP_ENVIRONMENT")=="PRODUCTION":
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

app_router = APIRouter(
    prefix="/v1",  
    tags=["v1"],   
)

@app_router.get("/", response_class = RedirectResponse, include_in_schema = False)
async def docs():
    return RedirectResponse(url = "/docs")

@app_router.post("/pdf/")
async def create_upload_file(file: UploadFile) -> PdfReturnModel:
    upload_directory = "app/docs/"
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB
    metadata_file_path = os.path.join(upload_directory, "metadata.json")

    # Validate file type and size
    if file.content_type != "application/pdf":
        logging.warning({"result": "An invalid file type was attempted to be loaded."})
        raise HTTPException(status_code=400, detail="Invalid file type. Only PDFs are allowed.")

    content = await file.read()  
    if len(content) > MAX_FILE_SIZE:
        logging.warning({"result": f"File '{file.filename}' exceeds the allowed size limit."})
        raise HTTPException(status_code=400, detail=f"File size exceeds the 5MB limit.")
    
    # Check if file with the same name already exists
    file_location = os.path.join(upload_directory, file.filename)
    if os.path.exists(file_location):
        logging.warning({"result": f"File '{file.filename}' already exists."})
        raise HTTPException(status_code=400, detail=f"File '{file.filename}' already exists. Please choose a different name for your file.")

    # Extract text from the PDF
    text = ""
    try:
        file.file.seek(0) 
        reader = PdfReader(file.file)
        for page in reader.pages:
            page_text = page.extract_text()
            text += page_text if page_text != ' \n' else ''
        logging.info({"extracted_text": text})
    except Exception as e:
        logging.error({"error": f"Failed to extract text from PDF: {str(e)}"})
        raise HTTPException(status_code=500, detail="Error extracting text from PDF.")
    
    # Load or initialize metadata
    if os.path.exists(metadata_file_path):
        with open(metadata_file_path, "r") as metadata_file:
            metadata = json.load(metadata_file)
    else:
        metadata = []
    # Generate a unique file name using the AI model
    if text != "":
        try:
            api_key = os.environ.get("API_KEY")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            logging.error({"error": f"Error initializing AI model: {str(e)}"})
            raise HTTPException(status_code=500, detail=f"Error initializing AI model: {str(e)}")

        # Prepare the question for the AI model
        question = f"""File names in my folder are: {[data['pdf_id'] for data in metadata]}. 
        Can you give me a one word unique PDF identifier without spaces for this text which is extracted from a PDF: {text[:500]}"""
        
        # Request AI model to generate a unique identifier
        try:
            response = model.generate_content(question)
            name_of_file = response.text.split(' ')[0]
        except Exception as e:
            logging.error({"error": f"Error generating unique file name: {str(e)}"})
            raise HTTPException(status_code=500, detail="Error generating unique PDF identifier.")

        
    else:
        name_of_file=file.filename

    # Add new metadata entry
    new_entry = {
        "pdf_id": name_of_file,
        "extracted_text": text[:500],
        "file_name" : file.filename,
        "creation_date" : datetime.now().strftime('%Y-%M-%d %H:%m')
    }
    metadata.append(new_entry)

    # Save updated metadata back to the metadata.json file
    try:
        with open(metadata_file_path, "w") as metadata_file:
            json.dump(metadata, metadata_file, indent=4)
        logging.info({"result": f"Metadata for '{name_of_file}' added."})
    except Exception as e:
        logging.error({"error": f"Failed to update metadata.json: {str(e)}"})
        raise HTTPException(status_code=500, detail="Error saving metadata.")
    # Save the file to the upload directory
    file_location = os.path.join(upload_directory, file.filename)
    with open(file_location, "wb") as f:
        f.write(content)
    logging.info({"result": f"File '{file.filename}' saved successfully."})

    # Return the PdfReturnModel with the generated pdf_id
    pdf_model = PdfReturnModel.Builder.builder().set_pdf_id(name_of_file).build()
    return pdf_model

@app_router.post("/chat/{pdf_id}")
async def chat(pdf_id: str, request_model: ChatRequestModel) -> dict:
    # Log the incoming request details
    logging.info({"message_of_request": request_model.message, "pdf_id": pdf_id})
    
    # Check if the API key is present in the environment
    api_key = os.environ.get("API_KEY")
    if not api_key:
        logging.error({"error": "API key is missing or not configured properly."})
        raise HTTPException(status_code=500, detail="API key is missing or not configured properly.")
    
    # Initialize the AI model
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-1.5-flash")
    except Exception as e:
        logging.error({"error": f"Error initializing AI model: {str(e)}"})
        raise HTTPException(status_code=500, detail=f"Error initializing AI model: {str(e)}")

    # Load metadata and find the corresponding PDF file
    metadata_file_path = os.path.join("app/docs", "metadata.json")
    if not os.path.exists(metadata_file_path):
        logging.error({"error": "Metadata file not found."})
        raise HTTPException(status_code=404, detail="Metadata file not found.")
    
    with open(metadata_file_path, "r") as metadata_file:
        metadata = json.load(metadata_file)
    
    # Find the PDF by its ID
    file_name = None
    for data in metadata:
        if data['pdf_id'] == pdf_id:
            file_name = data['file_name']
            break

    if not file_name:
        logging.error({"error": f"PDF with ID '{pdf_id}' not found in metadata."})
        raise HTTPException(status_code=404, detail=f"PDF with ID '{pdf_id}' not found in metadata.")
    
    # Check if the PDF file exists in the specified path
    pdf_path = os.path.join("app/docs", file_name)
    if not os.path.exists(pdf_path):
        logging.error({"error": f"PDF file '{file_name}' not found on disk."})
        raise HTTPException(status_code=404, detail=f"PDF file '{file_name}' not found.")

    # Upload the PDF file using the AI model
    try:
        sample_pdf = genai.upload_file(pdf_path)
    except Exception as e:
        logging.error({"error": f"Error uploading PDF file: {str(e)}"})
        raise HTTPException(status_code=500, detail=f"Error uploading PDF file: {str(e)}")
    
    # Generate content from the request message and PDF
    try:
        response = model.generate_content([request_model.message, sample_pdf])
    except Exception as e:
        logging.error({"error": f"Error generating content: {str(e)}"})
        raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")
    
    logging.info({"result": "Response returned successfully.", "response": response.text})
    return {"response": response.text}