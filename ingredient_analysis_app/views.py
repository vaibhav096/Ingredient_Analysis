from django.shortcuts import render
from django.http import HttpResponse

# ingredient_analysis_app/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import pytesseract
import cv2
import numpy as np
import io

# Specify the full path to the Tesseract executable
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def home(request):
    return render(request, 'index.html')

@csrf_exempt  # Temporarily disabling CSRF for simplicity; enable it in production
def analyze_ingredients(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        category = request.POST.get('category')

        if image and category:
            # Read the uploaded image file
            img = Image.open(image)
            img = np.array(img)

            # Convert the image to grayscale and preprocess it for OCR
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
            sharpened = cv2.filter2D(blurred, -1, kernel)
            binary = cv2.adaptiveThreshold(sharpened, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

            # Use Tesseract to extract text from the image
            custom_config = r'--oem 3 --psm 6'
            extracted_text = pytesseract.image_to_string(binary, config=custom_config)

            # Mock analysis result
            # This would be replaced by the actual LLM analysis in the future
            analysis_result = f"Category: {category}\nExtracted Ingredients: {extracted_text}\n\nAnalysis: This is a mock analysis result."

            # Return the result as JSON
            return JsonResponse({'result': analysis_result})

        return JsonResponse({'error': 'Invalid input'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)
