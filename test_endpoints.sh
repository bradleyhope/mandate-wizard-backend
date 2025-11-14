#!/bin/bash

echo "=== Testing Demand Analytics Endpoints ==="
echo ""

echo "1. GET /api/analytics/demand/stats"
curl -s "https://mandate-wizard-backend.onrender.com/api/analytics/demand/stats" | python3 -m json.tool
echo -e "\n"

echo "2. GET /api/analytics/demand/top?limit=5"
curl -s "https://mandate-wizard-backend.onrender.com/api/analytics/demand/top?limit=5" | python3 -m json.tool
echo -e "\n"

echo "3. GET /api/analytics/demand/trending?limit=5"
curl -s "https://mandate-wizard-backend.onrender.com/api/analytics/demand/trending?limit=5" | python3 -m json.tool
echo -e "\n"

echo "4. GET /api/analytics/demand/stale?limit=5"
curl -s "https://mandate-wizard-backend.onrender.com/api/analytics/demand/stale?limit=5" | python3 -m json.tool
echo -e "\n"

echo "5. GET /api/analytics/demand/entity/1 (testing with entity_id=1)"
curl -s "https://mandate-wizard-backend.onrender.com/api/analytics/demand/entity/1" | python3 -m json.tool
echo -e "\n"

echo "=== All tests complete ==="
