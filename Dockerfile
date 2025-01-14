# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /code

# Copy the current directory contents into the container at /app
# COPY . /app
COPY ./requirements.txt /code/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY ./app /code/app
COPY ./static /code/static
COPY ./templates /code/templates
# Make port 8000 available to the world outside this container

EXPOSE 8080

# Define environment variable
ENV NAME=GenerateAudio
ENV COQUI_TOS_AGREED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]