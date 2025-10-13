#!/usr/bin/env python3

import logging
from modem.card import SIM
from modem.interface import ModemInterface
from serial import Serial
from modem.at import AT

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Modem:
    def __init__(self, sim, modem):
        self.timeout = 1
        self.sim: SIM = sim
        self.modem: ModemInterface = modem
        self.serial = Serial(modem)
        self.at = AT(self.serial.serial_conn)

    def connect(self):
        self.modem.connect()

    def send_sms(self, phoneNumber, text):
        self.at.send_sms(phoneNumber, text)

    def receive_sms(self):
        raise NotImplementedError("Receive Sms is not yet implemented.")

    def get_gps_coordinates(self):
        """
        Prototype method to get GPS coordinates from the modem.
        Should return a tuple (latitude, longitude).
        """
        raise NotImplementedError("GPS coordinate retrieval is not yet implemented.")


if __name__ == "__main__":
    sim = SIM(
        phone_number="+491606128400",
        pin="0955",
        puk="91904144",
        apn="o2.de",
    )

    rm520_modem = ModemInterface(
        qmi="/dev/cdc-wdm0",
        ttyUSB1="/dev/ttyUSB1",
        ATCommand="/dev/ttyUSB2",
        ttyUSB3="/dev/ttyUSB3",
        ttyUSB4="/dev/ttyUSB4",
        apn=sim.apn,
    )

    modem = Modem(sim, rm520_modem)
    modem.connect()
    modem.send_sms(
        phone="+491606128400", text="Hallo, this is a test SMS sent from Modem class."
    )
