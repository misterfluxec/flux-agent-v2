import bcrypt
hashed = bcrypt.hashpw(b'Admin2026!', bcrypt.gensalt()).decode()
print("HASH_IS:" + hashed)
