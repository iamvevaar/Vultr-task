# Start from a small, official Python image. We pin 3.12 (stable, all our
# libraries have prebuilt wheels for it) instead of your local 3.14 so the
# container behaves identically on your Mac, in CI, and on the Vultr box.
FROM python:3.12-slim

# Don't write .pyc files, and don't buffer stdout/stderr (so logs show up live).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Everything below runs inside /app in the container.
WORKDIR /app

# Copy ONLY requirements first, then install. Docker caches this layer, so
# rebuilds are fast unless requirements.txt actually changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Now copy the application code.
COPY . .

# Default command: run the API with auto-reload for local development.
# (In production/Vultr we'll override this to drop --reload.)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
