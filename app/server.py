from flask import Flask, send_from_directory
import os

app = Flask(__name__)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('.', path)

@app.route('/test')
def serve_test():
    return send_from_directory('.', 'test.html')

if __name__ == '__main__':
    print("🚀 Starting server at http://localhost:5000")
    print("📁 Serving files from:", os.path.abspath('.'))
    app.run(debug=True, host='localhost', port=5000)