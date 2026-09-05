# import smtplib
# import ssl
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

# # 1. Setup email configuration
# smtp_server = "://gmail.com"  # Change for your provider
# port = 465  # For SSL
# sender_email = "india.namaste1998@gmail.com"
# receiver_email = "adarshtayde9011@gmail.com"

# password = "your_app_password"  # Do not use your main password

# # 2. Create the message
# message = MIMEMultipart()
# message["From"] = sender_email
# message["To"] = receiver_email
# message["Subject"] = "Python Email Test"

# body = "Hello! This email was sent automatically using Python."
# message.attach(MIMEText(body, "plain"))

# # 3. Connect to server and send
# context = ssl.create_default_context()
# with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
#     server.login(sender_email, password)
#     server.sendmail(sender_email, receiver_email, message.as_string())

# print("Email sent successfully!")
