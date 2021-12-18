from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP


class RSAClass:
    def __init__(self):
        self._keyPair = None
        self._generate_keys()

    def _generate_keys(self):
        '''
        no input.
        generate the RSA couple keys
        '''
        self._keyPair = RSA.generate(3072)


    def get_public_key_pem(self):
        '''
        export public key in PEM format
        :return:
        '''

        pubkey = self._keyPair.publickey()
        pubkeyPEM = pubkey.exportKey()
        return pubkeyPEM

    def decrypt_msg(self, encdata):
        '''
        decrypt the daya with the private key
        :param encdata: the encrypted message
        :return: the plaintext
        '''
        private_key = PKCS1_OAEP.new(self._keyPair)
        return private_key.decrypt(encdata)


def encrypt_msg(data, pubkeyPEM):
    '''
    encrypt message with the given public key
    :param data: the plain text in string
    :param pubkey: the public key
    :return: encrypted message
    '''
    result = None
    try:
        pubkey = RSA.import_key(pubkeyPEM)
    except Exception as e:
        print(e)
    else:
        encryptor = PKCS1_OAEP.new(pubkey)
        result = encryptor.encrypt(data.encode())
    return result



def main():
    pass
    # print("Hello World!")
    # hey = RSAClass()
if __name__ == "__main__":
    main()

