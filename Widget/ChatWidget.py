import threading

import logging
from flask import Flask, render_template
from flask_socketio import SocketIO

logging.getLogger('werkzeug').disabled = True

class ChatWidget:
    def __init__(self, host, port):
        self.app = Flask(__name__)
        self.app.route("/")(self.index)

        self.messages = []
        self.clients = set()

        self.host = host
        self.port = port

        self.socketio = SocketIO(self.app)

        self.thread = threading.Thread(target=self.run)
        self.thread.daemon = True
        self.thread.start()


    def index(self):
        return render_template("index.html")

    def run(self):
        self.socketio.run(self.app, host=self.host, port=self.port)


    def send_message(self, avatar_url, username, message):
        self.messages.append((avatar_url, username, message))
        self.socketio.emit('new_message', {
            'avatar_url': avatar_url, 
            'username': username,
            'message': message 
        })