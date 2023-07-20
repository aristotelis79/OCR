import pytesseract
import cv2
import numpy
import bardapi
import re
import os 
from qreader import QReader 

#from PIL import Image
from django.shortcuts import render

def qrcode(request):
    if request.method != 'POST' or request.FILES.get('invoice', None) is None :
        return render(request, "home/app.html", {'json_data': ''})

    qreader = QReader()
    im = cv2.imdecode(numpy.fromstring(request.FILES['invoice'].read(), numpy.uint8), cv2.IMREAD_UNCHANGED)
    image = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    decoded_code = qreader.detect_and_decode(image=image)

    return render(request, "home/app.html", {'json_data': decoded_code})

def home(request):
    if request.method != 'POST' or request.FILES.get('invoice', None) is None :
        return render(request, "home/app.html", {'json_data': 'Not valid request'})
    
    #img = Image.open(request.FILES['invoice']) 
    image = cv2.imdecode(numpy.fromstring(request.FILES['invoice'].read(), numpy.uint8), cv2.IMREAD_GRAYSCALE)
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
