import base64
import numpy
from django import template
  
register = template.Library()

@register.filter
def base64_encode(value):
    if type(value) is numpy.ndarray:
        return base64.b64encode(value).decode('utf-8')