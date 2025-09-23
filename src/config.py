import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass

class Config:
    """
    Configuration for the sync tool, loaded from a JSON file.
    """
    caldav_url: str
    caldav_username: str
    caldav_password: str
    outlook_calendar_name: str
    sync_interval_minutes: int = 15
    log_level: str = "INFO"
    sync_state_filepath: str = "specs/002-synchronise-outlook-work/sync_state.json"
    verify_ssl: bool = True
    pushbullet_api_key: Optional[str] = None

    @classmethod
    def load_from_file(cls, filepath: str = "config.json") -> 'Config':
        """
        Load configuration from a JSON file and validate required fields.
        Args:
            filepath: Path to the config JSON file
        Returns:
            Config instance
        Raises:
            FileNotFoundError, ValueError, RuntimeError
        """
        try:
            with open(filepath, 'r') as f:
                config_data = json.load(f)
            # Basic validation
            required_fields = ["caldav_url", "caldav_username", "caldav_password", "outlook_calendar_name"]
            for field_name in required_fields:
                if field_name not in config_data:
                    raise ValueError(f"Missing required configuration field: {field_name}")
            # Default verify_ssl to True if not present
            if "verify_ssl" not in config_data:
                config_data["verify_ssl"] = True
            # Default pushbullet_api_key to None if not present
            if "pushbullet_api_key" not in config_data:
                config_data["pushbullet_api_key"] = None
            return cls(**config_data)
        except FileNotFoundError:
            raise FileNotFoundError(f"Config file not found at {filepath}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in config file: {filepath}")
        except ValueError: # Catch specific ValueError and re-raise it
            raise
        except Exception as e:
            raise RuntimeError(f"Error loading configuration: {e}")

    def save_to_file(self, filepath: str = "config.json"):
        """
        Save the current configuration to a JSON file.
        Args:
            filepath: Path to save the config JSON file
        """
        with open(filepath, 'w') as f:
            json.dump(self.__dict__, f, indent=4)
