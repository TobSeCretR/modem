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

    def reset_modem(self):
        logging.info("Resetting the modem...")
        output = self.run_command(
            cmd=f"sudo qmicli -d {self.qmi} --dms-set-operating-mode=reset"
        )
        if "error" in output.lower():
            logging.warning("Failed to reset modem.")
        else:
            logging.info("Modem reset command issued successfully.")

        time.sleep(5)  # Allow time for the modem to reboot

    def get_operating_mode(self):
        output = self.run_command(
            cmd=f"sudo qmicli -d {self.qmi} --dms-get-operating-mode"
        )
        if "offline" in output.lower():
            logging.info("Modem is offline. Switching to online mode...")
            self.run_command(
                cmd=f"sudo qmicli -d {self.qmi} --dms-set-operating-mode=online"
            )
            time.sleep(2)  # Give it a moment to come online
        else:
            logging.info("Modem is already online.")

    def check_sim_status(self):
        output = self.run_command(
            cmd=f"sudo qmicli -d {self.qmi} --uim-get-card-status"
        )
        if "PIN1 state: 'enabled, not verified'" in output:
            logging.info("SIM requires PIN. Sending PIN...")
            self.run_command(
                cmd=f"sudo qmicli -d {self.qmi} --uim-verify-pin=PIN1,{self.sim.pin1}"
            )
            time.sleep(2)
        elif (
            "PIN1 state: 'disabled'" in output or "Application state: 'ready'" in output
        ):
            logging.info("SIM is ready.")
        else:
            logging.warning("Unexpected SIM status. Proceeding cautiously.")

    def check_registration(self) -> bool:
        output = self.run_command(
            cmd=f"sudo qmicli -d {self.qmi} --nas-get-serving-system"
        )
        time.sleep(2)
        if "registration state: 'registered'" in output.lower():
            logging.info("Modem is registered to network.")
            return True
        else:
            logging.info("Modem not registered. Retrying...")
            for i in range(3):
                time.sleep(3)
                output = self.run_command(
                    cmd=f"sudo qmicli -d {self.qmi} --nas-get-serving-system"
                )
                if "registration state: 'registered'" in output.lower():
                    logging.info("Modem is now registered.")
                    return True
            logging.warning("Modem failed to register after retries.")
            return False

    def start_network(self):
        output = self.run_command(
            cmd=f"sudo qmicli -d {self.qmi} --wds-start-network=\"apn={self.sim.apn},ip-type='4,6'\" --client-no-release-cid"
        )
        if (
            "network started" in output.lower()
            and "packet data handle" in output.lower()
        ):
            logging.info("Network session started.")
            return True
        else:
            logging.error("Failed to start network session.")
            return True

    def get_connection_info(self):
        output = self.run_command(
            cmd=f"sudo qmicli -d {self.qmi} --wds-get-current-settings"
        )
        logging.info("Connection info retrieved:\n" + output)

    def connect(self) -> bool:
        output = self.run_command(
            cmd=f"sudo qmicli -d {self.qmi} --wds-get-current-settings"
        )
        logging.info("Connection settings:\n" + output)

    def set_raw_ip_mode(self):
        raw_ip_path = f"/sys/class/net/{self.interface}/qmi/raw_ip"
        if Path(raw_ip_path).exists():
            logging.info(f"Enabling raw-ip mode on {self.interface}...")
            try:
                with open(raw_ip_path, "w") as f:
                    f.write("Y\n")
            except PermissionError:
                logging.error(
                    "Permission denied while setting raw-ip mode. Are you root?"
                )
                sys.exit(1)
        else:
            logging.warning(
                f"Raw IP sysfs path does not exist: {raw_ip_path}. Skipping."
            )

    def configure_interface(self):
        logging.info(f"Setting raw-ip mode for {self.interface}...")
        self.set_raw_ip_mode()

        logging.info(f"Bringing up interface {self.interface}...")
        self.run_command(cmd=f"sudo ip link set {self.interface} up")

        logging.info(f"Requesting IP address via DHCP on {self.interface}...")
        self.run_command(cmd=f"sudo udhcpc -i {self.interface}")

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

###to do
# phone call

# 	send_at('ATD'+phone_number+';','OK',1)
# 	time.sleep(20)
# 	ser.write('AT+CHUP\r\n'.encode())

# def SendShortMessage(phone_number,text_message):
	
# 	print("Setting SMS mode...")
# 	send_at("AT+CMGF=1","OK",1)
# 	print("Sending Short Message")
# 	answer = send_at("AT+CMGS=\""+phone_number+"\"",">",2)
# 	if 1 == answer:
# 		ser.write(text_message.encode())
# 		ser.write(b'\x1A')
# 		answer = send_at('','OK',20)
# 		if 1 == answer:
# 			print('send successfully')
# 		else:
# 			print('error')
# 	else:
# 		print('error%d'%answer)

# def ReceiveShortMessage():
# 	rec_buff = ''
# 	print('Setting SMS mode...')
# 	send_at('AT+CMGF=1','OK',1)
# 	send_at('AT+CPMS=\"SM\",\"SM\",\"SM\"', 'OK', 1)
# 	answer = send_at('AT+CMGR=1','+CMGR:',2)
# 	if 1 == answer:
# 		answer = 0
# 		if 'OK' in rec_buff:
# 			answer = 1
# 			print(rec_buff)
# 	else:
# 		print('error%d'%answer)
# 		return False
# 	return True


##iot tcp connection
# rec_buff = ''
# APN = 'CMNET'
# ServerIP = '118.190.93.84'
# Port = '2317'
# Message = 'Waveshare'



# try:
# 	power_on(power_key)
# 	send_at('AT+CSQ','OK',1)
# 	send_at('AT+CREG?','+CREG: 0,1',1)
# 	send_at('AT+CPSI?','OK',1)
# 	send_at('AT+CGREG?','+CGREG: 0,1',0.5)
# 	send_at('AT+CGSOCKCONT=1,\"IP\",\"'+APN+'\"','OK',1)
# 	send_at('AT+CSOCKSETPN=1', 'OK', 1)
# 	send_at('AT+CIPMODE=0', 'OK', 1)
# 	send_at('AT+NETOPEN', '+NETOPEN: 0',5)
# 	send_at('AT+IPADDR', '+IPADDR:', 1)
# 	send_at('AT+CIPOPEN=0,\"TCP\",\"'+ServerIP+'\",'+Port,'+CIPOPEN: 0,0', 5)
# 	send_at('AT+CIPSEND=0,', '>', 2)#If not sure the message number,write the command like this: AT+CIPSEND=0, (end with 1A(hex))
# 	ser.write(Message.encode())
# 	if 1 == send_at(b'\x1a'.decode(),'OK',5):
# 		print('send message successfully!')
# 	send_at('AT+CIPCLOSE=0','+CIPCLOSE: 0,0',15)
# 	send_at('AT+NETCLOSE', '+NETCLOSE: 0', 1)
# 	power_down(power_key)
