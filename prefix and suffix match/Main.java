class WordFilter {

    private static class TrieNode {
        TrieNode[] children;
        int weight;

        TrieNode() {
            // 26 lowercase English letters ('a'-'z') + 1 slot for '#'
            this.children = new TrieNode[27];
            this.weight = -1;
        }
    }

    private final TrieNode root;

    private int getIndex(char ch) {
        return (ch == '#') ? 26 : (ch - 'a');
    }

    public WordFilter(String[] words) {
        this.root = new TrieNode();

        for (int idx = 0; idx < words.length; idx++) {
            String word = words[idx];
            int wordLen = word.length();
            String base = word + '#' + word;

            for (int i = 0; i <= wordLen; i++) {
                TrieNode curr = root;
                curr.weight = idx;

                for (int j = i; j < base.length(); j++) {
                    int cIdx = getIndex(base.charAt(j));
                    if (curr.children[cIdx] == null) {
                        curr.children[cIdx] = new TrieNode();
                    }
                    curr = curr.children[cIdx];
                    curr.weight = idx;
                }
            }
        }
    }

    public int f(String pref, String suff) {
        String target = suff + '#' + pref;
        TrieNode curr = root;

        for (int i = 0; i < target.length(); i++) {
            int cIdx = getIndex(target.charAt(i));
            if (curr.children[cIdx] == null) {
                return -1;
            }
            curr = curr.children[cIdx];
        }

        return curr.weight;
    }
}