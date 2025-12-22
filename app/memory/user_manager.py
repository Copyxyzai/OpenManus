import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional


class UserManager:
    """
    Manages user identification and profile storage.
    """

    def __init__(self, base_path: str = "workspace/memory/users"):
        self.base_path = base_path
        self._ensure_base_directory()

    def _ensure_base_directory(self):
        """Ensure base users directory exists."""
        os.makedirs(self.base_path, exist_ok=True)

    def get_current_user_id(self) -> str:
        """Get current user ID from environment or default."""
        return os.getenv("MANUS_USER_ID", "default")

    def get_user_directory(self, user_id: str) -> str:
        """Get user's directory path."""
        return os.path.join(self.base_path, user_id)

    def get_or_create_user(self, user_id: str) -> Dict:
        """
        Get existing user profile or create a new one.

        Args:
            user_id: User identifier

        Returns:
            User profile dict
        """
        user_dir = self.get_user_directory(user_id)
        profile_path = os.path.join(user_dir, "profile.json")

        # Create user directory if it doesn't exist
        os.makedirs(user_dir, exist_ok=True)

        # Load or create profile
        if os.path.exists(profile_path):
            with open(profile_path, "r", encoding="utf-8") as f:
                return json.load(f)
        else:
            # Create new profile
            profile = {
                "user_id": user_id,
                "created_at": datetime.now().isoformat(),
                "preferences": {},
                "metadata": {},
            }
            self.save_user_profile(user_id, profile)
            return profile

    def save_user_profile(self, user_id: str, profile: Dict):
        """Save user profile to disk."""
        user_dir = self.get_user_directory(user_id)
        profile_path = os.path.join(user_dir, "profile.json")

        os.makedirs(user_dir, exist_ok=True)
        with open(profile_path, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)

    def update_preference(self, user_id: str, key: str, value: str):
        """Update a user preference."""
        profile = self.get_or_create_user(user_id)
        profile["preferences"][key] = value
        self.save_user_profile(user_id, profile)

    def get_preference(
        self, user_id: str, key: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Get a user preference."""
        profile = self.get_or_create_user(user_id)
        return profile["preferences"].get(key, default)
