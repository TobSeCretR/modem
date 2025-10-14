from pathlib import Path
import subprocess
import time
import logging
import os
import sys
from modem.card import SIM

class ModemInterface:
    def __init__(
        self,
        qmi: str,
        ttyUSB1: str,
        ATCommand: str,
        ttyUSB3: str,
        ttyUSB4: str,
        sim: SIM,
        baudrate: int = 115200,
        timeout: int = 5,
        interface: str = "wwan0",
    ):
        self.qmi = qmi
        self.ttyUSB1 = ttyUSB1
        self.ATCommand = ATCommand
        self.ttyUSB3 = ttyUSB3
        self.ttyUSB4 = ttyUSB4
        self.sim = sim
        self.baudrate = baudrate
        self.timeout = timeout
        self.interface = interface
        self.check_sudo()

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
    
    def check_sudo(self):
        if os.geteuid() != 0:
            logging.error("This script must be run with sudo/root privileges.")
            sys.exit(1)
        else:
            logging.info("Running as root.")

    def run_command(self, cmd):
        logging.info(f"Running: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.stdout:
            logging.info(f"Output: {result.stdout.strip()}")
        if result.stderr:
            logging.warning(f"Error: {result.stderr.strip()}")
        return result.stdout or ""

    def get_operating_mode(self):
        output = self.run_command(cmd = f"sudo qmicli -d {self.qmi} --dms-get-operating-mode")
        if "offline" in output.lower():
            logging.info("Modem is offline. Switching to online mode...")
            self.run_command(cmd = f"sudo qmicli -d {self.qmi} --dms-set-operating-mode=online")
            time.sleep(2)  # Give it a moment to come online
        else:
            logging.info("Modem is already online.")

    def check_sim_status(self):
        output = self.run_command(cmd = f"sudo qmicli -d {self.qmi} --uim-get-card-status")
        if "PIN1 state: 'enabled, not verified'" in output:
            logging.info("SIM requires PIN. Sending PIN...")
            self.run_command(cmd = f"sudo qmicli -d {self.qmi} --uim-verify-pin=PIN1,{self.sim.pin}")
            time.sleep(2)
        elif "PIN1 state: 'disabled'" in output or "Application state: 'ready'" in output:
            logging.info("SIM is ready.")
        else:
            logging.warning("Unexpected SIM status. Proceeding cautiously.")

    def check_registration(self) -> bool:
        output = self.run_command(cmd = f"sudo qmicli -d {self.qmi} --nas-get-serving-system")
        time.sleep(2)
        if "registration state: 'registered'" in output.lower():
            logging.info("Modem is registered to network.")
            return True
        else:
            logging.info("Modem not registered. Retrying...")
            for i in range(3):
                time.sleep(3)
                output = self.run_command(cmd = f"sudo qmicli -d {self.qmi} --nas-get-serving-system")
                if "registration state: 'registered'" in output.lower():
                    logging.info("Modem is now registered.")
                    return True
            logging.warning("Modem failed to register after retries.")
            return False

    def start_network(self):
        output = self.run_command(cmd = f"sudo qmicli -d {self.qmi} --wds-start-network=apn={self.sim.apn} --client-no-release-cid")
        if "network started" in output.lower() and "packet data handle" in output.lower():
            logging.info("Network session started.")
            return True
        else:
            logging.error("Failed to start network session.")
            return True

    def get_connection_info(self):
        output = self.run_command(cmd=f"sudo qmicli -d {self.qmi} --wds-get-current-settings")
        logging.info("Connection info retrieved:\n" + output)

    def connect(self) -> bool:
        output =  self.run_command(cmd = f"sudo qmicli -d {self.qmi} --wds-get-current-settings")
        logging.info("Connection settings:\n" + output)

    def set_raw_ip_mode(self):
        raw_ip_path = f"/sys/class/net/{self.interface}/qmi/raw_ip"
        if Path(raw_ip_path).exists():
            logging.info(f"Enabling raw-ip mode on {self.interface}...")
            try:
                with open(raw_ip_path, "w") as f:
                    f.write("Y\n")
            except PermissionError:
                logging.error("Permission denied while setting raw-ip mode. Are you root?")
                sys.exit(1)
        else:
            logging.warning(f"Raw IP sysfs path does not exist: {raw_ip_path}. Skipping.")
    
    def configure_interface(self):
        logging.info(f"Setting raw-ip mode for {self.interface}...")
        self.set_raw_ip_mode()

        logging.info(f"Bringing up interface {self.interface}...")
        self.run_command(cmd = f"sudo ip link set {self.interface} up")

        logging.info(f"Requesting IP address via DHCP on {self.interface}...")
        self.run_command(cmd = f"sudo udhcpc -i {self.interface}")

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
