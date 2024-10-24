from fastapi import HTTPException
import google.generativeai as genai
import logging,os
from google.generativeai.types import file_types
from google.generativeai.types import generation_types

class chat:
    def __init__(self):
        pass

    @staticmethod
    def initialize_genai(api_key:str)->genai.GenerativeModel:
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
        except Exception as e:
            logging.error({"error": f"Error initializing AI model: {str(e)}"})
            raise HTTPException(status_code=500, detail=f"Error initializing AI model: {str(e)}")
        
        return model
        
    @staticmethod
    def get_apikey()->str:
        api_key = os.environ.get("API_KEY")
        if not api_key:
            logging.error({"error": "API key is missing or not configured properly."})
            raise HTTPException(status_code=500, detail="API key is missing or not configured properly.")
        return api_key
    
    @staticmethod
    def get_pdf_path(date:str,file_name:str)->str:
        pdf_path = os.path.join("app\\docs",date, file_name+".pdf")
        if not os.path.exists(pdf_path):
            logging.error({"error": f"PDF file '{file_name}' not found on disk."})
            raise HTTPException(status_code=404, detail=f"PDF file '{file_name}' not found.")
        return pdf_path
    
    @staticmethod 
    def upload_pdf_to_genai(pdf_path:str)->file_types.File:
        try:
            sample_pdf = genai.upload_file(pdf_path)
        except Exception as e:
            logging.error({"error": f"Error uploading PDF file: {str(e)}"})
            raise HTTPException(status_code=500, detail=f"Error uploading PDF file: {str(e)}")
        
        return sample_pdf
    
    @staticmethod 
    def generate_content(model:genai.GenerativeModel,message:str,sample_pdf:file_types.File)->generation_types.GenerateContentResponse:
        try:
            response = model.generate_content([message, sample_pdf])
        except Exception as e:
            logging.error({"error": f"Error generating content: {str(e)}"})
            raise HTTPException(status_code=500, detail=f"Error generating content: {str(e)}")
        
        return response