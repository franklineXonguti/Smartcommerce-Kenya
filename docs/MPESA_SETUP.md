# M-Pesa Integration Setup Guide

This guide will help you set up and test M-Pesa payments in the SmartCommerce Kenya platform.

## Prerequisites

1. M-Pesa Daraja API credentials (Consumer Key & Secret)
2. ngrok installed (for callback URL)
3. Django backend running

## Step 1: M-Pesa Credentials

Your `.env` file already has the sandbox credentials configured:

```env
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=9ZKgJtcDiXdb6xhAq1SVtviEcdK02zpLnTIew7Gak4YsDkkx
MPESA_CONSUMER_SECRET=GfVQQwrNwoMNe7gqRuHEkMdZ36ni00w7wp6d4OAnVaoLCV0OwGaf3EA9UdAM7wBA
MPESA_SHORTCODE=174379
MPESA_PASSKEY=bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919
```

## Step 2: Install and Setup ngrok

### Install ngrok

**Windows:**
```bash
# Download from https://ngrok.com/download
# Or use chocolatey
choco install ngrok
```

**Mac:**
```bash
brew install ngrok
```

**Linux:**
```bash
# Download and extract
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin
```

### Sign up for ngrok (Free)

1. Go to https://ngrok.com/
2. Sign up for a free account
3. Get your auth token from the dashboard
4. Run: `ngrok config add-authtoken YOUR_AUTH_TOKEN`

## Step 3: Start Your Django Server

```bash
cd backend
python manage.py runserver
```

Your server should be running on `http://localhost:8000`

## Step 4: Start ngrok

Open a new terminal and run:

```bash
ngrok http 8000
```

You'll see output like:
```
Session Status                online
Account                       your-email@example.com
Version                       3.x.x
Region                        United States (us)
Forwarding                    https://abc123.ngrok.io -> http://localhost:8000
```

Copy the `https://abc123.ngrok.io` URL (your URL will be different).

## Step 5: Update Callback URL

Update your `.env` file with the ngrok URL:

```env
MPESA_CALLBACK_URL=https://abc123.ngrok.io/api/payments/mpesa/callback/
```

**Important:** 
- Use the `https://` URL (not `http://`)
- Include the full path `/api/payments/mpesa/callback/`
- Restart your Django server after updating

## Step 6: Test M-Pesa Payment

### Using the API

1. **Create an order** (if you don't have one):
```bash
POST /api/orders/orders/checkout/
{
    "address_id": 1,
    "payment_method": "mpesa"
}
```

2. **Initiate M-Pesa payment**:
```bash
POST /api/payments/payments/initiate_mpesa/
{
    "order_id": 1,
    "phone_number": "0712345678"
}
```

Response:
```json
{
    "success": true,
    "message": "STK Push sent to your phone",
    "payment_id": 1,
    "checkout_request_id": "ws_CO_123456789",
    "merchant_request_id": "12345-67890-1"
}
```

3. **Check your phone** - You should receive an STK Push prompt

4. **Enter your M-Pesa PIN** to complete payment

5. **Check payment status**:
```bash
GET /api/payments/payments/1/status/
```

## Testing with Sandbox

### Test Phone Numbers

For sandbox testing, use these test phone numbers:
- `254708374149` - Success scenario
- `254708374150` - Insufficient funds
- `254708374151` - User cancelled

### Test Amounts

Any amount works in sandbox, but common test amounts:
- KES 1 - Minimum
- KES 10 - Small amount
- KES 100 - Medium amount
- KES 1000 - Large amount

## Monitoring Callbacks

### View ngrok requests

ngrok provides a web interface to see all requests:
```
http://localhost:4040
```

This shows:
- All incoming requests
- Request/response details
- Timing information

### Check Django logs

Watch your Django console for callback logs:
```
M-Pesa Callback received: {...}
Payment completed for order ORD-KE-2026-000001
```

## Troubleshooting

### Issue: "STK Push failed"

**Solutions:**
1. Check your consumer key and secret are correct
2. Verify you're using sandbox environment
3. Check phone number format (254XXXXXXXXX)
4. Ensure amount is an integer

### Issue: "Callback not received"

**Solutions:**
1. Verify ngrok is running
2. Check callback URL in `.env` is correct
3. Ensure URL uses `https://` not `http://`
4. Check ngrok web interface (http://localhost:4040) for incoming requests
5. Restart Django server after updating callback URL

### Issue: "Invalid phone number"

**Solutions:**
1. Use format: `0712345678` or `254712345678`
2. Don't include spaces or special characters
3. Use Kenyan phone numbers only (07XX or 01XX)

### Issue: "Order not found"

**Solutions:**
1. Ensure order exists and belongs to authenticated user
2. Check order status is 'pending'
3. Verify order hasn't been paid already

## API Endpoints Reference

### Initiate Payment
```
POST /api/payments/payments/initiate_mpesa/
Authorization: Bearer {token}

Request:
{
    "order_id": 1,
    "phone_number": "0712345678"
}

Response (Success):
{
    "success": true,
    "message": "STK Push sent to your phone",
    "payment_id": 1,
    "checkout_request_id": "ws_CO_123456789",
    "merchant_request_id": "12345-67890-1"
}

Response (Failure):
{
    "success": false,
    "message": "Failed to initiate payment",
    "payment_id": 1
}
```

### Check Payment Status
```
GET /api/payments/payments/{id}/status/
Authorization: Bearer {token}

Response:
{
    "payment_id": 1,
    "status": "completed",
    "completed_at": "2026-03-04T14:30:22Z"
}
```

### List Payments
```
GET /api/payments/payments/
Authorization: Bearer {token}

Response:
{
    "count": 1,
    "results": [
        {
            "id": 1,
            "order_number": "ORD-KE-2026-000001",
            "payment_method": "mpesa",
            "amount": "2200.00",
            "currency": "KES",
            "status": "completed",
            "created_at": "2026-03-04T14:25:00Z",
            "completed_at": "2026-03-04T14:30:22Z"
        }
    ]
}
```

## Production Deployment

When deploying to production:

1. **Get Production Credentials**
   - Apply for production access on Safaricom Developer Portal
   - Get production consumer key and secret
   - Get production shortcode and passkey

2. **Update Environment**
   ```env
   MPESA_ENVIRONMENT=production
   MPESA_CONSUMER_KEY=your_production_key
   MPESA_CONSUMER_SECRET=your_production_secret
   MPESA_SHORTCODE=your_production_shortcode
   MPESA_PASSKEY=your_production_passkey
   ```

3. **Set Production Callback URL**
   ```env
   MPESA_CALLBACK_URL=https://yourdomain.com/api/payments/mpesa/callback/
   ```

4. **Configure Safaricom Portal**
   - Register your callback URL in the Safaricom portal
   - Whitelist your server IP address
   - Test with small amounts first

## Support

For M-Pesa API issues:
- Safaricom Developer Portal: https://developer.safaricom.co.ke/
- Documentation: https://developer.safaricom.co.ke/Documentation
- Support: apisupport@safaricom.co.ke

For SmartCommerce issues:
- Check logs in Django console
- Review ngrok requests at http://localhost:4040
- Check payment records in Django admin
