import pytesseract
import cv2
#import bardapi
import re
import os
import requests
import numpy as np
from urllib.parse import urlparse
from urllib.parse import parse_qs
from django.shortcuts import render
from qrdet import QRDetector
from qreader import QReader
from revChatGPT.V1 import Chatbot
#from PIL import Image

AADE_BASE_QRCODE_URL = "https://appodixi.aade.gr/appodixiapps/QrCodesService/webresources/qrcode/ese_esi/"

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

    qreader = QReader()
    image = cv2.cvtColor(qr_image, cv2.COLOR_BGR2RGB)
    decoded_code = qreader.detect_and_decode(image=image)
    
    if len(decoded_code) == 0:
        return render(request, "home/app.html", {'json_data': ''})

    urlParams = aadeParams(decoded_code[0])
    json_data = requests.get(url = f"{AADE_BASE_QRCODE_URL}{urlParams[0]}/{urlParams[1]}/{urlParams[2]}", headers={'Accept': 'application/json'})
    return render(request, "home/app.html", {'json_data': json_data.text}) 

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

    return render(request, "home/app.html", {'json_data': chatGPT(prompt)})
    
# def bard(prompt):
#     response = bardapi.core.Bard(os.environ.get('BARD1PSID')).get_answer(prompt)
    
#     return getJson(response['content'], r'```(.*?)```')

def chatGPT(prompt):
    chatbot = Chatbot(config={
      "access_token": os.environ.get('CHATGPT')
    })
    
    for data in chatbot.ask(prompt):
        response = data["message"]

    return getJson(response, r'```json\n{\n.*?\n}\n```')

def getJson(input, pattern):
    match = re.search(pattern, input, re.DOTALL)

    if match:
        json_string = match.group(match.re.groups).strip().replace('json','').replace('```','')

    return json_string if json_string else '{}'

def aadeParams(url):
    sig = parse_qs(urlparse(url).query)['SIG'][0]
    return [sig[:11],sig[11:19],sig[19:59]]
