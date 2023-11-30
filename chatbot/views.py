# Trong chatbot/views.py
from django.shortcuts import render

def chatbot(request):
    # Xử lý logic của chatbot
    return render(request, 'chatbot/chatbot.html')