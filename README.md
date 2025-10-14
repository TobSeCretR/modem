# 5G Modem Interface for Raspberry Pi 5 (Quectel RM520N-GL)

This open-source Python project provides a lightweight and practical solution for interfacing with a **5G modem**—specifically the **Quectel RM520N-GL**—on a **Raspberry Pi 5** running **Ubuntu 24.04.3 LTS**. It enables 5G/LTE internet connectivity, GPS access, and SMS messaging using **AT commands** or Python-based scripts.

Ideal for IoT, embedded Linux, or mobile networking projects.

---

## Supported Hardware

- **Modem:** Quectel RM520N-GL  
- **Revision:** RM520NGLAAR03A03M4G  
- **Platform:** Raspberry Pi 5  
- **Operating System:** Ubuntu 24.04.3 LTS

---

## Overview

This software enables full communication and control of the **Quectel RM520N-GL 5G modem** via **AT commands** or other serial interfaces. It's tailored for **Raspberry Pi 5** setups but can be adapted to other Linux SBCs or embedded systems.

---

Common use cases include:
- Enabling cellular internet access (5G/LTE)
- Sending/receiving SMS
- Retrieving GPS coordinates
- Automating modem interaction via scripts

## Requirements

- Raspberry Pi 5
- Ubuntu 24.04.3 LTS installed
- Quectel RM520N-GL modem (Revision: RM520NGLAAR03A03M4G)
- Appropriate USB/serial connection to modem (e.g., `/dev/ttyUSB2`)

---

## Features
- Set up and manage 5G or LTE internet connections
- Send and receive SMS messages
- Access GPS (GNSS) data from the modem
- Seamless integration with Raspberry Pi environment
- Use AT commands or automate via Python

---

## Technologies
- Python 3
- PySerial (or other serial tools)
- AT Command Protocol
- 5G, LTE, GPS (GNSS)
- Linux (Ubuntu 24.04.3)

---

## Usage
1. Connect the modem to the Raspberry Pi.
2. Identify the device path (e.g., `/dev/ttyUSB2`).
3. Use serial communication tools (like `minicom`) to send AT commands:

   ```bash
   sudo minicom -D /dev/ttyUSB2
   
### Basic Modem & SIM Status Commands
1. AT - Checks if the modem is responsive. The modem should reply with OK.
2. ATI - Requests information about the modem such as manufacturer, model, and firmware version.
3. AT+CPIN? - Checks the SIM card PIN status. If the SIM requires a PIN, the response will indicate this.
4. AT+CSQ - Returns the signal quality (RSSI) as a numeric value. Higher values generally mean better signal.
5. AT+CREG? - Checks the network registration status. Response indicates if the modem is registered on the cellular network.
6. AT+COPS? -Displays the current operator selection and registration status.

### SIM PIN Management
1. AT+CPIN="1234" - Enters the SIM PIN code to unlock the SIM. Replace "1234" with your actual SIM PIN.
2. AT+CLCK="SC",0,"1234" - Disables SIM PIN lock. Replace "1234" with your SIM PIN.
3. AT+CLCK="SC",1,"1234" - Enables SIM PIN lock.

### Write Custom Script
```python
#!/usr/bin/env python3

import gc
from modem.interface import ModemInterface
from modem.card import SIM
from modem.modem import Modem

rm520_modem = ModemInterface(
    qmi="/dev/cdc-wdm0",
    ttyUSB1="/dev/ttyUSB1",
    ATCommand="/dev/ttyUSB2",
    ttyUSB3="/dev/ttyUSB3",
    ttyUSB4="/dev/ttyUSB4",
    sim=SIM(
        phone_number="+49160xxxxx",
        pin="xxxx",
        puk="xxxx",
        apn="o2.de",
    ),
)

modem = Modem(rm520_modem)
modem.connect()
gc.collect()
```

## Coming Functionality
Planned features for future releases:
- IoT Integration
Support for sending sensor or device data over cellular networks to cloud platforms (e.g., MQTT, HTTP, or CoAP support).
- Enhanced GPS (GNSS)
More robust GPS handling including periodic location tracking, NMEA sentence parsing, and integration with mapping APIs.
- FTP Support
Enable file uploads/downloads over FTP directly via the modem for lightweight remote data transfer.
- TCP/UDP Socket Communication
Create raw TCP or UDP socket connections via the modem, enabling advanced use cases like remote device control or telemetry.