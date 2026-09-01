import random
import string
from collections import defaultdict

class Codec:
    def __init__(self):
        self.alphabet = string.ascii_letters + string.digits
        self.long_to_short = defaultdict(str)
        self.short_to_long = defaultdict(str)
        self.base_URL = "http://tinyurl.com/"

    def _generate_code():
        code = "".join(random.choices(self.alphabet, k=6))
        return code
        
    def encode(self, longUrl: str) -> str:
        """Encodes a URL to a shortened URL.
        """
        if longUrl in self.long_to_short:
            return self.base_URL + self.long_to_short[longUrl]

        code = self._generate_code()
        while code in self.short_to_long:
            code = self._generate_code()

        self.long_to_short[longUrl] = code
        self.short_to_long[code] = longUrl

        return self.base_URL+code

    def decode(self, shortUrl: str) -> str:
        """Decodes a shortened URL to its original URL.
        """
        code = shortUrl.replace(self.base_URL, "")
        return self.short_to_long[code]