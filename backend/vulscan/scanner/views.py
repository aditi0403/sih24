from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Subscriber
from .serializers import SubscriberSerializer
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from fpdf import FPDF
import smtplib
from email.mime.text import MIMEText

# Initialize WebDriver
def initialize_driver():
    driver_path = r"C:\Users\ACER\.cache\selenium\chromedriver\win64\128.0.6613.119\chromedriver.exe"
    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service)

    return driver
# Scraping logic for Cisco
def scrape_cisco(driver):
    data = []
    driver.get("https://sec.cloudapps.cisco.com/security/center/publicationListing.x")
    Wait = WebDriverWait(driver, 10)
    Wait.until(EC.presence_of_element_located((By.XPATH, ".//table[@class='advisoryAlertTable']")))

    rows = Wait.until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'rowRepeat')))
    one_week_ago = datetime.now() - timedelta(days=7)
    
    for row in rows:
        title_element = row.find_element(By.XPATH, ".//span[@class='advListItem']/a")
        title = title_element.text
        link = title_element.get_attribute("href")
        severity = row.find_element(By.CSS_SELECTOR, "span.ng-binding").text
        cve = row.find_element(By.XPATH, "//span[@class='ng-binding' and contains(@ng-bind, 'list.cve.split')]").text
        last_update = row.find_element(By.XPATH, ".//td[@width='15%']/span[@class='ng-binding']").text
        version = row.find_element(By.XPATH, ".//td[@width='10%']/span[@ng-if]").text

        last_update_date = datetime.strptime(last_update, "%Y %b %d")
        if last_update_date >= one_week_ago:
            data.append({
                "Title": title,
                "OEM": "Cisco",
                "Severity": severity,
                "CVE": cve,
                "Last Update": last_update,
                "Version": version,
                "Mitigation_Strategy": f"Patches details {link}"
            })
    return data

# Scraping logic for Microsoft (Placeholder)
def scrape_microsoft(driver):
    data = []
    # Implement Microsoft scraping logic here
    return data

# Scraping logic for IBM (Placeholder)
def scrape_ibm(driver):
    data = []
    # Implement IBM scraping logic here
    return data

# Generate PDF report
def generate_pdf_report(data, report_path):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    pdf.set_font("Arial", style='B', size=14)
    pdf.cell(200, 10, txt="Vulnerability Report", ln=True, align='C')
    pdf.ln(10)
    
    for entry in data:
        pdf.set_font("Arial", style='B', size=12)
        pdf.multi_cell(0, 8, f"Title: {entry['Title']}", align='L')
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 8, f"OEM Name: {entry['OEM']}", align='L')
        pdf.multi_cell(0, 8, f"Severity: {entry['Severity']}", align='L')
        pdf.multi_cell(0, 8, f"CVE: {entry['CVE']}", align='L')
        pdf.multi_cell(0, 8, f"Last Update: {entry['Last Update']}", align='L')
        pdf.multi_cell(0, 8, f"Version: {entry['Version']}", align='L')
        mitigation_text = f"Mitigation Strategy:{entry['Mitigation_Strategy']}"
        pdf.multi_cell(0, 8, mitigation_text.strip(), align='L')
        pdf.ln(3)
    
    pdf.output(report_path)
    print("Report is generated.")



def send_email(recipient, report_path):
    sender = "vulnerabilityscanreport@gmail.com"
    password = "kcsa txgn ijhg aqsc"
    subject = "Vulnerability Report"
    body = "Please find the attached vulnerability report."

    # Create the email message
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    # Attach the body text
    msg.attach(MIMEText(body, "plain"))

    # Attach the PDF file
    with open(report_path, "rb") as f:
        attachment = MIMEApplication(f.read(), _subtype="pdf")
        attachment.add_header("Content-Disposition", "attachment", filename="vulnerability_report.pdf")
        msg.attach(attachment)

    # Send the email
    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.starttls()  # Upgrade the connection to a secure encrypted SSL/TLS connection
            smtp.login(sender, password)
            smtp.send_message(msg)
    except Exception as e:
        print(f"Failed to send email: {e}")


@api_view(['POST'])
def subscribe(request):
    serializer = SubscriberSerializer(data=request.data)
    if serializer.is_valid():
        subscriber = serializer.save()

        # Scrape data from Cisco
        driver = initialize_driver()
        cisco_data = scrape_cisco(driver)
        driver.quit()

        # Scrape data from Microsoft (Placeholder)
        # microsoft_data = scrape_microsoft(driver)

        # Scrape data from IBM (Placeholder)
        # ibm_data = scrape_ibm(driver)

        all_data = cisco_data
        # all_data.extend(microsoft_data)
        # all_data.extend(ibm_data)

        # Generate PDF report
        report_path = "vulnerability_report.pdf"
        generate_pdf_report(all_data, report_path)

        # Send email with the report
        send_email(subscriber.email, report_path)

        return Response({"message": "Email sent successfully. Please check your inbox."}, status=status.HTTP_201_CREATED)
    return Response(serializer.error*s, status=status.HTTP_400_BAD_REQUEST)