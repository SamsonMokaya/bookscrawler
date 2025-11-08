#!/bin/bash
# MongoDB Replica Set Initialization Script
# This script initializes the MongoDB replica set for transaction support
# Run this from the project root after starting docker-compose

set -e

echo "========================================="
echo "MongoDB Replica Set Initialization"
echo "========================================="

# Wait for MongoDB to be ready
echo "Waiting for MongoDB to start..."
sleep 10

# Initialize replica set
echo "Initializing replica set 'rs0'..."
docker exec bookscrawler_mongodb mongosh -u admin -p admin123 --authenticationDatabase admin --eval "
try {
    rs.status();
    print('Replica set already initialized');
} catch(e) {
    rs.initiate({
        _id: 'rs0',
        members: [{ _id: 0, host: 'mongodb:27017' }]
    });
    print('Replica set initialized successfully');
}
" 2>&1 | grep -v "Current Mongosh"

echo ""
echo "========================================="
echo "Setup complete!"
echo "========================================="
echo ""
echo "You can now run crawls with transaction support."
