#!/usr/bin/env python3

import logging
import os
import time
from datetime import datetime
from modem.card import SIM
from modem.interface import ModemInterface
from modem.serial import Serial
from modem.at import AT

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Modem:
    def __init__(self, interface: ModemInterface):
        self.timeout = 1
        self.interface = interface
        self.serial = Serial(interface)
        self.at = AT(self.serial.serial_conn)
        self.sms_flag_file = "/tmp/sms_sent_once"

    def connect(self):
        self.interface.connect()

    def is_internet_up(self) -> bool:
        return self.interface.run_command(cmd=f"ping -c 2 8.8.8.8")

    def monitor_connection(self, check_interval=30):
        while True:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if not self.is_internet_up():
                if not self.has_sms_been_sent():
                    logging.warning(
                        f"{now}: Internet down. Restarting PPP and sending SMS."
                    )
                    #self.at.restart_ppp()
                    self.connect()
                    self.at.send_sms(
                        phoneNumber=self.interface.sim.phone_number,
                        text=f"PPP restarted at {now}",
                    )
                    self.mark_sms_sent()
                else:
                    logging.info(f"{now}: Internet down. SMS already sent. Skipping.")
            else:
                if self.has_sms_been_sent():
                    self.clear_sms_sent_flag()
                    logging.info(f"{now}: Internet back. SMS flag cleared.")
                else:
                    logging.debug(f"{now}: Internet up and running.")
            time.sleep(check_interval)

    def send_sms(self, phoneNumber, text):
        self.at.send_sms(phoneNumber=phoneNumber, text=text)

    def receive_sms(self):
        raise NotImplementedError("Receive Sms is not yet implemented.")

    def has_sms_been_sent(self):
        return os.path.exists(self.sms_flag_file)

    def mark_sms_sent(self):
        open(self.sms_flag_file, "a").close()

    def clear_sms_sent_flag(self):
        if os.path.exists(self.sms_flag_file):
            os.remove(self.sms_flag_file)

    def get_gps_coordinates(self):
        """
        Prototype method to get GPS coordinates from the modem.
        Should return a tuple (latitude, longitude).
        """
        raise NotImplementedError("GPS coordinate retrieval is not yet implemented.")


if __name__ == "__main__":
    rm520_modem = ModemInterface(
        qmi="/dev/cdc-wdm0",
        ttyUSB1="/dev/ttyUSB1",
        ATCommand="/dev/ttyUSB2",
        ttyUSB3="/dev/ttyUSB3",
        ttyUSB4="/dev/ttyUSB4",
        sim=SIM(
            phone_number="+491606128400",
            pin="0955",
            puk="91904144",
            apn="o2.de",
        ),
    )

    modem = Modem(rm520_modem)
    #modem.connect()
    modem.send_sms(phoneNumber=rm520_modem.sim.phone_number, text="wichtige Information")