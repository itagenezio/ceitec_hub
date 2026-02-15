"""
Modelos e operações do banco de dados SQLite
"""

import sqlite3
import hashlib
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, 'database.db')

class Database:
    def __init__(self, db_path=None):
        self.db_path = db_path or DATABASE
    
    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_db(self):
        """Inicializa o banco de dados com todas as tabelas"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabela de usuários
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT UNIQUE NOT NULL,
                escola TEXT NOT NULL,
                serie TEXT NOT NULL,
                senha_hash TEXT NOT NULL,
                tipo TEXT CHECK(tipo IN ('aluno', 'professor')) NOT NULL,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabela de resultados de matemática
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS resultados_matematica (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                nivel TEXT CHECK(nivel IN ('facil', 'medio', 'dificil')) NOT NULL,
                pontuacao INTEGER NOT NULL,
                data_jogo TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabela de avaliações IA
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS avaliacoes_ia (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                texto TEXT NOT NULL,
                nivel_classificacao TEXT CHECK(nivel_classificacao IN 
                    ('Iniciante', 'Intermediário', 'Proficiente', 'Avançado')) NOT NULL,
                feedback TEXT NOT NULL,
                pontuacao INTEGER,
                data_avaliacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Tabela de projetos de robótica
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projetos_robotica (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                titulo TEXT NOT NULL,
                descricao TEXT NOT NULL,
                area TEXT CHECK(area IN ('Arduino', 'Scratch', 'IA', 'Maker')) NOT NULL,
                nivel TEXT CHECK(nivel IN ('iniciante', 'intermediario', 'avancado')) NOT NULL,
                nota INTEGER CHECK(nota >= 0 AND nota <= 100),
                imagem TEXT,
                data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    
    # ==================== OPERAÇÕES DE USUÁRIO ====================
    
    def hash_senha(self, senha):
        """Cria hash seguro da senha"""
        return hashlib.sha256(senha.encode()).hexdigest()
    
    def create_user(self, nome, escola, serie, senha, tipo):
        """Cria novo usuário"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            senha_hash = self.hash_senha(senha)
            
            cursor.execute('''
                INSERT INTO usuarios (nome, escola, serie, senha_hash, tipo)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, escola, serie, senha_hash, tipo))
            
            conn.commit()
            conn.close()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def authenticate(self, nome, senha):
        """Autentica usuário"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        senha_hash = self.hash_senha(senha)
        
        cursor.execute('''
            SELECT * FROM usuarios 
            WHERE nome = ? AND senha_hash = ?
        ''', (nome, senha_hash))
        
        user = cursor.fetchone()
        conn.close()
        
        return dict(user) if user else None
    
    def get_user_by_id(self, user_id):
        """Busca usuário por ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,))
        user = cursor.fetchone()
        
        conn.close()
        return dict(user) if user else None
    
    # ==================== OPERAÇÕES MATEMÁTICA ====================
    
    def salvar_resultado_matematica(self, usuario_id, nivel, pontuacao):
        """Salva resultado de jogo matemático"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO resultados_matematica (usuario_id, nivel, pontuacao)
            VALUES (?, ?, ?)
        ''', (usuario_id, nivel, pontuacao))
        
        conn.commit()
        conn.close()
    
    def get_ranking_geral(self, limit=10):
        """Retorna ranking geral dos alunos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.nome, u.escola, 
                   COALESCE(SUM(r.pontuacao), 0) as total_pontos,
                   COUNT(r.id) as questoes_respondidas
            FROM usuarios u
            LEFT JOIN resultados_matematica r ON u.id = r.usuario_id
            WHERE u.tipo = 'aluno'
            GROUP BY u.id
            ORDER BY total_pontos DESC
            LIMIT ?
        ''', (limit,))
        
        ranking = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ranking
    
    def get_ranking_por_escola(self, escola, limit=10):
        """Retorna ranking de uma escola específica"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.nome, u.serie,
                   COALESCE(SUM(r.pontuacao), 0) as total_pontos
            FROM usuarios u
            LEFT JOIN resultados_matematica r ON u.id = r.usuario_id
            WHERE u.escola = ? AND u.tipo = 'aluno'
            GROUP BY u.id
            ORDER BY total_pontos DESC
            LIMIT ?
        ''', (escola, limit))
        
        ranking = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return ranking
    
    # ==================== OPERAÇÕES AVALIAÇÃO IA ====================
    
    def salvar_avaliacao_ia(self, usuario_id, texto, nivel_classificacao, feedback, pontuacao=None):
        """Salva avaliação de texto"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Extrair pontuação do nível
        pontos_nivel = {'Iniciante': 25, 'Intermediário': 50, 'Proficiente': 75, 'Avançado': 100}
        pontuacao = pontuacao or pontos_nivel.get(nivel_classificacao, 0)
        
        cursor.execute('''
            INSERT INTO avaliacoes_ia (usuario_id, texto, nivel_classificacao, feedback, pontuacao)
            VALUES (?, ?, ?, ?, ?)
        ''', (usuario_id, texto, nivel_classificacao, feedback, pontuacao))
        
        conn.commit()
        conn.close()
    
    # ==================== OPERAÇÕES ROBÓTICA ====================
    
    def cadastrar_projeto(self, usuario_id, titulo, descricao, area, nivel, nota, imagem):
        """Cadastra projeto de robótica"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO projetos_robotica 
            (usuario_id, titulo, descricao, area, nivel, nota, imagem)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (usuario_id, titulo, descricao, area, nivel, nota, imagem))
        
        projeto_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return projeto_id
    
    def get_projetos_robotica(self, limit=50):
        """Retorna projetos para galeria"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT p.*, u.nome as autor, u.escola
            FROM projetos_robotica p
            JOIN usuarios u ON p.usuario_id = u.id
            ORDER BY p.nota DESC, p.data_cadastro DESC
            LIMIT ?
        ''', (limit,))
        
        projetos = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return projetos
    
    # ==================== RELATÓRIOS E ESTATÍSTICAS ====================
    
    def get_pontuacao_total(self, usuario_id):
        """Calcula pontuação total do aluno"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Pontos de matemática
        cursor.execute('''
            SELECT COALESCE(SUM(pontuacao), 0) FROM resultados_matematica 
            WHERE usuario_id = ?
        ''', (usuario_id,))
        pts_mat = cursor.fetchone()[0] or 0
        
        # Pontos de avaliação IA
        cursor.execute('''
            SELECT COALESCE(SUM(pontuacao), 0) FROM avaliacoes_ia 
            WHERE usuario_id = ?
        ''', (usuario_id,))
        pts_ia = cursor.fetchone()[0] or 0
        
        # Pontos de robótica
        cursor.execute('''
            SELECT COALESCE(SUM(nota), 0) FROM projetos_robotica 
            WHERE usuario_id = ?
        ''', (usuario_id,))
        pts_rob = cursor.fetchone()[0] or 0
        
        conn.close()
        return pts_mat + pts_ia + pts_rob
    
    def get_pontuacao_modulo(self, usuario_id, modulo):
        """Retorna pontuação específica por módulo"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if modulo == 'matematica':
            cursor.execute('''
                SELECT COALESCE(SUM(pontuacao), 0) FROM resultados_matematica 
                WHERE usuario_id = ?
            ''', (usuario_id,))
        elif modulo == 'avaliacao_ia':
            cursor.execute('''
                SELECT COALESCE(SUM(pontuacao), 0) FROM avaliacoes_ia 
                WHERE usuario_id = ?
            ''', (usuario_id,))
        elif modulo == 'robotica':
            cursor.execute('''
                SELECT COALESCE(SUM(nota), 0) FROM projetos_robotica 
                WHERE usuario_id = ?
            ''', (usuario_id,))
        else:
            return 0
        
        result = cursor.fetchone()[0] or 0
        conn.close()
        return result
    
    def get_historico_matematica(self, usuario_id):
        """Retorna histórico de atividades de matemática"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT nivel, pontuacao, data_jogo 
            FROM resultados_matematica 
            WHERE usuario_id = ?
            ORDER BY data_jogo DESC
            LIMIT 10
        ''', (usuario_id,))
        
        historico = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return historico
    
    def get_historico_avaliacoes(self, usuario_id):
        """Retorna histórico de avaliações IA"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT nivel_classificacao, pontuacao, data_avaliacao 
            FROM avaliacoes_ia 
            WHERE usuario_id = ?
            ORDER BY data_avaliacao DESC
            LIMIT 10
        ''', (usuario_id,))
        
        historico = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return historico
    
    def get_historico_robotica(self, usuario_id):
        """Retorna histórico de projetos"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT titulo, area, nota, data_cadastro 
            FROM projetos_robotica 
            WHERE usuario_id = ?
            ORDER BY data_cadastro DESC
        ''', (usuario_id,))
        
        historico = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return historico
    
    def get_posicao_ranking(self, usuario_id):
        """Retorna posição do aluno no ranking geral"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            WITH ranking AS (
                SELECT usuario_id, SUM(pontuacao) as total,
                       RANK() OVER (ORDER BY SUM(pontuacao) DESC) as posicao
                FROM resultados_matematica
                GROUP BY usuario_id
            )
            SELECT posicao FROM ranking WHERE usuario_id = ?
        ''', (usuario_id,))
        
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    
    def get_total_alunos(self):
        """Retorna total de alunos cadastrados"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM usuarios WHERE tipo = 'aluno'")
        total = cursor.fetchone()[0]
        conn.close()
        return total
    
    def get_estatisticas_gerais(self):
        """Estatísticas para dashboard do professor"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total de alunos e professores
        cursor.execute("SELECT tipo, COUNT(*) FROM usuarios GROUP BY tipo")
        stats['usuarios'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Total de atividades por módulo
        cursor.execute("SELECT COUNT(*) FROM resultados_matematica")
        stats['total_matematica'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM avaliacoes_ia")
        stats['total_avaliacoes'] = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM projetos_robotica")
        stats['total_projetos'] = cursor.fetchone()[0]
        
        # Média de desempenho
        cursor.execute("SELECT AVG(pontuacao) FROM resultados_matematica")
        stats['media_matematica'] = round(cursor.fetchone()[0] or 0, 2)
        
        conn.close()
        return stats
    
    def get_desempenho_por_escola(self):
        """Retorna desempenho agregado por escola"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.escola, 
                   COUNT(DISTINCT u.id) as total_alunos,
                   COALESCE(SUM(r.pontuacao), 0) as pontuacao_total
            FROM usuarios u
            LEFT JOIN resultados_matematica r ON u.id = r.usuario_id
            WHERE u.tipo = 'aluno'
            GROUP BY u.escola
            ORDER BY pontuacao_total DESC
        ''')
        
        escolas = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return escolas
