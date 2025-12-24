# Configuração do Firebase Auth

Este documento explica como configurar a autenticação Firebase no Pimba.

## 🚀 Modo Desenvolvimento (Recomendado para iniciar)

Para desenvolver e testar o sistema **sem configurar Firebase**, simplesmente deixe `DEBUG=True` no arquivo `.env`:

```env
DEBUG=True
```

**O que acontece:**
- Auto-login automático como Personal Trainer
- Sem necessidade de credenciais Firebase
- Acesso completo a todas as funcionalidades
- Dados de teste disponíveis via `python utils/seed.py`

**Quando usar:** Desenvolvimento, testes locais, prototipagem

---

## 🔐 Modo Produção (Firebase Auth Real)

Para usar autenticação real em produção, configure `DEBUG=False` e adicione as credenciais do Firebase.

### Passo 1: Criar projeto Firebase

1. Acesse [Firebase Console](https://console.firebase.google.com)
2. Clique em "Adicionar projeto"
3. Dê um nome ao projeto (ex: "pimba-crm")
4. Siga os passos até criar o projeto

### Passo 2: Ativar Authentication

1. No menu lateral, clique em **Authentication**
2. Clique em "Começar"
3. Na aba **Sign-in method**, ative:
   - ✅ **Email/Password** (login com email e senha)
   - 🚧 **Google** (em breve)

### Passo 3: Obter credenciais Server-Side (Admin SDK)

**Necessário para validar tokens no backend**

1. Vá em **Project Settings** (ícone de engrenagem) → **Service Accounts**
2. Clique em **Generate New Private Key**
3. Salve o arquivo JSON baixado
4. Copie TODO o conteúdo do JSON
5. No arquivo `.env`, cole como string entre aspas simples:

```env
FIREBASE_SERVICE_ACCOUNT_KEY='{"type": "service_account", "project_id": "seu-projeto", ...}'
```

**Alternativa:** Referencie o caminho do arquivo:
```env
FIREBASE_SERVICE_ACCOUNT_KEY=caminho/para/firebase-credentials.json
```

⚠️ **Importante:** Nunca commite este arquivo no Git! Ele já está no `.gitignore`.

### Passo 4: Obter credenciais Client-Side (Web SDK)

**Necessário para fazer login no navegador**

1. Vá em **Project Settings** → aba **General**
2. Role até "Seus apps" e clique no ícone **</>** (Web)
3. Registre o app (ex: "pimba-web")
4. Copie o objeto `firebaseConfig` que aparece:

```javascript
const firebaseConfig = {
  apiKey: "AIzaSy...",
  authDomain: "pimba-crm.firebaseapp.com",
  projectId: "pimba-crm",
  storageBucket: "pimba-crm.appspot.com",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:abc123"
};
```

5. Converta para **uma única linha** e adicione no `.env`:

```env
FIREBASE_WEB_CONFIG='{"apiKey": "AIzaSy...", "authDomain": "pimba-crm.firebaseapp.com", "projectId": "pimba-crm", "storageBucket": "pimba-crm.appspot.com", "messagingSenderId": "123456789", "appId": "1:123456789:web:abc123"}'
```

### Passo 5: Criar usuários no Firebase

**Opção A - Via Firebase Console (recomendado):**
1. Vá em **Authentication** → **Users**
2. Clique em **Add user**
3. Digite email e senha
4. Salve

**Opção B - Via código Python:**
```python
import firebase_admin
from firebase_admin import auth

# Criar usuário
user = auth.create_user(
    email='personal@exemplo.com',
    password='senha123',
    display_name='Personal Trainer'
)
```

### Passo 6: Ativar modo produção

No `.env`, altere para:
```env
DEBUG=False
```

**Reinicie o app:**
```bash
./venv/bin/streamlit run app.py
```

Agora você verá a tela de login real com email/senha!

---

## 🔄 Alternando entre Dev e Produção

### Para desenvolvimento:
```env
DEBUG=True
# FIREBASE_WEB_CONFIG não é necessário
```

### Para produção:
```env
DEBUG=False
FIREBASE_SERVICE_ACCOUNT_KEY='{"type": "service_account", ...}'
FIREBASE_WEB_CONFIG='{"apiKey": "...", ...}'
```

---

## 🐛 Troubleshooting

### "FIREBASE_WEB_CONFIG não configurado"
- Verifique se adicionou a variável no `.env`
- Confirme que é um JSON válido em uma única linha
- Use aspas simples para envolver o JSON

### "Email ou senha incorretos"
- Confirme que o usuário existe no Firebase Console
- Verifique se a senha está correta
- Certifique-se de que Authentication está ativado

### "Erro ao conectar com Firebase"
- Verifique sua conexão com internet
- Confirme que o `apiKey` está correto
- Verifique se o projeto Firebase está ativo

### "Token inválido" no backend
- Verifique se o `FIREBASE_SERVICE_ACCOUNT_KEY` está correto
- Confirme que é do mesmo projeto Firebase
- Certifique-se de que não expirou

---

## 📋 Checklist Final

Antes de fazer deploy em produção:

- [ ] Firebase Auth ativado (Email/Password)
- [ ] `FIREBASE_SERVICE_ACCOUNT_KEY` configurado no .env
- [ ] `FIREBASE_WEB_CONFIG` configurado no .env
- [ ] `DEBUG=False` no .env
- [ ] Usuários criados no Firebase Console
- [ ] Testado login com email/senha
- [ ] `.gitignore` protegendo credenciais

---

## 🎯 Próximos passos

- [ ] Implementar login com Google (OAuth2)
- [ ] Adicionar "Esqueci minha senha"
- [ ] Implementar registro de novos usuários
- [ ] Adicionar verificação de email
- [ ] Implementar perfis customizados (Personal pode criar alunos com acesso)

---

**Dúvidas?** Consulte a [documentação oficial do Firebase Auth](https://firebase.google.com/docs/auth)
