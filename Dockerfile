# Microsoft ka bana banaya image use karenge (Isme browser pehle se hai)
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

# Folder set karna
WORKDIR /app

# Saari files copy karna
COPY . .

# Python libraries install karna
RUN pip install flask requests playwright gunicorn

# Browser install (Root access yahan mil jayega kyunki ye humara box hai)
RUN playwright install chromium

# Port kholna (Render ke liye)
EXPOSE 5000

# Script start karna
CMD ["python", "main.py"]
