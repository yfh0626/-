# security/game_crypto.py
import os
import base62
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import hashes, serialization

'''
1. 初始化阶段
AI 部署：生成 RSA 密钥对（公/私钥）及一次性 AES 会话密钥。
公开承诺：界面展示 RSA 公钥 与 被 RSA 加密的 AES 密钥。
2. 对局回合
加密出招：AI 使用 AES 会话密钥 + 随机 Nonce，以 AES-CTR 模式 加密操作，之后玩家再出招。
3. 结算阶段
亮牌：游戏结束时，AI 公布 RSA 私钥。
可信验证：此时玩家可使用私钥解密 AES 密钥，再解密历史回合的所有短密文。
'''

class GameCryptoEngine:
    def __init__(self):
        self._private_key = None
        self.public_key = None
        self._session_aes_key = None
        
    def start_new_game(self) -> tuple[str, str]:
        """
        游戏初始化：生成RSA和AES，返回给UI公开的数据
        :return: (RSA公钥字符串, 被加密的AES密钥字符串)
        """
        self._private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self._private_key.public_key()
        self._session_aes_key = os.urandom(32)
        encrypted_aes_bytes = self.public_key.encrypt(
            self._session_aes_key,
            padding.OAEP(mgf=padding.MGF1(hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        )
        pub_key_pem = self.public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')
        
        encrypted_aes_str = base62.encodebytes(encrypted_aes_bytes)
        
        return pub_key_pem, encrypted_aes_str

    def commit_action(self, action_text: str) -> str:
        """
        每回合调用：将AI的操作变为密文
        :param action_text: AI操作明文
        :return: AI操作密文
        """
        raw_bytes = action_text.encode('utf-8')
        short_nonce = os.urandom(4) # 4字节随机数防重放
        full_nonce = b'\x00' * 12 + short_nonce
        
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        cipher = Cipher(algorithms.AES(self._session_aes_key), modes.CTR(full_nonce))
        encryptor = cipher.encryptor()
        ciphertext_bytes = encryptor.update(raw_bytes) + encryptor.finalize()
        return base62.encodebytes(short_nonce + ciphertext_bytes)

    def reveal_private_key(self) -> str:
        """
        游戏结束：亮出私钥底牌
        :return: RSA私匙
        """
        if not self._private_key:
            return ""
        priv_pem = self._private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        )
        return priv_pem.decode('utf-8')