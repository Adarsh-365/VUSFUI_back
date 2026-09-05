from fastapi import APIRouter, Request, Header
from fastapi.responses import JSONResponse
import json
import razorpay
from src.services.payment_service import payment
from src.services.database_service import db

paymentrounter = APIRouter(prefix='/payment',tags=['payment'])

@paymentrounter.post("/verify-payment")
def verify_payment(data:dict):
  
    try:
        response1 = payment.verify(data)
        if response1.get('success'):
            db.verify_update(tabel='event_registrations',data=response1)
        return  response1 
    except razorpay.errors.SignatureVerificationError:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": "Invalid payment signature."
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "message": f"Payment verification failed: {str(e)}"
            }
        )

@paymentrounter.post("/webhook")
async def razorpay_webhook(request: Request, x_razorpay_signature: str = Header(None)):
    """
    Razorpay Webhook listener to handle dropped/abandoned mobile payments:
    Catches 'order.paid' or 'payment.captured' asynchronously and marks the registration as 'paid'.
    """
    try:
        raw_body_bytes = await request.body()
        raw_body_str = raw_body_bytes.decode('utf-8')
        
        # Verify webhook signature using RAZORPAY_WEBHOOK_SECRET
        sig = x_razorpay_signature or request.headers.get("x-razorpay-signature") or request.headers.get("X-Razorpay-Signature")
        if not payment.verify_webhook(raw_body_str, sig):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Invalid webhook signature"}
            )
        
        event_payload = json.loads(raw_body_str) if raw_body_str else {}
        event_type = event_payload.get("event")
        payload = event_payload.get("payload", {})
        
        # Handle payment success events
        if event_type in ["order.paid", "payment.captured"]:
            payment_entity = payload.get("payment", {}).get("entity", {})
            order_entity = payload.get("order", {}).get("entity", {})
            
            payment_id = payment_entity.get("id")
            order_id = payment_entity.get("order_id") or order_entity.get("id")
            
            if order_id and payment_id:
                update_data = {
                    "payment_id": payment_id,
                    "order_id": order_id,
                    "signature": sig or "webhook_auto_verified"
                }
                db.verify_update(tabel='event_registrations', data=update_data)
                return {
                    "status": "success",
                    "event": event_type,
                    "message": f"Updated order {order_id} to paid",
                    "payment_id": payment_id
                }
                
        return {"status": "ignored", "event": event_type}

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )
