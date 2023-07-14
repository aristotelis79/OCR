import pytesseract
import cv2
import numpy
import bardapi
import re
import os 

from PIL import Image
from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    if request.method == 'POST' and request.FILES['invoice']:
        #img = Image.open(request.FILES['invoice']) 
        img = cv2.imdecode(numpy.fromstring(request.FILES['invoice'].read(), numpy.uint8), cv2.IMREAD_GRAYSCALE)
        text = pytesseract.image_to_string(img, config= r'-l ell+eng --psm 6')
        
        promt_keys = ['Αριθμος', 'Συνολο', 'ΑΦΜ, ''πληρωτεο Ποσο' , 'Αρ.Παραστατικού', 'Ημερομηνία']
        extra_promts = request.POST.get('extra_promts')
        if(extra_promts):
            extra_promts.split(',')
            promt_keys.extend(extra_promts)


        promt = "Find and write the values of indicators ({}) from the greek text and return only the json with the values"\
                .format(", ".join("{}".format(value) for value in promt_keys))
        promt += "'" + text + "'"
        response = bardapi.core.Bard(os.environ.get('__Secure-1PSID')).get_answer(promt)

        return render(request, "home/app.html", {'json_data': getJson(response['content'])})
    
    return render(request, "home/app.html", {'json_data': ''})

def getJson(input):
    pattern = r'```(.*?)```'
    match = re.search(pattern, input, re.DOTALL)

    if match:
        json_string = match.group(1).strip().replace('json','')
    
    return json_string if json_string else '{}' 
