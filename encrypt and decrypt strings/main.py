from typing import List
from collections import Counter

class Encrypter:
    def __init__(self, keys: List[str], values: List[str], dictionary: List[str]):
        self.key_to_val = {k: v for k, v in zip(keys, values)}

        encrypted_words = []
        for word in dictionary:
            enc = self.encrypt(word)
            if enc:
                encrypted_words.append(enc)
        self.encrypted_counts = Counter(encrypted_words)

    def encrypt(self, word1: str) -> str:
        res = []
        for ch in word1:
            if ch not in self.key_to_val:
                return ""
            res.append(self.key_to_val[ch])
        return "".join(res)

    def decrypt(self, word2: str) -> int:
        return self.encrypted_counts.get(word2, 0)        


# Your Encrypter object will be instantiated and called as such:
# obj = Encrypter(keys, values, dictionary)
# param_1 = obj.encrypt(word1)
# param_2 = obj.decrypt(word2)