from typing import List

class TrieNode:
    def __init__(self):
        self.children = {}
        self.weight = -1

class WordFilter:
    def __init__(self, words: List[str]):
        self.root = TrieNode()

        for idx, word in enumerate(words):
            word_len = len(word)
            base = word + '#' + word

            for i in range(word_len+1):
                curr = self.root
                curr.weight = idx

                for ch in base[i:]:
                    if ch not in curr.children:
                        curr.children[ch] = TrieNode()
                    curr = curr.children[ch]
                    curr.weight = idx

    def f(self, pref: str, suff: str) -> int:
        target = suff + '#' + pref
        curr = self.root

        for ch in target:
            if ch not in curr.children:
                return -1
            curr = curr.children[ch]
        return curr.weight

