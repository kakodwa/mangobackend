import time
import requests
from django.conf import settings


class PayChanguService:
    """
    PayChangu Integration Service
    Handles Collections (Mobile Money & Card) and Payouts (Mobile Money & Bank Transfers).
    Official Payout Docs: https://developer.paychangu.com/reference/mobile-money-payout
    """
    # PAYMENT / COLLECTION URLS
    BASE_MOBILE_URL = "https://api.paychangu.com/mobile-money/payments/initialize"
    BASE_CARD_URL = "https://api.paychangu.com/hosted-payment-page"

    # PAYOUT URLS
    BASE_MOBILE_PAYOUT_URL = "https://api.paychangu.com/mobile-money/payouts/initialize"
    BASE_BANK_PAYOUT_URL = "https://api.paychangu.com/direct-charge/payouts/initialize"

    # OPERATOR REFERENCE IDS
    OPERATORS = {
        "airtel_money": {
            "prefixes": ("099", "098", "99", "98"),
            "id": "20be6c20-adeb-4b5b-a7ba-0769820df4fb",
            "name": "Airtel Money",
        },
        "tnm_mpamba": {
            "prefixes": ("088", "089", "88", "89"),
            "id": "27494cb5-ba9e-437f-a114-4e7a7686bcca",
            "name": "TNM Mpamba",
        }
    }

    # =========================
    # HEADERS & AUTHENTICATION
    # =========================
    def _headers(self):
        return {
            "Authorization": f"Bearer {settings.PAYCHANGU_SECRET_KEY}",
            "Accept": "application/json",
            "Content-Type": "application/json"
        }

    # =========================
    # PHONE NUMBER NORMALIZER
    # =========================
    def _normalize_phone(self, phone: str):
        """
        Sanitizes phone input (+265, 265, or 099/088) and resolves operator reference ID.
        """
        clean_phone = str(phone).strip().replace(" ", "").replace("+", "")
        
        # Strip country code if provided
        if clean_phone.startswith("265"):
            clean_phone = clean_phone[3:]
            
        # Ensure standard local zero prefix
        if not clean_phone.startswith("0"):
            clean_phone = f"0{clean_phone}"

        for key, op in self.OPERATORS.items():
            if any(clean_phone.startswith(prefix) for prefix in op["prefixes"]):
                return {
                    "phone": clean_phone,
                    "operator_id": op["id"],
                    "operator_name": op["name"]
                }

        raise ValueError("Invalid phone number. PayChangu payouts support Airtel Money (099/098) or TNM Mpamba (088/089).")

    # =========================
    # PAYMENT COLLECTIONS
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

    def initiate_card_payment(self, payment, redirect_url=None):
        payload = {
            "public_key": getattr(settings, 'PAYCHANGU_PUBLIC_KEY', 'PUB-TEST-WW4IESP3O5ngh9whOMlCEqz18Pos4wl2'),
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

    def verify_payment(self, charge_id):
        url = f"https://api.paychangu.com/mobile-money/payments/{charge_id}/verify"

        response = requests.get(
            url,
            headers=self._headers()
        )

        return self._handle_response(response)

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
    # PAYOUT ROUTINES (FIXED UNIQUE CHARGE_ID)
    # =========================
    def send_mobile_payout(self, withdrawal):
        """
        Executes a Mobile Money Payout via PayChangu API.
        """
        try:
            phone_data = self._normalize_phone(withdrawal.account_number)
            user = withdrawal.user
            
            first_name = user.first_name if user.first_name else "Customer"
            last_name = user.last_name if user.last_name else f"User{user.id}"
            email = user.email if user.email else "payouts@yourdomain.com"

            # Appending unix timestamp ensures charge_id is unique even during retries
            unique_charge_id = f"WD-MOB-{withdrawal.id}-{int(time.time())}"

            payload = {
                "mobile": phone_data["phone"],
                "mobile_money_operator_ref_id": phone_data["operator_id"],
                "amount": f"{float(withdrawal.amount):.2f}",
                "charge_id": unique_charge_id,
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
            }

            response = requests.post(
                self.BASE_MOBILE_PAYOUT_URL, 
                json=payload, 
                headers=self._headers(),
                timeout=30
            )
            
            return response.json()
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Service Exception: {str(e)}"
            }

    def send_bank_payout(self, withdrawal):
        """
        Executes a Bank Transfer Payout via PayChangu Direct Charge API.
        """
        try:
            user = withdrawal.user
            email = user.email if user.email else "payouts@yourdomain.com"

            # Appending unix timestamp ensures charge_id is unique even during retries
            unique_charge_id = f"WD-BNK-{withdrawal.id}-{int(time.time())}"

            payload = {
                "payout_method": "bank_transfer",
                "bank_uuid": withdrawal.bank_uuid, 
                "amount": f"{float(withdrawal.amount):.2f}",
                "charge_id": unique_charge_id,
                "bank_account_name": withdrawal.account_holder_name,
                "bank_account_number": withdrawal.account_number,
                "email": email,
            }
            
            response = requests.post(
                self.BASE_BANK_PAYOUT_URL, 
                json=payload, 
                headers=self._headers(),
                timeout=30
            )
            
            return response.json()
        except Exception as e:
            return {
                "status": "failed",
                "message": f"Service Exception: {str(e)}"
            }