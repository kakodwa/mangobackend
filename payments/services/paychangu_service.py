import requests
from django.conf import settings


class PayChanguService:
    """
    Reusable PayChangu integration service
    """
    #Payment URL
    #BASE_CARD_URL = "https://api.paychangu.com/charge-card/payments"
    BASE_MOBILE_URL = "https://api.paychangu.com/mobile-money/payments/initialize"
    BASE_CARD_URL = "https://api.paychangu.com/hosted-payment-page"

    #PAYOUT URL
    BASE_MOBILE_PAYOUT_URL = "https://api.paychangu.com/mobile-money/payouts/initialize"
    BASE_BANK_PAYOUT_URL = "https://api.paychangu.com/direct-charge/payouts/initialize"


    OPERATORS = {
        "airtel_money": {
            "prefixes": ("099", "098"),
            "id": "20be6c20-adeb-4b5b-a7ba-0769820df4fb",
            "name": "Airtel Money",
        },
        "tnm_mpamba": {
            "prefixes": ("088", "089"),
            "id": "27494cb5-ba9e-437f-a114-4e7a7686bcca",
            "name": "TNM Mpamba",
        }
    }

    # =========================
    # HEADERS
    # =========================
    def _headers(self):
        return {
            "Authorization": f"Bearer {settings.PAYCHANGU_SECRET_KEY}",
            "Content-Type": "application/json"
        }

    # =========================
    # PHONE DETECTION
    # =========================
    def _normalize_phone(self, phone: str):
        phone = phone.strip() 
        for key, op in self.OPERATORS.items():
            if any(phone.startswith(prefix) for prefix in op["prefixes"]):
                return {
                "phone": phone,
                "operator_id": op["id"],
                "operator_name": op["name"]
                }

        raise ValueError("Invalid Malawi phone number (099, 098, 088, 089 only)")

    # =========================
    # MOBILE MONEY
    # =========================
    def initiate_mobile_money(self, payment, phone_number):
        phone_data = self._normalize_phone(phone_number)

        payload = {
        "amount": float(payment.amount),
        "currency": "MWK",
        "mobile": phone_data["phone"],
        "mobile_money_operator_ref_id": phone_data["operator_id"],
        "charge_id": payment.payment_reference,
        "email": payment.user.email,
        }

        response = requests.post(
            self.BASE_MOBILE_URL,
            json=payload,
            headers=self._headers()
            )

        return self._handle_response(response)

    # =========================
    # CARD PAYMENT
    # =========================
    def initiate_card_payment(self, payment, redirect_url=None):

        payload = {
        "public_key":"PUB-TEST-WW4IESP3O5ngh9whOMlCEqz18Pos4wl2",
        "amount": float(payment.amount),
        "currency": "MWK",
        "email": payment.user.email,
        "tx_ref": payment.payment_reference,
        "callback_url": redirect_url,
        "return_url": redirect_url,
        }

        response = requests.post(
            self.BASE_CARD_URL,
            json=payload,
            headers=self._headers()
        )

        return self._handle_response(response)

    # =========================
    # VERIFY PAYMENT
    # =========================
    def verify_payment(self, charge_id):
        url = f"https://api.paychangu.com/mobile-money/payments/{charge_id}/verify"

        response = requests.get(
            url,
            headers=self._headers()
        )

        return self._handle_response(response)

    # =========================
    # RESPONSE HANDLER
    # =========================
    def _handle_response(self, response):
        try:
            data = response.json()
        except Exception:
            return {
                "success": False,
                "error": "Invalid JSON response",
                "raw": response.text
            }

        if response.status_code in [200, 201]:
            return {
                "success": True,
                "data": data
            }

        return {
            "success": False,
            "status_code": response.status_code,
            "error": data
        }


    # =========================
    # PAYCHANGU MOBILE MONEY DISBURSEMENT
    # =========================
    def send_mobile_payout(self, withdrawal):
        phone_data = self._normalize_phone(withdrawal.account_number)
        
        payload = {
            "mobile": phone_data["phone"],
            "mobile_money_operator_ref_id": phone_data["operator_id"],
            "amount": str(withdrawal.amount),
            "charge_id": f"WD-MOB-{withdrawal.id}",
            "email": withdrawal.user.email,
            "first_name": withdrawal.user.first_name,
            "last_name": withdrawal.user.last_name,
        }
        
        response = requests.post(self.BASE_MOBILE_PAYOUT_URL, json=payload, headers=self._headers())
        return response.json()

    # =========================
    # PAYCHANGU BANK DISBURSEMENT
    # =========================
    def send_bank_payout(self, withdrawal):
        payload = {
            "payout_method": "bank_transfer",
            "bank_uuid": withdrawal.bank_uuid, 
            "amount": str(withdrawal.amount),
            "charge_id": f"WD-BNK-{withdrawal.id}",
            "bank_account_name": withdrawal.account_holder_name,
            "bank_account_number": withdrawal.account_number,
            "email": withdrawal.user.email,
        }
        
        response = requests.post(self.BASE_BANK_PAYOUT_URL, json=payload, headers=self._headers())
        return response.json()