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


def gerar_codigo_barras():
    return "".join([str(random.randint(0, 9)) for _ in range(13)])


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

departamentos_data = [
    {"nome": "Vendas", "descricao": "Departamento de vendas e relacionamento com clientes"},
    {"nome": "Marketing", "descricao": "Departamento de marketing digital e comunicação"},
    {"nome": "Financeiro", "descricao": "Departamento financeiro e contabilidade"},
    {"nome": "Operações", "descricao": "Departamento de operações e logística"},
    {"nome": "TI / Tecnologia", "descricao": "Departamento de tecnologia da informação"},
    {"nome": "RH / Administração", "descricao": "Departamento de recursos humanos e administração"},
    {"nome": "Suporte ao Cliente", "descricao": "Departamento de suporte e atendimento ao cliente"},
    {"nome": "Logística", "descricao": "Departamento de logística e distribuição"},
]

funcionarios_data = [
    {"nome": "Marcos Ribeiro da Silva", "cargo": "Gerente de Vendas", "departamento": "Vendas", "salario": 8500, "comissao_pct": 5, "admissao": "2020-03-15"},
    {"nome": "Camila Ferreira Souza", "cargo": "Vendedora", "departamento": "Vendas", "salario": 3500, "comissao_pct": 8, "admissao": "2021-06-01"},
    {"nome": "Bruno Almeida Costa", "cargo": "Vendedor", "departamento": "Vendas", "salario": 3200, "comissao_pct": 7, "admissao": "2022-01-10"},
    {"nome": "Renata Oliveira Lima", "cargo": "Coordenadora de Marketing", "departamento": "Marketing", "salario": 7000, "comissao_pct": 3, "admissao": "2020-08-20"},
    {"nome": "Felipe Santos Nunes", "cargo": "Analista de Marketing", "departamento": "Marketing", "salario": 4500, "comissao_pct": 0, "admissao": "2023-02-15"},
    {"nome": "Juliana Rocha Pereira", "cargo": "Gerente Financeira", "departamento": "Financeiro", "salario": 9000, "comissao_pct": 0, "admissao": "2020-01-05"},
    {"nome": "André Martins Barbosa", "cargo": "Analista Financeiro", "departamento": "Financeiro", "salario": 5000, "comissao_pct": 0, "admissao": "2022-05-10"},
    {"nome": "Patricia Dias Alves", "cargo": "Coordenadora de Operações", "departamento": "Operações", "salario": 7500, "comissao_pct": 0, "admissao": "2020-11-20"},
    {"nome": "Ricardo Pinto Santos", "cargo": "Analista de Operações", "departamento": "Operações", "salario": 4200, "comissao_pct": 0, "admissao": "2023-07-01"},
    {"nome": "Lucas Oliveira da Costa", "cargo": "Desenvolvedor Senior", "departamento": "TI / Tecnologia", "salario": 11000, "comissao_pct": 0, "admissao": "2020-04-10"},
    {"nome": "Mariana Costa Ribeiro", "cargo": "Desenvolvedora Pleno", "departamento": "TI / Tecnologia", "salario": 7500, "comissao_pct": 0, "admissao": "2021-09-15"},
    {"nome": "Gabriel Pereira Lima", "cargo": "Estagiário de TI", "departamento": "TI / Tecnologia", "salario": 2000, "comissao_pct": 0, "admissao": "2025-01-10"},
    {"nome": "Fernanda Nunes Silva", "cargo": "Gerente de RH", "departamento": "RH / Administração", "salario": 8000, "comissao_pct": 0, "admissao": "2020-06-01"},
    {"nome": "Diego Santos Oliveira", "cargo": "Assistente Administrativo", "departamento": "RH / Administração", "salario": 2800, "comissao_pct": 0, "admissao": "2023-03-20"},
    {"nome": "Amanda Barbosa Costa", "cargo": "Analista de Suporte", "departamento": "Suporte ao Cliente", "salario": 3800, "comissao_pct": 0, "admissao": "2022-08-05"},
    {"nome": "Thiago Lima Martins", "cargo": "Coordenador de Suporte", "departamento": "Suporte ao Cliente", "salario": 6000, "comissao_pct": 3, "admissao": "2021-04-12"},
    {"nome": "Priscila Alves Ribeiro", "cargo": "Analista de Logística", "departamento": "Logística", "salario": 4000, "comissao_pct": 0, "admissao": "2022-11-01"},
    {"nome": "Roberto Carvalho Dias", "cargo": "Gerente de Logística", "departamento": "Logística", "salario": 7500, "comissao_pct": 0, "admissao": "2020-09-15"},
    {"nome": "Letícia Rocha Nunes", "cargo": "Vendedora", "departamento": "Vendas", "salario": 3300, "comissao_pct": 10, "admissao": "2024-02-01"},
    {"nome": "Eduardo Martins Pereira", "cargo": "Estagiário de Marketing", "departamento": "Marketing", "salario": 2200, "comissao_pct": 0, "admissao": "2025-03-10"},
]

produtos_data = [
    {"nome": "Notebook Dell Inspiron 15", "categoria": "Eletrônicos", "preco": 4299.90, "estoque_atual": 45, "estoque_minimo": 10, "unidade": "un"},
    {"nome": "Notebook Lenovo IdeaPad 3", "categoria": "Eletrônicos", "preco": 3199.90, "estoque_atual": 60, "estoque_minimo": 15, "unidade": "un"},
    {"nome": "Smartphone Samsung Galaxy A54", "categoria": "Eletrônicos", "preco": 1899.90, "estoque_atual": 80, "estoque_minimo": 20, "unidade": "un"},
    {"nome": "Monitor LG 24 Full HD", "categoria": "Eletrônicos", "preco": 999.90, "estoque_atual": 100, "estoque_minimo": 15, "unidade": "un"},
    {"nome": "Tablet Samsung Galaxy Tab S9", "categoria": "Eletrônicos", "preco": 2799.90, "estoque_atual": 30, "estoque_minimo": 8, "unidade": "un"},
    {"nome": "Ream de Papel A4 500 folhas", "categoria": "Materiais de Escritório", "preco": 29.90, "estoque_atual": 200, "estoque_minimo": 20, "unidade": "cx"},
    {"nome": "Caneta Esferográfica BIC Azul (cx c/ 50)", "categoria": "Materiais de Escritório", "preco": 45.00, "estoque_atual": 150, "estoque_minimo": 10, "unidade": "cx"},
    {"nome": "Lápis de Cor 24 Cores Faber-Castell", "categoria": "Materiais de Escritório", "preco": 38.90, "estoque_atual": 80, "estoque_minimo": 10, "unidade": "un"},
    {"nome": "Pasta Cliper A4 c/ 100 un", "categoria": "Materiais de Escritório", "preco": 59.90, "estoque_atual": 120, "estoque_minimo": 15, "unidade": "cx"},
    {"nome": "Post-it Super Sticky 76x127mm (cx c/ 12)", "categoria": "Materiais de Escritório", "preco": 52.90, "estoque_atual": 90, "estoque_minimo": 10, "unidade": "cx"},
    {"nome": "Antivírus Norton 360 Deluxe 1 ano", "categoria": "Software/Licenças", "preco": 149.90, "estoque_atual": 200, "estoque_minimo": 20, "unidade": "un"},
    {"nome": "Microsoft Office 365 Personal 1 ano", "categoria": "Software/Licenças", "preco": 299.90, "estoque_atual": 180, "estoque_minimo": 15, "unidade": "un"},
    {"nome": "Adobe Creative Cloud 1 ano", "categoria": "Software/Licenças", "preco": 499.90, "estoque_atual": 50, "estoque_minimo": 5, "unidade": "un"},
    {"nome": "Windows 11 Pro Licença", "categoria": "Software/Licenças", "preco": 699.90, "estoque_atual": 100, "estoque_minimo": 10, "unidade": "un"},
    {"nome": "Mouse Logitech MX Master 3S", "categoria": "Acessórios", "preco": 449.90, "estoque_atual": 70, "estoque_minimo": 10, "unidade": "un"},
    {"nome": "Teclado Mecânico Redragon Kumara RGB", "categoria": "Acessórios", "preco": 259.90, "estoque_atual": 90, "estoque_minimo": 10, "unidade": "un"},
    {"nome": "Headset Gamer HyperX Cloud II", "categoria": "Acessórios", "preco": 399.90, "estoque_atual": 55, "estoque_minimo": 8, "unidade": "un"},
    {"nome": "Webcam Logitech C920 HD Pro", "categoria": "Acessórios", "preco": 329.90, "estoque_atual": 65, "estoque_minimo": 10, "unidade": "un"},
    {"nome": "Mousepad Gamer XL Stitched", "categoria": "Acessórios", "preco": 89.90, "estoque_atual": 120, "estoque_minimo": 15, "unidade": "un"},
    {"nome": "Cadeira Ergonômica Executive Pro", "categoria": "Mobília", "preco": 1299.90, "estoque_atual": 25, "estoque_minimo": 5, "unidade": "un"},
    {"nome": "Mesa de Escritório Retrátil 120x60cm", "categoria": "Mobília", "preco": 899.90, "estoque_atual": 30, "estoque_minimo": 5, "unidade": "un"},
    {"nome": "Estante para Livros 5 Prateleiras", "categoria": "Mobília", "preco": 459.90, "estoque_atual": 40, "estoque_minimo": 5, "unidade": "un"},
    {"nome": "Armário 4 Gavetas Aço", "categoria": "Mobília", "preco": 649.90, "estoque_atual": 20, "estoque_minimo": 3, "unidade": "un"},
    {"nome": "Consultoria em TI (hora)", "categoria": "Serviços", "preco": 150.00, "estoque_atual": 200, "estoque_minimo": 20, "unidade": "pc"},
    {"nome": "Suporte Técnico Presencial (hora)", "categoria": "Serviços", "preco": 100.00, "estoque_atual": 200, "estoque_minimo": 20, "unidade": "pc"},
    {"nome": "Instalação de Rede (por ponto)", "categoria": "Serviços", "preco": 250.00, "estoque_atual": 100, "estoque_minimo": 10, "unidade": "pc"},
    {"nome": "Formatação de Computador", "categoria": "Serviços", "preco": 180.00, "estoque_atual": 150, "estoque_minimo": 15, "unidade": "pc"},
    {"nome": "Cabo de Rede Cat6 3m", "categoria": "Acessórios", "preco": 25.90, "estoque_atual": 200, "estoque_minimo": 20, "unidade": "un"},
]

vendas_status = ["Concluída", "Concluída", "Concluída", "Concluída", "Concluída", "Concluída", "Concluída",
                 "Pendente", "Pendente", "Cancelada", "Em Produção"]
vendas_metodos = ["Pix"] * 4 + ["Cartão"] * 2 + ["Boleto"] * 2 + ["Transferência"] * 2 + ["Dinheiro"]

metas_tipos = ["Vendas"] * 3 + ["Receita"] * 3 + ["Produto"] * 2 + ["Novos Clientes"] + ["Satisfação"]
metas_periodos = ["Mensal"] * 5 + ["Trimestral"] * 3 + ["Anual"] * 2
metas_status = ["Ativa"] * 8 + ["Concluída"] * 2 + ["Não Alcançada"]


def seed():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        print("Limpando tabelas existentes...")
        for tabela in ["itens_venda", "vendas", "metas", "financeiro", "servicos",
                        "produtos", "funcionarios", "departamentos", "clientes"]:
            cur.execute(f"DELETE FROM {tabela}")

        for seq in ["clientes_id_seq", "servicos_id_seq", "financeiro_id_seq",
                     "departamentos_id_seq", "funcionarios_id_seq", "produtos_id_seq",
                     "vendas_id_seq", "itens_venda_id_seq", "metas_id_seq"]:
            try:
                cur.execute(f"ALTER SEQUENCE {seq} RESTART WITH 1")
            except Exception:
                pass
        conn.commit()
        print("Tabelas limpas com sucesso!\n")

        # ==================== CLIENTES ====================
        print("Inserindo clientes...")
        for c in clientes_data:
            cur.execute(
                "INSERT INTO clientes (nome, documento, whatsapp, email) VALUES (%s, %s, %s, %s) RETURNING id",
                (c["nome"], c["documento"], c["whatsapp"], c["email"])
            )
        conn.commit()
        cur.execute("SELECT id FROM clientes ORDER BY id")
        cliente_ids = [row[0] for row in cur.fetchall()]
        print(f"  ✓ {len(cliente_ids)} clientes criados")

        # ==================== DEPARTAMENTOS ====================
        print("Inserindo departamentos...")
        for d in departamentos_data:
            cur.execute(
                "INSERT INTO departamentos (nome, descricao) VALUES (%s, %s) RETURNING id",
                (d["nome"], d["descricao"])
            )
        conn.commit()
        cur.execute("SELECT id, nome FROM departamentos ORDER BY id")
        dept_rows = cur.fetchall()
        dept_ids = [r[0] for r in dept_rows]
        dept_map = {r[1]: r[0] for r in dept_rows}
        print(f"  ✓ {len(dept_ids)} departamentos criados")

        # ==================== FUNCIONÁRIOS ====================
        print("Inserindo funcionários...")
        for f in funcionarios_data:
            dept_id = dept_map[f["departamento"]]
            cur.execute(
                """INSERT INTO funcionarios (nome, cargo, departamento_id, salario, comissao_pct, data_admissao)
                   VALUES (%s, %s, %s, %s, %s, %s) RETURNING id""",
                (f["nome"], f["cargo"], dept_id, f["salario"], f["comissao_pct"], f["admissao"])
            )
        conn.commit()
        cur.execute("SELECT id FROM funcionarios ORDER BY id")
        func_ids = [row[0] for row in cur.fetchall()]
        print(f"  ✓ {len(func_ids)} funcionários criados")

        # ==================== PRODUTOS ====================
        print("Inserindo produtos...")
        produto_precos = {}
        for p in produtos_data:
            cb = gerar_codigo_barras()
            custo = round(p["preco"] * random.uniform(0.60, 0.80), 2)
            cur.execute(
                """INSERT INTO produtos (nome, categoria, preco, custo, estoque_atual, estoque_minimo, unidade, codigo_barras)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (p["nome"], p["categoria"], p["preco"], custo, p["estoque_atual"],
                 p["estoque_minimo"], p["unidade"], cb)
            )
            prod_id = cur.fetchone()[0]
            produto_precos[prod_id] = p["preco"]
        conn.commit()
        cur.execute("SELECT id FROM produtos ORDER BY id")
        produto_ids = [row[0] for row in cur.fetchall()]
        print(f"  ✓ {len(produto_ids)} produtos criados")

        # ==================== SERVIÇOS ====================
        print("Inserindo serviços...")
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
                    razoes = ["Cliente desistiu do projeto.", "Orçamento não aprovado.",
                              "Mudança de escopo inviável.", "Projeto cancelado por acordo mútuo."]
                    descricao_final = random.choice(razoes)

                cur.execute(
                    """INSERT INTO servicos (cliente_id, titulo, descricao, valor_total, prazo_entrega, status, criado_em)
                       VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (cliente_id, tmpl["titulo"], descricao_final, valor,
                     prazo.strftime("%Y-%m-%d"), status, criado_em)
                )
                servico_ids.append(cur.fetchone()[0])
        conn.commit()
        print(f"  ✓ {len(servico_ids)} serviços criados")

        # ==================== FINANCEIRO ====================
        print("Inserindo financeiro...")
        fin_count = 0
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
                fin_count += 1
        conn.commit()
        print(f"  ✓ {fin_count} pagamentos criados")

        # ==================== VENDAS ====================
        print("Inserindo vendas...")
        vendas_start = datetime(2024, 1, 1)
        vendas_end = datetime(2026, 7, 1)
        vendas_total_days = (vendas_end - vendas_start).days
        venda_ids = []
        venda_clientes = {}

        for _ in range(50):
            random_days = random.randint(0, vendas_total_days)
            data_venda = vendas_start + timedelta(days=random_days)
            func_id = random.choice(func_ids)
            cli_id = random.choice(cliente_ids)
            status = random.choice(vendas_status)
            metodo = random.choice(vendas_metodos)
            desconto_pct = round(random.uniform(0, 0.15), 2) if random.random() < 0.4 else 0

            cur.execute(
                """INSERT INTO vendas (funcionario_id, cliente_id, data_venda, status,
                   metodo_pagamento, desconto, valor_total)
                   VALUES (%s, %s, %s, %s, %s, 0, 0) RETURNING id""",
                (func_id, cli_id, data_venda.strftime("%Y-%m-%d"), status, metodo)
            )
            vid = cur.fetchone()[0]
            venda_ids.append(vid)
            venda_clientes[vid] = {"func_id": func_id, "cli_id": cli_id, "status": status, "desconto_pct": desconto_pct}
        conn.commit()
        print(f"  ✓ {len(venda_ids)} vendas criadas")

        # ==================== ITENS_VENDA ====================
        print("Inserindo itens de venda e atualizando estoque...")
        itens_count = 0
        for vid in venda_ids:
            num_itens = random.randint(2, 6)
            itens_selecionados = random.sample(produto_ids, min(num_itens, len(produto_ids)))
            venda_valor_total = 0

            for pid in itens_selecionados:
                qtd = random.randint(1, 10)
                preco_unit = produto_precos[pid]
                subtotal = round(qtd * preco_unit, 2)
                venda_valor_total += subtotal

                cur.execute(
                    """INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal)
                       VALUES (%s, %s, %s, %s, %s)""",
                    (vid, pid, qtd, preco_unit, subtotal)
                )
                itens_count += 1

                if venda_clientes[vid]["status"] == "Concluída":
                    cur.execute(
                        "UPDATE produtos SET estoque_atual = estoque_atual - %s WHERE id = %s",
                        (qtd, pid)
                    )

            desconto_pct = venda_clientes[vid]["desconto_pct"]
            desconto_abs = round(venda_valor_total * desconto_pct, 2)
            valor_com_desconto = round(venda_valor_total - desconto_abs, 2)
            cur.execute(
                "UPDATE vendas SET valor_total = %s, desconto = %s WHERE id = %s",
                (valor_com_desconto, desconto_abs, vid)
            )
        conn.commit()
        print(f"  ✓ {itens_count} itens de venda criados")

        # ==================== METAS ====================
        print("Inserindo metas...")
        metas_count = 0
        for func_id in func_ids:
            num_metas = random.randint(1, 3)
            for _ in range(num_metas):
                tipo = random.choice(metas_tipos)
                periodo = random.choice(metas_periodos)
                status = random.choice(metas_status)

                if periodo == "Mensal":
                    data_inicio = datetime(2026, random.randint(1, 6), 1)
                    if data_inicio.month == 12:
                        data_fim = datetime(data_inicio.year + 1, 1, 1) - timedelta(days=1)
                    else:
                        data_fim = datetime(data_inicio.year, data_inicio.month + 1, 1) - timedelta(days=1)
                elif periodo == "Trimestral":
                    trimestre = random.randint(0, 3)
                    mes_inicio = trimestre * 3 + 1
                    data_inicio = datetime(2026, mes_inicio, 1)
                    mes_fim = mes_inicio + 3
                    if mes_fim > 12:
                        data_fim = datetime(data_inicio.year + 1, mes_fim - 12, 1) - timedelta(days=1)
                    else:
                        data_fim = datetime(data_inicio.year, mes_fim, 1) - timedelta(days=1)
                else:
                    data_inicio = datetime(random.choice([2025, 2026]), 1, 1)
                    data_fim = datetime(data_inicio.year, 12, 31)

                if tipo == "Vendas":
                    valor_meta = random.choice([15, 20, 25, 30, 40])
                elif tipo == "Receita":
                    valor_meta = random.choice([30000, 50000, 75000, 100000, 150000])
                elif tipo == "Produto":
                    valor_meta = random.choice([50, 80, 100, 150, 200])
                elif tipo == "Novos Clientes":
                    valor_meta = random.choice([5, 8, 10, 15, 20])
                else:
                    valor_meta = random.choice([85, 90, 92, 95, 98])

                pct_alcancado = random.uniform(0.60, 1.20)
                valor_alcancado = round(valor_meta * pct_alcancado, 2)

                cur.execute(
                    """INSERT INTO metas (funcionario_id, tipo, valor_meta, valor_alcancado,
                       periodo, data_inicio, data_fim, status)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                    (func_id, tipo, valor_meta, valor_alcancado, periodo,
                     data_inicio.strftime("%Y-%m-%d"), data_fim.strftime("%Y-%m-%d"), status)
                )
                metas_count += 1
        conn.commit()
        print(f"  ✓ {metas_count} metas criadas")

        print("\n" + "=" * 50)
        print("Banco populado com sucesso!")
        print("=" * 50)
        print(f"  - {len(cliente_ids)} clientes")
        print(f"  - {len(dept_ids)} departamentos")
        print(f"  - {len(func_ids)} funcionários")
        print(f"  - {len(produto_ids)} produtos")
        print(f"  - {len(servico_ids)} serviços")
        print(f"  - {fin_count} pagamentos")
        print(f"  - {len(venda_ids)} vendas")
        print(f"  - {itens_count} itens de venda")
        print(f"  - {metas_count} metas")
        print("=" * 50)

    except Exception as e:
        conn.rollback()
        print(f"Erro: {e}")
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    seed()
