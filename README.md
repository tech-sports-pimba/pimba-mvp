# Pimba - Personal Trainer Manager

Sistema multi-tenant para gestão de personal trainers, com autenticação via Firebase, gestão de alunos, agendamentos, fichas de treino com timer, controle financeiro e acompanhamento de evolução.

## 🚀 Status do Projeto

**Fase 1: Fundação** ✅ **COMPLETA**
- ✅ Estrutura base do projeto
- ✅ Modelos de dados (SQLAlchemy)
- ✅ Firebase Auth integration
- ✅ API REST (FastAPI) com endpoints de auth
- ✅ Streamlit UI moderna e responsiva
- ✅ Sistema multi-tenant pronto

**Fase 2: Gestão de Alunos** ✅ **COMPLETA**
- ✅ API CRUD de alunos com tenant isolation
- ✅ UI mobile-first para gestão de alunos
- ✅ Busca, filtros e estatísticas
- ✅ Seed com dados de teste

**Próximas Fases:**
- 📅 Fase 3: Agendamentos (Calendário)
- 💪 Fase 4: Fichas de Treino + Timer
- 💰 Fase 5: Controle Financeiro
- 📊 Fase 6: Evolução dos Alunos

## 📋 Requisitos

- Python 3.9+
- PostgreSQL
- Firebase Project (para autenticação)

## 🛠️ Setup Local

### 1. Criar ambiente virtual e instalar dependências

```bash
cd pimba-back
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configurar .env

Edite o arquivo `.env` (já existe no projeto):

```env
DATABASE_URL=postgresql://postgres@localhost:5432/pimba_db
SECRET_KEY=qualquer-string-aleatoria
DEBUG=True
```

#### Configurar Firebase (opcional para desenvolvimento)

**Opção 1: Usar modo desenvolvimento (sem Firebase)**
- No primeiro acesso, marque "Modo Desenvolvimento" e pule a configuração do Firebase

**Opção 2: Configurar Firebase (para produção)**

1. Acesse [Firebase Console](https://console.firebase.google.com)
2. Crie um novo projeto (ou use existente)
3. Vá em **Project Settings** → **Service Accounts**
4. Clique em **Generate New Private Key**
5. Salve o arquivo JSON baixado

**Como usar as credenciais:**

**Método A - JSON inline (recomendado para deploy):**
```env
FIREBASE_SERVICE_ACCOUNT_KEY='{"type": "service_account", "project_id": "seu-projeto", ...}'
```
Cole todo o conteúdo do JSON baixado entre as aspas simples.

**Método B - Caminho do arquivo (para desenvolvimento local):**
```env
FIREBASE_SERVICE_ACCOUNT_KEY=caminho/para/firebase-credentials.json
```

### 3. Criar banco de dados

```bash
createdb pimba_db
```

### 4. Popular banco com dados de teste (opcional)

```bash
source venv/bin/activate
python utils/seed.py
```

Isso vai criar:
- 1 Personal Trainer de teste (email: personal@pimba.com)
- 5 Alunos de teste (4 ativos, 1 inativo)

### 5. Executar aplicação

**Opção A - Com ambiente ativado (recomendado para dev):**
```bash
source venv/bin/activate  # Ativar venv (uma vez por sessão do terminal)
streamlit run app.py
```

**Opção B - Sem ativar (mais rápido):**
```bash
./venv/bin/streamlit run app.py
```

**Acesse:**
- UI: http://localhost:8501
- API Docs: http://localhost:8000/docs

**No primeiro acesso:**
- Marque "🚧 Modo Desenvolvimento" na tela de login
- Clique em "Entrar como Admin" ou "Entrar como Personal"
- Pronto! Não precisa configurar Firebase ainda

## 🔐 Primeiro Acesso

### Modo Desenvolvimento (sem Firebase configurado)

1. Acesse http://localhost:8501
2. Marque checkbox "🚧 Modo Desenvolvimento (bypass auth)"
3. Clique em "Entrar como Admin" ou "Entrar como Personal"

### Modo Produção (com Firebase)

1. Configure Firebase Auth no seu projeto
2. Implemente Firebase UI Web no componente `ui/auth_ui.py`
3. Use o fluxo de login com Firebase token

## 📂 Estrutura do Projeto

```
pimba-back/
├── config/              # Configurações (settings.py)
├── core/               # Core do sistema
│   ├── database.py     # Engine e session SQLAlchemy
│   ├── enums.py        # Enums (UserRole, etc)
│   └── models.py       # Modelos ORM
├── auth/               # Autenticação e autorização
│   ├── firebase_auth.py    # Firebase Admin SDK
│   └── dependencies.py     # FastAPI dependencies (get_current_user, etc)
├── api/                # API REST (FastAPI)
│   ├── main.py         # App FastAPI
│   ├── deps.py         # Dependencies (get_db)
│   └── routers/        # Endpoints
│       ├── auth.py     # Login, register
│       └── users.py    # User info
├── ui/                 # Interface Streamlit
│   ├── auth_ui.py      # Tela de login
│   └── dashboard_ui.py # Dashboard
├── app.py              # Aplicação Streamlit principal
└── requirements.txt    # Dependências Python
```

## 🗂️ Modelos de Dados

### User
- Usuário base com Firebase UID
- Roles: admin, personal, aluno

### Personal (Tenant)
- Personal Trainer
- Cada personal é um tenant isolado

### Aluno
- Vinculado a um Personal
- Tenant isolation por `personal_id`

### Agendamento
- Treinos agendados
- Data/hora, local, duração

### FichaTreino
- Fichas de treino personalizadas
- Contém múltiplos exercícios

### Exercicio
- Exercício individual em uma ficha
- Timer (duração + descanso)

### Pagamento
- Controle financeiro simples
- Entrada/saída por aluno

### RegistroEvolucao
- Métricas de evolução (peso, medidas)
- JSON flexível para diferentes medidas

## 🔒 Segurança

### Tenant Isolation

**CRÍTICO:** Todas as queries devem filtrar por `personal_id` para evitar vazamento de dados entre tenants.

Exemplo correto:
```python
# ✅ CORRETO - filtra por tenant
alunos = db.query(Aluno).filter(Aluno.personal_id == personal_id).all()

# ❌ ERRADO - vaza dados entre personals
alunos = db.query(Aluno).all()
```

Use a dependency `get_personal_id()` para obter o tenant_id automaticamente.

## 📡 API Endpoints

### Auth
- `POST /auth/login` - Login com Firebase token
- `POST /auth/register-personal` - Criar novo personal (admin)

### Users
- `GET /users/me` - Info do usuário autenticado

## 🧪 Desenvolvimento

### Executar sem Firebase (modo dev)

O sistema permite bypass de autenticação para desenvolvimento. Ative o checkbox "Modo Desenvolvimento" na tela de login.

### Criar migrations (Alembic)

```bash
# Inicializar Alembic
alembic init alembic

# Criar migration
alembic revision --autogenerate -m "Descrição"

# Aplicar migrations
alembic upgrade head
```

### Acessar API docs

Com a aplicação rodando, acesse:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 🐛 Troubleshooting

### Erro: "DATABASE_URL não encontrada"
- Verifique se o arquivo `.env` existe e está configurado
- Confirme que a string de conexão está correta

### Erro: "Falha ao inicializar Firebase"
- Verifique se `FIREBASE_SERVICE_ACCOUNT_KEY` está configurado corretamente
- Confirme que é um JSON válido ou caminho para arquivo
- Para desenvolvimento, use o modo bypass de auth

### API não responde
- Verifique se a porta 8000 está disponível: `lsof -i :8000`
- Confirme que o banco de dados está acessível
- Verifique logs do terminal para erros

### Erros de import
- Confirme que instalou todas as dependências: `pip install -r requirements.txt`
- Ative o ambiente virtual: `source venv/bin/activate`

## 📝 Próximos Passos

Para continuar o desenvolvimento, consulte o [Plano de Desenvolvimento](/Users/igorsal/.claude/plans/adaptive-churning-hellman.md) completo.

**Fase 3 - Agendamentos (Calendário):**
1. Implementar `api/routers/agendamentos.py` (CRUD completo)
2. Implementar `ui/agenda_ui.py` (visualização de calendário)
3. Integração com `streamlit-calendar` ou grid customizado

**Fase 4 - Fichas de Treino + Timer:**
1. Implementar `api/routers/treinos.py` e `exercicios.py`
2. Implementar `ui/treinos_ui.py` (criação de fichas)
3. Implementar `ui/timer_ui.py` (executor com cronômetro)

## 📄 Licença

[Definir licença]

## 👥 Contribuidores

- [Seu nome]

---

**Pimba** - Gestão inteligente para personal trainers 💪
