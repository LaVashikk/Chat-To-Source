from flask import Flask, render_template, Response

app = Flask(__name__)

@app.route('/events')
def chat_events(messages_generator):
    return Response(messages_generator(), content_type='text/event-stream')

@app.route('/')
def index():
    return render_template('index.html')

def run_server(chat_messages_generator):
    app.view_functions['chat_events'] = lambda: chat_events(chat_messages_generator)
    app.run(debug=True)