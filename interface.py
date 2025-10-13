from pathlib import Path
import subprocess
import time
import logging


class ModemInterface:
    def __init__(
        self,
        qmi: str,
        ttyUSB1: str,
        ATCommand: str,
        ttyUSB3: str,
        ttyUSB4: str,
        apn: str,
        baudrate: int = 115200,
        timeout: int = 1,
        interface: str = "wwan0",
    ):
        self.qmi = qmi
        self.ttyUSB1 = ttyUSB1
        self.ATCommand = ATCommand
        self.ttyUSB3 = ttyUSB3
        self.ttyUSB4 = ttyUSB4
        self.apn = apn
        self.baudrate = baudrate
        self.timeout = timeout
        self.interface = interface

    def all_devices_exist(self) -> bool:
        return all(
            p.exists()
            for p in [
                self.interface,
                self.ttyUSB1,
                self.ATCommand,
                self.ttyUSB3,
                self.ttyUSB4,
            ]
        )

    def __repr__(self):
        return (
            f"ModemInterface(wwan0={self.interface}, ttyUSB1={self.ttyUSB1}, "
            f"ATCommand={self.ATCommand}, ttyUSB3={self.ttyUSB3}, "
            f"ttyUSB4={self.ttyUSB4}, baudrate={self.baudrate})"
        )

    def run_command(self, cmd):
        logging.info(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            logging.info(f"Output: {result.stdout.strip()}")
        if result.stderr:
            logging.warning(f"Error: {result.stderr.strip()}")
        return result.stdout or ""

    def get_operating_mode(self):
        output = self.run_command(
            ["qmicli", "-d", self.qmi, "--dms-get-operating-mode"]
        )
        if "offline" in output.lower():
            logging.info("Modem is offline. Switching to online mode...")
            self.run_command(
                ["qmicli", "-d", self.qmi, "--dms-set-operating-mode=online"]
            )
            time.sleep(2)  # Give it a moment to come online
        else:
            logging.info("Modem is already online.")

    def check_sim_status(self):
        output = self.run_command(["qmicli", "-d", self.qmi, "--uim-get-card-status"])
        if "PIN1 (enabled, not verified)" in output:
            logging.info("SIM requires PIN. Sending PIN...")
            self.run_command(
                ["qmicli", "-d", self.qmi, f"--uim-verify-pin=PIN1,{self.pin}"]
            )
            time.sleep(2)
        elif "PIN1 (disabled)" in output or "verified" in output:
            logging.info("SIM is ready.")
        else:
            logging.warning("Unexpected SIM status. Proceeding cautiously.")

    def check_registration(self) -> bool:
        output = self.run_command(
            ["qmicli", "-d", self.qmi, "--nas-get-registration-state"]
        )
        if "registration state: 'registered'" in output.lower():
            logging.info("Modem is registered to network.")
            return True
        else:
            logging.info("Modem not registered. Retrying...")
            for i in range(5):
                time.sleep(3)
                output = self.run_command(
                    ["qmicli", "-d", self.qmi, "--nas-get-registration-state"]
                )
                if "registration state: 'registered'" in output.lower():
                    logging.info("Modem is now registered.")
                    return True
            logging.warning("Modem failed to register after retries.")
            return False

    def start_network(self):
        output = self.run_command(
            [
                "qmicli",
                "-d",
                self.qmi,
                f"--wds-start-network=apn={self.apn}",
                "--client-no-release-cid",
            ]
        )
        if "successfully started network" in output.lower():
            logging.info("Network session started.")
        else:
            raise RuntimeError("Failed to start network session.")

    def connect(self) -> bool:
        output = self.run_command(
            ["qmicli", "-d", self.device, "--wds-get-current-settings"]
        )
        logging.info("Connection settings:\n" + output)

    def configure_interface(self):
        logging.info(f"Running DHCP client on {self.interface}...")
        self.run_command(["udhcpc", "-i", self.interface])

    def connect(self):
        logging.info("[STEP] Checking modem operating mode...")
        self.get_operating_mode()

        logging.info("[STEP] Checking SIM status...")
        self.check_sim_status()

        logging.info("[STEP] Checking network registration...")
        if not self.check_registration():
            logging.error(
                "Modem is not registered to the network. Aborting connection attempt."
            )
            return False

        logging.info("[STEP] Starting network session...")
        if not self.start_network():
            logging.error("Failed to start network session.")
            return False

        logging.info("[STEP] Getting session details...")
        self.get_connection_info()

        logging.info("[STEP] Configuring interface...")
        self.configure_interface()

        logging.info("[DONE] WWAN connection should now be up.")
        return True
