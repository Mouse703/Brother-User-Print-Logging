import os
import shutil
import csv
from datetime import datetime
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import paho.mqtt.client as mqtt
from selenium.webdriver.firefox.options import Options
import json

# -----------------------------
# Configuration from environment
# -----------------------------
MQTT_BROKER = os.environ.get("MQTT_BROKER", "192.168.1.100")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")
MQTT_TOPIC_BASE = os.environ.get("MQTT_TOPIC_BASE", "printer/userdata")

PRINTER_URL = os.environ.get("PRINTER_URL", "http://192.168.1.50")
PRINTER_PASSWORD = os.environ.get("PRINTER_PASSWORD", "")

DOWNLOADS_FOLDER = os.environ.get("DOWNLOADS_FOLDER", "/downloads")
DESTINATION_FOLDER = os.environ.get("DESTINATION_FOLDER", "/logs")
DOWNLOADED_FILE = os.path.join(DOWNLOADS_FOLDER, "secure30_lock.csv")

# -----------------------------
# User mapping: from environment JSON or default
# -----------------------------
default_user_mapping = {
    "ADMIN": "louis"
}

user_mapping_env = os.environ.get("USER_MAPPING_JSON", "")
try:
    if user_mapping_env:
        user_mapping = json.loads(user_mapping_env)
        print("Using user mapping from environment variable.")
    else:
        user_mapping = default_user_mapping
        print("Using default user mapping.")
except json.JSONDecodeError as e:
    print(f"Invalid USER_MAPPING_JSON: {e}. Falling back to default.")
    user_mapping = default_user_mapping

# -----------------------------
# Ensure destination folder exists
# -----------------------------
os.makedirs(DESTINATION_FOLDER, exist_ok=True)

def download_csv_with_webdriver():
    print("Starting Selenium WebDriver to download CSV file...")

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Firefox(options=options)

    try:
        driver.get(PRINTER_URL)
        print("Accessing printer web interface...")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "LogBox"))
        ).send_keys(PRINTER_PASSWORD)
        print("Entered password.")

        driver.find_element(By.ID, "login").click()
        print("Clicked login button.")

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "mainContent"))
        )
        print("Logged in successfully.")

        admin_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/admin/password.html')]"))
        )
        admin_tab.click()
        print("Navigated to Admin tab.")

        last_counter_tab = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, '/admin/secure_function_lock_last_counter_record_30.html')]"))
        )
        last_counter_tab.click()
        print("Navigated to Last Counter Reading tab.")

        export_button = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, '//form[@action="/admin/secure30_lock.csv"]//input[@value="Export to CSV file"]'))
        )
        driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
        time.sleep(1)
        export_button.click()
        print("CSV export started.")
        time.sleep(5)

    except Exception as e:
        print(f"Error during CSV download: {e}")

    finally:
        driver.quit()
        print("WebDriver closed.")

def rename_and_move_csv_file():
    print("Renaming and moving the CSV file...")
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    renamed_file = f"printLog_{timestamp}.csv"
    destination_path = os.path.join(DESTINATION_FOLDER, renamed_file)

    if os.path.exists(DOWNLOADED_FILE):
        try:
            shutil.move(DOWNLOADED_FILE, destination_path)
            print(f"File renamed and moved to {destination_path}")
            return destination_path
        except Exception as e:
            print(f"Error moving file: {e}")
            raise
    else:
        raise FileNotFoundError(f"File {DOWNLOADED_FILE} not found.")

def publish_to_mqtt(file_path):
    print("Starting MQTT publishing...")

    client = mqtt.Client()
    if MQTT_USERNAME and MQTT_PASSWORD:
        client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)

    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    print("Connected to MQTT broker.")

    try:
        user_data = {}

        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                user = user_mapping.get(row['Name'])
                if user:
                    if user not in user_data:
                        user_data[user] = {"total": 0, "total_bw": 0, "total_color": 0}

                    user_data[user]["total"] += int(row['Current Total'])
                    user_data[user]["total_bw"] += int(row['Current B&W'])
                    user_data[user]["total_color"] += int(row['Current Color'])

        for user, subtopics in user_data.items():
            for subtopic, value in subtopics.items():
                topic = f"{MQTT_TOPIC_BASE}/{user}/{subtopic}"
                retries = 3
                while retries > 0:
                    result = client.publish(topic, value)
                    if result.rc == 0:
                        print(f"Published {value} to {topic}")
                        break
                    else:
                        print(f"Failed to publish {value} to {topic}, retrying...")
                        retries -= 1
                        time.sleep(2)
                if retries == 0:
                    print(f"Failed to publish {value} to {topic} after multiple attempts.")
                time.sleep(1)

    except Exception as e:
        print(f"Error during MQTT publishing: {e}")

    finally:
        client.disconnect()
        print("Disconnected from MQTT broker.")

# -----------------------------
# Main Execution
# -----------------------------
try:
    print("Process started.")
    download_csv_with_webdriver()
    csv_path = rename_and_move_csv_file()
    publish_to_mqtt(csv_path)
    print("Process completed successfully.")
    time.sleep(3)
except Exception as e:
    print(f"Fatal Error: {e}")