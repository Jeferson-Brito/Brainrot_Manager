from app import app, db, Brainrot, Conta, CampoPersonalizado, brainrot_conta
from flask import render_template, request, jsonify, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

# Lista de raridades disponíveis
RARIDADES = ['Comum', 'Raro', 'Épico', 'Lendário', 'Mítico', 'Deus Brainrot', 'Secreto', 'OG']

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ==================== ROTAS PRINCIPAIS ====================

@app.route('/')
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
def brainrots_list():
    """Lista todos os Brainrots"""
    return render_template('brainrots/list.html')

@app.route('/brainrots/novo')
def brainrot_new():
    """Página para criar novo Brainrot"""
    contas = Conta.query.all()
    campos_personalizados = CampoPersonalizado.query.all()
    return render_template('brainrots/form.html', 
                         brainrot=None, 
                         contas=contas,
                         campos_personalizados=campos_personalizados,
                         raridades=RARIDADES)

@app.route('/brainrots/<int:id>/editar')
def brainrot_edit(id):
    """Página para editar Brainrot"""
    brainrot = Brainrot.query.get_or_404(id)
    # Carregar contas associadas explicitamente
    contas_associadas = [c.id for c in brainrot.contas.all()]
    contas = Conta.query.all()
    campos_personalizados = CampoPersonalizado.query.all()
    return render_template('brainrots/form.html',
                         brainrot=brainrot,
                         contas=contas,
                         contas_associadas=contas_associadas,
                         campos_personalizados=campos_personalizados,
                         raridades=RARIDADES)

@app.route('/contas')
def contas_list():
    """Lista todas as Contas"""
    return render_template('contas/list.html')

@app.route('/contas/nova')
def conta_new():
    """Página para criar nova Conta"""
    brainrots = Brainrot.query.all()
    return render_template('contas/form.html', 
                         conta=None, 
                         brainrots=brainrots,
                         brainrots_associados=[])

@app.route('/contas/<int:id>/editar')
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
def conta_detail(id):
    """Página de detalhes da Conta"""
    conta = Conta.query.get_or_404(id)
    # Carregar brainrots explicitamente para o template
    brainrots = conta.brainrots.all()
    return render_template('contas/detail.html', conta=conta, brainrots=brainrots)

# ==================== API REST ====================

@app.route('/api/brainrots', methods=['GET'])
def api_brainrots_list():
    """API para listar Brainrots com busca e filtros"""
    # Parâmetros de busca e filtro
    busca = request.args.get('busca', '', type=str)
    raridade = request.args.get('raridade', '', type=str)
    valor_min = request.args.get('valor_min', type=float)
    valor_max = request.args.get('valor_max', type=float)
    quantidade_min = request.args.get('quantidade_min', type=int)
    quantidade_max = request.args.get('quantidade_max', type=int)
    mutacoes_min = request.args.get('mutacoes_min', type=int)
    mutacoes_max = request.args.get('mutacoes_max', type=int)
    conta_id = request.args.get('conta_id', type=int)
    
    # Query base
    query = Brainrot.query
    
    # Aplicar filtros
    if busca:
        query = query.filter(Brainrot.nome.ilike(f'%{busca}%'))
    if raridade:
        query = query.filter(Brainrot.raridade == raridade)
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
        br.ordem,
        br.data_criacao
    ))
    
    return jsonify([br.to_dict() for br in brainrots_ordenados])

@app.route('/api/brainrots', methods=['POST'])
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
        
        # Campos personalizados - SEMPRE atualizar (mesmo se vazio, para permitir remoção)
        campos_pers = data.get('campos_personalizados', {})
        # Se campos_pers for None, não definir. Se for dict (mesmo vazio), definir.
        if campos_pers is not None:
            brainrot.set_campos_personalizados(campos_pers)
        
        db.session.add(brainrot)
        
        # Associar contas
        conta_ids = data.get('contas', [])
        if conta_ids and len(conta_ids) > 0:
            try:
                contas = Conta.query.filter(Conta.id.in_(conta_ids)).all()
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

@app.route('/api/brainrots/<int:id>', methods=['DELETE'])
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
def api_contas_list():
    """API para listar Contas"""
    contas = Conta.query.all()
    return jsonify([conta.to_dict() for conta in contas])

@app.route('/api/contas', methods=['POST'])
def api_conta_create():
    """API para criar Conta"""
    try:
        data = request.get_json()
        
        conta = Conta(
            nome=data.get('nome'),
            roblox_id=data.get('roblox_id', '')
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
def api_conta_update(id):
    """API para atualizar Conta"""
    try:
        conta = Conta.query.get_or_404(id)
        data = request.get_json()
        
        conta.nome = data.get('nome', conta.nome)
        conta.roblox_id = data.get('roblox_id', conta.roblox_id)
        
        # Atualizar brainrots
        brainrot_ids = data.get('brainrots', [])
        if brainrot_ids is not None:
            brainrots = Brainrot.query.filter(Brainrot.id.in_(brainrot_ids)).all()
            conta.brainrots = brainrots
        
        db.session.commit()
        
        return jsonify({'success': True, 'conta': conta.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 400

@app.route('/api/contas/<int:id>', methods=['DELETE'])
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
def uploaded_file(filename):
    """Serve arquivos enviados"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

