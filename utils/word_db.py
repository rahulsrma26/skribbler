from collections import defaultdict
import pandas as pd


class WordDB:
    WORD = 'word'
    RANK = 'rank'
    FWD = 'fwd'
    CHARS = 'chars'
    WORDS = 'words'
    IMAGE = 'image'


    def __init__(self, filepath):
        self.df = self.load(filepath)
        self.tree = self.build()


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
        def img(row):
            if row[self.FWD]:
                return row[self.FWD].lower() if row[self.FWD] != '!' else ''
            return row[self.WORD].lower()
        df[self.IMAGE] = df.apply(lambda row: img(row), axis=1)
        return df


    def words(self):
        return self.df[self.WORD].tolist()


    def build(self):
        tree = {c:defaultdict(list) for c in 'abcdefghijklmnopqrstuvwxyz -./'}
        for word in self.words():
            for i, c in enumerate(word):
                tree[c][i].append(word)
        return tree


    def find(self, word):
        print(f'Searching for {word} ...')
        df = self.df
        df = df[df[self.CHARS] == len(word)]
        df = df[df[self.WORDS] == len(word.split(' '))]
        possible = set(df[self.WORD].values)
        for i, c in enumerate(word):
            if c != '_':
                possible.intersection_update(set(self.tree[c][i]))
        self.print(sorted(list(possible)))


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


    def image(self, word):
        df = self.df
        match = df.loc[df[self.WORD] == word.lower()]
        if len(match[self.IMAGE].values):
            return match[self.IMAGE].values[0]
        print(f'!!! Error: word not found {word}')



# print(WordDB('resources/counts.txt').df)
# worddb('resources/counts.txt').stats(['tie', 'cat'])
# WordDB('resources/counts.txt').find('___b_')
# WordDB('resources/counts.txt').find('a__')
