from pydantic import BaseModel, Field

class PdfReturnModel(BaseModel):
    pdf_id: str = Field(..., description="The unique identifier of the PDF")

    class Builder:
        def __init__(self):
            self._pdf_id = None

        @staticmethod
        def builder():
            return PdfReturnModel.Builder()

        def set_pdf_id(self, pdf_id: str):
            self._pdf_id = pdf_id
            return self

        def build(self):
            if not self._pdf_id:
                raise ValueError("pdf_id must be set before building the PdfReturnModel")
            return PdfReturnModel(pdf_id=self._pdf_id)