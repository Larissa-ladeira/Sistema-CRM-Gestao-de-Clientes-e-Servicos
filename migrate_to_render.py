import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import os

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets", ".env"))

LOCAL_DB = {
    "host": "localhost",
    "database": "db_crm_freelancer",
    "user": "postgres",
    "password": "201397"
}

def conectar(conn_params):
    if isinstance(conn_params, str):
        return psycopg2.connect(conn_params)
    return psycopg2.connect(**conn_params)

def migrar():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("ERRO: DATABASE_URL nao definida no .env")
        print("   Adicione a URL do banco do Render no secrets/.env:")
        print('   DATABASE_URL="postgresql://user:pass@host:5432/db"')
        return

    try:
        conn_local = conectar(LOCAL_DB)
        conn_render = conectar(database_url)
        cur_local = conn_local.cursor(cursor_factory=RealDictCursor)
        cur_render = conn_render.cursor()

        print("Limpando banco do Render...")
        cur_render.execute("DELETE FROM financeiro")
        cur_render.execute("DELETE FROM servicos")
        cur_render.execute("DELETE FROM clientes")
        conn_render.commit()

        cur_local.execute("SELECT * FROM clientes ORDER BY id")
        clientes = cur_local.fetchall()
        for c in clientes:
            cur_render.execute(
                "INSERT INTO clientes (id, nome, documento, whatsapp, email) VALUES (%s, %s, %s, %s, %s)",
                (c["id"], c["nome"], c["documento"], c["whatsapp"], c["email"])
            )
        conn_render.commit()
        print(f"+ {len(clientes)} clientes migrados")

        cur_local.execute("SELECT * FROM servicos ORDER BY id")
        servicos = cur_local.fetchall()
        for s in servicos:
            cur_render.execute(
                "INSERT INTO servicos (id, cliente_id, titulo, descricao, valor_total, prazo_entrega, status, criado_em) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                (s["id"], s["cliente_id"], s["titulo"], s["descricao"], s["valor_total"], s["prazo_entrega"], s["status"], s["criado_em"])
            )
        conn_render.commit()
        print(f"+ {len(servicos)} servicos migrados")

        cur_local.execute("SELECT * FROM financeiro ORDER BY id")
        financeiro = cur_local.fetchall()
        for f in financeiro:
            cur_render.execute(
                "INSERT INTO financeiro (id, servico_id, valor_recebido, metodo_pagamento, data_pagamento) VALUES (%s, %s, %s, %s, %s)",
                (f["id"], f["servico_id"], f["valor_recebido"], f["metodo_pagamento"], f["data_pagamento"])
            )
        conn_render.commit()
        print(f"+ {len(financeiro)} pagamentos migrados")

        cur_render.execute("SELECT setval('clientes_id_seq', (SELECT MAX(id) FROM clientes))")
        cur_render.execute("SELECT setval('servicos_id_seq', (SELECT MAX(id) FROM servicos))")
        cur_render.execute("SELECT setval('financeiro_id_seq', (SELECT MAX(id) FROM financeiro))")
        conn_render.commit()

        print("\nMigracao concluida com sucesso!")

    except Exception as e:
        print(f"ERRO: {e}")
    finally:
        if cur_local: cur_local.close()
        if conn_local: conn_local.close()
        if cur_render: cur_render.close()
        if conn_render: conn_render.close()

if __name__ == "__main__":
    migrar()
