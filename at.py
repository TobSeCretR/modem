import time
import serial
import logging
from modem.gps import GPSInfo

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class AT:
    def __init__(self, connection):
        self.connection = connection

    def send_cmd(self, cmd, wait=1):
        full_cmd = cmd + "\r"
        self.connection.write(full_cmd.encode())
        time.sleep(wait)
        response = self.connection.read_all().decode(errors="ignore")
        logger.info(
            f"--- {cmd} response ---\n{response.strip()}\n----------------------"
        )
        return response

    def send_sms(self, phoneNumber, text):
        if not self.connection:
            logger.error("Serial port not available. SMS not sent.")
            return
        try:
            self.send_cmd("AT")
            self.send_cmd("AT+CMGF=1")  # Set text mode
            self.send_cmd('AT+CSCS="GSM"')  # Set character set to GSM
            self.send_cmd(f'AT+CMGS="{phoneNumber}"')
            time.sleep(1)
            self.connection.write((text + "\x1a").encode())  # Send message + Ctrl+Z
            logger.info("Waiting for modem to send SMS...")
            time.sleep(5)  # Wait for message to send
            response = self.connection.read_all().decode(errors="ignore")
            logger.info(
                f"--- Final response ---\n{response.strip()}\n----------------------"
            )
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")


    def restart_ppp(self):
        try:
            self.connection.write("AT+CFUN=1,1\r".encode())
            logger.info("Waiting for modem to reboot...")
            time.sleep(20)  # Wait for message to send
            response = self.connection.read_all().decode(errors="ignore")
            logger.info(
                f"--- Final response ---\n{response.strip()}\n----------------------"
            )
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")
            
    def check_gps_power_status(self):
        if not self.connection:
            logger.error("Serial port not available. Cannot check GPS power status.")
            return None

        try:
            # Check GPS power status first
            gps_power_on = self.check_gps_power_status()

            if gps_power_on is False:
                self.send_cmd("AT+CGNSPWR=1")  # Power on GNSS
                time.sleep(2)
            elif gps_power_on is None:
                logger.warning("Could not determine GPS power status; attempting to power on GNSS anyway.")
                self.send_cmd("AT+CGNSPWR=1")
                time.sleep(2)
            else:
                logger.info("GPS already powered ON.")
            
            response = self.send_cmd("AT+CGPSPWR?")
            logger.info(f"GPS Power Status response: {response.strip()}")
            # Response format: +CGPSPWR: <status>
            # where <status> is 0 or 1
            if "+CGPSPWR:" in response:
                # Extract status number after the colon
                status_line = response.split(":")[1].strip()
                status = status_line.split()[0]  # Take the first token after colon
                if status == "1":
                    logger.info("GPS is ON.")
                    return True
                elif status == "0":
                    logger.info("GPS is OFF.")
                    return False
            logger.warning("Unexpected GPS power status response.")
            return None
        except Exception as e:
            logger.error(f"Error checking GPS power status: {e}")
            return None 
            
    def get_gps_info(self):
        if not self.connection:
            logger.error("Serial port not available. Cannot retrieve GPS info.")
            return None
    
        gps = GPSInfo(
            fix_status=None,
            latitude=None,
            longitude=None,
            altitude=None,
            speed=None,
            timestamp=None,
            raw=None
        )

        try:
            self.send_cmd("AT")
            self.send_cmd("AT+CGNSPWR=1")  # Power on GNSS
            time.sleep(2)
    
            response = self.send_cmd("AT+CGNSINF")  # Get GNSS info
            logger.info(f"--- Raw GPS response ---\n{response.strip()}\n----------------------")
    
            if "+CGNSINF:" in response:
                parts = response.split(":")[1].strip().split(",")
                gps["fix_status"] = parts[1]
                gps["timestamp"] = parts[2]
                gps["latitude"] = parts[3]
                gps["longitude"] = parts[4]
                gps["altitude"] = parts[5]
                gps["speed"] = parts[6]
                gps["raw"] = response.strip()
            else:
                logger.warning("GPS data not available or fix not acquired.")
            
            # Turn off GNSS after usage
            self.send_cmd("AT+CGNSPWR=0")

            return gps
    
        except Exception as e:
            logger.error(f"Error retrieving GPS information: {e}")
            return None
