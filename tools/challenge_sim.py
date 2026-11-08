"""Model of the vault challenge, used to set how strong mod monsters are (TierRules, set in ContentSetup).

    python3 tools/challenge_sim.py            # pass rates by skill for every tier, 1.2.0 numbers and now
    python3 tools/challenge_sim.py --needed   # how much stronger each tier must be for the goals

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
special), times the player's skill.

Calibration:
  - expert: one constant per vanilla tier makes the median score equal the game's own goal (K below). One
    constant fits all four tiers within 17%, which is the check that the hero's growth is modelled right.
  - moderate: 0.38 of the expert. Both scores players sent in fit it: the Tallow Grub (1.2.0 numbers) best 2,
    the Pyre Warden best 4 to 5.
  - Steam's global stats agree that the game's goals are for experts: 11% of players have passed one vault
    challenge, 1.8% ten of them.

The goals stay the game's own (4, 7 and 10). The rule: a moderate player passes the median monster of each tier in
half of all runs of five tries. That takes 1.5x the strength for starters, 1.75x for tier 2 and 2.25x for finals.
Half of it (on a log scale) applies in every game, the other half only inside a challenge (ChallengeBoost).
"""
import math
import random
import statistics
import sys

AVOID_ON = 4.5 / 7.5        # share of the time the bot hero is dodging
MARGIN = 12.0               # px he must cover to leave a hitbox once he reacts
REACT = 0.6                 # his reaction time is 0 to this many seconds

# expert calibration per vanilla tier (cost 0, 1, 2.5, 4): median score = the game's goal
K = {0: 2.72, 1: 3.19, 2.5: 3.70, 4: 2.69}
GAME_GOAL = {0: 4.2, 1: 5.3, 2.5: 7.3, 4: 9.7}
SKILL = {"new": 0.2, "moderate": 0.38, "skilled": 0.6, "expert": 1.0}

# Measured tier medians before 1.2.1 (health x damage per second, basic attack plus special; the basic attack's
# wind-up). Vanilla from the game's prefabs, ours from the kits.
TIERS = [
    # (name, cost, power before 1.2.1, wind-up, goal)
    ("Starters", 0, 1.82, 0.24, 4),
    ("Tier 2", 2.5, 4.70, 0.28, 7),
    ("Finals", 4, 11.09, 0.28, 10),
]
VANILLA = {0: 3.12, 2.5: 5.59, 4: 10.36}   # the game's own tier medians, same measure

# 1.2.1 (ContentSetup): health x hits in every game, then the challenge-only boost.
# Starters: health floor 4 (x1.14 on the median), hits x1.45, health x1.1.
EVERYWHERE = {0: 1.14 * 1.45 * 1.1, 2.5: 1.15 * 1.15, 4: 1.2 * 1.25}
CHALLENGE = {0: 1.25, 2.5: 1.32, 4: 1.5}

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


def best_of(sc, k, seed=7):
    rng = random.Random(seed)
    return [max(rng.choice(sc) for _ in range(k)) for _ in sc]


def passed(sc, goal):
    return sum(1 for s in sc if s >= goal) / float(len(sc))


def table(name, power, windup, k, goal):
    print("  goal %d:" % goal + "".join("  %s %3.0f%% / %3.0f%% / %3.0f%%" % (
        s, 100 * passed(sc, goal), 100 * passed(best_of(sc, 5), goal), 100 * passed(best_of(sc, 20), goal))
        for s, sc in ((s, scores(k * power * f, windup)) for s, f in SKILL.items())))


def needed(power, windup, k, goal):
    for m in [1 + 0.05 * i for i in range(80)]:
        if passed(best_of(scores(k * power * m * SKILL["moderate"], windup), 5), goal) >= 0.5:
            return m
    return None


if __name__ == "__main__":
    if "--needed" in sys.argv:
        for name, cost, power, windup, goal in TIERS:
            print("%-9s goal %d: x%.2f the 1.2.0 strength" % (name, goal, needed(power, windup, K[cost], goal)))
        sys.exit(0)
    print("Chance to pass in 1 / 5 / 20 attempts, by skill (median monster of each tier)")
    for name, cost, power, windup, goal in TIERS:
        now = power * EVERYWHERE[cost]
        print("%s, goal %d. In normal games: %.2f of the game's own tier before, %.2f now" % (
            name, goal, power / VANILLA[cost], now / VANILLA[cost]))
        print(" 1.2.0:")
        table(name, power, windup, K[cost], goal)
        print(" now, in a challenge:")
        table(name, now * CHALLENGE[cost], windup, K[cost], goal)
