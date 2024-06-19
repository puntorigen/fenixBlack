from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64, os, json
from hashlib import sha256

secret = os.getenv("SERVER_SECRET","super_default_secret")
 
def get_encryption_key(user_id: str):
    encryption_key = sha256((user_id + secret).encode()).hexdigest()
    return encryption_key

def decryptJSON(encrypted_data: str, user_id: str):
    try:
        encryption_key = get_encryption_key(user_id)
        b64 = base64.b64decode(encrypted_data)
        iv = b64[:AES.block_size]  # Extract the IV from the data
        cipher_text = b64[AES.block_size:]  # Extract the cipher text
        cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(cipher_text), AES.block_size)
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        print(f"An error occurred during decryption: {str(e)}")
        return None  # Return None or handle the error as needed