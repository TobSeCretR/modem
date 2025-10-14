import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class GPSInfo:
    def __init__(
        self,
        fix_status=None,
        latitude=None,
        longitude=None,
        altitude=None,
        speed=None,
        timestamp=None,
        raw=None,
    ):
        self.fix_status = fix_status
        self.latitude = latitude
        self.longitude = longitude
        self.altitude = altitude
        self.speed = speed
        self.timestamp = timestamp
        self.raw = raw

    def has_fix(self):
        """Check if GPS has a fix (fix_status == '1')"""
        return self.fix_status == "1"

    @classmethod
    def from_cgnsinf(cls, response):
        """
        Parse response from AT+CGNSINF and return GPSInfo instance.
        Example response:
        +CGNSINF: 1,1,20251014125633.000,37.7749,-122.4194,10.0,0.0,...
        """
        try:
            if "+CGNSINF:" not in response:
                raise ValueError("Invalid CGNSINF response.")

            parts = response.split(":")[1].strip().split(",")
            return cls(
                fix_status=parts[1],
                timestamp=parts[2],
                latitude=parts[3],
                longitude=parts[4],
                altitude=parts[5],
                speed=parts[6],
                raw=response.strip(),
            )
        except Exception as e:
            logger.error(f"Failed to parse CGNSINF: {e}")
            return cls(raw=response.strip())

    def __str__(self):
        return (
            f"GPS Fix: {self.fix_status}, "
            f"Timestamp: {self.timestamp}, "
            f"Latitude: {self.latitude}, Longitude: {self.longitude}, "
            f"Altitude: {self.altitude} m, Speed: {self.speed} km/h"
        )