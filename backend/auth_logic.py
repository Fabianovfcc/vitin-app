from werkzeug.security import generate_password_hash, check_password_hash

def hash_pin(pin: str) -> str:
    """Gera um hash seguro para o PIN de 4 dígitos."""
    return generate_password_hash(pin)

def verify_pin(pin: str, hashed_pin: str) -> bool:
    """Verifica se o PIN inserido corresponde ao hash armazenado."""
    if not hashed_pin:
        return False
    return check_password_hash(hashed_pin, pin)

def format_phone(phone: str) -> str:
    """Formata o número de telefone para o padrão E.164 (ex: +55...)."""
    # Remove caracteres não numéricos
    clean_phone = ''.join(filter(str.isdigit, phone))
    
    # Se não começar com +, e tiver 10 ou 11 dígitos (Brasil), assume +55
    if len(clean_phone) <= 11 and not phone.startswith('+'):
        return f"+55{clean_phone}"
    
    # Se já tiver o código do país mas sem o +, adiciona
    if not phone.startswith('+'):
        return f"+{clean_phone}"
        
    return phone
