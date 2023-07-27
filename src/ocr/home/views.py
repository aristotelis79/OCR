import pytesseract
import cv2
#import bardapi
import re
import os
import requests
import imutils
import numpy as np

from skimage.filters import threshold_local
from .transform import perspective_transform
from urllib.parse import urlparse
from urllib.parse import parse_qs
from django.shortcuts import render
from django.conf.urls.static import static
from django.conf import settings
from qrdet import QRDetector
from qreader import QReader
from revChatGPT.V1 import Chatbot
#from PIL import Image

IMG_RESIZE_H = 500.0
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

    invoice_file = request.FILES['invoice']
    
    detector = QRDetector()
    buf = np.asarray(bytearray(invoice_file.read()),np.uint8)
    #buf = np.fromstring(request.FILES['invoice'].read(), np.uint8)
    image = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
    detections = detector.detect(image=image, is_bgr=True)

    (x1, y1, x2, y2), confidence = detections[0]
    qr_image = image[y1:y2, x1:x2]

    qreader = QReader()
    image = cv2.cvtColor(qr_image, cv2.COLOR_BGR2RGB)
    decoded_code = qreader.detect_and_decode(image=image)
    
    if len(decoded_code) == 0:
        return render(request, "home/app.html", {'json_data': ''})
    
    # Draw the detections
    cv2.rectangle(image, (x1, y1), (x2, y2), color=(0, 255, 0), thickness=2)
    cv2.putText(image, f'{confidence:.2f}', (x1, y1 - 10), fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                fontScale=1, color=(0, 255, 0), thickness=2)
        
    image_url = get_media_url(invoice_file.name, image)

    urlParams = aadeParams(decoded_code[0])
    json_data = requests.get(url = f"{AADE_BASE_QRCODE_URL}{urlParams[0]}/{urlParams[1]}/{urlParams[2]}", headers={'Accept': 'application/json'})
    return render(request, "home/app.html", 
                {
                    'json_data': json_data.text,
                    'invoice_preview': image_url 
                }) 

def textreq(request):
    if request.method != 'POST' or request.FILES.get('invoice', None) is None :
        return render(request, "home/app.html", {'json_data': 'Not valid request'})
    
    # #img = Image.open(request.FILES['invoice'])
    # buf = np.asarray(bytearray(request.FILES['invoice'].read()),np.uint8)
    # #buf = np.fromstring(request.FILES['invoice'].read(), np.uint8)
    # image = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)

    invoice_file = request.FILES['invoice']
    
    crop_image = crop(invoice_file)

    gray_image = enhance_contrast(crop_image)

    # # Detect lines in the image using Hough transform
    # lines = cv2.HoughLinesP(gray_image, 1, np.pi/180, 200)

    text = pytesseract.image_to_string(gray_image, config= r'-l ell+eng --psm 12', )
        
    prompt_keys = request.POST.get('prompt_keys')
    extra_prompts = request.POST.get('extra_prompts')
    if extra_prompts:
        prompt_keys += ","+ extra_prompts 

    prompt = request.POST.get('prompt').format(prompt_keys)
    prompt += "'" + text + "'"

    image_url = get_media_url(invoice_file.name, gray_image)

    return render(request, "home/app.html", 
                {
                    'json_data': chatGPT(prompt),
                    'invoice_preview': image_url 
                })

def crop(invoice_file):
    # Passing the image path
    image = np.asarray(bytearray(invoice_file.read()),np.uint8)
    original_img = cv2.imdecode(image, cv2.IMREAD_COLOR)
    copy = original_img.copy()

    # The resized height in hundreds
    # ratio = original_img.shape[0] / IMG_RESIZE_H
    # img_resize = imutils.resize(original_img, height=500)
    
    # Converting the Resized Image to Grayscale
    gray_image = cv2.cvtColor(original_img, cv2.COLOR_BGR2GRAY)

    # Applying an Edge Detector
    blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
    edged_img = cv2.Canny(blurred_image, 75, 200)

    # Finding the Largest Contour
    cnts, _ = cv2.findContours(edged_img, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]
    for c in cnts:
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)
        if len(approx) == 4:
            doc = approx
            break

    # Circling the Four Corners of the Document Contour
    p = []
    for d in doc:
        tuple_point = tuple(d[0])
        cv2.circle(original_img, tuple_point, 3, (0, 0, 255), 4)
        p.append(tuple_point)
    
    # Using Warp Perspective to Get the Desired Image
    warped_image = perspective_transform(copy, doc.reshape(4, 2))
    
    return warped_image

def enhance_contrast(warped_image):
    warped_image = cv2.cvtColor(warped_image, cv2.COLOR_BGR2GRAY)

    # Applying Adaptive Threshold and Saving the Scanned Output
    T = threshold_local(warped_image, 11, offset=10, method="gaussian")
    # Apply thresholding to enhance contrast
    #thresh = cv2.threshold(warped, 0, 255, cv2.THRESH_BINARY)[1]
    warped = (warped_image > T).astype("uint8") * 255
  
    return warped

def get_media_url(name, image, prefix = 'scan'):
    image_url = 'static/home' + settings.MEDIA_URL + f"{prefix}_{name}"
    image_path = os.path.join(settings.BASE_DIR, 'ocr', 'home', image_url)
    cv2.imwrite(image_path, image)
    return image_url

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

# def bard(prompt):
#     response = bardapi.core.Bard(os.environ.get('BARD1PSID')).get_answer(prompt)
#     return getJson(response['content'], r'```(.*?)```')