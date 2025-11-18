# O'Brien's Storage Finder

A professional web application for finding available storage units with real-time pricing and availability.

## Features

- **Live Pricing & Availability**: All pricing and availability fetched in real-time from the API
- **Size Calculator**: Tell us what you're storing and we'll recommend the perfect size
- **Multiple Locations**: Wallsend, Boldon, Birtley, Sunderland, Chester-le-Street
- **UK-Friendly**: Proper validation for UK phone numbers and email addresses
- **Professional UI**: Clean, modern, and user-friendly interface

## Static Prices (Only These Are Hardcoded)

- **Container Storage**:
  - Deposit: £120
  - Lock: £25

- **Internal Storage**:
  - Deposit: £50
  - Padlock: £9.99

All other pricing is fetched live from the API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API token:
```
STORMAN_API_TOKEN=your_token_here
SECRET_KEY=your_secret_key_here
```

3. Run the application:
```bash
python app.py
```

## Deployment to Render

1. Push your code to a Git repository
2. Connect your repository to Render
3. Set environment variables in Render:
   - `STORMAN_API_TOKEN`: Your API token
   - `SECRET_KEY`: A secure secret key for sessions
4. Render will automatically detect `render.yaml` and deploy

## Project Structure

```
.
├── app.py                 # Flask application
├── Storage Finder.py      # Core business logic
├── requirements.txt       # Python dependencies
├── render.yaml           # Render deployment config
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── start.html
│   ├── find_storage.html
│   ├── items_input.html
│   ├── choose_size.html
│   ├── select_site.html
│   ├── select_storage_type.html
│   ├── select_known_size.html
│   ├── vehicle_warning.html
│   ├── results.html
│   ├── no_availability.html
│   └── no_suitable_size.html
└── static/               # Static files
    ├── style.css
    └── logo.jpg
```

## Copyright

Copyright (c) 2025 John Hibberd
All rights reserved.

