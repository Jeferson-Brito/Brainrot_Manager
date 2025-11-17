from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
from datetime import datetime
import json

# Carregar variáveis de ambiente
load_dotenv()

# Inicializar o Flask
app = Flask(__name__)

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
brainrot_conta, Brainrot, Conta, CampoPersonalizado = create_models(db)

# Importar rotas (depois de definir os modelos)
from routes import *

# Inicializar banco de dados ao iniciar
def init_db():
    with app.app_context():
        try:
            # Tentar aplicar migrações primeiro
            from flask_migrate import upgrade
            upgrade()
            print("✅ Migrações aplicadas com sucesso!")
        except Exception as e:
            print(f"⚠️  Erro ao aplicar migrações: {e}")
            try:
                # Fallback: criar tabelas diretamente
                db.create_all()
                print("✅ Tabelas criadas/verificadas com sucesso!")
            except Exception as e2:
                print(f"⚠️  Erro ao criar tabelas: {e2}")

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

