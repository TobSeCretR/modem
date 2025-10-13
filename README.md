# 5g-modem

This project is designed to interface with a 5G modem on a Raspberry Pi 5 running Ubuntu 24.04.3 LTS.

## Supported Hardware

- **Modem:** Quectel RM520N-GL  
- **Revision:** RM520NGLAAR03A03M4G

## Overview

This software facilitates communication and control of the Quectel RM520N-GL 5G modem using AT commands or other interfaces on a Raspberry Pi 5 with Ubuntu 24.04.3 LTS.

## Requirements

- Raspberry Pi 5
- Ubuntu 24.04.3 LTS installed
- Quectel RM520N-GL modem (Revision: RM520NGLAAR03A03M4G)
- Appropriate USB/serial connection to modem (e.g., `/dev/ttyUSB2`)

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

### Write custom script
```python
#!/usr/bin/env python3

from modem.interface import ModemInterface
from modem.card import SIM
from modem.modem import Modem

sim = SIM(
    phone_number="+49160xxx",
    pin="xxxx",
    puk="xxxx",
    apn="o2.de",
)

rm520_modem = ModemInterface(
    wwan0="/dev/cdc-wdm0",
    ttyUSB1="/dev/ttyUSB1",
    ATCommand="/dev/ttyUSB2",
    ttyUSB3="/dev/ttyUSB3",
    ttyUSB4="/dev/ttyUSB4",
)

modem = Modem(sim, rm520_modem)
modem.connect()
```



