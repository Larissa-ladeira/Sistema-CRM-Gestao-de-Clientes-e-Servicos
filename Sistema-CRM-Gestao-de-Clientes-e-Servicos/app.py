from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import os

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets", ".env"))

app = FastAPI()

# Diretório atual
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.on_event("startup")
def startup():
    import random
    from datetime import datetime, timedelta
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS clientes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                documento VARCHAR(100),
                whatsapp VARCHAR(50),
                email VARCHAR(255)
            );
            CREATE TABLE IF NOT EXISTS servicos (
                id SERIAL PRIMARY KEY,
                cliente_id INTEGER REFERENCES clientes(id),
                titulo VARCHAR(255) NOT NULL,
                descricao TEXT,
                valor_total NUMERIC(10,2) DEFAULT 0,
                prazo_entrega DATE,
                status VARCHAR(50) DEFAULT 'Pendente',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS financeiro (
                id SERIAL PRIMARY KEY,
                servico_id INTEGER REFERENCES servicos(id),
                valor_recebido NUMERIC(10,2) DEFAULT 0,
                metodo_pagamento VARCHAR(100),
                data_pagamento TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

        cur.execute("""
            ALTER TABLE servicos ADD COLUMN IF NOT EXISTS criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
        """)
        conn.commit()

        cur.execute("""
            ALTER TABLE clientes ADD COLUMN IF NOT EXISTS email VARCHAR(255);
        """)
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM servicos WHERE criado_em IS NULL OR criado_em < '2020-01-01'")
        count = cur.fetchone()[0]
        if count > 0:
            cur.execute("SELECT id FROM servicos WHERE criado_em IS NULL OR criado_em < '2020-01-01'")
            servico_ids = [row[0] for row in cur.fetchall()]
            start_date = datetime(2020, 1, 1)
            end_date = datetime(2026, 12, 31)
            total_days = (end_date - start_date).days
            for sid in servico_ids:
                random_days = random.randint(0, total_days)
                random_date = start_date + timedelta(days=random_days)
                cur.execute("UPDATE servicos SET criado_em = %s WHERE id = %s", (random_date, sid))
            conn.commit()
            print(f"📅 {len(servico_ids)} serviços atualizados com datas entre 2020 e 2026.")
    except Exception as e:
        conn.rollback()
        print(f"Erro na migração: {e}")
    finally:
        cur.close()
        conn.close()

# Configurações de autenticação
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

# Usuário administrador
ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

# PIN extra para visualizar detalhes de clientes
CLIENTE_VIEW_PIN = os.getenv("CLIENTE_VIEW_PIN", "1234")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Servir arquivos estáticos (style.css e script.js)
STATIC_DIR = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

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

def authenticate_user(username: str, password: str):
    if username == ADMIN_USER and password == ADMIN_PASSWORD:
        return True
    return False

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def verify_token(request: Request):
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Não autenticado")
    token = auth_header.split("Bearer ")[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

@app.get("/")
async def serve_ui():
    return FileResponse(os.path.join(BASE_DIR, "static", "crm-trackt.html"))

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_user(form_data.username, form_data.password):
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}

class PinSchema(BaseModel):
    pin: str

@app.post("/clientes/verificar-pin")
def verificar_pin_cliente(pin_data: PinSchema, token_data: dict = Depends(verify_token)):
    if pin_data.pin != CLIENTE_VIEW_PIN:
        raise HTTPException(status_code=403, detail="PIN inválido")
    return {"valido": True}

@app.get("/clientes")
def listar_clientes(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM clientes ORDER BY nome ASC;")
    clientes = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(c) for c in clientes]

@app.get("/clientes/buscar")
def buscar_clientes(q: str, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT * FROM clientes WHERE nome ILIKE %s OR documento ILIKE %s ORDER BY nome ASC;", (f"%{q}%", f"%{q}%"))
    clientes = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(c) for c in clientes]

@app.get("/clientes/{cliente_id}")
def detalhes_cliente(cliente_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM clientes WHERE id = %s;", (cliente_id,))
    cliente = cur.fetchone()
    if not cliente:
        cur.close()
        conn.close()
        raise HTTPException(status_code=404, detail="Cliente não encontrado")

    cur.execute("SELECT * FROM servicos WHERE cliente_id = %s ORDER BY prazo_entrega DESC;", (cliente_id,))
    servicos = cur.fetchall()

    servico_ids = [s["id"] for s in servicos]
    pagamentos = []
    if servico_ids:
        cur.execute("SELECT * FROM financeiro WHERE servico_id = ANY(%s) ORDER BY data_pagamento DESC;", (servico_ids,))
        pagamentos = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "cliente": dict(cliente),
        "servicos": [dict(s) for s in servicos],
        "pagamentos": [dict(p) for p in pagamentos]
    }

class ClienteSchema(BaseModel):
    nome: str
    documento: str
    whatsapp: str
    email: str

class ServicoInputSchema(BaseModel):
    titulo: str
    descricao: str = ""
    valor_total: float = 0
    prazo_entrega: str | None = None
    status: str = "Pendente"

class FinanceiroInputSchema(BaseModel):
    valor_recebido: float = 0
    metodo_pagamento: str = ""

class ClienteCompletoSchema(BaseModel):
    cliente: ClienteSchema
    servico: ServicoInputSchema
    financeiro: FinanceiroInputSchema | None = None

@app.post("/clientes/completo")
def cadastrar_cliente_completo(data: ClienteCompletoSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO clientes (nome, documento, whatsapp, email) VALUES (%s, %s, %s, %s) RETURNING id;",
            (data.cliente.nome, data.cliente.documento, data.cliente.whatsapp, data.cliente.email)
        )
        cliente_id = cur.fetchone()[0]

        cur.execute(
            "INSERT INTO servicos (cliente_id, titulo, descricao, valor_total, prazo_entrega, status, criado_em) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP) RETURNING id;",
            (cliente_id, data.servico.titulo, data.servico.descricao, data.servico.valor_total, data.servico.prazo_entrega, data.servico.status)
        )
        servico_id = cur.fetchone()[0]

        if data.financeiro and data.financeiro.metodo_pagamento and data.financeiro.valor_recebido > 0:
            cur.execute(
                "INSERT INTO financeiro (servico_id, valor_recebido, metodo_pagamento) VALUES (%s, %s, %s) RETURNING id;",
                (servico_id, data.financeiro.valor_recebido, data.financeiro.metodo_pagamento)
            )
            cur.fetchone()

        conn.commit()
        cur.close()
        conn.close()
        return {"mensagem": "Cliente, serviço e pagamento registrados!", "cliente_id": cliente_id, "servico_id": servico_id}
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"Erro ao cadastrar: {str(e)}")

@app.post("/clientes")
def cadastrar_cliente(cliente: ClienteSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO clientes (nome, documento, whatsapp, email) VALUES (%s, %s, %s, %s) RETURNING id;",
            (cliente.nome, cliente.documento, cliente.whatsapp, cliente.email)
        )
        novo_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {"mensagem": "Cliente cadastrado com sucesso!", "id": novo_id}
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"Erro ao cadastrar: {str(e)}")

class ServicoSchema(BaseModel):
    cliente_id: int
    titulo: str
    descricao: str
    valor_total: float
    prazo_entrega: str
    status: str

@app.post("/servicos")
def cadastrar_servico(servico: ServicoSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO servicos (cliente_id, titulo, descricao, valor_total, prazo_entrega, status, criado_em) VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP) RETURNING id;",
            (servico.cliente_id, servico.titulo, servico.descricao, servico.valor_total, servico.prazo_entrega, servico.status)
        )
        novo_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {"mensagem": "Serviço registrado!", "id": novo_id}
    except Exception as e:
        conn.rollback()
        return {"erro": str(e)}

class FinanceiroSchema(BaseModel):
    servico_id: int
    valor_recebido: float
    metodo_pagamento: str

@app.post("/financeiro")
def registrar_pagamento(pagamento: FinanceiroSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO financeiro (servico_id, valor_recebido, metodo_pagamento) VALUES (%s, %s, %s) RETURNING id;",
            (pagamento.servico_id, pagamento.valor_recebido, pagamento.metodo_pagamento)
        )
        novo_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return {"mensagem": "Pagamento registrado!", "id": novo_id}
    except Exception as e:
        conn.rollback()
        return {"erro": str(e)}

@app.get("/dashboard/resumo")
def dashboard_resumo(
    data_inicio: str = "",
    data_fim: str = "",
    status: str = "",
    cliente_busca: str = "",
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    where_clause = "WHERE 1=1"
    params = []

    if data_inicio and len(data_inicio) == 4 and data_inicio.isdigit() and not data_fim:
        data_fim = data_inicio
    if data_fim and len(data_fim) == 4 and data_fim.isdigit() and not data_inicio:
        data_inicio = data_fim

    if data_inicio:
        where_clause += " AND s.criado_em >= %s"
        params.append(f"{data_inicio}-01-01" if len(data_inicio) == 4 and data_inicio.isdigit() else data_inicio)
    if data_fim:
        where_clause += " AND s.criado_em <= %s"
        params.append(f"{data_fim}-12-31 23:59:59" if len(data_fim) == 4 and data_fim.isdigit() else data_fim + " 23:59:59")
    if status:
        where_clause += " AND s.status = %s"
        params.append(status)
    if cliente_busca:
        where_clause += " AND (c.nome ILIKE %s OR c.documento ILIKE %s)"
        params.append(f"%{cliente_busca}%")
        params.append(f"%{cliente_busca}%")

    cur.execute(f"SELECT COUNT(*) as total, COALESCE(SUM(s.valor_total), 0) as valor_total FROM servicos s JOIN clientes c ON s.cliente_id = c.id {where_clause}", list(params))
    servicos = cur.fetchone()

    cur.execute(f"SELECT COUNT(*) as pagos FROM servicos s JOIN clientes c ON s.cliente_id = c.id {where_clause} AND s.status = 'Finalizado'", list(params))
    pagos = cur.fetchone()

    cur.execute(f"SELECT COUNT(*) as pendentes FROM servicos s JOIN clientes c ON s.cliente_id = c.id {where_clause} AND s.status = 'Pendente'", list(params))
    pendentes = cur.fetchone()

    cur.execute(f"SELECT COALESCE(SUM(f.valor_recebido), 0) as total_recebido FROM financeiro f JOIN servicos s ON f.servico_id = s.id JOIN clientes c ON s.cliente_id = c.id {where_clause}", list(params))
    financeiro = cur.fetchone()

    cur.execute(f"SELECT s.status, COUNT(*) as quantidade, COALESCE(SUM(s.valor_total), 0) as valor FROM servicos s JOIN clientes c ON s.cliente_id = c.id {where_clause} GROUP BY s.status", list(params))
    por_status = cur.fetchall()

    cur.execute(f"""
        SELECT c.nome, COUNT(s.id) as total_servicos, COALESCE(SUM(s.valor_total), 0) as valor_total
        FROM clientes c
        LEFT JOIN servicos s ON c.id = s.cliente_id {where_clause}
        GROUP BY c.nome
        ORDER BY valor_total DESC
        LIMIT 10
    """, list(params))
    top_clientes = cur.fetchall()

    cur.execute(f"""
        SELECT f.metodo_pagamento, COUNT(*) as quantidade, COALESCE(SUM(f.valor_recebido), 0) as total
        FROM financeiro f
        JOIN servicos s ON f.servico_id = s.id
        JOIN clientes c ON s.cliente_id = c.id {where_clause}
        GROUP BY f.metodo_pagamento
    """, list(params))
    por_metodo = cur.fetchall()

    cur.close()
    conn.close()

    return {
        "total_servicos": servicos["total"],
        "valor_total_contratos": float(servicos["valor_total"]),
        "servicos_pagos": pagos["pagos"],
        "servicos_pendentes": pendentes["pendentes"],
        "total_recebido": float(financeiro["total_recebido"]),
        "total_pendente": float(servicos["valor_total"]) - float(financeiro["total_recebido"]),
        "por_status": [dict(r) for r in por_status],
        "top_clientes": [dict(r) for r in top_clientes],
        "por_metodo": [dict(r) for r in por_metodo]
    }

@app.get("/dashboard/servicos")
def dashboard_servicos(
    status: str = "",
    cliente_busca: str = "",
    data_inicio: str = "",
    data_fim: str = "",
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT s.*, c.nome as cliente_nome 
        FROM servicos s 
        JOIN clientes c ON s.cliente_id = c.id 
        WHERE 1=1
    """
    params = []

    if data_inicio and len(data_inicio) == 4 and data_inicio.isdigit() and not data_fim:
        data_fim = data_inicio
    if data_fim and len(data_fim) == 4 and data_fim.isdigit() and not data_inicio:
        data_inicio = data_fim

    if data_inicio:
        query += " AND s.criado_em >= %s"
        params.append(f"{data_inicio}-01-01" if len(data_inicio) == 4 and data_inicio.isdigit() else data_inicio)
    if data_fim:
        query += " AND s.criado_em <= %s"
        params.append(f"{data_fim}-12-31 23:59:59" if len(data_fim) == 4 and data_fim.isdigit() else data_fim + " 23:59:59")

    query += " ORDER BY c.nome ASC"

    cur.execute(query, params)
    servicos = cur.fetchall()
    total_count = len(servicos)
    total_valor = float(sum(s["valor_total"] for s in servicos)) if servicos else 0

    cur.close()
    conn.close()

    return {"servicos": [dict(s) for s in servicos], "total": total_count, "total_valor": total_valor}

@app.get("/dashboard/financeiro")
def dashboard_financeiro(
    data_inicio: str = "",
    data_fim: str = "",
    status: str = "",
    cliente_busca: str = "",
    metodo: str = "",
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    query = """
        SELECT f.*, s.titulo as servico_titulo, s.status as servico_status, s.descricao, c.nome as cliente_nome
        FROM financeiro f
        JOIN servicos s ON f.servico_id = s.id
        JOIN clientes c ON s.cliente_id = c.id
        WHERE 1=1
    """
    params = []

    if data_inicio and len(data_inicio) == 4 and data_inicio.isdigit() and not data_fim:
        data_fim = data_inicio
    if data_fim and len(data_fim) == 4 and data_fim.isdigit() and not data_inicio:
        data_inicio = data_fim

    if data_inicio:
        query += " AND f.data_pagamento >= %s"
        params.append(f"{data_inicio}-01-01" if len(data_inicio) == 4 and data_inicio.isdigit() else data_inicio)
    if data_fim:
        query += " AND f.data_pagamento <= %s"
        params.append(f"{data_fim}-12-31 23:59:59" if len(data_fim) == 4 and data_fim.isdigit() else data_fim + " 23:59:59")
    if status:
        query += " AND s.status = %s"
        params.append(status)
    if cliente_busca:
        query += " AND (c.nome ILIKE %s OR c.documento ILIKE %s)"
        params.append(f"%{cliente_busca}%")
        params.append(f"%{cliente_busca}%")
    if metodo:
        query += " AND f.metodo_pagamento = %s"
        params.append(metodo)

    query += " ORDER BY f.id DESC"

    cur.execute(query, params)
    pagamentos = cur.fetchall()
    total_count = len(pagamentos)
    total_valor = float(sum(p["valor_recebido"] for p in pagamentos)) if pagamentos else 0

    cur.close()
    conn.close()

    return {"pagamentos": [dict(p) for p in pagamentos], "total": total_count, "total_valor": total_valor}

@app.get("/dashboard/clientes")
def dashboard_lista_clientes(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, nome FROM clientes ORDER BY nome ASC;")
    clientes = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(c) for c in clientes]

@app.get("/clientes/{cliente_id}/servicos")
def listar_servicos_por_cliente(cliente_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        # Busca todos os serviços vinculados a um ID específico
        cur.execute("""
            SELECT s.*, c.nome as nome_cliente 
            FROM servicos s
            JOIN clientes c ON s.cliente_id = c.id
            WHERE s.cliente_id = %s 
            ORDER BY s.prazo_entrega ASC;
        """, (cliente_id,))
        
        servicos = cur.fetchall()
        
        if not servicos:
            # Se não encontrar serviços, ainda assim retorna uma lista vazia ou erro
            return {"mensagem": "Nenhum serviço encontrado para este cliente.", "servicos": []}
            
        cur.close()
        conn.close()
        return servicos
        
    except Exception as e:
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro no banco: {str(e)}")
