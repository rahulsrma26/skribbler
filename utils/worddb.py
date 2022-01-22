import pandas as pd

class worddb:
    WORD = 'word'
    RANK = 'rank'
    FWD = 'fwd'
    CHARS = 'chars'
    WORDS = 'words'

    def __init__(self, filepath):
        self.df = self.load(filepath)

    def load(self, filepath):
        df = pd.read_csv(filepath, sep=',', dtype={
            self.RANK: int,
            self.WORD: str,
            self.FWD: str
        })
        df[self.WORD] = df[self.WORD].apply(lambda s:s.lower())
        df[self.FWD] = df[self.FWD].apply(lambda s:s.lower() if type(s) == str else '')
        df[self.CHARS] = df[self.WORD].apply(lambda s:len(s))
        df[self.WORDS] = df[self.WORD].apply(lambda s:len(s.split(' ')))
        return df

    def find(self, word):
        print(f'Searching for {word} ...')
        checks = []
        for i, v in enumerate(word):
            if v != '_':
                checks.append((i, v))
        if len(checks) > 2:
            print('too many characters')
            return
        df = self.df
        df = df[df[self.CHARS] == len(word)]
        df = df[df[self.WORDS] == len(word.split(' '))]
        result = []
        for _, match in df.iterrows():
            matched, s = True, match[self.WORD]
            for i, v in checks:
                if s[i] != v:
                    matched = False
                    break
            if matched:
                result.append(s)
        self.print(sorted(result))

    def print(self, words, columns=120):
        cols = columns // (len(words[0]) + 3)
        rows = (len(words) + cols - 1) // cols
        array = [[] for _ in range(rows)]
        for i, word in enumerate(words):
            array[i % rows].append(word)
        for row in array:
            for elem in row:
                print(elem, end=' | ')
            print()

    def rank(self, word):
        df = self.df
        match = df.loc[df[self.WORD] == word.lower()]
        if match[self.RANK].values:
            return match[self.RANK].values[0]
        print(f'!!! Error: word not found {word}')
        return 0


# worddb('resources/counts.txt').stats(['tie', 'cat'])
# worddb('resources/counts.txt').find('___b_')
worddb('resources/counts.txt').find('___')
