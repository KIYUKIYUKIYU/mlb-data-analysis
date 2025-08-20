from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "Flask server is running!"

@app.route('/api/test')
def test_api():
    return jsonify({
        'status': 'ok',
        'message': 'API is working',
        'timestamp': '2025-06-24 01:55:00'
    })

if __name__ == '__main__':
    print("Starting test server...")
    print("Try accessing: http://localhost:5000/")
    print("Or: http://127.0.0.1:5000/api/test")
    app.run(host='127.0.0.1', port=5000, debug=False)