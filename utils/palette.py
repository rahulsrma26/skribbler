import numpy as np


def hex2bgr(code: str):
    code = code.lstrip('#')
    if code != 'none':
        return [int(code[i:i+2], 16) for i in (0, 2, 4)][::-1]
    return None


def bgr2hex(b: int, g:int, r:int):
    return f'#{r:02x}{g:02x}{b:02x}'


class Palette:
    def __init__(self, colors = [], name='Skribbl'):
        self.name = name
        self.colors = np.array(colors, dtype=np.uint8)
        self.pal = self.colors.astype(float) / 255.0


    def save(self, fname):
        with open(fname, 'w') as f:
            f.write(f'GIMP Palette\n')
            f.write(f'Name: {self.name}\n')
            f.write(f'# R   G   B Hex\n')
            for b, g, r in self.colors:
                f.write(f'{r:3} {g:3} {b:3} {bgr2hex(b,g,r)}\n')


    def nearest(self, col):
        flt = np.array(col, dtype=np.float) / 255.0
        flt = np.tile(flt, self.pal.shape[0]).reshape([-1, 3])
        return np.argmin(np.linalg.norm(flt - self.pal, axis=1))


    def __getitem__(self, idx):
        return self.colors[idx]


    @classmethod
    def from_file(cls, fname):
        colors, name = [], ''
        with open(fname, 'r') as f:
            if f.readline().strip() != 'GIMP Palette':
                return
            name = f.readline().split(':')[1].strip()
            for line in f:
                if not line.startswith('#'):
                    r, g, b = [int(x) for x in line.strip().split()[:3]]
                    colors.append([b, g, r])
        return cls(colors, name)
