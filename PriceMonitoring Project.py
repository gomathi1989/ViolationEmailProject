import smtplib
import pyodbc
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# SQL Server connection using Windows Authentication
conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=LAPTOP-GOMATHI\SQLEXPRESS;'          # e.g., "localhost\\SQLEXPRESS"
    'DATABASE=MAPProject;'      # e.g., "PriceMonitoringDB"
    'Trusted_Connection=yes;'
)
cursor = conn.cursor()

# Ensure ViolationLog table exists
cursor.execute("""
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ViolationLog' AND xtype='U')
CREATE TABLE ViolationLog (LogID INT IDENTITY(1,1) PRIMARY KEY,
    SKU VARCHAR(20),
    Marketplace VARCHAR(50),
    SellerName VARCHAR(100),
    Region VARCHAR(10),
    SellerPrice DECIMAL(10,2),
    MonitoringPrice DECIMAL(10,2),
    SellerEmail VARCHAR(100),
    SentAt DATETIME
);
""")
conn.commit()

# Query mismatches directly between Seller and PriceMonitoring
cursor.execute("""
SELECT 
    s.SKU,
    s.Marketplace,
    s.SellerName,
    s.Region,
    s.AdvertisedPrice AS SellerPrice,
    p.AdvertisedPrice AS MonitoringPrice
FROM Seller s
INNER JOIN PriceMonitoring p
    ON s.SKU = p.SKU
    AND s.Marketplace = p.Marketplace
    AND s.SellerName = p.SellerName
    AND s.Region = p.Region
WHERE s.AdvertisedPrice <> p.AdvertisedPrice;
""")

violations = cursor.fetchall()

# Email server settings (example: Outlook/Office365)
SMTP_SERVER = "smtp.office365.com"
SMTP_PORT = 587
EMAIL_ADDRESS = "manithivlogs@gmail.com"
EMAIL_PASSWORD = "Adhikavi$143"  # Use App Password if required

def send_violation_email(seller_email, sku, marketplace, region, seller_price, monitoring_price):
    subject = f"Price Violation Notification – SKU {sku}"
    body = f"""
Dear {seller_email},

We are writing to inform you that a discrepancy has been identified between your listed product prices and our monitored pricing records:

- SKU: {sku}
- Marketplace: {marketplace}
- Region: {region}
- Seller Price: {seller_price}
- Monitoring Price: {monitoring_price}

This mismatch violates the pricing policy agreed upon for marketplace listings. Please update your listing within the next 48 hours. Failure to comply may result in penalties, including suspension of your seller account.

If you believe this notification was sent in error, kindly reach out to our compliance team with supporting documentation.

Sincerely,
Compliance & Monitoring Team
[Your Company Name]
"""

    # Create email
    msg = MIMEMultipart()
    msg["From"] = EMAIL_ADDRESS
    msg["To"] = seller_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Send email
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
        server.send_message(msg)

    # Log into SQL table
    cursor.execute("""
        INSERT INTO ViolationLog (SKU, Marketplace, SellerName, Region, SellerPrice, MonitoringPrice, SellerEmail, SentAt)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (sku, marketplace, seller_name, region, seller_price, monitoring_price, seller_email, datetime.now()))
    conn.commit()

# Loop through violations and send emails + log
for violation in violations:
    sku, marketplace, seller_name, region, seller_price, monitoring_price = violation
    # Replace with actual seller email lookup logic
    seller_email = f"{seller_name.replace(' ', '').lower()}@example.com"
    send_violation_email(seller_email, sku, marketplace, region, seller_price, monitoring_price)

print("Violation emails sent and logged successfully.")
