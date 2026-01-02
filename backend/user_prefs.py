import json
import os

class UserPreferences:
    def __init__(self, filepath="user_preferences.json"):
        self.filepath = filepath
        self.preferences = self._load_preferences()

    def _load_preferences(self):
        """Load preferences from JSON file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return self._default_preferences()
        else:
            return self._default_preferences()

    def _default_preferences(self):
        """Return default empty preferences."""
        return {
            "dislikes": [],
            "favorites": []
        }

    def save_preferences(self, dislikes, favorites):
        """Save new preferences to file."""
        self.preferences = {
            "dislikes": list(set(dislikes)), # Ensure unique
            "favorites": list(set(favorites))
        }
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.preferences, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Error saving preferences: {e}")
            return False

    def get_dislikes(self):
        return self.preferences.get("dislikes", [])

    def get_favorites(self):
        return self.preferences.get("favorites", [])
