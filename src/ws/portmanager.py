import random
import time
from datetime import datetime, timedelta

class PortManager:
    def __init__(self, port: int, timestamp: int):
        self.port = port
        self.timestamp = timestamp
        self.expiration_time = self._calculate_expiration_time()

    def _calculate_expiration_time(self) -> datetime:
        """Calculate a random expiration time between 6 to 7 days after the timestamp."""
        min_days = 6
        max_days = 7
        random_minutes = random.randint(min_days * 24 * 60, max_days * 24 * 60)
        return datetime.fromtimestamp(self.timestamp) + timedelta(minutes=random_minutes)

    def get_port(self) -> int:
        """Return the port."""
        return self.port

    def is_expired(self) -> bool:
        """Check if the port is expired."""
        return datetime.now() > self.expiration_time

    def serialize_to_env(self, file_path: str) -> None:
        """Serialize the port and timestamp to a .env file."""
        try:
            with open(file_path, 'w') as file:
                file.write(f"WS_LAST_PORT={self.port}\n")
                file.write(f"WS_LAST_TIMESTAMP={self.timestamp}\n")
                file.write(f"WS_EXPIRATION={int(self.expiration_time.timestamp())}\n")
        except IOError as e:
            print(f"Error writing to file {file_path}: {e}")

    @classmethod
    def deserialize_from_env(cls, file_path: str) -> "PortManager":
        """Deserialize the port and timestamp from a .env file."""
        try:
            with open(file_path, 'r') as file:
                data = file.readlines()
                port = int(data[0].strip().split('=')[1])
                timestamp = int(data[1].strip().split('=')[1])
                expiration_time = int(data[2].strip().split('=')[1])
            
            instance = cls(port, timestamp)
            instance.expiration_time = datetime.fromtimestamp(expiration_time)
            return instance
        except (IOError, IndexError, ValueError) as e:
            print(f"Error reading from file {file_path}: {e}")
            return None