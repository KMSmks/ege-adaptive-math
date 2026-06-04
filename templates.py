# -*- coding: utf-8 -*-
"""
Параметрические шаблоны заданий ЕГЭ (часть 1, задания 1-12).

Каждый тип задания взят из реальных вариантов (Школа Пифагора 26/28/29/30/33/34):
храним не готовые задачи, а генератор значений + формулу ответа (всегда верную)
+ при необходимости SVG-рисунок (data-URI), согласованный с числами и текстом.

Шаблон: {task, skill, fn}; fn() -> (text, answer) либо (text, answer, image_url).
Часть 2 (13-19) генератором не покрывается (каталог в questions_data.json).
"""
import base64
import math
import random
from fractions import Fraction
from math import comb, isqrt

TASK_TOPICS = {
    1: ("Планиметрия", False), 2: ("Векторы", False), 3: ("Стереометрия", False),
    4: ("Теория вероятностей (простая)", False), 5: ("Теория вероятностей (сложная)", False),
    6: ("Уравнения", False), 7: ("Преобразование выражений", False),
    8: ("Графики и производная", False), 9: ("Прикладные задачи (формулы)", False),
    10: ("Текстовые задачи", False), 11: ("Графики функций", False),
    12: ("Наибольшее и наименьшее значение функции", False),
    13: ("Тригонометрические уравнения", True), 14: ("Стереометрия (часть 2)", True),
    15: ("Неравенства", True), 16: ("Экономическая задача", True),
    17: ("Планиметрия (часть 2)", True), 18: ("Задача с параметром", True),
    19: ("Числа и их свойства", True),
}


def _lin(c, v="x"):
    return v if c == 1 else ("-" + v if c == -1 else f"{c}{v}")


def _num(x):
    if isinstance(x, int):
        return str(x)
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return s


# ============ SVG: координатная сетка ============
_S = 336
_CELL = 24
_O = _S // 2


def _px(x):
    return _O + x * _CELL


def _py(y):
    return _O - y * _CELL


def _uri(svg):
    return "data:image/svg+xml;base64," + base64.b64encode(svg.encode()).decode()


def _grid(extra):
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_S} {_S}" width="{_S}" height="{_S}">',
         '<defs>'
         '<marker id="ax" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#111827"/></marker>'
         '<marker id="va" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#4F46E5"/></marker>'
         '<marker id="vb" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#0D9488"/></marker>'
         '</defs>', f'<rect width="{_S}" height="{_S}" fill="white"/>']
    for i in range(-7, 8):
        p.append(f'<line x1="{_px(i)}" y1="0" x2="{_px(i)}" y2="{_S}" stroke="#eceef1"/>')
        p.append(f'<line x1="0" y1="{_py(i)}" x2="{_S}" y2="{_py(i)}" stroke="#eceef1"/>')
    p.append(f'<line x1="0" y1="{_O}" x2="{_S}" y2="{_O}" stroke="#111827" stroke-width="1.4" marker-end="url(#ax)"/>')
    p.append(f'<line x1="{_O}" y1="{_S}" x2="{_O}" y2="0" stroke="#111827" stroke-width="1.4" marker-end="url(#ax)"/>')
    p.append(f'<line x1="{_px(1)}" y1="{_O-4}" x2="{_px(1)}" y2="{_O+4}" stroke="#111827"/>')
    p.append(f'<text x="{_px(1)-3}" y="{_O+16}" font-family="sans-serif" font-size="11" fill="#6b7280">1</text>')
    p.append(extra)
    p.append('</svg>')
    return "".join(p)


def _segments(f, skip=None, lo=-7.0, hi=7.0, step=0.08):
    segs, cur = [], []
    x = lo
    while x <= hi + 1e-9:
        if skip is not None and abs(x - skip) < 0.2:
            if cur:
                segs.append(cur); cur = []
            x += step; continue
        y = f(x)
        if -7 <= y <= 7:
            cur.append(f"{_px(x):.1f},{_py(y):.1f}")
        elif cur:
            segs.append(cur); cur = []
        x += step
    if cur:
        segs.append(cur)
    return segs


def _polylines(segs, color="#4F46E5", w=2.5):
    return "".join(f'<polyline points="{" ".join(s)}" fill="none" stroke="{color}" stroke-width="{w}"/>' for s in segs if len(s) > 1)


# ============ ЗАДАНИЕ 1 ============

def _t1_alt_median():
    a = random.choice([x for x in range(10, 85) if x != 45]); b = 90 - a
    return (f"Острые углы прямоугольного треугольника равны {a}° и {b}°. Найдите угол "
            f"между высотой и медианой, проведёнными из вершины прямого угла. "
            f"Ответ дайте в градусах."), str(abs(a - b))


def _t1_circumradius():
    angle = random.choice([30, 150, 45, 135, 60, 120]); R = random.randint(2, 15)
    ab = str(R) if angle in (30, 150) else (f"{R}√2" if angle in (45, 135) else f"{R}√3")
    return (f"В треугольнике ABC сторона AB = {ab}, угол C = {angle}°. Найдите радиус "
            f"описанной около этого треугольника окружности."), str(R)


def _t1_chord_tangent():
    arc = random.choice([a for a in range(20, 172, 2) if a != 90])
    return (f"Хорда AB стягивает дугу окружности в {arc}°. Найдите угол между этой хордой "
            f"и касательной к окружности, проведённой через точку B. Ответ дайте в градусах."), str(arc // 2)


def _t1_midline_area():
    m = random.randint(2, 30); S = 4 * m
    return (f"Площадь треугольника ABC равна {S}. DE — средняя линия, параллельная стороне "
            f"AB. Найдите площадь треугольника CDE."), str(m)


def _t1_bisector_altitude():
    b = random.choice([x for x in range(10, 81) if x != 45])
    return (f"Острый угол B прямоугольного треугольника равен {b}°. Найдите угол между "
            f"биссектрисой CD и высотой CM, проведёнными из вершины прямого угла. "
            f"Ответ дайте в градусах."), str(abs(45 - b))


def _t1_isosceles_cos():
    # AC=BC, высота CH = AC*sin A, cos A = p/h (пифагорова тройка p,q,h)
    triples = [(7, 24, 25), (3, 4, 5), (4, 3, 5), (8, 15, 17), (20, 21, 29), (5, 12, 13)]
    for _ in range(200):
        p, q, h = random.choice(triples)
        AC = random.randint(2, 9) * h // math.gcd(h, 10) * (10 // math.gcd(h, 10))
        AC = random.choice([5, 10, 15, 20, 25, h, 2 * h])
        CH = AC * q / h
        if abs(CH * 10 - round(CH * 10)) < 1e-9 and CH > 0:
            return (f"В треугольнике ABC AC = BC, высота CH равна {_num(round(CH, 1))}, "
                    f"cos A = {p}/{h}. Найдите AC."), str(AC)
    return _t1_isosceles_cos()


# ============ ЗАДАНИЕ 2 ============

def _t2_scalar():
    while True:
        x1, y1 = random.randint(-15, 15), random.randint(-15, 15)
        x2, y2 = random.randint(-9, 9), random.randint(-9, 9)
        if (x1, y1) == (0, 0) or (x2, y2) == (0, 0):
            continue
        return (f"Даны векторы a({x1}; {y1}) и b({x2}; {y2}). Найдите скалярное произведение "
                f"a · b."), str(x1 * x2 + y1 * y2)


def _t2_cos_angle():
    M5 = [(3, 4), (4, 3), (-3, 4), (3, -4), (-4, 3), (4, -3), (-3, -4), (-4, -3),
          (5, 0), (0, 5), (-5, 0), (0, -5)]
    while True:
        a = random.choice(M5); b = random.choice(M5)
        if a == b:
            continue
        cos = (a[0] * b[0] + a[1] * b[1]) / 25.0
        return (f"Даны векторы a({a[0]}; {a[1]}) и b({b[0]}; {b[1]}). Найдите косинус угла "
                f"между ними."), _num(round(cos, 4))


def _t2_combo_len():
    while True:
        a = (random.randint(-8, 8), random.randint(-8, 8))
        b = (random.randint(-3, 3), random.randint(-3, 3))
        k = random.choice([2, 3, 4, 5, 10, 20])
        sign = random.choice([1, -1])
        vx, vy = a[0] + sign * k * b[0], a[1] + sign * k * b[1]
        d2 = vx * vx + vy * vy
        r = isqrt(d2)
        if d2 == 0 or r * r != d2:
            continue
        op = "+" if sign > 0 else "−"
        return (f"Даны векторы a({a[0]}; {a[1]}) и b({b[0]}; {b[1]}). Найдите длину вектора "
                f"a {op} {k}b."), str(r)


def _t2_vectors_svg():
    while True:
        x1, y1 = random.randint(-6, 6), random.randint(-6, 6)
        x2, y2 = random.randint(-6, 6), random.randint(-6, 6)
        if (x1, y1) == (0, 0) or (x2, y2) == (0, 0) or (x1, y1) == (x2, y2):
            continue
        kind = random.choice(["scalar", "diff", "sum"])
        if kind == "scalar":
            q, ans = "Найдите скалярное произведение a · b.", x1 * x2 + y1 * y2
        else:
            sx, sy = (x1 - x2, y1 - y2) if kind == "diff" else (x1 + x2, y1 + y2)
            d2 = sx * sx + sy * sy; r = isqrt(d2)
            if d2 == 0 or r * r != d2:
                continue
            q = f"Найдите длину вектора a {'−' if kind == 'diff' else '+'} b."
            ans = r
        extra = (f'<line x1="{_O}" y1="{_O}" x2="{_px(x1)}" y2="{_py(y1)}" stroke="#4F46E5" stroke-width="2.6" marker-end="url(#va)"/>'
                 f'<text x="{_px(x1)+6}" y="{_py(y1)-4}" font-family="sans-serif" font-size="15" font-style="italic" fill="#4F46E5">a</text>'
                 f'<line x1="{_O}" y1="{_O}" x2="{_px(x2)}" y2="{_py(y2)}" stroke="#0D9488" stroke-width="2.6" marker-end="url(#vb)"/>'
                 f'<text x="{_px(x2)+6}" y="{_py(y2)-4}" font-family="sans-serif" font-size="15" font-style="italic" fill="#0D9488">b</text>')
        return "На координатной плоскости изображены векторы a и b. " + q, str(ans), _uri(_grid(extra))


# ============ ЗАДАНИЕ 3 (стереометрия + фигуры) ============

def _box_svg(a, b, c, half=False):
    u = 24; dx, dy = b * u * 0.55, -b * u * 0.5; ox, oy = 70, 200
    fbl, fbr = (ox, oy), (ox + a * u, oy)
    ftl, ftr = (ox, oy - c * u), (ox + a * u, oy - c * u)
    btl, btr, bbr, bbl = (ftl[0]+dx, ftl[1]+dy), (ftr[0]+dx, ftr[1]+dy), (fbr[0]+dx, fbr[1]+dy), (fbl[0]+dx, fbl[1]+dy)

    def L(p, q, d=False):
        s = ' stroke-dasharray="4 4"' if d else ''
        return f'<line x1="{p[0]:.1f}" y1="{p[1]:.1f}" x2="{q[0]:.1f}" y2="{q[1]:.1f}" stroke="#111827" stroke-width="1.5"{s}/>'
    body = "".join([L(fbl, fbr), L(fbr, ftr), L(ftr, ftl), L(ftl, fbl), L(ftl, btl), L(ftr, btr),
                    L(fbr, bbr), L(btl, btr), L(btr, bbr), L(fbl, bbl, True), L(bbl, btl, True), L(bbl, bbr, True)])
    if half:  # диагональ грани, отсекающая половину
        body += L(fbl, ftr)
    labels = (f'<text x="{(fbl[0]+fbr[0])/2-4:.0f}" y="{oy+18:.0f}" font-family="sans-serif" font-size="13" fill="#374151">{a}</text>'
              f'<text x="{ox-18:.0f}" y="{(oy+ftl[1])/2+4:.0f}" font-family="sans-serif" font-size="13" fill="#374151">{c}</text>'
              f'<text x="{(ftr[0]+btr[0])/2+5:.0f}" y="{(ftr[1]+btr[1])/2:.0f}" font-family="sans-serif" font-size="13" fill="#374151">{b}</text>')
    return _uri(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 300 240" width="300" height="240"><rect width="300" height="240" fill="white"/>{body}{labels}</svg>')


def _cone_svg(section=True):
    cx, cy, rx, ry = 120, 195, 70, 18; ax, ay = 120, 40
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240"><rect width="240" height="240" fill="white"/>']
    s.append(f'<path d="M{cx-rx},{cy} A{rx},{ry} 0 0 0 {cx+rx},{cy}" fill="none" stroke="#111827" stroke-width="1.5"/>')
    s.append(f'<path d="M{cx-rx},{cy} A{rx},{ry} 0 0 1 {cx+rx},{cy}" fill="none" stroke="#111827" stroke-width="1.2" stroke-dasharray="4 4"/>')
    s.append(f'<line x1="{ax}" y1="{ay}" x2="{cx-rx}" y2="{cy}" stroke="#111827" stroke-width="1.5"/>')
    s.append(f'<line x1="{ax}" y1="{ay}" x2="{cx+rx}" y2="{cy}" stroke="#111827" stroke-width="1.5"/>')
    if section:
        t = 0.45; sx = cx; sy = ay + (cy - ay) * t; srx = rx * t; sry = ry * t
        s.append(f'<ellipse cx="{sx}" cy="{sy:.0f}" rx="{srx:.0f}" ry="{sry:.0f}" fill="none" stroke="#4F46E5" stroke-width="1.4" stroke-dasharray="4 3"/>')
    s.append('</svg>')
    return _uri("".join(s))


def _cyl_cone_svg():
    cx, rx, ry = 120, 64, 16; top, bot = 60, 190
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240"><rect width="240" height="240" fill="white"/>']
    s.append(f'<line x1="{cx-rx}" y1="{top}" x2="{cx-rx}" y2="{bot}" stroke="#111827" stroke-width="1.5"/>')
    s.append(f'<line x1="{cx+rx}" y1="{top}" x2="{cx+rx}" y2="{bot}" stroke="#111827" stroke-width="1.5"/>')
    s.append(f'<ellipse cx="{cx}" cy="{top}" rx="{rx}" ry="{ry}" fill="none" stroke="#111827" stroke-width="1.5"/>')
    s.append(f'<path d="M{cx-rx},{bot} A{rx},{ry} 0 0 0 {cx+rx},{bot}" fill="none" stroke="#111827" stroke-width="1.5"/>')
    s.append(f'<path d="M{cx-rx},{bot} A{rx},{ry} 0 0 1 {cx+rx},{bot}" fill="none" stroke="#111827" stroke-width="1.2" stroke-dasharray="4 4"/>')
    s.append(f'<line x1="{cx}" y1="{top}" x2="{cx-rx}" y2="{bot}" stroke="#4F46E5" stroke-width="1.5"/>')
    s.append(f'<line x1="{cx}" y1="{top}" x2="{cx+rx}" y2="{bot}" stroke="#4F46E5" stroke-width="1.5"/>')
    s.append('</svg>')
    return _uri("".join(s))


def _hex_pyramid_svg():
    cx, cy, rx, ry = 120, 175, 72, 26; ax, ay = 120, 38
    verts = [(cx + rx * math.cos(math.radians(60 * i)), cy + ry * math.sin(math.radians(60 * i))) for i in range(6)]
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 240 240" width="240" height="240"><rect width="240" height="240" fill="white"/>']
    poly = " ".join(f"{x:.0f},{y:.0f}" for x, y in verts)
    s.append(f'<polygon points="{poly}" fill="none" stroke="#111827" stroke-width="1.5"/>')
    for i, (x, y) in enumerate(verts):
        dash = ' stroke-dasharray="4 4"' if y < cy - 2 else ''
        s.append(f'<line x1="{ax}" y1="{ay}" x2="{x:.0f}" y2="{y:.0f}" stroke="#111827" stroke-width="1.3"{dash}/>')
    s.append('</svg>')
    return _uri("".join(s))


def _t3_box():
    a, b, c = (random.randint(2, 8) for _ in range(3))
    if random.random() < 0.5:
        return "На рисунке изображён прямоугольный параллелепипед. Найдите его объём.", str(a * b * c), _box_svg(a, b, c)
    return ("На рисунке изображён прямоугольный параллелепипед. Найдите площадь его поверхности.",
            str(2 * (a * b + b * c + a * c)), _box_svg(a, b, c))


def _t3_half_box():
    while True:
        a, b, c = (random.randint(2, 8) for _ in range(3))
        if (a * b * c) % 2 == 0:
            break
    return ("В прямоугольном параллелепипеде ABCDA₁B₁C₁D₁ известно, что "
            f"AB = {a}, BC = {b}, AA₁ = {c}. Найдите объём многогранника, вершинами которого "
            "являются точки A, B, C, D, A₁ и B₁.", str(a * b * c // 2), _box_svg(a, b, c, half=True))


def _t3_cone_frustum():
    for _ in range(300):
        m, n = random.choice([(3, 2), (1, 1), (2, 3), (1, 2), (3, 1), (2, 1), (1, 4), (4, 1)])
        S = random.randint(10, 90)
        ans = S * (m / (m + n)) ** 2
        if abs(ans * 10 - round(ans * 10)) < 1e-9:
            return (f"Площадь полной поверхности конуса равна {S}. Параллельно основанию конуса "
                    f"проведено сечение, делящее высоту в отношении {m}:{n}, считая от вершины "
                    f"конуса. Найдите площадь полной поверхности отсечённого конуса.",
                    _num(round(ans, 1)), _cone_svg(section=True))
    return _t3_cone_frustum()


def _t3_hex_pyramid():
    base = [(3, 4, 5), (4, 3, 5), (5, 12, 13), (12, 5, 13), (8, 15, 17), (6, 8, 10), (8, 6, 10)]
    a0, h0, L0 = random.choice(base); sc = random.choice([0.5, 1])
    a, h, L = a0 * sc, h0 * sc, L0 * sc
    return (f"В правильной шестиугольной пирамиде боковое ребро равно {_num(L)}, а сторона "
            f"основания равна {_num(a)}. Найдите высоту пирамиды.", _num(h), _hex_pyramid_svg())


def _t3_cyl_cone():
    N = random.randint(2, 12)
    return (f"Цилиндр и конус имеют общие основание и высоту. Высота цилиндра равна радиусу "
            f"основания. Площадь боковой поверхности цилиндра равна {N}√2. Найдите площадь "
            f"боковой поверхности конуса.", str(N), _cyl_cone_svg())


def _t3_prism_cube():
    C = random.choice([4, 8, 12, 20, 24, 36])  # объём куба
    v = C / 8.0
    return (f"Объём треугольной призмы, отсекаемой от куба плоскостью, проходящей через "
            f"середины двух рёбер, выходящих из одной вершины, и параллельной третьему "
            f"ребру, выходящему из этой же вершины, равен {_num(round(v, 3))}. Найдите объём куба.",
            str(C), _box_svg(int(round(C ** (1 / 3))) or 2, int(round(C ** (1 / 3))) or 2, int(round(C ** (1 / 3))) or 2, half=True))


# ============ ЗАДАНИЕ 4 ============

def _t4_coins():
    n = random.choice([2, 3, 4]); kind = random.choice(["ровно", "меньше", "больше", "не меньше"])
    k = random.randint(0, n); total = 2 ** n
    if kind == "ровно":
        good = comb(n, k); cond = f"орлов выпало ровно {k}"
    elif kind == "меньше":
        good = sum(comb(n, i) for i in range(0, k)); cond = f"орлов выпало меньше {k}"
    elif kind == "больше":
        good = sum(comb(n, i) for i in range(k + 1, n + 1)); cond = f"орлов выпало больше {k}"
    else:
        good = sum(comb(n, i) for i in range(k, n + 1)); cond = f"орлов выпало не меньше {k}"
    if good in (0, total):
        return _t4_coins()
    w = {2: "дважды", 3: "трижды", 4: "четыре раза"}[n]
    return (f"В случайном эксперименте симметричную монету бросают {w}. Найдите вероятность "
            f"того, что {cond}.", _num(float(Fraction(good, total))))


# ============ ЗАДАНИЕ 5 ============

def _t5_lamps():
    n = random.choice([2, 3]); p = random.choice([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    return (f"Помещение освещается {'двумя' if n == 2 else 'тремя'} лампами. Вероятность "
            f"перегорания каждой лампы в течение года равна {_num(p).replace('.', ',')}. Лампы "
            f"перегорают независимо. Найдите вероятность того, что в течение года хотя бы одна "
            f"лампа не перегорит.", _num(round(1 - p ** n, 6)))


def _t5_shooter():
    n = random.choice([3, 4, 5]); p = random.choice([0.6, 0.7, 0.8, 0.9])
    return (f"Стрелок стреляет по одному разу в каждую из {n} мишеней. Вероятность попадания "
            f"при каждом выстреле равна {_num(p).replace('.', ',')}. Найдите вероятность того, "
            f"что стрелок попадёт в первую мишень и не попадёт в остальные.",
            _num(round(p * (1 - p) ** (n - 1), 6)))


# ============ ЗАДАНИЕ 6 ============

def _t6_log():
    A = random.choice([2, 3, 4, 5, 6, 7]); D = random.randint(1, 3); B = random.choice([1, 2, 3, 4, 5])
    x = random.randint(-12, 12); C = A ** D - B * x; sg = "+" if C >= 0 else "-"
    return f"Найдите корень уравнения log_{A}({_lin(B)} {sg} {abs(C)}) = {D}.", str(x)


def _t6_recip():
    while True:
        k, p = random.randint(2, 6), random.randint(2, 6)
        if k == p:
            continue
        x = random.randint(-12, 12); m = random.choice([i for i in range(-20, 21) if i])
        q = (k - p) * x + m
        if q == 0 or k * x + m == 0:
            continue
        sm = "+" if m >= 0 else "-"; sq = "+" if q >= 0 else "-"
        return f"Найдите корень уравнения 1/({_lin(k)} {sm} {abs(m)}) = 1/({_lin(p)} {sq} {abs(q)}).", str(x)


def _t6_psq():
    a = random.randint(2, 25)
    return f"Найдите корень уравнения (x + {a})² = {4 * a}x.", str(a)


# ============ ЗАДАНИЕ 7 ============

def _t7_radical_diff():
    p = random.randint(8, 40); q = random.randint(2, p - 1)
    return f"Найдите значение выражения (√{p} − √{q})(√{p} + √{q}).", str(p - q)


def _t7_log_power():
    a = random.choice([2, 3, 5, 7]); k = random.choice([2, 3, 4, 5, 6]); m = random.randint(2, 4)
    return f"Найдите значение выражения {k} · log_{a}({a}^{m}).", str(k * m)


# ============ ЗАДАНИЕ 9 ============

def _t9_braking():
    while True:
        a = random.randint(2, 6); t1 = random.randint(2, 8); t2 = random.randint(t1 + 1, 12)
        if (a * (t1 + t2)) % 2 or (a * t1 * t2) % 2:
            continue
        v0 = a * (t1 + t2) // 2; S = a * t1 * t2 // 2
        return (f"Автомобиль, движущийся со скоростью v₀ = {v0} м/с, начал торможение с "
                f"постоянным ускорением a = {a} м/с². За t секунд он прошёл путь "
                f"S = v₀t − at²/2 (м). Определите время с начала торможения, если за это время "
                f"автомобиль проехал {S} метров. Ответ дайте в секундах.", str(t1))


def _t9_adiabatic():
    v2 = random.choice([5, 6.4, 7.5, 8, 9.2, 10, 12.5, 14]); V1 = round(v2 * 32, 1)
    return (f"Адиабатическое сжатие: p₁V₁^1,4 = p₂V₂^1,4, p — давление (атм), V — объём (л). "
            f"Изначально объём газа {_num(V1).replace('.', ',')} л при давлении 1 атмосфера. До "
            f"какого объёма сжать газ, чтобы давление стало 128 атмосфер? Ответ дайте в литрах.",
            _num(v2).replace(".", ","))


# ============ ЗАДАНИЕ 10 ============

def _t10_avg_speed():
    sp = [40, 50, 60, 75, 80, 100, 120]
    for _ in range(3000):
        v = [random.choice(sp) for _ in range(3)]; t = [random.randint(1, 4) for _ in range(3)]
        d = [v[i] * t[i] for i in range(3)]
        if sum(d) % sum(t) == 0 and len(set(v)) == 3:
            return (f"Первые {d[0]} км автомобиль ехал со скоростью {v[0]} км/ч, следующие {d[1]} км — "
                    f"{v[1]} км/ч, затем {d[2]} км — {v[2]} км/ч. Найдите среднюю скорость на всём пути. "
                    f"Ответ дайте в км/ч.", str(sum(d) // sum(t)))
    return _t10_avg_speed()


def _t10_meet():
    # двое из одной точки до отметки L; второй быстрее, доходит и идёт назад; где встреча
    for _ in range(500):
        v1 = random.choice([2, 2.2, 2.5, 3]); v2 = 2 * v1; L = random.choice([1.5, 2, 3, 4])
        # встреча после разворота: x от старта = L - (расстояние второго после разворота)
        # время встречи: v1*t + v2*t = 2L -> t=2L/(v1+v2); место = v1*t
        t = 2 * L / (v1 + v2); x = v1 * t
        if abs(x * 100 - round(x * 100)) < 1e-9:
            return (f"Два человека отправляются из одного дома до опушки леса в {_num(L).replace('.', ',')} км. "
                    f"Один идёт со скоростью {_num(v1).replace('.', ',')} км/ч, другой — {_num(v2).replace('.', ',')} км/ч. "
                    f"Дойдя до опушки, второй с той же скоростью возвращается. На каком расстоянии от "
                    f"точки отправления произойдёт их встреча? Ответ дайте в километрах.",
                    _num(round(x, 2)).replace(".", ","))
    return _t10_avg_speed()


# ============ ЗАДАНИЕ 8 (график f'(x)) ============

def _t8_graph_svg():
    A = 3.2
    while True:
        bw = random.choice([0.6, 0.7, 0.8, 0.9]); ph = random.uniform(0, 6.28)
        cand = [x for x in range(-6, 7) if abs(math.sin(bw * x + ph)) > 0.45]
        k = random.choice([5, 6])
        if len(cand) < k:
            continue
        xs = sorted(random.sample(cand, k)); kind = random.choice(["incr", "decr"])
        if kind == "incr":
            ans = sum(1 for x in xs if math.sin(bw * x + ph) > 0)
            q = "Сколько из этих точек лежит на промежутках возрастания функции f(x)?"
        else:
            ans = sum(1 for x in xs if math.sin(bw * x + ph) < 0)
            q = "Сколько из этих точек лежит на промежутках убывания функции f(x)?"
        if ans in (0, k):
            continue
        segs = _segments(lambda x: A * math.sin(bw * x + ph))
        subs = "₁₂₃₄₅₆₇₈"; marks = ""
        for i, x in enumerate(xs):
            marks += f'<circle cx="{_px(x):.1f}" cy="{_O}" r="3" fill="#111827"/>'
            marks += f'<text x="{_px(x)-6:.1f}" y="{_O+18}" font-family="sans-serif" font-size="11" fill="#374151">x{subs[i]}</text>'
        extra = _polylines(segs, w=2.4) + marks + f'<text x="{_S-78}" y="18" font-family="sans-serif" font-size="13" font-style="italic" fill="#4F46E5">y = f\u2032(x)</text>'
        return (f"На рисунке изображён график y = f′(x) — производной функции f(x). На оси абсцисс "
                f"отмечены {k} точек. " + q), str(ans), _uri(_grid(extra))


# ============ ЗАДАНИЕ 11 (графики функций) ============

def _label_fx(extra):
    return extra + f'<text x="{_S-70}" y="20" font-family="sans-serif" font-size="13" font-style="italic" fill="#4F46E5">y = f(x)</text>'


def _t11_linear():
    while True:
        k = random.choice([-2, -1, 1, 2]); b = random.randint(-4, 4)
        segs = _segments(lambda x: k * x + b)
        if not segs:
            continue
        dots = "".join(f'<circle cx="{_px(xi)}" cy="{_py(k*xi+b)}" r="2.4" fill="#4F46E5"/>'
                       for xi in range(-7, 8) if -7 <= k * xi + b <= 7)
        extra = _label_fx(_polylines(segs) + dots)
        if random.random() < 0.5:
            x0 = random.choice([6, 7, 8, 9, -6, -7])
            return f"На рисунке изображён график функции вида f(x) = kx + b. Найдите значение f({x0}).", str(k * x0 + b), _uri(_grid(extra))
        cand = [xi for xi in range(-7, 8) if -7 <= k * xi + b <= 7]; x0 = random.choice(cand)
        return f"На рисунке изображён график функции вида f(x) = kx + b. Найдите значение x, при котором f(x) = {k*x0+b}.", str(x0), _uri(_grid(extra))


def _t11_parabola():
    a = random.choice([1, -1]); vx = random.randint(-2, 2); vy = random.randint(-3, 3)
    b = -2 * a * vx; c = a * vx * vx + vy

    def f(x):
        return a * x * x + b * x + c
    segs = _segments(f)
    dots = "".join(f'<circle cx="{_px(xi)}" cy="{_py(f(xi))}" r="2.4" fill="#4F46E5"/>'
                   for xi in range(-7, 8) if -7 <= f(xi) <= 7)
    extra = _label_fx(_polylines(segs) + dots)
    x0 = random.randint(-4, 5)
    return (f"На рисунке изображён график функции f(x) = ax² + bx + c, где a, b, c — целые числа. "
            f"Найдите значение f({x0}).", str(a * x0 * x0 + b * x0 + c), _uri(_grid(extra)))


def _t11_two_lines():
    while True:
        k1, k2 = random.sample([-2, -1, 1, 2], 2); xa = random.randint(-4, 4)
        b1 = random.randint(-3, 3); b2 = b1 + (k1 - k2) * xa
        ya = k1 * xa + b1
        if not (-6 <= ya <= 6) or not (-6 <= b2 <= 6):
            continue
        s1 = _segments(lambda x: k1 * x + b1); s2 = _segments(lambda x: k2 * x + b2)
        extra = _polylines(s1, "#4F46E5") + _polylines(s2, "#0D9488")
        extra += f'<circle cx="{_px(xa)}" cy="{_py(ya)}" r="3.2" fill="#111827"/>'
        extra += f'<text x="{_px(xa)+5}" y="{_py(ya)-5}" font-family="sans-serif" font-size="13" fill="#111827">A</text>'
        return ("На рисунке изображены графики двух линейных функций, пересекающиеся в точке A. "
                "Найдите абсциссу точки A.", str(xa), _uri(_grid(extra)))


def _t11_hyperbola():
    while True:
        k = random.choice([-8, -6, -4, -3, -2, 2, 3, 4, 6, 8])
        divs = [d for d in range(-6, 7) if d and k % d == 0 and -7 <= k // d <= 7]
        if not divs:
            continue
        x0 = random.choice(divs)
        segs = _segments(lambda x: k / x, skip=0.0)
        extra = _label_fx(_polylines(segs))
        return (f"На рисунке изображён график функции вида f(x) = k/x. Найдите значение f({x0}).",
                str(k // x0), _uri(_grid(extra)))


# ============ ЗАДАНИЕ 12 ============

def _t12_parabola():
    v = random.randint(-4, 5); m = random.randint(-20, 20)
    l = v - random.randint(1, 4); r = v + random.randint(1, 4); b = -2 * v; c = v * v + m
    sg = "+" if b >= 0 else "-"; cs = "+" if c >= 0 else "-"
    return f"Найдите наименьшее значение функции y = x² {sg} {abs(b)}x {cs} {abs(c)} на отрезке [{l}; {r}].", str(m)


def _t12_reciprocal():
    k = random.randint(2, 8); c = k * k; l = max(1, k - random.randint(1, 3)); r = k + random.randint(1, 3)
    return f"Найдите наименьшее значение функции y = x + {c}/x на отрезке [{l}; {r}].", str(2 * k)


TEMPLATES = [
    {"task": 1, "skill": "Высота и медиана из прямого угла", "fn": _t1_alt_median},
    {"task": 1, "skill": "Радиус описанной окружности", "fn": _t1_circumradius},
    {"task": 1, "skill": "Угол между хордой и касательной", "fn": _t1_chord_tangent},
    {"task": 1, "skill": "Средняя линия и площадь", "fn": _t1_midline_area},
    {"task": 1, "skill": "Биссектриса и высота из прямого угла", "fn": _t1_bisector_altitude},
    {"task": 1, "skill": "Равнобедренный треугольник, высота и cos", "fn": _t1_isosceles_cos},
    {"task": 2, "skill": "Скалярное произведение по координатам", "fn": _t2_scalar},
    {"task": 2, "skill": "Косинус угла между векторами", "fn": _t2_cos_angle},
    {"task": 2, "skill": "Длина линейной комбинации векторов", "fn": _t2_combo_len},
    {"task": 2, "skill": "Действия с векторами по рисунку", "fn": _t2_vectors_svg},
    {"task": 3, "skill": "Параллелепипед: объём и площадь поверхности", "fn": _t3_box},
    {"task": 3, "skill": "Объём части параллелепипеда", "fn": _t3_half_box},
    {"task": 3, "skill": "Сечение конуса (площадь поверхности)", "fn": _t3_cone_frustum},
    {"task": 3, "skill": "Высота шестиугольной пирамиды", "fn": _t3_hex_pyramid},
    {"task": 3, "skill": "Цилиндр и конус (боковая поверхность)", "fn": _t3_cyl_cone},
    {"task": 3, "skill": "Призма, отсекаемая от куба", "fn": _t3_prism_cube},
    {"task": 4, "skill": "Симметричная монета", "fn": _t4_coins},
    {"task": 5, "skill": "Независимые события (лампы)", "fn": _t5_lamps},
    {"task": 5, "skill": "Независимые события (стрелок)", "fn": _t5_shooter},
    {"task": 6, "skill": "Логарифмическое уравнение", "fn": _t6_log},
    {"task": 6, "skill": "Уравнение с равными дробями", "fn": _t6_recip},
    {"task": 6, "skill": "Уравнение, сводящееся к полному квадрату", "fn": _t6_psq},
    {"task": 7, "skill": "Разность квадратов с корнями", "fn": _t7_radical_diff},
    {"task": 7, "skill": "Логарифм степени", "fn": _t7_log_power},
    {"task": 8, "skill": "Чтение графика производной", "fn": _t8_graph_svg},
    {"task": 9, "skill": "Равноускоренное торможение", "fn": _t9_braking},
    {"task": 9, "skill": "Адиабатическое сжатие", "fn": _t9_adiabatic},
    {"task": 10, "skill": "Средняя скорость", "fn": _t10_avg_speed},
    {"task": 10, "skill": "Движение навстречу с разворотом", "fn": _t10_meet},
    {"task": 11, "skill": "График линейной функции", "fn": _t11_linear},
    {"task": 11, "skill": "График параболы", "fn": _t11_parabola},
    {"task": 11, "skill": "Пересечение двух прямых", "fn": _t11_two_lines},
    {"task": 11, "skill": "График гиперболы", "fn": _t11_hyperbola},
    {"task": 12, "skill": "Наименьшее значение квадратичной функции", "fn": _t12_parabola},
    {"task": 12, "skill": "Наименьшее значение x + c/x", "fn": _t12_reciprocal},
]


if __name__ == "__main__":
    for t in TEMPLATES:
        r = t["fn"]()
        print(f"[{t['task']:>2}] {t['skill']}{'  [SVG]' if len(r) == 3 else ''}: {r[1]}")
