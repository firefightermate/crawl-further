using System.Collections.Generic;
using System.Reflection;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.Testing
{
    using CrawlFurther.Heroes;
    using CrawlFurther.Monsters;
    using CrawlFurther.Objects;
    using CrawlFurther.Util;

    /// <summary>
    /// The game calls behind the test panel's actions, public so other mods' test actions can use them. Each one does
    /// what the game itself does for the same thing (its debug keys and menu, a death, a level end) rather than a
    /// copy of it. Calls that cannot run right now throw <see cref="TestModeException"/> with the reason.
    /// </summary>
    public static class TestGame
    {
        static readonly MethodInfo s_openDoors = AccessTools.Method(typeof(SystemLevel), "DebugOpenDoors");
        static readonly MethodInfo s_reload = AccessTools.Method(typeof(SystemLevel), "DebugReloadLevel");
        static readonly MethodInfo s_endLevel = AccessTools.Method(typeof(SystemLevel), "DebugEndLevel");
        static readonly MethodInfo s_toStore = AccessTools.Method(typeof(SystemLevel), "DebugTeleportToStore");
        static readonly MethodInfo s_toPortal = AccessTools.Method(typeof(SystemLevel), "DebugTeleportToPortal");
        static readonly FieldInfo s_bossEncounter = AccessTools.Field(typeof(SystemLevel), "m_bossEncounter");
        static readonly FieldInfo s_floor = AccessTools.Field(typeof(SystemGame), "m_level");

        /// <summary>The members above, for the self-test (a game update that renames one breaks only that action).</summary>
        internal static IEnumerable<KeyValuePair<string, MemberInfo>> Hooks()
        {
            yield return new KeyValuePair<string, MemberInfo>("SystemLevel.DebugOpenDoors", s_openDoors);
            yield return new KeyValuePair<string, MemberInfo>("SystemLevel.DebugReloadLevel", s_reload);
            yield return new KeyValuePair<string, MemberInfo>("SystemLevel.DebugEndLevel", s_endLevel);
            yield return new KeyValuePair<string, MemberInfo>("SystemLevel.DebugTeleportToStore", s_toStore);
            yield return new KeyValuePair<string, MemberInfo>("SystemLevel.DebugTeleportToPortal", s_toPortal);
            yield return new KeyValuePair<string, MemberInfo>("SystemLevel.m_bossEncounter", s_bossEncounter);
            yield return new KeyValuePair<string, MemberInfo>("SystemGame.m_level", s_floor);
        }

        /// <summary>Test mode slots this session has filled with bots (see <see cref="SpawnHostile"/>).</summary>
        static readonly List<int> s_bots = new List<int>();

        // ------------------------------------------------------------------ where we are

        /// <summary>True while a floor is being played (a level is loaded and has a hero).</summary>
        public static bool InLevel
        {
            get { return Singleton<SystemLevel>.HasInstance() && SystemLevel.GetHeroObject() != null && SystemLevel.GetCurrentRoom() != null; }
        }

        static SystemLevel Level()
        {
            if (!InLevel) throw new TestModeException("Start a run first");
            return Singleton<SystemLevel>.Get;
        }

        static GameObject HeroBody()
        {
            Level();
            return SystemLevel.GetHeroObject();
        }

        /// <summary>The body of <paramref name="pd"/>, which must be a player in the game who is not the hero.</summary>
        static GameObject MonsterPlayerBody(PlayerData pd)
        {
            Level();
            if (pd == null) throw new TestModeException("No monster player to act for: join one, or pick one at the top");
            if (pd.IsHero) throw new TestModeException("That player is the hero: pick a monster player at the top");
            if (pd.GameObject == null) throw new TestModeException("That player has no body or ghost right now");
            return pd.GameObject;
        }

        /// <summary>A free point about 40 pixels beside the hero, short of any wall (where the Spawn page puts things).</summary>
        public static Vector3 BesideHero()
        {
            Vector2 at = HeroBody().transform.position;
            Vector2 to = ModUtil.SafePoint(at, at + new Vector2(40f, 0f), 10f);
            if ((to - at).sqrMagnitude < 100f) to = ModUtil.SafePoint(at, at + new Vector2(-40f, 0f), 10f);
            return new Vector3(to.x, to.y, 0f);
        }

        // ------------------------------------------------------------------ bodies

        /// <summary>
        /// Put <paramref name="pd"/> (a monster player or ghost) into a new body of <paramref name="prefab"/> where it
        /// stands, in the current room. This is the game's own debug swap (SystemLevel's Tab + M key): spawn the new
        /// body, let the old one go, and InitAsPlayer the new one. Returns the new body.
        /// </summary>
        public static GameObject Become(PlayerData pd, GameObject prefab)
        {
            var old = MonsterPlayerBody(pd);
            var at = old.transform.position;
            at.z = 0f;
            return Swap(pd, prefab, at);
        }

        static GameObject Swap(PlayerData pd, GameObject prefab, Vector3 at)
        {
            if (prefab == null || prefab.GetComponent<Player>() == null) throw new TestModeException("That is not a monster");
            var lvl = Level();
            var old = pd.GameObject;
            bool flip = old != null && old.transform.localScale.x < 0f;
            var go = prefab.Spawn(at);
            if (old != null)
            {
                if (pd.IsAlive) lvl.OnMonsterDespawned(old);
                old.Despawn();
            }
            go.GetComponent<Player>().InitAsPlayer(pd);
            if (flip) go.transform.localScale = new Vector3(-Mathf.Abs(go.transform.localScale.x), go.transform.localScale.y, go.transform.localScale.z);
            CloseDoors();
            return go;
        }

        /// <summary>
        /// Make <paramref name="pd"/> a ghost: a monster body dies the normal way (so its ghost form and death effects
        /// play); a ghost is replaced by a fresh one of the player's current form.
        /// </summary>
        public static void BecomeGhost(PlayerData pd)
        {
            var body = MonsterPlayerBody(pd);
            if (pd.IsAlive)
            {
                var h = body.GetComponent<Health>();
                if (h == null) throw new TestModeException("That body cannot die");
                h.Suicide();
                return;
            }
            var at = body.transform.position;
            body.Despawn();
            pd.OnGameObjectUnassigned();
            Level().SpawnGhost(pd, (Vector2)at, 0f);
        }

        /// <summary>
        /// Make <paramref name="pd"/> the hero the way the game does it: their monster kills the hero, and the hero change
        /// plays out (the old hero's player becomes a ghost).
        /// </summary>
        public static void BecomeHero(PlayerData pd)
        {
            var body = MonsterPlayerBody(pd);
            if (!pd.IsAlive) throw new TestModeException("A ghost cannot take the crown: become a monster first");
            var hero = HeroBody().GetComponent<Health>();
            if (SystemLevel.GetBossEncounterActive()) throw new TestModeException("Not during a boss fight");
            hero.InstaKill(new DamageInfo(hero.GetHealthCurrent() + 1f, 0f, 0f, Vector2.zero, new DamageSource(body, body, pd)));
        }

        /// <summary>
        /// Set <paramref name="pd"/>'s hero origin (index into HeroClasses.All) and apply it. Stats and the starting
        /// weapon apply while the player is not the hero; the hero gets the origin's modifiers and items now.
        /// </summary>
        public static void SetOrigin(PlayerData pd, int index)
        {
            if (pd == null) throw new TestModeException("No player picked");
            if (index < 0 || index >= HeroClasses.All.Count) throw new TestModeException("No such origin");
            HeroClasses.Chosen[pd.Id] = index;
            HeroClasses.Apply(pd);
        }

        // ------------------------------------------------------------------ spawning

        /// <summary>
        /// Spawn a hostile <paramref name="prefab"/> beside the hero. Monsters with their own AI (fodder, blobs) run it;
        /// any other monster is given to a bot in a free player slot, so it fights with its real moves. Returns the body.
        /// </summary>
        public static GameObject SpawnHostile(GameObject prefab)
        {
            var at = BesideHero();
            var p = prefab != null ? prefab.GetComponent<Player>() : null;
            if (p == null) throw new TestModeException("That is not a monster");
            if (prefab.GetComponent<PlayerAI>() != null)
            {
                var go = prefab.Spawn(at);
                go.GetComponent<Player>().InitAsAI(null);
                CloseDoors();
                return go;
            }
            int slot = FreeSlot();
            if (slot < 0) throw new TestModeException("All four player slots are in use: remove the test bots first");
            Singleton<SystemPlayers>.Get.AssignBot(slot);
            if (!s_bots.Contains(slot)) s_bots.Add(slot);
            return Swap(SystemPlayers.GetPlayer(slot), prefab, at);
        }

        static int FreeSlot()
        {
            for (int i = 0; i < SystemPlayers.GetMaxPlayers(); i++)
            {
                var p = SystemPlayers.GetPlayer(i);
                if (p != null && !p.IsActive) return i;
            }
            return -1;
        }

        /// <summary>Take out the bots <see cref="SpawnHostile"/> added (not one that has become the hero). Returns how many.</summary>
        public static int RemoveTestBots()
        {
            int n = 0;
            foreach (var slot in s_bots.ToArray())
            {
                var pd = SystemPlayers.GetPlayer(slot);
                if (pd == null || !pd.IsActive || !pd.IsBot) { s_bots.Remove(slot); continue; }
                if (pd.IsHero) continue;
                var go = pd.GameObject;
                if (go != null)
                {
                    var p = go.GetComponent<Player>();
                    if (pd.IsAlive && p != null) p.Despawn();
                    else go.Despawn();
                    pd.OnGameObjectUnassigned();
                }
                Singleton<SystemPlayers>.Get.UnassignPlayer(slot);
                s_bots.Remove(slot);
                n++;
            }
            return n;
        }

        /// <summary>Place a registered room object (ObjectKit id) beside the hero.</summary>
        public static GameObject PlaceObject(string id)
        {
            var go = ObjectKit.SpawnAt(id, SystemLevel.GetCurrentRoom(), BesideHero());
            if (go == null) throw new TestModeException("No space for it here (room objects never go in a boss room)");
            return go;
        }

        /// <summary>Give the hero an item or spell, as a god's starting gift would (not counted as a vault find).</summary>
        public static void GiveItem(Powerup item)
        {
            HeroBody();
            if (item == null) throw new TestModeException("No such item");
            if (Powerup.Collect(item, SystemPlayers.GetHeroPlayerData(), fromDeity: true) == null)
                throw new TestModeException("The hero cannot take that one (already held, or not for this hero)");
        }

        /// <summary>Put a weapon in the hero's hands; <paramref name="combo"/> picks a named variant, null the default.</summary>
        public static void GiveWeapon(Weapon weapon, string combo = null)
        {
            var hero = HeroBody().GetComponent<Player>();
            if (weapon == null) throw new TestModeException("No such weapon");
            var wd = new WeaponData();
            if (string.IsNullOrEmpty(combo)) wd.Init(weapon); else wd.Init(weapon, combo);
            hero.ChangeWeapon(wd);
        }

        // ------------------------------------------------------------------ the run

        /// <summary>Give <paramref name="pd"/> another god mid-run (PlayerData.SetDeity, as the god select does). Their
        /// monster tree, perks and starting gold become the new god's.</summary>
        public static void SetGod(PlayerData pd, Deity god)
        {
            if (pd == null) throw new TestModeException("No player picked");
            if (god == null) throw new TestModeException("No such god");
            pd.SetDeity(god);
        }

        /// <summary>End this floor (as reaching the stairs does) so the next one is floor <paramref name="floor"/>.
        /// The evolve screen still comes first.</summary>
        public static void GoToFloor(int floor)
        {
            var lvl = Level();
            if (!Singleton<SystemGame>.HasInstance()) throw new TestModeException("Start a run first");
            s_floor.SetValue(Singleton<SystemGame>.Get, Mathf.Max(0, floor - 1));
            s_endLevel.Invoke(lvl, null);
        }

        /// <summary>End this floor as reaching the stairs does.</summary>
        public static void NextFloor() { s_endLevel.Invoke(Level(), null); }

        /// <summary>Open the boss portal now with <paramref name="boss"/> (null: the boss the game would pick).</summary>
        public static void GoToBoss(Boss boss)
        {
            var lvl = Level();
            var enc = s_bossEncounter.GetValue(lvl) as BossEncounter;
            if (enc == null) throw new TestModeException("This floor has no boss encounter");
            if (enc.GetActive()) throw new TestModeException("A boss fight is already on");
            enc.Start(SystemLevel.GetCurrentRoom(), null, boss);
        }

        /// <summary>Open the room's doors and take out the monsters in it (the game's own Open Doors).</summary>
        public static void OpenDoors() { s_openDoors.Invoke(Level(), null); }

        /// <summary>Load this floor again (the game's own Reload Level).</summary>
        public static void ReloadLevel() { s_reload.Invoke(Level(), null); }

        /// <summary>Move the hero to the shop (the game's own Go To Store).</summary>
        public static void GoToStore() { s_toStore.Invoke(Level(), null); }

        /// <summary>Move the hero to the portal room (the game's own Go To Portal).</summary>
        public static void GoToPortal() { s_toPortal.Invoke(Level(), null); }

        /// <summary>Move the hero through a door of this room: to a room not seen yet when there is one.</summary>
        public static void NextRoom()
        {
            var lvl = Level();
            var here = SystemLevel.GetCurrentRoom();
            Room pick = null;
            foreach (var door in here.m_doors)
            {
                if (door == null || door.m_room == null || door.m_room == here) continue;
                if (pick == null || (!door.m_room.GetSeenRoom() && pick.GetSeenRoom())) pick = door.m_room;
            }
            if (pick == null) throw new TestModeException("This room has no other room to go to");
            HeroBody().transform.position = pick.transform.position;
            lvl.OnTeleportToRoom(pick);
        }

        static void CloseDoors()
        {
            var room = SystemLevel.GetCurrentRoom();
            if (room != null && !room.m_isPowerupRoom) room.CloseDoors();
        }

        // ------------------------------------------------------------------ players

        /// <summary>Every player gains a level and evolves (the game's own Increment Lvl + Evolve).</summary>
        public static void LevelUpAll()
        {
            Level();
            Singleton<SystemPlayers>.Get.DebugSimulateLevelIncrease();
        }

        /// <summary>Every player jumps to level 10 and evolves as far as it can (the game's own Skip to Lvl 10).</summary>
        public static void SkipToLevel10()
        {
            Level();
            Singleton<SystemPlayers>.Get.DebugSkipToLevel10();
        }

        /// <summary>Raise the hero to <paramref name="level"/> through the normal level-ups. Levels never go down.</summary>
        public static void SetHeroLevel(int level)
        {
            HeroBody();
            var gd = SystemPlayers.GetHeroPlayerData().GameData;
            if (level <= gd.Level) throw new TestModeException("The hero is already level " + gd.Level + "; levels only go up");
            gd.TutorialSetLevel(level);
        }

        /// <summary>Add gold to a player.</summary>
        public static void AddGold(PlayerData pd, int amount)
        {
            if (pd == null) throw new TestModeException("No player picked");
            pd.OnGoldCollected(amount);
        }

        /// <summary>Heal a player's body to full. False when there is no living body.</summary>
        public static bool FullHeal(PlayerData pd)
        {
            if (pd == null || pd.GameObject == null || !pd.IsAlive) return false;
            var h = pd.GameObject.GetComponent<Health>();
            if (h == null || h.IsDead()) return false;
            h.Heal(h.GetHealthMax());
            return true;
        }

        // ------------------------------------------------------------------ trees

        /// <summary>
        /// A god's monsters with their tier (1 = starters), following each monster's evolutions as deep as they go
        /// (vanilla trees are four deep, Crawl: Further's three). Each monster is listed once, at its first tier.
        /// </summary>
        public static List<KeyValuePair<GameObject, int>> Tree(Deity god)
        {
            var list = new List<KeyValuePair<GameObject, int>>();
            if (god == null) return list;
            var seen = new HashSet<GameObject>();
            var frontier = new List<GameObject>();
            var starters = god.GetStartingMonsters();
            if (starters != null) foreach (var s in starters) if (s != null) frontier.Add(s);
            for (int tier = 1; tier <= 8 && frontier.Count > 0; tier++)
            {
                var next = new List<GameObject>();
                foreach (var go in frontier)
                {
                    if (!seen.Add(go)) continue;
                    list.Add(new KeyValuePair<GameObject, int>(go, tier));
                    var p = go.GetComponent<Player>();
                    var evolve = p != null ? p.GetEvolveTo() : null;
                    if (evolve != null) foreach (var e in evolve) if (e != null) next.Add(e.gameObject);
                }
                frontier = next;
            }
            return list;
        }

        /// <summary>Every monster prefab the game and the mods know: the vault's monster list plus every built mod monster.</summary>
        public static List<GameObject> AllMonsters()
        {
            var list = new List<GameObject>();
            var seen = new HashSet<GameObject>();
            if (Singleton<SystemLibrary>.HasInstance())
                foreach (var e in SystemLibrary.GetMonsters())
                    if (e != null && e.m_prefab != null && e.m_prefab.GetComponent<Player>() != null && seen.Add(e.m_prefab)) list.Add(e.m_prefab);
            foreach (var p in MonsterFactory.Built.Values)
                if (p != null && seen.Add(p.gameObject)) list.Add(p.gameObject);
            return list;
        }
    }
}
