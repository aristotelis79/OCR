import pytesseract
import cv2
import bardapi
import re
import os 
import numpy as np
from django.shortcuts import render
from qrdet import QRDetector
from qreader import QReader
from revChatGPT.V1 import Chatbot
#from PIL import Image

def home(request):
    if 'qrcode' in request.POST:
        return qrcode(request)
    if 'textreq' in request.POST:
        return textreq(request)
    return render(request, "home/app.html", {'json_data': ''})

def qrcode(request):
    if request.method != 'POST' or request.FILES.get('invoice', None) is None :
        return render(request, "home/app.html", {'json_data': ''})

    detector = QRDetector()
    image = cv2.imdecode(np.fromstring(request.FILES['invoice'].read(), np.uint8), cv2.IMREAD_UNCHANGED)
    detections = detector.detect(image=image, is_bgr=True)

    (x1, y1, x2, y2), confidence = detections[0]
    qr_image = image[y1:y2, x1:x2]
        
    # # Save the results
    # cv2.imwrite(filename='1_b.jpg', img=qr_image)

    qreader = QReader()
    image = cv2.cvtColor(qr_image, cv2.COLOR_BGR2RGB)
    decoded_code = qreader.detect_and_decode(image=image)

    return render(request, "home/app.html", {'json_data': decoded_code})

def textreq(request):
    if request.method != 'POST' or request.FILES.get('invoice', None) is None :
        return render(request, "home/app.html", {'json_data': 'Not valid request'})
    
    #img = Image.open(request.FILES['invoice']) 
    image = cv2.imdecode(np.fromstring(request.FILES['invoice'].read(), np.uint8), cv2.IMREAD_UNCHANGED)
    text = pytesseract.image_to_string(image, config= r'-l ell+eng --psm 6')
        
    prompt_keys = request.POST.get('prompt_keys')
    extra_prompts = request.POST.get('extra_prompts')
    if extra_prompts:
        prompt_keys += ","+ extra_prompts 

    prompt = request.POST.get('prompt').format(prompt_keys)
    prompt += "'" + text + "'"

    return render(request, "home/app.html", {'json_data': bard(prompt)})
    
def bard(prompt):
    response = bardapi.core.Bard(os.environ.get('BARD1PSID')).get_answer(prompt)
    
    return getJson(response['content'], r'```(.*?)```')

def chatGPT(prompt):
    chatbot = Chatbot(config={
      "access_token": os.environ.get('CHATGPT')
    })
    
    for data in chatbot.ask(prompt):
        response = data["message"]
    #response = "To extract the values from the Greek text for the given indicators (\'αριθμός\', \'σύνολο\', \'τελικό ποσό\', \'πληρωτέο ποσό\', \'αρ.παραστατικού\', \'ημερομηνία\', \'ΑΦΜ\'), we need to first identify the text segments containing these indicators and then extract the corresponding values. Let\'s proceed step by step:\n\n1. Identify the segments with the indicators.\n2. Extract the values corresponding to each indicator.\n\nAfter extracting the values, we will represent the results in JSON format. Please note that the provided text contains some non-Greek characters (e.g., English characters and symbols) and seems to be a mix of different information. To focus only on the relevant parts, I will assume that the values we are interested in are the numerical ones and not the non-Greek characters.\n\nHere\'s the extracted information in JSON format:\n\n```json\n{\n  \"αριθμός\": 997609880,\n  \"σύνολο\": 21.40,\n  \"τελικό ποσό\": 2.80,\n  \"πληρωτέο ποσό\": 24.20,\n  \"αρ.παραστατικού\": \"1129614\",\n  \"ημερομηνία\": \"2307201124\",\n  \"ΑΦΜ\": \"849712\"\n}\n```\n\nPlease note that this JSON representation only includes the values corresponding to the indicators. The extracted values are:\n\n- \'αριθμός\': 997609880\n- \'σύνολο\': 21.40\n- \'τελικό ποσό\': 2.80\n- \'πληρωτέο ποσό\': 24.20\n- \'αρ.παραστατικού\': \"1129614\"\n- \'ημερομηνία\': \"2307201124\"\n- \'ΑΦΜ\': \"849712\"\n\nKeep in mind that the accuracy of the extraction is based on the assumption that the provided text is consistent and the values are represented in a predictable format. If there are variations or missing information, the extraction may require additional processing steps or handling specific cases."
    return getJson(response, r'```json\n{\n.*?\n}\n```')

def getJson(input, pattern):
    match = re.search(pattern, input, re.DOTALL)

    if match:
        json_string = match.group(match.re.groups).strip().replace('json','')

    return json_string if json_string else '{}' 