# Use the official Python 3.12 slim image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Copy the dependency configuration files
COPY pyproject.toml ./

# Install gunicorn and other dependencies from pyproject.toml
# Using `pip install .` reads the pyproject.toml and installs the project
# along with its dependencies.
RUN pip install .

# Copy the rest of the application source code
COPY . .

# Expose the port the app runs on
EXPOSE 5000

# Run the application using Gunicorn
# This is a production-ready WSGI server
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]