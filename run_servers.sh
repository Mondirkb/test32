#!/bin/bash

echo " Starting Meeting Web App with WebRTC..."

# Check if SSL certificates exist
if [ ! -f "cert.pem" ] || [ ! -f "key.pem" ]; then
    echo " SSL certificates not found!"
    echo " Please run the certificate generator first:"
    echo "   chmod +x generate_certs.sh"
    echo "   ./generate_certs.sh"
    exit 1
fi

echo " SSL certificates found ✅"

# Get the local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')

echo " Local IP: $LOCAL_IP"
echo " URLs:"
echo "   - Main App: https://$LOCAL_IP:5000"
echo "   - Signaling Server: https://$LOCAL_IP:5001"
echo ""

# Function to cleanup on exit
cleanup() {
    echo ""
    echo " Stopping servers..."
    pkill -f "python.*signaling_server.py"
    pkill -f "python.*app.py"
    echo " Cleanup complete"
    exit 0
}

# Set trap to cleanup on Ctrl+C
trap cleanup INT TERM

# Start signaling server in background
echo " Starting signaling server..."
python3 signaling_server.py &
SIGNALING_PID=$!

# Wait a bit for signaling server to start
sleep 3

# Start main app
echo "  Starting main Flask app..."
python3 app.py &
APP_PID=$!

echo ""
echo " Both servers are running!"
echo " Access from mobile devices using: https://$LOCAL_IP:5000"
echo "  Accept security warnings for self-signed certificates"
echo " Press Ctrl+C to stop both servers"
echo ""

# Wait for both processes
wait $SIGNALING_PID $APP_PID