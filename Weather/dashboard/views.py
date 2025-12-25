from django.shortcuts import render
from django.conf import settings
import requests
import logging

logger = logging.getLogger(__name__)


def get_public_ip():
    try:
        response = requests.get('https://api.ipify.org?format=json', timeout=5)
        response.raise_for_status()
        return response.json().get('ip')
    except:
        return None


def get_location_from_ip(ip_address):
    ipinfo_url = f'https://ipinfo.io/{ip_address}/json'

    try:
        logger.info(f"Fetching location data for IP: {ip_address}")
        response = requests.get(ipinfo_url, timeout=5)
        response.raise_for_status()
        location_data = response.json()

        if location_data.get('bogon'):
            logger.warning(f"Bogon IP detected (private/localhost): {ip_address}")
            return {'error': 'Cannot get location for localhost or private IP addresses. Please access from a public IP.'}

        if not location_data.get('loc'):
            logger.warning(f"No location coordinates in IPinfo response for IP: {ip_address}")
            return {'error': 'IPinfo did not return location coordinates for this IP address.'}

        logger.info(f"Successfully fetched location data for IP: {ip_address}")
        return location_data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching location data for IP: {ip_address}")
        return {'error': 'Request to IPinfo timed out. Please try again.'}

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error while fetching location data: {e}")
        return {'error': f'IPinfo API error: {e.response.status_code}'}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception while fetching location data: {e}")
        return {'error': 'Could not connect to IPinfo service.'}

    except Exception as e:
        logger.exception(f"Unexpected error while fetching location data: {e}")
        return {'error': 'An unexpected error occurred while fetching location data.'}


def get_weather_data(latitude, longitude):
    api_key = getattr(settings, 'OPENWEATHER_API_KEY', '')

    if not api_key:
        logger.error("OpenWeatherMap API key is not configured")
        return {'error': 'OpenWeatherMap API key not configured.'}

    weather_url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {
        'lat': latitude,
        'lon': longitude,
        'units': 'metric',
        'appid': api_key
    }

    try:
        logger.info(f"Fetching weather data for coordinates: ({latitude}, {longitude})")
        response = requests.get(weather_url, params=params, timeout=5)
        response.raise_for_status()
        weather_data = response.json()
        logger.info(f"Successfully fetched weather data for coordinates: ({latitude}, {longitude})")
        return weather_data

    except requests.exceptions.Timeout:
        logger.error(f"Timeout while fetching weather data for coordinates: ({latitude}, {longitude})")
        return {'error': 'Request to OpenWeatherMap timed out. Please try again.'}

    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error while fetching weather data: {e}")
        if e.response.status_code == 401:
            return {'error': 'Invalid OpenWeatherMap API key.'}
        return {'error': f'OpenWeatherMap API error: {e.response.status_code}'}

    except requests.exceptions.RequestException as e:
        logger.error(f"Request exception while fetching weather data: {e}")
        return {'error': 'Could not connect to OpenWeatherMap service.'}

    except Exception as e:
        logger.exception(f"Unexpected error while fetching weather data: {e}")
        return {'error': 'An unexpected error occurred while fetching weather data.'}


def weather(request):
    ip = get_public_ip()
    
    if not ip:
        context = {
            'ip': None,
            'location_info': None,
            'weather_data': None,
            'error_message': 'Could not determine your public IP address. Please try again.',
        }
        return render(request, 'dashboard/weather.html', context)
    
    logger.info(f"Processing weather request for IP: {ip}")

    ip_data = get_location_from_ip(ip)

    weather_data = None
    error_message = None
    location_info = None

    if 'error' not in ip_data:
        location_info = {
            'city': ip_data.get('city', 'Unknown'),
            'region': ip_data.get('region', 'Unknown'),
            'country': ip_data.get('country', 'Unknown'),
        }

        location_coords = ip_data.get('loc')

        try:
            latitude, longitude = location_coords.split(',')
            weather_data = get_weather_data(latitude, longitude)

            if 'error' in weather_data:
                error_message = weather_data['error']
                weather_data = None

        except ValueError:
            logger.error(f"Invalid location coordinates format: {location_coords}")
            error_message = 'Invalid location coordinates received from IPinfo.'
    else:
        error_message = ip_data['error']
        logger.warning(f"Failed to get location data for IP: {ip}")

    context = {
        'ip': ip,
        'location_info': location_info,
        'weather_data': weather_data,
        'error_message': error_message,
    }

    return render(request, 'dashboard/weather.html', context)