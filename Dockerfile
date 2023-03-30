# Use the official Python image as the base image
FROM python:3.9-slim-buster

RUN apt-get update && apt-get install -y default-jre
ENV PATH $PATH:/usr/lib/jvm/java-11-openjdk-amd64/bin


# Set the working directory to /app
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any necessary dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code into the container
COPY . .

# Set the environment variable for Flask
ENV FLASK_APP=app.py

# Expose port 5000
EXPOSE 5000

# Run the Flask app when the container starts
CMD ["flask", "run", "--host=0.0.0.0"]
