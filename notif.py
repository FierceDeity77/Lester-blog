import smtplib
import os


class Notification:
    def __init__(self, name, email, phone, message):
        self.sender_name = name
        self.sender_email = email
        self.sender_phone = phone
        self.sender_message = message

    def send_email(self):
        email_message = (f"Subject:New Message\n\nName: {self.sender_name}\nEmail: {self.sender_email}"
                         f"\nPhone: {self.sender_phone}\nMessage:{self.sender_message}")
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=os.getenv("MY_MAIL_ADDRESS"), password=os.getenv("MAIL_APP_PW"))
            connection.sendmail(from_addr=self.sender_email,
                                to_addrs=os.getenv("MY_MAIL_ADDRESS"),
                                msg=email_message)
            print("Email Sent!")