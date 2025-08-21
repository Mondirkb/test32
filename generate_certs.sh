#!/bin/bash

echo " Generating SSL certificates for HTTPS..."

# Get the local IP address
LOCAL_IP=$(hostname -I | awk '{print $1}')
echo " Detected local IP: $LOCAL_IP"

# Create a config file for the certificate
cat > cert_config.conf << EOF
[req]
default_bits = 2048
prompt = no
default_md = sha256
distinguished_name = dn
req_extensions = v3_req

[dn]
C = US
ST = State
L = City
O = Organization
OU = IT Department
CN = $LOCAL_IP

[v3_req]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[alt_names]
IP.1 = $LOCAL_IP
IP.2 = 127.0.0.1
DNS.1 = localhost
EOF

# Generate private key
echo " Generating private key..."
openssl genrsa -out key.pem 2048

# Generate certificate
echo " Generating certificate..."
openssl req -new -x509 -key key.pem -out cert.pem -days 365 -config cert_config.conf -extensions v3_req

# Set permissions
chmod 600 key.pem
chmod 644 cert.pem

# Clean up
rm cert_config.conf

echo " SSL certificates generated successfully!"
echo " Files created:"
echo "   - cert.pem (certificate)"
echo "   - key.pem (private key)"
echo ""
echo " You can now access your app at:"
echo "   - Main app: https://$LOCAL_IP:5000"
echo "   - Signaling server: https://$LOCAL_IP:5001"
echo ""
echo "  Note: You'll need to accept the security warning in your browser"
echo "    since this is a self-signed certificate."