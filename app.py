from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from config import Config
from utils.db_utils import init_db, insert_feedback, get_all_feedbacks
from collections import Counter
from textblob import TextBlob
from datetime import datetime
import sqlite3

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
init_db()

# Sentiment analysis logic
def analyze_sentiment(message):
    blob = TextBlob(message)
    polarity = blob.sentiment.polarity
    if polarity > 0.1:
        return "Positive"
    elif polarity < -0.1:
        return "Negative"
    else:
        return "Neutral"

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        message = request.form.get("message")

        if not message:
            flash("Feedback message is required.", "warning")
            return redirect(url_for("index"))

        sentiment = analyze_sentiment(message)
        insert_feedback(name, email, message, sentiment)
        flash("Feedback submitted successfully!", "success")
        return redirect(url_for("thankyou"))

    return render_template("index.html")

@app.route("/thankyou")
def thankyou():
    return render_template("thankyou.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == Config.ADMIN_USERNAME and password == Config.ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            flash("Invalid credentials.", "danger")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/admin")
def admin_dashboard():
    if not session.get("admin"):
        return redirect(url_for("login"))
    
    feedbacks = get_all_feedbacks()
    return render_template("admin.html", feedbacks=feedbacks)

@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect(url_for("login"))

# For chart data
@app.route("/feedback-data")
def feedback_data():
    feedbacks = get_all_feedbacks()
    date_counts = Counter()

    for fb in feedbacks:
        try:
            timestamp = fb[4]  # fb[4] is timestamp
            date = timestamp[:10]  # 'YYYY-MM-DD'
            date_counts[date] += 1
        except:
            continue

    sorted_dates = sorted(date_counts.items())
    labels = [item[0] for item in sorted_dates]
    counts = [item[1] for item in sorted_dates]

    return jsonify({"labels": labels, "counts": counts})

if __name__ == "__main__":
    app.run(debug=True)
