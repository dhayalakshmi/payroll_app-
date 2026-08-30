"""
Payroll System — Module 1 (Registration & Authentication)
Flask implementation.

Same page, same look, same behavior as the original http.server version —
now served by Flask instead. All the login/register logic still runs
entirely in the browser (JavaScript), with an in-memory accounts array
that resets on every page reload. Flask's only job here is to serve the
HTML page.

HOW TO RUN
----------
    pip install -r requirements.txt
    python app.py

Then open this URL in your browser:
    http://127.0.0.1:8000
"""

from flask import Flask, render_template

app = Flask(__name__)

HOST = "127.0.0.1"
PORT = 8000


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    print(f"Payroll System (Module 1) running at http://{HOST}:{PORT}")
    print("Press CTRL+C in this terminal to stop the server.")
    app.run(host=HOST, port=PORT, debug=False)
