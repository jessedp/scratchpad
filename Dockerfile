FROM python:3.12-slim

WORKDIR /app

# Install dependencies
# Using pip directly for simplicity given the small dependency list
RUN pip install flask faker

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "app.py"]
