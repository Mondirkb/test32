from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room, rooms, leave_room

app = Flask(__name__)
socketio = SocketIO(app, 
                   cors_allowed_origins="*",
                   logger=True, 
                   engineio_logger=True,
                   async_mode='threading')

# Store room participants
room_participants = {}

@app.route("/")
def index():
    return "Signaling server running on HTTPS."

@socketio.on('connect')
def handle_connect():
    print(f"User connected: {request.sid}")
    emit('connection-confirmed', {'status': 'connected', 'id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    print(f"User disconnected: {request.sid}")
    # Remove from all rooms
    for room in list(room_participants.keys()):
        if request.sid in room_participants[room]:
            room_participants[room].remove(request.sid)
            print(f"Removed {request.sid} from room {room}")
            if len(room_participants[room]) == 0:
                del room_participants[room]
                print(f"Room {room} deleted (empty)")
            else:
                # Notify others in the room
                emit('user-left', {'user': request.sid}, room=room)
                print(f"Notified room {room} that user {request.sid} left")

@socketio.on('join-room')
def handle_join(data):
    room = data['room']
    user_id = request.sid
    
    print(f"=== JOIN ROOM EVENT ===")
    print(f"User {user_id} joining room: {room}")
    
    # Initialize room if it doesn't exist
    if room not in room_participants:
        room_participants[room] = []
        print(f"Created new room: {room}")
    
    # Add user to room if not already there
    if user_id not in room_participants[room]:
        room_participants[room].append(user_id)
        print(f"Added user {user_id} to room {room}")
    else:
        print(f"User {user_id} already in room {room}")
    
    # Join the socket.io room
    join_room(room)
    
    current_participants = len(room_participants[room])
    print(f"Room {room} now has {current_participants} participants: {room_participants[room]}")
    
    # Send confirmation to the user who just joined
    emit('room-joined', {
        'room': room, 
        'participants': current_participants,
        'your_id': user_id
    })
    
    # If there are multiple users, notify about room readiness
    if current_participants > 1:
        # Notify all users in the room (including the new one)
        emit('room-ready', {
            'participants': current_participants,
            'room': room
        }, room=room)
        
        # Also send user-joined event to others (excluding the new user)
        emit('user-joined', {
            'user': user_id,
            'total_participants': current_participants
        }, room=room, include_self=False)
        
        print(f"Emitted room-ready and user-joined events for room {room}")
    else:
        # First user - waiting for others
        emit('waiting-for-participants', {
            'participants': current_participants,
            'room': room
        })
        print(f"First user in room {room}, sent waiting message")

@socketio.on('offer')
def handle_offer(data):
    room = data['room']
    offer = data['offer']
    sender = request.sid
    
    print(f"=== OFFER EVENT ===")
    print(f"Offer received from {sender} for room: {room}")
    print(f"Forwarding offer to other participants in room {room}")
    
    # Forward offer to all other participants in the room
    emit('offer', {
        'room': room,
        'offer': offer,
        'from': sender
    }, room=room, include_self=False)
    
    print(f"Offer forwarded to room {room}")

@socketio.on('answer')
def handle_answer(data):
    room = data['room']
    answer = data['answer']
    sender = request.sid
    
    print(f"=== ANSWER EVENT ===")
    print(f"Answer received from {sender} for room: {room}")
    print(f"Forwarding answer to other participants in room {room}")
    
    # Forward answer to all other participants in the room
    emit('answer', {
        'room': room,
        'answer': answer,
        'from': sender
    }, room=room, include_self=False)
    
    print(f"Answer forwarded to room {room}")

@socketio.on('ice-candidate')
def handle_ice(data):
    room = data['room']
    candidate = data['candidate']
    sender = request.sid
    
    print(f"ICE candidate from {sender} for room {room}")
    
    # Forward ICE candidate to all other participants
    emit('ice-candidate', {
        'room': room,
        'candidate': candidate,
        'from': sender
    }, room=room, include_self=False)

@socketio.on('leave-room')
def handle_leave(data):
    room = data['room']
    user_id = request.sid
    
    print(f"=== LEAVE ROOM EVENT ===")
    print(f"User {user_id} leaving room: {room}")
    
    if room in room_participants and user_id in room_participants[room]:
        room_participants[room].remove(user_id)
        print(f"Removed {user_id} from room {room}")
        
        if len(room_participants[room]) == 0:
            del room_participants[room]
            print(f"Room {room} deleted (empty)")
        else:
            # Notify remaining participants
            emit('user-left', {
                'user': user_id,
                'remaining_participants': len(room_participants[room])
            }, room=room)
            print(f"Notified room {room} that user {user_id} left")
    
    # Leave the socket.io room
    leave_room(room)
    print(f"User {user_id} left socket.io room {room}")

# Add a test endpoint to check room status
@app.route("/rooms")
def room_status():
    return {"rooms": room_participants, "total_rooms": len(room_participants)}

if __name__ == "__main__":
    print("Starting signaling server with HTTPS...")
    print("Make sure cert.pem and key.pem are in the same directory")
    
    # Run with HTTPS
    socketio.run(
        app, 
        host="0.0.0.0", 
        port=5001, 
        debug=True, 
        ssl_context=("cert.pem", "key.pem"),
        allow_unsafe_werkzeug=True
    )