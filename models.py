from datetime import datetime
import json

# db será importado de app.py depois que este for criado
# Usamos uma função para inicializar os modelos com db

def create_models(db):
    """Cria todos os modelos e retorna a tabela de associação"""
    
    # Tabela de associação N:N entre Brainrots e Contas
    brainrot_conta = db.Table('brainrot_conta',
        db.Column('brainrot_id', db.Integer, db.ForeignKey('brainrot.id'), primary_key=True),
        db.Column('conta_id', db.Integer, db.ForeignKey('conta.id'), primary_key=True)
    )
    
    class Brainrot(db.Model):
        """Modelo para representar um Brainrot"""
        __tablename__ = 'brainrot'
        
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(200), nullable=False)
        foto = db.Column(db.String(500))  # Caminho da imagem
        raridade = db.Column(db.String(50), nullable=False, default='Comum')
        valor_por_segundo = db.Column(db.Float, default=0.0)  # Mantido para compatibilidade
        valor_formatado = db.Column(db.String(50), default='$0/s')  # Valor formatado (ex: $1.3B/s)
        quantidade = db.Column(db.Integer, default=1)
        numero_mutacoes = db.Column(db.Integer, default=0)
        campos_personalizados = db.Column(db.Text)  # JSON com campos dinâmicos
        data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
        data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # Relacionamento N:N com Contas
        contas = db.relationship('Conta', secondary=brainrot_conta, back_populates='brainrots', lazy='dynamic')
        
        def get_campos_personalizados(self):
            """Retorna os campos personalizados como dicionário"""
            if self.campos_personalizados:
                try:
                    return json.loads(self.campos_personalizados)
                except:
                    return {}
            return {}
        
        def set_campos_personalizados(self, campos_dict):
            """Define os campos personalizados a partir de um dicionário"""
            # Se o dicionário estiver vazio, salvar como JSON vazio (permitindo remover todos os campos)
            if campos_dict:
                self.campos_personalizados = json.dumps(campos_dict)
            else:
                self.campos_personalizados = json.dumps({})
        
        def to_dict(self):
            """Converte o Brainrot para dicionário"""
            return {
                'id': self.id,
                'nome': self.nome,
                'foto': self.foto,
                'raridade': self.raridade,
                'valor_por_segundo': self.valor_por_segundo,
                'valor_formatado': self.valor_formatado or f'${self.valor_por_segundo}/s',
                'quantidade': self.quantidade,
                'numero_mutacoes': self.numero_mutacoes,
                'campos_personalizados': self.get_campos_personalizados(),
                'contas': [conta.nome for conta in self.contas.all()],
                'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
            }
    
    class Conta(db.Model):
        """Modelo para representar uma Conta do Roblox"""
        __tablename__ = 'conta'
        
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(200), nullable=False)
        roblox_id = db.Column(db.String(100))  # ID opcional do Roblox
        data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
        data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # Relacionamento N:N com Brainrots
        brainrots = db.relationship('Brainrot', secondary=brainrot_conta, back_populates='contas', lazy='dynamic')
        
        def to_dict(self):
            """Converte a Conta para dicionário"""
            return {
                'id': self.id,
                'nome': self.nome,
                'roblox_id': self.roblox_id,
                'total_brainrots': self.brainrots.count(),
                'data_criacao': self.data_criacao.isoformat() if self.data_criacao else None
            }
    
    class CampoPersonalizado(db.Model):
        """Modelo para armazenar definições de campos personalizados"""
        __tablename__ = 'campo_personalizado'
        
        id = db.Column(db.Integer, primary_key=True)
        nome = db.Column(db.String(100), nullable=False, unique=True)
        tipo = db.Column(db.String(50), nullable=False)  # 'texto', 'numero', 'data', 'booleano'
        descricao = db.Column(db.String(300))
        data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
        
        def to_dict(self):
            """Converte o Campo Personalizado para dicionário"""
            return {
                'id': self.id,
                'nome': self.nome,
                'tipo': self.tipo,
                'descricao': self.descricao
            }
    
    return brainrot_conta, Brainrot, Conta, CampoPersonalizado
