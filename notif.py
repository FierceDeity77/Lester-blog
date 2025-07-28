import smtplib
import os


class Notification:
    def __init__(self, name_subj, email_frm, phone_to, message):
        self.sender_name_subj = name_subj
        self.sender_email_frm = email_frm
        self.sender_phone_to = phone_to
        self.sender_message = message

    def send_email(self):
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=os.getenv("MY_MAIL_ADDRESS"), password=os.getenv("MAIL_APP_PW"))
            connection.sendmail(from_addr=self.sender_email_frm,
                                to_addrs=self.sender_phone_to,
                                msg=f"Subject:{self.sender_name_subj} \n\n{self.sender_email_frm} "
                                    f"\n\n{self.sender_message}")

    def contact_email(self):
        with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
            connection.starttls()
            connection.login(user=os.getenv("MY_MAIL_ADDRESS"), password=os.getenv("MAIL_APP_PW"))
            connection.sendmail(from_addr=self.sender_email_frm,
                                to_addrs=os.environ.get('MY_MAIL_ADDRESS'),
                                msg=f"Subject:{self.sender_name_subj} \n\n{self.sender_email_frm} "
                                    f"\n\n{self.sender_phone_to}\n\n{self.sender_message}")
