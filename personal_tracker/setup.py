"""
Setup script for the Personal Tracker App
"""
from setuptools import setup, find_packages

setup(
    name="personal-tracker",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "Flask>=2.2.3",
        "Flask-WTF>=1.1.1",
        "Werkzeug>=2.2.3",
        "requests>=2.28.2",
        "oauthlib>=3.2.2",
        "requests-oauthlib>=1.3.1",
        "google-auth>=2.16.2",
        "google-auth-oauthlib>=1.0.0",
        "google-api-python-client>=2.80.0",
        "cryptography>=39.0.2",
        "PyJWT>=2.6.0",
        "python-dotenv>=1.0.0",
        "python-dateutil>=2.8.2",
        "APScheduler>=3.10.1",
    ],
    python_requires=">=3.9",
)
