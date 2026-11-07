using System;
using System.Collections.Generic;
using System.Text;
using HarmonyLib;
using UnityEngine;

namespace CrawlFurther.UI
{
    using CrawlFurther.Ghosts;
    using CrawlFurther.Gods;
    using CrawlFurther.Util;

    /// <summary>
    /// Adds the <see cref="TipRegistry"/> topics to the game's own Pause > Tips ("GAMEPLAY TIPS"). The vanilla tips are a MenuStateMachine
    /// (MenuPause.m_tips, object "MenuTips"): states TipCombat, TipIdol, TipVitae, TipEctoplasm, TipRooms, Back. Each state
    /// turns one page object on (under "MenuTips/Tips") and the others off; Action / Start goes to the next state, Alt
    /// to the previous one, and Back hands control back to the pause menu. The pages are built from a copy of a vanilla
    /// page (same fonts, colours, tab, rule line and appear effect), one state per page:
    ///   YOU (the monster the pausing player is right now: name, attack, special, passive, the same text as the HUD tip)
    ///   -> the topics of the gods in this game -> the vanilla pages, unchanged -> the <see cref="TipRegistry.TopicOrder"/>
    ///   topics -> every other topic.
    /// Browsing is the vanilla input (so keyboard and controller work alike); on the mod pages Left / Right also jumps
    /// to the previous / next topic. Built per pause (MenuPause is instantiated fresh each time), so the YOU page is
    /// always current. Any failure leaves the vanilla tips untouched.
    /// </summary>
    public static class PauseTips
    {
        /// <summary>
        /// Body: left edge and width in font px (1 px = 1 world unit at the tips' font size, as the vanilla pages are laid
        /// out), and the MiddleLeft anchor height of each line (one TextMesh per line, LinePitch apart: a MiddleLeft
        /// anchor sits 4.3 px above the baseline, the way the vanilla map legend lines up with its icons).
        /// </summary>
        public const float BodyLeft = -94f, BodyWidth = 188f, BodyFirstY = 30f, LinePitch = 7f, FooterY = -24f;
        public const int LinesPerPage = 7;
        // tab row (the vanilla combat page's numbers, in the "Tips" container's frame)
        const float TabY = 39.33f, TabTextY = 40.14f, RuleY = 34.33f, TabW = 43f, VanillaRuleHalf = 68.5f;

        public const string Highlight = "#d4be9c", Label = "#ea9d1a";
        static readonly Color SubtitleColour = new Color(0.69f, 0.584f, 0.431f, 1f);   // #b0956e, the vanilla tip captions
        static readonly Color DimColour = new Color(0.557f, 0.463f, 0.314f, 1f);       // #8e7650, the tab colour

        /// <summary>CrawlTextBodyThin advance widths, chars 32..126 (tools/merge_tips.py has the same table).</summary>
        static readonly byte[] Thin = { 3,2,4,0,4,4,5,2,3,3,2,4,2,4,2,4,4,3,4,4,4,4,4,4,4,4,2,2,4,4,4,4,6,4,4,3,4,3,3,4,4,2,4,4,3,5,
            4,4,4,4,4,4,4,4,4,5,4,4,4,3,4,3,4,4,2,4,4,3,4,4,3,4,4,2,2,4,2,5,4,4,4,4,3,4,3,4,4,5,4,4,4,3,2,3,4 };
        /// <summary>CrawlSmall advance widths (the tab headers).</summary>
        static readonly byte[] Small = { 5,3,4,6,7,0,7,2,4,4,6,6,2,5,2,4,6,4,6,6,6,6,6,6,6,6,2,2,5,4,5,7,7,6,6,5,6,5,5,6,6,3,6,6,5,8,
            6,6,6,6,6,6,5,6,6,8,6,6,6,4,4,4,4,6,2,6,6,5,6,5,5,6,6,3,6,6,5,8,6,6,6,6,6,6,5,6,6,8,6,6,6,0,0,0,0 };
        const string Indent = "  ";
        /// <summary>A space that never breaks a line (merge_tips joins numbers to their units with it); drawn as a space.</summary>
        public const char NoBreak = '~';

        // ------------------------------------------------------------------ text layout (no Unity calls: testable)
        public static int Width(string s, bool small = false)
        {
            var t = small ? Small : Thin;
            int w = 0;
            bool tag = false;
            foreach (char c in s)
            {
                if (c == '<') { tag = true; continue; }
                if (tag) { if (c == '>') tag = false; continue; }
                char d = c == NoBreak ? ' ' : c;
                w += d >= 32 && d < 127 ? t[d - 32] : 4;
            }
            return w;
        }

        /// <summary>
        /// Greedy word wrap of one rich-text paragraph to <see cref="BodyWidth"/>. Tags take no width; a colour tag
        /// still open at a line break is closed there and reopened on the next line; "- " bullets hang.
        /// </summary>
        public static List<string> Wrap(string para, float maxWidth = BodyWidth)
        {
            var lines = new List<string>();
            bool bullet = para.StartsWith("- ", StringComparison.Ordinal);
            string open = null, openAtStart = null;
            var cur = new StringBuilder();
            int curW = 0;
            foreach (var word in para.Split(' '))
            {
                int ww = Width(word), sp = cur.Length > 0 ? Width(" ") : 0;
                if (cur.Length > 0 && curW + sp + ww > maxWidth)
                {
                    lines.Add(Close(openAtStart, cur.ToString(), open));
                    cur.Length = 0;
                    curW = 0;
                    if (bullet) { cur.Append(Indent); curW = Width(Indent); }
                    openAtStart = open;
                    sp = 0;
                }
                if (sp > 0) { cur.Append(' '); curW += sp; }
                cur.Append(word);
                curW += ww;
                open = TagAfter(word, open);
            }
            if (cur.Length > 0) lines.Add(Close(openAtStart, cur.ToString(), open));
            for (int i = 0; i < lines.Count; i++) lines[i] = lines[i].Replace(NoBreak, ' ');
            return lines;
        }

        static string Close(string reopen, string body, string stillOpen)
        {
            return (reopen != null ? reopen : "") + body + (stillOpen != null ? "</color>" : "");
        }

        /// <summary>The colour tag open after <paramref name="word"/> (null if none).</summary>
        static string TagAfter(string word, string open)
        {
            int i = 0;
            while ((i = word.IndexOf('<', i)) >= 0)
            {
                int j = word.IndexOf('>', i);
                if (j < 0) break;
                string tag = word.Substring(i, j - i + 1);
                if (tag.StartsWith("<color", StringComparison.Ordinal)) open = tag;
                else if (tag == "</color>") open = null;
                i = j + 1;
            }
            return open;
        }

        const string ModViolet = "#b383d6";   // the mod gem's violet, lifted for text on the dark page
        public static string Hi(string s) { return "<color=" + Highlight + ">" + s + "</color>"; }

        /// <summary>While pages are built: the ghost button of whoever they are for, highlighted ("C", or "P1 C, P2 X"),
        /// put after each paragraph's "ghost button" (GhostControls.Personalise). Null: the text as written.</summary>
        internal static string GhostName;

        /// <summary>One page: what the tab, subtitle, counter and body show.</summary>
        public class Page
        {
            public string header, subtitle, counter, body;
            public int topic;     // index into the page list's topics (for Left / Right)
        }

        /// <summary>
        /// Split a topic's paragraphs into pages of <see cref="LinesPerPage"/> lines. A paragraph that doesn't fit the
        /// rest of a page starts the next one (unless it is longer than a page anyway). Same rule as merge_tips.py.
        /// </summary>
        public static List<Page> Paginate(string header, string subtitle, IList<string> paras, int topic)
        {
            var chunks = new List<List<string>>();
            var cur = new List<string>();
            foreach (var p0 in paras)
            {
                if (string.IsNullOrEmpty(p0)) continue;
                var p = GhostName != null ? GhostControls.Personalise(p0, GhostName) : p0;
                var lines = Wrap(p);
                if (cur.Count > 0 && cur.Count + lines.Count > LinesPerPage && lines.Count <= LinesPerPage) { chunks.Add(cur); cur = new List<string>(); }
                foreach (var l in lines)
                {
                    if (cur.Count == LinesPerPage) { chunks.Add(cur); cur = new List<string>(); }
                    cur.Add(l);
                }
            }
            if (cur.Count > 0 || chunks.Count == 0) chunks.Add(cur);
            var pages = new List<Page>();
            for (int i = 0; i < chunks.Count; i++)
                pages.Add(new Page
                {
                    header = header, subtitle = subtitle, topic = topic,
                    counter = chunks.Count > 1 ? (i + 1) + "/" + chunks.Count : "",
                    body = string.Join("\n", chunks[i].ToArray()),
                });
            return pages;
        }

        /// <summary>"0.8 s" / "70 px": keep a number and its unit on one line.</summary>
        public static string JoinUnits(string s)
        {
            if (string.IsNullOrEmpty(s)) return s;
            var sb = new StringBuilder(s);
            for (int i = 1; i + 1 < sb.Length; i++)
            {
                if (sb[i] != ' ' || !char.IsDigit(sb[i - 1])) continue;
                int end = i + 1;
                while (end < sb.Length && char.IsLetter(sb[end])) end++;
                string unit = sb.ToString(i + 1, end - i - 1);
                if (unit == "s" || unit == "px") sb[i] = NoBreak;
            }
            return sb.ToString();
        }

        // ------------------------------------------------------------------ content
        static PauseTopic Topic(string id)
        {
            foreach (var t in TipRegistry.Topics) if (t.id == id) return t;
            return null;
        }

        /// <summary>The paragraphs of the "you" page for a player (null: nothing to show).</summary>
        static List<string> YouParas(PlayerData pd, out string subtitle)
        {
            subtitle = null;
            string key = MonsterTips.CurrentKey(pd);
            var paras = new List<string>();
            var go = pd.GameObject;
            var ghostBody = go != null ? go.GetComponent<Player>() : null;
            if (ghostBody != null && !ModUtil.IsGhost(ghostBody)) ghostBody = null;
            // a ghost in a mod form (not one inside a boss part): its paragraph of the ghost pages says more than its tip
            if (ghostBody != null && (key == null || key.IndexOf('/') < 0))
            {
                var form = GhostForms.FormOf != null ? GhostForms.FormOf(pd) : null;
                var gt = form != null && !GhostForms.IsDefault(form) && TipRegistry.GhostFormTopic != null ? Topic(TipRegistry.GhostFormTopic) : null;
                string word = form != null ? ">" + form.id + ":<" : null;
                bool on = false;
                if (gt != null)
                    foreach (var p in gt.paras)
                    {
                        if (p.Contains(word)) on = true;                                   // the form's paragraph...
                        else if (on && !p.StartsWith("- ", StringComparison.Ordinal)) on = false;   // ...and its bullets
                        if (on) paras.Add(p);
                    }
                if (paras.Count > 0)
                {
                    subtitle = "your ghost form";
                    return paras;
                }
            }
            if (key == null) return null;
            var bodyP = pd.GameObject != null ? pd.GameObject.GetComponent<Player>() : null;
            var tip = MonsterTips.TipFor(key, bodyP);
            bool mod = key.StartsWith("Mod", StringComparison.Ordinal);
            string group;
            TipRegistry.Group.TryGetValue(key, out group);
            var godTopic = group != null ? Topic(group) : null;
            subtitle = "the monster you are now" + (godTopic != null && !string.IsNullOrEmpty(godTopic.god) ? " (" + godTopic.god + ")" : "");
            paras.Add(mod ? "<color=" + ModViolet + ">" + tip.name + "</color>" : Hi(tip.name));   // mod monsters: the violet of the mod gem, no tag
            paras.Add("<color=" + Label + ">Attack:</color> " + JoinUnits(tip.attack));
            paras.Add("<color=" + Label + ">Special:</color> " + JoinUnits(tip.special));
            if (!string.IsNullOrEmpty(tip.passive)) paras.Add("<color=" + Label + ">Passive:</color> " + JoinUnits(tip.passive.Replace("\n", " ")));
            if (godTopic != null)
            {
                // the pointer to the god's pages only when the monster page stays one page
                string more = "More on this in the " + godTopic.header + " pages.";
                int used = 1;
                foreach (var p in paras) used += Wrap(p).Count;
                if (used <= LinesPerPage) paras.Add(more);
            }
            return paras;
        }

        class Built
        {
            public readonly List<Page> front = new List<Page>(), back = new List<Page>();
            public int topics;
        }

        static Built Plan(int pausingPlayer)
        {
            var b = new Built();
            // YOU: the pausing player, or every human monster player when the pause came from a shared input
            var you = new List<PlayerData>();
            try
            {
                if (pausingPlayer >= 0) { var pd = SystemPlayers.GetPlayer(pausingPlayer); if (pd != null) you.Add(pd); }
                else
                    foreach (var pd in SystemPlayers.GetPlayers())
                        if (pd != null && pd.IsHuman && !pd.IsHero) you.Add(pd);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Pause tips: player scan failed: " + e.Message); }
            var firstGods = new List<string>();
            foreach (var pd in you)
            {
                string sub = null;
                List<string> paras = null;
                try { if (!pd.IsHero) paras = YouParas(pd, out sub); }
                catch (Exception e) { FurtherCore.Log.LogWarning("Pause tips: monster page failed: " + e.Message); paras = null; }
                if (paras == null) continue;
                string header = you.Count > 1 ? "P" + (pd.Id + 1) : "YOU";
                GhostName = Hi(GhostControls.Name(pd));
                try { b.front.AddRange(Paginate(header, sub, paras, b.topics++)); }
                finally { GhostName = null; }
                AddGod(firstGods, pd);
                string key = MonsterTips.CurrentKey(pd), group;
                if (key != null && TipRegistry.Group.TryGetValue(key, out group))
                {
                    var t = Topic(group);
                    if (t != null && !string.IsNullOrEmpty(t.god) && !firstGods.Contains(t.god)) firstGods.Insert(0, t.god);
                }
            }
            // the gods of everyone in this game (the pausing player's first)
            try { foreach (var pd in SystemPlayers.GetPlayers()) if (pd != null && pd.IsActive) AddGod(firstGods, pd); }
            catch { }
            // in front of the vanilla pages only after a monster page; the hero (or a tips signpost) gets the game's own
            // tips first and the gods of this game right after them
            // every other page names the ghost button of the pausing player (of each human monster player on a shared pause)
            GhostName = Hi(GhostControls.NameFor(you));
            try { PlanShared(b, firstGods); }
            finally { GhostName = null; }
            return b;
        }

        static void PlanShared(Built b, List<string> firstGods)
        {
            var godPages = b.front.Count > 0 ? b.front : b.back;
            var done = new HashSet<string>();
            foreach (var g in firstGods)
                foreach (var t in TipRegistry.Topics)
                    if (t.god == g && done.Add(t.id)) godPages.AddRange(Paginate(t.header, t.subtitle, t.paras, b.topics++));
            // after the vanilla pages: the shared mechanics, then the gods not in this game
            foreach (var id in TipRegistry.TopicOrder)
            {
                var t = Topic(id);
                if (t != null && done.Add(t.id)) b.back.AddRange(Paginate(t.header, t.subtitle, t.paras, b.topics++));
            }
            foreach (var t in TipRegistry.Topics)
                if (done.Add(t.id)) b.back.AddRange(Paginate(t.header, t.subtitle, t.paras, b.topics++));
        }

        static void AddGod(List<string> list, PlayerData pd)
        {
            try
            {
                var d = pd != null ? pd.GetDeity() : null;
                var idolGods = SlotGods.PageGodsOf != null ? SlotGods.PageGodsOf(d) : null;
                if (idolGods != null)
                {
                    // a silver / gold idol: the perk god's page, then the page of every god a starter came from
                    foreach (var n in idolGods) AddGodName(list, n);
                    return;
                }
                AddGodName(list, d != null ? d.GetName() : null);
            }
            catch { }
        }

        static void AddGodName(List<string> list, string n)
        {
            if (string.IsNullOrEmpty(n) || list.Contains(n)) return;
            foreach (var t in TipRegistry.Topics) if (t.god == n) { list.Add(n); return; }
        }

        // ------------------------------------------------------------------ building the pages
        class Parts { public GameObject tab, rule; public TextMesh header, body; }

        static bool IsSmall(TextMesh t) { return t != null && t.font != null && t.font.name.IndexOf("CrawlSmall", StringComparison.OrdinalIgnoreCase) >= 0; }

        /// <summary>A vanilla page with a tab, a rule line, a tab caption (CrawlSmall) and a body text (another font).</summary>
        static Transform FindTemplate(Transform container)
        {
            Transform best = null;
            for (int i = 0; i < container.childCount; i++)
            {
                var c = container.GetChild(i);
                if (c.name.StartsWith("ModTip", StringComparison.Ordinal)) continue;
                if (Pick(c, false) == null) continue;
                if (c.name == "MenuTipVitae") return c;
                if (best == null) best = c;
            }
            return best;
        }

        static Parts Pick(Transform page, bool strip)
        {
            var p = new Parts();
            float bestLen = -1f;
            for (int i = 0; i < page.childCount; i++)
            {
                var c = page.GetChild(i);
                if (p.tab == null && c.name.StartsWith("Tab", StringComparison.Ordinal) && c.GetComponent<exSprite>() != null) p.tab = c.gameObject;
                else if (p.rule == null && c.name.StartsWith("Line", StringComparison.Ordinal) && c.GetComponent<exSprite>() != null) p.rule = c.gameObject;
            }
            if (p.tab == null) return null;
            float bestD = float.MaxValue;
            for (int i = 0; i < page.childCount; i++)
            {
                var t = page.GetChild(i).GetComponent<TextMesh>();
                if (t == null) continue;
                if (IsSmall(t))
                {
                    float d = (t.transform.localPosition - p.tab.transform.localPosition).sqrMagnitude;
                    if (d < bestD) { bestD = d; p.header = t; }
                }
                else if (t.text != null && t.text.Length > bestLen) { bestLen = t.text.Length; p.body = t; }
            }
            if (p.header == null || p.body == null || p.rule == null) return null;
            if (strip)
            {
                var drop = new List<GameObject>();
                for (int i = 0; i < page.childCount; i++)
                {
                    var g = page.GetChild(i).gameObject;
                    if (g != p.tab && g != p.rule && g != p.header.gameObject && g != p.body.gameObject) drop.Add(g);
                }
                foreach (var g in drop) UnityEngine.Object.DestroyImmediate(g);
            }
            return p;
        }

        static TextMesh CloneText(TextMesh src, Transform parent, string name)
        {
            // made straight under the (inactive) page: never enabled at the scene root, so its appear effect only
            // runs when the page is shown
            var go = (GameObject)UnityEngine.Object.Instantiate(src.gameObject, parent, false);
            go.name = name;
            return go.GetComponent<TextMesh>();
        }

        static void Place(Component c, float x, float y)
        {
            var p = c.transform.localPosition;
            c.transform.localPosition = new Vector3(x, y, p.z);
        }

        static GameObject BuildPage(Transform container, Transform proto, Page pg, int index)
        {
            var go = (GameObject)UnityEngine.Object.Instantiate(proto.gameObject, container, false);
            go.name = "ModTip" + index;
            var pz = proto.localPosition.z;
            go.transform.localPosition = new Vector3(0f, 0f, pz);
            var parts = Pick(go.transform, false);

            // the tab, doubled up when the caption is wider than one tab
            int hw = Width(pg.header, true);
            float tabW = Mathf.Max(TabW, hw + 8f);
            float left = BodyLeft - 2f, centre = Mathf.Round(left + tabW * 0.5f);
            Place(parts.tab.transform, Mathf.Round(left + TabW * 0.5f), TabY);
            if (tabW > TabW)
            {
                var t2 = (GameObject)UnityEngine.Object.Instantiate(parts.tab, go.transform, false);
                t2.name = "Tab2";
                Place(t2.transform, Mathf.Round(left + tabW - TabW * 0.5f), TabY);
            }
            parts.header.text = pg.header;
            Place(parts.header, centre + (hw % 2 == 1 ? 0.5f : 0f), TabTextY);

            // the rule under the tab row, as wide as the body
            Place(parts.rule.transform, 0f, RuleY);
            var rs = parts.rule.transform.localScale;
            parts.rule.transform.localScale = new Vector3(rs.x * (BodyWidth * 0.5f + 2f) / VanillaRuleHalf, rs.y, rs.z);

            float tabRight = left + tabW;
            if (!string.IsNullOrEmpty(pg.subtitle))
            {
                var sub = CloneText(parts.body, go.transform, "Subtitle");
                sub.richText = false;
                sub.anchor = TextAnchor.MiddleLeft;
                sub.lineSpacing = 1f;
                sub.alignment = TextAlignment.Left;
                sub.color = SubtitleColour;
                sub.text = pg.subtitle;
                Place(sub, tabRight + 4f, TabTextY - 0.5f);
            }
            if (!string.IsNullOrEmpty(pg.counter))
            {
                var cnt = CloneText(parts.body, go.transform, "Counter");
                cnt.richText = false;
                cnt.anchor = TextAnchor.MiddleRight;
                cnt.alignment = TextAlignment.Right;
                cnt.color = DimColour;
                cnt.text = pg.counter;
                Place(cnt, BodyLeft + BodyWidth, TabTextY - 0.5f);
            }
            var foot = CloneText(parts.body, go.transform, "Footer");
            foot.richText = false;
            foot.anchor = TextAnchor.MiddleLeft;
            foot.alignment = TextAlignment.Left;
            foot.color = DimColour;
            foot.text = "Left / Right: skip to the previous / next topic";
            Place(foot, BodyLeft, FooterY);

            // one text per line: the layout never depends on how a TextMesh spaces several lines
            var lines = pg.body.Split('\n');
            for (int i = 0; i < lines.Length; i++)
            {
                var ln = i == 0 ? parts.body : CloneText(parts.body, go.transform, "Line" + i);
                ln.name = "Body" + i;
                ln.richText = true;
                ln.anchor = TextAnchor.MiddleLeft;
                ln.alignment = TextAlignment.Left;
                ln.lineSpacing = 1f;
                ln.text = lines[i];
                Place(ln, BodyLeft, BodyFirstY - i * LinePitch);
            }

            try
            {
                if (Singleton<SystemLevel>.HasInstance())
                    foreach (var s in go.GetComponentsInChildren<exSprite>(true)) s.renderCamera = SystemLevel.GetCameraGUI();
            }
            catch { }
            return go;
        }

        static MenuState MakeState(string name, GameObject page)
        {
            return new MenuState
            {
                m_name = name, m_nextState = string.Empty, m_backState = string.Empty,
                m_transitionOnInput = true, m_backTransitionOnInput = true,
                m_turnOn = new List<GameObject> { page }, m_turnOff = new List<GameObject>(),
                m_animate = new List<MenuStateActionAnimate>(), m_actions = new List<MenuStateAction>(),
            };
        }

        /// <summary>MenuPause.Start: add the mod's pages to this pause menu's tips (once per instance).</summary>
        public static void Inject(MenuPause pause)
        {
            var tips = R.Get<MenuStateMachine>(pause, "m_tips");
            if (tips == null || tips.GetComponent<PauseTipsNav>() != null) return;
            if (TipRegistry.Topics.Count == 0) return;
            var container = tips.transform.Find("Tips");
            var states = tips.m_states;
            if (container == null || states == null || states.Count == 0) { FurtherCore.Log.LogWarning("Pause tips: no tips container"); return; }
            var template = FindTemplate(container);
            if (template == null) { FurtherCore.Log.LogWarning("Pause tips: no vanilla page to copy"); return; }

            var made = new List<GameObject>();
            GameObject proto = null;
            try
            {
                var plan = Plan(R.Get<int>(pause, "m_playerId"));
                // made under the (inactive) tips object, so nothing on the copy wakes up
                proto = (GameObject)UnityEngine.Object.Instantiate(template.gameObject, container, false);
                proto.name = "ModTipProto";
                proto.SetActive(false);
                if (Pick(proto.transform, true) == null) throw new Exception("template parts missing");

                var frontStates = new List<MenuState>();
                var backStates = new List<MenuState>();
                var topicOf = new Dictionary<MenuState, int>();
                int n = 0;
                foreach (var list in new[] { plan.front, plan.back })
                    foreach (var pg in list)
                    {
                        var page = BuildPage(container, proto.transform, pg, n);
                        page.SetActive(false);
                        made.Add(page);
                        var st = MakeState("ModTip" + n, page);
                        topicOf[st] = pg.topic;
                        (list == plan.front ? frontStates : backStates).Add(st);
                        n++;
                    }
                UnityEngine.Object.DestroyImmediate(proto);
                proto = null;
                if (made.Count == 0) return;

                // every page off in every state but its own
                var vanillaPages = new List<GameObject>();
                foreach (var s in states)
                    if (s != null && s.m_turnOn != null)
                        foreach (var g in s.m_turnOn) if (g != null && g.transform.parent == container && !vanillaPages.Contains(g)) vanillaPages.Add(g);
                foreach (var st in frontStates.ConcatWith(backStates))
                {
                    st.m_turnOff.AddRange(vanillaPages);
                    foreach (var g in made) if (g != st.m_turnOn[0]) st.m_turnOff.Add(g);
                }
                foreach (var s in states)
                {
                    if (s == null) continue;
                    if (s.m_turnOff == null) s.m_turnOff = new List<GameObject>();
                    s.m_turnOff.AddRange(made);
                }

                // order: [you + gods in play] vanilla pages [status, ghosts, other gods] Back
                int back = tips.GetStateId("Back");
                if (back < 0) back = states.Count;
                if (frontStates.Count > 0)
                {
                    var first = states[0];
                    frontStates[0].m_backState = first.m_backState;   // Alt on the first page leaves, as before
                    if (first.m_backState == "Back") first.m_backState = string.Empty;   // ...and the old first page now steps back
                }
                states.InsertRange(back, backStates);
                states.InsertRange(0, frontStates);
                foreach (var s in states)
                {
                    if (s == null) continue;
                    s.m_nextStateId = string.IsNullOrEmpty(s.m_nextState) ? -1 : tips.GetStateId(s.m_nextState);
                    s.m_backStateId = string.IsNullOrEmpty(s.m_backState) ? -1 : tips.GetStateId(s.m_backState);
                }

                var topics = new int[states.Count];
                for (int i = 0; i < states.Count; i++)
                {
                    int t;
                    topics[i] = states[i] != null && topicOf.TryGetValue(states[i], out t) ? t : -1000 - i;   // vanilla: one topic per page
                }
                var nav = tips.gameObject.AddComponent<PauseTipsNav>();
                nav.Setup(tips, R.Get<int>(pause, "m_playerId"), topics);
                FurtherCore.Log.LogInfo("Pause tips: " + made.Count + " mod pages (" + frontStates.Count + " before the game's own, " + backStates.Count + " after)");
            }
            catch (Exception e)
            {
                FurtherCore.Log.LogError("Pause tips failed, the game's own tips are left as they were: " + e);
                if (proto != null) UnityEngine.Object.DestroyImmediate(proto);
                foreach (var g in made) if (g != null) UnityEngine.Object.DestroyImmediate(g);
                // undo any state edits
                states.RemoveAll(s => s != null && s.m_name != null && s.m_name.StartsWith("ModTip", StringComparison.Ordinal));
                foreach (var s in states) if (s != null && s.m_turnOff != null) s.m_turnOff.RemoveAll(g => g == null);
            }
        }

        static IEnumerable<T> ConcatWith<T>(this List<T> a, List<T> b)
        {
            foreach (var x in a) yield return x;
            foreach (var x in b) yield return x;
        }
    }

    [HarmonyPatch(typeof(MenuPause), "Start")]
    static class Patch_PauseTipsInject
    {
        static void Postfix(MenuPause __instance)
        {
            try { PauseTips.Inject(__instance); }
            catch (Exception e) { FurtherCore.Log.LogError("Pause tips inject failed: " + e); }
        }
    }

    /// <summary>
    /// Opening Tips a second time in one pause found the tips still on their closing "Back" state (an empty panel).
    /// Start them again from the first page.
    /// </summary>
    [HarmonyPatch(typeof(MenuPause), "MsgTips")]
    static class Patch_PauseTipsReopen
    {
        static void Postfix(MenuPause __instance)
        {
            try
            {
                var tips = R.Get<MenuStateMachine>(__instance, "m_tips");
                if (tips != null && tips.GetState() >= 0 && tips.GetStateName() == "Back") tips.SetState(0);
            }
            catch (Exception e) { FurtherCore.Log.LogWarning("Pause tips reopen: " + e.Message); }
        }
    }
}
