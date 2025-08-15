from flask import Flask
from flask_socketio import SocketIO, emit, join_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

@app.route("/")
def index():
    return "Signaling server running."

@socketio.on('join')
def handle_join(data):
    print(f"User joined room: {data['room']}")
    room = data['room']
    join_room(room)
    emit('ready', room=room)

@socketio.on('offer')
def handle_offer(data):
    print(f"Offer received for room: {data['room']}")
    emit('offer', data, room=data['room'])

@socketio.on('answer')
def handle_answer(data):
    print(f"Answer received for room: {data['room']}")
    emit('answer', data, room=data['room'])

@socketio.on('ice-candidate')
def handle_ice(data):
    print(f"ICE candidate received for room: {data['room']}")
    emit('ice-candidate', data, room=data['room'])

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001)