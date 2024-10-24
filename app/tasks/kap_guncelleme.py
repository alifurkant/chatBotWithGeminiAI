import os,requests
import logging,time
from datetime import datetime
from app.tasks.chat import chat
from bs4 import BeautifulSoup
from app.models.Notification import Notification
from app.models.NotificationResultModel import NotificationResultModel
from typing import List

class kap_guncelleme:
    def __init__(self):
        pass

    def get_target_folder()->str:
        today_date = datetime.now().strftime("%Y-%m-%d")
        target_folder = f"app/docs/{today_date}"
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
        return target_folder
    
    def get_notifications_list()->List[Notification]:
        url = "https://www.kap.org.tr/tr/api/disclosures"
        response = requests.get(url)
        data_list=[data['basic'] for data in response.json()]
        data_model_list = [Notification(**data) for data in data_list]
        return data_model_list

    def downloading_process(data_list:List[Notification],target_folder:str)->List[NotificationResultModel]:
        pdf_filename_list=[]
        baseUrl = "https://www.kap.org.tr/tr/BildirimPdf/"

        for data in data_list:
            try:
                bildirimId = data.disclosureIndex

                url = "https://www.kap.org.tr/tr/Bildirim/" + str(bildirimId)
                response = requests.get(url)
                soup = BeautifulSoup(response.text, 'html.parser')
                ek_indir_links = soup.find_all('a', href=lambda href: href and 'ek-indir' in href)
                code = data.stockCodes if len(data.stockCodes) > 3 else data.relatedStocks

                if len(ek_indir_links) > 0:
                    for link in ek_indir_links:
                        eklink = "https://www.kap.org.tr/" + link["href"]
                        response_pdf = requests.get(eklink)
                        pdf_filename = os.path.join(target_folder, code + "-" + str(bildirimId) + "No'lu Bildirimin İçindeki PDF.pdf")
                        if not os.path.exists(pdf_filename):
                            with open(pdf_filename, 'wb') as file:
                                file.write(response_pdf.content)
                                logging.info(f"{pdf_filename} başarıyla indirildi.")
                            pdf_filename_list.append(NotificationResultModel(title=data.title,ai_result="",date=data.publishDate,file_path=pdf_filename,code=code))

                pdf_link = baseUrl + str(bildirimId)
                response_pdf = requests.get(pdf_link)

                if response_pdf.status_code == 200:
                    pdf_filename = os.path.join(target_folder, code + "-"  + str(bildirimId) + ".pdf")
                    if not os.path.exists(pdf_filename):
                        with open(pdf_filename, 'wb') as file:
                            file.write(response_pdf.content)
                            logging.info(f"{pdf_filename} başarıyla indirildi.")
                        pdf_filename_list.append(NotificationResultModel(title=data.title,ai_result="",date=data.publishDate,file_path=pdf_filename,code=code))
                else:
                    logging.warning(f"Hata: {response_pdf.status_code} - İndirme başarısız.")

                time.sleep(5)
            except Exception as e:
                logging.warning(e)
                time.sleep(60)
        return pdf_filename_list
    
    def download_bussiness_relation_pdfs()->List[NotificationResultModel]:
        
        target_folder = kap_guncelleme.get_target_folder()

        model_list = kap_guncelleme.get_notifications_list()
        
        new_bussiness_relation_list = [notification for notification in model_list if notification.title=="Yeni İş İlişkisi"]

        pdf_filename_list=kap_guncelleme.downloading_process(new_bussiness_relation_list,target_folder)
            
        
        return pdf_filename_list
    
    def download_notification_pdfs()->List[NotificationResultModel]:
        
        target_folder = kap_guncelleme.get_target_folder()

        model_list = kap_guncelleme.get_notifications_list()

        restriction_list=[
            "Yeni İş İlişkisi",
            "İhale Süreci / Sonucu",
            "Sermaye Artırımı - Azaltımı İşlemlerine İlişkin Bildirim",
            "Pay Alım Satım Bildirimi",
            "İhraç Tavanına İlişkin Bildirim",
            "Payların Geri Alınmasına İlişkin Bildirim",
            "Kar Payı Dağıtım İşlemlerine İlişkin Bildirim",
            "Borsada İşlem Gören Tipe Dönüşüm Duyurusu"
        ]
        # restricted_model = [notification for notification in model_list if notification.title in restriction_list]
        # pdf_filename_list=kap_guncelleme.downloading_process(restricted_model,target_folder)
        pdf_filename_list=kap_guncelleme.downloading_process(model_list,target_folder)
        
        return pdf_filename_list
    
    @staticmethod
    def get_notification_results_from_ai(path_list:List[NotificationResultModel]):
        
        api_key = chat.get_apikey()

        model = chat.initialize_genai(api_key)

        
        if path_list == [] : return {"result": "Yeni Bildirim Bulunamadı."}
        for path in path_list:
        # Upload the PDF file using the AI model
            sample_pdf=chat.upload_pdf_to_genai(pdf_path=path.file_path)
            
            # Generate content from the request message and PDF
            response = chat.generate_content(model,"Senden tek kelimelik bir cevap bekliyorum. Bu pdf'te anlatılan şey şirketin hisseleri için aşağıdakilerden hangisi gibi olur: çok olumlu, olumlu, nötr, olumsuz, çok olumsuz?",sample_pdf)

            response_text=response.text.split('\n')[0]
            logging.info({"result": "Response returned successfully.", "response": response_text})
            path.ai_result=response_text
        return path_list
