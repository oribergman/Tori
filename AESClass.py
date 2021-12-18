import base64
from Crypto.Cipher import AES
from Crypto import Random
import hashlib


class AESCipher(object):

    def __init__(self, key):
        """
        constructor to AESCipher
        :param key: the key to decrypt and encrypt (String)
        """
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw):
        """
        takes a string and encrypts it
        :param raw: msg (String)
        :return: the msg but encrypted
        """
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw.encode()))

    def decrypt(self, enc):
        """
        gets a msg and decrypts it
        :param enc: encrypted msg (Bytes)
        :return: decrypted msg
        """
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        """

        :param s: String
        :return: makes it 64 bits
        """
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    @staticmethod
    def _unpad(s):
        """

        :param s: String
        :return: returns the string to normal size of bits
        """
        return s[:-ord(s[len(s)-1:])]


