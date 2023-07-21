import pytesseract
import cv2
import bardapi
import re
import os 
import numpy as np
#from imutils import perspective
#from rembg.bg import remove as rembg
from django.http import FileResponse
from django.shortcuts import render
from io import BytesIO
from qrdet import QRDetector
from qreader import QReader 
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
        
    promt_keys = request.POST.get('promt_keys')
    extra_promts = request.POST.get('extra_promts')
    if(extra_promts):
        promt_keys += ","+ extra_promts 

    promt = request.POST.get('promt').format(promt_keys)
    promt += "'" + text + "'"
    response = bardapi.core.Bard(os.environ.get('BARD1PSID')).get_answer(promt)

    return render(request, "home/app.html", {'json_data': getJson(response['content'])})
    

def getJson(input):
    pattern = r'```(.*?)```'
    match = re.search(pattern, input, re.DOTALL)

    if match:
        json_string = match.group(1).strip().replace('json','')
    
    return json_string if json_string else '{}' 