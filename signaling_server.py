from flask import Flask
from flask_socketio import SocketIO, emit, join_room, rooms, leave_room

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Store room participants
room_participants = {}

SIGNALING_SERVER = "https://192.168.1.134:5001"

@app.route("/")
def index():
    return "Signaling server running."

@socketio.on('connect')
def handle_connect(sid, environ):
    print(f"User connected: {sid}")

@socketio.on('disconnect')
def handle_disconnect(sid):
    print(f"User disconnected: {sid}")
    # Remove from all rooms
    for room in list(room_participants.keys()):
        if sid in room_participants[room]:
            room_participants[room].remove(sid)
            if len(room_participants[room]) == 0:
                del room_participants[room]
            else:
                # Notify others in the room
                emit('user-left', {'user': sid}, room=room)

@socketio.on('join-room')
def handle_join(data):
    room = data['room']
    user_id = request.sid
    
    print(f"User {user_id} joining room: {room}")
    
    # Initialize room if it doesn't exist
    if room not in room_participants:
        room_participants[room] = []
    
    # Add user to room
    if user_id not in room_participants[room]:
        room_participants[room].append(user_id)
    
    join_room(room)
    
    # If there are already users in the room, notify them
    if len(room_participants[room]) > 1:
        emit('user-joined', {'user': user_id}, room=room, include_self=False)
        emit('room-ready', {'participants': len(room_participants[room])}, room=room)
    
    print(f"Room {room} now has {len(room_participants[room])} participants")

@socketio.on('offer')
def handle_offer(data):
    room = data['room']
    print(f"Offer received for room: {room}")
    emit('offer', data, room=room, include_self=False)

@socketio.on('answer')
def handle_answer(data):
    room = data['room']
    print(f"Answer received for room: {room}")
    emit('answer', data, room=room, include_self=False)

@socketio.on('ice-candidate')
def handle_ice(data):
    room = data['room']
    print(f"ICE candidate received for room: {room}")
    emit('ice-candidate', data, room=room, include_self=False)

@socketio.on('leave-room')
def handle_leave(data):
    room = data['room']
    user_id = request.sid
    
    if room in room_participants and user_id in room_participants[room]:
        room_participants[room].remove(user_id)
        if len(room_participants[room]) == 0:
            del room_participants[room]
        else:
            emit('user-left', {'user': user_id}, room=room)
    
    leave_room(room)
    print(f"User {user_id} left room: {room}")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5001, debug=True, ssl_context=("cert.pem", "key.pem"))