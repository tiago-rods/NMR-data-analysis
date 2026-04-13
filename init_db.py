import sys
import os

# Adiciona o diretório atual ao path para garantir que pacotes locais sejam importados corretamente
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from database.db_manager import DataBaseManager
from database.migration_runner import MigrationRunner
from database.seeder import DatabaseSeeder

def main():
    print("Iniciando processo de configuração do Banco de Dados...")
    
    # 1. Conecta ao banco de dados usando as credenciais do .env
    db = DataBaseManager()
    
    # Verifica se a conexão foi bem-sucedida (o método connect_supabase já trata erros e devolve a conexão)
    if not db.conn:
        print("ERRO CRÍTICO: Não foi possível conectar ao banco de dados.")
        print("Verifique seu .env ou sua conexão com a rede (porta 5432).")
        sys.exit(1)
        
    print("Conexão ao banco estabelecida com sucesso!")

    # 2. Executa as Migrations Estruturais (Criação de Tabelas)
    runner = MigrationRunner(db.conn)
    runner.run_migrations()

    # 3. Executa o Seeder (Inserção de Dados Iniciais)
    seeder = DatabaseSeeder(db.conn)
    seeder.run_seeders()
    
    print("\nInicialização do Banco de Dados concluída com sucesso!")
    
    # Fecha a conexão para não deixar processos pendurados
    db.conn.close()

if __name__ == "__main__":
    main()
