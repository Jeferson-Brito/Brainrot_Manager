from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

# Credenciais fixas do sistema
ADMIN_EMAIL = "jeffersonbrito2455@gmail.com"
ADMIN_PASSWORD = "jeferson123"  # Será hasheado na primeira execução

class User(UserMixin):
    """Classe de usuário para autenticação"""
    def __init__(self, id, email, password_hash):
        self.id = id
        self.email = email
        self.password_hash = password_hash
    
    def check_password(self, password):
        """Verifica se a senha está correta"""
        return check_password_hash(self.password_hash, password)

def get_user():
    """Retorna o usuário administrador"""
    # Hash da senha jeferson123 (gerado uma vez)
    password_hash = generate_password_hash(ADMIN_PASSWORD)
    return User(id=1, email=ADMIN_EMAIL, password_hash=password_hash)

