#!/bin/bash

echo "=== Health Check ==="
exit_code=0

# Check Redis
echo "Checking Redis..."
redis-cli ping > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Redis is running"
else
    echo "⚠️ Redis is not responding (but may still work)"
fi

# Check Django on port 8001
echo "Checking Django server on port 8001..."
curl -s -f http://localhost:8001/login/ > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Django server is running on port 8001"
else
    echo "⚠️ Django server on port 8001 may have issues"
    exit_code=1
fi

# Check Apache proxy
echo "Checking Apache proxy on port 80..."
curl -s -f http://localhost:80/login/ > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Apache proxy is running on port 80"
else
    echo "⚠️ Apache proxy on port 80 may have issues"
    exit_code=1
fi

echo "=== Health Check Complete ==="
exit $exit_code 