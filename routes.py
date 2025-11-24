from app import app, db, Brainrot, Conta, CampoPersonalizado, brainrot_conta
from flask import render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from auth import get_user
import os
import json
import re
from datetime import datetime
from collections import defaultdict

# Lista de raridades disponíveis
RARIDADES = ['Comum', 'Raro', 'Épico', 'Lendário', 'Mítico', 'Deus Brainrot', 'Secreto', 'OG']

# Lista de eventos disponíveis
EVENTOS = [
    '10B', '1x1x1x1', '4 de Julho', 'Sangue Podre', 'Bombardeiro', 'Brasil', 'Doce', 'Celestial',
    'Concerto', 'Crab Rave', 'Diamante', 'Extinto', 'Fogo', 'Galáxia', 'Falha', 'Ouro',
    'Indonésia', 'Lava', 'Relâmpago', 'Matteo', 'Meowl', 'México', 'Gatos Nyan', 'Pintura',
    'Abóbora', 'Radioativo', 'Chuva', 'Arco-íris', 'Chovendo Tacos', 'RIP', 'Tubarão',
    'Sonolento', 'Neve', 'Aranha', 'Queda de Estrelas', 'Morango', 'Gravata', 'Ataque Tung Tung',
    'OVNI', 'Bruxa', 'Yin-Yang'
]

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_valor_formatado(valor_str):
    """Converte valor formatado (ex: $50K/s, $1.5M/s) para número para comparação"""
    if not valor_str:
        return 0.0
    
    try:
        # Remover espaços e converter para maiúsculo
        valor_str = str(valor_str).strip().upper()
        
        # Extrair número (pode ter ponto decimal)
        match = re.search(r'([\d.]+)', valor_str)
        if not match:
            return 0.0
        
        numero = float(match.group(1))
        
        # Multiplicadores baseados no sufixo
        if 'K' in valor_str:
            return numero * 1000
        elif 'M' in valor_str:
            return numero * 1000000
        elif 'B' in valor_str:
            return numero * 1000000000
        elif 'T' in valor_str:
            return numero * 1000000000000
        
        return numero
    except (ValueError, AttributeError):
        return 0.0

def formatar_valor_range(valores_formatados):
    """Recebe uma lista de valores formatados e retorna o range (menor - maior)"""
    if not valores_formatados:
        return None
    
    # Converter todos para números
    valores_numeros = [(parse_valor_formatado(v), v) for v in valores_formatados if v]
    
    if not valores_numeros:
        return None
    
    # Se houver apenas um valor único (após remover duplicatas)
    valores_unicos = list(set([v[1] for v in valores_numeros]))
    if len(valores_unicos) == 1:
        return valores_unicos[0]
    
    # Encontrar menor e maior baseado no valor numérico
    valores_numeros.sort(key=lambda x: x[0])
    menor_formatado = valores_numeros[0][1]
    maior_formatado = valores_numeros[-1][1]
    
    # Se houver apenas um valor ou todos são iguais numericamente
    if valores_numeros[0][0] == valores_numeros[-1][0]:
        return menor_formatado
    
    # Retornar range (menor - maior)
    return f"{menor_formatado} - {maior_formatado}"

# ==================== AUTENTICAÇÃO ====================

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        user = get_user()
        if email == user.email and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos!', 'error')
    
    # Se já estiver logado, redirecionar para home
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """Fazer logout"""
    logout_user()
    flash('Você foi deslogado com sucesso!', 'info')
    return redirect(url_for('login'))

# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
@login_required
def index():
    """Página inicial com dashboard"""
    total_contas = Conta.query.count()
    total_brainrots = Brainrot.query.count()
    
    # Calcular valor total por segundo
    brainrots = Brainrot.query.all()
    valor_total_por_segundo = sum(br.valor_por_segundo * br.quantidade for br in brainrots)
    
    # Brainrots recentes
    brainrots_recentes = Brainrot.query.order_by(Brainrot.data_criacao.desc()).limit(5).all()
    
    return render_template('index.html',
                         total_contas=total_contas,
                         total_brainrots=total_brainrots,
                         valor_total_por_segundo=valor_total_por_segundo,
                         brainrots_recentes=brainrots_recentes)

@app.route('/brainrots')
@login_required
def brainrots_list():
    """Lista todos os Brainrots"""
    # Contar brainrots por raridade
    total_brainrots = Brainrot.query.count()
    brainrots_por_raridade = {}
    for raridade in RARIDADES:
        brainrots_por_raridade[raridade] = Brainrot.query.filter_by(raridade=raridade).count()
    
    return render_template('brainrots/list.html', 
                         total_brainrots=total_brainrots,
                         brainrots_por_raridade=brainrots_por_raridade)

@app.route('/brainrots/novo')
@login_required
def brainrot_new():
    """Página para criar novo Brainrot"""
    conta_id = request.args.get('conta_id', type=int)  # ID da conta se vier da página de detalhes
    contas = Conta.query.all()
    campos_personalizados = CampoPersonalizado.query.all()
    brainrots_existentes = Brainrot.query.all()  # Para opção de copiar
    return render_template('brainrots/form.html', 
                         brainrot=None, 
                         contas=contas,
                         conta_pre_selecionada=conta_id,
                         conta_id_url=conta_id,  # Para usar no JavaScript
                         campos_personalizados=campos_personalizados,
                         raridades=RARIDADES,
                         eventos=EVENTOS,
                         brainrots_existentes=brainrots_existentes)

@app.route('/brainrots/<int:id>/editar')
@login_required
def brainrot_edit(id):
    """Página para editar Brainrot"""
    brainrot = Brainrot.query.get_or_404(id)
    conta_id = request.args.get('conta_id', type=int)  # ID da conta se vier da página de detalhes
    # Carregar contas associadas explicitamente
    contas_associadas = [c.id for c in brainrot.contas.all()]
    contas = Conta.query.all()
    campos_personalizados = CampoPersonalizado.query.all()
    
    # Buscar todas as instâncias do brainrot com o mesmo nome (exceto a atual)
    instancias = Brainrot.query.filter(Brainrot.nome == brainrot.nome, Brainrot.id != brainrot.id).all()
    
    # Preparar dados das instâncias para o template
    instancias_data = []
    for inst in instancias:
        instancias_data.append({
            'id': inst.id,
            'valor_formatado': inst.valor_formatado or f'${inst.valor_por_segundo}/s',
            'numero_mutacoes': inst.numero_mutacoes,
            'contas': [conta.nome for conta in inst.contas.all()],
            'quantidade': inst.quantidade
        })
    
    brainrots_existentes = Brainrot.query.all()  # Para opção de copiar
    return render_template('brainrots/form.html',
                         brainrot=brainrot,
                         contas=contas,
                         contas_associadas=contas_associadas,
                         conta_pre_selecionada=conta_id,  # Para pré-selecionar a conta
                         conta_id_url=conta_id,  # Para usar no JavaScript de redirecionamento
                         campos_personalizados=campos_personalizados,
                         raridades=RARIDADES,
                         eventos=EVENTOS,
                         instancias=instancias_data,
                         brainrots_existentes=brainrots_existentes)

@app.route('/contas')
@login_required
def contas_list():
    """Lista todas as Contas"""
    total_contas = Conta.query.count()
    return render_template('contas/list.html', total_contas=total_contas)

@app.route('/contas/nova')
@login_required
def conta_new():
    """Página para criar nova Conta"""
    brainrots = Brainrot.query.all()
    return render_template('contas/form.html', 
                         conta=None, 
                         brainrots=brainrots,
                         brainrots_associados=[])

@app.route('/contas/<int:id>/editar')
@login_required
def conta_edit(id):
    """Página para editar Conta"""
    conta = Conta.query.get_or_404(id)
    # Carregar brainrots associados explicitamente
    brainrots_associados = [b.id for b in conta.brainrots.all()]
    brainrots = Brainrot.query.all()
    return render_template('contas/form.html', 
                         conta=conta, 
                         brainrots=brainrots,
                         brainrots_associados=brainrots_associados)

@app.route('/contas/<int:id>')
@login_required
def conta_detail(id):
    """Página de detalhes da Conta"""
    conta = Conta.query.get_or_404(id)
    # Carregar brainrots explicitamente para o template
    brainrots = conta.brainrots.all()
    return render_template('contas/detail.html', conta=conta, brainrots=brainrots)

# ==================== API REST ====================

@app.route('/api/brainrots', methods=['GET'])
@login_required
def api_brainrots_list():
    """API para listar Brainrots com busca e filtros"""
    # Parâmetros de busca e filtro
    busca = request.args.get('busca', '', type=str)
    raridade = request.args.get('raridade', '', type=str)
    valor_min = request.args.get('valor_min', type=float)
    valor_max = request.args.get('valor_max', type=float)
    valor_formato = request.args.get('valor_formato', '', type=str)  # /s, K/s, M/s, B/s
    quantidade_min = request.args.get('quantidade_min', type=int)
    quantidade_max = request.args.get('quantidade_max', type=int)
    mutacoes_min = request.args.get('mutacoes_min', type=int)
    mutacoes_max = request.args.get('mutacoes_max', type=int)
    evento = request.args.get('evento', '', type=str)  # Filtro por evento
    conta_id = request.args.get('conta_id', type=int)
    
    # Query base
    query = Brainrot.query
    
    # Aplicar filtros
    if busca:
        query = query.filter(Brainrot.nome.ilike(f'%{busca}%'))
    if raridade:
        query = query.filter(Brainrot.raridade == raridade)
    
    # Filtro por formato de valor (valor_formatado contém o formato)
    if valor_formato:
        query = query.filter(Brainrot.valor_formatado.like(f'%{valor_formato}'))
    
    # Filtro por valor numérico (convertendo baseado no formato)
    if valor_min is not None or valor_max is not None:
        # Para filtrar por valor, precisamos converter baseado no formato
        # Por enquanto, vamos filtrar pelo valor_por_segundo se não houver formato específico
        if valor_min is not None:
            query = query.filter(Brainrot.valor_por_segundo >= valor_min)
        if valor_max is not None:
            query = query.filter(Brainrot.valor_por_segundo <= valor_max)
    
    if quantidade_min is not None:
        query = query.filter(Brainrot.quantidade >= quantidade_min)
    if quantidade_max is not None:
        query = query.filter(Brainrot.quantidade <= quantidade_max)
    if mutacoes_min is not None:
        query = query.filter(Brainrot.numero_mutacoes >= mutacoes_min)
    if mutacoes_max is not None:
        query = query.filter(Brainrot.numero_mutacoes <= mutacoes_max)
    
    # Filtro por evento
    if evento:
        # Buscar brainrots que tenham o evento na lista de eventos (JSON)
        query = query.filter(Brainrot.eventos.like(f'%"{evento}"%'))
    
    if conta_id:
        query = query.join(brainrot_conta).filter(brainrot_conta.c.conta_id == conta_id)
    
    # Ordenar por raridade primeiro, depois por ordem personalizada
    # Definir ordem de raridades
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
    
    brainrots = query.all()
    
    # Ordenar: primeiro por raridade, depois por ordem personalizada
    brainrots_ordenados = sorted(brainrots, key=lambda br: (
        ordem_raridades.get(br.raridade, 0),
        getattr(br, 'ordem', 0),  # Usar getattr para evitar erro se ordem não existir
        br.data_criacao
    ))
    
    # Agrupar brainrots por nome para calcular ranges de valores
    brainrots_por_nome = defaultdict(list)
    for br in brainrots_ordenados:
        brainrots_por_nome[br.nome].append(br)
    
    # Criar lista de resultados agrupados
    resultados = []
    for nome, lista_brainrots in brainrots_por_nome.items():
        if len(lista_brainrots) > 1:
            # Múltiplos brainrots com mesmo nome - criar um resultado com range
            valores_formatados = []
            for br in lista_brainrots:
                if br.valor_formatado:
                    valores_formatados.append(br.valor_formatado)
                else:
                    # Formatar usando valor_por_segundo se não houver valor_formatado
                    vps = br.valor_por_segundo or 0
                    if vps >= 1000000000:
                        valores_formatados.append(f'${vps/1000000000:.1f}B/s')
                    elif vps >= 1000000:
                        valores_formatados.append(f'${vps/1000000:.1f}M/s')
                    elif vps >= 1000:
                        valores_formatados.append(f'${vps/1000:.1f}K/s')
                    else:
                        valores_formatados.append(f'${vps:.0f}/s')
            
            valor_range = formatar_valor_range(valores_formatados)
            
            # Usar o primeiro brainrot como base
            brainrot_base = lista_brainrots[0]
            brainrot_dict = brainrot_base.to_dict()
            
            # Atualizar com range de valores (sobrescrever valor_formatado)
            brainrot_dict['valor_range'] = valor_range
            brainrot_dict['tem_multiplos'] = True
            brainrot_dict['total_instancias'] = len(lista_brainrots)
            
            # Listar todas as instâncias com seus detalhes
            brainrot_dict['instancias'] = []
            for inst in lista_brainrots:
                inst_valor = inst.valor_formatado
                if not inst_valor:
                    # Formatar usando valor_por_segundo
                    vps = inst.valor_por_segundo or 0
                    if vps >= 1000000000:
                        inst_valor = f'${vps/1000000000:.1f}B/s'
                    elif vps >= 1000000:
                        inst_valor = f'${vps/1000000:.1f}M/s'
                    elif vps >= 1000:
                        inst_valor = f'${vps/1000:.1f}K/s'
                    else:
                        inst_valor = f'${vps:.0f}/s'
                
                inst_dict = {
                    'id': inst.id,
                    'valor_formatado': inst_valor,
                    'numero_mutacoes': inst.numero_mutacoes,
                    'contas': [conta.nome for conta in inst.contas.all()]
                }
                brainrot_dict['instancias'].append(inst_dict)
            
            resultados.append(brainrot_dict)
        else:
            # Apenas um brainrot com esse nome
            brainrot_dict = lista_brainrots[0].to_dict()
            brainrot_dict['tem_multiplos'] = False
            brainrot_dict['total_instancias'] = 1
            resultados.append(brainrot_dict)
    
    return jsonify(resultados)

@app.route('/api/brainrots', methods=['POST'])
@login_required
def api_brainrot_create():
    """API para criar Brainrot"""
    try:
        data = request.get_json()
        
        # Obter valor formatado ou criar a partir do valor por segundo
        valor_formatado = data.get('valor_formatado', '')
        if not valor_formatado:
            valor_numero = data.get('valor_por_segundo', 0)
            valor_formatado = f'${valor_numero}/s'
        
        brainrot = Brainrot(
            nome=data.get('nome'),
            foto=data.get('foto', ''),
            raridade=data.get('raridade', 'Comum'),
            valor_formatado=valor_formatado,
            valor_por_segundo=float(data.get('valor_por_segundo', 0)),
            quantidade=int(data.get('quantidade', 1)),
            numero_mutacoes=int(data.get('numero_mutacoes', 0))
        )
        
        # Eventos - lista de eventos selecionados
        eventos_list = data.get('eventos', [])
        if eventos_list:
            brainrot.set_eventos(eventos_list)
        else:
            brainrot.set_eventos([])
        
        # Campos personalizados - SEMPRE atualizar (mesmo se vazio, para permitir remoção)
        campos_pers = data.get('campos_personalizados', {})
        # Se campos_pers for None, não definir. Se for dict (mesmo vazio), definir.
        if campos_pers is not None:
            brainrot.set_campos_personalizados(campos_pers)
        
        db.session.add(brainrot)
        
        # Associar contas (verificando espaços disponíveis)
        conta_ids = data.get('contas', [])
        if conta_ids and len(conta_ids) > 0:
            try:
                contas = Conta.query.filter(Conta.id.in_(conta_ids)).all()
                # Verificar se todas as contas têm espaço disponível
                contas_sem_espaco = [c.nome for c in contas if not c.tem_espaco_disponivel()]
                if contas_sem_espaco:
                    return jsonify({
                        'success': False, 
                        'error': f'As seguintes contas estão cheias: {", ".join(contas_sem_espaco)}'
                    }), 400
                brainrot.contas = contas
            except Exception as e:
                print(f"AVISO: Erro ao associar contas: {e}")
                # Continuar mesmo se não conseguir associar contas
        
        db.session.commit()
        
        return jsonify({'success': True, 'brainrot': brainrot.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = str(e)
        print(f"ERRO ao criar Brainrot: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 400

@app.route('/api/brainrots/<int:id>', methods=['PUT'])
@login_required
def api_brainrot_update(id):
    """API para atualizar Brainrot"""
    try:
        brainrot = Brainrot.query.get_or_404(id)
        data = request.get_json()
        
        brainrot.nome = data.get('nome', brainrot.nome)
        brainrot.foto = data.get('foto', brainrot.foto)
        brainrot.raridade = data.get('raridade', brainrot.raridade)
        
        # Atualizar valor formatado
        valor_formatado = data.get('valor_formatado', '')
        if valor_formatado:
            brainrot.valor_formatado = valor_formatado
        else:
            valor_numero = data.get('valor_por_segundo', brainrot.valor_por_segundo)
            brainrot.valor_formatado = f'${valor_numero}/s'
        
        brainrot.valor_por_segundo = float(data.get('valor_por_segundo', brainrot.valor_por_segundo))
        brainrot.quantidade = int(data.get('quantidade', brainrot.quantidade))
        brainrot.numero_mutacoes = int(data.get('numero_mutacoes', brainrot.numero_mutacoes))
        
        # Atualizar eventos
        eventos_list = data.get('eventos', None)
        if eventos_list is not None:
            brainrot.set_eventos(eventos_list)
        
        # Campos personalizados - SEMPRE atualizar (mesmo se vazio, para permitir remoção)
        campos_pers = data.get('campos_personalizados', {})
        # Se campos_pers for None, manter os existentes. Se for dict (mesmo vazio), atualizar.
        if campos_pers is not None:
            brainrot.set_campos_personalizados(campos_pers)
        
        # Atualizar contas
        conta_ids = data.get('contas', [])
        if conta_ids is not None:
            contas = Conta.query.filter(Conta.id.in_(conta_ids)).all()
            brainrot.contas = contas
        
        db.session.commit()
        
        return jsonify({'success': True, 'brainrot': brainrot.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/brainrots/reorder', methods=['POST'])
@login_required
def api_brainrots_reorder():
    """API para reordenar Brainrots via drag-and-drop"""
    try:
        data = request.get_json()
        brainrot_orders = data.get('orders', [])  # Lista de [{id: 1, ordem: 0}, ...]
        
        if not brainrot_orders:
            return jsonify({'success': False, 'error': 'Nenhuma ordem fornecida'}), 400
        
        # Atualizar ordem de cada Brainrot
        for item in brainrot_orders:
            brainrot_id = item.get('id')
            nova_ordem = item.get('ordem', 0)
            
            brainrot = Brainrot.query.get(brainrot_id)
            if brainrot:
                brainrot.ordem = nova_ordem
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Ordem atualizada com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = str(e)
        print(f"ERRO ao reordenar Brainrots: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 400

@app.route('/api/brainrots/buscar-por-nome', methods=['GET'])
@login_required
def api_brainrot_buscar_por_nome():
    """API para buscar brainrot por nome e retornar raridade sugerida"""
    nome = request.args.get('nome', '', type=str)
    if not nome:
        return jsonify({'success': False, 'error': 'Nome não fornecido'}), 400
    
    # Buscar brainrots com o mesmo nome
    brainrots = Brainrot.query.filter(Brainrot.nome.ilike(f'%{nome}%')).all()
    
    if brainrots:
        # Retornar a raridade mais comum ou a primeira encontrada
        raridades = [br.raridade for br in brainrots]
        raridade_sugerida = max(set(raridades), key=raridades.count) if raridades else brainrots[0].raridade
        
        return jsonify({
            'success': True,
            'raridade_sugerida': raridade_sugerida,
            'encontrados': len(brainrots)
        })
    
    return jsonify({'success': True, 'raridade_sugerida': None, 'encontrados': 0})

@app.route('/api/brainrots/<int:id>/copiar', methods=['GET'])
@login_required
def api_brainrot_copiar(id):
    """API para copiar dados de um brainrot existente"""
    try:
        brainrot = Brainrot.query.get_or_404(id)
        dados = brainrot.to_dict()
        # Remover id e data_criacao para criar novo
        dados.pop('id', None)
        dados.pop('data_criacao', None)
        return jsonify({'success': True, 'dados': dados})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/brainrots/<int:id>', methods=['DELETE'])
@login_required
def api_brainrot_delete(id):
    """API para deletar Brainrot"""
    try:
        brainrot = Brainrot.query.get_or_404(id)
        db.session.delete(brainrot)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/contas', methods=['GET'])
@login_required
def api_contas_list():
    """API para listar Contas com busca"""
    busca = request.args.get('busca', '', type=str)
    
    query = Conta.query
    
    # Aplicar filtro de busca se fornecido
    if busca:
        query = query.filter(Conta.nome.ilike(f'%{busca}%'))
    
    # Sempre ordenar por nome alfabeticamente
    contas = query.order_by(Conta.nome.asc()).all()
    return jsonify([conta.to_dict() for conta in contas])

@app.route('/api/contas', methods=['POST'])
@login_required
def api_conta_create():
    """API para criar Conta"""
    try:
        data = request.get_json()
        nome = data.get('nome', '').strip()
        
        # Verificar se já existe uma conta com o mesmo nome
        conta_existente = Conta.query.filter_by(nome=nome).first()
        if conta_existente:
            return jsonify({
                'success': False, 
                'error': f'Já existe uma conta com o nome "{nome}". Por favor, escolha outro nome.'
            }), 400
        
        conta = Conta(
            nome=nome,
            roblox_id=data.get('roblox_id', ''),
            espacos=int(data.get('espacos', 0)) or 0
        )
        
        db.session.add(conta)
        
        # Associar brainrots
        brainrot_ids = data.get('brainrots', [])
        if brainrot_ids and len(brainrot_ids) > 0:
            try:
                brainrots = Brainrot.query.filter(Brainrot.id.in_(brainrot_ids)).all()
                conta.brainrots = brainrots
            except Exception as e:
                print(f"AVISO: Erro ao associar brainrots: {e}")
                # Continuar mesmo se não conseguir associar brainrots
        
        db.session.commit()
        
        return jsonify({'success': True, 'conta': conta.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        import traceback
        error_msg = str(e)
        print(f"ERRO ao criar Conta: {error_msg}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': error_msg}), 400

@app.route('/api/contas/<int:id>', methods=['PUT'])
@login_required
def api_conta_update(id):
    """API para atualizar Conta"""
    try:
        conta = Conta.query.get_or_404(id)
        data = request.get_json()
        novo_nome = data.get('nome', conta.nome).strip()
        
        # Verificar se já existe outra conta com o mesmo nome (exceto a atual)
        if novo_nome != conta.nome:
            conta_existente = Conta.query.filter_by(nome=novo_nome).first()
            if conta_existente and conta_existente.id != conta.id:
                return jsonify({
                    'success': False, 
                    'error': f'Já existe uma conta com o nome "{novo_nome}". Por favor, escolha outro nome.'
                }), 400
        
        conta.nome = novo_nome
        conta.roblox_id = data.get('roblox_id', conta.roblox_id)
        conta.espacos = int(data.get('espacos', conta.espacos)) or 0
        
        # Atualizar brainrots (verificando espaços disponíveis)
        brainrot_ids = data.get('brainrots', [])
        if brainrot_ids is not None:
            brainrots = Brainrot.query.filter(Brainrot.id.in_(brainrot_ids)).all()
            # Verificar se há espaço suficiente
            if conta.espacos > 0 and len(brainrots) > conta.espacos:
                return jsonify({
                    'success': False, 
                    'error': f'A conta tem apenas {conta.espacos} espaço(s), mas você está tentando associar {len(brainrots)} brainrot(s).'
                }), 400
            conta.brainrots = brainrots
        
        db.session.commit()
        
        return jsonify({'success': True, 'conta': conta.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/contas/<int:id>', methods=['DELETE'])
@login_required
def api_conta_delete(id):
    """API para deletar Conta"""
    try:
        conta = Conta.query.get_or_404(id)
        db.session.delete(conta)
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/campos-personalizados', methods=['GET'])
def api_campos_personalizados_list():
    """API para listar campos personalizados"""
    campos = CampoPersonalizado.query.all()
    return jsonify([campo.to_dict() for campo in campos])

@app.route('/api/campos-personalizados', methods=['POST'])
@login_required
def api_campo_personalizado_create():
    """API para criar campo personalizado"""
    try:
        data = request.get_json()
        
        campo = CampoPersonalizado(
            nome=data.get('nome'),
            tipo=data.get('tipo', 'texto'),
            descricao=data.get('descricao', '')
        )
        
        db.session.add(campo)
        db.session.commit()
        
        return jsonify({'success': True, 'campo': campo.to_dict()}), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_file():
    """API para upload de imagens"""
    if 'file' not in request.files:
        return jsonify({'success': False, 'error': 'Nenhum arquivo enviado'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'Nenhum arquivo selecionado'}), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Adicionar timestamp para evitar conflitos
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'url': url_for('uploaded_file', filename=filename)
        })
    
    return jsonify({'success': False, 'error': 'Tipo de arquivo não permitido'}), 400

@app.route('/uploads/<filename>')
@login_required
def uploaded_file(filename):
    """Serve arquivos enviados"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

