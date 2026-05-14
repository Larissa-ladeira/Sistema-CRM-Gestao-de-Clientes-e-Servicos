CRM Freelancer - Trackt
Este é um sistema de CRM (Customer Relationship Management) desenvolvido especificamente para freelancers que precisam gerenciar clientes, serviços e o fluxo financeiro de forma centralizada e eficiente.

🚀 Tecnologias Utilizadas
O projeto utiliza uma arquitetura moderna com backend em Python e persistência de dados robusta:

Backend: FastAPI (Framework de alto desempenho)

Banco de Dados: PostgreSQL

Autenticação: JWT (JSON Web Tokens) com segurança via passlib e bcrypt

ORM/Driver: psycopg2 para comunicação direta com o banco

Variáveis de Ambiente: python-dotenv para segurança de chaves sensíveis

✨ Funcionalidades Principais
Gestão de Clientes: Cadastro, busca e listagem de clientes.

Gestão de Serviços: Registro de projetos, controle de prazos e status (Pendente, Em Produção, Finalizado).

Fluxo Financeiro: Registro de pagamentos vinculados a serviços com suporte a diferentes métodos.

Dashboard Inteligente: Resumo financeiro, contagem de serviços por status, clientes top e métodos de pagamento.

Segurança: Acesso protegido por autenticação e PIN de segurança para visualizar detalhes sensíveis dos clientes.

📦 Como Instalar e Rodar
Clone o repositório:

Bash
git clone https://github.com/seu-usuario/seu-repositorio.git
cd seu-repositorio
Instale as dependências:

Bash
pip install -r requirements.txt
Configuração de Ambiente:
Crie uma pasta chamada secrets na raiz do projeto e dentro dela um arquivo .env com as seguintes variáveis:

Snippet de código
DATABASE_URL="postgresql://usuario:senha@host:porta/banco"
SECRET_KEY="sua-chave-secreta"
ADMIN_USER="admin"
ADMIN_PASSWORD="sua-senha"
CLIENTE_VIEW_PIN="1234"
Popular o banco de dados (Opcional):
Utilize o script de seed para criar dados fictícios de teste:

Bash
python seed.py
Executar a aplicação:

Bash
uvicorn app:app --reload
🛠 Scripts Auxiliares
migrate_to_render.py: Script utilizado para migrar seus dados de um ambiente de desenvolvimento local para um banco de dados hospedado (ex: Render).

seed.py: Script de povoamento inicial do banco para testes.

📌 Notas de Desenvolvimento
O projeto possui um middleware de CORS configurado para aceitar requisições de qualquer origem (*).

O sistema de login utiliza OAuth2PasswordRequestForm padrão do FastAPI.

A migração de dados considera a integridade relacional entre clientes, servicos e financeiro.
