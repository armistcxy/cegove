# Payment API Migration Guide: v1 → v2

## Overview

The Payment Service API v2 introduces breaking changes to improve API consistency and clarity. v1 will be **sunset on February 26, 2026** (90 days from release).

## Timeline

| Date | Event |
|------|-------|
| Now (Nov 26, 2025) | v2 released, v1 marked as deprecated |
| Feb 26, 2026 | v1 endpoints stop accepting requests |
| After Feb 26, 2026 | v1 endpoints return 410 Gone |

## Deprecation Signals

When calling v1 endpoints, you'll receive these headers:

```
Deprecation: true
Sunset: Wed, 26 Feb 2026 23:59:59 GMT
Link: </api/v2/payments>; rel="successor-version"
Warning: 299 - "API v1 is deprecated. Will be removed on 2026-02-26. Please migrate to /api/v2/ endpoints."
X-API-Warn: v1 endpoints will sunset on 2026-02-26. Migrate to v2: /api/v2/payments
```

## Breaking Changes

### 1. Field Renames in Request/Response

All v1 fields have been renamed for better clarity:

| v1 Field | v2 Field | Type | Notes |
|----------|----------|------|-------|
| `booking_id` | `order_id` | `integer` | References the customer's order |
| `provider` | `payment_provider` | `string` | Payment gateway provider |
| `amount` | `total_amount` | `decimal` | Total amount to be paid |
| `status` | `payment_status` | `string` | Current payment state |
| N/A | `currency` | `string` | **NEW**: Currency code (e.g., 'VND') |

### 2. Response Wrapping Changes

#### v1 Response (POST /api/v1/payments)
```json
{
  "payment": {
    "id": 1,
    "booking_id": 12345,
    "provider": "vnpay",
    "amount": 100000.00,
    "status": "pending"
  },
  "url": "https://sandbox.vnpayment.vn/paygate?..."
}
```

#### v2 Response (POST /api/v2/payments)
```json
{
  "result": {
    "id": 1,
    "order_id": 12345,
    "payment_provider": "vnpay",
    "total_amount": 100000.00,
    "payment_status": "pending",
    "currency": "VND"
  },
  "redirect_url": "https://sandbox.vnpayment.vn/paygate?..."
}
```

### 3. Endpoint Changes

#### Create Payment

**v1 (DEPRECATED)**
```bash
curl -X POST http://localhost:8000/api/v1/payments \
  -H "Content-Type: application/json" \
  -d '{
    "booking_id": 12345,
    "provider": "vnpay",
    "amount": 100000.00,
    "status": "pending",
    "client_ip": "192.168.1.1"
  }'
```

**v2 (NEW)**
```bash
curl -X POST http://localhost:8000/api/v2/payments \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 12345,
    "payment_provider": "vnpay",
    "total_amount": 100000.00,
    "payment_status": "pending",
    "currency": "VND",
    "client_ip": "192.168.1.1"
  }'
```

#### Get Payment Details

**v1 (DEPRECATED)**
```bash
curl http://localhost:8000/api/v1/payments/1
```

Response:
```json
{
  "id": 1,
  "booking_id": 12345,
  "provider": "vnpay",
  "amount": 100000.00,
  "status": "pending"
}
```

**v2 (NEW)**
```bash
curl http://localhost:8000/api/v2/payments/1
```

Response:
```json
{
  "id": 1,
  "order_id": 12345,
  "payment_provider": "vnpay",
  "total_amount": 100000.00,
  "payment_status": "pending",
  "currency": "VND"
}
```

#### List Payments

**v1 (DEPRECATED)**
```bash
curl http://localhost:8000/api/v1/payments?page=1&per_page=20
```

Response:
```json
[
  {
    "id": 1,
    "booking_id": 12345,
    "provider": "vnpay",
    "amount": 100000.00,
    "status": "pending"
  }
]
```

**v2 (NEW)**
```bash
curl http://localhost:8000/api/v2/payments?page=1&per_page=20
```

Response:
```json
[
  {
    "id": 1,
    "order_id": 12345,
    "payment_provider": "vnpay",
    "total_amount": 100000.00,
    "payment_status": "pending",
    "currency": "VND"
  }
]
```

### 4. Webhook Endpoints (No Changes)

VNPay webhook endpoints remain unchanged:

- `GET /api/v1/payments/vnpay/ipn` → Still works (same as v2)
- `GET /api/v1/payments/vnpay/return` → Still works (same as v2)
- `GET /api/v2/payments/vnpay/ipn` → New v2 equivalent
- `GET /api/v2/payments/vnpay/return` → New v2 equivalent

## Migration Steps

### Step 1: Update Client Code

Replace all v1 endpoints with v2 equivalents:

```python
# BEFORE (v1)
def create_payment(booking_id, amount):
    response = requests.post(
        "http://api.example.com/api/v1/payments",
        json={
            "booking_id": booking_id,
            "provider": "vnpay",
            "amount": amount,
            "status": "pending",
            "client_ip": "192.168.1.1"
        }
    )
    payment = response.json()
    return payment["payment"]["id"], payment["url"]

# AFTER (v2)
def create_payment(order_id, amount):
    response = requests.post(
        "http://api.example.com/api/v2/payments",
        json={
            "order_id": order_id,
            "payment_provider": "vnpay",
            "total_amount": amount,
            "payment_status": "pending",
            "currency": "VND",
            "client_ip": "192.168.1.1"
        }
    )
    payment = response.json()
    return payment["result"]["id"], payment["redirect_url"]
```

### Step 2: Update Field References

Search and replace in your codebase:
- `booking_id` → `order_id`
- `provider` → `payment_provider`
- `amount` → `total_amount`
- `status` → `payment_status`
- `payment["payment"]` → `payment["result"]`
- `payment["url"]` → `payment["redirect_url"]`

### Step 3: Handle Currency Field

Add currency handling in your application:

```python
# Always include currency when creating payments
currency = "VND"  # Or get from configuration
response = requests.post(
    "/api/v2/payments",
    json={
        ...,
        "currency": currency
    }
)
```

### Step 4: Test Thoroughly

- Test all payment creation flows
- Verify payment retrieval returns correct field names
- Test webhook callbacks (both v1 and v2)
- Monitor deprecation headers in v1 responses during testing

### Step 5: Deploy and Monitor

1. Deploy updated client code
2. Monitor logs for deprecation warnings
3. Track API usage to ensure migration is complete
4. Remove v1 calls before sunset date

## Monitoring Deprecation

### From Your Application

Check for deprecation headers in responses:

```python
import requests

response = requests.get("http://api.example.com/api/v1/payments/1")

if response.headers.get("Deprecation") == "true":
    sunset = response.headers.get("Sunset")
    print(f"WARNING: This endpoint is deprecated and will sunset on {sunset}")
    successor = response.headers.get("Link")
    print(f"Please migrate to: {successor}")
```

### From Your Infrastructure

If using API Gateway or proxy (Kong, Nginx, etc.):
- Enable logging of `Deprecation` header
- Alert when traffic to `/api/v1/` increases
- Block traffic after Feb 26, 2026 (sunset date)

## FAQ

**Q: Can I use v1 and v2 simultaneously?**  
A: Yes, during the 90-day migration period (Nov 26, 2025 - Feb 26, 2026), both versions are supported.

**Q: What happens to v1 after sunset?**  
A: v1 endpoints will return HTTP 410 (Gone) after Feb 26, 2026.

**Q: Are webhooks affected?**  
A: No, webhook behavior is identical. VNPay webhooks work with both v1 and v2.

**Q: How do I update Swagger documentation?**  
A: Use the new `/api/v2` endpoints in your API documentation. v1 endpoints are marked deprecated.

**Q: Is there a compatibility layer?**  
A: No, you must update your client code. However, the fields map 1:1, so migration is straightforward.

## Support

For questions or issues during migration:
1. Check the Swagger UI at `/docs` for v2 endpoint documentation
2. Review breaking changes in this guide
3. Test using Postman or cURL examples above
