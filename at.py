import time
import serial
import logging

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class AT:
    def __init__(self,  connection):
        self.serial: serial.Serial = connection
            
    def send_cmd(self, cmd, wait=1):
        """Send an AT command to the modem and return the response."""
        full_cmd = cmd + '\r'
        self.serial.write(full_cmd.encode())
        time.sleep(wait)
        response = self.serial.read_all().decode(errors="ignore")
        logger.info(f"--- {cmd} response ---\n{response.strip()}\n----------------------")
        return response
    
    def send_sms(self, phoneNumber, text):
        if not self.serial:
            logger.error("Serial port not available. SMS not sent.")
            return
        try:
            self.serial.open()
            self.send_cmd("AT")
            self.send_cmd("AT+CMGF=1")                          # Set text mode
            self.send_cmd('AT+CSCS="GSM"')                      # Set character set to GSM
            self.send_cmd(f'AT+CMGS="{phoneNumber}"')
            time.sleep(1)
            self.serial.write((text + "\x1A").encode())         # Send message + Ctrl+Z
            logger.info("Waiting for modem to send SMS...")
            time.sleep(5)                                       # Wait for message to send
            response = self.serial.read_all().decode(errors="ignore")
            logger.info(f"--- Final response ---\n{response.strip()}\n----------------------")
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            self.serial.close()
