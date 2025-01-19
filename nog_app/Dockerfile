# Specify Python runtime
FROM python:3.13

# Create a working directory
RUN mkdir /app

# Set the working directory
WORKDIR /app

# Prevent Python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE=1
# Prevent Python from buffering stdout and stderr
ENV PYTHONUNBUFFERED=1

# upgrade pip
RUN pip install --upgrade pip

# Copy the requirements file
COPY ./requirements.txt /app/requirements.txt

# Install the requirements
RUN pip install --no-cache-dir -r requirements.txt

# Copy the project files
COPY . /app/

# Expose the port the app runs on
EXPOSE 8000

# Run the app
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]