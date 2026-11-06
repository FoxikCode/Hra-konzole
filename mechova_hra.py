#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HLUBINY POD MECHOVEM - ASCII rogue hra do konzole s bojem ve stylu Undertale.

Příběh: Ve vesnici Mechov někdo ukradl Zlatý Amulet ('*'), který chrání
celou vesnici. Zloděj, drak 'D', ho schoval v pátém patře jeskyní.

Svět:     W A S D / šipky = pohyb      P = lektvar     . = počkat     Q = konec
          Vrazíš-li do nepřítele (nebo on do tebe), začne BOJ.
          Přejdi na obchodníka 'M' a otevře se obchod.
          U rybníčku nahoře ve vesnici sedí někdo, kdo si rád popovídá...

Boj (jako v Undertale):
          BOJ    - zastavuj ukazatel co nejblíž středu = větší zásah
          AKCE   - mluv, zpívej, hlaď... zvyšuješ "náladu" nepřítele
          VĚCI   - lektvary
          MILOST - Ušetřit (když je nepřítel žlutý / nechce se bít) nebo Utéct
          Po tvém tahu útočí nepřítel: uhýbej srdíčku ♥ kulkám v rámečku (WASD).
          Dá se vyhrát bez jediného zabití!

Spuštění:  python mechova_hra.py      (Python 3.6+, bez dalších knihoven)
"""
import os
import sys
import time
import random
import textwrap

W, H = 60, 20
FINAL_DEPTH = 5

# --- nastavení bojového systému ---
BW, BH = 29, 7        # vnitřní rozměr bojového rámečku (šířka, výška)
FRAME = 0.10          # délka jednoho kroku při uhýbání (sekundy)
BAR_STEP = 0.035      # rychlost ukazatele při útoku
PAUSE = 0.6           # krátké pauzy (zobrazení poškození apod.)
ENTER = ("\r", "\n", " ", "z")
MOVES = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0),
         "k": (0, -1), "j": (0, 1), "h": (-1, 0), "l": (1, 0)}
MENU = ["BOJ", "AKCE", "VĚCI", "MILOST"]

RESET = "\033[0m"
COLORS = {
    "@": "\033[1;97m", "#": "\033[90m", ".": "\033[2;37m", ",": "\033[32m",
    "T": "\033[1;32m", ">": "\033[1;36m", "$": "\033[1;33m", "!": "\033[1;35m",
    "M": "\033[1;34m", "*": "\033[1;93m", "D": "\033[1;31m",
    "~": "\033[34m", "F": "\033[38;5;208m",
    "r": "\033[31m", "g": "\033[32m", "s": "\033[35m", "O": "\033[91m",
}

# ---------------------------------------------------------------------------
#  Nepřátelé
#  pattern = vzor kulek, bch = znak kulky, acts = (název, text, změna nálady)
# ---------------------------------------------------------------------------
ENEMIES = [
    {
        "ch": "r", "name": "Krysa", "hp": 6, "atk": 2,
        "pattern": "rain", "bch": "v",
        "check": "Malá, hladová, trochu opuštěná.",
        "flavor": ["Krysa ti očichává boty.", "Krysa cosi pisklavě vzkazuje.",
                   "Krysí ocásek nervózně cukl."],
        "acts": [("Pohladit", "Krysa se přitulí. Asi ji ještě nikdo nepohladil.", 50),
                 ("Zapískat", "Krysa zvědavě nakloní hlavu.", 30),
                 ("Zařvat", "Krysa se naježí!", -20)],
        "art": [r"  ()_()",
                r"  (o.o)",
                r"  (> <)~"],
    },
    {
        "ch": "g", "name": "Goblin", "hp": 10, "atk": 3,
        "pattern": "sweep", "bch": "=",
        "check": "Má drobnou dýku a velké sebevědomí.",
        "flavor": ["Goblin si cvičně švihá dýkou.", "Goblin si něco zlostně mumlá.",
                   "Ve vzduchu voní zatuchlý sýr."],
        "acts": [("Pochválit dýku", "'Pěkná dýka!' Goblin zrudne až po uši.", 40),
                 ("Zatančit", "Goblin se přidá a dupe do rytmu.", 45),
                 ("Vyplázout jazyk", "Goblin se urazí.", -25)],
        "art": [r"   ,___, ",
                r"  ( >.< )",
                r" --|[_]|--",
                r"   /   \ "],
    },
    {
        "ch": "s", "name": "Pavouk", "hp": 14, "atk": 4,
        "pattern": "web", "bch": "x",
        "check": "Obří pavouk. Je moc rád, že tu někdo je.",
        "flavor": ["Pavouk si splétá cosi hedvábného.", "Osm očí na tebe hledí.",
                   "Pavučina se zlehka kolébá."],
        "acts": [("Zazpívat ukolébavku", "Pavouk si zívne. Všech osm očí se přivře.", 50),
                 ("Pochválit pavučinu", "Pavouk se začervená (všemi osmi očima).", 40),
                 ("Šáhnout do sítě", "Pavouk sebou škubne a naštve se.", -25)],
        "art": [r" /\    /\ ",
                r"/  \  /  \ ",
                r"\  (oo)  / ",
                r" /|    |\ "],
    },
    {
        "ch": "O", "name": "Ork", "hp": 22, "atk": 6,
        "pattern": "aim", "bch": "#",
        "check": "Svalnatý ork. Rád by byl obdivován.",
        "flavor": ["Ork si pohrává s palicí.", "Ork se napne, až mu zapraskají kosti.",
                   "Ork zamručel."],
        "acts": [("Pochválit svaly", "'Ty jsou ale mohutné!' Ork se nadme pýchou.", 50),
                 ("Přetlačit se", "Ork vyhraje a je z toho nadšený.", 40),
                 ("Urazit", "Ork zuří!", -30)],
        "art": [r"   ,===,  ",
                r"  ( >_< ) ",
                r" ,|[===]|,",
                r"   /   \  "],
    },
]

BOSS = {
    "ch": "D", "name": "Drak", "hp": 45, "atk": 9,
    "pattern": "boss", "bch": "%",
    "check": "Strážce amuletu. V očích má víc smutku než zloby.",
    "flavor": ["Drak vydechne obláček kouře.", "Drak sklopí oči k amuletu.",
               "Jeskyní zahučí tiché zavrčení."],
    "acts": [("Zazpívat", "Drak zaposlouchá. Z nozder mu vyjde srdíčko z dýmu.", 25),
             ("Pochválit poklad", "Drak se rozzáří pýchou.", 30),
             ("Sednout si vedle", "Drak se přestane tvářit hrozivě.", 30),
             ("Zeptat se na amulet", "'Byl jsem tu tak sám...' zašeptá drak.", 20),
             ("Vyplázout jazyk", "Drak zařve! Hodně.", -20)],
    "art": [r"       /\_/\  ",
            r"  ____/ o o \ ",
            r" /___    ^   >",
            r"     \_vvv_/~~"],
}

# název, základní cena, klíč
STOCK = [
    ("Léčivý lektvar (+1 do batohu)", 10, "potion"),
    ("Lepší meč (+2 útok)", 30, "atk"),
    ("Kožené brnění (+1 obrana)", 25, "df"),
    ("Srdce hrdinů (+10 max HP, plné léčení)", 40, "hp"),
]


# ---------------------------------------------------------------------------
#  Terminál
# ---------------------------------------------------------------------------
def clear():
    sys.stdout.write("\033[H\033[J")


def render(lines):
    """Překreslí obrazovku bez blikání."""
    sys.stdout.write("\033[H" + "".join(l + "\033[K\n" for l in lines) + "\033[J")
    sys.stdout.flush()


class RawMode:
    """Čtení kláves bez Enteru a skrytý kurzor po dobu hry."""

    def __enter__(self):
        if os.name != "nt":
            import termios
            import tty
            self.fd = sys.stdin.fileno()
            self.old = termios.tcgetattr(self.fd)
            tty.setcbreak(self.fd)
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()
        return self

    def __exit__(self, *exc):
        if os.name != "nt":
            import termios
            termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old)
        sys.stdout.write("\033[?25h" + RESET)
        sys.stdout.flush()


def _decode(data):
    if data.startswith("\x1b["):
        return {"A": "w", "B": "s", "D": "a", "C": "d"}.get(data[2:3], "")
    return data[:1]


def poll(timeout=None):
    """Vrátí stisknutou klávesu, "" pro neznámou, nebo None při vypršení času."""
    if os.name == "nt":
        import msvcrt
        end = None if timeout is None else time.time() + timeout
        while True:
            if msvcrt.kbhit():
                ch = msvcrt.getwch()
                if ch in ("\x00", "\xe0"):
                    return {"H": "w", "P": "s", "K": "a", "M": "d"}.get(msvcrt.getwch(), "")
                return ch
            if end is not None and time.time() >= end:
                return None
            time.sleep(0.005)
    import select
    fd = sys.stdin.fileno()
    if select.select([fd], [], [], timeout)[0]:
        return _decode(os.read(fd, 8).decode(errors="ignore"))
    return None


def getkey():
    """Čeká na klávesu."""
    while True:
        k = poll(None)
        if k is not None:
            return k


def tap(timeout, keys=ENTER):
    """True, pokud byla do timeoutu stisknuta jedna z kláves."""
    end = time.time() + timeout
    while True:
        rem = end - time.time()
        if rem <= 0:
            return False
        if poll(rem) in keys:
            return True


def pause(sec):
    time.sleep(sec * PAUSE / 0.6)


def sign(n):
    return (n > 0) - (n < 0)


# ---------------------------------------------------------------------------
#  Pomocné funkce pro boj
# ---------------------------------------------------------------------------
def bar(v, m, n=10):
    f = max(0, round(n * v / m)) if m else 0
    if v > 0:
        f = max(1, f)
    return "#" * f + "-" * (n - f)


def text_rows(text):
    rows = []
    for para in text.split("\n"):
        for ln in textwrap.wrap(para, BW - 2) or [""]:
            rows.append((" " + ln).ljust(BW))
    rows = rows[:BH]
    while len(rows) < BH:
        rows.append(" " * BW)
    return rows


def menu_line(idx):
    parts = []
    for i, name in enumerate(MENU):
        if i == idx:
            parts.append("\033[30;43m " + name + " " + RESET)
        else:
            parts.append("\033[2m " + name + " " + RESET)
    return "   " + "   ".join(parts)


def arena_rows(soul, bullets, color, blink):
    grid = [[" "] * BW for _ in range(BH)]
    for bx, by, _, _, ch in bullets:
        if 0 <= bx < BW and 0 <= by < BH:
            grid[by][bx] = color + ch + RESET
    sx, sy = soul
    grid[sy][sx] = ("\033[2;31m" if blink else "\033[1;31m") + "♥" + RESET
    return ["".join(r) for r in grid]


def spawn(pattern, t, bullets, soul, bch):
    """Přidá kulky podle vzoru. Kulka = [x, y, dx, dy, znak]."""
    def rain():
        bullets.append([random.randrange(BW), 0, 0, 1, bch])

    def sweep():
        y = random.randrange(BH)
        if random.random() < 0.5:
            bullets.append([0, y, 1, 0, bch])
        else:
            bullets.append([BW - 1, y, -1, 0, bch])

    def aim():
        side = random.randrange(4)
        if side == 0:
            bullets.append([soul[0], 0, 0, 1, bch])
        elif side == 1:
            bullets.append([soul[0], BH - 1, 0, -1, bch])
        elif side == 2:
            bullets.append([0, soul[1], 1, 0, bch])
        else:
            bullets.append([BW - 1, soul[1], -1, 0, bch])

    if pattern == "rain" and t % 2 == 0:
        rain()
    elif pattern == "sweep" and t % 3 == 0:
        sweep()
    elif pattern == "web" and t % 2 == 0:
        bullets.append([random.randrange(BW), 0, random.choice((-1, 0, 1)), 1, bch])
    elif pattern == "aim" and t % 4 == 0:
        aim()
    elif pattern == "boss":
        if t % 3 == 0:
            rain()
        if t % 7 == 0:
            sweep()
        if t % 9 == 4:
            aim()


class Game:
    def __init__(self):
        self.hp = self.maxhp = 30
        self.atk = 3
        self.df = 0
        self.gold = 0
        self.potions = 1
        self.depth = 0
        self.turn = 0
        self.kills = 0
        self.spared = 0
        self.fish_talks = 0
        self.bought = {}
        self.won = False
        self.dead = False
        self.log = []
        self.new_level()
        self.say("Vítej v Mechově! Zlatý Amulet zmizel. Nakup výbavu u 'M' a vyraz na '>'.")

    # ---------- pomocné ----------
    def say(self, text):
        self.log.append(text)

    def enemy_at(self, x, y):
        for e in self.enemies:
            if e["x"] == x and e["y"] == y:
                return e
        return None

    def free(self, x, y):
        return (self.grid[y][x] == "." and (x, y) not in self.items
                and (x, y) != self.merchant and (x, y) != (self.px, self.py)
                and not self.enemy_at(x, y))

    def rand_in(self, room):
        x0, y0, w, h = room
        for _ in range(60):
            x = random.randint(x0, x0 + w - 1)
            y = random.randint(y0, y0 + h - 1)
            if self.free(x, y):
                return x, y
        return None

    def make_enemy(self, template, x, y):
        e = dict(template)
        e.update(x=x, y=y, maxhp=template["hp"], mercy=0, cool=0)
        return e

    # ---------- generování světa ----------
    def new_level(self):
        self.items = {}
        self.enemies = []
        self.merchant = None
        self.fisher = None
        self.seen = set()
        if self.depth == 0:
            self.make_village()
        else:
            self.make_dungeon()

    def make_village(self):
        g = [[","] * W for _ in range(H)]
        for x in range(W):
            g[0][x] = g[H - 1][x] = "T"
        for y in range(H):
            g[y][0] = g[y][W - 1] = "T"
        for _ in range(50):
            x, y = random.randint(1, W - 2), random.randint(1, H - 2)
            if not (4 <= x <= 18 and 2 <= y <= 9) \
                    and not (38 <= x <= 52 and 1 <= y <= 6) \
                    and abs(x - 24) + abs(y - 12) > 2 \
                    and abs(x - 52) + abs(y - 14) > 2:
                g[y][x] = "T"
        for y in range(3, 9):          # obchod
            for x in range(6, 17):
                edge = x in (6, 16) or y in (3, 8)
                g[y][x] = "#" if edge else "."
        g[8][11] = "."                 # dveře
        g[14][52] = ">"                # vchod do jeskyní
        for y in range(2, 5):          # rybníček nahoře
            for x in range(40, 51):
                g[y][x] = "~"
        self.grid = g
        self.merchant = (11, 5)
        self.fisher = (45, 5)          # rybář na břehu
        self.px, self.py = 24, 12
        self.seen = {(x, y) for x in range(W) for y in range(H)}

    def make_dungeon(self):
        while True:
            g = [["#"] * W for _ in range(H)]
            rooms = []
            for _ in range(60):
                w, h = random.randint(5, 11), random.randint(3, 6)
                x, y = random.randint(1, W - w - 2), random.randint(1, H - h - 2)
                if any(x < rx + rw + 2 and rx < x + w + 2 and
                       y < ry + rh + 2 and ry < y + h + 2
                       for rx, ry, rw, rh in rooms):
                    continue
                rooms.append((x, y, w, h))
                for yy in range(y, y + h):
                    for xx in range(x, x + w):
                        g[yy][xx] = "."
                if len(rooms) == 8:
                    break
            if len(rooms) >= 4:
                break
        centers = [(r[0] + r[2] // 2, r[1] + r[3] // 2) for r in rooms]
        for (ax, ay), (bx, by) in zip(centers, centers[1:]):
            for x in range(min(ax, bx), max(ax, bx) + 1):
                g[ay][x] = "."
            for y in range(min(ay, by), max(ay, by) + 1):
                g[y][bx] = "."
        self.grid = g
        self.px, self.py = centers[0]
        lx, ly = centers[-1]

        if self.depth < FINAL_DEPTH:
            g[ly][lx] = ">"
        else:
            self.enemies.append(self.make_enemy(BOSS, lx, ly))
            self.say("Z hlubin se ozve zaburácení... Drak hlídá amulet!")

        pos = self.rand_in(rooms[len(rooms) // 2])
        if pos:
            self.merchant = pos

        pool = ENEMIES[max(0, self.depth - 2): self.depth + 1]
        for _ in range(3 + self.depth):
            pos = self.rand_in(random.choice(rooms[1:]))
            if pos:
                self.enemies.append(self.make_enemy(random.choice(pool), *pos))
        for _ in range(5):
            pos = self.rand_in(random.choice(rooms))
            if pos:
                self.items[pos] = ("$", random.randint(3, 8) + self.depth * 2)
        for _ in range(random.randint(1, 2)):
            pos = self.rand_in(random.choice(rooms))
            if pos:
                self.items[pos] = ("!", 1)
        self.say(f"Sestoupil jsi do patra {self.depth}.")

    # ---------- vykreslení světa ----------
    def draw(self):
        R = 7
        vis = set()
        for y in range(max(0, self.py - R), min(H, self.py + R + 1)):
            for x in range(max(0, self.px - R), min(W, self.px + R + 1)):
                if (x - self.px) ** 2 + (y - self.py) ** 2 <= R * R + 1:
                    vis.add((x, y))
        if self.depth == 0:
            vis = {(x, y) for x in range(W) for y in range(H)}
        self.seen |= vis

        out = []
        place = "Vesnice Mechov" if self.depth == 0 else f"Jeskyně, patro {self.depth}/{FINAL_DEPTH}"
        out.append(f" {place}   HP {max(0, self.hp)}/{self.maxhp}   Útok {self.atk}   "
                   f"Obrana {self.df}   Zlato {self.gold}   Lektvary {self.potions}")
        out.append("")
        for y in range(H):
            row = []
            for x in range(W):
                ch, dim = " ", False
                if (x, y) == (self.px, self.py):
                    ch = "@"
                elif (x, y) in vis:
                    e = self.enemy_at(x, y)
                    if e:
                        ch = e["ch"]
                    elif (x, y) == self.merchant:
                        ch = "M"
                    elif (x, y) == self.fisher:
                        ch = "F"
                    elif (x, y) in self.items:
                        ch = self.items[(x, y)][0]
                    else:
                        ch = self.grid[y][x]
                elif (x, y) in self.seen:
                    ch = self.grid[y][x]
                    dim = True
                if ch == " ":
                    row.append(" ")
                elif dim:
                    row.append("\033[2;90m" + ch + RESET)
                else:
                    row.append(COLORS.get(ch, "") + ch + RESET)
            out.append("".join(row))
        out.append("")
        for line in self.log[-4:]:
            out.append(" " + line)
        for _ in range(4 - len(self.log[-4:])):
            out.append("")
        out.append("")
        out.append(" [WASD/šipky] pohyb  [P] lektvar  [.] čekat  [Q] konec   (vraz do nepřítele = boj)")
        render(out)

    # ---------- obchod ----------
    def price(self, key, base):
        if key == "potion":
            return base
        return int(base * (1 + 0.5 * self.bought.get(key, 0)))

    def shop(self):
        note = "Hezký den, dobrodruhu! Co to bude?"
        while True:
            clear()
            print(f"=== OBCHODNÍK ===      Zlato: {self.gold}\n")
            for i, (name, base, key) in enumerate(STOCK, 1):
                print(f"  [{i}] {name:<42} {self.price(key, base):>3} zl.")
            print("\n  [Q] odejít\n")
            print(f"  {note}")
            k = getkey().lower()
            if k and k in "1234":
                name, base, key = STOCK[int(k) - 1]
                cost = self.price(key, base)
                if self.gold < cost:
                    note = "To nemáš na zaplacení, příteli."
                    continue
                self.gold -= cost
                self.bought[key] = self.bought.get(key, 0) + 1
                if key == "potion":
                    self.potions += 1
                elif key == "atk":
                    self.atk += 2
                elif key == "df":
                    self.df += 1
                elif key == "hp":
                    self.maxhp += 10
                    self.hp = self.maxhp
                note = "Děkuji! Příště zase."
            elif k in ("q", "\x1b", "\r", "\n", " "):
                return

    # ---------- rybář (easter egg) ----------
    def talk_fisher(self):
        art = ["    _/\\_     ",
               "   ( -.- )    ",
               "   /|   |\\___ ",
               "  / |___|     ",
               "      ><(((o> "]
        story = [
            "Pšt... Neplaš mi ryby. Ne že by tu nějaké byly.",
            "Sedím tu třicet let. Chytil jsem jednu botu. Byla to dobrá bota.",
            "Dole v jeskyních bydlí drak. Dřív sem chodíval, sedl si vedle mě a koukal na vodu.",
            "Je smutný, víš? Kdo se k němu zachová hezky, toho nespálí. Jen tak povídám.",
        ]
        later = [
            "Zabírá! ...Ne, to byl jen list.",
            "Hm? Jo, ahoj. Pšt.",
            "Rybáři nespí. Rybáři čekají.",
            "Řeknu ti tajemství: ryby tu nejsou. Ale ticho jo.",
        ]
        n = self.fish_talks
        self.fish_talks += 1
        gift = False
        if n < len(story):
            text = story[n]
        elif n == len(story):
            text = "Na, vem si tuhle rybí polévku. Ne, nevím, z čeho je."
            self.potions += 1
            gift = True
            self.say("Rybář ti dal rybí polévku (+1 lektvar).")
        else:
            text = random.choice(later)
        clear()
        print()
        for ln in art:
            print("   " + COLORS["F"] + ln + RESET)
        print("\n   " + COLORS["F"] + "Rybář:" + RESET)
        for ln in textwrap.wrap(text, 56):
            print("   " + ln)
        if gift:
            print("\n   \033[1;35m+1 lektvar (rybí polévka)\033[0m")
        print("\n   \033[2m[Enter] pokračovat\033[0m")
        while getkey().lower() not in ENTER:
            pass

    # =======================================================================
    #  BOJ (Undertale styl)
    # =======================================================================
    def battle_screen(self, e, rows, menu_idx=None, hint=""):
        col = COLORS.get(e["ch"], "")
        lines = [""]
        for i in range(5):
            art = e["art"][i] if i < len(e["art"]) else ""
            lines.append("   " + col + art + RESET)
        name_col = "\033[1;33m" if e["mercy"] >= 100 else "\033[1;37m"
        lines.append(f"   {name_col}{e['name']}{RESET}   HP [{bar(e['hp'], e['maxhp'])}] "
                     f"{max(0, e['hp'])}/{e['maxhp']}")
        lines.append("")
        lines.append("  +" + "-" * BW + "+")
        for r in rows:
            lines.append("  |" + r + "|")
        lines.append("  +" + "-" * BW + "+")
        lines.append(f"  \033[1;31m♥\033[0m HP {max(0, self.hp)}/{self.maxhp} [{bar(self.hp, self.maxhp)}]"
                     f"   Útok {self.atk}  Obrana {self.df}  Lektvary {self.potions}")
        lines.append(menu_line(menu_idx))
        lines.append("  \033[2m" + hint + RESET)
        render(lines)

    def show_text(self, e, text, menu_idx=None):
        self.battle_screen(e, text_rows(text), menu_idx, "[Enter] pokračovat")
        while getkey().lower() not in ENTER:
            pass

    def main_menu(self, e, msg, sel):
        rows = text_rows(msg)
        while True:
            self.battle_screen(e, rows, sel, "[A/D] výběr  [Enter] potvrdit")
            k = getkey().lower()
            if k == "a":
                sel = (sel - 1) % 4
            elif k == "d":
                sel = (sel + 1) % 4
            elif k in ENTER:
                return sel
            elif k in ("1", "2", "3", "4"):
                return int(k) - 1

    def pick(self, e, options, menu_idx):
        """Podmenu v rámečku. Vrací index, nebo None (zpět)."""
        sel = 0
        while True:
            rows = []
            for i, o in enumerate(options):
                row = (" > " if i == sel else "   ") + o
                row = row.ljust(BW)
                rows.append("\033[1;33m" + row + RESET if i == sel else row)
            while len(rows) < BH:
                rows.append(" " * BW)
            self.battle_screen(e, rows[:BH], menu_idx, "[W/S] výběr  [Enter] potvrdit  [Q] zpět")
            k = getkey().lower()
            if k == "w":
                sel = (sel - 1) % len(options)
            elif k == "s":
                sel = (sel + 1) % len(options)
            elif k in ENTER:
                return sel
            elif k in ("q", "x", "\x1b"):
                return None

    def drop_loot(self, e, spared=False):
        pos = (e["x"], e["y"])
        if e["ch"] == "D":
            self.items[pos] = ("*", 0)
        elif spared and random.random() < 0.25:
            self.items[pos] = ("!", 1)
        else:
            bonus = 2 if spared else 0
            self.items[pos] = ("$", random.randint(2, 6) + self.depth * 2 + bonus)

    # --- BOJ: časování útoku ---
    def do_fight(self, e):
        center = BW // 2
        hit = None
        for pos in range(BW):
            rows = [" " * BW for _ in range(BH)]
            rows[1] = "Zmáčkni ENTER do středu!".center(BW)
            cells = []
            for i in range(BW):
                if i == pos:
                    cells.append("\033[1;31m#\033[0m")
                elif i == center:
                    cells.append("+")
                else:
                    cells.append("-")
            rows[3] = "".join(cells)
            rows[4] = " " * center + "^" + " " * (BW - center - 1)
            self.battle_screen(e, rows, 0, "[Enter] udeř!")
            if tap(BAR_STEP):
                hit = pos
                break
        if hit is None:
            return ("* Zaváhal jsi a minul.", False)
        dist = abs(hit - center)
        mult = max(0.3, 2.0 - dist * 0.12)
        dmg = max(1, int(self.atk * mult) + random.randint(0, 1))
        e["hp"] -= dmg
        rows = [" " * BW for _ in range(BH)]
        rows[3] = f"-{dmg}".center(BW)
        self.battle_screen(e, rows, 0, "")
        pause(0.8)
        if e["hp"] <= 0:
            self.enemies.remove(e)
            self.kills += 1
            self.drop_loot(e)
            if e["ch"] == "D":
                return ("* DRAK PADL! Na zemi září Zlatý Amulet!", True)
            return (f"* Porazil jsi: {e['name']}.", True)
        perfect = " Přesně do středu!" if dist <= 1 else ""
        return (f"* Zasáhl jsi: {e['name']} za {dmg}.{perfect}", False)

    # --- AKCE ---
    def do_act(self, e):
        names = ["Prozkoumat"] + [a[0] for a in e["acts"]]
        i = self.pick(e, names, 1)
        if i is None:
            return None
        if i == 0:
            return (f"* {e['name'].upper()} - ÚTOK {e['atk']}, HP {e['hp']}/{e['maxhp']}. "
                    f"{e['check']} Nálada: {e['mercy']} %.", False)
        _, text, delta = e["acts"][i - 1]
        e["mercy"] = max(0, min(100, e["mercy"] + delta))
        text = "* " + text
        if e["mercy"] >= 100:
            text += f" {e['name']} se už nechce bít."
        return (text, False)

    # --- VĚCI ---
    def do_item(self, e):
        label = f"Léčivý lektvar x{self.potions}" if self.potions > 0 else "(batoh je prázdný)"
        i = self.pick(e, [label], 2)
        if i is None or self.potions <= 0:
            return None
        heal = min(15, self.maxhp - self.hp)
        self.potions -= 1
        self.hp += heal
        return (f"* Vypil jsi lektvar. Léčí {heal} HP.", False)

    # --- MILOST ---
    def do_mercy(self, e):
        i = self.pick(e, ["Ušetřit", "Utéct"], 3)
        if i is None:
            return None
        if i == 0:
            if e["mercy"] < 100:
                return (f"* {e['name']} se zatím nechce vzdát.", False)
            self.enemies.remove(e)
            self.spared += 1
            self.drop_loot(e, spared=True)
            if e["ch"] == "D":
                return ("* Drak dlouze vydechne a položí amulet na zem. "
                        "'Dávej na něj pozor...'", True)
            return (f"* Ušetřil jsi: {e['name']}. Odchází pryč.", True)
        if e["ch"] == "D":
            return ("* Drak ti zahradil cestu. Neutečeš!", False)
        if random.random() < 0.6:
            e["cool"] = 4
            return ("* Utekl jsi!", True)
        return ("* Nepodařilo se utéct!", False)

    # --- Kolo nepřítele: uhýbání kulkám ---
    def dodge(self, e):
        soul = [BW // 2, BH // 2]
        bullets = []
        frames = 60 if e["ch"] == "D" else 36
        dmg = max(1, e["atk"] // 2 - self.df)
        col = COLORS.get(e["ch"], "")
        ifr = 0

        def hit():
            nonlocal ifr
            if ifr == 0 and any(b[0] == soul[0] and b[1] == soul[1] for b in bullets):
                self.hp -= dmg
                ifr = 8

        def show():
            self.battle_screen(e, arena_rows(soul, bullets, col, ifr > 0), None,
                               "[W A S D / šipky] uhýbej srdíčku!")

        for t in range(frames):
            spawn(e["pattern"], t, bullets, soul, e["bch"])
            deadline = time.time() + FRAME
            show()
            moved = 0
            while True:
                rem = deadline - time.time()
                if rem <= 0:
                    break
                k = poll(rem)
                if k in MOVES and moved < 2:
                    moved += 1
                    dx, dy = MOVES[k]
                    soul[0] = min(BW - 1, max(0, soul[0] + dx))
                    soul[1] = min(BH - 1, max(0, soul[1] + dy))
                    hit()
                    show()
            for b in bullets:
                b[0] += b[2]
                b[1] += b[3]
            bullets[:] = [b for b in bullets if 0 <= b[0] < BW and 0 <= b[1] < BH]
            hit()
            if ifr > 0:
                ifr -= 1
            if self.hp <= 0:
                self.hp = 0
                return

    def battle(self, e):
        if e["ch"] == "D":
            msg = "* Drak zvedne hlavu. V tlamě mu cosi zlatě září..."
        else:
            msg = f"* {e['name']} ti zastoupil cestu!"
        sel = 0
        while True:
            sel = self.main_menu(e, msg, sel)
            res = (self.do_fight, self.do_act, self.do_item, self.do_mercy)[sel](e)
            if res is None:            # zrušeno v podmenu, kolo se nepočítá
                msg = "* ..."
                continue
            text, ended = res
            self.show_text(e, text, sel)
            if ended:
                self.log.append(text)
                return
            self.dodge(e)
            if self.hp <= 0:
                self.dead = True
                return
            msg = "* " + random.choice(e["flavor"])

    # ---------- tahy ve světě ----------
    def move(self, dx, dy):
        nx, ny = self.px + dx, self.py + dy
        if not (0 <= nx < W and 0 <= ny < H):
            return False
        e = self.enemy_at(nx, ny)
        if e:
            self.battle(e)
            return False
        if (nx, ny) == self.merchant:
            self.shop()
            return False
        if (nx, ny) == self.fisher:
            self.talk_fisher()
            return False
        tile = self.grid[ny][nx]
        if tile in "#T~":
            return False
        self.px, self.py = nx, ny
        if (nx, ny) in self.items:
            ch, val = self.items.pop((nx, ny))
            if ch == "$":
                self.gold += val
                self.say(f"Sebral jsi {val} zlaťáků.")
            elif ch == "!":
                self.potions += 1
                self.say("Našel jsi léčivý lektvar!")
            elif ch == "*":
                self.won = True
        if tile == ">":
            self.depth += 1
            self.new_level()
        return True

    def drink(self):
        if self.potions <= 0:
            self.say("Nemáš žádný lektvar.")
            return False
        if self.hp >= self.maxhp:
            self.say("Jsi zdravý jako rybička.")
            return False
        self.potions -= 1
        self.hp = min(self.maxhp, self.hp + 15)
        self.say("Vypil jsi lektvar (+15 HP).")
        return True

    def enemy_phase(self):
        for e in list(self.enemies):
            if e not in self.enemies:
                continue
            if e["cool"] > 0:
                e["cool"] -= 1
                continue
            dist = abs(e["x"] - self.px) + abs(e["y"] - self.py)
            if dist == 1:
                self.battle(e)
                if self.dead or self.won:
                    return
                continue
            steps = []
            if dist <= 8:
                dx, dy = sign(self.px - e["x"]), sign(self.py - e["y"])
                ax, ay = abs(self.px - e["x"]), abs(self.py - e["y"])
                steps = [(dx, 0), (0, dy)] if ax >= ay else [(0, dy), (dx, 0)]
            elif random.random() < 0.3:
                steps = [random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])]
            for sx, sy in steps:
                if (sx, sy) == (0, 0):
                    continue
                nx, ny = e["x"] + sx, e["y"] + sy
                if self.grid[ny][nx] in ".," and (nx, ny) != (self.px, self.py) \
                        and (nx, ny) != self.merchant and not self.enemy_at(nx, ny):
                    e["x"], e["y"] = nx, ny
                    break

    def end_turn(self):
        self.turn += 1
        self.enemy_phase()
        if self.turn % 8 == 0 and self.hp < self.maxhp and not self.dead:
            self.hp += 1
        if self.hp <= 0:
            self.dead = True

    # ---------- hlavní smyčka ----------
    def run(self):
        while True:
            self.draw()
            if self.won:
                print("\n  *** VYHRÁL JSI! Zlatý Amulet je zpátky v Mechově! ***")
                if self.kills == 0:
                    print("  A to bez jediného zabití. Mechov má nejlaskavějšího hrdinu!")
                print(f"  Zabil jsi: {self.kills}, ušetřil: {self.spared}, "
                      f"tahů: {self.turn}, zlata: {self.gold}.\n")
                return
            if self.dead:
                print("\n  *** Padl jsi v hlubinách... ***")
                print(f"  Patro {self.depth}, zabil jsi: {self.kills}, ušetřil: {self.spared}.\n")
                return
            k = getkey().lower()
            acted = False
            if k in MOVES:
                acted = self.move(*MOVES[k])
            elif k == "p":
                acted = self.drink()
            elif k == ".":
                acted = True
            elif k == "q":
                print("\n  Na shledanou!\n")
                return
            if acted:
                self.end_turn()


def main():
    if os.name == "nt":
        os.system("")              # zapne ANSI barvy ve Windows
        os.system("chcp 65001 >nul")
    try:
        with RawMode():
            while True:
                Game().run()
                print("  Hrát znovu? [A/N]")
                if getkey().lower() != "a":
                    break
    except KeyboardInterrupt:
        print("\n  Na shledanou!\n")


if __name__ == "__main__":
    main()