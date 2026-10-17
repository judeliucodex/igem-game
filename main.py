# -*- coding: utf-8 -*-
"""
================================================================================
  MICROBE WARS : VOID EDITION  /  微生物大戰：虛空版            v4.0
  單一檔案 / Single file       需要 pygame 2.x  (pip install pygame)
  選配 / Optional: pip install pillow   -> 讀取 GIF 全部影格
--------------------------------------------------------------------------------
  設計準則 / Design rules
    * 無圓角、無圓形 (no rounded corners, no circles) - 全部稜角幾何
    * 背景只有星空 (starfield only)
    * 可互動地形 (interactive terrain) / 元素反應 / BREAK / EXECUTE / OVERDRIVE
  自訂素材：1.gif = 小怪, 2.gif = 首領  (也支援 png/webp/jpg)
================================================================================
"""

import os
import sys
import math
import platform
import random
import json
import array
import asyncio
import traceback

import pygame

# ==============================================================================
#  常數 / 調色盤
# ==============================================================================
LW, LH = 960, 540
GROUND_Y = 470
FPS_CAP = 60

try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except NameError:
    BASE_DIR = os.getcwd()
CFG_PATH = os.path.join(BASE_DIR, "microbe_wars_void.json")

# 瀏覽器版 (pygbag / WebAssembly) / running in the browser via pygbag
IS_WEB = sys.platform == "emscripten"
IS_ANDROID = ("ANDROID_ARGUMENT" in os.environ) or (getattr(sys, "getandroidapilevel", None) is not None)
EV_FDOWN = getattr(pygame, "FINGERDOWN", -101)
EV_FUP = getattr(pygame, "FINGERUP", -102)
EV_FMOVE = getattr(pygame, "FINGERMOTION", -103)

VOID = (3, 4, 8)
INK = (9, 11, 18)
STEEL = (24, 28, 38)
PLATE = (38, 44, 58)
EDGE = (64, 74, 96)
GREY = (118, 128, 150)
DIM = (66, 74, 92)
WHT = (234, 242, 255)
CYAN = (78, 232, 255)
MAG = (255, 62, 150)
AMB = (255, 176, 48)
LIME = (152, 255, 108)
VIOL = (172, 110, 255)
RED = (255, 66, 74)
ICE = (168, 232, 255)
GOLD = (255, 206, 88)
BLOOD = (214, 44, 70)
TOXIC = (142, 255, 120)


def clamp(v, a, b):
    return a if v < a else (b if v > b else v)


def lerp(a, b, t):
    return a + (b - a) * t


def sgn(v):
    return -1 if v < 0 else (1 if v > 0 else 0)


def mix(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)), int(lerp(c1[2], c2[2], t)))


def dk(c, f=.45):
    return (int(c[0] * f), int(c[1] * f), int(c[2] * f))


def wchoice(pairs):
    if not pairs:
        return None
    tot = 0.0
    for _, w in pairs:
        tot += max(0.0, w)
    if tot <= 0:
        return pairs[0][0]
    r = random.uniform(0, tot)
    for k, w in pairs:
        r -= max(0.0, w)
        if r <= 0:
            return k
    return pairs[-1][0]


# ==============================================================================
#  文字 / Localisation
# ==============================================================================
LANG = "zh"

TXT = {
    "title": ("MICROBE WARS", "微生物大戰"),
    "sub": ("VOID EDITION", "虛空版"),
    "m_campaign": ("Campaign", "戰役"),
    "m_endless": ("Endless", "無盡"),
    "m_bossrush": ("Boss Rush", "首領連戰"),
    "m_time": ("Time Attack", "限時"),
    "m_chaos": ("Chaos", "混沌"),
    "m_practice": ("Practice", "練習場"),
    "settings": ("Settings", "設定"),
    "help": ("Briefing", "操作說明"),
    "quit": ("Quit", "離開"),
    "language": ("Language", "語言"),
    "back": ("Back", "返回"),
    "nav_hint": ("Arrows / Mouse / Touch - ENTER to confirm", "方向鍵、滑鼠或觸控選擇，ENTER 確認"),
    "sel_title": ("DEPLOY UNIT", "出擊配置"),
    "microbe": ("Unit", "單位"),
    "weapon": ("Weapon", "武器"),
    "difficulty": ("Threat", "威脅度"),
    "skill": ("Skill", "技能"),
    "alt": ("ALT", "副武器"),
    "start": ("DEPLOY", "出擊"),
    "atk": ("PWR", "火力"),
    "spd": ("SPD", "速度"),
    "hp": ("INT", "結構"),
    "sup": ("ULT", "終極"),
    "d0": ("Low", "低"),
    "d1": ("Normal", "普通"),
    "d2": ("High", "高"),
    "d3": ("Lethal", "致命"),
    "d4": ("Void", "虛空"),
    "set_title": ("SETTINGS", "設定"),
    "graphics": ("Render", "畫質"),
    "g_low": ("Low", "低"),
    "g_mid": ("Mid", "中"),
    "g_high": ("High", "高"),
    "g_ultra": ("Ultra", "極致"),
    "g_auto": ("Auto", "自動"),
    "touchctl": ("Touch Pad", "觸控操作"),
    "volume": ("Volume", "音量"),
    "fullscreen": ("Fullscreen", "全螢幕"),
    "showfps": ("Show FPS", "顯示 FPS"),
    "sprites": ("Custom Sprites", "自訂素材"),
    "shakeopt": ("Screen Shake", "畫面震動"),
    "on": ("ON", "開"),
    "off": ("OFF", "關"),
    "help_title": ("BRIEFING", "操作說明"),
    "h1": ("Move A/D - Jump W - Dash K", "移動 A/D　跳躍 W　衝刺 K"),
    "h2": ("Fire SPACE/J - ALT fire L - Ultimate Z", "主攻擊 SPACE/J　副武器 L　終極 Z"),
    "h3": ("Skill C - Overdrive X - Guard SHIFT - Reload R", "技能 C　超載 X　防禦 SHIFT　換彈 R"),
    "h4": ("Weapon Q/E or 1-7 - Pause ESC - Fullscreen F11", "武器 Q/E 或 1-7　暫停 ESC　全螢幕 F11"),
    "h5": ("GUARD just before impact = PARRY -> RIPOSTE window.", "受擊瞬間防禦＝彈反，開啟反擊窗口。"),
    "h6": ("Hits build STAGGER. Full bar = BREAK (stun + 35% dmg).", "攻擊累積架勢，滿表 BREAK（暈眩＋受傷 +35%）。"),
    "h7": ("Strike from behind for WEAK POINT bonus damage.", "從背後攻擊觸發弱點加傷。"),
    "h8": ("Low HP enemies can be EXECUTED by melee.", "殘血敵人可被近戰處決。"),
    "h9": ("Elements react: BURN+SHOCK overload, CHILL+BLEED shatter,", "元素會反應：燃燒+電擊＝過載，冰緩+流血＝碎裂，"),
    "h10": ("BURN+CORRODE meltdown, SHOCK+CHILL superconduct (armor 0).", "燃燒+腐蝕＝熔毀，電擊+冰緩＝超導（破甲）。"),
    "h11": ("Shoot BARRELS for chain blasts. Break CRATES for loot.", "打爆裂桶可連鎖爆炸，打破箱子會掉補給。"),
    "h12": ("PYLONS shield nearby foes - destroy them first.", "護盾塔會替周圍敵人補盾，優先破壞。"),
    "h13": ("Wave AFFIX shown top-center changes the rules.", "畫面上方顯示的波次詞綴會改變規則。"),
    "h_asset": ("Place 1.gif / 2.gif beside the game for custom art.", "把 1.gif／2.gif 放在遊戲旁可使用自訂美術。"),
    "asset_on": ("Custom sprites loaded", "已載入自訂素材"),
    "asset_off": ("Built-in vector art", "使用內建幾何美術"),
    "lv": ("LV", "等級"),
    "score": ("SCORE", "分數"),
    "stage": ("SECTOR", "區域"),
    "wave": ("WAVE", "波次"),
    "kills": ("KILLS", "擊殺"),
    "combo": ("CHAIN", "連段"),
    "time": ("TIME", "時間"),
    "left": ("HOSTILES", "敵數"),
    "next_wave": ("Next wave {0}", "{0} 秒後下一波"),
    "wave_go": ("WAVE {0}", "第 {0} 波"),
    "wave_clear": ("WAVE CLEAR", "波次肅清"),
    "stage_clear": ("SECTOR {0} CLEAR", "第 {0} 區肅清"),
    "boss_warn": ("WARNING - APEX UNIT", "警告－首領單位"),
    "levelup": ("LEVEL UP", "等級提升"),
    "pick_card": ("SELECT AUGMENT", "選擇強化模組"),
    "pick_hint": ("Press 1 / 2 / 3 or tap", "按 1／2／3 或點選"),
    "parry": ("PARRY", "彈反"),
    "riposte": ("RIPOSTE", "反擊"),
    "brk": ("BREAK", "架勢崩潰"),
    "weak": ("WEAK", "弱點"),
    "exec": ("EXECUTE", "處決"),
    "overload": ("OVERLOAD", "過載"),
    "meltdown": ("MELTDOWN", "熔毀"),
    "shatter": ("SHATTER", "碎裂"),
    "supercon": ("SUPERCONDUCT", "超導"),
    "overdrive": ("OVERDRIVE", "超載"),
    "overheat": ("OVERHEAT", "過熱"),
    "reloading": ("RELOAD", "換彈"),
    "paused": ("PAUSED", "暫停"),
    "resume": ("Resume", "繼續"),
    "restart": ("Restart", "重新開始"),
    "tomenu": ("Main Menu", "回主選單"),
    "gameover": ("SIGNAL LOST", "訊號中斷"),
    "victory": ("SECTOR SECURED", "任務完成"),
    "r_score": ("Score {0}", "分數 {0}"),
    "r_best": ("Best {0}", "最高 {0}"),
    "r_new": ("NEW RECORD", "新紀錄"),
    "r_kills": ("Kills {0}", "擊殺 {0}"),
    "r_reach": ("Sector {0} - Wave {1}", "第 {0} 區 第 {1} 波"),
    "r_time": ("Time {0}s", "時間 {0} 秒"),
    "err": ("Fault contained - returned to menu", "發生異常，已返回主選單"),
    "fps": ("FPS", "FPS"),
    "phase": ("PHASE {0}", "階段 {0}"),
    "rarity0": ("COMMON", "普通"),
    "rarity1": ("RARE", "稀有"),
    "rarity2": ("EPIC", "史詩"),
    "af_none": ("CLEAR", "無詞綴"),
    "af_frenzy": ("FRENZY", "狂暴"),
    "af_hard": ("HARDENED", "硬化"),
    "af_volatile": ("VOLATILE", "不穩定"),
    "af_swarm": ("SWARM", "蟲群"),
    "af_lowg": ("LOW GRAVITY", "低重力"),
    "af_static": ("STATIC FIELD", "靜電場"),
    "af_vamp": ("VAMPIRIC", "吸血"),
    "af_shield": ("SHIELDED", "護盾化"),
    "af_hunt": ("HUNTERS", "追獵"),
}


def T(k, *a):
    e = TXT.get(k)
    if not e:
        return str(k)
    s = e[0] if LANG == "en" else e[1]
    if a:
        try:
            s = s.format(*a)
        except Exception:
            pass
    return s


def L(d, f):
    return d.get(f + ("_en" if LANG == "en" else "_zh"), d.get(f + "_en", ""))


# ==============================================================================
#  字型
# ==============================================================================
class FontMgr:
    CAND = ["microsoftjhenghei", "microsoftyahei", "msjh", "msyh", "notosanscjktc", "notosanscjksc",
            "notosanstc", "notosanssc", "sourcehansanstc", "pingfangtc", "pingfang", "stheiti",
            "heiti", "simhei", "simsun", "wqymicrohei", "wqyzenhei",
            "droidsansfallback", "arialunicodems", "unifont"]

    def __init__(self):
        self.path = self._find()
        self.cjk = bool(self.path) and self._ok(self.path)
        self.cache = {}

    def _find(self):
        for n in ("font.ttf", "font.otf", "font.ttc"):
            p = os.path.join(BASE_DIR, n)
            if os.path.isfile(p):
                return p
        for n in self.CAND:
            try:
                p = pygame.font.match_font(n)
            except Exception:
                p = None
            if p and self._ok(p):
                return p
        hints = ("hei", "ming", "song", "cjk", "gothic", "noto", "pingfang", "unifont", "fallback", "arialuni")
        try:
            names = pygame.font.get_fonts()
        except Exception:
            names = []
        for n in names:
            if any(h in n for h in hints):
                try:
                    p = pygame.font.match_font(n)
                except Exception:
                    p = None
                if p and self._ok(p):
                    return p
        return None

    @staticmethod
    def _ok(path):
        try:
            f = pygame.font.Font(path, 30)
            s = f.render("微生物戰", True, (255, 255, 255))
            return pygame.mask.from_surface(s).count() > 30
        except Exception:
            return False

    def get(self, px):
        px = int(clamp(px, 8, 260))
        f = self.cache.get(px)
        if f is None:
            try:
                f = pygame.font.Font(self.path, px) if self.path else pygame.font.Font(None, px)
            except Exception:
                try:
                    f = pygame.font.Font(None, px)
                except Exception:
                    f = pygame.font.SysFont("sans", px)
            if len(self.cache) > 40:
                self.cache.clear()
            self.cache[px] = f
        return f


# ==============================================================================
#  Painter : 只有稜角 / angular only
# ==============================================================================
class Painter:
    def __init__(self, fonts):
        self.s = None
        self.k = 1.0
        self.ox = 0.0
        self.oy = 0.0
        self.fonts = fonts
        self._glow = {}
        self._txt = {}
        self._pan = {}
        self._flash = None
        self.clips = []

    def begin(self, surf, k):
        self.s = surf
        self.k = k
        self.ox = 0.0
        self.oy = 0.0
        self.clips = []
        try:
            surf.set_clip(None)
        except Exception:
            pass

    def offset(self, x, y):
        self.ox = x
        self.oy = y

    def clear_cache(self):
        self._glow.clear()
        self._txt.clear()
        self._pan.clear()
        self._flash = None

    # --- transform ---
    def P(self, p):
        return (int((p[0] + self.ox) * self.k), int((p[1] + self.oy) * self.k))

    def R(self, r):
        if isinstance(r, pygame.Rect):
            x, y, w, h = r.x, r.y, r.w, r.h
        else:
            x, y, w, h = r
        k = self.k
        return pygame.Rect(int((x + self.ox) * k), int((y + self.oy) * k),
                           max(1, int(w * k)), max(1, int(h * k)))

    def W(self, w):
        return 0 if w <= 0 else max(1, int(round(w * self.k)))

    def push_clip(self, rect):
        r = self.R(rect)
        cur = self.s.get_clip()
        self.clips.append(cur)
        if cur is not None:
            r = r.clip(cur)
        self.s.set_clip(r)

    def pop_clip(self):
        if self.clips:
            self.s.set_clip(self.clips.pop())

    # --- 基本圖形（全稜角） ---
    def rect(self, c, r, width=0):
        pygame.draw.rect(self.s, c, self.R(r), self.W(width))

    def line(self, c, a, b, w=1):
        pygame.draw.line(self.s, c, self.P(a), self.P(b), max(1, int(w * self.k)))

    def poly(self, c, pts, width=0):
        if len(pts) < 3:
            return
        pygame.draw.polygon(self.s, c, [self.P(p) for p in pts], self.W(width))

    def sq(self, c, pos, r, width=0):
        self.rect(c, (pos[0] - r, pos[1] - r, r * 2, r * 2), width)

    def dia(self, c, pos, r, ry=None, width=0):
        ry = r if ry is None else ry
        x, y = pos
        self.poly(c, [(x, y - ry), (x + r, y), (x, y + ry), (x - r, y)], width)

    def hexa(self, c, pos, rx, ry=None, width=0, rot=0.0):
        ry = rx if ry is None else ry
        x, y = pos
        pts = []
        for i in range(6):
            a = rot + i * math.tau / 6
            pts.append((x + math.cos(a) * rx, y + math.sin(a) * ry))
        self.poly(c, pts, width)

    def ngon(self, c, pos, rx, ry=None, n=5, rot=0.0, width=0):
        ry = rx if ry is None else ry
        n = int(clamp(n, 3, 8))
        x, y = pos
        pts = []
        for i in range(n):
            a = rot + i * math.tau / n
            pts.append((x + math.cos(a) * rx, y + math.sin(a) * ry))
        self.poly(c, pts, width)

    def tri(self, c, pos, r, dirn=0, width=0):
        x, y = pos
        if dirn == 0:
            self.poly(c, [(x, y - r), (x + r, y + r), (x - r, y + r)], width)
        elif dirn == 1:
            self.poly(c, [(x, y + r), (x + r, y - r), (x - r, y - r)], width)
        elif dirn == 2:
            self.poly(c, [(x + r, y), (x - r, y - r), (x - r, y + r)], width)
        else:
            self.poly(c, [(x - r, y), (x + r, y - r), (x + r, y + r)], width)

    def chev(self, c, pos, r, f=1, w=3):
        x, y = pos
        self.line(c, (x - r * f, y - r), (x + r * f * .3, y), w)
        self.line(c, (x + r * f * .3, y), (x - r * f, y + r), w)

    def xmark(self, c, pos, r, w=2):
        x, y = pos
        self.line(c, (x - r, y - r), (x + r, y + r), w)
        self.line(c, (x + r, y - r), (x - r, y + r), w)

    def frame(self, c, r, w=2, cut=8):
        pts = self.cpts(r, cut)
        self.poly(c, pts, w)

    def cpts(self, r, cut=8):
        if isinstance(r, pygame.Rect):
            x, y, w, h = r.x, r.y, r.w, r.h
        else:
            x, y, w, h = r
        c = min(cut, w * .45, h * .45)
        return [(x + c, y), (x + w - c, y), (x + w, y + c), (x + w, y + h - c),
                (x + w - c, y + h), (x + c, y + h), (x, y + h - c), (x, y + c)]

    def arcpoly(self, ctr, rad, a0, a1, c, w=3, ry=None):
        """折線弧（用直線段組，不是圓）"""
        ry = rad if ry is None else ry
        span = a1 - a0
        if abs(span) < 1e-4:
            return
        n = int(clamp(abs(span) * rad * self.k / 14.0, 3, 16))
        px = None
        for i in range(n + 1):
            a = a0 + span * i / n
            p = (ctr[0] + math.cos(a) * rad, ctr[1] + math.sin(a) * ry)
            if px is not None:
                self.line(c, px, p, w)
            px = p

    def shadow(self, cx, y, w, a=110):
        col = (0, 0, 0)
        self.poly(col, [(cx - w * .5, y), (cx + w * .5, y), (cx + w * .32, y + 5), (cx - w * .32, y + 5)])

    def panel(self, r, fill=(10, 13, 22, 225), border=EDGE, cut=9, bw=2, tab=False):
        rr = self.R(r)
        key = (rr.w, rr.h, fill, border, int(cut * self.k), self.W(bw), tab)
        s = self._pan.get(key)
        if s is None:
            s = pygame.Surface((rr.w, rr.h), pygame.SRCALPHA)
            pts = self.cpts((0, 0, rr.w, rr.h), cut * self.k)
            pygame.draw.polygon(s, fill, pts)
            if border:
                pygame.draw.polygon(s, border, pts, max(1, self.W(bw)))
                if tab:
                    pygame.draw.line(s, border, (0, int(cut * self.k * 1.6)),
                                     (rr.w, int(cut * self.k * 1.6)), max(1, self.W(1)))
            if len(self._pan) > 90:
                self._pan.clear()
            self._pan[key] = s
        self.s.blit(s, rr.topleft)

    def glow(self, pos, rad, color, inten=1.0):
        r = int(clamp(rad * self.k, 2, 420))
        q = int(clamp(inten, .08, 1.0) * 4)
        key = (r, color, q)
        g = self._glow.get(key)
        if g is None:
            f0 = q / 4.0
            g = pygame.Surface((r * 2, r * 2))
            g.fill((0, 0, 0))
            steps = int(clamp(r // 3, 4, 13))
            for i in range(steps, 0, -1):
                rr = r * i / float(steps)
                f = ((1.0 - i / float(steps)) ** 1.85) * f0
                c = (int(clamp(color[0] * f, 0, 255)), int(clamp(color[1] * f, 0, 255)),
                     int(clamp(color[2] * f, 0, 255)))
                pygame.draw.polygon(g, c, [(r, r - rr), (r + rr, r), (r, r + rr), (r - rr, r)])
            if len(self._glow) > 200:
                self._glow.clear()
            self._glow[key] = g
        p = self.P(pos)
        self.s.blit(g, (p[0] - r, p[1] - r), special_flags=pygame.BLEND_RGB_ADD)

    def bar(self, r, frac, fg, bg=(18, 21, 30), seg=0, glow=False):
        frac = clamp(frac, 0.0, 1.0)
        x, y, w, h = (r.x, r.y, r.w, r.h) if isinstance(r, pygame.Rect) else r
        self.rect(bg, (x, y, w, h))
        if frac > .004:
            fw = w * frac
            self.poly(fg, [(x, y), (x + fw, y), (x + fw - min(h * .5, fw), y + h), (x, y + h)])
            self.rect(mix(fg, WHT, .45), (x, y, fw, max(1., h * .3)))
            if glow:
                self.glow((x + fw, y + h * .5), h * 2.0, fg, .5)
        if seg > 1:
            for i in range(1, seg):
                gx = x + w * i / float(seg)
                self.line(VOID, (gx, y), (gx, y + h), 1)
        self.rect(dk(EDGE, .8), (x, y, w, h), 1)

    # --- text ---
    def tsurf(self, txt, size, color):
        px = int(clamp(size * self.k, 8, 260))
        key = (txt, px, color)
        s = self._txt.get(key)
        if s is None:
            try:
                s = self.fonts.get(px).render(str(txt), True, color)
            except Exception:
                s = pygame.Surface((1, 1), pygame.SRCALPHA)
            if len(self._txt) > 700:
                self._txt.clear()
            self._txt[key] = s
        return s

    def tw(self, txt, size):
        return self.tsurf(txt, size, WHT).get_width() / max(1e-6, self.k)

    def fit(self, txt, size, maxw):
        if maxw is None or maxw <= 0:
            return size
        w = self.tw(txt, size)
        if w <= maxw or w <= 0:
            return size
        return max(8.0, size * maxw / w)

    def text(self, txt, size, color, pos, anchor="topleft", shadow=True, maxw=None, glow=None):
        txt = "" if txt is None else str(txt)
        if not txt:
            return pygame.Rect(0, 0, 0, 0)
        size = self.fit(txt, size, maxw)
        surf = self.tsurf(txt, size, color)
        rect = surf.get_rect()
        try:
            setattr(rect, anchor, self.P(pos))
        except Exception:
            rect.topleft = self.P(pos)
        if shadow:
            d = max(1, int(1.7 * self.k))
            self.s.blit(self.tsurf(txt, size, (0, 0, 0)), (rect.x + d, rect.y + d))
        if glow:
            self.glow(((rect.centerx / self.k) - self.ox, (rect.centery / self.k) - self.oy),
                      rect.height / self.k * .9, glow, .38)
        self.s.blit(surf, rect)
        return rect

    def flash(self, amt, color=(255, 255, 255)):
        a = int(clamp(amt, 0, 1) * 220)
        if a < 3:
            return
        sz = self.s.get_size()
        if self._flash is None or self._flash.get_size() != sz:
            self._flash = pygame.Surface(sz).convert()
        self._flash.fill(color)
        self._flash.set_alpha(a)
        self.s.blit(self._flash, (0, 0))


# ==============================================================================
#  顯示
# ==============================================================================
QLIST = ["low", "mid", "high", "ultra", "auto"]
QFAC = {"low": 0.75, "mid": 1.0, "high": 1.3, "ultra": 1.6}


class Display:
    def __init__(self, cfg):
        self.cfg = cfg
        self.autoq = 1.1
        self.flags = pygame.RESIZABLE | pygame.DOUBLEBUF
        self.canvas = None
        self.scaled = None
        self.smooth = True
        self.win_size = (1280, 720)
        self.full = bool(cfg.get("full", IS_ANDROID))
        dw, dh = 1280, 720
        if not IS_WEB:
            try:
                info = pygame.display.Info()
                dw, dh = max(320, info.current_w), max(240, info.current_h)
            except Exception:
                pass
        if IS_WEB:
            # 瀏覽器會自動縮放畫布 / pygbag scales the canvas to the page; fullscreen goes through the browser
            self.win_size = (1280, 720)
            self.full = False
            self.screen = pygame.display.set_mode(self.win_size)
            try:
                # 重新計算畫布比例 / pygbag sized the canvas before set_mode; refit it to 16:9
                platform.window.window_resize()
            except Exception:
                pass
        elif IS_ANDROID:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            self.full = True
        else:
            h = int(clamp(dh * .78, 432, 1080))
            w = int(h * LW / LH)
            if w > dw * .95:
                w = int(dw * .9)
                h = int(w * LH / LW)
            self.win_size = (max(480, w), max(270, h))
            if self.full:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                self.screen = pygame.display.set_mode(self.win_size, self.flags)
        pygame.display.set_caption("Microbe Wars : Void Edition")
        self.view = pygame.Rect(0, 0, LW, LH)
        self.vscale = 1.0
        self.k = 1.0
        self.box = False
        self.rebuild()

    def qf(self):
        q = self.cfg.get("quality", "high")
        return self.autoq if q == "auto" else QFAC.get(q, 1.0)

    def rebuild(self):
        w, h = self.screen.get_size()
        w, h = max(64, w), max(64, h)
        sc = min(w / float(LW), h / float(LH))
        vw, vh = max(64, int(LW * sc)), max(36, int(LH * sc))
        self.view = pygame.Rect((w - vw) // 2, (h - vh) // 2, vw, vh)
        self.vscale = vw / float(LW)
        self.k = clamp(sc * self.qf(), .35, 2.5)
        cw, ch = max(64, int(LW * self.k)), max(36, int(LH * self.k))
        if self.canvas is None or self.canvas.get_size() != (cw, ch):
            self.canvas = pygame.Surface((cw, ch)).convert()
        if self.scaled is None or self.scaled.get_size() != (vw, vh):
            self.scaled = pygame.Surface((vw, vh)).convert()
        self.box = (self.view.topleft != (0, 0)) or ((vw, vh) != (w, h))

    def resize(self, w, h):
        if not self.full and not IS_WEB:
            self.win_size = (max(360, int(w)), max(240, int(h)))
            try:
                self.screen = pygame.display.set_mode(self.win_size, self.flags)
            except Exception:
                pass
        self.rebuild()

    def toggle_full(self):
        self.full = not self.full
        if IS_WEB:
            try:
                doc = platform.window.document
                if self.full:
                    doc.documentElement.requestFullscreen()
                else:
                    doc.exitFullscreen()
            except Exception:
                self.full = not self.full
            self.cfg["full"] = self.full
            return
        try:
            if self.full:
                self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            else:
                self.screen = pygame.display.set_mode(self.win_size, self.flags)
        except Exception:
            self.full = not self.full
        self.cfg["full"] = self.full
        self.rebuild()

    def auto_tune(self, ms):
        if self.cfg.get("quality") != "auto":
            return False
        ch = False
        if ms > 21.0 and self.autoq > .7:
            self.autoq = max(.7, self.autoq - .05)
            ch = True
        elif ms < 12.0 and self.autoq < 1.4:
            self.autoq = min(1.4, self.autoq + .02)
            ch = True
        if ch:
            old = self.canvas.get_size()
            self.rebuild()
            return self.canvas.get_size() != old
        return False

    def present(self):
        if self.box:
            self.screen.fill((0, 0, 0))
        tgt = (self.view.w, self.view.h)
        if self.canvas.get_size() == tgt:
            self.screen.blit(self.canvas, self.view.topleft)
        else:
            done = False
            if self.smooth:
                try:
                    pygame.transform.smoothscale(self.canvas, tgt, self.scaled)
                    done = True
                except Exception:
                    self.smooth = False
            if not done:
                try:
                    self.scaled = pygame.transform.smoothscale(self.canvas, tgt)
                except Exception:
                    self.scaled = pygame.transform.scale(self.canvas, tgt)
            self.screen.blit(self.scaled, self.view.topleft)
        pygame.display.flip()

    def to_log(self, pos):
        s = max(1e-6, self.vscale)
        return ((pos[0] - self.view.x) / s, (pos[1] - self.view.y) / s)

    def finger(self, e):
        w, h = self.screen.get_size()
        return self.to_log((getattr(e, "x", 0.) * w, getattr(e, "y", 0.) * h))


# ==============================================================================
#  音效
# ==============================================================================
class Sfx:
    def __init__(self, cfg):
        self.cfg = cfg
        self.ok = False
        self.snd = {}
        self.last = {}
        self.now = 0.0
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(44100, -16, 2, 512)
            init = pygame.mixer.get_init()
            if init and init[1] == -16 and init[2] in (1, 2):
                self.rate, _, self.ch = init
                pygame.mixer.set_num_channels(24)
                self._build()
                self.ok = True
        except Exception:
            self.ok = False

    def _mk(self, dur, f0, f1, kind="sine", dec=6.0, noise=0.0, vol=.8):
        try:
            n = int(self.rate * dur)
            buf = array.array("h")
            tp = math.pi * 2
            for i in range(n):
                t = i / float(self.rate)
                p = t / dur
                f = f0 + (f1 - f0) * p
                ph = tp * f * t
                if kind == "sine":
                    s = math.sin(ph)
                elif kind == "square":
                    s = 1.0 if math.sin(ph) > 0 else -1.0
                else:
                    s = 2.0 * ((f * t) % 1.0) - 1.0
                if noise > 0:
                    s = s * (1 - noise) + (random.random() * 2 - 1) * noise
                env = math.exp(-dec * p) * (1 - math.exp(-40.0 * p))
                v = int(clamp(s * env * vol, -1, 1) * 30200)
                buf.append(v)
                if self.ch == 2:
                    buf.append(v)
            return pygame.mixer.Sound(buffer=buf.tobytes())
        except Exception:
            return None

    def _build(self):
        m = self._mk
        self.snd = {
            "slash": m(.14, 1020, 240, "saw", 11, .28, .5),
            "hit": m(.08, 460, 120, "square", 14, .45, .42),
            "shoot": m(.07, 1320, 520, "square", 16, .12, .34),
            "saw": m(.06, 240, 175, "saw", 7, .58, .24),
            "boom": m(.34, 230, 40, "sine", 5, .68, .8),
            "jump": m(.10, 400, 780, "sine", 11, .05, .3),
            "dash": m(.12, 180, 900, "saw", 9, .22, .34),
            "hurt": m(.18, 300, 84, "square", 8, .3, .55),
            "level": m(.30, 500, 1200, "sine", 3.2, 0, .46),
            "ui": m(.05, 920, 1280, "square", 14, 0, .22),
            "ult": m(.55, 130, 920, "saw", 2.4, .18, .66),
            "parry": m(.16, 1650, 700, "sine", 7, .06, .5),
            "zap": m(.11, 1800, 380, "square", 12, .3, .4),
            "guard": m(.09, 680, 940, "sine", 10, .1, .3),
            "brk": m(.26, 700, 130, "saw", 6, .4, .6),
            "react": m(.30, 320, 1400, "saw", 4.2, .3, .6),
            "exec": m(.24, 900, 110, "square", 6, .5, .62),
            "ovd": m(.42, 220, 700, "square", 3.0, .2, .55),
            "grap": m(.14, 500, 1500, "saw", 9, .2, .38),
            "alarm": m(.5, 360, 300, "square", 1.6, .1, .45),
            "brkbox": m(.16, 320, 90, "saw", 9, .6, .5),
        }

    def play(self, n, cd=.04):
        if not self.ok:
            return
        v = float(self.cfg.get("vol", .6))
        if v <= .01:
            return
        s = self.snd.get(n)
        if s is None:
            return
        if self.now - self.last.get(n, -9) < cd:
            return
        self.last[n] = self.now
        try:
            s.set_volume(clamp(v, 0, 1))
            s.play()
        except Exception:
            pass

    def tick(self, dt):
        self.now += dt


# ==============================================================================
#  自訂素材
# ==============================================================================
EXTS = (".gif", ".png", ".webp", ".jpg", ".jpeg", ".bmp")


def find_file(name):
    for d in (BASE_DIR, os.getcwd(), os.path.join(BASE_DIR, "assets")):
        for e in EXTS:
            p = os.path.join(d, name + e)
            try:
                if os.path.isfile(p):
                    return p
            except Exception:
                pass
    return None


class Anim:
    def __init__(self, frames, durs):
        self.f = frames
        self.d = durs or [.1] * len(frames)
        self.total = max(.02, sum(self.d))
        self.cache = {}

    def _idx(self, t):
        tt = t % self.total
        acc = 0.0
        for i, d in enumerate(self.d):
            acc += d
            if tt < acc:
                return i
        return len(self.f) - 1

    def get(self, t, w, h, flip=False):
        if not self.f:
            return None
        w = int(clamp(w, 2, 1400))
        h = int(clamp(h, 2, 1400))
        key = (self._idx(t), w, h, bool(flip))
        s = self.cache.get(key)
        if s is None:
            try:
                s = pygame.transform.smoothscale(self.f[key[0]], (w, h))
            except Exception:
                try:
                    s = pygame.transform.scale(self.f[key[0]], (w, h))
                except Exception:
                    return None
            if flip:
                s = pygame.transform.flip(s, True, False)
            if len(self.cache) > 220:
                self.cache.clear()
            self.cache[key] = s
        return s


def load_anim(name):
    p = find_file(name)
    if not p:
        return None
    fr, du = [], []
    try:
        # 網頁版不載入 Pillow / On the web, skip Pillow: pygbag auto-installs it when it sees the import,
        # and that breaks pygame's display. importlib hides the import from pygbag's scanner.
        if IS_WEB:
            raise ImportError("Pillow disabled on web")
        import importlib
        Image = importlib.import_module("PIL.Image")
        ImageSequence = importlib.import_module("PIL.ImageSequence")
        im = Image.open(p)
        conv = getattr(pygame.image, "frombytes", None) or pygame.image.fromstring
        for f in ImageSequence.Iterator(im):
            c = f.convert("RGBA")
            try:
                fr.append(conv(c.tobytes(), c.size, "RGBA").convert_alpha())
            except Exception:
                continue
            d = f.info.get("duration", 80)
            try:
                d = int(d)
            except Exception:
                d = 80
            du.append(max(30, d) / 1000.0)
            if len(fr) >= 80:
                break
    except Exception:
        fr, du = [], []
    if not fr:
        try:
            fr = [pygame.image.load(p).convert_alpha()]
            du = [.1]
        except Exception:
            return None
    return Anim(fr, du)


# ==============================================================================
#  粒子 / 浮字 / 特效 / 碎片 / 場域
# ==============================================================================
class Parts:
    def __init__(self, cap=700):
        self.p = []
        self.cap = cap

    def clear(self):
        self.p = []

    def add(self, x, y, vx, vy, life, size, col, grav=420., spark=False):
        if len(self.p) >= self.cap:
            return
        self.p.append([x, y, vx, vy, life, life, size, col, grav, spark])

    def burst(self, x, y, col, n=10, spd=190, size=4, life=.5, grav=420., spark=False):
        n = int(min(n, max(0, self.cap - len(self.p))))
        for _ in range(n):
            a = random.uniform(0, math.tau)
            s = random.uniform(.25, 1.) * spd
            self.add(x, y, math.cos(a) * s, math.sin(a) * s, life * random.uniform(.6, 1.3),
                     size * random.uniform(.6, 1.2), col, grav, spark)

    def cone(self, x, y, ang, spread, col, n=8, spd=260, size=3, life=.35):
        for _ in range(int(n)):
            a = ang + random.uniform(-spread, spread)
            s = random.uniform(.4, 1.) * spd
            self.add(x, y, math.cos(a) * s, math.sin(a) * s, life * random.uniform(.6, 1.2),
                     size, col, 60, True)

    def update(self, dt):
        out = []
        for q in self.p:
            q[4] -= dt
            if q[4] <= 0:
                continue
            q[3] += q[8] * dt
            q[0] += q[2] * dt
            q[1] += q[3] * dt
            q[2] *= (1 - 1.6 * dt)
            out.append(q)
        self.p = out

    def draw(self, pt):
        for q in self.p:
            f = q[4] / q[5]
            r = q[6] * (.3 + .7 * f)
            if r < .4:
                continue
            if q[9]:
                pt.line(q[7], (q[0], q[1]), (q[0] - q[2] * .026, q[1] - q[3] * .026), max(1., r * .85))
            else:
                pt.rect(q[7], (q[0] - r, q[1] - r, r * 2, r * 2))


class FText:
    __slots__ = ("x", "y", "vy", "t", "life", "s", "c", "sz")

    def __init__(self, x, y, s, c, sz=19, life=.75):
        self.x, self.y, self.s, self.c, self.sz = x, y, s, c, sz
        self.vy = -52.
        self.t = life
        self.life = life

    def update(self, dt):
        self.t -= dt
        self.y += self.vy * dt
        self.vy += 44 * dt
        return self.t > 0

    def draw(self, pt):
        f = clamp(self.t / self.life, 0, 1)
        pt.text(self.s, self.sz * (.8 + .35 * f), self.c, (self.x, self.y), "center", True)


class Fx:
    def __init__(self, kind, x, y, life, col, r=90, ang=0.0, w=0.0):
        self.kind, self.x, self.y = kind, x, y
        self.t = life
        self.life = life
        self.c = col
        self.r = r
        self.ang = ang
        self.w = w

    def update(self, dt):
        self.t -= dt
        return self.t > 0

    def draw(self, pt):
        f = clamp(1 - self.t / self.life, 0, 1)
        k = self.kind
        if k == "ring":  # 稜角擴散環
            rr = self.r * (.2 + f)
            w = max(1., 6 * (1 - f))
            pt.dia(self.c, (self.x, self.y), rr, rr * .72, w)
            pt.glow((self.x, self.y), rr * .6, self.c, .38 * (1 - f))
        elif k == "shock":
            rr = self.r * (.2 + f)
            pt.hexa(self.c, (self.x, self.y), rr, rr * .7, max(1., 4 * (1 - f)))
        elif k == "slash":
            Lg = LW * 1.5
            dx, dy = math.cos(self.ang), math.sin(self.ang)
            w = 26 * (1 - f)
            if w > .5:
                pt.line(self.c, (self.x - dx * Lg, self.y - dy * Lg), (self.x + dx * Lg, self.y + dy * Lg), w)
                pt.line(WHT, (self.x - dx * Lg, self.y - dy * Lg), (self.x + dx * Lg, self.y + dy * Lg),
                        max(1., w * .3))
        elif k == "spark":
            pt.glow((self.x, self.y), max(2, self.r * (1 - f)), self.c, .85 * (1 - f))
            pt.xmark(self.c, (self.x, self.y), self.r * .4 * (1 - f) + 2, 2)
        elif k == "beamh":
            h = self.w * (1 - f * .4)
            pt.rect(self.c, (0, self.y - h * .5, LW, h))
            pt.rect(WHT, (0, self.y - h * .16, LW, h * .32))
            pt.glow((LW * .5, self.y), 90, self.c, .55 * (1 - f))
        elif k == "beamv":
            w = self.w * (1 - f * .35)
            pt.rect(self.c, (self.x - w * .5, 0, w, LH))
            pt.rect(WHT, (self.x - w * .16, 0, w * .32, LH))
        elif k == "bolt":
            n = 6
            px, py = self.x, self.y
            tx, ty = self.r, self.ang
            for i in range(1, n + 1):
                t = i / float(n)
                nx = lerp(self.x, tx, t) + random.uniform(-10, 10)
                ny = lerp(self.y, ty, t) + random.uniform(-10, 10)
                pt.line(self.c, (px, py), (nx, ny), max(1.2, 4 * (1 - f)))
                px, py = nx, ny
            pt.glow((tx, ty), 24, self.c, .55 * (1 - f))
        elif k == "warn":
            pt.rect(self.c, (self.x - self.w * .5, self.y, self.w, LH - self.y), 2)
            a = .25 + .4 * abs(math.sin(f * 16))
            pt.glow((self.x, self.y + 70), self.w, self.c, a)
        elif k == "shard":
            for i in range(5):
                a = self.ang + i * 1.257
                d = self.r * f
                pt.tri(self.c, (self.x + math.cos(a) * d, self.y + math.sin(a) * d), 5 * (1 - f) + 1, i % 4)


class Debris:
    def __init__(self, rect, col, top=True):
        self.w = max(4, rect.w // 2)
        self.h = max(3, rect.h // 3)
        self.x = float(rect.x + random.uniform(0, max(1, rect.w - self.w)))
        self.y = float(rect.y if top else rect.centery)
        self.vx = random.uniform(-180, 180)
        self.vy = random.uniform(-280, -90)
        self.rot = random.uniform(0, 3)
        self.vr = random.uniform(-7, 7)
        self.c = col
        self.t = 1.6

    def update(self, dt):
        self.t -= dt
        self.vy += 980 * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rot += self.vr * dt
        if self.y + self.h > GROUND_Y:
            self.y = GROUND_Y - self.h
            self.vy *= -.28
            self.vx *= .55
            self.vr *= .5
        return self.t > 0

    def draw(self, pt):
        a = clamp(self.t / 1.6, 0, 1)
        c = dk(self.c, .35 + .65 * a)
        cx, cy = self.x + self.w * .5, self.y + self.h * .5
        ca, sa = math.cos(self.rot), math.sin(self.rot)
        hw, hh = self.w * .5, self.h * .5
        pts = []
        for ox, oy in ((-hw, -hh), (hw, -hh * .6), (hw * .7, hh), (-hw * .8, hh * .7)):
            pts.append((cx + ox * ca - oy * sa, cy + ox * sa + oy * ca))
        pt.poly(c, pts)


class Zone:
    def __init__(self, x, y, w, h, life, dps, owner, col, elem=None, slow=False):
        self.rect = pygame.Rect(int(x - w * .5), int(y - h), int(w), int(h))
        self.x, self.y = float(x), float(y)
        self.w, self.h = w, h
        self.life = life
        self.max_life = life
        self.dps = dps
        self.owner = owner
        self.c = col
        self.elem = elem
        self.slow = slow
        self.tick = 0.0
        self.t = 0.0

    def update(self, dt):
        self.t += dt
        self.life -= dt
        self.tick -= dt
        return self.life > 0

    def hits(self, rect):
        return self.rect.colliderect(rect)

    def draw(self, pt):
        f = clamp(self.life / self.max_life, 0, 1)
        r = self.rect
        pt.glow((r.centerx, r.centery), self.w * .5, self.c, .18 + .12 * math.sin(self.t * 6))
        pt.poly(self.c, [(r.x, r.bottom), (r.x + 6, r.y), (r.right - 6, r.y), (r.right, r.bottom)], 2)
        n = max(2, int(self.w / 18))
        for i in range(n):
            x = r.x + 6 + i * (self.w - 12) / max(1, n - 1)
            hh = (self.h * .5) * (.4 + .6 * abs(math.sin(self.t * 4 + i)))
            pt.line(self.c, (x, r.bottom), (x, r.bottom - hh), 2)
        pt.rect(dk(self.c, .6), (r.x, r.bottom - 2, r.w, 2 + 2 * f))


# ==============================================================================
#  星空背景 / Starfield only
# ==============================================================================
class Starfield:
    def __init__(self):
        self.surf = None
        self.vig = None
        self.k = -1.
        self.seed = random.randint(1, 10 ** 6)
        self.t = 0.
        rng = random.Random(self.seed)
        self.tw = [[rng.uniform(0, LW), rng.uniform(0, GROUND_Y - 30), rng.uniform(0, 6.3),
                    rng.uniform(.8, 2.0)] for _ in range(26)]
        self.dust = [[rng.uniform(0, LW), rng.uniform(0, LH), rng.uniform(-7, 7),
                      rng.uniform(-16, -3), rng.uniform(.8, 1.9)] for _ in range(26)]
        self.meteor = None
        self.mt = rng.uniform(2, 7)

    def invalidate(self):
        self.k = -1.

    def update(self, dt):
        self.t += dt
        for s in self.tw:
            s[2] += dt * 2.2
        for d in self.dust:
            d[0] += d[2] * dt
            d[1] += d[3] * dt
            if d[1] < -8:
                d[1] = LH + 8
                d[0] = random.uniform(0, LW)
            if d[0] < -8:
                d[0] = LW + 8
            elif d[0] > LW + 8:
                d[0] = -8
        self.mt -= dt
        if self.meteor is not None:
            self.meteor[0] += self.meteor[2] * dt
            self.meteor[1] += self.meteor[3] * dt
            self.meteor[4] -= dt
            if self.meteor[4] <= 0:
                self.meteor = None
        elif self.mt <= 0:
            self.mt = random.uniform(3.5, 9.)
            self.meteor = [random.uniform(-40, LW * .7), random.uniform(-20, 140),
                           random.uniform(420, 680), random.uniform(120, 230), 1.6]

    def build(self, pt, k, size):
        surf = pygame.Surface(size).convert()
        pt.begin(surf, k)
        rng = random.Random(self.seed)
        g = pygame.Surface((2, 120))
        for i in range(120):
            t = i / 119.
            pygame.draw.line(g, (int(lerp(2, 12, t ** 1.5)), int(lerp(3, 14, t ** 1.4)),
                                 int(lerp(7, 24, t))), (0, i), (1, i))
        try:
            surf.blit(pygame.transform.smoothscale(g, size), (0, 0))
        except Exception:
            surf.blit(pygame.transform.scale(g, size), (0, 0))
        # 星點（方形像素星）
        for _ in range(300):
            x, y = rng.uniform(0, LW), rng.uniform(0, GROUND_Y - 10)
            b = rng.randint(70, 255)
            s = rng.choice([1, 1, 1, 2])
            pt.rect((b, b, min(255, b + 14)), (x, y, s, s))
        # 十字閃星
        for _ in range(16):
            x, y = rng.uniform(20, LW - 20), rng.uniform(10, GROUND_Y - 60)
            r = rng.uniform(3.2, 6.5)
            c = rng.choice([WHT, (190, 220, 255), (255, 235, 210)])
            pt.line(c, (x - r, y), (x + r, y), 1)
            pt.line(c, (x, y - r), (x, y + r), 1)
            pt.glow((x, y), r * 2.6, c, .22)
        # 地面：暗金屬平台 + 霓虹邊 + 透視格線
        pt.rect((7, 9, 14), (0, GROUND_Y, LW, LH - GROUND_Y))
        for i in range(16):
            x = i * (LW / 15.)
            pt.line((16, 20, 30), (x, GROUND_Y), (x + (x - LW * .5) * .18, LH), 1)
        for i in range(4):
            y = GROUND_Y + 8 + i * i * 6
            pt.line((14, 18, 27), (0, y), (LW, y), 1)
        pt.rect((20, 26, 38), (0, GROUND_Y, LW, 5))
        pt.line(dk(CYAN, .55), (0, GROUND_Y), (LW, GROUND_Y), 2)
        for i in range(0, LW, 64):
            pt.poly(dk(CYAN, .3), [(i, GROUND_Y), (i + 10, GROUND_Y), (i + 5, GROUND_Y + 6)])
        # vignette
        v = pygame.Surface((80, 45), pygame.SRCALPHA)
        for yy in range(45):
            for xx in range(80):
                dx = (xx / 79. - .5) * 2
                dy = (yy / 44. - .5) * 2
                d = math.sqrt(dx * dx * .85 + dy * dy)
                a = int(clamp((d - .45) / .75, 0, 1) * 205)
                if a:
                    v.set_at((xx, yy), (0, 0, 0, a))
        try:
            self.vig = pygame.transform.smoothscale(v, size)
        except Exception:
            self.vig = pygame.transform.scale(v, size)
        self.surf = surf
        self.k = k

    def draw_live(self, pt):
        for s in self.tw:
            a = .25 + .45 * (.5 + .5 * math.sin(s[2]))
            pt.glow((s[0], s[1]), s[3] * 3.2, (200, 225, 255), a * .45)
            pt.rect(WHT, (s[0], s[1], 1, 1))
        for d in self.dust:
            pt.rect((44, 60, 86), (d[0], d[1], d[4], d[4]))
        if self.meteor:
            m = self.meteor
            pt.line((190, 215, 255), (m[0], m[1]), (m[0] - m[2] * .06, m[1] - m[3] * .06), 2)
            pt.glow((m[0], m[1]), 16, (190, 220, 255), .5)


# ==============================================================================
#  地形 / 可互動障礙物
# ==============================================================================
SOLIDK = {"crate", "barrel", "pylon"}
PLATK = {"slab", "mover", "crumble", "spike", "pad", "belt"}

OBS_COL = {
    "slab": (52, 60, 78), "mover": (58, 70, 96), "crumble": (72, 62, 54),
    "spike": (92, 40, 52), "pad": (40, 92, 84), "belt": (48, 58, 82),
    "crate": (76, 66, 48), "barrel": (98, 52, 34), "gate": (40, 70, 96),
    "vent": (36, 74, 92), "emitter": (96, 40, 56), "pylon": (56, 46, 96),
}
OBS_NEON = {
    "slab": dk(CYAN, .5), "mover": CYAN, "crumble": AMB, "spike": RED, "pad": LIME,
    "belt": CYAN, "crate": AMB, "barrel": (255, 120, 50), "gate": CYAN,
    "vent": ICE, "emitter": RED, "pylon": VIOL,
}


class Obstacle:
    def __init__(self, kind, x, y, w, h, **kw):
        self.kind = kind
        self.rect = pygame.Rect(int(x), int(y), int(w), int(h))
        self.home = self.rect.copy()
        self.maxhp = float(kw.get("hp", 0))
        self.hp = self.maxhp
        self.alive = True
        self.t = random.uniform(0, 6)
        self.vx_now = 0.
        self.span = kw.get("span", 140)
        self.spd = kw.get("spd", 62)
        self.axis = kw.get("axis", "x")
        self.dirn = kw.get("dir", 1)
        self.period = kw.get("period", 3.2)
        self.duty = kw.get("duty", .5)
        self.power = kw.get("power", 1.0)
        self.state = 0
        self.timer = 0.
        self.respawn = 0.
        self.fire = random.uniform(.6, 2.4)
        self.beam = 0.
        self.hit_flash = 0.
        self.col = OBS_COL.get(kind, PLATE)
        self.neon = OBS_NEON.get(kind, EDGE)

    # ---- 狀態 ----
    def solid_now(self):
        if not self.alive:
            return False
        if self.kind in SOLIDK:
            return True
        if self.kind == "gate":
            return self.state == 1
        return False

    def plat_now(self):
        return self.alive and self.kind in PLATK

    def blocks_shots(self):
        return self.solid_now()

    def damage(self, d, g, from_x=None):
        if self.maxhp <= 0 or not self.alive:
            return 0
        self.hp -= d
        self.hit_flash = .16
        g.parts.burst(self.rect.centerx, self.rect.centery, self.neon, 5, 150, 3, .28, 320, True)
        if self.hp <= 0:
            self.destroy(g)
        else:
            g.sfx.play("brkbox", .06)
        return d

    def destroy(self, g):
        self.alive = False
        self.hp = 0
        g.sfx.play("brkbox", .04)
        for _ in range(3):
            g.debris.append(Debris(self.rect, self.col, True))
        g.parts.burst(self.rect.centerx, self.rect.centery, self.neon, 16, 240, 4, .5, 460, True)
        if self.kind == "barrel":
            g.explode(self.rect.centerx, self.rect.centery, 112, 26, "n", "burn", (255, 130, 50))
            g.shake = max(g.shake, 14)
        elif self.kind == "crate":
            k = random.choice(["hp", "en", "xp", "xp", "ovd", "barrier"])
            g.pickups.append(Pickup(self.rect.centerx, self.rect.centery, k))
        elif self.kind == "pylon":
            g.fx.append(Fx("ring", self.rect.centerx, self.rect.centery, .5, VIOL, r=130))

    # ---- 更新 ----
    def update(self, dt, g):
        self.t += dt
        if self.hit_flash > 0:
            self.hit_flash = max(0., self.hit_flash - dt)
        k = self.kind
        self.vx_now = 0.
        if not self.alive:
            if k == "crumble":
                self.respawn -= dt
                if self.respawn <= 0:
                    self.alive = True
                    self.timer = 0.
                    self.rect = self.home.copy()
            return
        if k == "mover":
            ph = math.sin(self.t * self.spd / max(20., self.span))
            nx = self.home.x + (self.span * ph if self.axis == "x" else 0)
            ny = self.home.y + (self.span * ph * .5 if self.axis == "y" else 0)
            self.vx_now = (nx - self.rect.x) / max(1e-5, dt)
            self.rect.x = int(nx)
            self.rect.y = int(ny)
        elif k == "crumble":
            if self.timer > 0:
                self.timer -= dt
                if self.timer <= 0:
                    self.alive = False
                    self.respawn = 5.0
                    g.parts.burst(self.rect.centerx, self.rect.top, self.col, 12, 180, 3, .5)
                    for _ in range(2):
                        g.debris.append(Debris(self.rect, self.col, True))
        elif k == "gate":
            ph = (self.t % self.period) / self.period
            ns = 1 if ph < self.duty else 0
            if ns != self.state:
                self.state = ns
                g.sfx.play("guard", .2)
        elif k == "emitter":
            self.fire -= dt
            if self.beam > 0:
                self.beam -= dt
                p = g.player
                span = pygame.Rect(self.rect.x, self.rect.bottom, self.rect.w, GROUND_Y - self.rect.bottom)
                if p is not None and not p.dead and span.colliderect(p.rect):
                    p.hurt(1, g, self.rect.centerx, None)
                for e in g.enemies:
                    if span.colliderect(e.rect):
                        g.hurt_enemy(e, 14, False, self.rect.centerx, 0, "burn")
            elif self.fire <= 0:
                self.fire = self.period
                self.beam = .55
                g.fx.append(Fx("warn", self.rect.centerx, self.rect.bottom, .45, RED, w=self.rect.w))
                g.sfx.play("zap", .12)
        elif k == "pylon":
            self.timer -= dt
            if self.timer <= 0:
                self.timer = 1.8
                for e in g.enemies:
                    if abs(e.rect.centerx - self.rect.centerx) < 190 and abs(e.rect.centery - self.rect.centery) < 190:
                        if e.shield_max <= 0:
                            e.shield_max = 24
                        e.shield = min(e.shield_max, e.shield + 12)
                        g.fx.append(Fx("bolt", self.rect.centerx, self.rect.centery, .2, VIOL,
                                       r=e.rect.centerx, ang=e.rect.centery))
        elif k == "vent":
            pass

    # ---- 互動 ----
    def on_land(self, u, g, is_player):
        k = self.kind
        if k == "pad":
            u.vy = -1020.
            u.on_ground = False
            g.sfx.play("jump", .05)
            g.parts.cone(u.rect.centerx, u.rect.bottom, -math.pi / 2, .5, LIME, 10, 320, 3, .3)
        elif k == "crumble" and self.timer <= 0:
            self.timer = .75
        elif k == "spike" and is_player:
            u.hurt(1, g, u.rect.centerx, None)
            u.vy = -420

    def on_stand(self, u, dt, g, is_player):
        k = self.kind
        if k == "belt":
            u.x += self.dirn * 170 * dt
        elif k == "mover":
            u.x += self.vx_now * dt
        elif k == "spike" and is_player and random.random() < 2.0 * dt:
            u.hurt(1, g, u.rect.centerx, None)

    def field(self, u, dt, g, is_player):
        if self.kind == "vent" and self.alive:
            zone = pygame.Rect(self.rect.x, self.rect.y - 210, self.rect.w, 210 + self.rect.h)
            if zone.colliderect(u.rect):
                u.vy = max(-470., u.vy - 1750 * dt)

    # ---- 繪製 ----
    def draw(self, pt, g):
        if not self.alive:
            if self.kind == "crumble":
                r = self.home
                pt.poly(dk(self.neon, .3), [(r.x, r.bottom), (r.x + 4, r.y), (r.right - 4, r.y), (r.right, r.bottom)], 1)
            return
        r = self.rect
        k = self.kind
        c = self.col if self.hit_flash <= 0 else WHT
        n = self.neon
        if k in ("slab", "mover", "belt", "crumble", "spike", "pad"):
            pt.poly(dk(c, .55), [(r.x - 3, r.bottom + 3), (r.x + 5, r.y + 2), (r.right - 5, r.y + 2), (r.right + 3, r.bottom + 3)])
            pt.poly(c, [(r.x, r.bottom), (r.x + 6, r.y), (r.right - 6, r.y), (r.right, r.bottom)])
            pt.line(n, (r.x + 6, r.y), (r.right - 6, r.y), 2)
            pt.glow((r.centerx, r.y), r.w * .2, n, .18)
            for i in range(max(1, r.w // 30)):
                x = r.x + 12 + i * 30
                if x < r.right - 8:
                    pt.line(dk(n, .35), (x, r.y + 3), (x - 3, r.bottom - 2), 1)
        if k == "spike":
            nsp = max(2, r.w // 14)
            for i in range(nsp):
                x = r.x + 4 + i * (r.w - 8) / max(1, nsp - 1)
                pt.tri(RED, (x, r.y - 6), 6, 0)
                pt.line((255, 160, 170), (x, r.y - 11), (x, r.y - 2), 1)
            pt.glow((r.centerx, r.y - 6), r.w * .3, RED, .25)
        elif k == "pad":
            pt.chev(LIME, (r.centerx, r.y - 4 - 3 * math.sin(self.t * 6)), 8, 1, 3)
            pt.chev(LIME, (r.centerx, r.y - 14 - 3 * math.sin(self.t * 6)), 8, 1, 2)
        elif k == "belt":
            off = (self.t * 90 * self.dirn) % 24
            for i in range(-1, r.w // 24 + 1):
                x = r.x + 6 + i * 24 + off
                if r.x + 3 < x < r.right - 6:
                    pt.tri(CYAN, (x, r.y + 5), 5, 3 if self.dirn > 0 else 2)
        elif k == "mover":
            pt.line(dk(CYAN, .4), (r.centerx - self.span, r.centery), (r.centerx + self.span, r.centery), 1)
            pt.dia(CYAN, (r.centerx, r.bottom + 4), 4, 3)
        elif k == "crumble":
            f = 1. - clamp(self.timer / .75, 0, 1)
            if self.timer > 0:
                pt.rect(mix(AMB, RED, f), (r.x, r.y - 3, r.w * (1 - f), 2))
                pt.xmark(AMB, (r.centerx, r.centery), 5, 2)
        elif k == "crate":
            pt.poly(dk(c, .55), (self._box(r, 5)))
            pt.poly(c, self._box(r, 4))
            pt.poly(dk(n, .9), self._box(r, 4), 2)
            pt.line(dk(n, .5), (r.x + 4, r.y + 4), (r.right - 4, r.bottom - 4), 1)
            pt.line(dk(n, .5), (r.right - 4, r.y + 4), (r.x + 4, r.bottom - 4), 1)
            f = clamp(self.hp / max(1., self.maxhp), 0, 1)
            pt.rect(mix(RED, AMB, f), (r.x + 3, r.y - 4, (r.w - 6) * f, 2))
        elif k == "barrel":
            pulse = .55 + .45 * math.sin(self.t * 5)
            pt.poly(dk(c, .5), self._box(r, 6))
            pt.poly(c, self._box(r, 5))
            pt.poly((255, 140, 60), self._box(r, 5), 2)
            pt.dia((255, int(120 + 90 * pulse), 40), (r.centerx, r.centery), r.w * .22, r.h * .26)
            pt.glow((r.centerx, r.centery), r.w * .7, (255, 120, 40), .22 + .2 * pulse)
            pt.text("!", r.h * .5, (30, 12, 6), (r.centerx, r.centery), "center", False, maxw=r.w)
        elif k == "gate":
            pt.rect(dk(c, .8), (r.x - 4, r.y - 6, 8, r.h + 12))
            pt.rect(dk(c, .8), (r.right - 4, r.y - 6, 8, r.h + 12))
            if self.state == 1:
                for i in range(max(1, r.h // 10)):
                    y = r.y + 4 + i * 10
                    pt.line(CYAN, (r.x, y), (r.right, y), 2)
                pt.glow((r.centerx, r.centery), r.h * .5, CYAN, .3)
            else:
                pt.line(dk(CYAN, .35), (r.x, r.y), (r.x, r.bottom), 1)
                pt.line(dk(CYAN, .35), (r.right, r.y), (r.right, r.bottom), 1)
        elif k == "vent":
            pt.poly(c, [(r.x, r.bottom), (r.x + 4, r.y), (r.right - 4, r.y), (r.right, r.bottom)])
            pt.poly(ICE, [(r.x, r.bottom), (r.x + 4, r.y), (r.right - 4, r.y), (r.right, r.bottom)], 2)
            for i in range(4):
                yy = r.y - ((self.t * 150 + i * 52) % 200)
                a = clamp(1 - (r.y - yy) / 200., 0, 1)
                pt.line(dk(ICE, .2 + .6 * a), (r.centerx - 8, yy), (r.centerx - 8, yy - 12), 2)
                pt.line(dk(ICE, .2 + .6 * a), (r.centerx + 8, yy + 20), (r.centerx + 8, yy + 8), 2)
        elif k == "emitter":
            pt.poly(c, [(r.x, r.y), (r.right, r.y), (r.right - 6, r.bottom), (r.x + 6, r.bottom)])
            pt.poly(RED, [(r.x, r.y), (r.right, r.y), (r.right - 6, r.bottom), (r.x + 6, r.bottom)], 2)
            pt.dia(RED if self.beam > 0 else dk(RED, .4), (r.centerx, r.bottom - 2), 4, 3)
            if self.beam > 0:
                w = r.w * (.4 + .6 * clamp(self.beam / .55, 0, 1))
                pt.rect((255, 90, 110), (r.centerx - w * .5, r.bottom, w, GROUND_Y - r.bottom))
                pt.rect(WHT, (r.centerx - w * .16, r.bottom, w * .32, GROUND_Y - r.bottom))
                pt.glow((r.centerx, r.bottom + 60), 60, RED, .5)
        elif k == "pylon":
            pt.poly(c, [(r.centerx, r.y), (r.right, r.y + r.h * .35), (r.right - 5, r.bottom),
                        (r.x + 5, r.bottom), (r.x, r.y + r.h * .35)])
            pt.poly(VIOL, [(r.centerx, r.y), (r.right, r.y + r.h * .35), (r.right - 5, r.bottom),
                           (r.x + 5, r.bottom), (r.x, r.y + r.h * .35)], 2)
            rr = 12 + 5 * math.sin(self.t * 3)
            pt.dia(VIOL, (r.centerx, r.centery + 2), rr, rr * .8, 2)
            pt.glow((r.centerx, r.centery), 40, VIOL, .3)
            f = clamp(self.hp / max(1., self.maxhp), 0, 1)
            pt.rect(mix(RED, VIOL, f), (r.x, r.y - 6, r.w * f, 3))

    @staticmethod
    def _box(r, c=4):
        return [(r.x + c, r.y), (r.right - c, r.y), (r.right, r.y + c), (r.right, r.bottom - c),
                (r.right - c, r.bottom), (r.x + c, r.bottom), (r.x, r.bottom - c), (r.x, r.y + c)]


def build_level(idx):
    """5 種佈局 / five interactive layouts"""
    idx = int(idx) % 5
    O = Obstacle
    if idx == 0:
        return [
            O("slab", 90, 368, 170, 14), O("slab", 396, 368, 170, 14), O("slab", 704, 368, 170, 14),
            O("slab", 238, 258, 150, 14), O("slab", 570, 258, 150, 14),
            O("slab", 400, 154, 160, 14),
            O("crate", 300, 430, 40, 40, hp=40), O("crate", 340, 430, 40, 40, hp=40),
            O("crate", 620, 430, 40, 40, hp=40),
            O("barrel", 470, 424, 34, 46, hp=22),
            O("pad", 130, 440, 70, 12),
            O("pad", 790, 440, 70, 12),
        ]
    if idx == 1:
        return [
            O("slab", 70, 400, 150, 14), O("slab", 740, 400, 150, 14),
            O("mover", 380, 330, 130, 14, span=170, spd=70, axis="x"),
            O("mover", 240, 210, 110, 14, span=120, spd=52, axis="y"),
            O("belt", 380, 456, 200, 14, dir=1),
            O("spike", 250, 456, 90, 12), O("spike", 640, 456, 90, 12),
            O("slab", 560, 240, 150, 14),
            O("crate", 100, 360, 40, 40, hp=44),
            O("barrel", 700, 354, 34, 46, hp=22),
        ]
    if idx == 2:
        return [
            O("crumble", 160, 360, 120, 14), O("crumble", 420, 300, 120, 14),
            O("crumble", 690, 360, 120, 14),
            O("slab", 300, 210, 140, 14), O("slab", 560, 180, 140, 14),
            O("gate", 470, 330, 18, 140, period=4.0, duty=.55),
            O("barrel", 250, 424, 34, 46, hp=22), O("barrel", 680, 424, 34, 46, hp=22),
            O("crate", 400, 430, 40, 40, hp=48), O("crate", 520, 430, 40, 40, hp=48),
            O("pad", 60, 440, 70, 12),
        ]
    if idx == 3:
        return [
            O("slab", 80, 390, 160, 14), O("slab", 720, 390, 160, 14),
            O("mover", 400, 340, 150, 14, span=190, spd=82),
            O("emitter", 250, 60, 40, 26, period=3.4),
            O("emitter", 660, 60, 40, 26, period=4.2),
            O("vent", 470, 440, 46, 30),
            O("pylon", 120, 418, 40, 52, hp=60), O("pylon", 800, 418, 40, 52, hp=60),
            O("slab", 300, 220, 130, 14), O("slab", 540, 220, 130, 14),
            O("belt", 620, 456, 170, 14, dir=-1),
        ]
    return [
        O("slab", 60, 380, 130, 14), O("slab", 770, 380, 130, 14),
        O("mover", 300, 300, 120, 14, span=150, spd=76), O("mover", 560, 240, 120, 14, span=130, spd=64, axis="y"),
        O("crumble", 430, 380, 110, 14),
        O("gate", 240, 300, 16, 170, period=3.2, duty=.5), O("gate", 700, 300, 16, 170, period=3.2, duty=.5),
        O("spike", 380, 456, 200, 12),
        O("emitter", 470, 50, 42, 26, period=2.8),
        O("vent", 120, 442, 44, 28), O("vent", 800, 442, 44, 28),
        O("barrel", 330, 424, 34, 46, hp=22), O("barrel", 600, 424, 34, 46, hp=22),
        O("pylon", 470, 330, 38, 50, hp=70),
        O("crate", 200, 430, 40, 40, hp=50), O("crate", 730, 430, 40, 40, hp=50),
    ]


# ==============================================================================
#  共用物理（與地形互動）
# ==============================================================================
def world_move(u, dt, g, flying=False, is_player=False):
    prev = u.rect.copy()
    obs = g.obs
    # ---- X ----
    u.x += u.vx * dt
    u.rect.x = int(u.x)
    for o in obs:
        if o.solid_now() and u.rect.colliderect(o.rect):
            if u.vx > 0:
                u.x = o.rect.left - u.w
            elif u.vx < 0:
                u.x = o.rect.right
            else:
                u.x = o.rect.left - u.w if u.rect.centerx < o.rect.centerx else o.rect.right
            u.vx = 0.
            u.rect.x = int(u.x)
    u.x = clamp(u.x, -110 if not is_player else 4, (LW + 110 - u.w) if not is_player else LW - u.w - 4)
    u.rect.x = int(u.x)
    # ---- Y ----
    u.y += u.vy * dt
    u.rect.y = int(u.y)
    was = u.on_ground
    u.on_ground = False
    u.rider = None
    if flying:
        u.y = clamp(u.y, 14, GROUND_Y - u.h - 4)
        u.rect.y = int(u.y)
        for o in obs:
            o.field(u, dt, g, is_player)
        return was
    if u.y + u.h >= GROUND_Y and u.vy >= 0:
        u.y = GROUND_Y - u.h
        u.vy = 0.
        u.on_ground = True
        u.rect.y = int(u.y)
    for o in obs:
        if not o.alive:
            continue
        if o.solid_now():
            if u.rect.colliderect(o.rect):
                if u.vy > 0 and prev.bottom <= o.rect.top + 8:
                    u.y = o.rect.top - u.h
                    u.vy = 0.
                    u.on_ground = True
                    u.rider = o
                    o.on_land(u, g, is_player)
                elif u.vy < 0 and prev.top >= o.rect.bottom - 8:
                    u.y = o.rect.bottom
                    u.vy = 60.
                u.rect.y = int(u.y)
        elif o.plat_now():
            if u.vy >= 0 and prev.bottom <= o.rect.top + 7:
                nb = u.y + u.h
                if o.rect.top <= nb <= o.rect.top + 26 and u.x + u.w > o.rect.left + 3 and u.x < o.rect.right - 3:
                    u.y = o.rect.top - u.h
                    u.vy = 0.
                    u.on_ground = True
                    u.rider = o
                    u.rect.y = int(u.y)
                    o.on_land(u, g, is_player)
        o.field(u, dt, g, is_player)
    if u.rider is not None:
        u.rider.on_stand(u, dt, g, is_player)
        u.x = clamp(u.x, 2, LW - u.w - 2)
    u.rect.topleft = (int(u.x), int(u.y))
    return was


# ==============================================================================
#  資料表
# ==============================================================================
CHARS = [
    dict(key="ecoli", name_en="E. COLI", name_zh="大腸桿菌", color=(96, 240, 170),
         desc_en="Balanced frame, reliable everywhere.", desc_zh="均衡機體，全能可靠。",
         atk=84, speed=308, hp=26, ult=100, dash=1.0, skcd=9.0, armor=0,
         sk_en="Fission Pulse", sk_zh="分裂脈衝",
         skd_en="Angular shockwave: knockback, stun, brief invuln.",
         skd_zh="稜形衝擊波：擊退、暈眩並短暫無敵。"),
    dict(key="yeast", name_en="S. CEREVISIAE", name_zh="釀酒酵母", color=(255, 150, 60),
         desc_en="Heavy plating, high power, slower.", desc_zh="重裝高攻，速度較慢。",
         atk=100, speed=268, hp=32, ult=100, dash=1.25, skcd=13.0, armor=3,
         sk_en="Ferment Surge", sk_zh="發酵狂潮",
         skd_en="+60% damage, lifesteal and burn aura for 7s.",
         skd_zh="7 秒傷害 +60%，附帶吸血與燃燒光環。"),
    dict(key="subtilis", name_en="B. SUBTILIS", name_zh="枯草桿菌", color=(96, 186, 255),
         desc_en="Fast, evasive, short dash cooldown.", desc_zh="高速閃避，衝刺冷卻極短。",
         atk=76, speed=352, hp=23, ult=90, dash=.65, skcd=10.0, armor=0,
         sk_en="Spore Phase", sk_zh="孢子相位",
         skd_en="3s invulnerable dash-state trailing burn spores.",
         skd_zh="3 秒無敵加速，沿路留下燃燒孢子。"),
    dict(key="lacto", name_en="LACTOBACILLUS", name_zh="乳酸菌", color=(240, 110, 200),
         desc_en="Zone control through corrosive fields.", desc_zh="以腐蝕場域控制戰場。",
         atk=80, speed=296, hp=25, ult=95, dash=1.05, skcd=9.5, armor=1,
         sk_en="Acid Lattice", sk_zh="酸性晶格",
         skd_en="Corrosive lattice: damage over time and slow.",
         skd_zh="生成腐蝕晶格，持續傷害並減速。"),
    dict(key="halo", name_en="HALOBACTERIUM", name_zh="鹽菌", color=(180, 130, 255),
         desc_en="Static specialist, reflects and shocks.", desc_zh="靜電專精，反射與電擊。",
         atk=82, speed=300, hp=24, ult=90, dash=.95, skcd=11.0, armor=2,
         sk_en="Static Veil", sk_zh="靜電帷幕",
         skd_en="4s reflect barrier, shock nova on expiry.",
         skd_zh="4 秒反射屏障，結束時釋放電擊新星。"),
]

WEAPONS = [
    dict(key="blade", kind="arc", name_en="RIFT BLADE", name_zh="裂隙刃", color=(96, 255, 210),
         desc_en="Wide burning arc, strong knockback.", desc_zh="大範圍燃燒斬，強力擊退。",
         cd=.32, dmg=34, rng=92, elem="burn",
         alt_en="Phase Cut - dash through foes", alt_zh="相位斬－穿刺衝擊", acost=22),
    dict(key="saw", kind="rapid", name_en="PRBA SAW", name_zh="prbA 電鋸", color=(255, 168, 48),
         desc_en="Shreds fast, builds heat.", desc_zh="高速切割，累積熱量。",
         cd=.08, dmg=11, rng=70, elem="bleed",
         alt_en="Disc Toss - bouncing sawblade", alt_zh="飛盤－彈跳鋸片", acost=18),
    dict(key="pipette", kind="gun", name_en="ENZYME PIPETTE", name_zh="酵素移液槍", color=(130, 216, 255),
         desc_en="Rapid corrosive rounds, reloads.", desc_zh="高速腐蝕彈，需換彈。",
         cd=.18, dmg=23, rng=0, elem="corrode", ammo=15,
         alt_en="Burst Fire - 3 round spread", alt_zh="三連發散射", acost=14),
    dict(key="bow", kind="charge", name_en="PLASMID BOW", name_zh="質體弓", color=(176, 150, 255),
         desc_en="Charge for piercing shock bolt.", desc_zh="蓄力射出穿透電矢。",
         cd=.2, dmg=21, rng=0, elem="shock",
         alt_en="Split Volley - 3 way fan", alt_zh="散裂齊射－三方扇形", acost=20),
    dict(key="mortar", kind="mortar", name_en="ANTIBIO MORTAR", name_zh="抗生素臼砲", color=(255, 118, 104),
         desc_en="Lobbed shells, splash burn.", desc_zh="拋射爆裂彈，範圍燃燒。",
         cd=.66, dmg=31, rng=0, elem="burn", ammo=5,
         alt_en="Airburst - cluster bomblets", alt_zh="空爆－集束子彈", acost=26),
    dict(key="whip", kind="whip", name_en="PHAGE WHIP", name_zh="噬菌體鞭", color=(120, 244, 255),
         desc_en="Long reach, chains shock.", desc_zh="長距離，連鎖電擊。",
         cd=.38, dmg=25, rng=132, elem="shock",
         alt_en="Grapple - yank foe or pull in", alt_zh="抓鉤－拉扯敵人或位移", acost=16),
    dict(key="lance", kind="lance", name_en="VOID LANCE", name_zh="虛空長矛", color=(200, 120, 255),
         desc_en="Charged void beam, pierces all.", desc_zh="蓄力虛空光束，全穿透。",
         cd=.5, dmg=46, rng=0, elem="void",
         alt_en="Collapse - short void blast", alt_zh="崩縮－短距虛空爆", acost=24),
]

AIR = {"spore", "drone", "mother", "wraith", "hexer"}

EN = {
    "paraben": dict(w=36, h=44, hp=26, sp=80, dmg=1, sc=10, xp=7, col=(230, 60, 66), ar=0,
                    name_en="PARABEN", name_zh="防腐劑"),
    "spore": dict(w=34, h=32, hp=18, sp=128, dmg=1, sc=14, xp=8, col=(196, 96, 240), ar=0,
                  name_en="SPORE", name_zh="孢子"),
    "phage": dict(w=40, h=40, hp=30, sp=62, dmg=1, sc=20, xp=10, col=(64, 208, 206), ar=1,
                  name_en="PHAGE", name_zh="噬菌體"),
    "metal": dict(w=54, h=58, hp=88, sp=54, dmg=2, sc=42, xp=20, col=(212, 152, 44), ar=5,
                  name_en="HEAVY METAL", name_zh="重金屬"),
    "blob": dict(w=46, h=42, hp=46, sp=66, dmg=1, sc=22, xp=12, col=(154, 214, 88), ar=0,
                 name_en="BLOB", name_zh="抗生素凝團"),
    "blobmini": dict(w=24, h=22, hp=14, sp=136, dmg=1, sc=6, xp=4, col=(184, 234, 120), ar=0,
                     name_en="BLOBLING", name_zh="小凝團"),
    "bomber": dict(w=34, h=36, hp=20, sp=140, dmg=1, sc=18, xp=9, col=(255, 132, 64), ar=0,
                   name_en="VESICLE", name_zh="爆裂囊"),
    "shielder": dict(w=44, h=50, hp=48, sp=62, dmg=1, sc=28, xp=14, col=(108, 162, 236), ar=2,
                     name_en="BIOFILM GUARD", name_zh="生物膜盾兵"),
    "cryo": dict(w=38, h=40, hp=32, sp=66, dmg=1, sc=24, xp=12, col=(140, 224, 255), ar=1,
                 name_en="CRYO SPORE", name_zh="冷凍孢子"),
    "drone": dict(w=42, h=30, hp=34, sp=96, dmg=1, sc=30, xp=15, col=(204, 208, 240), ar=1,
                  name_en="UV DRONE", name_zh="紫外線無人機"),
    "mother": dict(w=62, h=58, hp=155, sp=40, dmg=2, sc=92, xp=38, col=(214, 88, 176), ar=2,
                   name_en="MUTANT MOTHER", name_zh="突變母體"),
    "lancer": dict(w=42, h=46, hp=52, sp=118, dmg=2, sc=38, xp=18, col=(255, 96, 128), ar=2,
                   name_en="LANCER", name_zh="穿刺兵"),
    "turret": dict(w=48, h=44, hp=70, sp=0, dmg=1, sc=36, xp=17, col=(160, 170, 200), ar=6,
                   name_en="SPORE TURRET", name_zh="孢子砲塔"),
    "warden": dict(w=58, h=62, hp=140, sp=44, dmg=2, sc=70, xp=30, col=(120, 140, 170), ar=9,
                   name_en="WARDEN", name_zh="守衛機"),
    "wraith": dict(w=38, h=46, hp=42, sp=120, dmg=1, sc=44, xp=20, col=(176, 120, 255), ar=0,
                   name_en="WRAITH", name_zh="幽體"),
    "sapper": dict(w=36, h=38, hp=34, sp=92, dmg=1, sc=34, xp=16, col=(230, 200, 90), ar=1,
                   name_en="SAPPER", name_zh="佈雷兵"),
    "hexer": dict(w=40, h=44, hp=50, sp=74, dmg=1, sc=48, xp=22, col=(120, 255, 200), ar=1,
                  name_en="HEXER", name_zh="咒術體"),
    "reaper": dict(w=40, h=48, hp=58, sp=150, dmg=2, sc=54, xp=24, col=(255, 70, 90), ar=1,
                   name_en="REAPER", name_zh="收割者"),
}

BOSSES = {
    "necro": dict(name_en="NECROPLASM", name_zh="腐漿巨龍", hp=620, col=(240, 62, 70)),
    "monarch": dict(name_en="PHAGE MONARCH", name_zh="噬菌君主", hp=700, col=(62, 216, 208)),
    "colossus": dict(name_en="BIOFILM COLOSSUS", name_zh="生物膜巨像", hp=820, col=(154, 216, 94)),
    "mitosis": dict(name_en="VOID MITOSIS", name_zh="虛空分裂體", hp=760, col=(186, 112, 255)),
}
BOSS_ORDER = ("monarch", "colossus", "mitosis", "necro")

MODS = ("armored", "swift", "regen", "volatile", "leech", "warded")

AFFIX = {
    "none": dict(key="af_none", c=GREY),
    "frenzy": dict(key="af_frenzy", c=RED),
    "hard": dict(key="af_hard", c=GREY),
    "volatile": dict(key="af_volatile", c=AMB),
    "swarm": dict(key="af_swarm", c=LIME),
    "lowg": dict(key="af_lowg", c=CYAN),
    "static": dict(key="af_static", c=ICE),
    "vamp": dict(key="af_vamp", c=MAG),
    "shield": dict(key="af_shield", c=VIOL),
    "hunt": dict(key="af_hunt", c=GOLD),
}
AFFIX_KEYS = ("frenzy", "hard", "volatile", "swarm", "lowg", "static", "vamp", "shield", "hunt")

# ---- 強化卡（含稀有度） ----
AUG = [
    dict(r=0, n_en="Enzyme Boost", n_zh="酵素強化", d_en="Damage +18%", d_zh="傷害 +18%", c=RED,
         f=lambda p: setattr(p, "atk_mult", p.atk_mult * 1.18)),
    dict(r=0, n_en="Thick Membrane", n_zh="強化膜壁", d_en="Max HP +3, heal 3", d_zh="最大結構 +3 並修復 3", c=LIME,
         f=lambda p: (setattr(p, "max_hp", p.max_hp + 3), setattr(p, "hp", min(p.max_hp, p.hp + 3)))),
    dict(r=0, n_en="Flagella Tune", n_zh="鞭毛調校", d_en="Move speed +12%", d_zh="移動速度 +12%", c=CYAN,
         f=lambda p: setattr(p, "move_mult", p.move_mult * 1.12)),
    dict(r=0, n_en="Rapid Metabolism", n_zh="快速代謝", d_en="Attack speed +15%", d_zh="攻擊速度 +15%", c=GOLD,
         f=lambda p: setattr(p, "cd_mult", p.cd_mult * .87)),
    dict(r=0, n_en="Lethal Mutation", n_zh="致命突變", d_en="Crit +9%", d_zh="暴擊率 +9%", c=MAG,
         f=lambda p: setattr(p, "crit", min(.8, p.crit + .09))),
    dict(r=0, n_en="Mitochondria+", n_zh="粒線體＋", d_en="Energy regen +9", d_zh="能量回復 +9", c=CYAN,
         f=lambda p: setattr(p, "energy_regen", p.energy_regen + 9)),
    dict(r=0, n_en="Ion Magnet", n_zh="離子磁場", d_en="Pickup range, drops +20%", d_zh="拾取範圍提升，掉落 +20%", c=VIOL,
         f=lambda p: (setattr(p, "magnet", p.magnet + 70), setattr(p, "drop_mult", p.drop_mult + .2))),
    dict(r=0, n_en="Spiked Capsule", n_zh="刺狀莢膜", d_en="Contact damage +16", d_zh="接觸反傷 +16", c=AMB,
         f=lambda p: setattr(p, "thorns", p.thorns + 16)),
    dict(r=0, n_en="Hard Shell", n_zh="硬化外殼", d_en="Armor +3 (flat reduction)", d_zh="護甲 +3（固定減傷）", c=GREY,
         f=lambda p: setattr(p, "armor", p.armor + 3)),
    dict(r=0, n_en="Ammo Belt", n_zh="彈藥帶", d_en="Max ammo +6, reload 25% faster", d_zh="最大彈藥 +6，換彈快 25%",
         c=AMB, f=lambda p: (setattr(p, "ammo_bonus", p.ammo_bonus + 6),
                             setattr(p, "reload_mult", p.reload_mult * .75), p.refresh_ammo())),
    dict(r=0, n_en="Coolant Gel", n_zh="冷卻凝膠", d_en="Heat build -35%", d_zh="熱量累積 -35%", c=AMB,
         f=lambda p: setattr(p, "heat_mult", p.heat_mult * .65)),
    dict(r=1, n_en="Chain Reaction", n_zh="連鎖反應", d_en="+5% damage per chain step", d_zh="每段連段 +5% 傷害", c=GOLD,
         f=lambda p: setattr(p, "combo_dmg", p.combo_dmg + .05)),
    dict(r=1, n_en="Gas Vesicle", n_zh="氣囊", d_en="Extra jump +1", d_zh="額外跳躍 +1", c=LIME,
         f=lambda p: setattr(p, "max_jumps", p.max_jumps + 1)),
    dict(r=1, n_en="Osmotic Rounds", n_zh="滲透彈頭", d_en="Projectiles pierce +1", d_zh="投射物穿透 +1", c=CYAN,
         f=lambda p: setattr(p, "pierce", p.pierce + 1)),
    dict(r=1, n_en="Multi Channel", n_zh="多通道槍口", d_en="Guns fire +1 projectile", d_zh="槍械多射 1 發", c=CYAN,
         f=lambda p: setattr(p, "proj", p.proj + 1)),
    dict(r=1, n_en="Chemotaxis", n_zh="趨化推進", d_en="Dash cd -25%, dash damages", d_zh="衝刺冷卻 -25%，衝刺傷害", c=CYAN,
         f=lambda p: (setattr(p, "dash_cd_mult", p.dash_cd_mult * .75), setattr(p, "dash_dmg", p.dash_dmg + 34))),
    dict(r=1, n_en="Toxin Refinery", n_zh="毒素精煉", d_en="Status damage +60%", d_zh="狀態傷害 +60%", c=TOXIC,
         f=lambda p: setattr(p, "elem_mult", p.elem_mult + .6)),
    dict(r=1, n_en="Sticky Payload", n_zh="黏性載荷", d_en="Status duration +50%", d_zh="狀態持續 +50%", c=TOXIC,
         f=lambda p: setattr(p, "status_mult", p.status_mult + .5)),
    dict(r=1, n_en="Kinetic Breaker", n_zh="動能破勢", d_en="Stagger buildup +45%", d_zh="架勢累積 +45%", c=AMB,
         f=lambda p: setattr(p, "stagger_mult", p.stagger_mult + .45)),
    dict(r=1, n_en="Hollow Point", n_zh="穿甲彈心", d_en="Ignore 60% of enemy armor", d_zh="無視 60% 敵方護甲", c=GREY,
         f=lambda p: setattr(p, "pen", min(.95, p.pen + .6))),
    dict(r=1, n_en="Phagocytosis", n_zh="胞噬作用", d_en="Kill heal chance +20%", d_zh="擊殺回復機率 +20%", c=LIME,
         f=lambda p: setattr(p, "lifesteal", min(.9, p.lifesteal + .2))),
    dict(r=1, n_en="Neural Relay", n_zh="神經傳導", d_en="Skill cooldown -24%", d_zh="技能冷卻 -24%", c=CYAN,
         f=lambda p: setattr(p, "skill_cd_mult", p.skill_cd_mult * .76)),
    dict(r=1, n_en="Reactive Plating", n_zh="反應裝甲", d_en="Parry window +0.12s, parry blast", d_zh="彈反窗口 +0.12 秒並爆波",
         c=ICE, f=lambda p: (setattr(p, "parry_win", p.parry_win + .12), setattr(p, "parry_blast", True))),
    dict(r=2, n_en="Reflective Coat", n_zh="反射鏡衣", d_en="Guard reflects enemy shots", d_zh="防禦可反射敵方子彈", c=ICE,
         f=lambda p: setattr(p, "reflect", True)),
    dict(r=2, n_en="Void Catalyst", n_zh="虛空觸媒", d_en="Reactions +80% power", d_zh="元素反應威力 +80%", c=VIOL,
         f=lambda p: setattr(p, "react_mult", p.react_mult + .8)),
    dict(r=2, n_en="Overclock Core", n_zh="超頻核心", d_en="Overdrive builds 60% faster, +2s", d_zh="超載充能快 60%，時長 +2 秒",
         c=GOLD, f=lambda p: (setattr(p, "ovd_gain", p.ovd_gain * 1.6), setattr(p, "ovd_len", p.ovd_len + 2.))),
    dict(r=2, n_en="Executioner", n_zh="處決者", d_en="Execute threshold 12% -> 24%", d_zh="處決門檻 12%→24%", c=BLOOD,
         f=lambda p: setattr(p, "exec_thr", p.exec_thr + .12)),
    dict(r=2, n_en="Second Wall", n_zh="第二道牆", d_en="Barrier 24, regenerates slowly", d_zh="獲得 24 點屏障並緩慢回復", c=ICE,
         f=lambda p: (setattr(p, "barrier_max", p.barrier_max + 24), setattr(p, "barrier", p.barrier_max))),
    dict(r=2, n_en="Twin Strike", n_zh="雙重打擊", d_en="Melee hits twice for 55%", d_zh="近戰追加一次 55% 傷害", c=MAG,
         f=lambda p: setattr(p, "double", True)),
    dict(r=2, n_en="Ultimate Loop", n_zh="終極迴路", d_en="Ultimate charge +45%", d_zh="終極充能 +45%", c=GOLD,
         f=lambda p: setattr(p, "ult_gain", p.ult_gain * 1.45)),
]


# ==============================================================================
#  狀態 / 元素反應
# ==============================================================================
STAT_COL = {"burn": (255, 130, 60), "corrode": TOXIC, "bleed": BLOOD, "shock": CYAN,
            "chill": ICE, "freeze": (200, 244, 255), "void": VIOL, "stun": GOLD}
STAT_DUR = {"burn": 2.6, "corrode": 3.4, "bleed": 2.4, "shock": .9, "chill": 2.4,
            "freeze": 1.3, "void": 4.0, "stun": .8}


class Stat:
    def __init__(self):
        self.d = {}

    def add(self, name, dur, power=1.0):
        cur = self.d.get(name)
        if cur is None:
            self.d[name] = [dur, power]
        else:
            cur[0] = max(cur[0], dur)
            cur[1] = max(cur[1], power)

    def has(self, n):
        return n in self.d

    def power(self, n):
        e = self.d.get(n)
        return e[1] if e else 0.0

    def clear(self, n):
        self.d.pop(n, None)

    def update(self, dt):
        dead = []
        for k, v in self.d.items():
            v[0] -= dt
            if v[0] <= 0:
                dead.append(k)
        for k in dead:
            self.d.pop(k, None)
        return dead

    def names(self):
        return list(self.d.keys())


# ==============================================================================
#  投射物 / 掉落
# ==============================================================================
class Proj:
    __slots__ = ("x", "y", "vx", "vy", "r", "dmg", "owner", "kind", "col", "life", "pierce",
                 "grav", "homing", "elem", "expl", "crit", "dead", "rect", "t", "spin", "bounce")

    def __init__(self, x, y, vx, vy, dmg, owner, kind="shot", col=CYAN, r=7, life=2.2,
                 pierce=0, grav=0., homing=0., elem=None, expl=0., crit=False, bounce=0):
        self.x, self.y = float(x), float(y)
        self.vx, self.vy = float(vx), float(vy)
        self.r = r
        self.dmg = dmg
        self.owner = owner
        self.kind = kind
        self.col = col
        self.life = life
        self.pierce = pierce
        self.grav = grav
        self.homing = homing
        self.elem = elem
        self.expl = expl
        self.crit = crit
        self.bounce = bounce
        self.dead = False
        self.t = 0.
        self.spin = random.uniform(0, 6.3)
        self.rect = pygame.Rect(int(x - r), int(y - r), int(r * 2), int(r * 2))

    def update(self, dt, g):
        self.t += dt
        self.life -= dt
        if self.life <= 0:
            self.dead = True
            return
        if self.homing > 0:
            tgt = None
            if self.owner == "e":
                tgt = g.player
            else:
                best = 1e9
                for e in g.targets():
                    d = (e.rect.centerx - self.x) ** 2 + (e.rect.centery - self.y) ** 2
                    if d < best:
                        best = d
                        tgt = e
            if tgt is not None:
                dx = tgt.rect.centerx - self.x
                dy = tgt.rect.centery - self.y
                d = max(1., math.hypot(dx, dy))
                self.vx += dx / d * self.homing * dt
                self.vy += dy / d * self.homing * dt
        self.vy += self.grav * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.spin += dt * 10
        self.rect.center = (int(self.x), int(self.y))
        # 與地形互動
        for o in g.obs:
            if o.blocks_shots() and self.rect.colliderect(o.rect):
                if self.owner in ("p", "n") and o.maxhp > 0:
                    o.damage(self.dmg, g, self.x)
                if self.bounce > 0:
                    self.bounce -= 1
                    self.vx *= -1
                else:
                    if self.expl > 0:
                        g.explode(self.x, self.y, self.expl, self.dmg, self.owner, self.elem, self.col)
                    self.dead = True
                return
        if self.grav > 0 and self.y > GROUND_Y - 4:
            if self.bounce > 0:
                self.bounce -= 1
                self.y = GROUND_Y - 6
                self.vy = -abs(self.vy) * .6
            else:
                self.dead = True
                g.explode(self.x, GROUND_Y - 6, max(42., self.expl), self.dmg, self.owner, self.elem, self.col)
            return
        if self.kind == "disc":
            if self.y > GROUND_Y - 6 and self.vy > 0:
                self.vy = -abs(self.vy) * .8
            if (self.x < 12 and self.vx < 0) or (self.x > LW - 12 and self.vx > 0):
                if self.bounce > 0:
                    self.bounce -= 1
                    self.vx *= -1
                else:
                    self.dead = True
        if self.x < -150 or self.x > LW + 150 or self.y > LH + 180 or self.y < -320:
            self.dead = True

    def draw(self, pt):
        k = self.kind
        c = self.col
        if k == "bolt":
            a = math.atan2(self.vy, self.vx)
            Lg = self.r * 3.6
            dx, dy = math.cos(a), math.sin(a)
            pt.glow((self.x, self.y), self.r * 3.0, c, .7)
            pt.poly(c, [(self.x + dx * self.r * 1.4, self.y + dy * self.r * 1.4),
                        (self.x - dy * self.r * .55, self.y + dx * self.r * .55),
                        (self.x - dx * Lg, self.y - dy * Lg),
                        (self.x + dy * self.r * .55, self.y - dx * self.r * .55)])
            pt.line(WHT, (self.x - dx * Lg * .5, self.y - dy * Lg * .5),
                    (self.x + dx * self.r, self.y + dy * self.r), max(1., self.r * .35))
        elif k == "shell":
            pt.glow((self.x, self.y), self.r * 2.4, c, .5)
            pt.hexa(dk(c, .5), (self.x, self.y), self.r * 1.1, self.r * .8)
            pt.hexa(c, (self.x, self.y), self.r * .72, self.r * .55)
            pt.line((255, 200, 140), (self.x, self.y), (self.x - self.vx * .05, self.y - self.vy * .05), 2)
        elif k == "acid":
            pt.glow((self.x, self.y), self.r * 2.6, c, .45)
            pt.dia(c, (self.x, self.y), self.r * .9, self.r * 1.2)
            pt.dia(WHT, (self.x, self.y - self.r * .2), self.r * .3, self.r * .4)
        elif k == "ice":
            pt.glow((self.x, self.y), self.r * 2.8, ICE, .5)
            for i in range(3):
                a = self.spin + i * 2.09
                pt.line(ICE, (self.x - math.cos(a) * self.r, self.y - math.sin(a) * self.r),
                        (self.x + math.cos(a) * self.r, self.y + math.sin(a) * self.r), 2.2)
            pt.sq(WHT, (self.x, self.y), self.r * .28)
        elif k == "fire":
            pt.glow((self.x, self.y), self.r * 3.0, (255, 150, 60), .7)
            pt.tri(c, (self.x, self.y), self.r, 1 if self.vy > 0 else 0)
            pt.tri(WHT, (self.x, self.y), self.r * .4, 1 if self.vy > 0 else 0)
        elif k == "disc":
            pt.glow((self.x, self.y), self.r * 2.6, c, .6)
            pt.ngon(dk(c, .6), (self.x, self.y), self.r * 1.15, self.r * 1.15, 6, self.spin)
            pt.ngon(c, (self.x, self.y), self.r * .7, self.r * .7, 6, -self.spin)
        elif k == "drop":
            pt.glow((self.x, self.y), self.r * 2.4, c, .55)
            pt.poly(c, [(self.x, self.y - self.r * 2), (self.x + self.r * .5, self.y + self.r),
                        (self.x - self.r * .5, self.y + self.r)])
        elif k == "mine":
            pt.glow((self.x, self.y), self.r * 2.2, c, .4 + .3 * math.sin(self.t * 10))
            pt.dia(c, (self.x, self.y), self.r, self.r * .7, 2)
            pt.xmark(c, (self.x, self.y), self.r * .5, 2)
        elif k == "void":
            pt.glow((self.x, self.y), self.r * 3.4, VIOL, .8)
            pt.ngon(VIOL, (self.x, self.y), self.r * 1.3, self.r * 1.0, 4, self.spin)
            pt.ngon(WHT, (self.x, self.y), self.r * .5, self.r * .4, 4, -self.spin)
        else:
            pt.glow((self.x, self.y), self.r * 2.8, c, .55)
            pt.dia(c, (self.x, self.y), self.r, self.r)
            pt.sq(WHT, (self.x, self.y), self.r * .3)


PICK_COL = {"hp": (255, 88, 108), "en": (108, 200, 255), "xp": LIME, "ovd": GOLD, "barrier": ICE}


class Pickup:
    __slots__ = ("x", "y", "vy", "kind", "t", "life", "rect")

    def __init__(self, x, y, kind):
        self.x, self.y = float(x), float(y)
        self.vy = -160.
        self.kind = kind
        self.t = random.random() * 6
        self.life = 14.
        self.rect = pygame.Rect(int(x - 9), int(y - 9), 18, 18)

    def update(self, dt, p):
        self.t += dt
        self.life -= dt
        self.vy += 900 * dt
        self.y += self.vy * dt
        if self.y > GROUND_Y - 12:
            self.y = GROUND_Y - 12
            self.vy = 0
        if p is not None and not p.dead:
            dx = p.rect.centerx - self.x
            dy = p.rect.centery - self.y
            d = math.hypot(dx, dy)
            if d < 72 + p.magnet:
                self.x += dx / max(1, d) * 300 * dt
                self.y += dy / max(1, d) * 300 * dt
        self.rect.center = (int(self.x), int(self.y))
        return self.life > 0

    def draw(self, pt):
        col = PICK_COL.get(self.kind, WHT)
        b = math.sin(self.t * 5) * 3
        y = self.y + b
        pt.glow((self.x, y), 18, col, .6)
        if self.kind == "hp":
            pt.poly(col, [(self.x - 3, y - 7), (self.x + 3, y - 7), (self.x + 3, y - 3), (self.x + 7, y - 3),
                          (self.x + 7, y + 3), (self.x + 3, y + 3), (self.x + 3, y + 7),
                          (self.x - 3, y + 7), (self.x - 3, y + 3), (self.x - 7, y + 3),
                          (self.x - 7, y - 3), (self.x - 3, y - 3)])
        elif self.kind == "en":
            pt.poly(col, [(self.x + 2, y - 8), (self.x - 5, y + 1), (self.x, y + 1),
                          (self.x - 2, y + 8), (self.x + 5, y - 1), (self.x, y - 1)])
        elif self.kind == "ovd":
            pt.dia(col, (self.x, y), 6, 8, 2)
            pt.sq(col, (self.x, y), 2)
        elif self.kind == "barrier":
            pt.poly(col, [(self.x, y - 8), (self.x + 6, y - 3), (self.x + 4, y + 7),
                          (self.x - 4, y + 7), (self.x - 6, y - 3)], 2)
        else:
            pt.dia(col, (self.x, y), 5, 5)
            pt.sq(WHT, (self.x - 1, y - 1), 1.4)


# ==============================================================================
#  單位基底（共用狀態 / 護甲 / 架勢 / 弱點）
# ==============================================================================
class Unit:
    def init_common(self):
        self.st = Stat()
        self.chill_stack = 0
        self.hit_flash = 0.
        self.stun = 0.
        self.dot_tick = 0.
        self.shield = 0.
        self.shield_max = 0.
        self.stagger = 0.
        self.stagger_max = 40.
        self.broke = 0.
        self.mods = []
        self.elite = False
        self.rider = None
        self.on_ground = False

    def alive(self):
        return self.hp > 0

    def armor_now(self):
        a = self.armor
        if "armored" in self.mods:
            a += 5
        if self.st.has("supercon"):
            a = 0
        return max(0., a)

    def dmg_taken_mult(self):
        m = 1.0
        if self.broke > 0:
            m *= 1.35
        if self.st.has("void"):
            m *= 1.0 + .22 * self.st.power("void")
        if self.st.has("freeze"):
            m *= 1.25
        return m

    def is_weak(self, from_x):
        return (from_x - self.rect.centerx) * self.face < 0

    def take(self, dmg, g, from_x=0., knock=0., pen=0.0, stag=1.0):
        if self.st.has("supercon"):
            pen = 1.0
        eff = max(1., dmg - self.armor_now() * (1. - clamp(pen, 0, 1)))
        eff *= self.dmg_taken_mult()
        if self.shield > 0:
            a = min(self.shield, eff)
            self.shield -= a
            eff -= a
            self.hit_flash = .14
            if self.shield <= 0:
                self.shield = 0.
                self.stun = max(self.stun, .5)
                g.parts.burst(self.rect.centerx, self.rect.centery, ICE, 14, 230, 3.4, .45, 250, True)
                g.sfx.play("parry", .06)
            if eff <= 0:
                return 0
        d = max(1, int(eff))
        self.hp -= d
        self.hit_flash = .18
        # 架勢
        self.stagger += d * .4 * stag
        if self.broke <= 0 and self.stagger >= self.stagger_max:
            self.stagger = 0.
            self.stagger_max *= 1.28
            self.broke = 3.0
            self.stun = max(self.stun, 1.15)
            g.texts.append(FText(self.rect.centerx, self.rect.y - 26, T("brk"), AMB, 24, .9))
            g.fx.append(Fx("shock", self.rect.centerx, self.rect.centery, .45, AMB, r=110))
            g.sfx.play("brk", .05)
            g.shake = max(g.shake, 10)
        if knock:
            hv = .3 if self.rect.w > 54 else 1.
            self.vx += sgn(self.rect.centerx - from_x) * knock * hv
            if self.kind not in AIR and self.on_ground:
                self.vy = min(self.vy, -70)
        return d

    def tick_status(self, dt, g):
        gone = self.st.update(dt)
        if "freeze" in gone:
            self.chill_stack = 0
        if self.broke > 0:
            self.broke = max(0., self.broke - dt)
        if self.hit_flash > 0:
            self.hit_flash = max(0., self.hit_flash - dt)
        if self.stun > 0:
            self.stun = max(0., self.stun - dt)
        self.stagger = max(0., self.stagger - 6 * dt)
        s = self.st
        if s.has("burn") or s.has("corrode") or s.has("bleed") or s.has("void"):
            self.dot_tick -= dt
            if self.dot_tick <= 0:
                self.dot_tick = .35
                dmg = 0.
                col = AMB
                if s.has("burn"):
                    dmg += 5.4 * s.power("burn")
                    col = STAT_COL["burn"]
                if s.has("corrode"):
                    dmg += 4.0 * s.power("corrode")
                    col = STAT_COL["corrode"]
                if s.has("bleed"):
                    dmg += 5.0 * s.power("bleed") * (1.5 if abs(self.vx) > 30 else 1.0)
                    col = STAT_COL["bleed"]
                if s.has("void"):
                    dmg += 3.2 * s.power("void")
                if dmg > 0:
                    self.hp -= dmg
                    g.texts.append(FText(self.rect.centerx + random.uniform(-7, 7), self.rect.y,
                                         str(int(max(1, dmg))), col, 15, .45))

    def acting(self):
        return self.stun <= 0 and not self.st.has("freeze") and not self.st.has("stun")

    def slow_mult(self):
        m = 1.0
        if self.st.has("chill"):
            m *= .55
        if self.st.has("shock"):
            m *= .8
        return m

    def draw_status(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        if self.hit_flash > 0:
            pt.glow((cx, cy), self.rect.w * .8, WHT, self.hit_flash * 3.2)
        s = self.st
        if s.has("burn"):
            for i in range(2):
                pt.tri(STAT_COL["burn"], (cx + random.uniform(-9, 9), cy + random.uniform(-10, 6)), 4, 0)
            pt.glow((cx, cy), r.w * .5, STAT_COL["burn"], .22)
        if s.has("corrode"):
            pt.glow((cx, cy), r.w * .5, TOXIC, .18)
            pt.dia(TOXIC, (cx, cy + r.h * .4), 4, 3)
        if s.has("bleed"):
            pt.line(BLOOD, (cx - 4, r.bottom), (cx - 4, r.bottom + 6), 2)
        if s.has("chill") or s.has("freeze"):
            c = ICE if not s.has("freeze") else (210, 245, 255)
            pt.hexa(c, (cx, cy), r.w * .58, r.h * .58, 2)
        if s.has("shock"):
            for i in range(2):
                a = self.t * 12 + i * 3
                pt.line(CYAN, (cx + math.cos(a) * 12, cy + math.sin(a) * 12),
                        (cx + math.cos(a + 1) * 16, cy + math.sin(a + 1) * 16), 2)
        if s.has("void"):
            pt.ngon(VIOL, (cx, cy), r.w * .66, r.h * .66, 4, self.t, 2)
        if s.has("stun") or self.stun > 0:
            for i in range(3):
                a = self.t * 8 + i * 2.1
                pt.sq(GOLD, (cx + math.cos(a) * 14, cy - r.h * .65 + math.sin(a) * 4), 2)
        if self.broke > 0:
            pt.xmark(AMB, (cx, cy - r.h * .7), 5, 2)

    def draw_bars(self, pt):
        if self.hp >= self.max_hp - .5 and self.shield <= 0 and self.stagger <= 1:
            return
        r = self.rect
        w = max(28, r.w)
        x = r.centerx - w * .5
        y = r.y - 13
        f = clamp(self.hp_show / self.max_hp, 0, 1)
        pt.rect((14, 10, 14), (x, y, w, 5))
        pt.poly(mix(RED, LIME, f), [(x, y), (x + w * f, y), (x + w * f - 2, y + 5), (x, y + 5)])
        pt.rect(dk(EDGE, .8), (x, y, w, 5), 1)
        if self.shield > 0 and self.shield_max > 0:
            pt.rect(ICE, (x, y - 4, w * clamp(self.shield / self.shield_max, 0, 1), 2))
        if self.stagger > 1:
            pt.rect(AMB, (x, y + 6, w * clamp(self.stagger / self.stagger_max, 0, 1), 2))


# ==============================================================================
#  玩家
# ==============================================================================
COMBO_RANK = ((0, "D"), (6, "C"), (14, "B"), (26, "A"), (42, "S"), (64, "SS"), (95, "SSS"))


class Player(Unit):
    def __init__(self, char, wkey, g):
        self.g = g
        self.char = char
        self.ckey = char["key"]
        self.color = char["color"]
        self.kind = "player"
        self.w, self.h = 38, 52
        self.x, self.y = 150., float(GROUND_Y - 52)
        self.rect = pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        self.vx = self.vy = 0.
        self.face = 1
        self.t = 0.
        self.init_common()

        self.max_hp = char["hp"]
        self.hp = self.max_hp
        self.hp_show = self.hp
        self.base_speed = char["speed"]
        self.atk_mult = char["atk"] / 84.0
        self.dash_cd_base = char["dash"]
        self.skill_cd_base = char["skcd"]
        self.armor = char["armor"]

        self.move_mult = 1.
        self.cd_mult = 1.
        self.crit = .05
        self.lifesteal = 0.
        self.pierce = 0
        self.thorns = 0
        self.magnet = 0.
        self.energy_regen = 19.
        self.combo_dmg = 0.
        self.max_jumps = 1
        self.proj = 1
        self.heat_mult = 1.
        self.dash_cd_mult = 1.
        self.dash_dmg = 0
        self.reflect = False
        self.skill_cd_mult = 1.
        self.elem_mult = 1.
        self.status_mult = 1.
        self.parry_win = .2
        self.parry_blast = False
        self.drop_mult = 1.
        self.reload_mult = 1.
        self.ammo_bonus = 0
        self.stagger_mult = 1.
        self.pen = 0.
        self.react_mult = 1.
        self.exec_thr = .12
        self.double = False
        self.barrier = 0.
        self.barrier_max = 0.
        self.ovd_gain = 1.
        self.ovd_len = 6.
        self.ult_gain = 1.

        self.weapon = wkey
        self.max_energy = 100.
        self.energy = 100.
        self.max_ammo = 15
        self.ammo = 15
        self.reload_t = 0.
        self.heat = 0.
        self.overheat = 0.
        self.refresh_ammo()

        self.jumps = 1
        self.coyote = 0.
        self.p_up = self.p_dash = self.p_ult = self.p_skill = self.p_alt = self.p_ovd = False

        self.atk_cd = 0.
        self.swing_t = 0.
        self.swing_max = .26
        self.muzzle = 0.
        self.saw_spin = 0.
        self.charge = 0.
        self.charging = False
        self.whip_t = 0.
        self.lance_t = 0.
        self.phase_t = 0.

        self.iframe = 0.
        self.guarding = False
        self.was_guard = False
        self.parry = 0.
        self.riposte = 0.
        self.dash_t = 0.
        self.dash_cd = 0.
        self.trail = []
        self.grap = None
        self.grap_t = 0.

        self.combo = 0
        self.combo_t = 0.
        self.ult = 0.
        self.ult_need = float(char["ult"])
        self.ult_t = 0.
        self.ult_kind = None
        self.ult_tick = 0.
        self.ult_n = 0
        self.ovd = 0.
        self.ovd_t = 0.

        self.skill_cd = 0.
        self.buff_atk = 0.
        self.buff_spd = 0.
        self.spore_t = 0.
        self.spore_tick = 0.
        self.veil = 0.
        self.walk = 0.
        self.dead = False

    # ---------- helpers ----------
    def wdata(self):
        for w in WEAPONS:
            if w["key"] == self.weapon:
                return w
        return WEAPONS[0]

    def refresh_ammo(self):
        w = self.wdata()
        base = w.get("ammo", 15)
        self.max_ammo = int(base + self.ammo_bonus)
        self.ammo = min(getattr(self, "ammo", self.max_ammo), self.max_ammo)
        if self.ammo <= 0:
            self.ammo = self.max_ammo

    def swap(self, step):
        i = 0
        for j, w in enumerate(WEAPONS):
            if w["key"] == self.weapon:
                i = j
        self.set_weapon((i + step) % len(WEAPONS))

    def set_weapon(self, i):
        if not (0 <= i < len(WEAPONS)):
            return
        if WEAPONS[i]["key"] == self.weapon:
            return
        self.weapon = WEAPONS[i]["key"]
        self.atk_cd = max(self.atk_cd, .16)
        self.charge = 0.
        self.charging = False
        self.reload_t = 0.
        self.refresh_ammo()
        self.g.sfx.play("ui")

    def rank(self):
        r = "D"
        i = 0
        for j, (thr, nm) in enumerate(COMBO_RANK):
            if self.combo >= thr:
                r = nm
                i = j
        return r, i

    def dscale(self):
        _, ri = self.rank()
        m = self.atk_mult * (1. + self.combo * self.combo_dmg) * (1. + ri * .05)
        if self.buff_atk > 0:
            m *= 1.6
        if self.ovd_t > 0:
            m *= 1.15
        if self.riposte > 0:
            m *= 1.6
        return m

    def roll(self, base):
        d = base * self.dscale()
        c = random.random() < self.crit
        if c:
            d *= 2.
        return max(1, int(round(d))), c

    def speed(self):
        s = self.base_speed * self.move_mult
        if self.buff_spd > 0:
            s *= 1.35
        if self.ovd_t > 0:
            s *= 1.1
        s *= self.slow_mult()
        if self.guarding:
            s *= .34
        return s

    def gain_ult(self, v):
        self.ult = clamp(self.ult + v * self.ult_gain, 0, self.ult_need)

    def gain_ovd(self, v):
        if self.ovd_t <= 0:
            self.ovd = clamp(self.ovd + v * self.ovd_gain, 0, 100.)

    def free_ammo(self):
        return self.ovd_t > 0

    # ---------- update ----------
    def update(self, dt, g):
        self.t += dt
        inp = g.inp
        self.tick_status(dt, g)
        self.hp_show = self.hp
        for a in ("iframe", "atk_cd", "swing_t", "muzzle", "parry", "riposte", "dash_t",
                  "dash_cd", "overheat", "coyote", "skill_cd", "buff_atk", "buff_spd",
                  "spore_t", "whip_t", "lance_t", "phase_t", "veil", "grap_t", "ovd_t"):
            v = getattr(self, a)
            if v > 0:
                setattr(self, a, max(0., v - dt))
        if self.ovd_t <= 0 and self.veil <= 0 and self.barrier_max > 0 and self.barrier < self.barrier_max:
            self.barrier = min(self.barrier_max, self.barrier + 2.4 * dt)
        if self.combo_t > 0:
            self.combo_t -= dt
            if self.combo_t <= 0:
                self.combo = 0
        if self.reload_t > 0:
            self.reload_t -= dt
            if self.reload_t <= 0:
                self.reload_t = 0.
                self.ammo = self.max_ammo
                g.sfx.play("ui")
        if self.ult_t > 0:
            self.tick_ult(dt, g)
        if self.spore_t > 0:
            self.spore_tick -= dt
            if self.spore_tick <= 0:
                self.spore_tick = .2
                g.zones.append(Zone(self.rect.centerx, GROUND_Y if self.on_ground else self.rect.bottom,
                                    44, 20, 1.6, 16 * self.elem_mult, "p", (150, 255, 190), "burn"))
        if self.veil > 0 and self.veil < dt * 2:
            g.explode(self.rect.centerx, self.rect.centery, 150, int(40 * self.dscale()), "p", "shock", CYAN)

        # 防禦 / 彈反
        can = self.energy > 4 and self.dash_t <= 0 and self.ult_t <= 0
        self.guarding = bool(inp.get("guard")) and can
        if self.guarding:
            self.energy = max(0., self.energy - 23 * dt)
            if not self.was_guard:
                self.parry = self.parry_win
                g.sfx.play("guard")
        else:
            self.energy = min(self.max_energy, self.energy + self.energy_regen * dt)
        self.was_guard = self.guarding

        # 衝刺
        dn = bool(inp.get("dash"))
        if dn and not self.p_dash and self.dash_cd <= 0 and self.energy >= 16 and self.ult_t <= 0:
            self.dash_t = .18
            self.dash_cd = self.dash_cd_base * self.dash_cd_mult
            self.energy -= 16
            self.iframe = max(self.iframe, .26)
            self.vx = self.face * 800
            self.vy = 0
            g.sfx.play("dash")
            g.parts.cone(self.rect.centerx, self.rect.centery, math.pi if self.face > 0 else 0, .5,
                         self.color, 12, 260, 3, .3)
        self.p_dash = dn

        # 技能 / 終極 / 超載 / 副武器
        sk = bool(inp.get("skill"))
        if sk and not self.p_skill and self.skill_cd <= 0 and self.ult_t <= 0:
            self.use_skill(g)
        self.p_skill = sk

        up_ult = bool(inp.get("ult"))
        if up_ult and not self.p_ult and self.ult_t <= 0 and self.ult >= self.ult_need:
            self.start_ult(g)
        self.p_ult = up_ult

        ov = bool(inp.get("ovd"))
        if ov and not self.p_ovd and self.ovd_t <= 0 and self.ovd >= 100:
            self.ovd = 0.
            self.ovd_t = self.ovd_len
            g.flash = max(g.flash, .4)
            g.shake = max(g.shake, 10)
            g.sfx.play("ovd")
            g.banner(T("overdrive"), 1.2, GOLD)
        self.p_ovd = ov

        al = bool(inp.get("altfire"))
        if al and not self.p_alt and self.atk_cd <= 0 and self.ult_t <= 0 and self.dash_t <= 0:
            self.alt_fire(g)
        self.p_alt = al

        # 移動
        if self.dash_t <= 0 and self.phase_t <= 0:
            sp_v = self.speed()
            tgt = 0.
            if inp.get("left"):
                tgt -= sp_v
            if inp.get("right"):
                tgt += sp_v
            if tgt != 0 and self.ult_t <= 0:
                self.face = 1 if tgt > 0 else -1
            acc = 3200. if self.on_ground else 2200.
            if tgt == 0:
                self.vx += -sgn(self.vx) * min(abs(self.vx), acc * dt)
            else:
                self.vx += clamp(tgt - self.vx, -acc * dt, acc * dt)

        # 跳躍
        up = bool(inp.get("up"))
        if up and not self.p_up and self.ult_t <= 0:
            if self.on_ground or self.coyote > 0:
                self.vy = -660
                self.on_ground = False
                self.coyote = 0
                self.jumps = self.max_jumps - 1
                g.sfx.play("jump")
                g.parts.cone(self.rect.centerx, self.rect.bottom, math.pi / 2, .6, GREY, 7, 150, 3, .25)
            elif self.jumps > 0:
                self.vy = -590
                self.jumps -= 1
                g.sfx.play("jump")
                g.parts.cone(self.rect.centerx, self.rect.bottom, math.pi / 2, .9, self.color, 10, 190, 3, .3)
        if not up and self.vy < -250:
            self.vy = -250
        self.p_up = up

        # 抓鉤位移
        if self.grap is not None:
            self.grap_t -= dt
            gx, gy = self.grap
            dx, dy = gx - self.rect.centerx, gy - self.rect.centery
            d = math.hypot(dx, dy)
            if d < 30 or self.grap_t <= 0:
                self.grap = None
            else:
                self.vx = dx / d * 900
                self.vy = dy / d * 900

        # 物理
        gm = g.grav_mult()
        if self.dash_t > 0 or self.grap is not None:
            if self.dash_t > 0:
                self.vy = 0
        else:
            self.vy = min(1000., self.vy + 1900 * gm * dt)
        was_air = not self.on_ground
        world_move(self, dt, g, False, True)
        if self.on_ground:
            self.jumps = self.max_jumps
            self.coyote = .11
            if was_air:
                g.parts.cone(self.rect.centerx, self.rect.bottom, -math.pi / 2, 1.1, GREY, 6, 120, 2.6, .24)
        if self.on_ground and abs(self.vx) > 20:
            self.walk += dt * (6 + abs(self.vx) * .02)

        if self.dash_t > 0 or self.phase_t > 0:
            self.trail.append([self.rect.centerx, self.rect.centery, .24])
        for tr in self.trail:
            tr[2] -= dt
        self.trail = [t for t in self.trail if t[2] > 0][-10:]

        # 熱量
        if self.weapon == "saw":
            if (not inp.get("attack")) or self.overheat > 0 or self.ovd_t > 0:
                self.heat = max(0., self.heat - 34 * dt)
        else:
            self.heat = max(0., self.heat - 52 * dt)

        # 主攻擊
        atk = bool(inp.get("attack")) and not self.guarding and self.ult_t <= 0 and self.dash_t <= 0
        wd = self.wdata()
        if wd["kind"] in ("charge", "lance"):
            if atk:
                self.charging = True
                self.charge = min(1., self.charge + dt / (.55 if wd["kind"] == "lance" else .78))
            elif self.charging:
                if wd["kind"] == "lance":
                    self.fire_lance(g)
                else:
                    self.fire_bow(g)
                self.charging = False
                self.charge = 0.
        else:
            self.charging = False
            self.charge = 0.
            if atk:
                self.attack(g)

        # 相位斬 / 衝刺傷害
        if (self.phase_t > 0 or (self.dash_t > 0 and self.dash_dmg > 0)):
            dmg = 46 if self.phase_t > 0 else self.dash_dmg
            for e in g.targets():
                if self.rect.colliderect(e.rect):
                    g.hurt_enemy(e, int(dmg * self.dscale() * .6), False, self.rect.centerx, 150,
                                 "burn" if self.phase_t > 0 else None)
        if self.hp <= 0:
            self.dead = True

    # ---------- 攻擊 ----------
    def melee_box(self, rng, hpad=14):
        if self.face > 0:
            return pygame.Rect(int(self.rect.right - 6), int(self.rect.y - hpad * .5), int(rng), int(self.h + hpad))
        return pygame.Rect(int(self.rect.left - rng + 6), int(self.rect.y - hpad * .5), int(rng), int(self.h + hpad))

    def melee_hit(self, g, hb, base, elem, knock, stag=1.0):
        hit = 0
        for e in list(g.targets()):
            if hb.colliderect(e.rect):
                d, c = self.roll(base)
                if e.is_weak(self.rect.centerx):
                    d = int(d * 1.5)
                    c = True
                    g.texts.append(FText(e.rect.centerx, e.rect.y - 22, T("weak"), MAG, 18, .55))
                if e.hp <= e.max_hp * self.exec_thr and e.hp < e.max_hp and getattr(e, "boss", False) is False:
                    g.execute(e)
                    hit += 1
                    continue
                g.hurt_enemy(e, d, c, self.rect.centerx, knock, elem, stag * self.stagger_mult, self.pen)
                if self.double:
                    g.hurt_enemy(e, int(d * .55), False, self.rect.centerx, 0, elem, .5, self.pen)
                hit += 1
        g.hit_obstacles(hb, base * 1.2, self.rect.centerx)
        if hit:
            self.add_combo(g)
            if self.riposte > 0:
                self.riposte = 0.
                g.flash = max(g.flash, .2)
        return hit

    def attack(self, g):
        if self.atk_cd > 0:
            return
        wd = self.wdata()
        kind = wd["kind"]
        cdm = self.cd_mult * (.6 if self.ovd_t > 0 else 1.)
        if kind == "arc":
            self.atk_cd = wd["cd"] * cdm
            self.swing_max = .26
            self.swing_t = self.swing_max
            g.sfx.play("slash")
            hb = self.melee_box(wd["rng"], 20)
            n = self.melee_hit(g, hb, wd["dmg"], "burn", 250, 1.2)
            g.fx.append(Fx("spark", self.rect.centerx + self.face * 60, self.rect.centery, .18,
                           (120, 255, 214), r=52))
            if n:
                g.shake = max(g.shake, 5)
        elif kind == "rapid":
            if self.overheat > 0:
                return
            self.atk_cd = wd["cd"] * cdm
            self.swing_max = .12
            self.swing_t = self.swing_max
            if self.ovd_t <= 0:
                self.heat = min(100., self.heat + 5.2 * self.heat_mult)
                if self.heat >= 100:
                    self.overheat = 1.5
                    g.sfx.play("boom")
                    g.parts.burst(self.rect.centerx + self.face * 40, self.rect.centery,
                                  (255, 190, 120), 18, 210, 4, .5)
            g.sfx.play("saw", .05)
            hb = self.melee_box(wd["rng"], 4)
            self.melee_hit(g, hb, wd["dmg"], "bleed", 42, .6)
        elif kind == "whip":
            self.atk_cd = wd["cd"] * cdm
            self.swing_max = .22
            self.swing_t = self.swing_max
            self.whip_t = .22
            g.sfx.play("zap")
            hb = self.melee_box(wd["rng"], -16)
            first = None
            for e in g.targets():
                if hb.colliderect(e.rect):
                    first = e
                    break
            self.melee_hit(g, hb, wd["dmg"], "shock", 100, 1.0)
            if first is not None:
                ch = 0
                for e in g.targets():
                    if e is first or ch >= 2:
                        continue
                    if (e.rect.centerx - first.rect.centerx) ** 2 + (e.rect.centery - first.rect.centery) ** 2 < 180 ** 2:
                        d, c = self.roll(wd["dmg"] * .55)
                        g.hurt_enemy(e, d, c, first.rect.centerx, 30, "shock", .5, self.pen)
                        g.fx.append(Fx("bolt", first.rect.centerx, first.rect.centery, .18, CYAN,
                                       r=e.rect.centerx, ang=e.rect.centery))
                        ch += 1
        elif kind == "gun":
            if self.reload_t > 0:
                return
            if self.ammo <= 0 and not self.free_ammo():
                self.reload_t = 1.05 * self.reload_mult
                return
            self.atk_cd = wd["cd"] * cdm
            if not self.free_ammo():
                self.ammo -= 1
            self.muzzle = .09
            g.sfx.play("shoot")
            bx = self.rect.centerx + self.face * 28
            by = self.rect.centery - 2
            n = max(1, self.proj)
            for i in range(n):
                sp = 0. if n == 1 else (i - (n - 1) / 2.) * .09
                d, c = self.roll(wd["dmg"])
                g.add_proj(Proj(bx, by, math.cos(sp) * 760 * self.face, math.sin(sp) * 760, d, "p",
                                "bolt", (140, 216, 255), 7, 1.3, self.pierce, elem="corrode", crit=c))
            g.parts.cone(bx, by, 0 if self.face > 0 else math.pi, .25, (170, 230, 255), 5, 190, 2.6, .18)
            if self.ammo <= 0 and not self.free_ammo():
                self.reload_t = 1.05 * self.reload_mult
        elif kind == "mortar":
            if self.reload_t > 0:
                return
            if self.ammo <= 0 and not self.free_ammo():
                self.reload_t = 1.45 * self.reload_mult
                return
            self.atk_cd = wd["cd"] * cdm
            if not self.free_ammo():
                self.ammo -= 1
            self.muzzle = .12
            g.sfx.play("boom", .08)
            d, c = self.roll(wd["dmg"])
            g.add_proj(Proj(self.rect.centerx + self.face * 24, self.rect.centery - 10, 440 * self.face,
                            -340, d, "p", "shell", (255, 150, 110), 9, 3.0, 0, grav=900.,
                            elem="burn", expl=80., crit=c))
            self.vx -= self.face * 70
            if self.ammo <= 0 and not self.free_ammo():
                self.reload_t = 1.45 * self.reload_mult

    def fire_bow(self, g):
        if self.charge < .14:
            return
        wd = self.wdata()
        f = self.charge
        self.atk_cd = wd["cd"] * self.cd_mult
        self.muzzle = .1
        g.sfx.play("zap")
        d, c = self.roll(wd["dmg"] * (0.7 + f * 2.7))
        pierce = self.pierce + (2 if f > .9 else (1 if f > .55 else 0))
        g.add_proj(Proj(self.rect.centerx + self.face * 28, self.rect.centery - 2,
                        (720 + f * 470) * self.face, 0, d, "p", "bolt", (186, 156, 255),
                        7 + f * 6, 1.6, pierce, elem="shock", crit=c))
        if f > .9:
            g.shake = max(g.shake, 5)

    def fire_lance(self, g):
        if self.charge < .2:
            return
        wd = self.wdata()
        f = self.charge
        self.atk_cd = wd["cd"] * self.cd_mult
        self.lance_t = .22
        g.sfx.play("ult", .1)
        g.shake = max(g.shake, 8 + f * 6)
        base = wd["dmg"] * (.6 + f * 1.8)
        y = self.rect.centery - 2
        beam = pygame.Rect(self.rect.centerx if self.face > 0 else 0, y - 14,
                           LW if self.face > 0 else self.rect.centerx, 28)
        g.fx.append(Fx("beamh", 0, y, .3, VIOL, w=20 + f * 16))
        for e in list(g.targets()):
            if beam.colliderect(e.rect):
                d, c = self.roll(base)
                g.hurt_enemy(e, d, c, self.rect.centerx, 60, "void", 1.4 * self.stagger_mult, self.pen)
        g.hit_obstacles(beam, base, self.rect.centerx)
        self.add_combo(g)

    # ---------- 副武器 ----------
    def alt_fire(self, g):
        wd = self.wdata()
        cost = wd.get("acost", 18)
        if self.energy < cost and self.ovd_t <= 0:
            return
        if self.ovd_t <= 0:
            self.energy -= cost
        k = wd["key"]
        self.atk_cd = max(self.atk_cd, .3 * self.cd_mult)
        if k == "blade":
            self.phase_t = .26
            self.vx = self.face * 900
            self.iframe = max(self.iframe, .3)
            g.sfx.play("dash")
            g.fx.append(Fx("slash", self.rect.centerx, self.rect.centery, .3, (140, 255, 220), ang=0.0))
        elif k == "saw":
            g.sfx.play("saw", .02)
            d, c = self.roll(20)
            g.add_proj(Proj(self.rect.centerx + self.face * 20, self.rect.centery, 620 * self.face, -80,
                            d, "p", "disc", AMB, 12, 2.4, 6, grav=260., elem="bleed", crit=c, bounce=4))
        elif k == "pipette":
            g.sfx.play("shoot", .02)
            for i in (-1, 0, 1):
                d, c = self.roll(18)
                g.add_proj(Proj(self.rect.centerx + self.face * 26, self.rect.centery,
                                math.cos(i * .16) * 700 * self.face, math.sin(i * .16) * 700, d, "p",
                                "bolt", (150, 230, 255), 6, 1.2, self.pierce, elem="corrode", crit=c))
        elif k == "bow":
            g.sfx.play("zap", .02)
            for i in (-1, 0, 1):
                d, c = self.roll(24)
                g.add_proj(Proj(self.rect.centerx + self.face * 26, self.rect.centery - 2,
                                math.cos(i * .22) * 820 * self.face, math.sin(i * .22) * 820, d, "p",
                                "bolt", VIOL, 7, 1.5, self.pierce + 1, elem="shock", crit=c))
        elif k == "mortar":
            g.sfx.play("boom", .04)
            d, _ = self.roll(16)
            for i in range(5):
                g.add_proj(Proj(self.rect.centerx + self.face * 20, self.rect.centery - 12,
                                (200 + i * 80) * self.face, -420 + i * 30, d, "p", "shell",
                                (255, 170, 110), 7, 2.4, 0, grav=940., elem="burn", expl=58.))
        elif k == "whip":
            g.sfx.play("grap")
            tgt = None
            best = 1e9
            for e in g.targets():
                if (e.rect.centerx - self.rect.centerx) * self.face > 0:
                    d2 = abs(e.rect.centerx - self.rect.centerx)
                    if d2 < best and d2 < 300:
                        best = d2
                        tgt = e
            if tgt is not None:
                g.fx.append(Fx("bolt", self.rect.centerx, self.rect.centery, .2, CYAN,
                               r=tgt.rect.centerx, ang=tgt.rect.centery))
                if tgt.rect.w >= 54 or getattr(tgt, "boss", False):
                    self.grap = (tgt.rect.centerx - self.face * 40, tgt.rect.centery)
                    self.grap_t = .35
                else:
                    tgt.vx = sgn(self.rect.centerx - tgt.rect.centerx) * 700
                    tgt.stun = max(tgt.stun, .4)
                    g.hurt_enemy(tgt, int(18 * self.dscale()), False, self.rect.centerx, 0, "shock", 1.2, self.pen)
            else:
                best = None
                for o in g.obs:
                    if not o.alive or not (o.solid_now() or o.plat_now()):
                        continue
                    if (o.rect.centerx - self.rect.centerx) * self.face > 0 and o.rect.centery < self.rect.centery + 40:
                        d2 = abs(o.rect.centerx - self.rect.centerx)
                        if d2 < 380 and (best is None or d2 < best[0]):
                            best = (d2, o)
                if best:
                    o = best[1]
                    self.grap = (o.rect.centerx, o.rect.top - 30)
                    self.grap_t = .45
                    g.fx.append(Fx("bolt", self.rect.centerx, self.rect.centery, .2, CYAN,
                                   r=o.rect.centerx, ang=o.rect.top))
        else:  # lance
            g.sfx.play("boom", .03)
            g.explode(self.rect.centerx + self.face * 60, self.rect.centery, 110,
                      int(40 * self.dscale()), "p", "void", VIOL)
            self.vx -= self.face * 220

    def add_combo(self, g, silent=False):
        self.combo += 1
        self.combo_t = 2.4
        r, ri = self.rank()
        if not silent and self.combo in (6, 14, 26, 42, 64, 95):
            g.texts.append(FText(self.rect.centerx, self.rect.y - 34, "RANK " + r, GOLD, 24, 1.0))

    # ---------- 技能 ----------
    def use_skill(self, g):
        self.skill_cd = self.skill_cd_base * self.skill_cd_mult
        k = self.ckey
        cx, cy = self.rect.center
        g.sfx.play("ult", .05)
        if k == "ecoli":
            self.iframe = max(self.iframe, .85)
            g.fx.append(Fx("ring", cx, cy, .5, self.color, r=200))
            g.shake = max(g.shake, 11)
            for e in g.targets():
                if (e.rect.centerx - cx) ** 2 + (e.rect.centery - cy) ** 2 < 190 * 190:
                    d, c = self.roll(36)
                    g.hurt_enemy(e, d, c, cx, 360, "stun", 2.0, self.pen)
            g.hit_obstacles(pygame.Rect(cx - 190, cy - 190, 380, 380), 40, cx)
        elif k == "yeast":
            self.buff_atk = 7.
            self.lifesteal = min(.9, self.lifesteal + .28)
            g.fx.append(Fx("ring", cx, cy, .6, AMB, r=140))
            g.zones.append(Zone(cx, self.rect.bottom, 150, 26, 7., 14 * self.elem_mult, "p",
                                (255, 150, 70), "burn"))
        elif k == "subtilis":
            self.iframe = max(self.iframe, 3.0)
            self.buff_spd = 3.0
            self.spore_t = 3.0
            g.fx.append(Fx("ring", cx, cy, .5, CYAN, r=150))
        elif k == "lacto":
            g.zones.append(Zone(cx, min(GROUND_Y, self.rect.bottom), 230, 40, 6.5,
                                22 * self.elem_mult, "p", (240, 110, 200), "corrode", True))
            g.fx.append(Fx("ring", cx, self.rect.bottom, .5, MAG, r=140))
        else:  # halo
            self.veil = 4.0
            self.reflect = True
            self.barrier = max(self.barrier, 26)
            g.fx.append(Fx("shock", cx, cy, .6, VIOL, r=150))

    # ---------- 終極 ----------
    def start_ult(self, g):
        self.ult_kind = self.weapon
        self.ult_t = 2.1 if self.weapon in ("blade", "whip") else 2.5
        self.ult_tick = 0.
        self.ult_n = 0
        self.ult = 0.
        self.iframe = max(self.iframe, self.ult_t + .25)
        g.flash = .65
        g.shake = 18
        g.slow = .7
        g.sfx.play("ult")
        g.banner(L(self.wdata(), "name"), 1.5, GOLD)

    def tick_ult(self, dt, g):
        self.ult_t -= dt
        self.ult_tick -= dt
        k = self.ult_kind
        cx, cy = self.rect.center
        if k == "blade":
            if self.ult_tick <= 0:
                self.ult_tick = .4
                g.fx.append(Fx("slash", LW * .5, LH * .45, .4, (140, 255, 220), ang=random.uniform(-.6, .6)))
                g.shake = max(g.shake, 12)
                g.flash = max(g.flash, .3)
                g.sfx.play("slash")
                for e in list(g.targets()):
                    g.hurt_enemy(e, int(66 + e.max_hp * .26), True, LW * .5, 110, "burn", 2., 1.)
        elif k == "saw":
            self.saw_spin += dt * 16
            if self.ult_tick <= 0:
                self.ult_tick = .11
                g.sfx.play("saw", .05)
                for e in list(g.targets()):
                    if (e.rect.centerx - cx) ** 2 + (e.rect.centery - cy) ** 2 < 140 * 140:
                        d, c = self.roll(20)
                        g.hurt_enemy(e, d, c, cx, 70, "bleed", .8, self.pen)
        elif k == "pipette":
            if self.ult_tick <= 0:
                self.ult_tick = .06
                g.sfx.play("shoot", .05)
                d, c = self.roll(22)
                g.add_proj(Proj(random.uniform(40, LW - 40), -26, random.uniform(-40, 40), 840, d, "p",
                                "acid", TOXIC, 8, 1.7, 2, elem="corrode", crit=c))
        elif k == "bow":
            if self.ult_tick <= 0:
                self.ult_tick = .28
                self.ult_n += 1
                y = 110 + ((self.ult_n * 79) % 320)
                g.fx.append(Fx("beamh", 0, y, .32, VIOL, w=24))
                g.sfx.play("zap", .05)
                for e in list(g.targets()):
                    if abs(e.rect.centery - y) < 42:
                        g.hurt_enemy(e, int(54 + e.max_hp * .12), True, e.rect.centerx - 1, 50, "shock", 1.2, 1.)
        elif k == "mortar":
            if self.ult_tick <= 0:
                self.ult_tick = .15
                x = random.uniform(50, LW - 50)
                g.explode(x, GROUND_Y - 18, 86, int(48 * self.dscale()), "p", "burn", (255, 160, 90))
                g.shake = max(g.shake, 9)
        elif k == "lance":
            if self.ult_tick <= 0:
                self.ult_tick = .34
                self.ult_n += 1
                x = 90 + ((self.ult_n * 137) % (LW - 180))
                g.fx.append(Fx("beamv", x, 0, .34, VIOL, w=30))
                g.sfx.play("ult", .1)
                col = pygame.Rect(x - 18, 0, 36, LH)
                for e in list(g.targets()):
                    if col.colliderect(e.rect):
                        g.hurt_enemy(e, int(60 + e.max_hp * .1), True, x, 40, "void", 1.6, 1.)
                g.hit_obstacles(col, 50, x)
        else:  # whip
            if self.ult_tick <= 0:
                self.ult_tick = .15
                tg = list(g.targets())
                if tg:
                    e = random.choice(tg)
                    g.fx.append(Fx("bolt", cx, cy, .2, CYAN, r=e.rect.centerx, ang=e.rect.centery))
                    g.sfx.play("zap", .04)
                    g.hurt_enemy(e, int(42 * self.dscale()), True, cx, 50, "shock", 1., 1.)
                    for o in tg:
                        if o is e:
                            continue
                        if (o.rect.centerx - e.rect.centerx) ** 2 + (o.rect.centery - e.rect.centery) ** 2 < 210 ** 2:
                            g.fx.append(Fx("bolt", e.rect.centerx, e.rect.centery, .18, CYAN,
                                           r=o.rect.centerx, ang=o.rect.centery))
                            g.hurt_enemy(o, int(26 * self.dscale()), False, e.rect.centerx, 20, "shock", .5, 1.)
        if self.ult_t <= 0:
            self.ult_t = 0.
            self.ult_kind = None

    # ---------- 受傷 ----------
    def hurt(self, dmg, g, from_x=None, src=None):
        if self.iframe > 0 or self.dead:
            return False
        fx = self.rect.centerx if from_x is None else from_x
        front = (fx - self.rect.centerx) * self.face >= 0
        if self.guarding and front:
            if self.parry > 0:
                self.energy = min(self.max_energy, self.energy + 34)
                self.gain_ult(14)
                self.gain_ovd(14)
                self.riposte = 1.6
                g.texts.append(FText(self.rect.centerx, self.rect.y - 26, T("parry"), CYAN, 24, .8))
                g.fx.append(Fx("ring", self.rect.centerx, self.rect.centery, .4, CYAN, r=110))
                g.shake = max(g.shake, 9)
                g.flash = max(g.flash, .22)
                g.slow = max(g.slow, .35)
                g.sfx.play("parry")
                for e in g.targets():
                    if abs(e.rect.centerx - self.rect.centerx) < 130:
                        e.stun = max(e.stun, .7)
                        e.stagger += e.stagger_max * .3
                        e.vx = sgn(e.rect.centerx - self.rect.centerx) * 280
                if self.parry_blast:
                    g.explode(self.rect.centerx, self.rect.centery, 140, int(36 * self.dscale()),
                              "p", "shock", CYAN)
            else:
                self.energy = max(0., self.energy - 10)
                g.sfx.play("hit")
            self.iframe = .22
            return True
        d = max(1, int(dmg) - int(self.armor * .34))
        if self.barrier > 0:
            a = min(self.barrier, d * 6)
            self.barrier -= a
            self.iframe = .3
            g.parts.burst(self.rect.centerx, self.rect.centery, ICE, 10, 200, 3, .3)
            g.sfx.play("guard")
            if self.barrier <= 0:
                g.fx.append(Fx("shock", self.rect.centerx, self.rect.centery, .3, ICE, r=80))
            return True
        self.hp -= d
        self.iframe = .8
        self.hit_flash = .28
        self.combo = 0
        self.riposte = 0.
        self.vx = -sgn(fx - self.rect.centerx) * 250
        self.vy = min(self.vy, -190)
        g.shake = max(g.shake, 9)
        g.flash = max(g.flash, .22)
        g.sfx.play("hurt")
        g.parts.burst(self.rect.centerx, self.rect.centery, RED, 16, 240, 4, .5, 450, True)
        g.texts.append(FText(self.rect.centerx, self.rect.y - 14, "-%d" % d, (255, 110, 110), 21, .7))
        if src is not None and self.thorns > 0 and hasattr(src, "take"):
            g.hurt_enemy(src, self.thorns, False, self.rect.centerx, 100)
        if self.hp <= 0:
            self.dead = True
        return True

    # ---------- 繪製 ----------
    def draw(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        bob = math.sin(self.t * 3.4) * 1.5
        step = math.sin(self.walk) * 6 if self.on_ground else 0
        col = self.color
        d1 = dk(col, .45)
        d2 = dk(col, .22)

        gy = GROUND_Y
        for o in self.g.obs:
            if o.alive and (o.plat_now() or o.solid_now()) and r.bottom <= o.rect.top + 4 and o.rect.left < cx < o.rect.right:
                gy = min(gy, o.rect.top)
        pt.shadow(cx, gy - 2, 40 - min(16, (gy - r.bottom) * .07), 110)
        for tr in self.trail:
            a = tr[2] / .24
            pt.glow((tr[0], tr[1]), 26 * a, col, .4 * a)
            pt.dia(dk(col, .5 * a), (tr[0], tr[1]), 12 * a, 18 * a, 1)
        pt.glow((cx, cy + bob), 34, col, .2 + .07 * math.sin(self.t * 4))

        # 斗篷（折角布）
        sway = math.sin(self.t * 2.6) * 5 - self.vx * .02
        pt.poly(d2, [(cx - self.face * 3, cy - 18 + bob), (cx - self.face * 20 + sway, cy + 2 + bob),
                     (cx - self.face * 24 + sway * 1.3, cy + 18 + bob),
                     (cx - self.face * 10 + sway, cy + 26 + bob), (cx + self.face * 2, cy + 8 + bob)])
        # 腿（稜角）
        for s in (-1, 1):
            lx = cx + s * 9
            off = step * s
            pt.poly(PLATE, [(lx - 5, cy + 14 + bob), (lx + 5, cy + 14 + bob),
                            (lx + 4, cy + 30 + bob), (lx - 4, cy + 30 + bob)])
            pt.poly(GREY, [(lx - 8, cy + 30 + bob + off * .25), (lx + 8, cy + 30 + bob + off * .25),
                           (lx + 6, cy + 37 + bob + off * .25), (lx - 9, cy + 37 + bob + off * .25)])
        # 軀幹
        body = [(cx - 17, cy - 14 + bob), (cx - 8, cy - 18 + bob), (cx + 8, cy - 18 + bob),
                (cx + 17, cy - 14 + bob), (cx + 14, cy + 16 + bob), (cx - 14, cy + 16 + bob)]
        pt.poly(d1, body)
        pt.poly(STEEL, [(p[0] * .88 + cx * .12, p[1] * .9 + (cy + bob) * .1) for p in body])
        pt.poly(dk(EDGE, 1.0), body, 2)
        pt.dia(col, (cx, cy + bob), 6, 8)
        pt.dia(WHT, (cx, cy + bob), 2.2, 3)
        pt.line(col, (cx - 12, cy + 8 + bob), (cx + 12, cy + 8 + bob), 2)
        # 肩甲
        for s in (-1, 1):
            pt.poly(PLATE, [(cx + s * 14, cy - 16 + bob), (cx + s * 25, cy - 12 + bob),
                            (cx + s * 22, cy - 2 + bob), (cx + s * 13, cy - 5 + bob)])
            pt.poly(dk(col, .8), [(cx + s * 14, cy - 16 + bob), (cx + s * 25, cy - 12 + bob),
                                  (cx + s * 22, cy - 2 + bob), (cx + s * 13, cy - 5 + bob)], 1)
        # 頭盔（稜角 + 視鏡條）
        hy = cy - 32 + bob
        pt.poly(PLATE, [(cx - 14, hy + 4), (cx - 9, hy - 6), (cx + 9, hy - 6), (cx + 14, hy + 4),
                        (cx + 11, hy + 17), (cx - 11, hy + 17)])
        pt.poly(dk(EDGE, 1.1), [(cx - 14, hy + 4), (cx - 9, hy - 6), (cx + 9, hy - 6), (cx + 14, hy + 4),
                                (cx + 11, hy + 17), (cx - 11, hy + 17)], 2)
        ex = cx + self.face * 2
        pt.poly(CYAN, [(ex - 9, hy + 5), (ex + 9, hy + 3), (ex + 9, hy + 9), (ex - 9, hy + 10)])
        pt.glow((ex, hy + 7), 13, CYAN, .55)
        pt.poly(RED, [(cx - 2, hy - 6), (cx + 2, hy - 6), (cx + 5, hy - 20), (cx - 1, hy - 14)])

        self.draw_weapon(pt, cx, cy + bob)

        # 防禦 / 彈反 / 屏障
        if self.guarding:
            sx = cx + self.face * 16
            a = .45 + .25 * math.sin(self.t * 12)
            pt.glow((sx, cy), 50, CYAN, a * .8)
            pts = [(sx + self.face * 10, cy - 30), (sx + self.face * 18, cy), (sx + self.face * 10, cy + 30),
                   (sx - self.face * 4, cy + 22), (sx - self.face * 4, cy - 22)]
            pt.poly((16, 36, 56), pts)
            pt.poly(CYAN, pts, 2)
            if self.parry > 0:
                pt.poly(WHT, pts, 3)
        if self.barrier > 0:
            f = clamp(self.barrier / max(1., self.barrier_max), 0, 1)
            pt.hexa(ICE, (cx, cy), 28, 34, 2)
            pt.glow((cx, cy), 40, ICE, .2 * f)
        if self.veil > 0:
            pt.ngon(VIOL, (cx, cy), 30, 36, 4, self.t * 2, 2)
        if self.riposte > 0:
            pt.text(T("riposte"), 13, GOLD, (cx, r.y - 30), "center", True, maxw=90)
        if self.buff_atk > 0:
            pt.dia(AMB, (cx, cy), 30, 36, 2)
        if self.spore_t > 0 or self.buff_spd > 0:
            pt.dia(CYAN, (cx, cy), 26, 32, 2)
        if self.ovd_t > 0:
            pt.hexa(GOLD, (cx, cy), 32 + 3 * math.sin(self.t * 10), 38, 2)
            pt.glow((cx, cy), 56, GOLD, .3)
        if self.ult_t > 0:
            pt.glow((cx, cy), 80, GOLD, .5)
            if self.ult_kind == "saw":
                for i in range(4):
                    a = self.saw_spin + i * (math.tau / 4)
                    sx, sy = cx + math.cos(a) * 118, cy + math.sin(a) * 118
                    pt.glow((sx, sy), 30, AMB, .7)
                    pt.ngon(PLATE, (sx, sy), 14, 14, 6, a)
                    pt.ngon(AMB, (sx, sy), 14, 14, 6, a, 2)
        if self.iframe > 0 and self.hit_flash <= 0 and int(self.t * 20) % 2 == 0:
            pt.hexa(WHT, (cx, cy), 26, 32, 1)
        self.draw_status(pt)

    # ----- 武器外觀 -----
    def draw_weapon(self, pt, cx, cy):
        f = self.face
        hand = (cx + f * 19, cy + 5)
        wk = self.weapon
        fn = {"blade": self._w_blade, "saw": self._w_saw, "pipette": self._w_pipe, "bow": self._w_bow,
              "mortar": self._w_mortar, "whip": self._w_whip, "lance": self._w_lance}.get(wk)
        if fn:
            fn(pt, hand, f)
        pt.poly(GREY, [(hand[0] - 5, hand[1] - 5), (hand[0] + 5, hand[1] - 5),
                       (hand[0] + 5, hand[1] + 5), (hand[0] - 5, hand[1] + 5)])

    def _swing_angle(self, base=-34., sweep=152.):
        if self.swing_t > 0 and self.swing_max > 0:
            p = 1. - self.swing_t / self.swing_max
            return math.radians(-118 + p * sweep)
        return math.radians(base + math.sin(self.t * 2.2) * 6)

    def _w_blade(self, pt, hand, f):
        ang = self._swing_angle()
        dx, dy = math.cos(ang) * f, math.sin(ang)
        bl = 66
        tx, ty = hand[0] + dx * bl, hand[1] + dy * bl
        pt.line((92, 76, 54), (hand[0] - dx * 15, hand[1] - dy * 15), hand, 6)
        pt.line(AMB, (hand[0] - dy * 12, hand[1] + dx * 12), (hand[0] + dy * 12, hand[1] - dx * 12), 5)
        pt.poly((224, 240, 255), [(hand[0] + dx * 10 - dy * 5, hand[1] + dy * 10 + dx * 5),
                                  (hand[0] + dx * 10 + dy * 5, hand[1] + dy * 10 - dx * 5),
                                  (tx + dy * 1.5, ty - dx * 1.5), (tx, ty), (tx - dy * 1.5, ty + dx * 1.5)])
        pt.line((96, 255, 210), (hand[0] + dx * 14, hand[1] + dy * 14), (tx, ty), 2)
        for i in range(5):
            t = i / 4.
            px = hand[0] + dx * (16 + t * bl * .8)
            py = hand[1] + dy * (16 + t * bl * .8)
            pt.glow((px, py), 13 - i * 1.6, (96, 255, 206), .42)
        pt.glow((tx, ty), 22, (120, 255, 214), .7)
        if self.swing_t > 0:
            p = 1. - self.swing_t / max(1e-3, self.swing_max)
            for i in range(6):
                aa = math.radians(-118) + (p * 152 - i * 14) * math.pi / 180
                if aa < math.radians(-118):
                    continue
                ex = hand[0] + math.cos(aa) * f * bl
                ey = hand[1] + math.sin(aa) * bl
                al = 1 - i / 6.
                pt.line((120, 255, 210), (hand[0], hand[1]), (ex, ey), 2 * al)

    def _w_saw(self, pt, hand, f):
        self.saw_spin += .5
        b = (hand[0] + f * 9, hand[1])
        pt.poly(dk(AMB, .55), [(b[0] - 14, b[1] - 12), (b[0] + 14, b[1] - 12),
                               (b[0] + 12, b[1] + 12), (b[0] - 14, b[1] + 12)])
        pt.poly(AMB, [(b[0] - 12, b[1] - 10), (b[0] + 11, b[1] - 10), (b[0] + 9, b[1] + 9), (b[0] - 12, b[1] + 9)])
        bar = b[0] + f * 14 if f > 0 else b[0] - 44 + f * 0
        pt.rect(PLATE, (bar if f > 0 else b[0] - 44, b[1] - 6, 44, 12))
        x0 = bar if f > 0 else b[0] - 44
        pt.rect(GREY, (x0, b[1] - 5, 44, 3))
        off = (self.saw_spin % 6)
        for i in range(9):
            tx = x0 + 3 + i * 5 + off
            if tx > x0 + 42:
                continue
            pt.tri((70, 74, 88), (tx, b[1] - 8), 4, 0)
            pt.tri((70, 74, 88), (tx, b[1] + 8), 4, 1)
        hf = self.heat / 100.
        if self.overheat > 0:
            pt.glow((x0 + 22, b[1]), 34, (255, 90, 40), .9)
        elif hf > .2:
            pt.glow((x0 + 22, b[1]), 22 * hf, (255, 150, 40), hf)

    def _w_pipe(self, pt, hand, f):
        b = (hand[0] + f * 7, hand[1])
        x0 = b[0] - 14 if f > 0 else b[0] - 18
        pt.poly((34, 74, 104), [(x0, b[1] - 8), (x0 + 30, b[1] - 8), (x0 + 32, b[1]), (x0 + 30, b[1] + 8), (x0, b[1] + 8)])
        pt.rect((116, 196, 240), (x0 + 3, b[1] - 5, 24, 5))
        tipx = b[0] + f * 20
        pt.poly((150, 220, 255), [(tipx, b[1] - 4), (tipx + f * 18, b[1]), (tipx, b[1] + 4)])
        n = max(0, min(6, int(self.ammo / max(1., self.max_ammo / 6.))))
        for i in range(6):
            c = CYAN if i < n else (44, 54, 70)
            pt.rect(c, (x0 + 4 + i * 4, b[1] + 3, 3, 3))
        if self.muzzle > 0:
            pt.glow((tipx + f * 18, b[1]), 30, (190, 240, 255), 1.)

    def _w_bow(self, pt, hand, f):
        cxx, cyy = hand[0] + f * 7, hand[1]
        R = 23
        top = (cxx + f * 4, cyy - R)
        bot = (cxx + f * 4, cyy + R)
        mid = (cxx + f * (R * .8), cyy)
        pt.poly(VIOL, [top, mid, bot, (cxx - f * 2, cyy)], 3)
        pull = self.charge * 13
        nock = (cxx - f * (3 + pull), cyy)
        pt.line((226, 226, 255), top, nock, 2)
        pt.line((226, 226, 255), nock, bot, 2)
        if self.charge > .05:
            pt.glow((cxx + f * 6, cyy), 10 + self.charge * 28, VIOL, .35 + self.charge * .6)
            pt.poly(WHT, [(nock[0], cyy - 2), (cxx + f * (18 + self.charge * 22), cyy),
                          (nock[0], cyy + 2)])
            if self.charge >= 1.:
                pt.hexa(WHT, (cxx, cyy), R + 6, R + 6, 2)

    def _w_mortar(self, pt, hand, f):
        b = (hand[0] + f * 5, hand[1] - 2)
        ang = -0.5 * f
        dx, dy = math.cos(ang) * f, math.sin(ang)
        Lg = 32
        ex, ey = b[0] + dx * Lg, b[1] + dy * Lg
        pt.line(PLATE, (b[0] - dx * 8, b[1] - dy * 8), (ex, ey), 15)
        pt.line(GREY, (b[0] - dx * 8, b[1] - dy * 8), (ex, ey), 7)
        pt.dia((190, 100, 90), (ex, ey), 7, 7)
        pt.poly(PLATE, [(b[0] - 10, b[1] + 2), (b[0] + 2, b[1] - 2), (b[0] + 4, b[1] + 10), (b[0] - 10, b[1] + 12)])
        for i in range(5):
            c = (255, 150, 120) if i < max(0, self.ammo) else (44, 48, 60)
            pt.rect(c, (b[0] - 10 + i * 4, b[1] + 13, 3, 4))
        if self.muzzle > 0:
            pt.glow((ex + dx * 12, ey + dy * 12), 30, (255, 170, 110), 1.)

    def _w_whip(self, pt, hand, f):
        pt.rect((30, 56, 70), (hand[0] - 5, hand[1] - 9, 10, 18))
        pt.rect(CYAN, (hand[0] - 3, hand[1] - 7, 6, 4))
        n = 9
        act = self.whip_t > 0
        prog = 0. if not act else 1. - self.whip_t / .22
        px, py = hand[0], hand[1]
        for i in range(1, n + 1):
            t = i / float(n)
            if act:
                reach = 132 * min(1., prog * 1.9)
                x = hand[0] + f * reach * t
                y = hand[1] + math.sin(t * 3.2 + prog * 6) * 13 * (1 - t)
            else:
                x = hand[0] + f * 32 * t
                y = hand[1] + 22 * t * t
            r = 5.0 - t * 3.2
            pt.line((70, 200, 226), (px, py), (x, y), max(1.4, r))
            pt.dia(CYAN, (x, y), r * .9, r * .9)
            px, py = x, y
        if act:
            pt.glow((px, py), 22, CYAN, .85)

    def _w_lance(self, pt, hand, f):
        b = (hand[0] + f * 6, hand[1] - 2)
        Lg = 58 + self.charge * 18
        tip = (b[0] + f * Lg, b[1])
        pt.line(PLATE, (b[0] - f * 14, b[1]), (b[0] + f * Lg * .7, b[1]), 8)
        pt.poly(VIOL, [(b[0] + f * Lg * .6, b[1] - 7), (tip[0], tip[1]), (b[0] + f * Lg * .6, b[1] + 7)])
        pt.poly(WHT, [(b[0] + f * Lg * .72, b[1] - 3), (tip[0], tip[1]), (b[0] + f * Lg * .72, b[1] + 3)])
        pt.hexa(VIOL, (b[0], b[1]), 9, 9, 2)
        if self.charge > .05:
            pt.glow(tip, 14 + self.charge * 34, VIOL, .4 + self.charge * .6)
            if self.charge >= 1:
                pt.ngon(WHT, tip, 12, 12, 4, self.t * 4, 2)
        if self.lance_t > 0:
            pt.glow(tip, 40, VIOL, 1.)


# ==============================================================================
#  敵人
# ==============================================================================
class Enemy(Unit):
    def __init__(self, kind, x, y, diff, g, elite=False):
        d = EN.get(kind, EN["paraben"])
        self.kind = kind
        self.g = g
        self.boss = False
        sc = 1.2 if elite else 1.0
        self.w = int(d["w"] * sc)
        self.h = int(d["h"] * sc)
        self.x, self.y = float(x), float(y)
        self.rect = pygame.Rect(int(x), int(y), self.w, self.h)
        self.init_common()
        af = g.affix
        hpm = 1.
        if af == "swarm":
            hpm = .8
        self.max_hp = max(4., d["hp"] * (1. + .17 * diff) * (2.3 if elite else 1.) * hpm * g.dmul())
        self.hp = self.max_hp
        self.hp_show = self.max_hp
        self.base_sp = d["sp"] * (1. + .03 * diff) * (.9 if elite else 1.)
        if af == "frenzy":
            self.base_sp *= 1.25
        self.armor = d["ar"] + (4 if elite else 0) + (6 if af == "hard" else 0) + int(diff * .35)
        self.dmg = d["dmg"] + (1 if elite else 0)
        self.score = int(d["sc"] * (2.4 if elite else 1.))
        self.xp = int(d["xp"] * (2.3 if elite else 1.))
        self.color = d["col"]
        self.elite = elite
        self.stagger_max = 28 + self.max_hp * .35
        if elite:
            self.mods = [random.choice(MODS)]
        if af == "volatile":
            self.mods.append("volatile")
        if af == "vamp":
            self.mods.append("leech")
        if af == "shield":
            self.shield_max = 20 + diff * 2
            self.shield = self.shield_max
        self.vx = self.vy = 0.
        self.face = 1
        self.t = random.uniform(0, 6)
        self.blink = random.uniform(1., 4.)
        self.shoot_cd = random.uniform(1.0, 2.6)
        self.charging = False
        self.charge_t = 0.
        self.hover = random.uniform(0, 6.3)
        self.dive = 0.
        self.jump_cd = random.uniform(.6, 2.2)
        self.fuse = 0.
        self.beam_t = 0.
        self.beam_state = 0
        self.spawn_cd = 3.0
        self.tp_cd = random.uniform(1.4, 3.0)
        self.mine_cd = random.uniform(1.6, 3.4)
        self.buff_cd = 2.0
        self.dash_cd = random.uniform(1.0, 2.6)
        self.dash_t = 0.
        if kind == "shielder":
            self.shield_max = max(self.shield_max, 34 + diff * 4)
            self.shield = self.shield_max
        if kind == "warden":
            self.shield_max = max(self.shield_max, 40 + diff * 5)
            self.shield = self.shield_max

    def speed(self):
        s = self.base_sp
        if "swift" in self.mods:
            s *= 1.35
        return s * self.slow_mult()

    def is_weak(self, from_x):
        if self.kind in ("metal", "shielder", "warden"):
            return (from_x - self.rect.centerx) * self.face < 0
        return (from_x - self.rect.centerx) * self.face < 0

    def blocks(self, from_x):
        if self.kind in ("shielder", "warden") and self.shield > 0:
            return (from_x - self.rect.centerx) * self.face > 0
        return False

    # ---- update ----
    def update(self, dt, g):
        self.t += dt
        self.tick_status(dt, g)
        self.blink -= dt
        if self.blink <= -.12:
            self.blink = random.uniform(1.6, 4.4)
        self.hp_show += (self.hp - self.hp_show) * min(1., dt * 9)
        if "regen" in self.mods and self.hp < self.max_hp:
            self.hp = min(self.max_hp, self.hp + self.max_hp * .035 * dt)
        if self.dash_t > 0:
            self.dash_t = max(0., self.dash_t - dt)

        p = g.player
        fly = self.kind in AIR
        if p is not None and not p.dead and self.acting():
            k = self.kind
            fn = getattr(self, "_ai_" + k, None)
            if fn is None:
                fn = self._ai_walk
            fn(dt, p, g)
        else:
            self.vx *= (1 - 3 * dt)
        if not fly:
            self.vy = min(1000., self.vy + 1700 * g.grav_mult() * dt)
        world_move(self, dt, g, fly, False)
        if p is not None and not p.dead and self.rect.colliderect(p.rect):
            p.hurt(self.dmg, g, self.rect.centerx, self)

    # ---- AI ----
    def _ai_walk(self, dt, p, g, mul=1.0):
        dx = p.rect.centerx - self.rect.centerx
        self.face = 1 if dx > 0 else -1
        self.vx += clamp(self.face * self.speed() * mul - self.vx, -900 * dt, 900 * dt)
        self.jump_cd -= dt
        if self.on_ground and self.jump_cd <= 0:
            self.jump_cd = random.uniform(1.0, 2.6)
            if p.rect.bottom < self.rect.top + 8 or abs(dx) < 90:
                self.vy = -580
                self.on_ground = False

    _ai_paraben = _ai_walk
    _ai_blob = _ai_walk
    _ai_blobmini = _ai_walk

    def _ai_shielder(self, dt, p, g):
        self._ai_walk(dt, p, g, .9)

    def _ai_warden(self, dt, p, g):
        self._ai_walk(dt, p, g, .8)
        self.shoot_cd -= dt
        if self.shoot_cd <= 0 and abs(p.rect.centerx - self.rect.centerx) < 340:
            self.shoot_cd = 2.6
            for i in (-1, 0, 1):
                a = math.atan2(p.rect.centery - self.rect.centery,
                               (p.rect.centerx - self.rect.centerx) or 1) + i * .2
                g.add_proj(Proj(self.rect.centerx, self.rect.centery, math.cos(a) * 300,
                                math.sin(a) * 300, self.dmg, "e", "shot", (170, 190, 220), 8, 3.))
            g.sfx.play("shoot", .12)

    def _ai_spore(self, dt, p, g):
        self.hover += dt * 3
        if self.dive > 0:
            self.dive -= dt
            tx, ty, mul = p.rect.centerx, p.rect.centery, 2.0
        else:
            tx = p.rect.centerx
            ty = p.rect.centery - 70 + math.sin(self.hover) * 24
            mul = 1.0
            if abs(tx - self.rect.centerx) < 150 and random.random() < .9 * dt:
                self.dive = .6
        dx, dy = tx - self.rect.centerx, ty - self.rect.centery
        d = max(1., math.hypot(dx, dy))
        sp = self.speed() * mul
        self.vx += clamp(dx / d * sp - self.vx, -700 * dt, 700 * dt)
        self.vy += clamp(dy / d * sp - self.vy, -700 * dt, 700 * dt)
        self.face = 1 if self.vx > 0 else -1

    def _ai_phage(self, dt, p, g):
        dx = p.rect.centerx - self.rect.centerx
        self.face = 1 if dx > 0 else -1
        want = 240.
        if abs(dx) > want + 40:
            self.vx += clamp(self.face * self.speed() - self.vx, -700 * dt, 700 * dt)
        elif abs(dx) < want - 50:
            self.vx += clamp(-self.face * self.speed() - self.vx, -700 * dt, 700 * dt)
        else:
            self.vx *= (1 - 3 * dt)
        self.shoot_cd -= dt
        self.charging = self.shoot_cd < .5
        if self.shoot_cd <= 0:
            self.charging = False
            self.shoot_cd = random.uniform(1.6, 2.8)
            a0 = math.atan2(p.rect.centery - self.rect.centery, dx if dx != 0 else 1)
            hm = 90 if g.affix == "hunt" else 0
            for i in ((-1, 0, 1) if self.elite else (0,)):
                a = a0 + i * .15
                g.add_proj(Proj(self.rect.centerx, self.rect.centery, math.cos(a) * 340,
                                math.sin(a) * 340, self.dmg, "e", "acid", TOXIC, 8, 3.,
                                homing=hm, elem="corrode"))
            g.sfx.play("shoot", .09)

    def _ai_metal(self, dt, p, g):
        dx = p.rect.centerx - self.rect.centerx
        self.face = 1 if dx > 0 else -1
        if self.charging:
            self.charge_t -= dt
            self.vx *= (1 - 5 * dt)
            if self.charge_t <= 0:
                self.charging = False
                self.vx = self.face * 560
                self.shoot_cd = 2.4
                g.sfx.play("boom", .2)
        else:
            self.shoot_cd -= dt
            if abs(dx) < 290 and self.shoot_cd <= 0 and self.on_ground:
                self.charging = True
                self.charge_t = .7
            else:
                self.vx += clamp(self.face * self.speed() - self.vx, -450 * dt, 450 * dt)

    def _ai_bomber(self, dt, p, g):
        dx = p.rect.centerx - self.rect.centerx
        self.face = 1 if dx > 0 else -1
        self.vx += clamp(self.face * self.speed() - self.vx, -1100 * dt, 1100 * dt)
        self.jump_cd -= dt
        if self.on_ground and self.jump_cd <= 0 and abs(dx) < 150:
            self.jump_cd = 1.2
            self.vy = -540
        d2 = (p.rect.centerx - self.rect.centerx) ** 2 + (p.rect.centery - self.rect.centery) ** 2
        if self.fuse > 0 or d2 < 78 ** 2:
            if self.fuse <= 0:
                self.fuse = .72
            self.fuse -= dt
            if self.fuse <= 0:
                self.hp = 0
                g.explode(self.rect.centerx, self.rect.centery, 100, 22, "e", "burn", (255, 150, 80))

    def _ai_cryo(self, dt, p, g):
        dx = p.rect.centerx - self.rect.centerx
        self.face = 1 if dx > 0 else -1
        if abs(dx) > 300:
            self.vx += clamp(self.face * self.speed() - self.vx, -600 * dt, 600 * dt)
        else:
            self.vx *= (1 - 2.4 * dt)
        self.shoot_cd -= dt
        self.charging = self.shoot_cd < .45
        if self.shoot_cd <= 0:
            self.shoot_cd = random.uniform(1.9, 3.1)
            self.charging = False
            a = math.atan2(p.rect.centery - self.rect.centery, dx if dx != 0 else 1)
            g.add_proj(Proj(self.rect.centerx, self.rect.centery, math.cos(a) * 270, math.sin(a) * 270,
                            self.dmg, "e", "ice", ICE, 9, 3.2, elem="chill"))
            g.sfx.play("shoot", .1)

    def _ai_drone(self, dt, p, g):
        tx, ty = p.rect.centerx, 118 + math.sin(self.t * 1.4) * 26
        dx, dy = tx - self.rect.centerx, ty - self.rect.centery
        d = max(1., math.hypot(dx, dy))
        sp = self.speed()
        self.vx += clamp(dx / d * sp - self.vx, -600 * dt, 600 * dt)
        self.vy += clamp(dy / d * sp - self.vy, -600 * dt, 600 * dt)
        self.face = 1 if self.vx > 0 else -1
        self.beam_t -= dt
        if self.beam_state == 0:
            if self.beam_t <= 0 and abs(dx) < 60:
                self.beam_state = 1
                self.beam_t = .75
                g.fx.append(Fx("warn", self.rect.centerx, self.rect.bottom, .75, RED, w=24))
        elif self.beam_state == 1:
            if self.beam_t <= 0:
                self.beam_state = 2
                self.beam_t = .5
                g.sfx.play("zap", .1)
        else:
            if abs(p.rect.centerx - self.rect.centerx) < 22 and p.rect.bottom > self.rect.bottom:
                p.hurt(self.dmg, g, self.rect.centerx, self)
            if self.beam_t <= 0:
                self.beam_state = 0
                self.beam_t = random.uniform(2.0, 3.2)

    def _ai_mother(self, dt, p, g):
        ty = 148 + math.sin(self.t * .9) * 30
        dx = p.rect.centerx - self.rect.centerx
        self.face = 1 if dx > 0 else -1
        self.vx += clamp(sgn(dx) * self.speed() * .5 - self.vx, -300 * dt, 300 * dt)
        self.vy += clamp((ty - self.rect.centery) * 1.4 - self.vy, -300 * dt, 300 * dt)
        self.spawn_cd -= dt
        if self.spawn_cd <= 0:
            self.spawn_cd = 3.4
            for _ in range(2):
                if len(g.enemies) < 28:
                    g.enemies.append(Enemy("spore", self.rect.centerx + random.uniform(-20, 20),
                                           self.rect.bottom, g.diff() * .5, g))
            g.sfx.play("level", .2)

    def _ai_lancer(self, dt, p, g):
        dx = p.rect.centerx - self.rect.centerx
        self.face = 1 if dx > 0 else -1
        self.dash_cd -= dt
        if self.dash_t > 0:
            return
        if self.dash_cd <= 0 and abs(dx) < 340:
            self.dash_cd = 2.2
            self.dash_t = .34
            self.vx = self.face * 720
            g.sfx.play("dash", .1)
            g.parts.cone(self.rect.centerx, self.rect.centery, math.pi if self.face > 0 else 0, .4,
                         self.color, 8, 200, 3, .3)
        else:
            self.vx += clamp(self.face * self.speed() * .7 - self.vx, -600 * dt, 600 * dt)
        self.jump_cd -= dt
        if self.on_ground and self.jump_cd <= 0 and p.rect.bottom < self.rect.top:
            self.jump_cd = 1.6
            self.vy = -600

    def _ai_turret(self, dt, p, g):
        self.vx *= (1 - 5 * dt)
        self.face = 1 if p.rect.centerx > self.rect.centerx else -1
        self.shoot_cd -= dt
        self.charging = self.shoot_cd < .6
        if self.shoot_cd <= 0:
            self.shoot_cd = 1.9
            a0 = math.atan2(p.rect.centery - self.rect.centery,
                            (p.rect.centerx - self.rect.centerx) or 1)
            for i in range(3):
                g.add_proj(Proj(self.rect.centerx, self.rect.centery - 6,
                                math.cos(a0) * (320 + i * 40), math.sin(a0) * (320 + i * 40),
                                self.dmg, "e", "shot", (200, 210, 235), 7, 2.6))
            g.sfx.play("shoot", .1)

    def _ai_wraith(self, dt, p, g):
        self.tp_cd -= dt
        if self.tp_cd <= 0:
            self.tp_cd = random.uniform(2.0, 3.6)
            g.fx.append(Fx("ring", self.rect.centerx, self.rect.centery, .3, VIOL, r=70))
            self.x = clamp(p.rect.centerx + random.choice([-130, 130]), 20, LW - self.w - 20)
            self.y = clamp(p.rect.centery - 30, 20, GROUND_Y - self.h - 10)
            self.rect.topleft = (int(self.x), int(self.y))
            g.fx.append(Fx("ring", self.rect.centerx, self.rect.centery, .3, VIOL, r=70))
            g.sfx.play("zap", .1)
            a = math.atan2(p.rect.centery - self.rect.centery,
                           (p.rect.centerx - self.rect.centerx) or 1)
            g.add_proj(Proj(self.rect.centerx, self.rect.centery, math.cos(a) * 380, math.sin(a) * 380,
                            self.dmg, "e", "void", VIOL, 8, 2.6, elem="void"))
        dx, dy = p.rect.centerx - self.rect.centerx, p.rect.centery - 40 - self.rect.centery
        d = max(1., math.hypot(dx, dy))
        self.vx += clamp(dx / d * self.speed() * .6 - self.vx, -400 * dt, 400 * dt)
        self.vy += clamp(dy / d * self.speed() * .6 - self.vy, -400 * dt, 400 * dt)
        self.face = 1 if dx > 0 else -1

    def _ai_sapper(self, dt, p, g):
        dx = p.rect.centerx - self.rect.centerx
        self.face = 1 if dx > 0 else -1
        if abs(dx) < 220:
            self.vx += clamp(-self.face * self.speed() - self.vx, -700 * dt, 700 * dt)
        else:
            self.vx += clamp(self.face * self.speed() * .6 - self.vx, -500 * dt, 500 * dt)
        self.mine_cd -= dt
        if self.mine_cd <= 0 and self.on_ground:
            self.mine_cd = random.uniform(2.2, 3.6)
            g.add_proj(Proj(self.rect.centerx, self.rect.centery, self.face * 120, -240, self.dmg, "e",
                            "mine", (235, 205, 90), 8, 8., 0, grav=760., elem="burn", expl=74., bounce=1))
            g.sfx.play("shoot", .12)
        self.jump_cd -= dt
        if self.on_ground and self.jump_cd <= 0:
            self.jump_cd = 2.0
            self.vy = -520

    def _ai_hexer(self, dt, p, g):
        ty = 200 + math.sin(self.t) * 40
        dx = p.rect.centerx - self.rect.centerx
        self.face = 1 if dx > 0 else -1
        want = 300.
        self.vx += clamp((-sgn(dx) if abs(dx) < want else sgn(dx)) * self.speed() * .6 - self.vx,
                         -400 * dt, 400 * dt)
        self.vy += clamp((ty - self.rect.centery) * 1.2 - self.vy, -300 * dt, 300 * dt)
        self.buff_cd -= dt
        if self.buff_cd <= 0:
            self.buff_cd = 3.0
            n = 0
            for e in g.enemies:
                if e is self or n >= 3:
                    continue
                if abs(e.rect.centerx - self.rect.centerx) < 220:
                    if e.shield_max <= 0:
                        e.shield_max = 22
                    e.shield = min(e.shield_max, e.shield + 14)
                    e.st.add("hexed", 3.0, 1.0)
                    g.fx.append(Fx("bolt", self.rect.centerx, self.rect.centery, .2, TOXIC,
                                   r=e.rect.centerx, ang=e.rect.centery))
                    n += 1
            g.sfx.play("level", .2)

    def _ai_reaper(self, dt, p, g):
        dx = p.rect.centerx - self.rect.centerx
        dy = p.rect.centery - self.rect.centery
        self.face = 1 if dx > 0 else -1
        self.vx += clamp(self.face * self.speed() - self.vx, -1200 * dt, 1200 * dt)
        self.jump_cd -= dt
        if self.on_ground and self.jump_cd <= 0 and (dy < -20 or abs(dx) < 120):
            self.jump_cd = .9
            self.vy = -640

    # ---- 繪製 ----
    def draw(self, pt, g):
        r = self.rect
        cx, cy = r.centerx, r.centery
        an = g.anim_enemy()
        if an is not None:
            w, h = self.w * 1.5, self.h * 1.5
            s = an.get(self.t, int(w * pt.k), int(h * pt.k), self.face < 0)
            if s is not None:
                pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w)
                pt.s.blit(s, pt.P((cx - w * .5, cy - h * .5)))
                self._extra(pt)
                self.draw_status(pt)
                self.draw_bars(pt)
                return
        fn = getattr(self, "_d_" + self.kind, None)
        if fn is None:
            fn = self._d_paraben
        fn(pt)
        self._extra(pt)
        self.draw_status(pt)
        self.draw_bars(pt)

    def _extra(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        if self.elite:
            c = {"armored": (206, 214, 232), "swift": CYAN, "regen": LIME, "volatile": AMB,
                 "leech": MAG, "warded": VIOL}.get(self.mods[0] if self.mods else "armored", GOLD)
            pt.hexa(c, (cx, cy), self.w * .78 + 2 * math.sin(self.t * 5), self.h * .72, 2)
        if self.shield > 0 and self.shield_max > 0:
            f = self.shield / max(1., self.shield_max)
            if self.kind in ("shielder", "warden"):
                sx = cx + self.face * (self.w * .5 + 8)
                pts = [(sx + self.face * 6, cy - self.h * .45), (sx + self.face * 12, cy),
                       (sx + self.face * 6, cy + self.h * .45), (sx - self.face * 3, cy + self.h * .34),
                       (sx - self.face * 3, cy - self.h * .34)]
                pt.poly((18, 40, 62), pts)
                pt.poly(ICE, pts, 2)
                pt.glow((sx, cy), 30, ICE, .25 + .25 * f)
            else:
                pt.hexa(ICE, (cx, cy), self.w * .66, self.h * .66, 2)
        if self.kind == "drone" and self.beam_state == 2:
            pt.rect((255, 235, 235), (cx - 8, self.rect.bottom, 16, LH - self.rect.bottom))
            pt.rect(WHT, (cx - 3, self.rect.bottom, 6, LH - self.rect.bottom))
            pt.glow((cx, self.rect.bottom + 40), 44, RED, .6)

    def _eyes(self, pt, cx, cy, sz=1., c=None):
        c = c or (255, 240, 240)
        ex = cx + self.face * 3 * sz
        if self.blink < 0:
            pt.line((30, 18, 18), (ex - 8 * sz, cy), (ex + 8 * sz, cy), 2 * sz)
            return
        for s in (-1, 1):
            pt.poly(c, [(ex + s * 6 * sz - 4 * sz, cy - 2 * sz), (ex + s * 6 * sz + 4 * sz, cy - 3 * sz),
                        (ex + s * 6 * sz + 3 * sz, cy + 2 * sz), (ex + s * 6 * sz - 3 * sz, cy + 2 * sz)])
        pt.glow((ex, cy), 10 * sz, c, .3)

    # --- 個別外觀（皆為稜角幾何） ---
    def _d_paraben(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        walk = math.sin(self.t * 9) * 5 if (self.on_ground and abs(self.vx) > 10) else 0
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w * .9)
        for s in (-1, 1):
            lx = cx + s * self.w * .22
            pt.line(dk(c, .5), (lx, cy + self.h * .25), (lx + walk * s, cy + self.h * .5), 4)
        body = [(cx - self.w * .42, cy - self.h * .3), (cx, cy - self.h * .48),
                (cx + self.w * .42, cy - self.h * .3), (cx + self.w * .34, cy + self.h * .32),
                (cx - self.w * .34, cy + self.h * .32)]
        pt.poly(dk(c, .5), body)
        pt.poly(c, [(p[0] * .86 + cx * .14, p[1] * .88 + cy * .12) for p in body])
        pt.poly(dk(c, .25), body, 2)
        for i in range(5):
            a = -2.4 + i * 1.2 + math.sin(self.t * 2) * .2
            pt.tri(dk(c, .7), (cx + math.cos(a) * self.w * .5, cy + math.sin(a) * self.h * .44), 5, 0)
        self._eyes(pt, cx, cy - 2)

    def _d_spore(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        flap = math.sin(self.t * 18)
        pt.glow((cx, cy), self.w * 1.1, c, .3 + (.25 if self.dive > 0 else 0))
        for s in (-1, 1):
            pt.poly(dk(c, .7), [(cx, cy - 2), (cx + s * self.w * .9, cy - 12 + flap * 11),
                                (cx + s * self.w * .5, cy + 8)])
        pt.ngon(dk(c, .5), (cx, cy), self.w * .48, self.h * .48, 4, math.pi / 4)
        pt.ngon(c, (cx, cy), self.w * .34, self.h * .34, 4, math.pi / 4)
        for j in range(3):
            pt.line(dk(c, .8), (cx, cy + 8), (cx + (j - 1) * 8, cy + 8 + 14 + math.sin(self.t * 8 + j) * 3), 2)
        self._eyes(pt, cx, cy, .7)
        if self.dive > 0:
            pt.dia(WHT, (cx, cy), self.w * .6, self.h * .6, 2)

    def _d_phage(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w * .9)
        for i in range(6):
            a = math.pi * (.15 + i * .14)
            lx = cx + math.cos(a) * self.w * .44
            k = math.sin(self.t * 7 + i) * 4
            pt.line(dk(c, .6), (lx, cy + self.h * .14), (lx + k, cy + self.h * .5), 2)
        pt.hexa(dk(c, .5), (cx, cy - 4), self.w * .47, self.h * .44, 0, math.pi / 6)
        pt.hexa(c, (cx, cy - 4), self.w * .36, self.h * .34, 0, math.pi / 6)
        pt.hexa(dk(c, .25), (cx, cy - 4), self.w * .47, self.h * .44, 2, math.pi / 6)
        self._eyes(pt, cx, cy - 5, .8)
        if self.charging:
            f = clamp(1 - self.shoot_cd / .5, 0, 1)
            pt.glow((cx + self.face * self.w * .45, cy), 12 + 22 * f, TOXIC, .5 + .5 * f)

    def _d_metal(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w)
        step = math.sin(self.t * 6) * 6 if abs(self.vx) > 10 else 0
        for s in (-1, 1):
            lx = cx + s * self.w * .24
            pt.rect(dk(c, .5), (lx - 6, cy + self.h * .18, 12, self.h * .3))
            pt.rect(dk(c, .75), (lx - 8 + step * s * .4, cy + self.h * .44, 16, 6))
        bx = [(cx - self.w * .46, cy - self.h * .28), (cx - self.w * .3, cy - self.h * .46),
              (cx + self.w * .3, cy - self.h * .46), (cx + self.w * .46, cy - self.h * .28),
              (cx + self.w * .38, cy + self.h * .26), (cx - self.w * .38, cy + self.h * .26)]
        pt.poly(dk(c, .45), bx)
        pt.poly(c, [(p[0] * .9 + cx * .1, p[1] * .9 + cy * .1) for p in bx])
        pt.poly((36, 26, 10), bx, 2)
        px = cx + self.face * (self.w * .4)
        pt.rect((210, 216, 232), (px - 7, cy - self.h * .34, 14, self.h * .66))
        pt.rect((58, 62, 74), (px - 7, cy - self.h * .34, 14, self.h * .66), 2)
        self._eyes(pt, cx, cy - 4, 1.1)
        if self.charging:
            f = clamp(1 - self.charge_t / .7, 0, 1)
            pt.glow((cx, cy), self.w * (.7 + f * .6), (255, 120, 40), .5 + .5 * f)

    def _d_blob(self, pt, small=False):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        wob = math.sin(self.t * 6) * .12
        rx, ry = self.w * .5 * (1 + wob), self.h * .5 * (1 - wob)
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w * .9)
        pt.glow((cx, cy), self.w * .6, c, .2)
        pt.ngon(dk(c, .5), (cx, cy), rx, ry, 5, math.pi / 2)
        pt.ngon(c, (cx, cy), rx * .8, ry * .8, 5, math.pi / 2)
        self._eyes(pt, cx, cy, .7 if not small else .5)

    def _d_blobmini(self, pt):
        self._d_blob(pt, True)

    def _d_bomber(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        fz = 0. if self.fuse <= 0 else 1. - self.fuse / .72
        pulse = 1. + fz * .25 * abs(math.sin(self.t * (12 + fz * 26)))
        rr = self.w * .48 * pulse
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w * .9)
        if self.fuse > 0:
            pt.glow((cx, cy), self.w * (.9 + fz), (255, 120, 60), .4 + fz * .6)
        pt.dia(dk(c, .5), (cx, cy), rr, rr * 1.05)
        pt.dia(c, (cx, cy), rr * .74, rr * .8)
        pt.line((90, 70, 50), (cx, cy - rr), (cx + 5, cy - rr - 9), 2)
        pt.sq((255, 230, 120) if int(self.t * 12) % 2 == 0 else (110, 84, 40), (cx + 5, cy - rr - 11), 2.4)
        self._eyes(pt, cx, cy, .7)

    def _d_shielder(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w * .9)
        step = math.sin(self.t * 6) * 5 if abs(self.vx) > 10 else 0
        for s in (-1, 1):
            lx = cx + s * self.w * .2
            pt.line(dk(c, .55), (lx, cy + self.h * .24), (lx + step * s, cy + self.h * .48), 4)
        pts = [(cx - self.w * .36, cy - self.h * .3), (cx, cy - self.h * .44),
               (cx + self.w * .36, cy - self.h * .3), (cx + self.w * .3, cy + self.h * .28),
               (cx - self.w * .3, cy + self.h * .28)]
        pt.poly(dk(c, .5), pts)
        pt.poly(c, [(p[0] * .88 + cx * .12, p[1] * .9 + cy * .1) for p in pts])
        pt.poly((18, 30, 48), pts, 2)
        self._eyes(pt, cx, cy - 4, .8)

    def _d_cryo(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w * .85)
        pt.glow((cx, cy), self.w * .7, ICE, .25)
        for i in range(6):
            a = self.t * .8 + i * math.tau / 6
            ex, ey = cx + math.cos(a) * self.w * .5, cy + math.sin(a) * self.h * .5
            pt.line(ICE, (cx, cy), (ex, ey), 3)
            pt.dia((235, 250, 255), (ex, ey), 3.4, 3.4)
        pt.ngon(dk(c, .6), (cx, cy), self.w * .3, self.h * .3, 4, self.t)
        pt.ngon(c, (cx, cy), self.w * .2, self.h * .2, 4, -self.t)
        self._eyes(pt, cx, cy, .6, ICE)
        if self.charging:
            pt.glow((cx + self.face * self.w * .4, cy), 20, ICE, .8)

    def _d_drone(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        rot = self.t * 22
        pt.glow((cx, cy), self.w * .8, (180, 200, 255), .22)
        for s in (-1, 1):
            ax = cx + s * self.w * .42
            pt.line(dk(c, .6), (cx + s * 8, cy - 2), (ax, cy - 8), 3)
            pt.sq(dk(c, .8), (ax, cy - 8), 4)
            bl = 12 + 4 * math.sin(rot + s)
            pt.line((210, 220, 245), (ax - bl, cy - 8), (ax + bl, cy - 8), 2)
        pt.poly(dk(c, .55), [(cx - self.w * .3, cy - self.h * .3), (cx + self.w * .3, cy - self.h * .3),
                             (cx + self.w * .22, cy + self.h * .34), (cx - self.w * .22, cy + self.h * .34)])
        pt.rect(c, (cx - self.w * .2, cy - self.h * .2, self.w * .4, self.h * .26))
        ec = RED if self.beam_state else CYAN
        pt.glow((cx, cy + self.h * .24), 14, ec, .8)
        pt.dia(ec, (cx, cy + self.h * .24), 4.4, 4.4)

    def _d_mother(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        pulse = 1 + .07 * math.sin(self.t * 3)
        rx, ry = self.w * .5 * pulse, self.h * .5 * pulse
        pt.glow((cx, cy), self.w, c, .3)
        for i in range(6):
            a = self.t * 1.2 + i * math.tau / 6
            px, py = cx, cy + ry * .6
            for j in range(1, 4):
                nx = cx + math.cos(a + j * .25) * j * 10
                ny = cy + ry * .6 + j * 9
                pt.line(dk(c, .7), (px, py), (nx, ny), 3.2 - j * .5)
                px, py = nx, ny
            pt.dia(c, (px, py), 3, 3)
        pt.ngon(dk(c, .5), (cx, cy), rx, ry, 6, math.pi / 6)
        pt.ngon(c, (cx, cy), rx * .78, ry * .78, 6, math.pi / 6)
        for i in range(4):
            a = self.t * .7 + i * 1.57
            pt.dia(WHT, (cx + math.cos(a) * rx * .3, cy + math.sin(a) * ry * .3), 4, 4)
        if self.spawn_cd < .6:
            pt.glow((cx, cy + ry * .5), 26, WHT, .7)

    def _d_lancer(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        f = self.face
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w * .85)
        pt.poly(dk(c, .5), [(cx - f * self.w * .3, cy - self.h * .34), (cx + f * self.w * .34, cy - self.h * .1),
                            (cx + f * self.w * .3, cy + self.h * .3), (cx - f * self.w * .34, cy + self.h * .22)])
        pt.poly(c, [(cx - f * self.w * .22, cy - self.h * .26), (cx + f * self.w * .26, cy - self.h * .06),
                    (cx + f * self.w * .22, cy + self.h * .22), (cx - f * self.w * .26, cy + self.h * .14)])
        pt.line(WHT, (cx, cy), (cx + f * self.w * 1.05, cy - 4), 3)
        pt.tri(WHT, (cx + f * self.w * 1.1, cy - 4), 6, 3 if f > 0 else 2)
        self._eyes(pt, cx, cy - 6, .7, RED)
        if self.dash_t > 0:
            pt.glow((cx, cy), 32, RED, .6)

    def _d_turret(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w)
        pt.poly(dk(c, .45), [(cx - self.w * .48, cy + self.h * .4), (cx - self.w * .3, cy - self.h * .1),
                             (cx + self.w * .3, cy - self.h * .1), (cx + self.w * .48, cy + self.h * .4)])
        pt.poly(c, [(cx - self.w * .26, cy - self.h * .34), (cx + self.w * .26, cy - self.h * .34),
                    (cx + self.w * .2, cy - self.h * .02), (cx - self.w * .2, cy - self.h * .02)])
        f = self.face
        pt.rect((80, 88, 108), (cx if f > 0 else cx - self.w * .5, cy - self.h * .22, self.w * .5, 8))
        pt.dia(RED if self.charging else dk(RED, .5), (cx + f * self.w * .5, cy - self.h * .18), 5, 5)
        if self.charging:
            pt.glow((cx + f * self.w * .5, cy - self.h * .18), 22, RED, .8)

    def _d_warden(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w)
        for s in (-1, 1):
            pt.rect(dk(c, .5), (cx + s * self.w * .26 - 7, cy + self.h * .18, 14, self.h * .3))
        pts = [(cx - self.w * .42, cy - self.h * .26), (cx - self.w * .22, cy - self.h * .46),
               (cx + self.w * .22, cy - self.h * .46), (cx + self.w * .42, cy - self.h * .26),
               (cx + self.w * .34, cy + self.h * .22), (cx - self.w * .34, cy + self.h * .22)]
        pt.poly(dk(c, .45), pts)
        pt.poly(c, [(p[0] * .9 + cx * .1, p[1] * .9 + cy * .1) for p in pts])
        pt.poly((20, 24, 32), pts, 2)
        for i in range(3):
            pt.rect((200, 210, 228), (cx - 18 + i * 13, cy - self.h * .36, 9, self.h * .32))
        pt.poly(CYAN, [(cx - 12, cy - 2), (cx + 12, cy - 4), (cx + 12, cy + 3), (cx - 12, cy + 5)])
        pt.glow((cx, cy), 18, CYAN, .4)

    def _d_wraith(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        a = .5 + .3 * math.sin(self.t * 4)
        pt.glow((cx, cy), self.w * .9, VIOL, .3 * a)
        pts = [(cx, cy - self.h * .5), (cx + self.w * .38, cy - self.h * .1),
               (cx + self.w * .2, cy + self.h * .46), (cx - self.w * .2, cy + self.h * .46),
               (cx - self.w * .38, cy - self.h * .1)]
        pt.poly(dk(c, .4), pts)
        pt.poly(c, [(p[0] * .82 + cx * .18, p[1] * .82 + cy * .18) for p in pts], 2)
        for i in range(3):
            yy = cy + self.h * .3 + i * 6
            pt.line(dk(VIOL, .6), (cx - self.w * .2 + i * 4, yy), (cx + self.w * .2 - i * 4, yy), 1)
        self._eyes(pt, cx, cy - 6, .7, VIOL)

    def _d_sapper(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w * .85)
        pt.poly(dk(c, .5), [(cx - self.w * .4, cy + self.h * .3), (cx - self.w * .26, cy - self.h * .3),
                            (cx + self.w * .26, cy - self.h * .3), (cx + self.w * .4, cy + self.h * .3)])
        pt.poly(c, [(cx - self.w * .28, cy + self.h * .2), (cx - self.w * .18, cy - self.h * .2),
                    (cx + self.w * .18, cy - self.h * .2), (cx + self.w * .28, cy + self.h * .2)])
        for i in range(3):
            pt.dia(AMB if self.mine_cd > 1 else RED, (cx - 8 + i * 8, cy + self.h * .34), 3, 3)
        self._eyes(pt, cx, cy - 4, .7, AMB)

    def _d_hexer(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        pt.glow((cx, cy), self.w * .9, TOXIC, .26)
        pt.ngon(dk(c, .45), (cx, cy), self.w * .48, self.h * .46, 3, -math.pi / 2)
        pt.ngon(c, (cx, cy), self.w * .34, self.h * .32, 3, math.pi / 2)
        for i in range(3):
            a = self.t * 2 + i * 2.09
            pt.dia(TOXIC, (cx + math.cos(a) * self.w * .6, cy + math.sin(a) * self.h * .5), 4, 5)
        self._eyes(pt, cx, cy, .6, TOXIC)
        if self.buff_cd < .5:
            pt.hexa(TOXIC, (cx, cy), self.w * .8, self.h * .8, 2)

    def _d_reaper(self, pt):
        r = self.rect
        cx, cy = r.centerx, r.centery
        c = self.color if self.hit_flash <= 0 else WHT
        f = self.face
        pt.shadow(cx, min(GROUND_Y, r.bottom) - 1, self.w * .85)
        pts = [(cx - f * self.w * .3, cy - self.h * .44), (cx + f * self.w * .3, cy - self.h * .3),
               (cx + f * self.w * .22, cy + self.h * .4), (cx - f * self.w * .3, cy + self.h * .3)]
        pt.poly(dk(c, .42), pts)
        pt.poly(c, [(p[0] * .86 + cx * .14, p[1] * .88 + cy * .12) for p in pts])
        # 鐮刃
        pt.line(WHT, (cx + f * 6, cy - self.h * .3), (cx + f * self.w * .9, cy - self.h * .1), 3)
        pt.poly((235, 240, 255), [(cx + f * self.w * .9, cy - self.h * .1),
                                  (cx + f * self.w * 1.25, cy - self.h * .34),
                                  (cx + f * self.w * 1.0, cy + self.h * .06)])
        self._eyes(pt, cx, cy - 8, .7, RED)
        pt.glow((cx, cy), 24, RED, .22)


# ==============================================================================
#  首領
# ==============================================================================
class Boss(Unit):
    def __init__(self, btype, power, g, dmul=1.0):
        d = BOSSES.get(btype, BOSSES["necro"])
        self.btype = btype
        self.g = g
        self.boss = True
        self.kind = "boss"
        self.power = power
        self.name = L(d, "name")
        self.color = d["col"]
        if btype == "necro":
            self.w, self.h = 152, 92
            self.fly = True
            self.x, self.y = LW * .5 - self.w * .5, 120.
        elif btype == "monarch":
            self.w, self.h = 126, 116
            self.fly = False
            self.x, self.y = LW * .5 - self.w * .5, GROUND_Y - 116
        elif btype == "colossus":
            self.w, self.h = 158, 106
            self.fly = False
            self.x, self.y = LW * .5 - self.w * .5, GROUND_Y - 106
        else:  # mitosis
            self.w, self.h = 128, 104
            self.fly = True
            self.x, self.y = LW * .5 - self.w * .5, 150.
        self.rect = pygame.Rect(int(self.x), int(self.y), self.w, self.h)
        self.init_common()
        self.max_hp = (d["hp"] + power * 220) * dmul
        self.hp = self.max_hp
        self.hp_show = self.max_hp
        self.armor = 4 + power
        self.stagger_max = 130 + power * 40
        self.score = 950 + power * 360
        self.xp = 72 + power * 30
        self.dmg = 2
        self.elite = True
        self.plate = 3
        self.vx = self.vy = 0.
        self.face = -1
        self.t = 0.
        self.phase = 1
        self.state = "intro"
        self.state_t = 1.8
        self.atk_cd = 2.2
        self.tx, self.ty = LW * .5, 140.
        self.jaw = 0.
        self.wing = 0.
        self.beam_ang = 0.
        self.beam_dir = 1
        self.beam_on = False
        self.dive_x = LW * .5
        self.roll_dir = 1
        self.core = 0.

    def pcol(self):
        if self.phase == 1:
            return self.color
        if self.phase == 2:
            return mix(self.color, MAG, .4)
        return GOLD

    def armor_now(self):
        a = Unit.armor_now(self)
        if self.btype == "colossus" and self.plate > 0:
            a += 5 * self.plate
        return a

    def is_weak(self, from_x):
        return self.core > 0

    def head(self):
        if self.btype == "necro":
            return (self.rect.centerx + self.face * 64, self.rect.centery - 12)
        if self.btype == "monarch":
            return (self.rect.centerx, self.rect.y + 26)
        if self.btype == "mitosis":
            return (self.rect.centerx, self.rect.centery)
        return (self.rect.centerx + self.face * 56, self.rect.centery - 18)

    def take(self, dmg, g, from_x=0., knock=0., pen=0.0, stag=1.0):
        if self.state == "intro":
            return 0
        d = Unit.take(self, dmg, g, from_x, knock * .18, pen, stag * .55)
        if self.btype == "colossus" and self.plate > 0 and self.hp < self.max_hp * (self.plate / 4.0):
            self.plate -= 1
            g.parts.burst(self.rect.centerx, self.rect.centery, (206, 216, 196), 22, 260, 5, .6, 400, True)
            g.sfx.play("brk", .05)
            g.texts.append(FText(self.rect.centerx, self.rect.y, "ARMOR -", AMB, 20, .8))
        return d

    # ---- update ----
    def update(self, dt, g):
        self.t += dt
        self.wing += dt * (7 + self.phase)
        self.tick_status(dt, g)
        self.hp_show += (self.hp - self.hp_show) * min(1., dt * 6)
        self.jaw = max(0., self.jaw - dt * 2.4)
        if self.core > 0:
            self.core = max(0., self.core - dt)

        f = self.hp / max(1., self.max_hp)
        ph = 3 if f < .32 else (2 if f < .66 else 1)
        if ph != self.phase:
            self.phase = ph
            g.shake = max(g.shake, 18)
            g.flash = max(g.flash, .5)
            g.sfx.play("boom")
            g.fx.append(Fx("ring", self.rect.centerx, self.rect.centery, .7, self.pcol(), r=300))
            g.banner(T("phase", ph), 1.2, self.pcol())
            self.core = 3.0

        p = g.player
        self.state_t -= dt
        if self.state == "intro":
            if self.state_t <= 0:
                self.state = "move"
                self.state_t = 1.2
        elif self.state == "move":
            self._move(dt, p)
            if self.acting():
                self.atk_cd -= dt
                if self.atk_cd <= 0 and p is not None and not p.dead:
                    self._attack(g, p)
        elif self.state == "beam":
            self.beam_ang += self.beam_dir * dt * .85
            self.beam_on = self.state_t < 1.6
            if self.beam_on and p is not None:
                hx, hy = self.head()
                dx, dy = p.rect.centerx - hx, p.rect.centery - hy
                if math.hypot(dx, dy) > 8:
                    da = abs((math.atan2(dy, dx) - self.beam_ang + math.pi) % math.tau - math.pi)
                    if da < .1:
                        p.hurt(1, g, hx, self)
            if self.state_t <= 0:
                self.state = "move"
                self.state_t = 1.
                self.beam_on = False
                self.atk_cd = max(.8, 2.2 - .3 * self.phase)
        elif self.state == "dive":
            if self.state_t > .85:
                self.x = lerp(self.x, self.dive_x, min(1, dt * 3))
                self.y = lerp(self.y, 110, min(1, dt * 3))
            else:
                self.y += 1500 * dt
                if self.y + self.h >= GROUND_Y - 8:
                    self.y = GROUND_Y - 8 - self.h
                    self._slam(g, p)
                    self.state = "recover"
                    self.state_t = 1.0
                    self.core = 1.6
        elif self.state == "roll":
            self.vx = self.roll_dir * 440
            self.x += self.vx * dt
            if self.x < 20 or self.x > LW - self.w - 20 or self.state_t <= 0:
                self.state = "recover"
                self.state_t = .9
                self.core = 1.4
                g.shake = max(g.shake, 12)
            if p is not None and self.rect.colliderect(p.rect):
                p.hurt(2, g, self.rect.centerx, self)
        elif self.state == "recover":
            if self.fly:
                self.y = lerp(self.y, 140, min(1, dt * 2.2))
            if self.state_t <= 0:
                self.state = "move"
                self.state_t = 1.2
                self.atk_cd = max(.7, 2.0 - .3 * self.phase)

        self.x = clamp(self.x, 20, LW - self.w - 20)
        if self.fly:
            self.y = clamp(self.y, 40, GROUND_Y - self.h - 10)
        else:
            self.y = GROUND_Y - self.h
        self.rect.topleft = (int(self.x), int(self.y))
        if p is not None and not p.dead and self.state != "intro" and self.rect.colliderect(p.rect):
            p.hurt(1, g, self.rect.centerx, self)

    def _move(self, dt, p):
        if self.fly:
            dx, dy = self.tx - self.x, self.ty - self.y
            sp = 64 + 24 * self.phase
            d = max(1., math.hypot(dx, dy))
            self.x += dx / d * sp * dt
            self.y += dy / d * sp * dt
            if d < 20 or self.state_t <= 0:
                self.tx = random.uniform(70, LW - self.w - 70)
                self.ty = random.uniform(70, 250)
                self.state_t = 1.6
        elif p is not None:
            self.x += sgn(p.rect.centerx - self.rect.centerx) * (48 + 13 * self.phase) * dt
        if p is not None:
            self.face = 1 if p.rect.centerx > self.rect.centerx else -1

    def _slam(self, g, p):
        g.shake = max(g.shake, 22)
        g.sfx.play("boom")
        g.fx.append(Fx("ring", self.rect.centerx, GROUND_Y - 8, .55, AMB, r=280))
        g.parts.burst(self.rect.centerx, GROUND_Y - 6, (255, 170, 80), 30, 320, 6, .7, 700, True)
        g.hit_obstacles(pygame.Rect(self.rect.centerx - 200, GROUND_Y - 60, 400, 70), 40, self.rect.centerx)
        if p is not None and abs(p.rect.centerx - self.rect.centerx) < 210 and p.on_ground:
            p.hurt(1, g, self.rect.centerx, self)

    def _attack(self, g, p):
        self.atk_cd = max(.72, 2.4 - .32 * self.phase)
        hx, hy = self.head()
        self.jaw = 1.
        if self.btype == "necro":
            opts = ["volley", "spread"]
            if self.phase >= 2:
                opts += ["beam", "dive"]
            if self.phase >= 3:
                opts += ["summon", "beam", "spread"]
        elif self.btype == "monarch":
            opts = ["rain", "stomp"]
            if self.phase >= 2:
                opts += ["spread", "summon"]
            if self.phase >= 3:
                opts += ["beam", "rain", "mines"]
        elif self.btype == "colossus":
            opts = ["tide", "stomp"]
            if self.phase >= 2:
                opts += ["roll", "summon"]
            if self.phase >= 3:
                opts += ["spikes", "roll"]
        else:
            opts = ["voidnova", "clone"]
            if self.phase >= 2:
                opts += ["beam", "mines"]
            if self.phase >= 3:
                opts += ["voidnova", "summon", "spread"]
        a = random.choice(opts)
        hm = 70 if self.phase >= 3 else 0
        if a == "volley":
            n = 3 + self.phase
            for i in range(n):
                ang = math.atan2(p.rect.centery - hy, p.rect.centerx - hx) + (i - n / 2.) * .09
                g.add_proj(Proj(hx, hy, math.cos(ang) * 340, math.sin(ang) * 340, 1, "e", "fire",
                                (255, 150, 60), 13, 3.2, homing=hm, elem="burn"))
            g.sfx.play("shoot", .1)
        elif a == "spread":
            n = 9 + self.phase * 2
            for i in range(n):
                ang = math.tau * i / n
                g.add_proj(Proj(hx, hy, math.cos(ang) * 250, math.sin(ang) * 250, 1, "e", "fire",
                                (255, 190, 90), 10, 2.8, elem="burn"))
            g.sfx.play("boom", .1)
        elif a == "beam":
            self.state = "beam"
            self.state_t = 2.4
            self.beam_ang = math.atan2(p.rect.centery - hy, p.rect.centerx - hx) - .5
            self.beam_dir = 1 if random.random() < .5 else -1
            g.sfx.play("alarm")
        elif a == "dive":
            self.state = "dive"
            self.state_t = 1.5
            self.dive_x = clamp(p.rect.centerx - self.w * .5, 30, LW - self.w - 30)
        elif a == "rain":
            for i in range(6 + self.phase * 2):
                g.add_proj(Proj(random.uniform(40, LW - 40), -30 - i * 18, 0,
                                340 + random.uniform(0, 80), 1, "e", "drop", (240, 240, 255), 8, 4.))
            g.sfx.play("zap", .1)
        elif a == "stomp":
            self._slam(g, p)
            for s in (-1, 1):
                for i in range(4):
                    g.add_proj(Proj(self.rect.centerx + s * 30, GROUND_Y - 16, s * (210 + i * 60),
                                    -40, 1, "e", "fire", (255, 200, 120), 11, 2.4, elem="burn"))
        elif a == "tide":
            for i in range(5):
                g.zones.append(Zone(clamp(self.rect.centerx + (i - 2) * 96, 30, LW - 30), GROUND_Y,
                                    80, 34, 4.0, 16, "e", (150, 220, 100), "corrode", True))
            g.sfx.play("boom", .12)
        elif a == "roll":
            self.state = "roll"
            self.state_t = 1.7
            self.roll_dir = 1 if p.rect.centerx > self.rect.centerx else -1
            g.sfx.play("dash")
        elif a == "spikes":
            for i in range(5):
                x = clamp(p.rect.centerx + (i - 2) * 66, 20, LW - 20)
                g.fx.append(Fx("warn", x, GROUND_Y - 80, .55, LIME, w=18))
                g.zones.append(Zone(x, GROUND_Y, 40, 46, 1.4, 28, "e", (190, 250, 130)))
        elif a == "mines":
            for i in range(4):
                g.add_proj(Proj(hx, hy, random.uniform(-280, 280), -300, 1, "e", "mine",
                                (235, 205, 90), 9, 8., 0, grav=800., elem="burn", expl=80., bounce=1))
            g.sfx.play("shoot", .1)
        elif a == "voidnova":
            for ring in range(2):
                n = 10 + self.phase * 2
                for i in range(n):
                    ang = math.tau * i / n + ring * .3
                    g.add_proj(Proj(hx, hy, math.cos(ang) * (180 + ring * 120),
                                    math.sin(ang) * (180 + ring * 120), 1, "e", "void", VIOL, 9, 3.,
                                    elem="void"))
            g.sfx.play("ult", .1)
        elif a == "clone":
            for s in (-1, 1):
                if len(g.enemies) < 26:
                    e = Enemy("wraith", clamp(self.rect.centerx + s * 120, 20, LW - 60),
                              self.rect.centery, g.diff() * .7, g, True)
                    g.enemies.append(e)
            g.sfx.play("zap", .1)
        else:  # summon
            kinds = {"necro": "spore", "monarch": "phage", "colossus": "blob", "mitosis": "wraith"}
            for i in range(2 + self.phase):
                if len(g.enemies) < 26:
                    g.enemies.append(Enemy(kinds.get(self.btype, "spore"),
                                           clamp(self.rect.centerx + random.uniform(-120, 120), 20, LW - 60),
                                           self.rect.bottom - 20, g.diff() * .55, g))
            g.sfx.play("level", .15)

    # ---- 繪製 ----
    def draw(self, pt, g):
        cx, cy = self.rect.center
        col = self.pcol() if self.hit_flash <= 0 else WHT
        pt.glow((cx, cy), self.w * .8, col, .35)
        an = g.anim_boss()
        if an is not None:
            w, h = self.w * 1.55, self.h * 1.55
            s = an.get(self.t, int(w * pt.k), int(h * pt.k), self.face > 0)
            if s is not None:
                pt.s.blit(s, pt.P((cx - w * .5, cy - h * .5)))
                self._beam(pt)
                self.draw_status(pt)
                return
        fn = {"necro": self._d_necro, "monarch": self._d_monarch,
              "colossus": self._d_colossus, "mitosis": self._d_mitosis}[self.btype]
        fn(pt, cx, cy, col)
        self._beam(pt)
        if self.core > 0:
            hx, hy = self.head()
            pt.hexa(MAG, (hx, hy), 18 + 3 * math.sin(self.t * 12), 18, 2)
            pt.text(T("weak"), 13, MAG, (hx, hy - 30), "center", True, maxw=80)
        self.draw_status(pt)

    def _beam(self, pt):
        if not self.beam_on:
            return
        hx, hy = self.head()
        ex = hx + math.cos(self.beam_ang) * 1200
        ey = hy + math.sin(self.beam_ang) * 1200
        pt.line((255, 110, 60), (hx, hy), (ex, ey), 20)
        pt.line((255, 200, 120), (hx, hy), (ex, ey), 10)
        pt.line(WHT, (hx, hy), (ex, ey), 4)
        pt.glow((hx, hy), 54, (255, 170, 80), .85)

    def _d_necro(self, pt, cx, cy, col):
        f = self.face
        flap = math.sin(self.wing)
        d1 = dk(col, .5)
        for s in (1, -1):
            base = (cx - f * 10, cy - 10)
            pts = [base, (base[0] - f * 124, base[1] - 50 + flap * 42 * s),
                   (base[0] - f * 84, base[1] + 6 + flap * 20 * s),
                   (base[0] - f * 96, base[1] + 34 + flap * 12 * s)]
            pt.poly(d1, pts)
            pt.poly((24, 14, 20), pts, 2)
        tx, ty = cx - f * 56, cy + 12
        for i in range(7):
            nx = tx - f * (i * 17)
            ny = ty + i * 5 + math.sin(self.t * 3 - i * .5) * 8
            rr = 14 - i * 1.7
            pt.dia(d1, (nx, ny), rr, rr)
            pt.tri(col, (nx, ny - rr), 5, 0)
        body = [(cx - 48, cy - 6), (cx - 26, cy - 34), (cx + 28, cy - 32), (cx + 48, cy - 2),
                (cx + 26, cy + 32), (cx - 30, cy + 30)]
        pt.poly(d1, body)
        pt.poly(col, [(p[0] * .88 + cx * .12, p[1] * .88 + cy * .12) for p in body])
        pt.poly((22, 12, 16), body, 2)
        for i in range(5):
            pt.tri((246, 238, 226), (cx - 28 + i * 15, cy - 34), 8, 0)
        hx, hy = self.head()
        for i in range(4):
            t = (i + 1) / 4.
            nx = lerp(cx + f * 24, hx, t)
            ny = lerp(cy - 16, hy, t)
            pt.dia(d1, (nx, ny), 15 - i * 2, 14 - i * 2)
        pt.poly(d1, [(hx - f * 20, hy - 16), (hx + f * 16, hy - 12), (hx + f * 26, hy + 4),
                     (hx - f * 6, hy + 14), (hx - f * 22, hy + 4)])
        jaw = self.jaw * 11
        pt.poly(col, [(hx + f * 10, hy - 4), (hx + f * 46, hy - 6 - jaw * .3), (hx + f * 12, hy + 3)])
        pt.poly(dk(col, .6), [(hx + f * 10, hy + 5), (hx + f * 44, hy + 10 + jaw), (hx + f * 12, hy + 13)])
        for s in (-1, 1):
            pt.poly((240, 234, 224), [(hx - f * 8, hy - 14 + s * 4), (hx - f * 30, hy - 34 + s * 12),
                                      (hx - f * 6, hy - 6 + s * 6)])
        pt.glow((hx + f * 8, hy - 8), 16, (255, 230, 120), .85)
        pt.dia((255, 235, 120), (hx + f * 8, hy - 8), 5, 4)
        if self.jaw > .3:
            pt.glow((hx + f * 42, hy + 4), 24 * self.jaw, (255, 160, 60), self.jaw)

    def _d_monarch(self, pt, cx, cy, col):
        f = self.face
        pt.shadow(cx, GROUND_Y - 2, self.w * 1.1)
        for i in range(6):
            a = math.pi * (.12 + i * .15)
            lx = cx + math.cos(a) * self.w * .42
            k = math.sin(self.t * 4 + i) * 6
            mid = (lx + k, cy + self.h * .3)
            foot = (lx + k * .4, GROUND_Y - 2)
            pt.line(dk(col, .5), (lx, cy - 6), mid, 5)
            pt.line(dk(col, .75), mid, foot, 4)
            pt.tri(dk(col, .6), foot, 5, 1)
        pts = []
        for i in range(6):
            a = -math.pi / 2 + i * math.tau / 6 + .07 * math.sin(self.t)
            pts.append((cx + math.cos(a) * self.w * .44, cy - 22 + math.sin(a) * self.h * .38))
        pt.poly(dk(col, .45), pts)
        pt.poly(col, [(cx + (p[0] - cx) * .82, (cy - 22) + (p[1] - (cy - 22)) * .82) for p in pts])
        pt.poly((10, 44, 52), pts, 3)
        for p in pts:
            pt.line(dk(col, .6), (cx, cy - 22), p, 1)
        pt.rect(dk(col, .5), (cx - 12, cy - 6, 24, self.h * .34))
        hx, hy = self.head()
        pt.glow((hx, hy), 28, (255, 240, 180), .6)
        pt.dia((250, 250, 230), (hx, hy), 11, 11)
        pt.dia((16, 56, 66), (hx + f * 3, hy), 5, 5)
        for s in (-1, 1):
            pt.line(dk(col, .8), (cx + s * 10, cy - 46), (cx + s * 28, cy - 74), 3)
            pt.tri(WHT, (cx + s * 28, cy - 74), 5, 0)

    def _d_colossus(self, pt, cx, cy, col):
        f = self.face
        pt.shadow(cx, GROUND_Y - 2, self.w * 1.05)
        wob = math.sin(self.t * 2.4) * .05
        rx, ry = self.w * .5 * (1 + wob), self.h * .5 * (1 - wob)
        for i in range(5):
            a = self.t * 1.3 + i * 1.25
            pt.dia(dk(col, .7), (cx + math.cos(a) * rx * .8, cy + ry * .64 + math.sin(a) * 6), 8, 8)
        pt.ngon(dk(col, .45), (cx, cy), rx, ry, 6, 0)
        pt.ngon(col, (cx, cy), rx * .84, ry * .84, 6, 0)
        for i in range(self.plate):
            px = cx + (i - 1) * rx * .56 + f * 6
            pt.poly((206, 214, 196), [(px - 15, cy - ry * .84), (px + 15, cy - ry * .84),
                                      (px + 12, cy - ry * .2), (px - 12, cy - ry * .2)])
            pt.poly((60, 70, 58), [(px - 15, cy - ry * .84), (px + 15, cy - ry * .84),
                                   (px + 12, cy - ry * .2), (px - 12, cy - ry * .2)], 2)
        hx, hy = self.head()
        pt.ngon(dk(col, .6), (hx, hy), 24, 22, 5, math.pi / 2)
        pt.ngon(col, (hx, hy), 18, 17, 5, math.pi / 2)
        for i in range(3):
            ex = hx + math.cos(self.t * .8 + i * 2.1) * 9
            ey = hy + math.sin(self.t * .8 + i * 2.1) * 7
            pt.dia((250, 255, 230), (ex, ey), 5, 5)
        jaw = self.jaw * 10
        pt.poly(dk(col, .5), [(hx + f * 10, hy + 6), (hx + f * 36, hy + 10 + jaw), (hx + f * 12, hy + 17)])
        for i in range(6):
            a = -2.2 + i * .45
            pt.tri((230, 240, 210), (cx + math.cos(a) * rx * 1.05, cy + math.sin(a) * ry * 1.05), 7, 0)

    def _d_mitosis(self, pt, cx, cy, col):
        split = 14 + 10 * math.sin(self.t * 1.6)
        for s in (-1, 1):
            ox = cx + s * split
            pts = [(ox, cy - self.h * .48), (ox + s * self.w * .42, cy - self.h * .12),
                   (ox + s * self.w * .3, cy + self.h * .42), (ox - s * self.w * .06, cy + self.h * .34)]
            pt.poly(dk(col, .45), pts)
            pt.poly(col, [(p[0] * .86 + ox * .14, p[1] * .88 + cy * .12) for p in pts])
            pt.poly((30, 12, 46), pts, 2)
            pt.dia(WHT, (ox + s * 10, cy - 6), 5, 7)
        pt.glow((cx, cy), 46, VIOL, .5)
        pt.ngon(VIOL, (cx, cy), 20, 22, 4, self.t * 1.4, 2)
        pt.ngon(WHT, (cx, cy), 8, 9, 4, -self.t * 2)
        for i in range(4):
            a = self.t * 2 + i * 1.57
            pt.line(dk(VIOL, .8), (cx, cy), (cx + math.cos(a) * 40, cy + math.sin(a) * 34), 2)


# ==============================================================================
#  觸控
# ==============================================================================
class Touch:
    def __init__(self):
        self.btn = {
            "attack": (868, 448, 42),
            "altfire": (900, 372, 30),
            "jump": (766, 468, 33),
            "dash": (782, 396, 29),
            "skill": (830, 336, 28),
            "ult": (760, 320, 27),
            "ovd": (902, 300, 25),
            "guard": (660, 424, 29),
            "swap": (676, 348, 22),
        }
        self.lab = {"attack": "ATK", "altfire": "ALT", "jump": "JMP", "dash": "DSH", "skill": "SKL",
                    "ult": "ULT", "ovd": "OVD", "guard": "DEF", "swap": "WPN"}
        self.col = {"attack": (255, 120, 108), "altfire": MAG, "jump": LIME, "dash": CYAN,
                    "skill": TOXIC, "ult": GOLD, "ovd": AMB, "guard": ICE, "swap": VIOL}
        self.down = {}
        self.org = None
        self.pos = None
        self.fid = None
        self.R = 66

    def reset(self):
        self.down.clear()
        self.org = None
        self.pos = None
        self.fid = None

    def zone(self, lp):
        for n, (cx, cy, r) in self.btn.items():
            if (lp[0] - cx) ** 2 + (lp[1] - cy) ** 2 <= (r * 1.3) ** 2:
                return n
        if lp[0] < LW * .44 and lp[1] > LH * .34:
            return "joy"
        return None

    def press(self, z, fid, lp):
        if z == "joy":
            self.org = (clamp(lp[0], 80, LW * .4), clamp(lp[1], LH * .42, LH - 56))
            self.pos = lp
            self.fid = fid
        else:
            self.down[z] = fid

    def move(self, fid, lp):
        if self.fid == fid:
            self.pos = lp

    def up(self, fid):
        if self.fid == fid:
            self.fid = None
            self.org = None
            self.pos = None
        for n, f in list(self.down.items()):
            if f == fid:
                self.down.pop(n, None)

    def axis(self):
        if self.org is None or self.pos is None:
            return (0., 0.)
        dx = self.pos[0] - self.org[0]
        dy = self.pos[1] - self.org[1]
        d = math.hypot(dx, dy)
        if d < 1e-4:
            return (0., 0.)
        s = min(1., d / self.R)
        return (dx / d * s, dy / d * s)

    def draw(self, pt):
        base = self.org if self.org else (130, LH - 104)
        pt.hexa((18, 24, 36), base, self.R, self.R * .9)
        pt.hexa((90, 130, 180), base, self.R, self.R * .9, 2)
        ax, ay = self.axis()
        kx, ky = base[0] + ax * self.R * .76, base[1] + ay * self.R * .76
        pt.glow((kx, ky), 26, CYAN, .4)
        pt.dia((130, 190, 240), (kx, ky), 22, 22)
        pt.dia((22, 32, 48), (kx, ky), 22, 22, 2)
        for n, (cx, cy, r) in self.btn.items():
            c = self.col.get(n, WHT)
            pt.hexa((16, 20, 30), (cx, cy), r, r * .92)
            if n in self.down:
                pt.glow((cx, cy), r * 1.7, c, .65)
            pt.hexa(c, (cx, cy), r, r * .92, 2)
            pt.text(self.lab[n], r * .55, c, (cx, cy), "center", True, maxw=r * 1.6)


# ==============================================================================
#  設定存檔
# ==============================================================================
DEFAULT = {"lang": "en", "quality": ("low" if IS_ANDROID else "high"), "touch": IS_ANDROID,
           "vol": .6, "full": IS_ANDROID, "fps": False, "sprites": True, "shake": True, "best": {}}


CFG_KEY = "microbe_wars_void"


def load_cfg():
    c = dict(DEFAULT)
    try:
        if IS_WEB:
            raw = platform.window.localStorage.getItem(CFG_KEY)
            d = json.loads(raw) if raw else {}
        else:
            with open(CFG_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
        if isinstance(d, dict):
            for k in DEFAULT:
                if k in d:
                    c[k] = d[k]
    except Exception:
        pass
    if c.get("quality") not in QLIST:
        c["quality"] = "high"
    if not isinstance(c.get("best"), dict):
        c["best"] = {}
    try:
        c["vol"] = float(clamp(float(c.get("vol", .6)), 0, 1))
    except Exception:
        c["vol"] = .6
    return c


def save_cfg(c):
    try:
        if IS_WEB:
            platform.window.localStorage.setItem(CFG_KEY, json.dumps(c, ensure_ascii=False))
            return
        with open(CFG_PATH, "w", encoding="utf-8") as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


# ==============================================================================
#  主程式
# ==============================================================================
MODES = ("campaign", "endless", "bossrush", "time", "chaos", "practice")


class Game:
    def __init__(self):
        global LANG
        pygame.init()
        try:
            pygame.font.init()
        except Exception:
            pass
        self.cfg = load_cfg()
        self.fonts = FontMgr()
        LANG = self.cfg.get("lang", "zh")
        if not self.fonts.cjk:
            LANG = "en"
            self.cfg["lang"] = "en"
        self.disp = Display(self.cfg)
        self.pt = Painter(self.fonts)
        self.sfx = Sfx(self.cfg)
        self.clock = pygame.time.Clock()
        self.bg = Starfield()
        self.a1 = load_anim("1")
        self.a2 = load_anim("2")
        self.asset_note = T("asset_on") if (self.a1 or self.a2) else T("asset_off")

        self.state = "menu"
        self.prev = "menu"
        self.sel = 0
        self.btns = []
        self.inp = {}
        self.fing = {}
        self.touch = Touch()
        self.swap_latch = False

        self.c_i = 0
        self.w_i = 0
        self.d_i = 1
        self.mode = "campaign"

        self.player = None
        self.preview = None
        self.enemies = []
        self.projs = []
        self.zones = []
        self.pickups = []
        self.texts = []
        self.fx = []
        self.debris = []
        self.parts = Parts()
        self.boss = None
        self.obs = []
        self.affix = "none"

        self.shake = 0.
        self.flash = 0.
        self.slow = 0.
        self.ban = ""
        self.ban_t = 0.
        self.ban_c = GOLD
        self.cards = []
        self.result = None
        self.menu_t = 0.
        self.fps = 0.
        self.toast = ""
        self.toast_t = 0.

        self.stage = 1
        self.wave = 0
        self.kills = 0
        self.score = 0
        self.level = 1
        self.xp = 0
        self.xp_need = 28
        self.pending = 0
        self.rt = 0.
        self.tleft = 0.
        self.quota = 0
        self.spawned = 0
        self.gap = 1.
        self.stimer = 0.
        self.alive_cap = 10
        self.brk = 0.
        self.addt = 6.
        self.bqueue = []
        self.static_t = 0.
        self.obs = build_level(0)
        self.new_preview()

    # ---------- misc ----------
    def anim_enemy(self):
        return self.a1 if (self.cfg.get("sprites") and self.a1) else None

    def anim_boss(self):
        return self.a2 if (self.cfg.get("sprites") and self.a2) else None

    def tc(self):
        return bool(self.cfg.get("touch"))

    def go(self, s):
        if s != "settings" and self.state in ("menu", "pause"):
            self.prev = self.state
        self.state = s
        self.sel = 0
        self.btns = []

    def banner(self, s, life=1.5, c=GOLD):
        if s:
            self.ban = str(s)
            self.ban_t = life
            self.ban_c = c

    def say(self, s, life=2.6):
        self.toast = str(s)
        self.toast_t = life

    def targets(self):
        if self.boss is not None and self.boss.state != "intro":
            return self.enemies + [self.boss]
        return list(self.enemies)

    def dmul(self):
        return (.72, 1.0, 1.3, 1.62, 2.0)[int(clamp(self.d_i, 0, 4))]

    def grav_mult(self):
        return .78 if self.affix == "lowg" else 1.0

    def progress(self):
        if self.mode == "campaign":
            return (self.stage - 1) * 3 + self.wave
        if self.mode in ("endless", "chaos"):
            return self.wave
        if self.mode == "bossrush":
            return 9
        if self.mode == "time":
            return 2 + int(self.rt / 17.)
        return 7

    def diff(self):
        return self.progress() * .8 * self.dmul()

    def new_preview(self):
        try:
            self.preview = Player(CHARS[self.c_i], WEAPONS[self.w_i]["key"], self)
        except Exception:
            self.preview = None

    def add_proj(self, p):
        if len(self.projs) > 320:
            self.projs.pop(0)
        self.projs.append(p)

    def hit_obstacles(self, rect, dmg, from_x=None):
        for o in self.obs:
            if o.alive and o.maxhp > 0 and rect.colliderect(o.rect):
                o.damage(dmg, self, from_x)

    # ---------- loop ----------
    async def run(self):
        while True:
            # 讓出控制權給瀏覽器 / yield to the browser once per frame (required by pygbag)
            await asyncio.sleep(0)
            ms = self.clock.tick(FPS_CAP)
            dt = min(.05, ms / 1000.)
            self.fps = self.clock.get_fps()
            if self.disp.auto_tune(ms):
                self.pt.clear_cache()
                self.bg.invalidate()
            self.sfx.tick(dt)
            try:
                self.events()
                self.read_input()
                self.update(dt)
            except SystemExit:
                raise
            except Exception:
                self.crash()
            try:
                self.draw()
            except SystemExit:
                raise
            except Exception:
                self.crash(True)

    def crash(self, in_draw=False):
        try:
            traceback.print_exc()
        except Exception:
            pass
        try:
            self.player = None
            self.boss = None
            self.enemies = []
            self.projs = []
            self.zones = []
            self.pickups = []
            self.texts = []
            self.fx = []
            self.debris = []
            self.cards = []
            self.parts.clear()
            self.obs = build_level(0)
            self.shake = self.flash = self.slow = 0.
            self.state = "menu"
            self.sel = 0
            self.btns = []
            self.touch.reset()
            self.fing.clear()
            self.say(T("err"), 3.2)
            self.pt.clear_cache()
            if in_draw:
                self.disp.canvas.fill(VOID)
                self.disp.present()
        except Exception:
            pass

    def quit(self):
        self.cfg["lang"] = LANG
        save_cfg(self.cfg)
        if IS_WEB:
            return
        pygame.quit()
        sys.exit(0)

    # ---------- events ----------
    def events(self):
        for e in pygame.event.get():
            t = e.type
            if t == pygame.QUIT:
                self.quit()
            elif t == pygame.VIDEORESIZE:
                self.disp.resize(getattr(e, "w", LW), getattr(e, "h", LH))
                self.pt.clear_cache()
                self.bg.invalidate()
            elif t == pygame.KEYDOWN:
                self.key(e)
            elif t == pygame.MOUSEBUTTONDOWN and getattr(e, "button", 1) in (1, 3):
                if getattr(e, "button", 1) == 3 and self.state == "play":
                    self.inp["altmouse"] = True
                else:
                    self.pdown("m", self.disp.to_log(e.pos))
            elif t == pygame.MOUSEBUTTONUP:
                if getattr(e, "button", 1) == 3:
                    self.inp["altmouse"] = False
                else:
                    self.pup("m")
            elif t == pygame.MOUSEMOTION:
                if "m" in self.fing:
                    self.pmove("m", self.disp.to_log(e.pos))
            elif t == EV_FDOWN:
                self.cfg["touch"] = True
                self.pdown(("f", getattr(e, "finger_id", 0)), self.disp.finger(e))
            elif t == EV_FMOVE:
                self.pmove(("f", getattr(e, "finger_id", 0)), self.disp.finger(e))
            elif t == EV_FUP:
                self.pup(("f", getattr(e, "finger_id", 0)))

    def key(self, e):
        k = e.key
        if k == pygame.K_F11:
            self.disp.toggle_full()
            self.pt.clear_cache()
            self.bg.invalidate()
            return
        st = self.state
        if st in ("menu", "sel", "settings", "help", "pause", "over", "win"):
            items = self.menu_items()
            if k in (pygame.K_UP, pygame.K_w):
                if items:
                    self.sel = (self.sel - 1) % len(items)
                self.sfx.play("ui")
            elif k in (pygame.K_DOWN, pygame.K_s):
                if items:
                    self.sel = (self.sel + 1) % len(items)
                self.sfx.play("ui")
            elif k in (pygame.K_LEFT, pygame.K_a):
                if items:
                    self.adjust(items[self.sel][0], -1)
            elif k in (pygame.K_RIGHT, pygame.K_d):
                if items:
                    self.adjust(items[self.sel][0], 1)
            elif k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                if items:
                    self.act(items[self.sel][0])
            elif k == pygame.K_ESCAPE:
                if st == "pause":
                    self.go("play")
                elif st == "settings":
                    self.go(self.prev if self.prev in ("menu", "pause") else "menu")
                elif st in ("sel", "help", "over", "win"):
                    self.go("menu")
                else:
                    self.quit()
            return
        if st == "card":
            if k in (pygame.K_1, pygame.K_KP1):
                self.pick(0)
            elif k in (pygame.K_2, pygame.K_KP2):
                self.pick(1)
            elif k in (pygame.K_3, pygame.K_KP3):
                self.pick(2)
            return
        if st == "play" and self.player is not None:
            if k in (pygame.K_ESCAPE, pygame.K_p):
                self.go("pause")
                self.touch.reset()
            elif k == pygame.K_q:
                self.player.swap(-1)
            elif k == pygame.K_e:
                self.player.swap(1)
            elif pygame.K_1 <= k <= pygame.K_7:
                self.player.set_weapon(k - pygame.K_1)
            elif k == pygame.K_r:
                p = self.player
                if p.wdata()["kind"] in ("gun", "mortar") and p.reload_t <= 0 and p.ammo < p.max_ammo:
                    p.reload_t = 1.05 * p.reload_mult

    def pdown(self, fid, lp):
        for r, bid in self.btns:
            if r.collidepoint(lp):
                self.fing[fid] = ("ui", bid)
                self.sfx.play("ui")
                self.act(bid)
                return
        if self.state == "play" and self.tc():
            z = self.touch.zone(lp)
            if z:
                self.fing[fid] = ("t", z)
                self.touch.press(z, fid, lp)
                return
        self.fing[fid] = ("none", None)

    def pmove(self, fid, lp):
        e = self.fing.get(fid)
        if e and e[0] == "t":
            self.touch.move(fid, lp)

    def pup(self, fid):
        self.touch.up(fid)
        self.fing.pop(fid, None)

    # ---------- input ----------
    def read_input(self):
        i = self.inp
        keys = ("left", "right", "up", "attack", "guard", "dash", "ult", "skill", "altfire", "ovd")
        am = bool(i.get("altmouse"))
        for k in keys:
            i[k] = False
        if self.state != "play":
            return
        try:
            ks = pygame.key.get_pressed()
        except Exception:
            ks = None
        if ks:
            i["left"] = ks[pygame.K_a] or ks[pygame.K_LEFT]
            i["right"] = ks[pygame.K_d] or ks[pygame.K_RIGHT]
            i["up"] = ks[pygame.K_w] or ks[pygame.K_UP]
            i["attack"] = ks[pygame.K_SPACE] or ks[pygame.K_j]
            i["guard"] = ks[pygame.K_LSHIFT] or ks[pygame.K_RSHIFT]
            i["dash"] = ks[pygame.K_k]
            i["ult"] = ks[pygame.K_z]
            i["skill"] = ks[pygame.K_c]
            i["altfire"] = ks[pygame.K_l] or am
            i["ovd"] = ks[pygame.K_x]
        if self.tc():
            ax, ay = self.touch.axis()
            if ax < -.28:
                i["left"] = True
            if ax > .28:
                i["right"] = True
            if ay < -.55:
                i["up"] = True
            d = self.touch.down
            for a, b in (("attack", "attack"), ("guard", "guard"), ("jump", "up"), ("dash", "dash"),
                         ("ult", "ult"), ("skill", "skill"), ("altfire", "altfire"), ("ovd", "ovd")):
                if a in d:
                    i[b] = True
            if "swap" in d:
                if not self.swap_latch and self.player is not None:
                    self.player.swap(1)
                    self.swap_latch = True
            else:
                self.swap_latch = False

    # ---------- menus ----------
    def menu_items(self):
        st = self.state
        if st == "menu":
            return [("campaign", T("m_campaign"), ""), ("endless", T("m_endless"), ""),
                    ("bossrush", T("m_bossrush"), ""), ("time", T("m_time"), ""),
                    ("chaos", T("m_chaos"), ""), ("practice", T("m_practice"), ""),
                    ("settings", T("settings"), ""), ("help", T("help"), ""),
                    ("lang", T("language"), "中文" if LANG == "zh" else "English"),
                    ("quit", T("quit"), "")]
        if st == "sel":
            return [("char", T("microbe"), L(CHARS[self.c_i], "name")),
                    ("weap", T("weapon"), L(WEAPONS[self.w_i], "name")),
                    ("diff", T("difficulty"), T("d%d" % self.d_i)),
                    ("start", T("start"), ""), ("back", T("back"), "")]
        if st == "settings":
            q = self.cfg.get("quality", "high")
            qn = {"low": "g_low", "mid": "g_mid", "high": "g_high", "ultra": "g_ultra", "auto": "g_auto"}
            return [("lang", T("language"), "中文" if LANG == "zh" else "English"),
                    ("quality", T("graphics"), T(qn.get(q, "g_high"))),
                    ("touch", T("touchctl"), T("on") if self.cfg.get("touch") else T("off")),
                    ("vol", T("volume"), "%d%%" % int(float(self.cfg.get("vol", .6)) * 100)),
                    ("full", T("fullscreen"), T("on") if self.disp.full else T("off")),
                    ("shake", T("shakeopt"), T("on") if self.cfg.get("shake") else T("off")),
                    ("fps", T("showfps"), T("on") if self.cfg.get("fps") else T("off")),
                    ("sprites", T("sprites"), T("on") if self.cfg.get("sprites") else T("off")),
                    ("back", T("back"), "")]
        if st == "help":
            return [("back", T("back"), "")]
        if st == "pause":
            return [("resume", T("resume"), ""), ("restart", T("restart"), ""),
                    ("settings", T("settings"), ""), ("menu", T("tomenu"), "")]
        if st in ("over", "win"):
            return [("restart", T("restart"), ""), ("menu", T("tomenu"), "")]
        return []

    def flip_lang(self):
        global LANG
        LANG = "en" if (LANG == "zh" or not self.fonts.cjk) else "zh"
        if not self.fonts.cjk:
            LANG = "en"
        self.cfg["lang"] = LANG
        self.asset_note = T("asset_on") if (self.a1 or self.a2) else T("asset_off")
        self.pt.clear_cache()
        save_cfg(self.cfg)

    def adjust(self, bid, d):
        c = self.cfg
        if bid == "char":
            self.c_i = (self.c_i + d) % len(CHARS)
            self.new_preview()
            self.sfx.play("ui")
        elif bid == "weap":
            self.w_i = (self.w_i + d) % len(WEAPONS)
            self.new_preview()
            self.sfx.play("ui")
        elif bid == "diff":
            self.d_i = int(clamp(self.d_i + d, 0, 4))
            self.sfx.play("ui")
        elif bid == "lang":
            self.flip_lang()
        elif bid == "quality":
            i = QLIST.index(c.get("quality")) if c.get("quality") in QLIST else 2
            c["quality"] = QLIST[(i + d) % len(QLIST)]
            self.disp.rebuild()
            self.pt.clear_cache()
            self.bg.invalidate()
            save_cfg(c)
        elif bid == "touch":
            c["touch"] = not c.get("touch")
            self.touch.reset()
            save_cfg(c)
        elif bid == "vol":
            c["vol"] = round(clamp(float(c.get("vol", .6)) + d * .1, 0, 1), 2)
            self.sfx.play("ui")
            save_cfg(c)
        elif bid == "full":
            self.disp.toggle_full()
            self.pt.clear_cache()
            self.bg.invalidate()
            save_cfg(c)
        elif bid == "shake":
            c["shake"] = not c.get("shake")
            save_cfg(c)
        elif bid == "fps":
            c["fps"] = not c.get("fps")
            save_cfg(c)
        elif bid == "sprites":
            c["sprites"] = not c.get("sprites")
            save_cfg(c)

    def act(self, bid):
        if bid in MODES:
            self.mode = bid
            self.go("sel")
        elif bid == "settings":
            self.prev = self.state
            self.go("settings")
        elif bid == "help":
            self.go("help")
        elif bid == "quit":
            self.quit()
        elif bid in ("char", "weap", "diff", "lang", "quality", "touch", "vol", "full",
                     "fps", "sprites", "shake"):
            self.adjust(bid, 1)
        elif bid == "start":
            self.begin(self.mode)
        elif bid == "back":
            if self.state == "settings":
                self.go(self.prev if self.prev in ("menu", "pause") else "menu")
            else:
                self.go("menu")
        elif bid == "resume":
            self.go("play")
        elif bid == "restart":
            self.begin(self.mode)
        elif bid == "menu":
            self.go("menu")
        elif bid == "pausebtn":
            self.go("pause")
            self.touch.reset()
        elif bid.startswith("card"):
            try:
                self.pick(int(bid[4:]))
            except Exception:
                pass

    # ---------- run ----------
    def begin(self, mode):
        self.mode = mode if mode in MODES else "campaign"
        self.player = Player(CHARS[self.c_i], WEAPONS[self.w_i]["key"], self)
        self.enemies = []
        self.projs = []
        self.zones = []
        self.pickups = []
        self.texts = []
        self.fx = []
        self.debris = []
        self.parts.clear()
        self.boss = None
        self.obs = build_level(0)
        self.affix = "none"
        self.stage = 1
        self.wave = 0
        self.kills = 0
        self.score = 0
        self.level = 1
        self.xp = 0
        self.xp_need = 28
        self.pending = 0
        self.rt = 0.
        self.tleft = 120. if self.mode == "time" else 0.
        self.spawned = 0
        self.quota = 0
        self.stimer = 0.
        self.gap = 1.
        self.alive_cap = 9
        self.brk = 1.6
        self.addt = 6.
        self.static_t = 0.
        self.bqueue = list(BOSS_ORDER) if self.mode == "bossrush" else []
        self.shake = self.flash = self.slow = 0.
        self.result = None
        self.cards = []
        self.touch.reset()
        self.banner(T("m_" + self.mode), 1.4, GOLD)
        self.go("play")

    def finish(self, win):
        self.result = {"win": win, "score": int(self.score), "kills": self.kills,
                       "stage": self.stage, "wave": max(1, self.wave), "time": int(self.rt), "rec": False}
        best = self.cfg.setdefault("best", {})
        if int(self.score) > int(best.get(self.mode, 0)):
            best[self.mode] = int(self.score)
            self.result["rec"] = True
        save_cfg(self.cfg)
        self.sfx.play("level" if win else "boom")
        self.go("win" if win else "over")

    # ---------- director ----------
    def pool(self):
        d = self.progress()
        p = [("paraben", 100)]
        add = (("spore", 1, 72), ("phage", 2, 58), ("blob", 3, 46), ("bomber", 4, 42),
               ("lancer", 4, 40), ("metal", 5, 36), ("shielder", 6, 34), ("cryo", 6, 34),
               ("sapper", 7, 32), ("drone", 8, 30), ("reaper", 8, 30), ("turret", 9, 26),
               ("wraith", 10, 26), ("hexer", 11, 22), ("warden", 12, 20), ("mother", 13, 14))
        for k, thr, w in add:
            if d >= thr:
                p.append((k, w))
        if self.mode == "practice":
            p = [(k, 40) for k in EN if k != "blobmini"]
        return p

    def spawn(self, kind=None):
        if len(self.enemies) > 30:
            return
        k = kind or wchoice(self.pool()) or "paraben"
        if k not in EN:
            k = "paraben"
        dd = self.diff()
        elite = dd > 3.5 and random.random() < min(.26, .03 + dd * .02)
        d = EN[k]
        if k in AIR:
            x, y = random.uniform(50, LW - 90), random.uniform(-80, 30)
        elif k == "turret":
            x, y = random.uniform(80, LW - 120), GROUND_Y - d["h"] - 2
        else:
            x = -60 if random.random() < .5 else LW + 20
            y = GROUND_Y - d["h"] - 2
        e = Enemy(k, x, y, dd, self, elite)
        self.enemies.append(e)
        self.parts.burst(e.rect.centerx, e.rect.centery, e.color, 7, 140, 3, .3, 200, True)

    def spawn_boss(self, btype, power):
        self.boss = Boss(btype, power, self, self.dmul())
        self.banner(T("boss_warn"), 2.0, RED)
        self.shake = 20
        self.flash = .45
        self.sfx.play("alarm")

    def roll_affix(self):
        if self.mode == "practice":
            self.affix = "none"
            return
        chance = .38 if self.mode != "chaos" else 1.0
        if random.random() < chance and self.progress() >= 2:
            self.affix = random.choice(AFFIX_KEYS)
            a = AFFIX[self.affix]
            self.banner(T(a["key"]), 1.5, a["c"])
        else:
            self.affix = "none"

    def new_wave(self):
        if self.mode == "bossrush":
            if self.bqueue:
                self.spawn_boss(self.bqueue.pop(0), 1 + (len(BOSS_ORDER) - len(self.bqueue)))
            else:
                self.finish(True)
            return
        self.wave += 1
        self.spawned = 0
        self.roll_affix()
        base = 6 + self.wave * 2 + (self.stage - 1) * 3
        if self.affix == "swarm":
            base = int(base * 1.4)
        self.quota = int(clamp(base * (.8 + .2 * self.d_i), 4, 64))
        self.gap = max(.3, 1.2 - .05 * self.wave - .06 * self.stage)
        self.alive_cap = int(min(18, 7 + self.wave + self.stage))
        self.stimer = 0.
        self.banner(T("wave_go", self.wave), 1.3, CYAN)

    def wave_done(self):
        self.score += 130 * max(1, self.wave)
        if self.mode == "campaign":
            if self.wave >= 3:
                bt = {2: "monarch", 3: "colossus", 4: "mitosis", 5: "necro"}.get(self.stage)
                if bt:
                    self.spawn_boss(bt, self.stage)
                else:
                    self.stage_up()
            else:
                self.brk = 2.1
                self.banner(T("wave_clear"), 1.3, LIME)
        elif self.mode in ("endless", "chaos"):
            if self.wave % 5 == 0:
                self.spawn_boss(BOSS_ORDER[(self.wave // 5 - 1) % len(BOSS_ORDER)], 1 + self.wave // 5)
            else:
                self.brk = 1.9
                self.banner(T("wave_clear"), 1.2, LIME)
        else:
            self.brk = 1.4

    def stage_up(self):
        if self.stage >= 5:
            self.finish(True)
            return
        self.banner(T("stage_clear", self.stage), 1.9, GOLD)
        self.score += 550
        self.stage += 1
        self.wave = 0
        self.brk = 2.8
        self.obs = build_level(self.stage - 1)
        p = self.player
        if p:
            p.hp = min(p.max_hp, p.hp + max(2, p.max_hp // 3))
            p.energy = p.max_energy

    def boss_dead(self):
        b = self.boss
        if b is None:
            return
        self.score += b.score
        self.kills += 1
        self.gain_xp(b.xp)
        for _ in range(3):
            self.fx.append(Fx("ring", b.rect.centerx + random.uniform(-40, 40),
                              b.rect.centery + random.uniform(-30, 30), .8,
                              random.choice([GOLD, AMB, RED]), r=260))
        self.parts.burst(b.rect.centerx, b.rect.centery, (255, 190, 90), 54, 420, 7, .9, 480, True)
        for _ in range(5):
            self.debris.append(Debris(b.rect, b.pcol(), True))
        self.shake = 24
        self.flash = .6
        self.sfx.play("boom")
        self.boss = None
        if self.mode == "campaign":
            if self.stage >= 5:
                self.finish(True)
            else:
                self.stage_up()
        elif self.mode == "bossrush":
            self.brk = 2.2
        else:
            self.brk = 2.3

    def director(self, dt):
        if self.affix == "static":
            self.static_t -= dt
            if self.static_t <= 0:
                self.static_t = 2.4
                self.zones.append(Zone(random.uniform(60, LW - 60), GROUND_Y, 70, 28, 2.4, 12, "e",
                                       ICE, "shock"))
        if self.mode == "practice":
            self.stimer -= dt
            if self.stimer <= 0 and len(self.enemies) < 8:
                self.spawn()
                self.stimer = 1.1
            if self.player:
                self.player.ult = self.player.ult_need
                self.player.ovd = 100.
                self.player.skill_cd = 0.
            return
        if self.boss is not None:
            self.addt -= dt
            if self.addt <= 0 and len(self.enemies) < 6:
                self.addt = 7.
                self.spawn("spore")
            return
        if self.brk > 0:
            self.brk -= dt
            if self.brk <= 0:
                self.new_wave()
            return
        if self.spawned < self.quota:
            self.stimer -= dt
            if self.stimer <= 0 and len(self.enemies) < self.alive_cap:
                self.spawn()
                self.spawned += 1
                self.stimer = self.gap
        elif not self.enemies:
            self.wave_done()

    # ---------- 元素反應 ----------
    def apply_status(self, u, name, dur, pw, src_x=None):
        p = self.player
        rm = p.react_mult if p else 1.
        s = u.st
        if name == "chill":
            u.chill_stack += 1
            if u.chill_stack >= 3:
                u.chill_stack = 0
                s.add("freeze", STAT_DUR["freeze"], pw)
                self.texts.append(FText(u.rect.centerx, u.rect.y - 18, "FREEZE", ICE, 18, .6))
        reacted = None
        if name == "shock" and s.has("burn"):
            reacted = "overload"
        elif name == "burn" and s.has("shock"):
            reacted = "overload"
        elif name in ("burn", "corrode") and (s.has("corrode") if name == "burn" else s.has("burn")):
            reacted = "meltdown"
        elif name == "bleed" and (s.has("chill") or s.has("freeze")):
            reacted = "shatter"
        elif name in ("chill", "freeze") and s.has("bleed"):
            reacted = "shatter"
        elif name == "shock" and (s.has("chill") or s.has("freeze")):
            reacted = "supercon"
        elif name in ("chill", "freeze") and s.has("shock"):
            reacted = "supercon"
        s.add(name, dur, pw)
        if reacted is None:
            return
        cx, cy = u.rect.center
        self.sfx.play("react", .05)
        if reacted == "overload":
            self.texts.append(FText(cx, u.rect.y - 26, T("overload"), AMB, 21, .8))
            self.explode(cx, cy, 110, int(38 * rm), "p", None, AMB)
            s.clear("shock")
        elif reacted == "meltdown":
            self.texts.append(FText(cx, u.rect.y - 26, T("meltdown"), (255, 170, 80), 20, .8))
            s.add("burn", dur * 1.6, pw * 2.2)
            s.add("corrode", dur * 1.6, pw * 2.0)
            self.fx.append(Fx("ring", cx, cy, .4, (255, 160, 70), r=90))
        elif reacted == "shatter":
            self.texts.append(FText(cx, u.rect.y - 26, T("shatter"), ICE, 22, .85))
            self.fx.append(Fx("shard", cx, cy, .4, ICE, r=70, ang=random.uniform(0, 3)))
            u.take(int(52 * rm), self, cx, 0, 1.0, 2.0)
            s.clear("chill")
            s.clear("freeze")
            s.clear("bleed")
            self.shake = max(self.shake, 8)
        elif reacted == "supercon":
            self.texts.append(FText(cx, u.rect.y - 26, T("supercon"), CYAN, 19, .8))
            s.add("supercon", 3.2 * rm, 1.)
            self.fx.append(Fx("shock", cx, cy, .4, CYAN, r=100))

    # ---------- 傷害 ----------
    def hurt_enemy(self, e, dmg, crit, from_x, knock=0., elem=None, stag=1.0, pen=0.0):
        if e is None or e.hp <= 0:
            return
        if e.blocks(from_x) and e.shield > 0:
            e.take(dmg, self, from_x, 0, pen, stag * .4)
            self.parts.burst(e.rect.centerx, e.rect.centery, ICE, 6, 150, 3, .25)
            return
        d = e.take(dmg, self, from_x, knock, pen, stag)
        p = self.player
        if elem and p is not None:
            dur = STAT_DUR.get(elem, 2.0) * p.status_mult
            self.apply_status(e, elem, dur, p.elem_mult, from_x)
        if d <= 0:
            self.parts.burst(e.rect.centerx, e.rect.centery, ICE, 6, 150, 3, .25)
            return
        col = GOLD if crit else WHT
        if d < dmg * .7:
            col = (172, 188, 210)
        self.texts.append(FText(e.rect.centerx + random.uniform(-7, 7), e.rect.y - 4,
                                ("%d!" % d) if crit else str(d), col, 23 if crit else 18, .6))
        self.parts.burst(e.rect.centerx, e.rect.centery, e.color, 11 if crit else 6, 190, 3.2, .3, 320, True)
        self.sfx.play("hit")
        if "leech" in e.mods and e.hp > 0:
            e.hp = min(e.max_hp, e.hp + d * .25)
        if p:
            self.score += int(d * (1 + p.combo * .02))
            p.gain_ult(d * .16)
            p.gain_ovd(d * .12)

    def execute(self, e):
        p = self.player
        self.texts.append(FText(e.rect.centerx, e.rect.y - 30, T("exec"), BLOOD, 26, 1.0))
        self.fx.append(Fx("slash", e.rect.centerx, e.rect.centery, .3, WHT, ang=random.uniform(-.7, .7)))
        self.parts.burst(e.rect.centerx, e.rect.centery, BLOOD, 24, 320, 5, .6, 420, True)
        self.sfx.play("exec")
        self.shake = max(self.shake, 11)
        self.slow = max(self.slow, .18)
        e.hp = 0
        self.score += e.score
        if p:
            p.energy = min(p.max_energy, p.energy + 22)
            p.gain_ovd(16)
            p.gain_ult(12)
            if p.hp < p.max_hp:
                p.hp += 1

    def enemy_dead(self, e):
        p = self.player
        self.kills += 1
        self.score += int(e.score * (1 + (p.combo * .02 if p else 0)))
        self.gain_xp(e.xp)
        self.parts.burst(e.rect.centerx, e.rect.centery, e.color, 18, 290, 5, .55, 480, True)
        self.fx.append(Fx("spark", e.rect.centerx, e.rect.centery, .24, e.color, r=56))
        self.sfx.play("boom", .05)
        if e.w >= 40 or e.elite:
            for _ in range(2):
                self.debris.append(Debris(e.rect, e.color, True))
        if e.kind == "blob":
            for s in (-1, 1):
                if len(self.enemies) < 30:
                    self.enemies.append(Enemy("blobmini", e.rect.centerx + s * 14, e.rect.y,
                                              self.diff(), self))
        if "volatile" in e.mods:
            self.explode(e.rect.centerx, e.rect.centery, 96, 20, "e", "burn", AMB)
        if p:
            p.gain_ult(7)
            p.gain_ovd(6)
            p.add_combo(self)
            if p.lifesteal > 0 and random.random() < p.lifesteal and p.hp < p.max_hp:
                p.hp += 1
                self.texts.append(FText(p.rect.centerx, p.rect.y - 18, "+1", LIME, 19, .7))
        dm = p.drop_mult if p else 1.
        r = random.random() / max(.2, dm)
        if r < .08:
            self.pickups.append(Pickup(e.rect.centerx, e.rect.centery, "hp"))
        elif r < .2:
            self.pickups.append(Pickup(e.rect.centerx, e.rect.centery, "en"))
        elif r < .27:
            self.pickups.append(Pickup(e.rect.centerx, e.rect.centery, "ovd"))
        elif r < .48:
            self.pickups.append(Pickup(e.rect.centerx, e.rect.centery, "xp"))

    def explode(self, x, y, rad, dmg, owner, elem=None, col=AMB):
        self.fx.append(Fx("ring", x, y, .4, col, r=rad * 1.5))
        self.parts.burst(x, y, col, 20, 300, 5, .55, 400, True)
        self.sfx.play("boom", .06)
        self.shake = max(self.shake, 8)
        box = pygame.Rect(x - rad, y - rad, rad * 2, rad * 2)
        self.hit_obstacles(box, dmg * 1.5, x)
        if owner in ("p", "n"):
            for e in self.targets():
                if (e.rect.centerx - x) ** 2 + (e.rect.centery - y) ** 2 < rad * rad:
                    self.hurt_enemy(e, dmg, False, x, 150, elem, 1.2, .3)
        if owner in ("e", "n"):
            p = self.player
            if p and not p.dead and (p.rect.centerx - x) ** 2 + (p.rect.centery - y) ** 2 < rad * rad:
                p.hurt(max(1, 1 if owner == "e" else 1), self, x, None)

    def gain_xp(self, amt):
        self.xp += max(0, int(amt))
        guard = 0
        while self.xp >= self.xp_need and guard < 20:
            guard += 1
            self.xp -= self.xp_need
            self.level += 1
            self.xp_need = int(self.xp_need * 1.33) + 11
            self.pending += 1
            self.sfx.play("level")
            self.banner(T("levelup"), 1.1, GOLD)

    def roll_cards(self):
        lv = self.level
        pool = []
        for a in AUG:
            w = (100 if a["r"] == 0 else (46 if a["r"] == 1 else 18)) + lv * (a["r"] * 4)
            pool.append((a, w))
        out = []
        tries = 0
        while len(out) < 3 and tries < 40:
            tries += 1
            c = wchoice(pool)
            if c is not None and c not in out:
                out.append(c)
        self.cards = out
        self.go("card")

    def pick(self, i):
        if not self.cards or not (0 <= i < len(self.cards)):
            return
        c = self.cards[i]
        if self.player:
            try:
                c["f"](self.player)
            except Exception:
                traceback.print_exc()
        self.sfx.play("level")
        self.pending = max(0, self.pending - 1)
        self.cards = []
        if self.pending > 0:
            self.roll_cards()
        else:
            self.go("play")

    # ---------- update ----------
    def update(self, dt):
        self.menu_t += dt
        self.bg.update(dt)
        if self.shake > 0:
            self.shake = max(0., self.shake - dt * 34)
        if self.flash > 0:
            self.flash = max(0., self.flash - dt * 2.2)
        if self.slow > 0:
            self.slow = max(0., self.slow - dt)
        if self.ban_t > 0:
            self.ban_t = max(0., self.ban_t - dt)
        if self.toast_t > 0:
            self.toast_t = max(0., self.toast_t - dt)
        self.texts = [t for t in self.texts if t.update(dt)]
        self.fx = [f for f in self.fx if f.update(dt)]
        self.debris = [d for d in self.debris if d.update(dt)]
        self.parts.update(dt)
        if self.state == "sel" and self.preview:
            self.preview.t += dt
            self.preview.walk += dt * 2
        if self.state != "play":
            return
        p = self.player
        if p is None:
            self.go("menu")
            return
        gdt = dt * (.45 if self.slow > 0 else 1.)
        self.rt += gdt
        if self.mode == "time":
            self.tleft -= gdt
            if self.tleft <= 0:
                self.tleft = 0
                self.finish(True)
                return
        for o in self.obs:
            o.update(gdt, self)
        p.update(gdt, self)
        for e in list(self.enemies):
            e.update(gdt, self)
            if e.hp <= 0:
                self.enemy_dead(e)
                if e in self.enemies:
                    self.enemies.remove(e)
            elif e.y > LH + 220:
                if e in self.enemies:
                    self.enemies.remove(e)
        if self.boss is not None:
            self.boss.update(gdt, self)
            if self.boss.hp <= 0:
                self.boss_dead()
        self.upd_projs(gdt)
        self.upd_zones(gdt)
        for pu in list(self.pickups):
            if not pu.update(gdt, p):
                self.pickups.remove(pu)
                continue
            if pu.rect.colliderect(p.rect):
                if pu.kind == "hp":
                    p.hp = min(p.max_hp, p.hp + 1)
                    self.texts.append(FText(p.rect.centerx, p.rect.y - 18, "+1", LIME, 19, .7))
                elif pu.kind == "en":
                    p.energy = min(p.max_energy, p.energy + 34)
                elif pu.kind == "ovd":
                    p.gain_ovd(30)
                elif pu.kind == "barrier":
                    p.barrier_max = max(p.barrier_max, 20)
                    p.barrier = p.barrier_max
                else:
                    self.gain_xp(7)
                self.sfx.play("ui", .05)
                self.parts.burst(pu.x, pu.y, PICK_COL.get(pu.kind, WHT), 8, 150, 3, .3)
                self.pickups.remove(pu)
        self.director(gdt)
        if p.dead:
            self.parts.burst(p.rect.centerx, p.rect.centery, p.color, 34, 340, 6, .9, 500, True)
            self.shake = 22
            self.flash = .55
            self.finish(False)
            return
        if self.pending > 0:
            self.roll_cards()

    def upd_projs(self, dt):
        p = self.player
        tg = self.targets()
        for b in list(self.projs):
            b.update(dt, self)
            if b.dead:
                if b in self.projs:
                    self.projs.remove(b)
                continue
            if b.owner in ("p", "n"):
                for e in tg:
                    if e.hp <= 0 or not b.rect.colliderect(e.rect):
                        continue
                    if b.expl > 0:
                        self.explode(b.x, b.y, b.expl, b.dmg, "p", b.elem, b.col)
                        b.dead = True
                    else:
                        self.hurt_enemy(e, b.dmg, b.crit, b.x, 60, b.elem, 1.0,
                                        p.pen if p else 0.)
                        if b.pierce > 0:
                            b.pierce -= 1
                        else:
                            b.dead = True
                    break
            else:
                if p and not p.dead and b.rect.colliderect(p.rect):
                    front = (b.x - p.rect.centerx) * p.face >= 0
                    if (p.guarding or p.veil > 0) and front and p.reflect:
                        b.owner = "p"
                        b.vx *= -1.2
                        b.vy *= -1.
                        b.dmg = int(b.dmg * 10 + 20)
                        b.col = CYAN
                        b.kind = "bolt"
                        b.elem = "shock"
                        p.energy = min(p.max_energy, p.energy + 6)
                        p.gain_ovd(6)
                        self.sfx.play("parry", .08)
                    elif p.hurt(b.dmg, self, b.x, None):
                        b.dead = True
                        if b.elem:
                            if b.elem == "chill":
                                p.st.add("chill", 2.0)
                            elif b.elem == "void":
                                p.st.add("void", 3.0)
                            elif b.elem == "corrode":
                                p.st.add("corrode", 2.2)
            if b.dead and b in self.projs:
                self.projs.remove(b)

    def upd_zones(self, dt):
        p = self.player
        for z in list(self.zones):
            if not z.update(dt):
                self.zones.remove(z)
                continue
            if z.tick > 0:
                continue
            z.tick = .35
            if z.owner == "p":
                for e in self.targets():
                    if z.hits(e.rect):
                        self.hurt_enemy(e, max(1, int(z.dps * .35)), False, z.x, 0, z.elem, .4,
                                        p.pen if p else 0.)
                        if z.slow:
                            self.apply_status(e, "chill", 1.4, 1.)
            else:
                if p and not p.dead and z.hits(p.rect):
                    p.hurt(1, self, z.x, None)
                    if z.slow:
                        p.st.add("chill", 1.0)
                    if z.elem == "shock":
                        p.st.add("shock", .8)

    # ---------- draw ----------
    def draw(self):
        d = self.disp
        pt = self.pt
        self.btns = []
        if self.bg.surf is None or abs(self.bg.k - d.k) > 1e-6 or self.bg.surf.get_size() != d.canvas.get_size():
            self.bg.build(pt, d.k, d.canvas.get_size())
        pt.begin(d.canvas, d.k)
        ox = oy = 0.
        if self.shake > .4 and self.cfg.get("shake", True):
            a = min(12., self.shake)
            ox, oy = random.uniform(-a, a), random.uniform(-a, a)
            d.canvas.fill(VOID)
        d.canvas.blit(self.bg.surf, (int(ox * d.k), int(oy * d.k)))
        pt.offset(ox, oy)
        self.bg.draw_live(pt)
        if self.state in ("play", "pause", "card", "over", "win"):
            self.draw_world(pt)
        pt.offset(0, 0)
        if self.bg.vig is not None and self.bg.vig.get_size() == d.canvas.get_size():
            d.canvas.blit(self.bg.vig, (0, 0))
        if self.flash > .01:
            pt.flash(self.flash)
        if self.state in ("play", "pause", "card", "over", "win"):
            self.draw_hud(pt)
            if self.state == "play" and self.tc():
                self.touch.draw(pt)
        if self.state in ("menu", "sel", "settings", "help"):
            self.draw_screen(pt)
        elif self.state == "pause":
            self.dim(pt, 172)
            pt.text(T("paused"), 50, GOLD, (LW / 2, 90), "midtop", True, maxw=500, glow=GOLD)
            self.draw_list(pt, LW / 2, 168, 380, 42)
        elif self.state == "card":
            self.draw_cards(pt)
        elif self.state in ("over", "win"):
            self.draw_result(pt)
        if self.toast_t > 0:
            r = pygame.Rect(LW / 2 - 220, LH - 44, 440, 32)
            pt.panel(r, (24, 12, 16, 220), (200, 110, 100), 8)
            pt.push_clip(r)
            pt.text(self.toast, 18, (255, 200, 190), (r.centerx, r.centery), "center", True, maxw=r.w - 20)
            pt.pop_clip()
        if self.cfg.get("fps"):
            pt.text("%s %d" % (T("fps"), int(self.fps)), 15, (120, 160, 140),
                    (LW - 10, LH - 18), "topright", True, maxw=120)
        d.present()

    def dim(self, pt, a=150):
        pt.panel((0, 0, LW, LH), (3, 4, 9, a), None, 0)

    def draw_world(self, pt):
        for o in self.obs:
            o.draw(pt, self)
        for d in self.debris:
            d.draw(pt)
        for z in self.zones:
            z.draw(pt)
        for pu in self.pickups:
            pu.draw(pt)
        for e in self.enemies:
            e.draw(pt, self)
        if self.boss is not None:
            self.boss.draw(pt, self)
        for b in self.projs:
            b.draw(pt)
        if self.player:
            self.player.draw(pt)
        self.parts.draw(pt)
        for f in self.fx:
            f.draw(pt)
        for t in self.texts:
            t.draw(pt)
        if self.ban_t > 0:
            f = clamp(self.ban_t, 0, 1)
            pt.text(self.ban, 42 + (1 - f) * 6, self.ban_c, (LW / 2, 118), "center", True,
                    maxw=LW - 120, glow=self.ban_c)

    # ---------- HUD ----------
    def draw_hud(self, pt):
        p = self.player
        if p is None:
            return
        # 左：狀態面板
        box = pygame.Rect(12, 10, 250, 80)
        pt.panel(box, (7, 10, 18, 215), EDGE, 9, 2, True)
        pt.push_clip(box)
        pt.dia(p.color, (40, 46), 17, 20)
        pt.dia(dk(p.color, .3), (40, 46), 17, 20, 2)
        pt.text(L(p.char, "name"), 15, WHT, (66, 16), "topleft", True, maxw=120)
        pt.text("%s %d" % (T("lv"), self.level), 14, GOLD, (box.right - 10, 17), "topright", maxw=62)
        pt.bar(pygame.Rect(66, 34, 178, 11), p.hp / max(1, p.max_hp),
               LIME if p.hp > p.max_hp * .34 else RED, seg=max(1, int(p.max_hp // 4)))
        pt.text("%d/%d" % (max(0, int(p.hp)), int(p.max_hp)), 12, WHT, (155, 39), "center", maxw=80)
        pt.bar(pygame.Rect(66, 48, 178, 6), p.energy / p.max_energy, CYAN)
        if p.barrier > 0:
            pt.bar(pygame.Rect(66, 56, 178, 4), p.barrier / max(1., p.barrier_max), ICE)
        pt.bar(pygame.Rect(66, 63, 178, 4), self.xp / max(1, self.xp_need), LIME)
        if p.armor > 0:
            pt.text("AR %d" % int(p.armor), 12, GREY, (20, 66), "topleft", maxw=44)
        pt.pop_clip()

        # 左下：武器 + 冷卻
        b2 = pygame.Rect(12, 94, 250, 54)
        pt.panel(b2, (7, 10, 18, 205), EDGE, 9)
        pt.push_clip(b2)
        wd = p.wdata()
        pt.text(L(wd, "name"), 15, wd["color"], (20, 99), "topleft", True, maxw=136)
        k = wd["kind"]
        if k in ("gun", "mortar"):
            if p.reload_t > 0:
                pt.text(T("reloading"), 12, AMB, (20, 120), "topleft", maxw=54)
                pt.bar(pygame.Rect(74, 122, 66, 7), 1 - p.reload_t / max(.1, 1.45 * p.reload_mult), AMB)
            else:
                pt.text("%d/%d" % (p.ammo, p.max_ammo), 13, LGREY if False else GREY, (20, 120), "topleft", maxw=54)
                pt.bar(pygame.Rect(74, 122, 66, 7), p.ammo / max(1, p.max_ammo), CYAN, seg=p.max_ammo)
        elif k == "rapid":
            pt.text(T("overheat") if p.overheat > 0 else "HEAT", 12, RED if p.overheat > 0 else GREY,
                    (20, 120), "topleft", maxw=54)
            pt.bar(pygame.Rect(74, 122, 66, 7), p.heat / 100., RED if p.heat > 70 else AMB)
        elif k in ("charge", "lance"):
            pt.bar(pygame.Rect(20, 122, 120, 7), p.charge, VIOL, glow=p.charge >= 1)
        else:
            pt.text("x%.2f" % p.dscale(), 13, GREY, (20, 120), "topleft", maxw=60)
        for i, (nm, cur, mx, c) in enumerate(
                (("SKL", p.skill_cd, p.skill_cd_base * p.skill_cd_mult, TOXIC),
                 ("DSH", p.dash_cd, max(.01, p.dash_cd_base * p.dash_cd_mult), CYAN))):
            cx, cy = 166 + i * 32, 122
            f = 1. - clamp(cur / max(.01, mx), 0, 1)
            pt.hexa((14, 18, 28), (cx, cy), 14, 14)
            pt.hexa(c if f >= 1 else (60, 70, 90), (cx, cy), 14, 14, 2)
            if f < 1:
                pt.rect(c, (cx - 12, cy + 8 - 18 * f, 24, max(1, 18 * f)))
            else:
                pt.glow((cx, cy), 18, c, .4)
            pt.text(nm, 10, c if f >= 1 else (96, 106, 128), (cx, cy), "center", True, maxw=24)
        pt.pop_clip()

        # ULT / OVD 指示
        ur = p.ult / max(1., p.ult_need)
        rdy = p.ult >= p.ult_need
        pt.hexa((12, 16, 26), (232, 122), 19, 19)
        pt.hexa(GOLD if rdy else (70, 80, 100), (232, 122), 19, 19, 2)
        pt.rect(GOLD if rdy else (110, 120, 145), (232 - 15, 122 + 12 - 24 * clamp(ur, 0, 1), 30,
                                                   max(1, 24 * clamp(ur, 0, 1))))
        pt.text("Z" if rdy else "%d" % int(ur * 100), 14, VOID if rdy else WHT, (232, 122), "center",
                False, maxw=28)
        if rdy:
            pt.glow((232, 122), 26, GOLD, .45 + .25 * math.sin(self.menu_t * 8))
        ob = pygame.Rect(12, 152, 250, 12)
        pt.panel(ob, (7, 10, 18, 190), EDGE, 4, 1)
        if p.ovd_t > 0:
            pt.bar(pygame.Rect(16, 155, 242, 6), p.ovd_t / p.ovd_len, GOLD, glow=True)
            pt.text(T("overdrive"), 11, VOID, (137, 158), "center", False, maxw=200)
        else:
            pt.bar(pygame.Rect(16, 155, 242, 6), p.ovd / 100., AMB if p.ovd < 100 else GOLD,
                   glow=p.ovd >= 100)
            if p.ovd >= 100:
                pt.text("X : " + T("overdrive"), 10, VOID, (137, 158), "center", False, maxw=200)

        # 狀態 icon
        sx = 16
        for n in p.st.names()[:5]:
            c = STAT_COL.get(n, WHT)
            pt.dia(c, (sx + 6, 176), 6, 7)
            sx += 18

        # 上中：關卡 / 詞綴
        if self.mode == "time":
            mid = "%s %0.1f" % (T("time"), self.tleft)
            mc = RED if self.tleft < 15 else CYAN
        elif self.mode == "campaign":
            mid = "%s %d   %s %d" % (T("stage"), self.stage, T("wave"), max(1, self.wave))
            mc = CYAN
        elif self.mode == "bossrush":
            mid = T("m_bossrush")
            mc = CYAN
        else:
            mid = "%s %d" % (T("wave"), max(1, self.wave))
            mc = CYAN
        pt.text(mid, 18, mc, (LW / 2, 12), "midtop", True, maxw=300)
        af = AFFIX.get(self.affix, AFFIX["none"])
        if self.affix != "none":
            r = pygame.Rect(LW / 2 - 90, 34, 180, 20)
            pt.panel(r, (14, 8, 14, 200), af["c"], 5, 1)
            pt.text(T(af["key"]), 13, af["c"], (r.centerx, r.centery), "center", True, maxw=r.w - 12)
            y0 = 58
        else:
            y0 = 36
        if self.boss is None and self.mode != "practice":
            if self.brk > 0:
                pt.text(T("next_wave", "%0.1f" % self.brk), 14, (140, 170, 200),
                        (LW / 2, y0), "midtop", True, maxw=280)
            else:
                left = max(0, self.quota - self.spawned) + len(self.enemies)
                pt.text("%s %d" % (T("left"), left), 14, (220, 160, 160), (LW / 2, y0), "midtop",
                        True, maxw=200)
        if p.combo > 1:
            rk, ri = p.rank()
            pt.text("%s %s  x%d" % (T("combo"), rk, p.combo), 22 + min(12, ri * 3), GOLD,
                    (LW / 2, y0 + 20), "midtop", True, maxw=320, glow=GOLD if ri >= 4 else None)

        # 右上：分數
        r3 = pygame.Rect(LW - 172, 10, 160, 50)
        pt.panel(r3, (7, 10, 18, 210), EDGE, 9)
        pt.push_clip(r3)
        pt.text(T("score"), 12, (130, 150, 180), (r3.x + 10, r3.y + 6), "topleft", maxw=70)
        pt.text("{:,}".format(int(self.score)), 21, GOLD, (r3.right - 10, r3.y + 21), "topright",
                True, maxw=138)
        pt.pop_clip()
        pt.text("%s %d" % (T("kills"), self.kills), 13, (150, 170, 200), (LW - 12, 64), "topright",
                True, maxw=140)

        if self.state == "play":
            rb = pygame.Rect(LW - 44, 84, 32, 26)
            pt.panel(rb, (12, 16, 28, 200), EDGE, 4)
            pt.rect(GREY, (rb.x + 10, rb.y + 6, 4, 14))
            pt.rect(GREY, (rb.x + 18, rb.y + 6, 4, 14))
            self.btns.append((rb, "pausebtn"))

        # 首領條
        if self.boss is not None:
            b = self.boss
            bw = 420
            r4 = pygame.Rect(LW / 2 - bw / 2 - 8, LH - 58, bw + 16, 44)
            pt.panel(r4, (14, 7, 12, 210), (170, 84, 80), 8, 2, True)
            pt.push_clip(r4)
            pt.text("%s   %s" % (b.name, T("phase", b.phase)), 15, (255, 170, 130),
                    (r4.centerx, r4.y + 4), "midtop", True, maxw=r4.w - 24)
            pt.bar(pygame.Rect(r4.x + 8, r4.y + 22, r4.w - 16, 11),
                   clamp(b.hp_show / max(1., b.max_hp), 0, 1), b.pcol(), glow=True)
            pt.bar(pygame.Rect(r4.x + 8, r4.y + 34, r4.w - 16, 4),
                   clamp(b.stagger / b.stagger_max, 0, 1), AMB)
            if b.btype == "colossus":
                for i in range(3):
                    c = (206, 214, 196) if i < b.plate else (50, 54, 60)
                    pt.rect(c, (r4.x + 10 + i * 14, r4.y + 15, 10, 4))
            pt.pop_clip()

    # ---------- 選單畫面 ----------
    def draw_list(self, pt, cx, y0, w=420, gap=42, maxrows=None):
        items = self.menu_items()
        if maxrows:
            items = items[:maxrows]
        for i, (bid, label, val) in enumerate(items):
            r = pygame.Rect(int(cx - w / 2), int(y0 + i * gap), int(w), int(gap - 6))
            if r.top > LH - 18:
                break
            on = (i == self.sel)
            pt.panel(r, (20, 26, 44, 232) if on else (8, 11, 20, 190), GOLD if on else EDGE, 7, 2)
            pt.push_clip(r)
            if on:
                pt.glow((r.centerx, r.centery), 40, (60, 90, 170), .28)
                pt.tri(GOLD, (r.x + 14, r.centery), 6, 3)
            vw = 0
            if val:
                vw = 152
                pt.text(("< %s >" % val) if on else val, 17, GOLD if on else CYAN,
                        (r.right - 12, r.centery), "midright", True, maxw=vw - 8)
            pt.text(label, 19, WHT if on else (176, 190, 214), (r.x + 30, r.centery), "midleft",
                    True, maxw=r.w - 48 - vw)
            pt.pop_clip()
            self.btns.append((r, bid))

    def wrap(self, pt, s, size, maxw):
        s = "" if s is None else str(s)
        if not s:
            return []
        out = []
        for part in s.split("\n"):
            cur = ""
            for w in part.split(" "):
                test = (cur + " " + w).strip()
                if pt.tw(test, size) <= maxw or not cur:
                    cur = test
                else:
                    out.append(cur)
                    cur = w
            if cur:
                out.append(cur)
        fin = []
        for ln in out:
            if pt.tw(ln, size) <= maxw:
                fin.append(ln)
                continue
            cur = ""
            for ch in ln:
                if pt.tw(cur + ch, size) <= maxw:
                    cur += ch
                else:
                    fin.append(cur)
                    cur = ch
            if cur:
                fin.append(cur)
        return fin

    def draw_screen(self, pt):
        st = self.state
        self.dim(pt, 126)
        if st == "menu":
            r = pygame.Rect(LW / 2 - 250, 18, 500, LH - 44)
            pt.panel(r, (6, 9, 17, 220), GOLD, 14, 2, True)
            pt.text(T("title"), 46, GOLD, (r.centerx, r.y + 10), "midtop", True, maxw=r.w - 40,
                    glow=(150, 120, 40))
            pt.text(T("sub"), 15, CYAN, (r.centerx, r.y + 58), "midtop", True, maxw=r.w - 80)
            self.draw_list(pt, LW / 2, 100, 400, 38)
            pt.text(T("nav_hint"), 13, (110, 130, 160), (LW / 2, LH - 30), "midtop", True, maxw=LW - 80)
        elif st == "sel":
            r = pygame.Rect(20, 10, LW - 40, LH - 20)
            pt.panel(r, (6, 9, 17, 220), GOLD, 14, 2, True)
            pt.text(T("sel_title"), 28, GOLD, (LW / 2, r.y + 7), "midtop", True, maxw=r.w - 60)
            ch = CHARS[self.c_i]
            wd = WEAPONS[self.w_i]
            box = pygame.Rect(r.x + 20, r.y + 44, 236, 288)
            pt.panel(box, (10, 14, 26, 200), EDGE, 10)
            pt.push_clip(box)
            pt.glow((box.centerx, box.centery), 100, ch["color"], .22)
            if self.preview:
                self.preview.color = ch["color"]
                self.preview.char = ch
                self.preview.ckey = ch["key"]
                self.preview.weapon = wd["key"]
                self.preview.face = 1
                self.preview.on_ground = True
                self.preview.rect.center = (box.centerx, box.centery + 24)
                self.preview.x = self.preview.rect.x
                self.preview.y = self.preview.rect.y
                try:
                    self.preview.draw(pt)
                except Exception:
                    pass
            pt.text(L(ch, "name"), 21, ch["color"], (box.centerx, box.y + 8), "midtop", True,
                    maxw=box.w - 16)
            pt.pop_clip()
            info = pygame.Rect(box.right + 14, r.y + 44, r.right - box.right - 34, 288)
            pt.push_clip(info)
            sx, sy = info.x, info.y + 2
            stats = [(T("atk"), ch["atk"], 105, RED), (T("spd"), ch["speed"], 360, CYAN),
                     (T("hp"), ch["hp"], 34, LIME), (T("sup"), 110 - ch["ult"], 30, GOLD)]
            for i, (nm, v, mx, c) in enumerate(stats):
                pt.text(nm, 15, WHT, (sx, sy + i * 22), "topleft", True, maxw=52)
                pt.bar(pygame.Rect(sx + 56, sy + i * 22 + 2, min(190, info.w - 108), 11),
                       v / float(mx), c, seg=6)
                pt.text(str(int(v)), 13, GREY, (sx + 58 + min(190, info.w - 108) + 8,
                                                sy + i * 22 + 1), "topleft", maxw=44)
            y = sy + 98
            for ln in self.wrap(pt, L(ch, "desc"), 15, info.w - 8)[:2]:
                pt.text(ln, 15, (170, 190, 214), (sx, y), "topleft")
                y += 19
            y += 4
            pt.text("%s: %s" % (T("skill"), L(ch, "sk")), 17, TOXIC, (sx, y), "topleft", True,
                    maxw=info.w - 8)
            y += 22
            for ln in self.wrap(pt, L(ch, "skd"), 14, info.w - 8)[:2]:
                pt.text(ln, 14, (150, 210, 195), (sx, y), "topleft")
                y += 18
            y += 6
            pt.text(L(wd, "name"), 19, wd["color"], (sx, y), "topleft", True, maxw=info.w - 8)
            y += 22
            for ln in self.wrap(pt, L(wd, "desc"), 14, info.w - 8)[:2]:
                pt.text(ln, 14, (166, 182, 204), (sx, y), "topleft")
                y += 18
            pt.text("%s: %s" % (T("alt"), L(wd, "alt")), 14, MAG, (sx, y), "topleft", True,
                    maxw=info.w - 8)
            pt.pop_clip()
            self.draw_list(pt, LW / 2, r.y + 340, 460, 34)
        elif st == "settings":
            r = pygame.Rect(LW / 2 - 280, 24, 560, LH - 48)
            pt.panel(r, (6, 9, 17, 222), GOLD, 14, 2, True)
            pt.text(T("set_title"), 30, GOLD, (r.centerx, r.y + 10), "midtop", True, maxw=r.w - 60)
            for i in range(3):
                pt.line(dk(GOLD, .35), (r.x + 18 + i * 10, r.y + 44), (r.x + 26 + i * 10, r.y + 44), 2)
            self.draw_list(pt, LW / 2, r.y + 54, 480, 42)
            if not self.fonts.cjk:
                pt.text("CJK font not found - English only", 13, AMB,
                        (LW / 2, r.bottom - 24), "midtop", True, maxw=r.w - 40)
        elif st == "help":
            r = pygame.Rect(28, 16, LW - 56, LH - 32)
            pt.panel(r, (6, 9, 17, 224), GOLD, 14, 2, True)
            pt.text(T("help_title"), 30, GOLD, (r.centerx, r.y + 8), "midtop", True, maxw=r.w - 60)
            body = pygame.Rect(r.x + 18, r.y + 46, r.w - 36, r.h - 104)
            pt.push_clip(body)
            lines = [(T("h1"), WHT), (T("h2"), WHT), (T("h3"), WHT), (T("h4"), WHT),
                     ("", WHT),
                     (T("h5"), ICE), (T("h6"), AMB), (T("h7"), MAG), (T("h8"), BLOOD),
                     ("", WHT),
                     (T("h9"), TOXIC), (T("h10"), TOXIC),
                     ("", WHT),
                     (T("h11"), (255, 140, 70)), (T("h12"), VIOL), (T("h13"), CYAN),
                     ("", WHT),
                     (T("h_asset"), GOLD), (self.asset_note, (130, 190, 160))]
            col_w = (body.w - 26) * .5
            x = body.x
            y = body.y
            for s, c in lines:
                if not s:
                    y += 9
                    continue
                for ln in self.wrap(pt, s, 16, col_w):
                    if y > body.bottom - 18:
                        if x > body.x:
                            break
                        x = body.x + col_w + 26
                        y = body.y
                    pt.line(dk(c, .55), (x - 8, y + 9), (x - 3, y + 9), 2)
                    pt.text(ln, 16, c, (x, y), "topleft")
                    y += 20
            pt.pop_clip()
            pt.line(dk(EDGE, 1.0), (body.x + col_w + 13, body.y), (body.x + col_w + 13, body.bottom), 1)
            self.draw_list(pt, LW / 2, r.bottom - 50, 220, 40)

    # ---------- 強化卡 ----------
    def draw_cards(self, pt):
        self.dim(pt, 192)
        pt.text(T("pick_card"), 34, GOLD, (LW / 2, 36), "midtop", True, maxw=LW - 120, glow=GOLD)
        pt.text(T("pick_hint"), 15, CYAN, (LW / 2, 76), "midtop", True, maxw=LW - 140)
        w, h = 250, 306
        rc = {0: (GREY, (10, 13, 22, 236)), 1: (CYAN, (8, 16, 28, 238)), 2: (VIOL, (16, 9, 28, 240))}
        for i, c in enumerate(self.cards):
            x = int(clamp(LW / 2 + (i - 1) * (w + 20) - w / 2, 6, LW - w - 6))
            r = pygame.Rect(x, 112, w, h)
            rar = int(c.get("r", 0))
            bc, fill = rc.get(rar, rc[0])
            pulse = .5 + .5 * math.sin(self.menu_t * 4 + i)
            pt.panel(r, fill, bc, 14, 3, True)
            pt.push_clip(r)
            pt.glow((r.centerx, r.y + 70), 70, c["c"], .22 + pulse * .22)
            # 稜角徽記
            pt.hexa(dk(c["c"], .35), (r.centerx, r.y + 70), 34, 34)
            pt.hexa(c["c"], (r.centerx, r.y + 70), 34, 34, 3)
            pt.ngon(c["c"], (r.centerx, r.y + 70), 16, 16, 4, self.menu_t * .8 + i, 2)
            pt.text(str(i + 1), 30, WHT, (r.centerx, r.y + 70), "center", True, maxw=38)
            # 稀有度
            pt.text(T("rarity%d" % rar), 12, bc, (r.centerx, r.y + 112), "midtop", True, maxw=r.w - 40)
            pt.line(dk(bc, .7), (r.x + 22, r.y + 130), (r.right - 22, r.y + 130), 1)
            y = r.y + 138
            for ln in self.wrap(pt, L(c, "n"), 21, r.w - 26)[:2]:
                pt.text(ln, 21, WHT, (r.centerx, y), "midtop", True)
                y += 25
            y += 8
            for ln in self.wrap(pt, L(c, "d"), 16, r.w - 30)[:4]:
                pt.text(ln, 16, c["c"], (r.centerx, y), "midtop", True)
                y += 20
            for j in range(rar + 1):
                pt.dia(bc, (r.centerx - rar * 7 + j * 14, r.bottom - 16), 4, 5)
            pt.pop_clip()
            self.btns.append((r, "card%d" % i))

    # ---------- 結算 ----------
    def draw_result(self, pt):
        self.dim(pt, 198)
        res = self.result or {}
        win = bool(res.get("win"))
        c = GOLD if win else RED
        pt.text(T("victory") if win else T("gameover"), 52, c, (LW / 2, 44), "midtop", True,
                maxw=LW - 140, glow=c)
        pt.line(dk(c, .8), (LW / 2 - 200, 104), (LW / 2 + 200, 104), 2)
        pt.tri(c, (LW / 2 - 208, 104), 6, 2)
        pt.tri(c, (LW / 2 + 208, 104), 6, 3)
        y = 118
        pt.text(T("r_score", "{:,}".format(int(res.get("score", 0)))), 27, WHT, (LW / 2, y),
                "midtop", True, maxw=520)
        y += 34
        best = self.cfg.get("best", {}).get(self.mode, 0)
        pt.text(T("r_best", "{:,}".format(int(best))), 19, GOLD, (LW / 2, y), "midtop", True, maxw=420)
        y += 26
        if res.get("rec"):
            pt.text(T("r_new"), 23, CYAN, (LW / 2, y), "midtop", True, maxw=380, glow=CYAN)
            y += 30
        for s in (T("r_kills", res.get("kills", 0)),
                  T("r_reach", res.get("stage", 1), res.get("wave", 1)),
                  T("r_time", res.get("time", 0))):
            pt.text(s, 18, (150, 168, 196), (LW / 2, y), "midtop", True, maxw=420)
            y += 23
        pt.text("%s  /  %s  /  %s" % (T("m_" + self.mode), L(CHARS[self.c_i], "name"),
                                      L(WEAPONS[self.w_i], "name")),
                15, (110, 132, 162), (LW / 2, y + 6), "midtop", True, maxw=LW - 160)
        self.draw_list(pt, LW / 2, LH - 112, 300, 42)


# ==============================================================================
async def main():
    try:
        pygame.mixer.pre_init(44100, -16, 2, 512)
    except Exception:
        pass
    await Game().run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except SystemExit:
        pass
    except Exception:
        traceback.print_exc()
    finally:
        try:
            pygame.quit()
        except Exception:
            pass

