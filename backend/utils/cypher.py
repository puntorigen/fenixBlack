from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
import base64, os, json
from hashlib import sha256

secret = os.getenv("SERVER_SECRET","super_default_secret")
 
def get_encryption_key(user_id: str):
    return sha256((user_id + secret).encode()).digest()[:32]

def get_encryption_key_base64(user_id: str):
    key_bytes = get_encryption_key(user_id)  # This should return the raw bytes
    inbase64 = base64.b64encode(key_bytes).decode('utf-8')  # Encode bytes to a Base64 string
    return inbase64

def decryptJSON(encrypted_data: str, user_id: str): 
    try:
        encryption_key = get_encryption_key(user_id)
        b64 = base64.b64decode(encrypted_data)
        if len(b64) % 16 != 0:
            print("Encrypted data is not a multiple of the block size. Length: ", len(b64))
        iv = b64[:AES.block_size]
        cipher_text = b64[AES.block_size:] 
        cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
        decrypted = unpad(cipher.decrypt(cipher_text), AES.block_size)
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        print(f"An error occurred during decryption: {str(e)}")
        return None

# encrypt version - 28-jun-24
def encryptJSON(data: dict, user_id: str):
    try:
        # Convert the data to a JSON string and then to bytes
        data_bytes = json.dumps(data).encode('utf-8')
        encryption_key = get_encryption_key(user_id)
        iv = os.urandom(AES.block_size)
        cipher = AES.new(encryption_key, AES.MODE_CBC, iv)
        cipher_text = cipher.encrypt(pad(data_bytes, AES.block_size))
        iv_cipher_text = iv + cipher_text
        encrypted_data = base64.b64encode(iv_cipher_text).decode('utf-8')
        return encrypted_data
    except Exception as e:
        print(f"An error occurred during encryption: {str(e)}")
        return None