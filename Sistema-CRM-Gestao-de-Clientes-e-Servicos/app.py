from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Form
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import psycopg2
from psycopg2.extras import RealDictCursor
from jose import JWTError, jwt
import bcrypt as _bcrypt
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import os

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "secrets", ".env"))

app = FastAPI()

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

        cur.execute("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                senha_hash VARCHAR(255) NOT NULL,
                data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ativo BOOLEAN DEFAULT TRUE
            );
        """)
        conn.commit()
        print("✓ Tabela 'usuarios' criada/verificada.")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS departamentos (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                descricao TEXT DEFAULT '',
                ativo BOOLEAN DEFAULT TRUE
            );
        """)
        conn.commit()
        print("✓ Tabela 'departamentos' criada/verificada.")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS funcionarios (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                cargo VARCHAR(255) DEFAULT '',
                departamento_id INTEGER REFERENCES departamentos(id),
                data_admissao DATE DEFAULT CURRENT_DATE,
                salario NUMERIC(10,2) DEFAULT 0,
                comissao_pct NUMERIC(5,2) DEFAULT 0,
                telefone VARCHAR(50) DEFAULT '',
                email VARCHAR(255) DEFAULT '',
                foto_url VARCHAR(500) DEFAULT '',
                ativo BOOLEAN DEFAULT TRUE,
                usuario_id INTEGER REFERENCES usuarios(id)
            );
        """)
        conn.commit()
        print("✓ Tabela 'funcionarios' criada/verificada.")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS produtos (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                categoria VARCHAR(255) DEFAULT '',
                preco NUMERIC(10,2) DEFAULT 0,
                custo NUMERIC(10,2) DEFAULT 0,
                estoque_atual INTEGER DEFAULT 0,
                estoque_minimo INTEGER DEFAULT 5,
                unidade VARCHAR(50) DEFAULT 'un',
                codigo_barras VARCHAR(100) DEFAULT '',
                ativo BOOLEAN DEFAULT TRUE
            );
        """)
        conn.commit()
        print("✓ Tabela 'produtos' criada/verificada.")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS vendas (
                id SERIAL PRIMARY KEY,
                funcionario_id INTEGER REFERENCES funcionarios(id),
                cliente_id INTEGER REFERENCES clientes(id),
                data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                valor_total NUMERIC(10,2) DEFAULT 0,
                desconto NUMERIC(10,2) DEFAULT 0,
                metodo_pagamento VARCHAR(100) DEFAULT '',
                status VARCHAR(50) DEFAULT 'Concluída',
                observacoes TEXT DEFAULT ''
            );
        """)
        conn.commit()
        print("✓ Tabela 'vendas' criada/verificada.")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS itens_venda (
                id SERIAL PRIMARY KEY,
                venda_id INTEGER REFERENCES vendas(id) ON DELETE CASCADE,
                produto_id INTEGER REFERENCES produtos(id),
                quantidade INTEGER DEFAULT 1,
                preco_unitario NUMERIC(10,2) DEFAULT 0,
                subtotal NUMERIC(10,2) DEFAULT 0
            );
        """)
        conn.commit()
        print("✓ Tabela 'itens_venda' criada/verificada.")

        cur.execute("""
            CREATE TABLE IF NOT EXISTS metas (
                id SERIAL PRIMARY KEY,
                funcionario_id INTEGER REFERENCES funcionarios(id),
                tipo VARCHAR(100) NOT NULL,
                valor_meta NUMERIC(10,2) DEFAULT 0,
                valor_alcancado NUMERIC(10,2) DEFAULT 0,
                periodo VARCHAR(50) DEFAULT 'Mensal',
                data_inicio DATE DEFAULT CURRENT_DATE,
                data_fim DATE DEFAULT CURRENT_DATE,
                status VARCHAR(50) DEFAULT 'Ativa'
            );
        """)
        conn.commit()
        print("✓ Tabela 'metas' criada/verificada.")

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

SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key-change-me")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 1440))

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

CLIENTE_VIEW_PIN = os.getenv("CLIENTE_VIEW_PIN", "1234")

def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed: str) -> bool:
    return _bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        return {"sub": username, "role": "admin"}
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM usuarios WHERE email = %s AND ativo = TRUE", (username,))
        user = cur.fetchone()
        if user and verify_password(password, user["senha_hash"]):
            return {"sub": user["email"], "role": "user", "user_id": user["id"], "nome": user["nome"]}
        return None
    except Exception:
        return None
    finally:
        cur.close()
        conn.close()

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

# ──────────────────────────── UI ────────────────────────────

@app.get("/")
async def serve_ui():
    return FileResponse(os.path.join(BASE_DIR, "static", "crm-trackt.html"))

# ──────────────────────────── AUTH ────────────────────────────

@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), remember_me: bool = Form(False)):
    user_data = authenticate_user(form_data.username, form_data.password)
    if not user_data:
        raise HTTPException(status_code=401, detail="Usuário ou senha inválidos")
    expire_days = 30 if remember_me else 1
    access_token = create_access_token(data=user_data, expires_delta=timedelta(days=expire_days))
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": expire_days * 86400,
        "user": {
            "sub": user_data["sub"],
            "role": user_data["role"],
            "nome": user_data.get("nome", "Admin"),
            "user_id": user_data.get("user_id")
        }
    }

class RegisterSchema(BaseModel):
    nome: str
    email: str
    password: str

class CheckEmailSchema(BaseModel):
    email: str

@app.post("/auth/register")
def register(data: RegisterSchema):
    if not data.nome or not data.email or not data.password:
        raise HTTPException(status_code=400, detail="Todos os campos são obrigatórios")
    if len(data.password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve ter no mínimo 6 caracteres")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (data.email,))
        if cur.fetchone():
            raise HTTPException(status_code=400, detail="Este email já está cadastrado")
        senha_hash = hash_password(data.password)
        cur.execute(
            "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s) RETURNING id, data_criacao;",
            (data.nome.strip(), data.email.strip().lower(), senha_hash)
        )
        user = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return {
            "mensagem": "Cadastro realizado com sucesso!",
            "user": {
                "id": user[0],
                "nome": data.nome.strip(),
                "email": data.email.strip().lower(),
                "data_criacao": user[1].isoformat() if user[1] else None
            }
        }
    except HTTPException:
        conn.rollback()
        cur.close()
        conn.close()
        raise
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail=f"Erro ao cadastrar: {str(e)}")

@app.post("/auth/check-email")
def check_email(data: CheckEmailSchema):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM usuarios WHERE email = %s", (data.email.strip().lower(),))
        exists = cur.fetchone() is not None
        return {"disponivel": not exists}
    finally:
        cur.close()
        conn.close()

class GoogleAuthSchema(BaseModel):
    credential: str

@app.post("/auth/google")
def google_login(data: GoogleAuthSchema, remember_me: bool = False):
    try:
        import google.oauth2.id_token
        import google.auth.transport.requests
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        if not GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=500, detail="Google Login não configurado. Configure GOOGLE_CLIENT_ID no .env")
        request = google.auth.transport.requests.Request()
        id_info = google.oauth2.id_token.verify_oauth2_token(data.credential, request, GOOGLE_CLIENT_ID)
        email = id_info.get("email")
        name = id_info.get("name", email.split("@")[0])
        if not email:
            raise HTTPException(status_code=400, detail="Email não fornecido pelo Google")
        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)
        try:
            cur.execute("SELECT * FROM usuarios WHERE email = %s", (email,))
            user = cur.fetchone()
            if not user:
                cur.execute(
                    "INSERT INTO usuarios (nome, email, senha_hash) VALUES (%s, %s, %s) RETURNING id, nome, data_criacao;",
                    (name, email, hash_password(os.urandom(24).hex()))
                )
                new_user = cur.fetchone()
                conn.commit()
                user_id = new_user["id"]
                nome = new_user["nome"]
            else:
                user_id = user["id"]
                nome = user["nome"]
            expire_days = 30 if remember_me else 1
            user_data = {"sub": email, "role": "user", "user_id": user_id, "nome": nome}
            access_token = create_access_token(data=user_data, expires_delta=timedelta(days=expire_days))
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": expire_days * 86400,
                "user": {
                    "sub": email,
                    "role": "user",
                    "nome": nome,
                    "user_id": user_id
                }
            }
        finally:
            cur.close()
            conn.close()
    except ValueError as e:
        raise HTTPException(status_code=401, detail=f"Token Google inválido: {str(e)}")

@app.get("/auth/google-client-id")
def get_google_client_id():
    client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    return {"client_id": client_id}

@app.get("/usuarios/me")
def usuario_atual(token_data: dict = Depends(verify_token)):
    return {
        "sub": token_data.get("sub"),
        "role": token_data.get("role", "user"),
        "nome": token_data.get("nome", "Usuário"),
        "user_id": token_data.get("user_id")
    }

# ──────────────────────────── CLIENTES ────────────────────────────

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

@app.get("/clientes/{cliente_id}/servicos")
def listar_servicos_por_cliente(cliente_id: int):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT s.*, c.nome as nome_cliente
            FROM servicos s
            JOIN clientes c ON s.cliente_id = c.id
            WHERE s.cliente_id = %s
            ORDER BY s.prazo_entrega ASC;
        """, (cliente_id,))
        servicos = cur.fetchall()
        if not servicos:
            return {"mensagem": "Nenhum serviço encontrado para este cliente.", "servicos": []}
        cur.close()
        conn.close()
        return servicos
    except Exception as e:
        cur.close()
        conn.close()
        raise HTTPException(status_code=500, detail=f"Erro no banco: {str(e)}")

# ──────────────────────────── SERVIÇOS ────────────────────────────

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

# ──────────────────────────── FINANCEIRO ────────────────────────────

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

# ──────────────────────────── DASHBOARD EXISTENTE ────────────────────────────

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
        SELECT s.*, c.nome as cliente_nome, c.id as cliente_id
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
    if status:
        query += " AND s.status = %s"
        params.append(status)
    if cliente_busca:
        query += " AND (c.nome ILIKE %s OR c.documento ILIKE %s)"
        params.append(f"%{cliente_busca}%")
        params.append(f"%{cliente_busca}%")

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
        SELECT f.*, s.titulo as servico_titulo, s.status as servico_status, s.descricao, c.nome as cliente_nome, c.id as cliente_id
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

# ──────────────────────────── DEPARTAMENTOS ────────────────────────────

class DepartamentoSchema(BaseModel):
    nome: str
    descricao: str = ""

@app.get("/departamentos")
def listar_departamentos(todos: bool = False, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if todos:
            cur.execute("SELECT * FROM departamentos ORDER BY nome ASC;")
        else:
            cur.execute("SELECT * FROM departamentos WHERE ativo = TRUE ORDER BY nome ASC;")
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.post("/departamentos")
def criar_departamento(data: DepartamentoSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO departamentos (nome, descricao) VALUES (%s, %s) RETURNING id;",
            (data.nome, data.descricao)
        )
        novo_id = cur.fetchone()[0]
        conn.commit()
        return {"mensagem": "Departamento criado!", "id": novo_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar departamento: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.put("/departamentos/{dept_id}")
def atualizar_departamento(dept_id: int, data: DepartamentoSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM departamentos WHERE id = %s;", (dept_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Departamento não encontrado")
        cur.execute(
            "UPDATE departamentos SET nome = %s, descricao = %s WHERE id = %s;",
            (data.nome, data.descricao, dept_id)
        )
        conn.commit()
        return {"mensagem": "Departamento atualizado!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.delete("/departamentos/{dept_id}")
def deletar_departamento(dept_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM departamentos WHERE id = %s;", (dept_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Departamento não encontrado")
        cur.execute("UPDATE departamentos SET ativo = FALSE WHERE id = %s;", (dept_id,))
        conn.commit()
        return {"mensagem": "Departamento removido!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao remover: {str(e)}")
    finally:
        cur.close()
        conn.close()

# ──────────────────────────── FUNCIONÁRIOS ────────────────────────────

class FuncionarioSchema(BaseModel):
    nome: str
    cargo: str = ""
    departamento_id: int | None = None
    data_admissao: str | None = None
    salario: float = 0
    comissao_pct: float = 0
    telefone: str = ""
    email: str = ""
    foto_url: str = ""

@app.get("/funcionarios/ranking")
def ranking_funcionarios(periodo_inicio: str = "", periodo_fim: str = "", token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        where_clause = "WHERE v.status = 'Concluída'"
        params = []
        if periodo_inicio:
            where_clause += " AND v.data_venda >= %s"
            params.append(periodo_inicio)
        if periodo_fim:
            where_clause += " AND v.data_venda <= %s"
            params.append(periodo_fim + " 23:59:59")

        cur.execute(f"""
            SELECT f.id, f.nome, f.cargo, f.foto_url,
                COUNT(v.id) as total_vendas,
                COALESCE(SUM(v.valor_total), 0) as valor_total_vendas,
                CASE WHEN COUNT(v.id) > 0 THEN COALESCE(SUM(v.valor_total), 0) / COUNT(v.id) ELSE 0 END as ticket_medio
            FROM funcionarios f
            LEFT JOIN vendas v ON v.funcionario_id = f.id {where_clause}
            WHERE f.ativo = TRUE
            GROUP BY f.id, f.nome, f.cargo, f.foto_url
            ORDER BY valor_total_vendas DESC
        """, params)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/funcionarios/funcionario-do-mes")
def funcionario_do_mes(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT f.id, f.nome, f.cargo, f.foto_url,
                COUNT(v.id) as total_vendas,
                COALESCE(SUM(v.valor_total), 0) as valor_total_vendas
            FROM funcionarios f
            LEFT JOIN vendas v ON v.funcionario_id = f.id
                AND v.status = 'Concluída'
                AND EXTRACT(MONTH FROM v.data_venda) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM v.data_venda) = EXTRACT(YEAR FROM CURRENT_DATE)
            WHERE f.ativo = TRUE
            GROUP BY f.id, f.nome, f.cargo, f.foto_url
            ORDER BY valor_total_vendas DESC
            LIMIT 1
        """)
        result = cur.fetchone()
        return dict(result) if result else {}
    finally:
        cur.close()
        conn.close()

@app.get("/funcionarios")
def listar_funcionarios(q: str = "", departamento_id: int = 0, cargo: str = "", ativo: str = "true", token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        where = "WHERE 1=1"
        params = []
        if ativo.lower() == "true":
            where += " AND f.ativo = TRUE"
        elif ativo.lower() == "false":
            where += " AND f.ativo = FALSE"
        if q:
            where += " AND (f.nome ILIKE %s OR f.cargo ILIKE %s)"
            params.extend([f"%{q}%", f"%{q}%"])
        if departamento_id:
            where += " AND f.departamento_id = %s"
            params.append(departamento_id)
        if cargo:
            where += " AND f.cargo ILIKE %s"
            params.append(f"%{cargo}%")

        cur.execute(f"""
            SELECT f.*, d.nome as departamento_nome
            FROM funcionarios f
            LEFT JOIN departamentos d ON f.departamento_id = d.id
            {where}
            ORDER BY f.nome ASC
        """, params)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/funcionarios/{func_id}")
def detalhes_funcionario(func_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT f.*, d.nome as departamento_nome
            FROM funcionarios f
            LEFT JOIN departamentos d ON f.departamento_id = d.id
            WHERE f.id = %s
        """, (func_id,))
        func = cur.fetchone()
        if not func:
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")

        cur.execute("""
            SELECT COUNT(v.id) as total_vendas,
                COALESCE(SUM(v.valor_total), 0) as valor_total_vendas,
                CASE WHEN COUNT(v.id) > 0 THEN COALESCE(SUM(v.valor_total), 0) / COUNT(v.id) ELSE 0 END as ticket_medio
            FROM vendas v
            WHERE v.funcionario_id = %s AND v.status = 'Concluída'
        """, (func_id,))
        stats = cur.fetchone()

        cur.execute("""
            SELECT m.*,
                CASE WHEN m.valor_meta > 0 THEN ROUND((m.valor_alcancado / m.valor_meta * 100)::numeric, 1) ELSE 0 END as percentual
            FROM metas m
            WHERE m.funcionario_id = %s AND m.status = 'Ativa'
            ORDER BY m.data_fim DESC
        """, (func_id,))
        metas = cur.fetchall()

        return {
            "funcionario": dict(func),
            "stats": dict(stats),
            "metas": [dict(m) for m in metas]
        }
    except HTTPException:
        raise
    finally:
        cur.close()
        conn.close()

@app.post("/funcionarios")
def criar_funcionario(data: FuncionarioSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO funcionarios (nome, cargo, departamento_id, data_admissao, salario, comissao_pct, telefone, email, foto_url)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;""",
            (data.nome, data.cargo, data.departamento_id, data.data_admissao, data.salario, data.comissao_pct, data.telefone, data.email, data.foto_url)
        )
        novo_id = cur.fetchone()[0]
        conn.commit()
        return {"mensagem": "Funcionário criado!", "id": novo_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar funcionário: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.put("/funcionarios/{func_id}")
def atualizar_funcionario(func_id: int, data: FuncionarioSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM funcionarios WHERE id = %s;", (func_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        cur.execute(
            """UPDATE funcionarios SET nome = %s, cargo = %s, departamento_id = %s, data_admissao = %s,
               salario = %s, comissao_pct = %s, telefone = %s, email = %s, foto_url = %s WHERE id = %s;""",
            (data.nome, data.cargo, data.departamento_id, data.data_admissao, data.salario, data.comissao_pct, data.telefone, data.email, data.foto_url, func_id)
        )
        conn.commit()
        return {"mensagem": "Funcionário atualizado!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.delete("/funcionarios/{func_id}")
def deletar_funcionario(func_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM funcionarios WHERE id = %s;", (func_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Funcionário não encontrado")
        cur.execute("UPDATE funcionarios SET ativo = FALSE WHERE id = %s;", (func_id,))
        conn.commit()
        return {"mensagem": "Funcionário removido!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao remover: {str(e)}")
    finally:
        cur.close()
        conn.close()

# ──────────────────────────── PRODUTOS ────────────────────────────

class ProdutoSchema(BaseModel):
    nome: str
    categoria: str = ""
    preco: float = 0
    custo: float = 0
    estoque_atual: int = 0
    estoque_minimo: int = 5
    unidade: str = "un"
    codigo_barras: str = ""

@app.get("/produtos/alertas")
def produtos_alerta(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT * FROM produtos
            WHERE ativo = TRUE AND estoque_atual <= estoque_minimo
            ORDER BY estoque_atual ASC
        """)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/produtos/categorias")
def listar_categorias(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT DISTINCT categoria FROM produtos
            WHERE ativo = TRUE AND categoria != ''
            ORDER BY categoria ASC
        """)
        result = cur.fetchall()
        return [r["categoria"] for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/produtos")
def listar_produtos(q: str = "", categoria: str = "", ativo: str = "true", token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        where = "WHERE 1=1"
        params = []
        if ativo.lower() == "true":
            where += " AND ativo = TRUE"
        elif ativo.lower() == "false":
            where += " AND ativo = FALSE"
        if q:
            where += " AND (nome ILIKE %s OR codigo_barras ILIKE %s)"
            params.extend([f"%{q}%", f"%{q}%"])
        if categoria:
            where += " AND categoria ILIKE %s"
            params.append(f"%{categoria}%")

        cur.execute(f"SELECT * FROM produtos {where} ORDER BY nome ASC", params)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/produtos/{produto_id}")
def detalhes_produto(produto_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT * FROM produtos WHERE id = %s;", (produto_id,))
        prod = cur.fetchone()
        if not prod:
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        return dict(prod)
    except HTTPException:
        raise
    finally:
        cur.close()
        conn.close()

@app.post("/produtos")
def criar_produto(data: ProdutoSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO produtos (nome, categoria, preco, custo, estoque_atual, estoque_minimo, unidade, codigo_barras)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;""",
            (data.nome, data.categoria, data.preco, data.custo, data.estoque_atual, data.estoque_minimo, data.unidade, data.codigo_barras)
        )
        novo_id = cur.fetchone()[0]
        conn.commit()
        return {"mensagem": "Produto criado!", "id": novo_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar produto: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.put("/produtos/{produto_id}")
def atualizar_produto(produto_id: int, data: ProdutoSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM produtos WHERE id = %s;", (produto_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        cur.execute(
            """UPDATE produtos SET nome = %s, categoria = %s, preco = %s, custo = %s,
               estoque_atual = %s, estoque_minimo = %s, unidade = %s, codigo_barras = %s WHERE id = %s;""",
            (data.nome, data.categoria, data.preco, data.custo, data.estoque_atual, data.estoque_minimo, data.unidade, data.codigo_barras, produto_id)
        )
        conn.commit()
        return {"mensagem": "Produto atualizado!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.delete("/produtos/{produto_id}")
def deletar_produto(produto_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM produtos WHERE id = %s;", (produto_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Produto não encontrado")
        cur.execute("UPDATE produtos SET ativo = FALSE WHERE id = %s;", (produto_id,))
        conn.commit()
        return {"mensagem": "Produto removido!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao remover: {str(e)}")
    finally:
        cur.close()
        conn.close()

# ──────────────────────────── VENDAS ────────────────────────────

class ItemVendaSchema(BaseModel):
    produto_id: int
    quantidade: int = 1
    preco_unitario: float = 0

class VendaSchema(BaseModel):
    funcionario_id: int | None = None
    cliente_id: int | None = None
    desconto: float = 0
    metodo_pagamento: str = ""
    status: str = "Concluída"
    observacoes: str = ""
    itens: list[ItemVendaSchema] = []

@app.get("/vendas/por-periodo")
def vendas_por_periodo(ano: str = "", token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if not ano:
            ano = str(datetime.now().year)
        cur.execute("""
            SELECT EXTRACT(MONTH FROM data_venda) as mes,
                COUNT(*) as total_vendas,
                COALESCE(SUM(valor_total), 0) as valor_total,
                COALESCE(SUM(valor_total - desconto), 0) as valor_liquido
            FROM vendas
            WHERE EXTRACT(YEAR FROM data_venda) = %s AND status != 'Cancelada'
            GROUP BY EXTRACT(MONTH FROM data_venda)
            ORDER BY mes ASC
        """, (ano,))
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/vendas/por-funcionario")
def vendas_por_funcionario(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT f.id, f.nome,
                COUNT(v.id) as total_vendas,
                COALESCE(SUM(v.valor_total), 0) as valor_total
            FROM funcionarios f
            LEFT JOIN vendas v ON v.funcionario_id = f.id AND v.status != 'Cancelada'
            WHERE f.ativo = TRUE
            GROUP BY f.id, f.nome
            ORDER BY valor_total DESC
        """)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/vendas")
def listar_vendas(
    funcionario_id: int = 0,
    cliente_id: int = 0,
    status: str = "",
    data_inicio: str = "",
    data_fim: str = "",
    metodo_pagamento: str = "",
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        where = "WHERE 1=1"
        params = []
        if funcionario_id:
            where += " AND v.funcionario_id = %s"
            params.append(funcionario_id)
        if cliente_id:
            where += " AND v.cliente_id = %s"
            params.append(cliente_id)
        if status:
            where += " AND v.status = %s"
            params.append(status)
        if data_inicio:
            where += " AND v.data_venda >= %s"
            params.append(data_inicio)
        if data_fim:
            where += " AND v.data_venda <= %s"
            params.append(data_fim + " 23:59:59")
        if metodo_pagamento:
            where += " AND v.metodo_pagamento = %s"
            params.append(metodo_pagamento)

        cur.execute(f"""
            SELECT v.*, f.nome as funcionario_nome, c.nome as cliente_nome
            FROM vendas v
            LEFT JOIN funcionarios f ON v.funcionario_id = f.id
            LEFT JOIN clientes c ON v.cliente_id = c.id
            {where}
            ORDER BY v.data_venda DESC
        """, params)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/vendas/{venda_id}")
def detalhes_venda(venda_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT v.*, f.nome as funcionario_nome, c.nome as cliente_nome
            FROM vendas v
            LEFT JOIN funcionarios f ON v.funcionario_id = f.id
            LEFT JOIN clientes c ON v.cliente_id = c.id
            WHERE v.id = %s
        """, (venda_id,))
        venda = cur.fetchone()
        if not venda:
            raise HTTPException(status_code=404, detail="Venda não encontrada")

        cur.execute("""
            SELECT iv.*, p.nome as produto_nome, p.unidade
            FROM itens_venda iv
            JOIN produtos p ON iv.produto_id = p.id
            WHERE iv.venda_id = %s
        """, (venda_id,))
        itens = cur.fetchall()

        return {
            "venda": dict(venda),
            "itens": [dict(i) for i in itens]
        }
    except HTTPException:
        raise
    finally:
        cur.close()
        conn.close()

@app.post("/vendas")
def criar_venda(data: VendaSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        valor_total = 0
        for item in data.itens:
            valor_total += item.quantidade * item.preco_unitario
        valor_total -= data.desconto

        cur.execute(
            """INSERT INTO vendas (funcionario_id, cliente_id, valor_total, desconto, metodo_pagamento, status, observacoes)
               VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;""",
            (data.funcionario_id, data.cliente_id, valor_total, data.desconto, data.metodo_pagamento, data.status, data.observacoes)
        )
        venda_id = cur.fetchone()["id"]

        for item in data.itens:
            subtotal = item.quantidade * item.preco_unitario
            cur.execute(
                """INSERT INTO itens_venda (venda_id, produto_id, quantidade, preco_unitario, subtotal)
                   VALUES (%s, %s, %s, %s, %s);""",
                (venda_id, item.produto_id, item.quantidade, item.preco_unitario, subtotal)
            )
            if data.status == "Concluída":
                cur.execute(
                    "UPDATE produtos SET estoque_atual = estoque_atual - %s WHERE id = %s;",
                    (item.quantidade, item.produto_id)
                )

        conn.commit()
        return {"mensagem": "Venda criada!", "id": venda_id, "valor_total": float(valor_total)}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar venda: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.put("/vendas/{venda_id}")
def atualizar_venda(venda_id: int, data: VendaSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, status FROM vendas WHERE id = %s;", (venda_id,))
        existing = cur.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Venda não encontrada")

        cur.execute(
            """UPDATE vendas SET funcionario_id = %s, cliente_id = %s, desconto = %s,
               metodo_pagamento = %s, status = %s, observacoes = %s WHERE id = %s;""",
            (data.funcionario_id, data.cliente_id, data.desconto, data.metodo_pagamento, data.status, data.observacoes, venda_id)
        )
        conn.commit()
        return {"mensagem": "Venda atualizada!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.delete("/vendas/{venda_id}")
def cancelar_venda(venda_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("SELECT id, status FROM vendas WHERE id = %s;", (venda_id,))
        venda = cur.fetchone()
        if not venda:
            raise HTTPException(status_code=404, detail="Venda não encontrada")
        if venda["status"] == "Cancelada":
            raise HTTPException(status_code=400, detail="Venda já está cancelada")

        cur.execute("""
            SELECT produto_id, quantidade FROM itens_venda WHERE venda_id = %s
        """, (venda_id,))
        itens = cur.fetchall()
        for item in itens:
            cur.execute(
                "UPDATE produtos SET estoque_atual = estoque_atual + %s WHERE id = %s;",
                (item["quantidade"], item["produto_id"])
            )

        cur.execute("UPDATE vendas SET status = 'Cancelada' WHERE id = %s;", (venda_id,))
        conn.commit()
        return {"mensagem": "Venda cancelada e estoque restaurado!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao cancelar: {str(e)}")
    finally:
        cur.close()
        conn.close()

# ──────────────────────────── METAS ────────────────────────────

class MetaSchema(BaseModel):
    funcionario_id: int
    tipo: str
    valor_meta: float = 0
    periodo: str = "Mensal"
    data_inicio: str | None = None
    data_fim: str | None = None

@app.get("/metas/resumo")
def metas_resumo(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT m.*, f.nome as funcionario_nome,
                CASE WHEN m.valor_meta > 0 THEN ROUND((m.valor_alcancado / m.valor_meta * 100)::numeric, 1) ELSE 0 END as percentual
            FROM metas m
            LEFT JOIN funcionarios f ON m.funcionario_id = f.id
            WHERE m.status = 'Ativa'
            ORDER BY percentual DESC
        """)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/metas")
def listar_metas(
    funcionario_id: int = 0,
    tipo: str = "",
    status: str = "",
    periodo: str = "",
    token_data: dict = Depends(verify_token)
):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        where = "WHERE 1=1"
        params = []
        if funcionario_id:
            where += " AND m.funcionario_id = %s"
            params.append(funcionario_id)
        if tipo:
            where += " AND m.tipo ILIKE %s"
            params.append(f"%{tipo}%")
        if status:
            where += " AND m.status = %s"
            params.append(status)
        if periodo:
            where += " AND m.periodo = %s"
            params.append(periodo)

        cur.execute(f"""
            SELECT m.*, f.nome as funcionario_nome,
                CASE WHEN m.valor_meta > 0 THEN ROUND((m.valor_alcancado / m.valor_meta * 100)::numeric, 1) ELSE 0 END as percentual
            FROM metas m
            LEFT JOIN funcionarios f ON m.funcionario_id = f.id
            {where}
            ORDER BY m.id DESC
        """, params)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.post("/metas")
def criar_meta(data: MetaSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """INSERT INTO metas (funcionario_id, tipo, valor_meta, periodo, data_inicio, data_fim)
               VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;""",
            (data.funcionario_id, data.tipo, data.valor_meta, data.periodo, data.data_inicio, data.data_fim)
        )
        novo_id = cur.fetchone()[0]
        conn.commit()
        return {"mensagem": "Meta criada!", "id": novo_id}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao criar meta: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.put("/metas/{meta_id}")
def atualizar_meta(meta_id: int, data: MetaSchema, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM metas WHERE id = %s;", (meta_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Meta não encontrada")
        cur.execute(
            """UPDATE metas SET funcionario_id = %s, tipo = %s, valor_meta = %s, periodo = %s,
               data_inicio = %s, data_fim = %s WHERE id = %s;""",
            (data.funcionario_id, data.tipo, data.valor_meta, data.periodo, data.data_inicio, data.data_fim, meta_id)
        )
        conn.commit()
        return {"mensagem": "Meta atualizada!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao atualizar: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.delete("/metas/{meta_id}")
def deletar_meta(meta_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("SELECT id FROM metas WHERE id = %s;", (meta_id,))
        if not cur.fetchone():
            raise HTTPException(status_code=404, detail="Meta não encontrada")
        cur.execute("DELETE FROM metas WHERE id = %s;", (meta_id,))
        conn.commit()
        return {"mensagem": "Meta removida!"}
    except HTTPException:
        conn.rollback()
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=400, detail=f"Erro ao remover: {str(e)}")
    finally:
        cur.close()
        conn.close()

@app.get("/metas/{meta_id}/progress")
def progresso_meta(meta_id: int, token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT m.*, f.nome as funcionario_nome,
                CASE WHEN m.valor_meta > 0 THEN ROUND((m.valor_alcancado / m.valor_meta * 100)::numeric, 1) ELSE 0 END as percentual
            FROM metas m
            LEFT JOIN funcionarios f ON m.funcionario_id = f.id
            WHERE m.id = %s
        """, (meta_id,))
        meta = cur.fetchone()
        if not meta:
            raise HTTPException(status_code=404, detail="Meta não encontrada")

        if meta["tipo"] == "Vendas":
            cur.execute("""
                SELECT COUNT(*) as total_vendas, COALESCE(SUM(valor_total), 0) as valor_total
                FROM vendas
                WHERE funcionario_id = %s AND status = 'Concluída'
                    AND data_venda >= %s AND data_venda <= %s
            """, (meta["funcionario_id"], meta["data_inicio"], meta["data_fim"]))
            detalhes = cur.fetchone()
            return {
                "meta": dict(meta),
                "detalhes": dict(detalhes)
            }
        else:
            return {"meta": dict(meta), "detalhes": {}}
    except HTTPException:
        raise
    finally:
        cur.close()
        conn.close()

# ──────────────────────────── DASHBOARD AVANÇADO ────────────────────────────

@app.get("/dashboard/geral")
def dashboard_geral(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        now = datetime.now()
        mes_atual = now.month
        ano_atual = now.year

        cur.execute("""
            SELECT COUNT(*) as total, COALESCE(SUM(valor_total), 0) as receita
            FROM vendas
            WHERE EXTRACT(MONTH FROM data_venda) = %s AND EXTRACT(YEAR FROM data_venda) = %s
                AND status != 'Cancelada'
        """, (mes_atual, ano_atual))
        vendas_mes = cur.fetchone()

        cur.execute("""
            SELECT COALESCE(SUM(valor_total), 0) as receita
            FROM vendas
            WHERE EXTRACT(MONTH FROM data_venda) = %s AND EXTRACT(YEAR FROM data_venda) = %s
                AND status != 'Cancelada'
        """, (mes_atual, ano_atual))
        receita_mes = cur.fetchone()

        cur.execute("""
            SELECT COALESCE(SUM(valor_meta), 0) as meta_total
            FROM metas
            WHERE status = 'Ativa' AND tipo = 'Receita'
                AND data_inicio <= CURRENT_DATE AND data_fim >= CURRENT_DATE
        """)
        meta_row = cur.fetchone()
        meta_receita = float(meta_row["meta_total"]) if meta_row else 0
        receita_val = float(receita_mes["receita"]) if receita_mes else 0
        percentual_meta = round((receita_val / meta_receita * 100), 1) if meta_receita > 0 else 0

        fm = cur.fetchone()
        cur.execute("""
            SELECT f.id, f.nome, COALESCE(SUM(v.valor_total), 0) as valor_total
            FROM funcionarios f
            LEFT JOIN vendas v ON v.funcionario_id = f.id AND v.status != 'Cancelada'
                AND EXTRACT(MONTH FROM v.data_venda) = %s AND EXTRACT(YEAR FROM v.data_venda) = %s
            WHERE f.ativo = TRUE
            GROUP BY f.id, f.nome
            ORDER BY valor_total DESC
            LIMIT 1
        """, (mes_atual, ano_atual))
        func_mes = cur.fetchone()

        cur.execute("""
            SELECT CASE WHEN COUNT(*) > 0 THEN COALESCE(SUM(valor_total), 0) / COUNT(*) ELSE 0 END as ticket_medio
            FROM vendas
            WHERE EXTRACT(MONTH FROM data_venda) = %s AND EXTRACT(YEAR FROM data_venda) = %s
                AND status != 'Cancelada'
        """, (mes_atual, ano_atual))
        ticket = cur.fetchone()

        cur.execute("SELECT COUNT(*) as count FROM produtos WHERE ativo = TRUE AND estoque_atual <= estoque_minimo;")
        estoque_baixo = cur.fetchone()

        cur.execute("SELECT COUNT(*) as count FROM funcionarios WHERE ativo = TRUE;")
        funcs_ativos = cur.fetchone()

        cur.execute("""
            SELECT TO_CHAR(DATE_TRUNC('month', data_venda), 'YYYY-MM') as mes,
                COUNT(*) as total, COALESCE(SUM(valor_total), 0) as receita
            FROM vendas
            WHERE status != 'Cancelada' AND data_venda >= (CURRENT_DATE - INTERVAL '12 months')
            GROUP BY mes
            ORDER BY mes ASC
        """)
        vendas_por_mes = cur.fetchall()

        cur.execute("""
            SELECT f.nome, COUNT(v.id) as total, COALESCE(SUM(v.valor_total), 0) as valor
            FROM funcionarios f
            LEFT JOIN vendas v ON v.funcionario_id = f.id AND v.status != 'Cancelada'
                AND EXTRACT(MONTH FROM v.data_venda) = %s AND EXTRACT(YEAR FROM v.data_venda) = %s
            WHERE f.ativo = TRUE
            GROUP BY f.nome
            ORDER BY valor DESC
        """, (mes_atual, ano_atual))
        vendas_por_func = cur.fetchall()

        cur.execute("""
            SELECT status, COUNT(*) as count FROM vendas
            WHERE EXTRACT(MONTH FROM data_venda) = %s AND EXTRACT(YEAR FROM data_venda) = %s
            GROUP BY status
        """, (mes_atual, ano_atual))
        status_vendas = cur.fetchall()

        return {
            "total_vendas_mes": vendas_mes["total"] if vendas_mes else 0,
            "receita_mes": receita_val,
            "meta_receita": meta_receita,
            "percentual_meta_receita": percentual_meta,
            "funcionario_do_mes": dict(func_mes) if func_mes else None,
            "ticket_medio": float(ticket["ticket_medio"]) if ticket else 0,
            "produtos_estoque_baixo": estoque_baixo["count"] if estoque_baixo else 0,
            "funcionarios_ativos": funcs_ativos["count"] if funcs_ativos else 0,
            "vendas_por_mes": [dict(r) for r in vendas_por_mes],
            "vendas_por_funcionario": [dict(r) for r in vendas_por_func],
            "status_vendas": [dict(r) for r in status_vendas]
        }
    finally:
        cur.close()
        conn.close()

@app.get("/dashboard/vendas-mensal")
def dashboard_vendas_mensal(ano: str = "", token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        if not ano:
            ano = str(datetime.now().year)
        cur.execute("""
            SELECT EXTRACT(MONTH FROM data_venda) as mes,
                COUNT(*) as total_vendas,
                COALESCE(SUM(valor_total), 0) as valor_total,
                COALESCE(SUM(valor_total - desconto), 0) as valor_liquido
            FROM vendas
            WHERE EXTRACT(YEAR FROM data_venda) = %s AND status != 'Cancelada'
            GROUP BY EXTRACT(MONTH FROM data_venda)
            ORDER BY mes ASC
        """, (ano,))
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/dashboard/desempenho")
def dashboard_desempenho(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT f.id, f.nome, f.cargo, f.foto_url,
                COUNT(v.id) as total_vendas,
                COALESCE(SUM(v.valor_total), 0) as valor_total,
                CASE WHEN COUNT(v.id) > 0 THEN COALESCE(SUM(v.valor_total), 0) / COUNT(v.id) ELSE 0 END as ticket_medio,
                EXTRACT(MONTH FROM CURRENT_DATE) as mes_atual,
                EXTRACT(YEAR FROM CURRENT_DATE) as ano_atual
            FROM funcionarios f
            LEFT JOIN vendas v ON v.funcionario_id = f.id AND v.status != 'Cancelada'
                AND EXTRACT(MONTH FROM v.data_venda) = EXTRACT(MONTH FROM CURRENT_DATE)
                AND EXTRACT(YEAR FROM v.data_venda) = EXTRACT(YEAR FROM CURRENT_DATE)
            WHERE f.ativo = TRUE
            GROUP BY f.id, f.nome, f.cargo, f.foto_url
            ORDER BY valor_total DESC
        """)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/dashboard/estoque-resumo")
def dashboard_estoque_resumo(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT categoria,
                COUNT(*) as total_produtos,
                COALESCE(SUM(estoque_atual), 0) as estoque_total,
                COALESCE(SUM(estoque_atual * preco), 0) as valor_estoque,
                SUM(CASE WHEN estoque_atual <= estoque_minimo THEN 1 ELSE 0 END) as alertas
            FROM produtos
            WHERE ativo = TRUE
            GROUP BY categoria
            ORDER BY categoria ASC
        """)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()

@app.get("/dashboard/metas-resumo")
def dashboard_metas_resumo(token_data: dict = Depends(verify_token)):
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cur.execute("""
            SELECT m.*, f.nome as funcionario_nome,
                CASE WHEN m.valor_meta > 0 THEN ROUND((m.valor_alcancado / m.valor_meta * 100)::numeric, 1) ELSE 0 END as percentual
            FROM metas m
            LEFT JOIN funcionarios f ON m.funcionario_id = f.id
            WHERE m.status = 'Ativa'
            ORDER BY percentual DESC
        """)
        result = cur.fetchall()
        return [dict(r) for r in result]
    finally:
        cur.close()
        conn.close()
