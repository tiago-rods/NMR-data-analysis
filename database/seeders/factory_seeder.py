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
    """
    Classe base abstrata para todos os seeders do projeto.

    Responsabilidades:
    - Gerenciar o carregamento do .env e a conexão com o Supabase.
    - Definir o contrato `seed()` que todo seeder concreto deve implementar.
    - Oferecer um `run()` padrão que pode ser sobrescrito para lógicas de
      orquestração mais complexas (ex: menus CLI, loops, etc.).

    Design Pattern: Factory Method — cada subclasse implementa `seed()` com
    sua própria estratégia de população de dados.
    """

    def __init__(self):
        load_dotenv()
        self.supabase: Optional["Client"] = self._connect()

    def _connect(self) -> Optional["Client"]:
        """Cria e retorna o cliente Supabase a partir das variáveis de ambiente."""
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")

        if not url or not key:
            raise RuntimeError(
                "SUPABASE_URL e SUPABASE_KEY devem estar definidos no .env"
            )

        if Client is None:
            raise RuntimeError(
                "Biblioteca supabase não instalada. Execute: pip install supabase"
            )

        return create_client(url, key)

    @abstractmethod
    def seed(self, *args, **kwargs) -> None:
        """
        Implementar em cada seeder concreto com a lógica de população.
        Deve ser idempotente (upsert) sempre que possível.
        """
        ...

    def run(self) -> None:
        """
        Ponto de entrada padrão. Chama seed() diretamente.
        Sobrescrever quando for necessária lógica adicional (ex: menus CLI).
        """
        self.seed()
