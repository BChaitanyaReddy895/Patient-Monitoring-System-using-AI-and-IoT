# 🏥 AI-IoT Smart Patient Monitoring & Alert System
A smart and scalable IoT-based health monitoring system designed using the ESP32 DevKit, capable of tracking patient vitals in real time. The system monitors heart rate, body temperature, and humidity using sensors like Pulse Sensor and DHT11, and transmits the data via Wi-Fi to ThingSpeak for cloud visualization.

# What makes this system stand out is its built-in intelligence and alerting mechanism:
a Python-based machine learning model classifies the health data as normal or abnormal.
# When an anomaly (such as fever or tachycardia) is detected, the system triggers:
    Continuous email alerts to caregivers via the Gmail API.
    Local voice alerts using a speaker module
    Visual and audio alerts using LED and buzzer
    This ensures timely intervention and is ideal for home care, elderly monitoring, and remote health support.
    
# 🔧 Features
Real-time monitoring of heart rate, temperature, and humidity
ESP32 with Wi-Fi connectivity for cloud integration
ThingSpeak dashboard for live data visualization
Machine learning model for anomaly detection
Continuous email notifications for critical conditions
Voice alerts via speaker module for on-site warnings
Buzzer for immediate local signaling
Low-cost, customizable, and easy to deploy

# 🛠️ Technologies Used
ESP32 DevKit, DHT11, Pulse Sensor
Arduino IDE, ThingSpeak API
Python, Scikit-learn
Gmail API for email alerts
Speaker module for voice feedback


