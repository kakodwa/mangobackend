# utils/sms.py
import africastalking

africastalking.initialize("sandbox", "atsk_0632e00cec7a536a7632b200ea4968ff62b5f78b994b79d11dd3c8bd153a98214b0990de")

sms = africastalking.SMS



def send_sms(phone, message):
    try:
        response = sms.send(
            message,
            [phone],
            "MANGOSYS"  # sender ID (optional)
        )
        return response
    except Exception as e:
        print("SMS error:", e)
        return None