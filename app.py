from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from dotenv import load_dotenv
import os
from datetime import datetime
import json

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar o Flask
app = Flask(__name__)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Configurações do banco de dados PostgreSQL
# Render fornece DATABASE_URL automaticamente
database_url = os.getenv('DATABASE_URL')
if not database_url:
    # Fallback para desenvolvimento local
    database_url = os.getenv('LOCAL_DATABASE_URL', 'postgresql://postgres:%40Lionnees14@localhost:5433/brainrot_db')

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'sua-chave-secreta-aqui-mude-em-producao')
app.config['UPLOAD_FOLDER'] = 'static/uploads'

# Criar pasta de uploads se não existir
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar extensões
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Importar e criar modelos (depois de criar db para evitar dependência circular)
from models import create_models

# Criar modelos com a instância do db
brainrot_conta, Brainrot, Conta, CampoPersonalizado, HistoricoAlteracao, FiltroSalvo, Meta = create_models(db)

# Configurar user_loader do Flask-Login
from auth import get_user

@login_manager.user_loader
def load_user(user_id):
    user = get_user()
    if str(user.id) == str(user_id):
        return user
    return None

# Importar rotas (depois de definir os modelos)
from routes import *

# Inicializar banco de dados ao iniciar
def init_db():
    with app.app_context():
        try:
            # Primeiro: tentar aplicar migrações (isso cria/atualiza tabelas)
            try:
                from flask_migrate import upgrade
                upgrade()
                print("Migracoes aplicadas com sucesso!")
            except Exception as migrate_error:
                print(f"Aviso migracoes: {migrate_error}")
                # Se migrações falharem, tentar criar tabelas diretamente
                try:
                    db.create_all()
                    # Tentar adicionar colunas manualmente se não existirem
                    try:
                        from sqlalchemy import text
                        db.session.execute(text("ALTER TABLE brainrot ADD COLUMN IF NOT EXISTS ordem INTEGER DEFAULT 0"))
                        db.session.execute(text("ALTER TABLE brainrot ADD COLUMN IF NOT EXISTS eventos TEXT"))
                        db.session.execute(text("ALTER TABLE brainrot ADD COLUMN IF NOT EXISTS favorito BOOLEAN DEFAULT FALSE"))
                        db.session.execute(text("ALTER TABLE brainrot ADD COLUMN IF NOT EXISTS tags TEXT"))
                        db.session.execute(text("ALTER TABLE conta ADD COLUMN IF NOT EXISTS espacos INTEGER DEFAULT 0"))
                        # Criar tabelas dos novos modelos se não existirem
                        try:
                            db.create_all()
                        except:
                            pass
                        db.session.commit()
                        print("Colunas e tabelas adicionadas com sucesso!")
                    except Exception as col_error:
                        print(f"Aviso ao adicionar colunas: {col_error}")
                        db.session.rollback()
                    print("Tabelas criadas/verificadas com sucesso!")
                except Exception as create_error:
                    print(f"Erro ao criar tabelas: {create_error}")
        except Exception as e:
            print(f"⚠️  Erro ao inicializar banco: {e}")
            import traceback
            traceback.print_exc()

# Inicializar apenas quando não estiver importando (para testes)
if __name__ != '__main__':
    init_db()

if __name__ == '__main__':
    # Inicializar banco antes de rodar
    init_db()
    # Modo desenvolvimento local
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    app.run(debug=debug, host='0.0.0.0', port=port)

