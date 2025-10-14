import time
import serial
import logging

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AT:
    def __init__(self, connection):
        self.serial: serial.Serial = connection

    def send_cmd(self, cmd, wait=1):
        """Send an AT command to the modem and return the response."""
        full_cmd = cmd + "\r"
        self.serial.write(full_cmd.encode())
        time.sleep(wait)
        response = self.serial.read_all().decode(errors="ignore")
        logger.info(
            f"--- {cmd} response ---\n{response.strip()}\n----------------------"
        )
        return response

    def send_sms(self, phoneNumber, text):
        if not self.serial:
            logger.error("Serial port not available. SMS not sent.")
            return
        try:
            self.serial.open()
            self.send_cmd("AT")
            self.send_cmd("AT+CMGF=1")  # Set text mode
            self.send_cmd('AT+CSCS="GSM"')  # Set character set to GSM
            self.send_cmd(f'AT+CMGS="{phoneNumber}"')
            time.sleep(1)
            self.serial.write((text + "\x1a").encode())  # Send message + Ctrl+Z
            logger.info("Waiting for modem to send SMS...")
            time.sleep(5)  # Wait for message to send
            response = self.serial.read_all().decode(errors="ignore")
            logger.info(
                f"--- Final response ---\n{response.strip()}\n----------------------"
            )
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            self.serial.close()

    def restart_ppp(self):
        """Restart the PPP modem by sending AT command via serial."""
        try:
            with serial.Serial(self.serial_device, baudrate=115200, timeout=1) as ser:
                ser.write(b"AT+CFUN=1,1\r")  # Restart the modem
                print(f"[INFO] Sent modem reset command via AT+CFUN.")
        except serial.SerialException as e:
            print(f"[ERROR] Failed to access serial device {self.serial_device}: {e}")
