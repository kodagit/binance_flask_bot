from flask import Flask, render_template, jsonify

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('base.html')

@app.route('/settings')
def settings():
    return render_template('base.html')

@app.route('/backtest')
def backtest():
    return render_template('base.html')

@app.route('/advanced')
def advanced():
    return render_template('base.html')

@app.route('/api/test')
def test():
    return jsonify({"status": "success"})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
