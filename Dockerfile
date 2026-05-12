# Use an official Python runtime as the base image
FROM python:slim

# Set environment variables (modify as needed)
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory within the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install app dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

EXPOSE 8000

# Start Gunicorn with 3 workers
CMD ["gunicorn", "Rems.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]