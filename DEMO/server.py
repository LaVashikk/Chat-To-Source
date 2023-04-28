from flask import Flask, render_template, Response

app = Flask(__name__)

@app.route('/events')
def chat_events(messages_generator):
    return Response(messages_generator(), content_type='text/event-stream')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/bar')
def bar():
    return render_template('commandBar.html')

@app.route('/chat')
def chat():
    return render_template('commandChat.html')

def run_server(chat_messages_generator):
    app.view_functions['chat_events'] = lambda: chat_events(chat_messages_generator)
    app.run(debug=True)