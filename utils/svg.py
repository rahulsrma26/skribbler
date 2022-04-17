import re
import math
import random
from xml.dom import minidom
from svgelements import Path, CubicBezier, Move, Line, Point, Close, Matrix
from utils.palette import hex2bgr, bgr2hex


class SVGElement:
    SPEED_RE = re.compile(r"\[([0-9]+)s\]")
    def __init__(self, elem):
        self.elem = elem
        self.style = dict([tuple(e.split(':')) for e in elem.getAttribute('style').split(';')])
        self.thickness = int(float(self.style['stroke-width']) + 0.5)
        self.color = hex2bgr(self.style['stroke'])
        self.fill = hex2bgr(self.style['fill'])
        self.name = self.id = elem.getAttribute('id') if elem.hasAttribute('id') else ''
        if elem.hasAttribute('inkscape:label'):
            self.name = elem.getAttribute('inkscape:label')
        result = self.SPEED_RE.search(self.name)
        self.speed = int(result.group(1)) if result else 100
        self.transform = None
        if elem.hasAttribute('transform'):
            self.transform = Matrix(elem.getAttribute('transform'))

    def serialize(self) -> str:
        raise NotImplementedError


class PathElement(SVGElement):

    def __init__(self, elem):
        super().__init__(elem)
        self.path = Path(elem.getAttribute("d"))
        self.apply_transform()
        if self.fill:
            if elem.hasAttribute('cx'):
                self.cx = int(float(elem.getAttribute('cx')) + 0.5)
                self.cy = int(float(elem.getAttribute('cy')) + 0.5)
            else:
                cx, cy = [], []
                for obj in self.path:
                    if isinstance(obj, Line) or isinstance(obj, Close) or isinstance(obj, CubicBezier):
                        cx.append(obj.start[0])
                        cy.append(obj.start[1])
                self.cx = int(sum(cx) / len(cx) + 0.5)
                self.cy = int(sum(cy) / len(cy) + 0.5)


    def to_str(self) -> str:
        def pts(p):
            return f'{int(p[0] + SVG.ROUND)},{int(p[1] + SVG.ROUND)}'
        line = ''
        if self.color:
            line = f'P {self.thickness} {bgr2hex(*self.color)}'
            if self.speed != 100:
                line += f' {self.speed}'
            for obj in self.path:
                if isinstance(obj, Line) or isinstance(obj, Close):
                    line += f':L {pts(obj.start)} {pts(obj.end)}'
                elif isinstance(obj, CubicBezier):
                    line += f':C {pts(obj.start)} {pts(obj.control1)} {pts(obj.control2)} {pts(obj.end)}'
        if self.fill:
            fl = f'F {self.cx},{self.cy} {bgr2hex(*self.fill)}'
            line = line + '\n' + fl if self.color else fl
        return line


    @classmethod
    def from_str(cls, line):
        obj = cls.__new__(cls)
        obj.fill = obj.color = None
        obj.path = []
        def pnt(txt):
            return Point(*[int(x) for x in txt.split(',')])
        if line.startswith('F'):
            _, point, color = line.split()
            obj.cx, obj.cy = pnt(point)
            obj.fill = hex2bgr(color)
        else:
            init, *segments = line.split(':')
            _, thickness, color, *extra = init.split()
            obj.thickness = int(thickness)
            obj.color = hex2bgr(color)
            if extra:
                obj.speed = int(extra[0])
            for segment in segments:
                if segment.startswith('L'):
                    _, start, end = segment.split()
                    obj.path.append(Line(pnt(start), pnt(end)))
                elif segment.startswith('C'):
                    _, start, c1, c2, end = segment.split()
                    obj.path.append(CubicBezier(pnt(start), pnt(c1), pnt(c2), pnt(end)))
        return obj


    def apply_transform(self):
        def t(p):
            return self.transform.transform_point(p)
        if self.transform:
            for obj in self.path:
                if isinstance(obj, CubicBezier):
                    obj.start = t(obj.start)
                    obj.control1 = t(obj.control1)
                    obj.control2 = t(obj.control2)
                    obj.end = t(obj.end)


    def __str__(self):
        return self.to_str()


    @staticmethod
    def fromCircle(elem):
        r = float(elem.getAttribute('r'))
        elem.setAttribute('rx', r)
        elem.setAttribute('ry', r)
        return PathElement.fromEllipse(elem)


    @staticmethod
    def fromEllipse(elem):
        D = 0.552284749831
        cx = float(elem.getAttribute('cx'))
        cy = float(elem.getAttribute('cy'))
        rx = float(elem.getAttribute('rx'))
        ry = float(elem.getAttribute('ry'))
        s = f'm {cx-rx},{cy} c 0,{-D*ry} {rx*(1-D)},{-ry} {rx},{-ry}'
        s += f' {D*rx},0 {rx},{ry*(1-D)} {rx},{ry}'
        s += f' 0,{D*ry} {-rx*(1-D)},{ry} {-rx},{ry}'
        s += f' {-D*rx},0 {-rx},{-ry*(1-D)} {-rx},{-ry}'
        elem.setAttribute('d', s)
        return PathElement(elem)


class SVG:
    DIST_THRESHOLD = 50
    PIXEL_THRESHOLD = 30
    ANGLE_THRESHOLD = 0.25
    HUMAN_ERROR = 2
    ROUND = 0.5
    CORE = {'#text', 'sodipodi:namedview', 'defs', 'metadata'}

    def __init__(self, viewbox, objs) -> None:
        self.vb = viewbox
        self.left, self.top, self.right, self.bottom = [int(x) for x in self.vb.split()]
        self.paths = objs


    def export(self, filepath):
        with open(filepath, 'w') as f:
            f.write(f'{self.vb}\n')
            for path in self.paths:
                f.write(path.to_str() + '\n')


    def __str__(self) -> str:
        s = f'SVG {self.vb}'
        for path in self.paths:
            s += f'\n|- {path}'
        return s


    @staticmethod
    def _calc(p, t):
        ps = []
        for i in range(2):
            ps.append(((1-t)**3)*p[0][i] + 3*(1-t)*(1-t)*t*p[1][i] + 3*(1-t)*t*t*p[2][i] + (t**3)*p[3][i])
        return tuple([int(x + SVG.ROUND) for x in ps])


    def _bz(self, pts, l, r):
        x1, y1 = SVG._calc(pts, l)
        x3, y3 = SVG._calc(pts, r)
        m = (l + r) / 2
        x2, y2 = SVG._calc(pts, m)
        dist = math.dist((x1, y1), (x3, y3))
        delta = random.uniform(-self.HUMAN_ERROR, self.HUMAN_ERROR)
        x2 = int(x2 + delta * min(1, dist / self.PIXEL_THRESHOLD))
        delta = random.uniform(-self.HUMAN_ERROR, self.HUMAN_ERROR)
        y2 = int(y2 + delta * min(1, dist / self.PIXEL_THRESHOLD))
        x2 = min(max(x2, self.left), self.right)
        y2 = min(max(y2, self.top), self.bottom)
        split = False
        if dist > self.DIST_THRESHOLD:
            # print('d', math.dist((x1, y1), (x3, y3)))
            split = True
        elif dist > self.PIXEL_THRESHOLD:
            a1 = math.atan2 (y1 - y2, x2 - x1)
            a2 = math.atan2 (y2 - y3, x3 - x2)
            da = math.atan2(math.sin(a1-a2), math.cos(a1-a2))
            if abs(da) > self.ANGLE_THRESHOLD:
                # print('a', a1, a2, abs(a1 - a2))
                split = True
        if split:
            return self._bz(pts, l, m) + self._bz(pts, m, r)
        else:
            return [(x2, y2), (x3, y3)]


    def _ln(self, x1, y1, x2, y2, d=0):
        dist = math.dist((x1, y1), (x2, y2))
        th = self.PIXEL_THRESHOLD if d < 3 else self.DIST_THRESHOLD
        if dist > th:
            xm = int((x1 + x2) / 2 + random.uniform(-self.HUMAN_ERROR, self.HUMAN_ERROR) + SVG.ROUND)
            ym = int((y1 + y2) / 2 + random.uniform(-self.HUMAN_ERROR, self.HUMAN_ERROR) + SVG.ROUND)
            xm = min(max(xm, self.left), self.right)
            ym = min(max(ym, self.top), self.bottom)
            return self._ln(x1, y1, xm, ym, d+1) + self._ln(xm, ym, x2, y2, d+1)
        else:
            return [(x2, y2)]


    def is_inside(self, point):
        x , y = point
        if x < self.left or x > self.right or y < self.top or y > self.bottom:
            return False
        return True


    def is_solo_line(self, elem: PathElement):
        if len(elem.path) == 2:
            obj = elem.path[1]
            if isinstance(obj, Line) or isinstance(obj, Close):
                return True
        return False


    def get_points(self, elem: PathElement):
        for obj in elem.path:
            if isinstance(obj, Line) or isinstance(obj, Close):
                start = tuple([int(x + SVG.ROUND) for x in obj.start])
                end = tuple([int(x + SVG.ROUND) for x in obj.end])
                yield [start] + self._ln(*start, *end)
            elif isinstance(obj, CubicBezier):
                pts = [obj.start, obj.control1, obj.control2, obj.end]
                yield [SVG._calc(pts, 0)] + self._bz(pts, 0, 1)
            else:
                if not isinstance(obj, Move):
                    print(f'type {type(obj)} not supported')


    @classmethod
    def get_elements(cls, svg):
        objs = []
        for child in svg.childNodes:
            if child.nodeName in cls.CORE:
                continue
            if child.nodeName == 'path':
                objs.append(PathElement(child))
            elif child.nodeName == 'circle':
                objs.append(PathElement.fromCircle(child))
            elif child.nodeName == 'ellipse':
                objs.append(PathElement.fromEllipse(child))
            elif child.nodeName == 'g':
                objs.extend(cls.get_elements(child))
            else:
                print(f'Warning! tag {child.nodeName} not supported')
        return objs


    @classmethod
    def from_file(cls, filepath):
        with open(filepath) as svgfile:
            doc = minidom.parse(svgfile)
            svg = doc.getElementsByTagName('svg')
            if not svg:
                raise ValueError('No svg tag found')
            return cls(svg[0].getAttribute('viewBox'), cls.get_elements(svg[0]))


    @classmethod
    def import_from(cls, filepath):
        with open(filepath, 'r') as f:
            vb = f.readline().strip()
            paths = [PathElement.from_str(line.strip()) for line in f]
            return cls(vb, paths)


# svg = SVG.from_file('db/asia.svg')
# svg = SVG.import_from('tmp/xprt/asia.txt')
# print(svg.__dict__, svg.HUMAN_ERROR)
# svg.export('tmp/asia.txt')
# for elem in svg.paths:
#     print([x for x in svg.get_points(elem)])
