#!/bin/bash

echo "=== Testing Prioritization Endpoints ==="
echo ""

echo "1. GET /api/priority/statistics"
curl -s "https://mandate-wizard-backend.onrender.com/api/priority/statistics" | python3 -m json.tool
echo -e "\n"

echo "2. GET /api/priority/batch?limit=5"
curl -s "https://mandate-wizard-backend.onrender.com/api/priority/batch?limit=5" | python3 -m json.tool
echo -e "\n"

echo "3. GET /api/priority/critical"
curl -s "https://mandate-wizard-backend.onrender.com/api/priority/critical" | python3 -m json.tool
echo -e "\n"

echo "4. GET /api/priority/schedule?daily_budget=100"
curl -s "https://mandate-wizard-backend.onrender.com/api/priority/schedule?daily_budget=100" | python3 -m json.tool | head -50
echo -e "\n"

echo "=== All tests complete ==="
