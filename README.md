# NMR-data-analysis
**Projeto de Iniciação Científica** desenvolvido em conjunto com o LNBio,
**Documento Final**: ainda não disponível
**Objetivos:** 
- Desenvolver um software que padroniza dados de espectros RMN ¹H para um formato csv, pronto para ser testado em diversas ferramentas
- Receber dados de perfilamento metabolômico de diferentes ferramentas, salvá-los em um banco de dados modelado rodando localmente em postgreSQL
- Comparar desempenho de diferentes ferramentas de perfilamento metabolômico e salva-los em um banco de dados.

**Projeto ainda em andamento, ao final será disponibilizada a publicação e dados mais detalhados no readme**

transformation of NMR ¹H to a paternized data type and statistic review of diferent softwares of automated profiling

## O que foi feito até o momento

Até agora, o desenvolvimento focou em estruturar a base de dados e criar uma arquitetura robusta para o processamento de dados:

- **Arquitetura Modular (Pipeline de Dados):**
  - Implementação de um padrão de projeto dividindo as responsabilidades em etapas: **Readers** (leitura de arquivos), **Cleaners** (limpeza e filtragem de redundâncias), **Formatters** (padronização para o formato do projeto) e **Processors** (orquestração do fluxo).
  - Separação de lógicas específicas para diferentes origens de dados (ASICS, MagMet e nmRanalysis).

- **Processamento e Padronização:**
  - Criação de scripts em Python para ingestão programática de arquivos CSV e espectros.

- **Banco de Dados:**
  - Configuração de um banco de dados **PostgreSQL** rodando localmente.
  - Criação de scripts em Python (`init_database.py`, `migrate_data.py`, `populate_database.py`) para gerenciar as tabelas e popular os dados.

- **Qualidade de Código:**
  - Refatoração contínua da base de código (ex: separação dos "Runners" de scripts na pasta `Scripts/`).
  - Adoção de princípios de design para manter a base de código limpa e escalável.
