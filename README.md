# Mood Predictor

A Flask web application that predicts your mood based on weather conditions and temperature. The application learns from user feedback to improve its predictions over time.

## Features

- Predicts mood based on weather conditions and temperature
- Learns from user feedback
- Maintains history of predictions and rule changes
- Visualizes data and prediction rules
- Automatically updates prediction rules based on user feedback

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd mood-predictor
```

2. Create and activate virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
python main.py
```

The application will be available at `http://localhost:5001`

## Data Storage

The application stores data in two JSON files:
- `mood_data.json`: Stores user entries and feedback
- `mood_rules.json`: Stores the current prediction rules

## Contributing

Feel free to open issues or submit pull requests to improve the application. 