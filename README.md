# 🧠 Brainrot Manager

Sistema web completo para gerenciamento de Brainrots do jogo Roblox "Steal a Brainrot".

## 🚀 Tecnologias Utilizadas

- **Backend**: Flask (Python)
- **Banco de Dados**: PostgreSQL
- **Frontend**: Tailwind CSS + JavaScript
- **ORM**: SQLAlchemy
- **Migrações**: Flask-Migrate
- **Deploy**: Render

## 📋 Pré-requisitos

Antes de começar, você precisa ter instalado:

1. **Python 3.8+** - [Download Python](https://www.python.org/downloads/)
2. **PostgreSQL** - [Download PostgreSQL](https://www.postgresql.org/download/)
3. **pip** (geralmente vem com Python)

## 🔧 Instalação Passo a Passo

### 1. Criar e Ativar Ambiente Virtual

Abra o terminal (PowerShell no Windows) na pasta do projeto e execute:

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 2. Instalar Dependências

Com o ambiente virtual ativado, execute:

```bash
pip install -r requirements.txt
```

### 3. Configurar PostgreSQL

#### 3.1. Criar o Banco de Dados

Abra o **pgAdmin** ou use o terminal PostgreSQL e execute:

```sql
CREATE DATABASE brainrot_db;
```

#### 3.2. Configurar Conexão

Crie um arquivo `.env` na raiz do projeto (ou use as configurações padrão no `app.py`):

```env
DATABASE_URL=postgresql://postgres:SUA_SENHA@localhost:5432/brainrot_db
SECRET_KEY=sua-chave-secreta-aqui-mude-em-producao
```

**Importante**: Substitua `SUA_SENHA` pela senha do seu PostgreSQL.

### 4. Executar Migrações

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### 5. Executar o Projeto

```bash
python app.py
```

O sistema estará disponível em: **http://localhost:5000**

## 📁 Estrutura do Projeto

```
roube_um_brairout/
├── app.py                 # Arquivo principal do Flask
├── models.py              # Modelos do banco de dados
├── routes.py              # Rotas e APIs
├── requirements.txt       # Dependências Python
├── templates/             # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── brainrots/
│   │   ├── list.html
│   │   └── form.html
│   └── contas/
│       ├── list.html
│       ├── form.html
│       └── detail.html
├── static/                # Arquivos estáticos
│   └── uploads/           # Imagens enviadas
└── migrations/            # Migrações do banco (criado após flask db init)
```

## 🎯 Funcionalidades

### Brainrots
- ✅ Criar, editar, listar e excluir Brainrots
- ✅ Upload de imagens
- ✅ Filtros avançados (raridade, valor, quantidade, mutações, conta)
- ✅ Busca por nome
- ✅ Campos personalizados dinâmicos

### Contas
- ✅ Criar, editar, listar e excluir Contas
- ✅ Associação N:N com Brainrots
- ✅ Visualização detalhada de cada conta

### Dashboard
- ✅ Estatísticas gerais
- ✅ Brainrots recentes
- ✅ Valor total por segundo

## 🎨 Design

O sistema possui:
- ✨ Design moderno com Tailwind CSS
- 📱 Totalmente responsivo
- 🎭 Animações suaves
- 🎨 Paleta de cores elegante
- 🔄 Transições fluidas

## 🆘 Solução de Problemas

### Erro de conexão com PostgreSQL

Verifique se:
1. O PostgreSQL está rodando
2. A senha no `.env` está correta
3. O banco `brainrot_db` foi criado

### Erro de importação

Certifique-se de que:
1. O ambiente virtual está ativado
2. Todas as dependências foram instaladas: `pip install -r requirements.txt`

### Erro ao fazer upload de imagens

Verifique se a pasta `static/uploads` existe e tem permissão de escrita.

## 📝 Notas Importantes

- O sistema cria automaticamente as tabelas na primeira execução
- As imagens são salvas em `static/uploads/`
- Campos personalizados são armazenados como JSON no banco de dados

## 🔐 Segurança

⚠️ **ATENÇÃO**: Em produção, mude:
- `SECRET_KEY` no `.env`
- Desative o modo debug (`debug=False`)
- Use variáveis de ambiente para credenciais sensíveis

## 📞 Suporte

Se tiver dúvidas ou problemas, consulte a documentação ou entre em contato!

