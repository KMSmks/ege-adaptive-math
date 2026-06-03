"""
Параметрические шаблоны заданий ЕГЭ (часть 1).

Не храним готовые варианты — храним ТИП задания + генератор значений.
Ответ считается в коде, поэтому всегда корректен. Формулы сверены с банком
sdamgia и вариантами Школы Пифагора (26/28/29/30/33/34).

Шаблон — словарь: {task, skill, fn}, где fn() -> (text, answer) или
(text, answer, image_url). image_url — data-URI с SVG (для заданий по рисунку).

Файл не импортирует БД: можно гонять отдельно (`python templates.py`).
Часть 2 (13-19) сюда не входит — грузится статикой через seed.py.
"""
import base64
import random
from fractions import Fraction
from math import comb

TASK_TOPICS = {
    1: ("Планиметрия", False),
    2: ("Векторы", False),
    3: ("Стереометрия", False),
    4: ("Теория вероятностей (простая)", False),
    5: ("Теория вероятностей (сложная)", False),
    6: ("Уравнения", False),
    7: ("Преобразование выражений", False),
    8: ("Графики и производная", False),
    9: ("Прикладные задачи (формулы)", False),
    10: ("Текстовые задачи", False),
    11: ("Графики функций", False),
    12: ("Наибольшее и наименьшее значение функции", False),
    13: ("Тригонометрические уравнения", True),
    14: ("Стереометрия (часть 2)", True),
    15: ("Неравенства", True),
    16: ("Экономическая задача", True),
    17: ("Планиметрия (часть 2)", True),
    18: ("Задача с параметром", True),
    19: ("Числа и их свойства", True),
}


def _lin(coef, var="x"):
    if coef == 1:
        return var
    if coef == -1:
        return "-" + var
    return f"{coef}{var}"


def _num(x):
    if isinstance(x, int):
        return str(x)
    s = f"{x:.4f}".rstrip("0").rstrip(".")
    return s


# ---------- SVG (координатная сетка) ----------

_SVG_SIZE = 336
_CELL = 24
_C = _SVG_SIZE // 2


def _px(x):
    return _C + x * _CELL


def _py(y):
    return _C - y * _CELL


def _datauri(svg):
    b64 = base64.b64encode(svg.encode("utf-8")).decode("ascii")
    return "data:image/svg+xml;base64," + b64


def _grid(extra):
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_SVG_SIZE} {_SVG_SIZE}" '
        f'width="{_SVG_SIZE}" height="{_SVG_SIZE}">',
        '<defs>'
        '<marker id="ax" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">'
        '<path d="M0,0 L6,3 L0,6 Z" fill="#111827"/></marker>'
        '<marker id="va" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">'
        '<path d="M0,0 L6,3 L0,6 Z" fill="#4F46E5"/></marker>'
        '<marker id="vb" markerWidth="9" markerHeight="9" refX="6" refY="3" orient="auto">'
        '<path d="M0,0 L6,3 L0,6 Z" fill="#0D9488"/></marker>'
        '</defs>',
        f'<rect width="{_SVG_SIZE}" height="{_SVG_SIZE}" fill="white"/>',
    ]
    for i in range(-7, 8):
        parts.append(f'<line x1="{_px(i)}" y1="0" x2="{_px(i)}" y2="{_SVG_SIZE}" stroke="#eceef1" stroke-width="1"/>')
        parts.append(f'<line x1="0" y1="{_py(i)}" x2="{_SVG_SIZE}" y2="{_py(i)}" stroke="#eceef1" stroke-width="1"/>')
    parts.append(f'<line x1="0" y1="{_C}" x2="{_SVG_SIZE}" y2="{_C}" stroke="#111827" stroke-width="1.4" marker-end="url(#ax)"/>')
    parts.append(f'<line x1="{_C}" y1="{_SVG_SIZE}" x2="{_C}" y2="0" stroke="#111827" stroke-width="1.4" marker-end="url(#ax)"/>')
    parts.append(f'<line x1="{_px(1)}" y1="{_C-4}" x2="{_px(1)}" y2="{_C+4}" stroke="#111827" stroke-width="1.2"/>')
    parts.append(f'<text x="{_px(1)-3}" y="{_C+16}" font-family="sans-serif" font-size="11" fill="#6b7280">1</text>')
    parts.append(extra)
    parts.append('</svg>')
    return "".join(parts)


# ---------- ЗАДАНИЕ 1 ----------

def _t1_alt_median():
    a = random.choice([x for x in range(10, 85) if x != 45])
    b = 90 - a
    text = (f"Острые углы прямоугольного треугольника равны {a}° и {b}°. "
            f"Найдите угол между высотой и медианой, проведёнными из вершины "
            f"прямого угла. Ответ дайте в градусах.")
    return text, str(abs(a - b))


def _t1_circumradius():
    angle = random.choice([30, 150, 45, 135, 60, 120])
    R = random.randint(2, 15)
    if angle in (30, 150):
        ab = str(R)
    elif angle in (45, 135):
        ab = f"{R}√2"
    else:
        ab = f"{R}√3"
    text = (f"В треугольнике ABC сторона AB = {ab}, угол C = {angle}°. "
            f"Найдите радиус описанной около этого треугольника окружности.")
    return text, str(R)


# ---------- ЗАДАНИЕ 2 ----------

def _t2_scalar():
    while True:
        x1, y1 = random.randint(-15, 15), random.randint(-15, 15)
        x2, y2 = random.randint(-9, 9), random.randint(-9, 9)
        if (x1, y1) == (0, 0) or (x2, y2) == (0, 0):
            continue
        text = (f"Даны векторы a({x1}; {y1}) и b({x2}; {y2}). "
                f"Найдите скалярное произведение a · b.")
        return text, str(x1 * x2 + y1 * y2)


def _t2_scalar_svg():
    while True:
        x1, y1 = random.randint(-6, 6), random.randint(-6, 6)
        x2, y2 = random.randint(-6, 6), random.randint(-6, 6)
        if (x1, y1) == (0, 0) or (x2, y2) == (0, 0) or (x1, y1) == (x2, y2):
            continue
        extra = (
            f'<line x1="{_C}" y1="{_C}" x2="{_px(x1)}" y2="{_py(y1)}" stroke="#4F46E5" stroke-width="2.6" marker-end="url(#va)"/>'
            f'<text x="{_px(x1)+6}" y="{_py(y1)-4}" font-family="sans-serif" font-size="15" font-style="italic" fill="#4F46E5">a</text>'
            f'<line x1="{_C}" y1="{_C}" x2="{_px(x2)}" y2="{_py(y2)}" stroke="#0D9488" stroke-width="2.6" marker-end="url(#vb)"/>'
            f'<text x="{_px(x2)+6}" y="{_py(y2)-4}" font-family="sans-serif" font-size="15" font-style="italic" fill="#0D9488">b</text>'
        )
        text = ("На координатной плоскости изображены векторы a и b. "
                "Найдите скалярное произведение a · b.")
        return text, str(x1 * x2 + y1 * y2), _datauri(_grid(extra))


# ---------- ЗАДАНИЕ 4 ----------

def _t4_coins():
    n = random.choice([2, 3, 4])
    kind = random.choice(["ровно", "меньше", "больше", "не меньше"])
    k = random.randint(0, n)
    total = 2 ** n
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
    p = Fraction(good, total)
    word = {2: "дважды", 3: "трижды", 4: "четыре раза"}[n]
    text = (f"В случайном эксперименте симметричную монету бросают {word}. "
            f"Найдите вероятность того, что {cond}.")
    return text, _num(float(p))


# ---------- ЗАДАНИЕ 5 ----------

def _t5_lamps():
    n = random.choice([2, 3])
    p = random.choice([0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8])
    ans = 1 - p ** n
    text = (f"Помещение освещается {'двумя' if n == 2 else 'тремя'} лампами. "
            f"Вероятность перегорания каждой лампы в течение года равна "
            f"{_num(p).replace('.', ',')}. Лампы перегорают независимо друг от друга. "
            f"Найдите вероятность того, что в течение года хотя бы одна лампа не перегорит.")
    return text, _num(round(ans, 6))


def _t5_shooter():
    n = random.choice([3, 4, 5])
    p = random.choice([0.6, 0.7, 0.8, 0.9])
    ans = p * (1 - p) ** (n - 1)
    text = (f"Стрелок стреляет по одному разу в каждую из {n} мишеней. "
            f"Вероятность попадания при каждом отдельном выстреле равна "
            f"{_num(p).replace('.', ',')}. Найдите вероятность того, что стрелок "
            f"попадёт в первую мишень и не попадёт в остальные.")
    return text, _num(round(ans, 6))


# ---------- ЗАДАНИЕ 6 ----------

def _t6_log():
    A = random.choice([2, 3, 4, 5, 6, 7]); D = random.randint(1, 3); B = random.choice([1, 2, 3, 4, 5])
    x = random.randint(-12, 12)
    C = A ** D - B * x
    sign = "+" if C >= 0 else "-"
    return f"Найдите корень уравнения log_{A}({_lin(B)} {sign} {abs(C)}) = {D}.", str(x)


def _t6_recip():
    while True:
        k, p = random.randint(2, 6), random.randint(2, 6)
        if k == p:
            continue
        x = random.randint(-12, 12)
        m = random.choice([i for i in range(-20, 21) if i != 0])
        q = (k - p) * x + m
        if q == 0 or k * x + m == 0:
            continue
        sm = "+" if m >= 0 else "-"; sq = "+" if q >= 0 else "-"
        return (f"Найдите корень уравнения "
                f"1/({_lin(k)} {sm} {abs(m)}) = 1/({_lin(p)} {sq} {abs(q)}).", str(x))


def _t6_psq():
    a = random.randint(2, 25)
    return f"Найдите корень уравнения (x + {a})² = {4 * a}x.", str(a)


# ---------- ЗАДАНИЕ 7 ----------

def _t7_radical_diff():
    p = random.randint(8, 40); q = random.randint(2, p - 1)
    return f"Найдите значение выражения (√{p} − √{q})(√{p} + √{q}).", str(p - q)


def _t7_log_power():
    a = random.choice([2, 3, 5, 7]); k = random.choice([2, 3, 4, 5, 6]); m = random.randint(2, 4)
    return f"Найдите значение выражения {k} · log_{a}({a}^{m}).", str(k * m)


# ---------- ЗАДАНИЕ 9 ----------

def _t9_braking():
    while True:
        a = random.randint(2, 6); t1 = random.randint(2, 8); t2 = random.randint(t1 + 1, 12)
        if (a * (t1 + t2)) % 2 or (a * t1 * t2) % 2:
            continue
        v0 = a * (t1 + t2) // 2; S = a * t1 * t2 // 2
        text = (f"Автомобиль, движущийся со скоростью v₀ = {v0} м/с, начал торможение "
                f"с постоянным ускорением a = {a} м/с². За t секунд после начала "
                f"торможения он прошёл путь S = v₀t − at²/2 (м). Определите время, "
                f"прошедшее с начала торможения, если за это время автомобиль проехал "
                f"{S} метров. Ответ дайте в секундах.")
        return text, str(t1)


def _t9_adiabatic():
    v2 = random.choice([5, 6.4, 7.5, 8, 9.2, 10, 12.5, 14])
    V1 = round(v2 * 32, 1)
    text = (f"Установка для адиабатического сжатия: объём и давление связаны "
            f"соотношением p₁V₁^1,4 = p₂V₂^1,4, где p — давление (атм), V — объём (л). "
            f"Изначально объём газа равен {_num(V1).replace('.', ',')} л, давление равно "
            f"1 атмосфере. До какого объёма нужно сжать газ, чтобы давление стало "
            f"128 атмосфер? Ответ дайте в литрах.")
    return text, _num(v2).replace(".", ",")


# ---------- ЗАДАНИЕ 10 ----------

def _t10_avg_speed():
    speeds = [40, 50, 60, 75, 80, 100, 120]
    for _ in range(3000):
        v = [random.choice(speeds) for _ in range(3)]
        t = [random.randint(1, 4) for _ in range(3)]
        dist = [v[i] * t[i] for i in range(3)]
        if sum(dist) % sum(t) == 0 and len(set(v)) == 3:
            text = (f"Первые {dist[0]} км автомобиль ехал со скоростью {v[0]} км/ч, "
                    f"следующие {dist[1]} км — со скоростью {v[1]} км/ч, а затем "
                    f"{dist[2]} км — со скоростью {v[2]} км/ч. Найдите среднюю "
                    f"скорость автомобиля на протяжении всего пути. Ответ дайте в км/ч.")
            return text, str(sum(dist) // sum(t))
    return _t10_avg_speed()


# ---------- ЗАДАНИЕ 11 ----------

def _t11_linear_svg():
    while True:
        k = random.choice([-2, -1, 1, 2]); b = random.randint(-4, 4)
        x0 = random.choice([6, 7, 8, 9, -6, -7])
        ans = k * x0 + b
        pts = []
        xx = -7.0
        while xx <= 7.0001:
            yy = k * xx + b
            if -7 <= yy <= 7:
                pts.append(f"{_px(xx):.1f},{_py(yy):.1f}")
            xx += 0.25
        if len(pts) < 6:
            continue
        dots = ""
        for xi in range(-7, 8):
            yi = k * xi + b
            if -7 <= yi <= 7:
                dots += f'<circle cx="{_px(xi)}" cy="{_py(yi)}" r="2.4" fill="#4F46E5"/>'
        extra = (f'<polyline points="{" ".join(pts)}" fill="none" stroke="#4F46E5" stroke-width="2.6"/>'
                 + dots
                 + f'<text x="{_SVG_SIZE-70}" y="20" font-family="sans-serif" font-size="13" '
                   f'font-style="italic" fill="#4F46E5">y = f(x)</text>')
        text = (f"На рисунке изображён график функции вида f(x) = kx + b. "
                f"Найдите значение f({x0}).")
        return text, str(ans), _datauri(_grid(extra))


# ---------- ЗАДАНИЕ 12 ----------

def _t12_parabola():
    v = random.randint(-4, 5); m = random.randint(-20, 20)
    l = v - random.randint(1, 4); r = v + random.randint(1, 4)
    b = -2 * v; c = v * v + m
    sign = "+" if b >= 0 else "-"; cs = "+" if c >= 0 else "-"
    text = (f"Найдите наименьшее значение функции "
            f"y = x² {sign} {abs(b)}x {cs} {abs(c)} на отрезке [{l}; {r}].")
    return text, str(m)


def _t12_reciprocal():
    k = random.randint(2, 8); c = k * k
    l = max(1, k - random.randint(1, 3)); r = k + random.randint(1, 3)
    text = f"Найдите наименьшее значение функции y = x + {c}/x на отрезке [{l}; {r}]."
    return text, str(2 * k)


TEMPLATES = [
    {"task": 1, "skill": "Угол между высотой и медианой", "fn": _t1_alt_median},
    {"task": 1, "skill": "Радиус описанной окружности (теорема синусов)", "fn": _t1_circumradius},
    {"task": 2, "skill": "Скалярное произведение по координатам", "fn": _t2_scalar},
    {"task": 2, "skill": "Скалярное произведение по рисунку", "fn": _t2_scalar_svg},
    {"task": 4, "skill": "Симметричная монета", "fn": _t4_coins},
    {"task": 5, "skill": "Независимые события (лампы)", "fn": _t5_lamps},
    {"task": 5, "skill": "Независимые события (стрелок)", "fn": _t5_shooter},
    {"task": 6, "skill": "Логарифмическое уравнение", "fn": _t6_log},
    {"task": 6, "skill": "Уравнение с равными дробями", "fn": _t6_recip},
    {"task": 6, "skill": "Уравнение, сводящееся к полному квадрату", "fn": _t6_psq},
    {"task": 7, "skill": "Разность квадратов с корнями", "fn": _t7_radical_diff},
    {"task": 7, "skill": "Логарифм степени", "fn": _t7_log_power},
    {"task": 9, "skill": "Равноускоренное торможение", "fn": _t9_braking},
    {"task": 9, "skill": "Адиабатическое сжатие", "fn": _t9_adiabatic},
    {"task": 10, "skill": "Средняя скорость", "fn": _t10_avg_speed},
    {"task": 11, "skill": "График линейной функции", "fn": _t11_linear_svg},
    {"task": 12, "skill": "Наименьшее значение квадратичной функции", "fn": _t12_parabola},
    {"task": 12, "skill": "Наименьшее значение x + c/x", "fn": _t12_reciprocal},
]


if __name__ == "__main__":
    for tpl in TEMPLATES:
        res = tpl["fn"]()
        text, ans = res[0], res[1]
        img = "  [+SVG]" if len(res) == 3 else ""
        print(f"[{tpl['task']:>2}] {tpl['skill']}{img}\n     {text}\n     -> {ans}\n")
