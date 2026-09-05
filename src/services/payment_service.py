
import os
amount_str = os.environ.get("COURCE_COST")
from src.core.payment import client
RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
TABLE_NAME = os.getenv("TABLE_NAME", "business_leads")
import uuid
import time

class Payment:
    def __init__(self):
        
        self.client = client
    
    def verify(self, data):
        """
        Verifies Razorpay payment signature.
        Raises razorpay.errors.SignatureVerificationError if signature is invalid.
        """
        self.client.utility.verify_payment_signature({
            "razorpay_order_id": data["razorpay_order_id"],
            "razorpay_payment_id": data["razorpay_payment_id"],
            "razorpay_signature": data["razorpay_signature"]
        })
        return {
            "success": True,
            "message": "Payment verified successfully.",
            "payment_id": data["razorpay_payment_id"],
            "order_id": data["razorpay_order_id"],
            "signature": data["razorpay_signature"]
        }

    def verify_webhook(self, raw_body: str, signature: str) -> bool:
        webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET")
        if not webhook_secret:
            print("Warning: RAZORPAY_WEBHOOK_SECRET not configured in .env; skipping verification.")
            return True
        if not signature:
            print("Error: Webhook signature header missing.")
            return False
        try:
            self.client.utility.verify_webhook_signature(raw_body, signature, webhook_secret)
            return True
        except Exception as e:
            print(f"Webhook signature verification failed: {e}")
            return False

    def create_order(self,cost):
        # print(data)
        try:
            
            order = self.client.order.create({
                "amount": int(cost),  # amount in paise
                "currency": "INR",
                "receipt": f"rcpt_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            })
            
            return {
                "order_id": order["id"],
                "key": RAZORPAY_KEY_ID,
                "amount": order["amount"],
                "currency": order["currency"]
            }
        
        except:
            return {
                "Success":False,
                  "message":"Verification Faild"
            }
            

payment = Payment()