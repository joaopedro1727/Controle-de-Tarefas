# TaskFlow - Gerenciador de Tarefas

Um sistema desktop completo para gerenciamento e controle de tarefas desenvolvido em Python, utilizando a biblioteca Tkinter para a interface gráfica no estilo Dark Mode, SQLite3 para a persistência de dados e JSON para manipulacão de dados.

## Funcionalidades

* Dashboard Integrado: Exibição do total de tarefas, tarefas pendentes, em andamento, concluídas e vencidas, além de uma barra com a porcentagem total de progresso.


* Gestão Completa de Tarefas (CRUD): Cadastro de tarefas com nome, descrição, categoria, prioridade, data de entrega, tags e nível de progresso; edição e edição rápida para marcar tarefas como concluídas; exclusão individual e opção para limpar todo o banco de dados.


* Filtros e Busca: Busca em tempo real por nome, descrição ou tags; filtro combinável por status, categoria e prioridade.


* Alertas de Prazos: Identificação de tarefas vencidas, que vencem no dia ou no dia seguinte diretamente na listagem.


* Exportação: Opção para gerar relatórios completos das tarefas registradas em formato TXT.



## Tecnologias Utilizadas

* Linguagem: Python 3


* Interface Gráfica: Tkinter / ttk (Tema customizado Deep Ocean)


* Banco de Dados: SQLite3


* Manipulação de Dados: JSON



## Estrutura do Projeto

* tarefas.py: Código-fonte principal da aplicação contendo a interface e as regras de negócio.


* tarefas.db: Banco de dados SQLite criado automaticamente na primeira execução do sistema.


* relatorio_tarefas.txt: Arquivo gerado ao exportar o relatório das tarefas.


* README.md: Documentação oficial do projeto.



## Como Executar o Projeto

### Pré-requisitos

É necessário ter o Python 3.x instalado em sua máquina. Não há necessidade de instalar bibliotecas de terceiros pelo pip, pois a interface utiliza módulos nativos da linguagem (tkinter, sqlite3 e json).

### 1. Clonar o repositório

git clone [https://github.com/seu-usuario/seu-repositorio.git](https://github.com/seu-usuario/seu-repositorio.git)
cd seu-repositorio

### 2. Executar a aplicação

python tarefas.py

## Autor

Desenvolvido por João Pedro.