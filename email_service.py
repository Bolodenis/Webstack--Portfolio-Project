import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(name, email, message):
    sender_email = "bollodenis5020@gmail.com"  # Replace with your email
    receiver_email = "bollodenis5020@gmail.com"  # Replace with the receiver's email
    password = "Bolo@32073134"  # Replace with your email password

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = f"Contact Form Message from {name}"

    body = f"Message from: {name}\nEmail: {email}\n\nMessage:\n{message}"
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        print("Email sent successfully")
    except Exception as e:
        print(f"Error: {e}")
