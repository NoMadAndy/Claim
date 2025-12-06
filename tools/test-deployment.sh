#!/bin/bash
# Test deployed application

DOMAIN="claim.macherwerkstatt.cc"
URL="https://$DOMAIN"

echo "=== Testing Deployment: $URL ==="
echo ""

# Test 1: Check if site is up
echo "1. Testing site availability..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$URL")
if [ "$HTTP_CODE" == "200" ]; then
    echo "✅ Site is up (HTTP $HTTP_CODE)"
else
    echo "❌ Site returned HTTP $HTTP_CODE"
fi
echo ""

# Test 2: Check cache headers
echo "2. Checking cache headers (HTML)..."
echo "Cache-Control headers:"
curl -s -I "$URL" | grep -i "cache-control" || echo "❌ No Cache-Control header found"
echo ""

# Test 3: Check for new app.js version
echo "3. Checking app.js cache buster..."
CACHE_BUSTER=$(curl -s "$URL" | grep -o 'app\.js?v=[0-9]*' | head -1)
if [ -n "$CACHE_BUSTER" ]; then
    echo "✅ Found cache buster: $CACHE_BUSTER"
else
    echo "❌ No cache buster found in HTML"
fi
echo ""

# Test 4: Check if API is responding
echo "4. Testing API health check..."
API_HEALTH=$(curl -s "$URL/api/health" | grep -o "healthy")
if [ -n "$API_HEALTH" ]; then
    echo "✅ API is responding (health: $API_HEALTH)"
else
    echo "❌ API health check failed"
fi
echo ""

# Test 5: Check app.js content for cooldown message
echo "5. Checking for new cooldown feature..."
COOLDOWN_CHECK=$(curl -s "$URL/app.js" | grep -o "Cooldown active: .* remaining" | head -1)
if [ -n "$COOLDOWN_CHECK" ]; then
    echo "✅ New cooldown message found"
else
    echo "⚠️  Cooldown message not found (might be minified or old cache)"
fi
echo ""

echo "=== Test Complete ==="
echo ""
echo "If tests fail:"
echo "1. Check if server is running"
echo "2. Do a hard refresh in browser (Ctrl+Shift+R)"
echo "3. Check browser DevTools → Network → Response Headers"
