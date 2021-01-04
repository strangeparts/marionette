# Marionette
Twitch extension for controlling robots remotely


# Installation

    cd server
    virtualenv virtualenv
    pip3 install -r requirements.txt

# Run development server

    gunicorn -k flask_sockets.worker --threads 5 --workers 5 -b '0.0.0.0:8000' app:app
