import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import random

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets", ".env"))

def get_db_connection():
    use_local = os.getenv("USE_LOCAL", "false").lower() == "true"
    if use_local:
        return psycopg2.connect(
            host="localhost",
            database="db_crm_freelancer",
            user="postgres",
            password="201397"
        )
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return psycopg2.connect(database_url)
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "db_crm_freelancer"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )

clientes_data = [
    {"nome": "Ana Beatriz Oliveira", "documento": "123.456.789-01", "whatsapp": "(11) 99999-1001", "email": "ana.oliveira@email.com"},
    {"nome": "Carlos Eduardo Santos", "documento": "234.567.890-12", "whatsapp": "(21) 98888-1002", "email": "carlos.santos@email.com"},
    {"nome": "Mariana Costa Lima", "documento": "345.678.901-23", "whatsapp": "(31) 97777-1003", "email": "mariana.lima@email.com"},
    {"nome": "Pedro Henrique Alves", "documento": "456.789.012-34", "whatsapp": "(41) 96666-1004", "email": "pedro.alves@email.com"},
    {"nome": "Juliana Ferreira Dias", "documento": "567.890.123-45", "whatsapp": "(51) 95555-1005", "email": "juliana.dias@email.com"},
    {"nome": "Lucas Gabriel Martins", "documento": "678.901.234-56", "whatsapp": "(61) 94444-1006", "email": "lucas.martins@email.com"},
    {"nome": "Fernanda Souza Ribeiro", "documento": "789.012.345-67", "whatsapp": "(71) 93333-1007", "email": "fernanda.ribeiro@email.com"},
    {"nome": "Rafael Augusto Barbosa", "documento": "890.123.456-78", "whatsapp": "(81) 92222-1008", "email": "rafael.barbosa@email.com"},
    {"nome": "Larissa Cristina Nunes", "documento": "901.234.567-89", "whatsapp": "(91) 91111-1009", "email": "larissa.nunes@email.com"},
    {"nome": "Gustavo Henrique Pinto", "documento": "012.345.678-90", "whatsapp": "(85) 90000-1010", "email": "gustavo.pinto@email.com"},
    {"nome": "Amanda Rodrigues Carvalho", "documento": "111.222.333-44", "whatsapp": "(11) 98888-1011", "email": "amanda.carvalho@email.com"},
    {"nome": "Diego Almeida Costa", "documento": "222.333.444-55", "whatsapp": "(21) 97777-1012", "email": "diego.costa@email.com"},
    {"nome": "Patrícia Oliveira Santos", "documento": "333.444.555-66", "whatsapp": "(31) 96666-1013", "email": "patricia.santos@email.com"},
    {"nome": "Thiago Silva Pereira", "documento": "444.555.666-77", "whatsapp": "(41) 95555-1014", "email": "thiago.pereira@email.com"},
    {"nome": "Camila Rocha Barbosa", "documento": "555.666.777-88", "whatsapp": "(51) 94444-1015", "email": "camila.barbosa@email.com"},
]

servicos_templates = [
    {"titulo": "Criação de Site Institucional", "descricao": "Desenvolvimento completo de site institucional com 5 páginas, responsivo e otimizado para SEO.", "valor_base": (3000, 8000)},
    {"titulo": "Landing Page", "descricao": "Criação de landing page para campanha de marketing digital com formulário de captura.", "valor_base": (1500, 3500)},
    {"titulo": "Sistema Web Personalizado", "descricao": "Desenvolvimento de sistema web sob medida com painel administrativo e banco de dados.", "valor_base": (8000, 25000)},
    {"titulo": "Identidade Visual Completa", "descricao": "Criação de logotipo, paleta de cores, tipografia e manual da marca.", "valor_base": (2000, 5000)},
    {"titulo": "Design de UI/UX", "descricao": "Design de interface e experiência do usuário para aplicativo mobile e web.", "valor_base": (4000, 10000)},
    {"titulo": "Otimização SEO", "descricao": "Auditoria e otimização completa para mecanismos de busca, incluindo análise de palavras-chave.", "valor_base": (1500, 4000)},
    {"titulo": "Manutenção Mensal de Site", "descricao": "Manutenção mensal incluindo atualizações, backups e suporte técnico.", "valor_base": (500, 1500)},
    {"titulo": "Integração de API", "descricao": "Integração de sistemas com APIs de terceiros (pagamento, CRM, redes sociais).", "valor_base": (3000, 8000)},
    {"titulo": "E-commerce Completo", "descricao": "Loja virtual completa com carrinho, gateway de pagamento e painel de gestão.", "valor_base": (10000, 30000)},
    {"titulo": "Campanha de E-mail Marketing", "descricao": "Criação e gestão de campanha de e-mail marketing com relatórios de desempenho.", "valor_base": (1000, 3000)},
    {"titulo": "Aplicativo Mobile", "descricao": "Desenvolvimento de aplicativo mobile para Android e iOS com backend.", "valor_base": (15000, 40000)},
    {"titulo": "Consultoria em Marketing Digital", "descricao": "Consultoria estratégica de marketing digital com análise de concorrência e plano de ação.", "valor_base": (2000, 6000)},
    {"titulo": "Hospedagem e Domínio", "descricao": "Configuração de hospedagem, domínio e certificado SSL com suporte anual.", "valor_base": (500, 1200)},
    {"titulo": "Redesign de Site", "descricao": "Redesign completo de site existente com nova identidade visual e melhorias de UX.", "valor_base": (4000, 10000)},
    {"titulo": "Automação de Processos", "descricao": "Automação de processos empresariais com integração de ferramentas e relatórios.", "valor_base": (5000, 15000)},
    {"titulo": "Produção de Conteúdo", "descricao": "Produção de conteúdo otimizado para blog e redes sociais (pacote mensal).", "valor_base": (800, 2500)},
    {"titulo": "Suporte Técnico Mensal", "descricao": "Pacote de suporte técnico com horas dedicadas e SLA de atendimento.", "valor_base": (1000, 3000)},
    {"titulo": "Migração de Servidor", "descricao": "Migração completa de servidor com mínimo de downtime e validação pós-migração.", "valor_base": (1500, 5000)},
    {"titulo": "Dashboard de Indicadores", "descricao": "Criação de dashboard interativo com indicadores de desempenho empresarial.", "valor_base": (3000, 8000)},
    {"titulo": "Treinamento de Equipe", "descricao": "Treinamento presencial ou remoto para equipe sobre ferramentas e processos digitais.", "valor_base": (1500, 4000)},
]

status_opcoes = ["Finalizado", "Finalizado", "Finalizado", "Em Produção", "Em Produção", "Pendente", "Cancelado"]
metodos_pagamento = ["Pix", "Boleto", "Cartão", "Transferência"]

def seed():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM financeiro")
        cur.execute("DELETE FROM servicos")
        cur.execute("DELETE FROM clientes")
        cur.execute("ALTER SEQUENCE clientes_id_seq RESTART WITH 1")
        cur.execute("ALTER SEQUENCE servicos_id_seq RESTART WITH 1")
        cur.execute("ALTER SEQUENCE financeiro_id_seq RESTART WITH 1")
        conn.commit()

        # Clientes
        for c in clientes_data:
            cur.execute(
                "INSERT INTO clientes (nome, documento, whatsapp, email) VALUES (%s, %s, %s, %s) RETURNING id",
                (c["nome"], c["documento"], c["whatsapp"], c["email"])
            )
        conn.commit()

        cur.execute("SELECT id FROM clientes ORDER BY id")
        cliente_ids = [row[0] for row in cur.fetchall()]

        # Serviços
        servico_ids = []
        start_date = datetime(2023, 1, 1)
        end_date = datetime(2026, 5, 1)
        total_days = (end_date - start_date).days

        for cliente_id in cliente_ids:
            num_servicos = random.randint(1, 4)
            for _ in range(num_servicos):
                tmpl = random.choice(servicos_templates)
                valor = round(random.uniform(tmpl["valor_base"][0], tmpl["valor_base"][1]), 2)
                status = random.choice(status_opcoes)
                random_days = random.randint(0, total_days)
                criado_em = start_date + timedelta(days=random_days)
                prazo = criado_em + timedelta(days=random.randint(15, 120))

                descricao_final = tmpl["descricao"]
                if status == "Cancelado":
                    razoes = ["Cliente desistiu do projeto.", "Orçamento não aprovado.", "Mudança de escopo inviável.", "Projeto cancelado por acordo mútuo."]
                    descricao_final = random.choice(razoes)

                cur.execute(
                    """INSERT INTO servicos (cliente_id, titulo, descricao, valor_total, prazo_entrega, status, criado_em)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (cliente_id, tmpl["titulo"], descricao_final, valor,
                     prazo.strftime("%Y-%m-%d"), status, criado_em)
                )
                servico_ids.append(cur.fetchone()[0])

        conn.commit()

        # Financeiro (apenas para serviços finalizados)
        for sid in servico_ids:
            cur.execute("SELECT status, valor_total, criado_em FROM servicos WHERE id = %s", (sid,))
            s = cur.fetchone()
            if s and s[0] == "Finalizado":
                valor_pago = round(s[1] * random.uniform(0.8, 1.0), 2)
                metodo = random.choice(metodos_pagamento)
                data_pag = s[2] + timedelta(days=random.randint(0, 30))
                cur.execute(
                    "INSERT INTO financeiro (servico_id, valor_recebido, metodo_pagamento, data_pagamento) VALUES (%s, %s, %s, %s)",
                    (sid, valor_pago, metodo, data_pag)
                )

        conn.commit()
        print("Banco populado com sucesso!")
        print(f"  - {len(cliente_ids)} clientes")
        print(f"  - {len(servico_ids)} serviços")
        cur.execute("SELECT COUNT(*) FROM financeiro")
        print(f"  - {cur.fetchone()[0]} pagamentos")

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    seed()
