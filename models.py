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
        numero_mutacoes = db.Column(db.Integer, default=0)  # Mantido para compatibilidade
        eventos = db.Column(db.Text)  # JSON com lista de eventos
        ordem = db.Column(db.Integer, default=0)  # Ordem personalizada para arrastar e soltar
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
        
        def get_eventos(self):
            """Retorna os eventos como lista"""
            if self.eventos:
                try:
                    return json.loads(self.eventos)
                except:
                    return []
            return []
        
        def set_eventos(self, eventos_list):
            """Define os eventos a partir de uma lista"""
            if eventos_list:
                self.eventos = json.dumps(eventos_list)
            else:
                self.eventos = json.dumps([])
        
        def get_raridade_ordem(self):
            """Retorna a ordem numérica da raridade para ordenação"""
            ordem_raridades = {
                'Comum': 1,
                'Raro': 2,
                'Épico': 3,
                'Lendário': 4,
                'Mítico': 5,
                'Deus Brainrot': 6,
                'Secreto': 7,
                'OG': 8
            }
            return ordem_raridades.get(self.raridade, 0)
        
        def to_dict(self):
            """Converte o Brainrot para dicionário"""
            # Tentar obter ordem, se não existir retornar 0
            try:
                ordem_valor = self.ordem if hasattr(self, 'ordem') else 0
            except:
                ordem_valor = 0
            
            return {
                'id': self.id,
                'nome': self.nome,
                'foto': self.foto,
                'raridade': self.raridade,
                'valor_por_segundo': self.valor_por_segundo,
                'valor_formatado': self.valor_formatado or f'${self.valor_por_segundo}/s',
                'quantidade': self.quantidade,
                'numero_mutacoes': self.numero_mutacoes,
                'eventos': self.get_eventos(),
                'ordem': ordem_valor,
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
        espacos = db.Column(db.Integer, default=0)  # Número de espaços para brainrots
        data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
        data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        
        # Relacionamento N:N com Brainrots
        brainrots = db.relationship('Brainrot', secondary=brainrot_conta, back_populates='contas', lazy='dynamic')
        
        def get_espacos_ocupados(self):
            """Retorna o número de espaços ocupados"""
            return self.brainrots.count()
        
        def get_espacos_livres(self):
            """Retorna o número de espaços livres"""
            if self.espacos == 0:
                return None  # Espaços ilimitados
            return max(0, self.espacos - self.get_espacos_ocupados())
        
        def tem_espaco_disponivel(self):
            """Verifica se a conta tem espaço disponível"""
            if self.espacos == 0:
                return True  # Espaços ilimitados
            return self.get_espacos_ocupados() < self.espacos
        
        def to_dict(self):
            """Converte a Conta para dicionário"""
            espacos_ocupados = self.get_espacos_ocupados()
            espacos_livres = self.get_espacos_livres()
            return {
                'id': self.id,
                'nome': self.nome,
                'roblox_id': self.roblox_id,
                'espacos': self.espacos,
                'espacos_ocupados': espacos_ocupados,
                'espacos_livres': espacos_livres,
                'total_brainrots': espacos_ocupados,
                'tem_espaco': self.tem_espaco_disponivel(),
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
