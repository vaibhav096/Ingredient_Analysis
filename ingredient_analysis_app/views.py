# ingredient_analysis_app/views.py

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import IngredientAnalysis
from PIL import Image
import pytesseract
import cv2
import numpy as np
import os
import re
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv
load_dotenv()
import easyocr
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Set your environment variables (these should be stored securely)
os.environ["LANGCHAIN_TRACING_V2"] = "true"
# os.environ["LANGCHAIN_API_KEY"] = "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"
os.environ["LANGCHAIN_API_KEY"] = os.getenv('LANGCHAIN_API_KEY')
os.environ["GROQ_API_KEY"] =  os.getenv('GROQ_API_KEY')

# Initialize your model
model = ChatGroq(model="llama3-8b-8192")
parser = StrOutputParser()

# Create the prompt template
system_template = '''I am developing a model to analyze the ingredients of various products and predict their effects on the human body.
The goal is to understand how these ingredients impact health, identify potential risks, and suggest healthier alternatives. 
Given a product's ingredient list as follows: {list_of_ingredients} and the product category: {category}, provide a detailed analysis including the following:

Ingredient Analysis:
- Describe its common uses.
- Outline its positive effects on health.
- Highlight its negative effects and potential risks.

Health Impact Prediction:
- Predict the cumulative health impact based on daily usage of the product.
- Compare ingredient quantities with recommended safety limits.

Healthier Alternatives:
- Suggest safer or healthier alternatives for product .
- Explain why these alternatives are better for health.

Summary:
-provide overall result as it is not good for any specific allergy or good for all types of peoples
-provide name of product if have in database

Make it concise, focusing on the most important details.'''

prompt_template = ChatPromptTemplate.from_messages([("system", system_template)])

 # Ensure the user is logged in
@login_required 
def home(request):
    return render(request,'index.html')



@csrf_exempt  # Temporarily disable CSRF protection for simplicity; enable it in production
def analyze_ingredients(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        category = request.POST.get('category')

        if image and category:
            # Read the uploaded image file
            img = Image.open(image)
            img = np.array(img)
            
            
            reader = easyocr.Reader(['en'])
            results = reader.readtext(img)

            # Generate LLM analysis
            chain = prompt_template | model | parser
            llm_response = chain.invoke({
                "list_of_ingredients": results,
                "category": category
            })

            # print(llm_response)
            def format_html(llm_response):
    
                formatted_response = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', llm_response)
                # Convert *text* to <li>text</li>
                formatted_response = re.sub(r'\*(.*?)\*', r'<li>\1</li>', formatted_response)
                # Replace newlines (\n) with <br> for line breaks
                formatted_response = formatted_response.replace('\n', '<br>')
                return formatted_response

            formatted_response = format_html(llm_response)
            # print(formatted_response)
            # Save the result to the database
            analysis = IngredientAnalysis.objects.create(
                user=request.user,
                category=category,
                result=formatted_response
            )
            
            analysis.save()
            # Return the result as JSON
            return JsonResponse({'result': formatted_response})

        return JsonResponse({'error': 'Invalid input'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def history(request):
    # Retrieve all analyses related to the logged-in user
    user_analyses = IngredientAnalysis.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'history.html', {'user_analyses': user_analyses})

def analysis_detail(request, analysis_id):
    analysis = IngredientAnalysis.objects.get(id=analysis_id, user=request.user)
    return render(request, 'analysis_detail.html', {'analysis': analysis})

def register(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeat_password = request.POST['repeatPassword']

        if password != repeat_password:
            return render(request, 'register.html', {'error_message': "Passwords don't match"})

        if User.objects.filter(username=username).exists():
            return render(request, 'register.html', {'error_message': "Username already taken"})

        user = User.objects.create_user(username=username, email=email, password=password)
        user.save()

        login(request, user)
        return redirect('home')
        # messages.success(request, 'Account created successfully! Please log in.')
        # return redirect('login')

    return render(request, 'register.html')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error_message': 'Invalid credentials'})

    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')