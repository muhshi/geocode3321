FROM python:3.10-slim

# 1. Install Dependencies System (Chrome & Utilities)
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gnupg \
    unzip \
    fonts-liberation \
    libnss3 \
    libgconf-2-4 \
    libappindicator3-1 \
    libasound2 \
    xdg-utils \
    --no-install-recommends

# 2. Install Google Chrome Stable
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# 3. Setup Workspace
WORKDIR /app

# 4. Install Python Dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy Application Code
COPY . .

# 6. Command to Run
# --host 0.0.0.0 wajib agar bisa diakses dari luar container
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8800"]
