from flask import Flask, render_template, request, redirect, url_for, g
from datetime import datetime
import json
import os
from collections import defaultdict

app = Flask(__name__)

# File paths for storing data
DATA_FILE = "mood_data.json"
RULES_FILE = "mood_rules.json"

# Initialize default rules
DEFAULT_RULES = {
    "Sunny": {
        "below": {"temp": 65, "mood": "cheerful"},
        "above": {"temp": 65, "mood": "happy"}
    },
    "Rainy": {
        "below": {"temp": 50, "mood": "gloomy"},
        "above": {"temp": 50, "mood": "calm"}
    },
    "Overcast": {
        "below": {"temp": 55, "mood": "melancholy"},
        "above": {"temp": 55, "mood": "lively"}
    }
}

# Load data from file
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as file:
            return json.load(file)
    else:
        return {"entries": [], "history": []}

# Save data to file
def save_data(data):
    with open(DATA_FILE, 'w') as file:
        json.dump(data, file, indent=4)

# Load rules from file
def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, 'r') as file:
            return json.load(file)
    else:
        return DEFAULT_RULES

# Save rules to file
def save_rules(rules):
    with open(RULES_FILE, 'w') as file:
        json.dump(rules, file, indent=4)

# Add a new data point and analyze immediately if threshold met
def add_data_point(weather, temperature, mood):
    data = load_data()
    data["entries"].append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "weather": weather,
        "temperature": temperature,
        "mood": mood
    })
    save_data(data)

    # Check if we have reached the threshold for automatic analysis
    # Count entries with this weather and temperature range
    threshold = 3
    count = 0

    # Get current rules to check temperature threshold
    rules = load_rules()

    # Determine if this is above or below threshold temperature
    is_above_threshold = True
    if weather in rules:
        temp_threshold = rules[weather]['below']['temp']
        is_above_threshold = temperature >= temp_threshold

    # Count matching entries
    for entry in data["entries"]:
        if entry["weather"] == weather:
            entry_above_threshold = True
            if weather in rules:
                entry_above_threshold = entry["temperature"] >= temp_threshold

            # If this entry is in the same temperature range (above or below threshold)
            if entry_above_threshold == is_above_threshold:
                count += 1

    # If we have 3 or more entries for this condition, analyze automatically
    if count >= threshold:
        print(f"Automatic analysis triggered: {count} entries for {weather} {'above' if is_above_threshold else 'below'} {temp_threshold}°F")
        analyze_and_update_rules()

# Find most common mood for a temperature range
def most_common_mood(entries, is_below, threshold):
    mood_counts = defaultdict(int)

    for entry in entries:
        temp = entry['temperature']
        if (is_below and temp < threshold) or (not is_below and temp >= threshold):
            mood_counts[entry['mood']] += 1

    if not mood_counts:
        return None, 0

    # Find the mood with the highest count
    most_common = max(mood_counts.items(), key=lambda x: x[1])
    return most_common[0], most_common[1]  # Return the mood and its count

# Analyze collected data and update rules
def analyze_and_update_rules():
    data = load_data()
    current_rules = load_rules()

    # Create deep copies for comparison
    original_rules = json.loads(json.dumps(current_rules))
    updated_rules = json.loads(json.dumps(current_rules))

    # Only need 3 entries total to start analysis
    if len(data['entries']) < 3:
        return current_rules

    # Track if we made any changes
    rules_changed = False

    # Group data by weather condition
    weather_data = defaultdict(list)
    for entry in data['entries']:
        weather_data[entry['weather']].append(entry)

    # Analyze each weather condition
    for weather, entries in weather_data.items():
        # Need at least 2 entries for a weather type
        if len(entries) < 2:
            continue

        # If weather not in rules, add it
        if weather not in updated_rules:
            updated_rules[weather] = {
                'below': {'temp': 50, 'mood': 'neutral'},
                'above': {'temp': 50, 'mood': 'neutral'}
            }
            rules_changed = True

        # Get the current threshold
        threshold = updated_rules[weather]['below']['temp']

        # Find most common moods for below and above threshold
        below_mood, below_count = most_common_mood(entries, True, threshold)
        above_mood, above_count = most_common_mood(entries, False, threshold)

        # Only update below threshold mood if we have at least 3 instances of this mood
        if below_mood and below_count >= 3 and below_mood != updated_rules[weather]['below']['mood']:
            updated_rules[weather]['below']['mood'] = below_mood
            rules_changed = True

        # Only update above threshold mood if we have at least 3 instances of this mood
        if above_mood and above_count >= 3 and above_mood != updated_rules[weather]['above']['mood']:
            updated_rules[weather]['above']['mood'] = above_mood
            rules_changed = True

        # Check if we should adjust the threshold
        # But only if we have at least 4 entries for this weather
        if len(entries) >= 4:
            # Sort entries by temperature
            sorted_entries = sorted(entries, key=lambda x: x['temperature'])

            # Find temperature where mood tends to change
            mood_changes = []
            prev_mood = None

            for entry in sorted_entries:
                if prev_mood is not None and entry['mood'] != prev_mood:
                    mood_changes.append(entry['temperature'])
                prev_mood = entry['mood']

            # If we found mood changes, use the average as new threshold
            if mood_changes:
                new_threshold = int(sum(mood_changes) / len(mood_changes))

                # Only update if significantly different (at least 2 degrees)
                if abs(new_threshold - threshold) >= 2:
                    updated_rules[weather]['below']['temp'] = new_threshold
                    updated_rules[weather]['above']['temp'] = new_threshold
                    rules_changed = True

    # If rules changed, save to history and update rules file
    if rules_changed:
        # Record the changes in history
        if 'history' not in data:
            data['history'] = []

        data['history'].append({
            'timestamp': datetime.now().strftime("%Y-%m-%d"),
            'rules': updated_rules
        })
        save_data(data)

        # Save the updated rules
        save_rules(updated_rules)

        return updated_rules

    return current_rules

# Predict mood based on weather and temperature
def predict_mood(weather, temperature):
    rules = load_rules()

    if weather not in rules:
        return 'neutral'  # Default if weather not in rules

    weather_rule = rules[weather]
    if temperature < weather_rule['below']['temp']:
        return weather_rule['below']['mood']
    else:
        return weather_rule['above']['mood']

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/result', methods=['POST'])
def result():
    if request.method == 'POST':
        weather = request.form['weather']
        temperature = int(request.form['temperature'])

        # Predict mood
        mood = predict_mood(weather, temperature)

        return render_template('result.html',
                              condition=weather,
                              temperature=temperature,
                              mood=mood)

@app.route('/feedback', methods=['POST'])
def feedback():
    if request.method == 'POST':
        weather = request.form['weather']
        temperature = int(request.form['temperature'])
        actual_mood = request.form['actual_mood']

        # Add data point and analyze immediately
        add_data_point(weather, temperature, actual_mood)

        return render_template('feedback.html',
                              mood=actual_mood,
                              condition=weather,
                              temperature=temperature)

@app.route('/data')
def data_view():
    data = load_data()
    return render_template('data.html', entries=data['entries'])

@app.route('/rules')
def rules_view():
    rules = load_rules()
    data = load_data()

    # Count data points per weather type
    weather_counts = defaultdict(int)
    for entry in data['entries']:
        weather_counts[entry['weather']] += 1

    return render_template('rules.html',
                          rules=rules,
                          total_entries=len(data['entries']),
                          weather_counts=weather_counts)

@app.route('/history')
def history_view():
    data = load_data()
    if 'history' not in data:
        data['history'] = []

    return render_template('history.html', history=data['history'])

@app.route('/analyze')
def analyze():
    analyze_and_update_rules()
    return redirect(url_for('rules_view'))

@app.route('/reset')
def reset_data():
    """Reset all data and rules to defaults (for testing)"""
    if os.path.exists(DATA_FILE):
        os.remove(DATA_FILE)
    if os.path.exists(RULES_FILE):
        os.remove(RULES_FILE)
    return redirect(url_for('home'))

@app.context_processor
def inject_request():
    """Make request object available to all templates"""
    return dict(request=request)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)