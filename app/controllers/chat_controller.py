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
from app.tasks.chat import chat

load_dotenv()

if os.environ.get("APP_ENVIRONMENT")=="PRODUCTION":
    logging.basicConfig(level=logging.WARNING)
else:
    logging.basicConfig(level=logging.INFO)

chat_router = APIRouter(
    prefix="/AI",  
    tags=["AI"],   
)

@chat_router.get("/", response_class = RedirectResponse, include_in_schema = False)
async def docs():
    return RedirectResponse(url = "/docs")

@chat_router.post("/pdf/")
async def create_upload_file(file: UploadFile) -> PdfReturnModel:
    upload_directory = "docs/"
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

    pdf_model = PdfReturnModel.Builder.builder().set_pdf_id(name_of_file).build()
    return pdf_model

@chat_router.post("/chat/{pdf_id}")
async def chat_ai(pdf_id: str, request_model: ChatRequestModel) -> dict:

    logging.info({"message_of_request": request_model.message, "pdf_id": pdf_id})
    
    api_key = chat.get_apikey()

    model = chat.initialize_genai(api_key)

    file_name=pdf_id
    
    pdf_path = chat.get_pdf_path(request_model.date,file_name)

    # Upload the PDF file using the AI model
    sample_pdf=chat.upload_pdf_to_genai(pdf_path=pdf_path)
    
    # Generate content from the request message and PDF
    response = chat.generate_content(model,request_model.message,sample_pdf)
    
    logging.info({"result": "Response returned successfully.", "response": response.text})
    return {"response": response.text}