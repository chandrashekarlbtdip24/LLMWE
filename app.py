from flask import Flask, request, jsonify, send_from_directory
import requests
import re

app = Flask(__name__, static_folder='static')


def get_current_weather(location: str) -> dict:
    """Tool: Fetch current weather for a location using wttr.in (j1 JSON).

    Returns a structured dict with a few key fields.
    """
    url = f"https://wttr.in/{location}?format=j1"
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        return {"error": f"failed to fetch weather: {e}"}

    # wttr.in j1 format contains 'current_condition'
    try:
        cur = data.get('current_condition', [])[0]
        weather = {
            'location': location,
            'temp_C': cur.get('temp_C'),
            'feels_like_C': cur.get('FeelsLikeC'),
            'humidity': cur.get('humidity'),
            'wind_kmph': cur.get('windspeedKmph'),
            'weather_desc': cur.get('weatherDesc', [{}])[0].get('value'),
            'raw': data,
        }
    except Exception:
        return {"error": "unexpected response format from wttr.in", "raw": data}

    return weather


def extract_location_from_question(question: str) -> str:
    # very simple heuristic: look for "in <Place>" or the last token
    m = re.search(r"in\s+([A-Za-z\s,-]+)\?*$", question, re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # fallback: take last word without punctuation
    tokens = re.findall(r"[A-Za-z\-]+", question)
    return tokens[-1] if tokens else ''


@app.route('/')
def index():
    return send_from_directory('static', 'index.html')


@app.route('/api/ask', methods=['POST'])
def api_ask():
    payload = request.get_json() or {}
    question = payload.get('question', '')

    # Simulate LLM chain-of-thought: decide to call the tool
    location = extract_location_from_question(question)
    thought = f"I should call the tool get_current_weather('{location}') to fetch current conditions."

    tool_output = get_current_weather(location)

    if 'error' in tool_output:
        final = f"I couldn't fetch the weather: {tool_output.get('error')}"
    else:
        final = (
            f"Current weather in {tool_output['location']}: {tool_output['weather_desc']}, "
            f"temp {tool_output['temp_C']}°C (feels like {tool_output['feels_like_C']}°C), "
            f"humidity {tool_output['humidity']}%, wind {tool_output['wind_kmph']} km/h."
        )

    return jsonify({'thought': thought, 'tool_output': tool_output, 'final_answer': final})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
