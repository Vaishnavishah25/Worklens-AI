# backend/auth/password.py
import bcrypt

def get_password_hash(password: str) -> str:
    """
    Generates a secure, native bcrypt password hash from a plain text string.
    """
    # 1. Convert the plain text string to bytes
    password_bytes = password.encode('utf-8')
    
    # 2. Generate a secure salt and hash the password
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password_bytes, salt)
    
    # 3. Decode back to a clean string format to store easily in PostgreSQL
    return hashed_password.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a plain text password against an existing database bcrypt hash string.
    """
    password_bytes = plain_password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    
    # Safely performs cryptographic time-constant comparison
    return bcrypt.checkpw(password_bytes, hashed_bytes)