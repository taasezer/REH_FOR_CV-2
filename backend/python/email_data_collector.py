import re
from app import db, Kisi

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def collect_emails():
    emails = []
    kisiler = Kisi.query.all()
    for kisi in kisiler:
        if validate_email(kisi.eposta):
            emails.append(kisi.eposta)
    return emails

def export_emails_to_file(filename="emails.txt"):
    emails = collect_emails()
    with open(filename, 'w') as file:
        for email in emails:
            file.write(f"{email}\n")
    return filename
