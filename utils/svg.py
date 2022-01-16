import math
import random
from xml.dom import minidom
from svgelements import Path, CubicBezier, Line, Move, Close


def hexcolor2RGB(code: str):
    code = code.lstrip('#')
    if code != 'none':
        return [int(code[i:i+2], 16) for i in (0, 2, 4)][::-1]
    return None


class SVGElement:
    def __init__(self, elem):
        self.elem = elem
        self.path = Path(elem.getAttribute("d"))
        self.style = dict([tuple(e.split(':')) for e in elem.getAttribute('style').split(';')])
        self.thickness = int(float(self.style['stroke-width']) * 1.2)
        self.color = hexcolor2RGB(self.style['stroke'])
        self.fill = hexcolor2RGB(self.style['fill'])

    def __str__(self):
        return str(self.path._segments)


class SVG:
    DIST_THRESHOLD = 100
    PIXEL_THRESHOLD = 20
    ANGLE_THRESHOLD = 0.3
    HUMAN_ERROR = 2

    def __init__(self, viewbox, paths) -> None:
        self.vb = viewbox
        self.left, self.top, self.right, self.bottom = [int(x) for x in self.vb.split()]
        self.paths = [SVGElement(p) for p in paths]

    def __str__(self) -> str:
        s = f'SVG {self.vb}'
        for path in self.paths:
            s += f'\n|- {path}'
        return s

    def _calc(self, p, t):
        ps = []
        for i in range(2):
            ps.append(((1-t)**3)*p[0][i] + 3*(1-t)*(1-t)*t*p[1][i] + 3*(1-t)*t*t*p[2][i] + (t**3)*p[3][i])
        return tuple([int(x) for x in ps])

    def _bz(self, pts, l, r):
        x1, y1 = self._calc(pts, l)
        m = (l + r) / 2
        x2, y2 = self._calc(pts, m)
        x2 = int(x2 + random.uniform(-self.HUMAN_ERROR, self.HUMAN_ERROR))
        y2 = int(y2 + random.uniform(-self.HUMAN_ERROR, self.HUMAN_ERROR))
        x2 = min(max(x2, self.left), self.right)
        y2 = min(max(y2, self.top), self.bottom)
        x3, y3 = self._calc(pts, r)
        split = False
        dist = math.dist((x1, y1), (x3, y3))
        if dist > self.DIST_THRESHOLD:
            # print('d', math.dist((x1, y1), (x3, y3)))
            split = True
        elif dist > self.PIXEL_THRESHOLD:
            a1 = math.atan2 (y1 - y2, x2 - x1)
            a2 = math.atan2 (y2 - y3, x3 - x2)
            if abs(a1 - a2) > self.ANGLE_THRESHOLD:
                # print('a', a1, a2, abs(a1 - a2))
                split = True
        if split:
            return self._bz(pts, l, m) + self._bz(pts, m, r)
        else:
            return [(x2, y2), (x3, y3)]

    def _ln(self, x1, y1, x2, y2):
        dist = math.dist((x1, y1), (x2, y2))
        if dist > self.DIST_THRESHOLD:
            xm = int((x1 + x2) / 2 + random.uniform(-self.HUMAN_ERROR, self.HUMAN_ERROR))
            ym = int((y1 + y2) / 2 + random.uniform(-self.HUMAN_ERROR, self.HUMAN_ERROR))
            xm = min(max(xm, self.left), self.right)
            ym = min(max(ym, self.top), self.bottom)
            return self._ln(x1, y1, xm, ym) + self._ln(xm, ym, x2, y2)
        else:
            return [(x2, y2)]

    def get_points(self, elem: SVGElement):
        for obj in elem.path:
            if isinstance(obj, Line) or isinstance(obj, Close):
                #Todo: break lines
                start = tuple([int(x) for x in obj.start])
                end = tuple([int(x) for x in obj.end])
                yield [start] + self._ln(*start, *end)
            elif isinstance(obj, CubicBezier):
                pts = [obj.start, obj.control1, obj.control2, obj.end]
                yield [self._calc(pts, 0)] + self._bz(pts, 0, 1)
            else:
                if not isinstance(obj, Move):
                    print(f'type {type(obj)} not supported')

    @classmethod
    def from_file(cls, filepath):
        with open(filepath) as svgfile:
            doc = minidom.parse(svgfile)
            svg = doc.getElementsByTagName('svg')
            if not svg:
                raise ValueError('No svg tag found')
            svg = svg[0]
            return cls(svg.getAttribute('viewBox'), svg.getElementsByTagName('path'))
