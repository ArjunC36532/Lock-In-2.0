import datetime
from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import openai
import os

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Set up OpenAI API key from environment variable
openai.api_key =openai.api_key = os.getenv('API_KEY')

# Define a database model for storing URLs
class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(500), nullable=False)
    date_added = db.Column(db.DateTime, default=datetime.utcnow)

# Initialize the database
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/quiz-and-learn')
def quiz_and_learn():
    return render_template('quiz-and-learn.html')

@app.route('/learn', methods=['POST'])
def learn_topic():
    topic = request.json.get("topic", "")
    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    chatgpt_response = get_chatgpt_response(topic)
    return jsonify({"response": chatgpt_response})

@app.route('/generate-quiz', methods=['POST'])
def generate_quiz():
    topic = request.json.get("topic", "")
    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    quiz_data = generate_quiz_questions(topic)
    return jsonify({"questions": quiz_data})

def get_chatgpt_response(topic):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Teach me about {topic}."}
        ],
        max_tokens=100,
        temperature=0.7,
    )
    return response.choices[0].message['content'].strip()

def generate_quiz_questions(topic):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are an expert quiz creator."},
            {"role": "user", "content": f"Generate 5 detailed, multiple-choice quiz questions about '{topic}' with correct answers labeled A-D."}
        ],
        max_tokens=500,
        temperature=0.7,
    )

    quiz_text = response.choices[0].message['content'].strip().split("\n\n")
    questions = []

    for quiz in quiz_text:
        lines = quiz.split("\n")
        question = lines[0]
        options = lines[1:5]
        correct_answer = "A"  # Default to "A" if parsing fails; adjust parsing as needed.

        questions.append({
            "question": question,
            "options": options,
            "correct_answer": correct_answer
        })

    return questions

# Route for adding URLs and displaying saved URLs
@app.route('/setup', methods=['POST', 'GET'])
def setup():
    if request.method == 'POST':
        link_url = request.form['link']
        
        # Save the new link in the database
        new_link = Link(url=link_url)
        db.session.add(new_link)
        db.session.commit()

    # Retrieve all saved links from the database
    links = Link.query.all()
    return render_template('setup.html', links=links)

# Route for deleting the last added link
@app.route('/delete_last_link', methods=['POST'])
def delete_last_link():
    last_link = Link.query.order_by(Link.date_added.desc()).first()
    if last_link:
        db.session.delete(last_link)
        db.session.commit()
    # Retrieve updated links list for display
    links = Link.query.all()
    return render_template('setup.html', links=links)

# REST API endpoint to retrieve allowed URLs as JSON
@app.route('/api/allowed_urls', methods=['GET'])
def get_allowed_urls():
    # Query all links from the database
    links = Link.query.all()
    urls = [link.url for link in links]
    return jsonify({"allowed_urls": urls})

@app.route('/start', methods=['POST'])
def start():
    # Placeholder for future functionality
    links = Link.query.all()  # Get current links from database
    return render_template('start.html', links=links)

@app.route('/timer')
def lock_in_timer():
    return render_template('timer_scrn.html')

if __name__ == "__main__":
    app.run(debug=True)
