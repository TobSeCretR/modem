class SIM:
    def __init__(self, phone_number, pin, puk, apn):
        self.phone_number = phone_number
        self.pin = pin
        self.puk = puk
        self.apn = apn

    def __str__(self):
        return (f"SIMCard(phone_number={self.phone_number}, "
                f"PIN={'*' * len(self.pin)}, "
                f"PUK={'*' * len(self.puk)}, "
                f"APN={self.apn})")

    def unlock(self, pin):
        if pin == self.pin:
            return "SIM unlocked successfully."
        else:
            return "Invalid PIN."

    def reset_pin(self, puk, new_pin):
        if puk == self.puk:
            self.pin = new_pin
            return "PIN reset successfully."
        else:
            return "Invalid PUK. Cannot reset PIN."

