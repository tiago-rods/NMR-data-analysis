import os
from abc import ABC, abstractmethod
from dotenv import load_dotenv
from typing import Optional

try:
    from supabase import create_client, Client
except ImportError:
    print("Please install supabase: pip install supabase")
    Client = None


class FactorySeeder(ABC):
    """Abstract base class for all project seeders.

    Responsibilities:
    - Load ``.env`` configuration and create the Supabase client connection.
    - Define the ``seed()`` contract that every concrete seeder must implement.
    - Provide a default ``run()`` entry point that can be overridden for more
      complex orchestration logic (e.g. CLI menus, retry loops).

    Design Pattern: Factory Method — each subclass implements ``seed()`` with
    its own data-population strategy.
    """

    def __init__(self) -> None:
        """Loads environment variables and initialises the Supabase client."""
        load_dotenv()
        self.supabase: Optional["Client"] = self._connect()

    def _connect(self) -> Optional["Client"]:
        """Creates and returns the Supabase client from environment variables.

        Returns:
            Optional[Client]: An authenticated Supabase client.

        Raises:
            RuntimeError: If ``SUPABASE_URL`` or ``SUPABASE_KEY`` are missing,
                or if the ``supabase`` library is not installed.
        """
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL and SUPABASE_KEY must be defined in the .env file."
            )

        if Client is None:
            raise RuntimeError(
                "The supabase library is not installed. Run: pip install supabase"
            )

        return create_client(url, key)

    @abstractmethod
    def seed(self, *args, **kwargs) -> None:
        """Populates the database with data specific to this seeder.

        Must be implemented by every concrete subclass. Implementations should
        be idempotent (prefer upsert over plain insert) whenever possible.
        """
        ...

    def run(self) -> None:
        """Default entry point. Calls ``seed()`` directly.

        Override this method when additional orchestration logic is needed
        (e.g. CLI menus, conditional seeding, retry loops).
        """
        self.seed()
