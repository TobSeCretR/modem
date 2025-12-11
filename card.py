class SIM:
    def __init__(self, phone_number, pin1, pin2, puk1, puk2, apn):
        self.phone_number = phone_number
        self.pin1 = pin1
        self.pin2 = pin2
        self.puk1 = puk1
        self.puk1 = puk2
        self.apn = apn

    def __str__(self):
        return (
            f"SIMCard(phone_number={self.phone_number}, "
            f"PIN1={'*' * len(self.pin1)}, "
            f"PIN2={'*' * len(self.pin2)}, "
            f"PUK1={'*' * len(self.puk1)}, "
            f"PUK2={'*' * len(self.puk2)}, "
            f"APN={self.apn})"
        )

    def unlock(self, pin1):
        if pin1 == self.pin1:
            return "SIM unlocked successfully."
        else:
            return "Invalid PIN."

    def reset_pin(self, puk1, new_pin):
        if puk1 == self.puk1:
            self.pin1 = new_pin
            return "PIN reset successfully."
        else:
            return "Invalid PUK. Cannot reset PIN."
