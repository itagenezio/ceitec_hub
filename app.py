"""
CEITEC HUB - Plataforma Educacional Integrada
Desenvolvido para o Centro de Inovação em Tecnologia e Educação do Ceará
"""

from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from models import Database

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'ceitec-hub-secret-key-2024')

# Configuração de caminhos absolutos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static', 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Garantir que pasta de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = Database()

# ==================== DECORATORS ====================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def professor_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = db.get_user_by_id(session['user_id'])
        if not user or user['tipo'] != 'professor':
            flash('Acesso restrito a professores.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        nome = request.form['nome']
        senha = request.form['senha']
        
        user = db.authenticate(nome, senha)
        if user:
            session['user_id'] = user['id']
            session['user_name'] = user['nome']
            session['user_type'] = user['tipo']
            flash(f'Bem-vindo, {user["nome"]}!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Nome ou senha incorretos.', 'danger')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nome = request.form['nome']
        escola = request.form['escola']
        serie = request.form['serie']
        senha = request.form['senha']
        tipo = request.form['tipo']
        
        if db.create_user(nome, escola, serie, senha, tipo):
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Nome de usuário já existe.', 'danger')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('Você saiu do sistema.', 'info')
    return redirect(url_for('login'))

# ==================== DASHBOARD ====================

@app.route('/dashboard')
@login_required
def dashboard():
    user = db.get_user_by_id(session['user_id'])
    pontuacao_total = db.get_pontuacao_total(session['user_id'])
    
    # Estatísticas para o dashboard
    stats = {
        'matematica': db.get_pontuacao_modulo(session['user_id'], 'matematica'),
        'avaliacao_ia': db.get_pontuacao_modulo(session['user_id'], 'avaliacao_ia'),
        'robotica': db.get_pontuacao_modulo(session['user_id'], 'robotica'),
        'total': pontuacao_total
    }
    
    return render_template('dashboard.html', user=user, stats=stats)

# ==================== MÓDULO MATEMÁTICA ====================

@app.route('/matematica')
@login_required
def matematica():
    return render_template('matematica.html')

@app.route('/matematica/questao', methods=['POST'])
@login_required
def gerar_questao():
    import random
    
    nivel = request.json.get('nivel', 'facil')
    
    # Configurações por nível
    configs = {
        'facil': {'max_num': 10, 'operacoes': ['+', '-'], 'pontos': 10},
        'medio': {'max_num': 50, 'operacoes': ['+', '-', '*'], 'pontos': 20},
        'dificil': {'max_num': 100, 'operacoes': ['+', '-', '*', '/'], 'pontos': 30}
    }
    
    config = configs.get(nivel, configs['facil'])
    operacao = random.choice(config['operacoes'])
    
    if operacao == '+':
        a, b = random.randint(1, config['max_num']), random.randint(1, config['max_num'])
        resposta = a + b
        questao = f"{a} + {b} = ?"
    elif operacao == '-':
        a, b = random.randint(1, config['max_num']), random.randint(1, config['max_num'])
        a, b = max(a, b), min(a, b)  # Evitar negativos
        resposta = a - b
        questao = f"{a} - {b} = ?"
    elif operacao == '*':
        a, b = random.randint(2, 12), random.randint(2, 12)
        resposta = a * b
        questao = f"{a} × {b} = ?"
    else:  # divisão
        b = random.randint(2, 10)
        resposta = random.randint(2, 10)
        a = b * resposta
        questao = f"{a} ÷ {b} = ?"
    
    # Armazenar resposta correta na sessão temporariamente
    session['resposta_atual'] = resposta
    session['pontos_questao'] = config['pontos']
    session['nivel_atual'] = nivel
    
    return jsonify({
        'questao': questao,
        'nivel': nivel,
        'pontos': config['pontos']
    })

@app.route('/matematica/responder', methods=['POST'])
@login_required
def responder_questao():
    resposta_usuario = request.json.get('resposta')
    resposta_correta = session.get('resposta_atual')
    pontos = session.get('pontos_questao', 0)
    nivel = session.get('nivel_atual', 'facil')
    
    if resposta_usuario == resposta_correta:
        # Salvar no banco
        db.salvar_resultado_matematica(session['user_id'], nivel, pontos)
        return jsonify({
            'correto': True,
            'mensagem': 'Resposta correta! 🎉',
            'pontos_ganhos': pontos
        })
    else:
        return jsonify({
            'correto': False,
            'mensagem': f'Resposta incorreta. A resposta certa era {resposta_correta}.',
            'pontos_ganhos': 0
        })

@app.route('/matematica/ranking')
@login_required
def ranking_matematica():
    ranking_geral = db.get_ranking_geral()
    user = db.get_user_by_id(session['user_id'])
    ranking_escola = db.get_ranking_por_escola(user['escola'])
    
    return jsonify({
        'geral': ranking_geral,
        'escola': ranking_escola,
        'minha_escola': user['escola']
    })

# ==================== MÓDULO AVALIAÇÃO IA ====================

@app.route('/avaliacao-ia')
@login_required
def avaliacao_ia():
    return render_template('avaliacao_ia.html')

@app.route('/avaliacao-ia/submeter', methods=['POST'])
@login_required
def submeter_avaliacao():
    texto = request.json.get('texto', '')
    tema = request.json.get('tema', 'Tecnologia e Educação')
    
    # Motor de avaliação interno (sem API externa)
    resultado = avaliar_texto_ia(texto, tema)
    
    # Salvar no banco
    db.salvar_avaliacao_ia(
        session['user_id'], 
        texto, 
        resultado['nivel'], 
        resultado['feedback']
    )
    
    return jsonify(resultado)

def avaliar_texto_ia(texto, tema):
    """
    Motor de IA interno para avaliação de textos
    Baseado em critérios objetivos e análise de padrões
    """
    texto_lower = texto.lower()
    palavras = texto.split()
    num_palavras = len(palavras)
    num_frases = texto.count('.') + texto.count('!') + texto.count('?')
    num_frases = max(1, num_frases)
    
    # Palavras-chave por tema
    palavras_chave = {
        'tecnologia': ['computador', 'software', 'hardware', 'internet', 'digital', 
                      'programação', 'código', 'algoritmo', 'dados', 'sistema'],
        'educacao': ['aprendizado', 'ensino', 'escola', 'conhecimento', 'estudo',
                    'pedagogia', 'curriculum', 'aluno', 'professor', 'sala de aula'],
        'robotica': ['arduino', 'sensor', 'motor', 'automação', 'robô', 
                    'circuito', 'programação', 'engenharia', 'maker'],
        'ia': ['inteligência artificial', 'machine learning', 'rede neural', 
               'algoritmo', 'automação', 'dados', 'predição', 'modelo']
    }
    
    # Critérios de avaliação
    pontuacao = 0
    feedback_detalhado = []
    
    # 1. Tamanho mínimo (até 30 pontos)
    if num_palavras >= 100:
        pontuacao += 30
        feedback_detalhado.append("✅ Texto com extensão excelente (100+ palavras)")
    elif num_palavras >= 50:
        pontuacao += 20
        feedback_detalhado.append("⚠️ Texto com boa extensão, mas pode ser mais detalhado")
    elif num_palavras >= 20:
        pontuacao += 10
        feedback_detalhado.append("❌ Texto muito curto. Desenvolva mais suas ideias.")
    else:
        feedback_detalhado.append("❌ Texto insuficiente. Mínimo recomendado: 20 palavras.")
    
    # 2. Uso de palavras-chave (até 40 pontos)
    palavras_encontradas = []
    for categoria, keywords in palavras_chave.items():
        for palavra in keywords:
            if palavra in texto_lower:
                palavras_encontradas.append(palavra)
    
    num_keywords = len(set(palavras_encontradas))
    if num_keywords >= 5:
        pontuacao += 40
        feedback_detalhado.append(f"✅ Excelente uso de vocabulário técnico ({num_keywords} termos relevantes)")
    elif num_keywords >= 3:
        pontuacao += 25
        feedback_detalhado.append(f"⚠️ Bom vocabulário, mas pode incluir mais termos técnicos ({num_keywords} encontrados)")
    else:
        feedback_detalhado.append(f"❌ Poucos termos técnicos. Tente incluir conceitos específicos do tema.")
    
    # 3. Estrutura lógica (até 30 pontos)
    palavras_conectivas = ['porque', 'portanto', 'assim', 'além disso', 'contudo', 
                          'entretanto', 'logo', 'consequentemente', 'primeiro', 'finalmente']
    conectivos_encontrados = sum(1 for p in palavras_conectivas if p in texto_lower)
    
    media_palavras_frase = num_palavras / num_frases
    
    if conectivos_encontrados >= 3 and media_palavras_frase >= 8:
        pontuacao += 30
        feedback_detalhado.append("✅ Excelente estrutura lógica e coesão textual")
    elif conectivos_encontrados >= 1:
        pontuacao += 15
        feedback_detalhado.append("⚠️ Estrutura adequada, mas pode melhorar a conexão entre ideias")
    else:
        feedback_detalhado.append("❌ Use mais conectivos para melhorar a coesão do texto")
    
    # Classificação final
    if pontuacao >= 80:
        nivel = "Avançado"
        mensagem = "Parabéns! Você demonstrou domínio excepcional do tema."
    elif pontuacao >= 60:
        nivel = "Proficiente"
        mensagem = "Muito bom! Você tem boa compreensão do assunto."
    elif pontuacao >= 40:
        nivel = "Intermediário"
        mensagem = "Bom começo! Há espaço para aprofundar seus conhecimentos."
    else:
        nivel = "Iniciante"
        mensagem = "Continue estudando! Tente desenvolver mais suas respostas."
    
    return {
        'nivel': nivel,
        'pontuacao': pontuacao,
        'feedback': mensagem,
        'detalhes': feedback_detalhado,
        'estatisticas': {
            'palavras': num_palavras,
            'frases': num_frases,
            'termos_tecnicos': num_keywords
        }
    }

# ==================== MÓDULO ROBÓTICA ====================

@app.route('/robotica')
@login_required
def robotica():
    return render_template('robotica.html')

@app.route('/robotica/cadastrar', methods=['POST'])
@login_required
def cadastrar_projeto():
    titulo = request.form['titulo']
    descricao = request.form['descricao']
    area = request.form['area']
    nivel = request.form['nivel']
    
    # Processar imagem
    imagem_path = None
    if 'imagem' in request.files:
        imagem = request.files['imagem']
        if imagem.filename:
            filename = secure_filename(f"{session['user_id']}_{datetime.now().strftime('%Y%m%d%H%M%S')}_{imagem.filename}")
            imagem_path = os.path.join('uploads', filename)
            imagem.save(os.path.join('static', imagem_path))
    
    # Calcular nota baseada nos critérios (simulação de avaliação)
    nota = calcular_nota_projeto(descricao, area, nivel)
    
    projeto_id = db.cadastrar_projeto(
        session['user_id'], titulo, descricao, area, nivel, nota, imagem_path
    )
    
    flash(f'Projeto cadastrado com sucesso! Nota: {nota}/100', 'success')
    return redirect(url_for('galeria_robotica'))

def calcular_nota_projeto(descricao, area, nivel):
    """Avaliação automática baseada em critérios objetivos"""
    nota = 50  # Base
    
    # Critério: Criatividade (baseado na originalidade da descrição)
    palavras_unicas = len(set(descricao.lower().split()))
    if palavras_unicas > 20:
        nota += 15
    elif palavras_unicas > 10:
        nota += 8
    
    # Critério: Complexidade técnica
    niveis = {'iniciante': 5, 'intermediario': 15, 'avancado': 25}
    nota += niveis.get(nivel, 5)
    
    # Critério: Aplicação de programação
    termos_tecnicos = ['código', 'programa', 'sensor', 'algoritmo', 'loop', 
                      'condição', 'variável', 'função', 'biblioteca']
    count_tecnicos = sum(1 for termo in termos_tecnicos if termo in descricao.lower())
    nota += min(count_tecnicos * 3, 15)
    
    return min(nota, 100)

@app.route('/robotica/galeria')
@login_required
def galeria_robotica():
    projetos = db.get_projetos_robotica()
    return render_template('robotica_galeria.html', projetos=projetos)

# ==================== MÓDULO RELATÓRIOS ====================

@app.route('/relatorios')
@login_required
def relatorios():
    user = db.get_user_by_id(session['user_id'])
    
    # Dados para gráficos
    dados_matematica = db.get_historico_matematica(session['user_id'])
    dados_avaliacao = db.get_historico_avaliacoes(session['user_id'])
    dados_robotica = db.get_historico_robotica(session['user_id'])
    
    # Ranking do aluno
    posicao_geral = db.get_posicao_ranking(session['user_id'])
    
    context = {
        'user': user,
        'pontuacao_total': db.get_pontuacao_total(session['user_id']),
        'dados_matematica': dados_matematica,
        'dados_avaliacao': dados_avaliacao,
        'dados_robotica': dados_robotica,
        'posicao_ranking': posicao_geral,
        'total_alunos': db.get_total_alunos()
    }
    
    return render_template('relatorios.html', **context)

@app.route('/relatorios/professor')
@login_required
@professor_required
def relatorios_professor():
    """Dashboard exclusivo para professores"""
    estatisticas_gerais = db.get_estatisticas_gerais()
    desempenho_escolas = db.get_desempenho_por_escola()
    
    return render_template('relatorios_professor.html', 
                         stats=estatisticas_gerais,
                         escolas=desempenho_escolas)

# ==================== API AUXILIARES ====================

@app.route('/api/pontuacao')
@login_required
def api_pontuacao():
    return jsonify({
        'total': db.get_pontuacao_total(session['user_id']),
        'matematica': db.get_pontuacao_modulo(session['user_id'], 'matematica'),
        'avaliacao_ia': db.get_pontuacao_modulo(session['user_id'], 'avaliacao_ia'),
        'robotica': db.get_pontuacao_modulo(session['user_id'], 'robotica')
    })

if __name__ == '__main__':
    db.init_db()
    app.run(debug=True, host='0.0.0.0', port=5000)
