"""Model of the vault challenge, used to set how strong mod monsters are (TierRules, set in ContentSetup).

    python3 tools/challenge_sim.py          # the Steam fit, then each tier: normal-game strength and pass rates
    python3 tools/challenge_sim.py --fit    # refit the player population to Steam's numbers (slow)

The aim (firefightermate, 2026-11-08): mod monsters closely match the base game's. In normal games their strength
matches the game's own monsters of the same tier. In vault challenges, at the game's own goals (hero level 4, 7
and 10), players pass them about as often as they pass the game's own challenges of that tier, judged against the
real pass rates on Steam.

The challenge, as the game runs it (SystemLevelChallengeHelper):
  - one room, the player's monster against a bot hero (difficulty 1). He starts at hero level 1 with Vitality,
    Strength and Agility at 0, gains 1 of each and a level weapon every time he dies, and a spell or artifact at
    levels 5, 10, 13, 16, 19 and 22 (Advanced Roll, Hyperdash, Haunted Axe, Follower Cyclone, Book of the Sun,
    Bleeder Shield);
  - each time the monster kills him it heals half its max health; he comes back 50 px or more away, invulnerable
    for 1 s;
  - the score is his level when the monster dies.
Hero numbers (balance row for 2 players): health 8, speed x0.9. Per point of a stat from 5: Vitality +0.8 health,
Strength +8% damage, Agility +2.92 speed, -3.5% attack cooldown, +4% attack speed. The bot dodges damage it
notices within 0 to 0.6 s, about 60% of the time (4 to 5 s on, 3 s off), so long wind-ups miss more as he speeds up.

Each fight the monster loses   hero health x hero damage rate x his evasion / (monster power x accuracy)   of its
health, with noise between fights and between attempts. Monster power is health x damage rate (basic attack and
special) times the player's skill. Skill 1 is an expert: a base-game monster's median score at skill 1 is its goal.

The players: Steam's global achievement rates (steamcommunity.com/stats/293780/achievements, read 2026-11-08) for
passing one vault challenge (11.1% of owners), ten (1.9%), all (0.5%), and the Necromancer (2.0%), Spikewurm (1.5%)
and Gargoyle (1.3%) challenges. Fitted: 77% of owners try challenges, skill is log-normal with median 0.14 of an
expert (sigma 0.7), ten tries per challenge. The fit matches one challenge, the Necromancer and all challenges
closely; it puts ten passes and the Spikewurm and Gargoyle a little high (see the table it prints).
"""
import math
import random
import statistics
import sys

AVOID_ON = 4.5 / 7.5        # share of the time the bot hero is dodging
MARGIN = 12.0               # px he must cover to leave a hitbox once he reacts
REACT = 0.6                 # his reaction time is 0 to this many seconds

# expert calibration per vanilla tier (cost 0, 1, 2.5, 4): power per unit of measured health x damage rate
K = {0: 2.72, 1: 3.19, 2.5: 3.70, 4: 2.69}

# Measured tier medians (health x damage per second, basic attack plus special; the basic attack's wind-up) with
# 1.2.0's numbers. Vanilla from the game's prefabs, ours from the kits.
TIERS = [
    # (name, cost, power in 1.2.0, wind-up, goal)
    ("Starters", 0, 1.82, 0.24, 4),
    ("Tier 2", 2.5, 4.70, 0.28, 7),
    ("Finals", 4, 11.09, 0.28, 10),
]
VANILLA = {0: 3.12, 2.5: 5.59, 4: 10.36}   # the game's own tier medians, same measure

# 1.2.1 (ContentSetup). In every game: starters at least 4 health (x1.14 on the median) and hits x1.45, tier 2
# health x1.1 and hits x1.08, finals unchanged. Inside a challenge only: strength x0.75 / x0.85 / x1.2.
EVERYWHERE = {0: 1.14 * 1.45, 2.5: 1.1 * 1.08, 4: 1.0}
CHALLENGE = {0: 0.75, 2.5: 0.85, 4: 1.2}

# the game's own challenges: (evolve cost, goal) for all 61
GAME_CHALLENGES = [(0, 3), (0, 4), (0, 4), (0, 4), (0, 4), (0, 5), (0, 5), (0, 5), (1, 2), (1, 3), (1, 4), (1, 4),
                   (1, 5), (1, 5), (1, 5), (1, 5), (1, 5), (1, 6), (1, 6), (1, 6), (1, 6), (1, 6), (1, 6), (1, 6),
                   (1, 6), (1, 7), (1, 8), (2.5, 5), (2.5, 6), (2.5, 6), (2.5, 7), (2.5, 7), (2.5, 7), (2.5, 7),
                   (2.5, 7), (2.5, 7), (2.5, 8), (2.5, 8), (2.5, 8), (2.5, 8), (2.5, 8), (2.5, 8), (2.5, 8),
                   (2.5, 8), (2.5, 8), (3.5, 7), (4, 8), (4, 8), (4, 8), (4, 9), (4, 9), (4, 9), (4, 10), (4, 10),
                   (4, 10), (4, 10), (4, 10), (4, 11), (4, 12), (4, 12), (4.5, 10)]
NAMED = {"Necromancer": (2.5, 5), "Spikewurm": (1, 7), "Gargoyle": (0, 5)}
STEAM = {"one": 11.1, "ten": 1.9, "all": 0.5, "Necromancer": 2.0, "Spikewurm": 1.5, "Gargoyle": 1.3}
POPULATION = {"mu": -2.0, "sigma": 0.7, "tries": 10, "share": 0.768}
GRID = [math.exp(i * 0.15 - 3.0) for i in range(30)]   # skill 0.05 to 3.7


def hero(level):
    s = min(20, level - 1)
    health = 8 + 0.8 * (s - 5)
    damage = 1 + 0.08 * (s - 5)
    rate = 1.0 / (0.42 / (1 + 0.04 * (s - 5)) + 0.3 * (1 - 0.035 * (s - 5)))
    weapon = 0.9 if level == 1 else 1.08 if level >= 9 else 1.0
    speed = (73 + 2.92 * (s - 5)) * 0.9
    evade = 1.0
    for at, f in ((5, 1.15), (10, 1.08), (13, 1.1), (16, 1.1), (19, 1.1), (22, 1.05)):
        if level >= at:
            evade *= f
    return health, damage * rate * weapon, speed, evade


def accuracy(windup, level):
    speed = hero(level)[2]
    return 1.0 - AVOID_ON * min(1.0, max(0.0, (windup - MARGIN / speed) / REACT))


def attempt(power, windup, rng, sd=0.45, cap=30):
    health = 1.0
    for level in range(1, cap + 1):
        h, dps, _, evade = hero(level)
        health -= h * dps * evade / (accuracy(windup, level) * power) * math.exp(rng.gauss(0, sd) - sd * sd / 2)
        if health <= 0:
            return level
        health = min(1.0, health + 0.5)
    return cap


def scores(power, windup, n=4000, seed=1):
    rng = random.Random(seed)
    return [attempt(power * math.exp(rng.gauss(0, 0.25)), windup, rng) for _ in range(n)]


def passed(sc, goal):
    return sum(1 for s in sc if s >= goal) / float(len(sc))


def expert_power(goal, windup=0.17):
    """The power at which an expert's median score is the goal (how the game's own challenges are set)."""
    lo, hi = 0.05, 2000.0
    for _ in range(28):
        mid = math.sqrt(lo * hi)
        if statistics.median(scores(mid, windup, n=600, seed=3)) < goal:
            lo = mid
        else:
            hi = mid
    return math.sqrt(lo * hi)


def curve(power, windup, goal, n=800):
    """One attempt's pass chance at each skill on GRID."""
    return [passed(scores(power * s, windup, n=n, seed=11 + i), goal) for i, s in enumerate(GRID)]


def weights(mu, sigma):
    w = [math.exp(-((math.log(s) - mu) / sigma) ** 2 / 2) for s in GRID]
    t = sum(w)
    return [x / t for x in w]


def owners_passing(c, pop=POPULATION):
    """Share of all owners who pass a challenge with pass curve c."""
    w = weights(pop["mu"], pop["sigma"])
    return pop["share"] * sum(wt * (1 - (1 - p) ** pop["tries"]) for wt, p in zip(w, c))


def game_curves():
    cache, out = {}, []
    for cost, goal in GAME_CHALLENGES:
        if goal not in cache:
            cache[goal] = curve(expert_power(goal), 0.17, goal)
        out.append((cost, goal, cache[goal]))
    return out


def steam_table(curves, pop=POPULATION):
    w = weights(pop["mu"], pop["sigma"])
    one = ten = every = 0.0
    for gi, wt in enumerate(w):
        dist = [1.0]
        for _, _, c in curves:
            p = 1 - (1 - c[gi]) ** pop["tries"]
            nd = [0.0] * (len(dist) + 1)
            for j, d in enumerate(dist):
                nd[j] += d * (1 - p)
                nd[j + 1] += d * p
            dist = nd
        one += wt * (1 - dist[0])
        ten += wt * sum(dist[10:])
        every += wt * dist[-1]
    by_goal = {g: c for _, g, c in curves}
    out = {"one": one * pop["share"], "ten": ten * pop["share"], "all": every * pop["share"]}
    for name, (_, goal) in NAMED.items():
        out[name] = owners_passing(by_goal[goal], pop)
    return out


def fit(curves):
    best = None
    for mu in [i * 0.1 - 3.0 for i in range(36)]:
        for sigma in (0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.2, 1.5):
            for tries in (1, 2, 3, 5, 10, 20):
                pop = {"mu": mu, "sigma": sigma, "tries": tries, "share": 1.0}
                t = steam_table(curves, pop)
                share = STEAM["one"] / 100.0 / max(t["one"], 1e-9)
                if share > 1:
                    continue
                err = sum((math.log(max(share * t[k] * 100, 1e-6)) - math.log(STEAM[k])) ** 2 for k in STEAM if k != "one")
                if best is None or err < best[0]:
                    best = (err, dict(pop, share=share))
    return best[1]


if __name__ == "__main__":
    curves = game_curves()
    pop = fit(curves) if "--fit" in sys.argv else POPULATION
    print("Players (median skill %.2f of an expert, sigma %.1f, %d tries, %.0f%% of owners try challenges)" % (
        math.exp(pop["mu"]), pop["sigma"], pop["tries"], pop["share"] * 100))
    t = steam_table(curves, pop)
    for k in STEAM:
        print("  %-12s Steam %4.1f%%   model %4.1f%%" % (k, STEAM[k], t[k] * 100))
    print("\nEach tier: strength in normal games against the game's own tier; share of owners passing one challenge")
    for name, cost, power, windup, goal in TIERS:
        game = [owners_passing(c, pop) for c_cost, _, c in curves
                if (c_cost == 0 if cost == 0 else 2 <= c_cost < 4 if cost == 2.5 else c_cost >= 4)]
        now = power * EVERYWHERE[cost]
        before = owners_passing(curve(K[cost] * power, windup, goal), pop)
        after = owners_passing(curve(K[cost] * now * CHALLENGE[cost], windup, goal), pop)
        print("%-9s normal games %.2f -> %.2f of the game's own.  Challenge (goal %d): game's own %.1f%%, ours %.1f%% -> %.1f%%" % (
            name, power / VANILLA[cost], now / VANILLA[cost], goal, 100 * sum(game) / len(game), before * 100, after * 100))
