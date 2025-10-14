import serial
import subprocess
import logging
from modem.interface import ModemInterface


class Serial:
    def __init__(self, modem: ModemInterface):
        self.modem = modem
        self.logger = logging.getLogger(self.__class__.__name__)
        self.serial_conn = None
        if self.serialAvailable():
            self.serial_conn = self.open_serial()
        else:
            self.serial_conn = None

    def serialAvailable(self) -> bool:
        try:
            output = subprocess.check_output(
                ["sudo", "lsof", self.modem.ATCommand], text=True
            )
            if output.strip():  # If there's any output, the port is in use
                self.logger.info(
                    f"Serial port {self.modem.ATCommand} is in use by the following processes:\n{output}"
                )
                return False
        except subprocess.CalledProcessError:
            self.logger.info(f"Serial port {self.modem.ATCommand} is not in use.")
        return True

    def open_serial(self) -> serial.Serial:
        self.logger.debug(
            f"Opening serial with: port={self.modem.ATCommand}, baudrate={self.modem.baudrate}, timeout={self.modem.timeout}"
        )
        try:
            serial_conn = serial.Serial(
                port=self.modem.ATCommand,
                baudrate=self.modem.baudrate,
                timeout=self.modem.timeout,
            )
            self.logger.info(f"Opened serial port {serial_conn.port} successfully.")
            return serial_conn
        except serial.SerialException as e:
            self.logger.error(f"Could not open serial port: {e}")
            return None

    def close_serial(self):
        """Close the serial connection."""
        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
            self.logger.info("Serial connection closed.")

    def __del__(self):
        """Destructor: ensure the serial port is closed on object deletion."""
        self.close_serial()
