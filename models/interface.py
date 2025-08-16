import pandas as pd
from abc import ABC, abstractmethod


class SqlDatabaseAdapter(ABC):

    @abstractmethod
    def create_table(self, file: str, table_name: str):
        """Cria uma tabela no banco de dados a partir de um arquivo CSV."""
        pass

    @abstractmethod
    def select_query(self, query: str) -> pd.DataFrame:
        """Executa uma consulta SQL e retorna o resultado como um DataFrame."""
        pass