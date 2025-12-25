# Weather Dashboard

A beautiful, responsive Django-based weather dashboard that automatically detects your location and displays real-time weather information with dynamic backgrounds and animated icons.

![Weather Dashboard](https://img.shields.io/badge/Django-6.0-green.svg)
![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## Features

- **Automatic Location Detection**: Uses your public IP address to determine your location
- **Real-time Weather Data**: Fetches current weather conditions from OpenWeatherMap API
- **Dynamic UI**: Weather-themed backgrounds that change based on current conditions
- **Animated Icons**: Beautiful emoji icons with floating animations
- **Comprehensive Weather Info**:
  - Current temperature and "feels like" temperature
  - Weather description
  - Humidity levels
  - Wind speed
  - Atmospheric pressure
  - Visibility
  - Cloudiness
  - Min/Max temperatures
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile devices
- **Error Handling**: Robust error handling with user-friendly messages and logging

## Technologies Used

- **Backend**: Django 6.0
- **APIs**:
  - IPinfo.io (for geolocation)
  - OpenWeatherMap (for weather data)
  - ipify (for public IP detection)
- **Frontend**: HTML5, CSS3 (with gradients and animations)
- **Python Libraries**: requests, logging

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.8 or higher
- pip (Python package manager)
- Git (optional, for cloning)

## Installation

### 1. Clone or Download the Repository

```bash
git clone <repository-url>
cd Weather
```

Or download and extract the ZIP file.

### 2. Create a Virtual Environment (Recommended)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install django requests
```

### 4. Configure API Keys

The application requires an OpenWeatherMap API key. Get your free API key:

1. Visit [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for a free account
3. Generate an API key

Open `Weather/settings.py` and update the API key on line 130:

```python
OPENWEATHER_API_KEY = "your_api_key_here"
```

**Note**: The IPinfo API doesn't require a token for the free tier (up to 50,000 requests/month).

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Start the Development Server

```bash
python manage.py runserver
```

The application will be available at: **http://127.0.0.1:8000/**

## Usage

1. Open your web browser and navigate to `http://127.0.0.1:8000/`
2. The application will automatically:
   - Detect your public IP address
   - Fetch your location (city, region, country)
   - Display current weather conditions for your location
3. The background and icon will automatically match the current weather condition

## Weather Conditions & Themes

The dashboard dynamically changes its appearance based on weather:

- **☀️ Clear Sky**: Bright sunny gradient
- **☁️ Cloudy**: Gray cloudy gradient
- **🌧️ Rain**: Blue rainy gradient
- **🌦️ Drizzle**: Light rain gradient
- **⛈️ Thunderstorm**: Dark dramatic gradient
- **❄️ Snow**: Winter white gradient
- **🌫️ Fog/Mist**: Foggy gray gradient

## Project Structure

```
Weather/
├── dashboard/              # Main application
│   ├── templates/
│   │   └── dashboard/
│   │       └── weather.html    # Weather dashboard template
│   ├── views.py           # View logic for weather
│   ├── urls.py            # URL routing
│   └── ...
├── Weather/               # Project settings
│   ├── settings.py        # Django settings & API keys
│   ├── urls.py            # Main URL configuration
│   └── ...
├── manage.py              # Django management script
└── README.md              # This file
```

## API Endpoints

### Main Weather Dashboard
- **URL**: `/`
- **Method**: GET
- **Description**: Displays weather dashboard for user's location