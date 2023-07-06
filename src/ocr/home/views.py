from datetime import datetime

from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return render(request, "home/app.html",
        {'message': "This is an ocr app",
        'msg_class': "main_msg"})
