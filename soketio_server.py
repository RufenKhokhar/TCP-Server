import eventlet
eventlet.monkey_patch()  # ✅ MUST BE FIRST

from flask import Flask
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, cors_allowed_origins='*')

@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')

@socketio.on('log')
def handle_disconnect(data):
    print(f"logging -> {data}")

@socketio.on('send_message')
def handle_send_message(data):
    print(f"Received message: {data}")
    emit('receive_message', data, broadcast=True, include_self=False)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=3000)
