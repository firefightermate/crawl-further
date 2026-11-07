using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;

namespace CrawlFurther.Content.Library
{
    using CrawlFurther.Art;
    using CrawlFurther.Ghosts;
    using CrawlFurther.Gods;
    using CrawlFurther.Heroes;
    using CrawlFurther.Monsters;
    using CrawlFurther.UI;
    using CrawlFurther.Util;
    using CrawlFurther.Content.Gods;

    /// <summary>
    /// The vault's FURTHER and SECRETS categories: a page for every god, idol, hero origin and ghost form of Crawl:
    /// Further (and every VaultRegistry entry that is not a monster), and the secrets with their groups.
    /// </summary>
    public static class FurtherVault
    {
        public const string Name = "Crawl: Further";

        static readonly VaultCategory s_further = new VaultCategory
        {
            label = "FURTHER",
            stamp = "VaultStampFurther",
            summary = (found, total) => found + " / " + total + " entries found\n\nThe gods, hero origins, ghost forms and blobs of " + Name + ", each with its own page",
            pages = Pages,
            selfCheck = SelfCheck,
        };

        static readonly VaultCategory s_secrets = new VaultCategory
        {
            label = "SECRETS",
            stamp = "VaultStampSecrets",
            summary = (found, total) => found + " / " + total + " secrets found\n\nRiddles that point to the rarest finds in " + Name,
            secrets = true,
        };

        public static void Register()
        {
            Vault.AddCategory(s_further);
            Vault.AddCategory(s_secrets);
            Secrets.AddGroup("Silver", "A silver secret", SlotTier.Silver);
            Secrets.AddGroup("Gold", "A gold secret", SlotTier.Gold);
            Secrets.AddGroup("Statues", "A statue secret");
            Secrets.AddGroup("Objects", "A hidden object");
            Secrets.AddGroup("Items", "A hidden item");
            VaultLines.Register();
        }

        /// <summary>One page per mod god, idol, origin and ghost form (the vanilla Wanderer and Wisp are left out), then
        /// every VaultRegistry entry that is not a built monster (those are in MONSTERS).</summary>
        static IEnumerable<VaultPage> Pages()
        {
            foreach (var god in DeityFactory.BuiltNames)
            {
                var d = SystemDeity.GetDeity(god);
                string art;
                DeityFactory.ArtByName.TryGetValue(god, out art);
                yield return new VaultPage { kind = "God", id = god, name = god, text = GodText(d), art = art };
            }
            foreach (var t in new[] { SlotTier.Silver, SlotTier.Gold })
                yield return new VaultPage
                {
                    kind = "Idol", id = t.ToString(), name = Title(CustomGod.TierName(t)), text = IdolText(t),
                    art = IdolArt(t), unlock = Unlocks.IdFor("God", t),
                };
            foreach (var h in HeroClasses.All)
            {
                if (h == null || h.portraitArt == "HeroWanderer") continue;
                // the player-1 colour set (Hero<id>_P1) when the origin has per-player sheets
                string art = h.portraitArt;
                if (!string.IsNullOrEmpty(art) && File.Exists(SpriteSheets.PathOf(art + "_P1.json"))) art += "_P1";
                yield return new VaultPage
                {
                    kind = "Hero", id = h.id ?? h.name, name = Title(h.name), text = Join(h.summary, h.flavour), art = art,
                    unlock = Unlocks.IdFor("Hero", h.tier),
                };
            }
            foreach (var g in GhostForms.All)
            {
                if (g == null || GhostForms.IsDefault(g)) continue;
                yield return new VaultPage
                {
                    kind = "Ghost", id = g.portraitArt ?? g.name, name = Title(g.name), text = Join(g.summary, g.flavour), art = g.portraitArt,
                    unlock = Unlocks.IdFor("Ghost", g.tier),
                };
            }
            // the blobs a ghost can pick (the plain one is the game's own): locked until their challenge is done
            foreach (var b in GhostBlobs.All)
            {
                if (b == null || string.IsNullOrEmpty(b.art)) continue;
                var page = new VaultPage { kind = "Blob", id = b.id, name = b.name, text = BlobText(b), art = b.art, unlock = b.unlock };
                if (b.unlock == null && b.fits != null) page.locked = () => !AnyFormOpen(b);
                yield return page;
            }
            foreach (var e in VaultRegistry.Entries)
            {
                if (e == null || string.IsNullOrEmpty(e.id)) continue;
                if (e.id == "GhostWisp" || e.iconSheet == "GhostWisp" || e.iconSheet == "HeroWanderer") continue;
                if (e.category == "Monsters")
                {
                    string id = e.id.StartsWith("Mod", StringComparison.Ordinal) ? e.id.Substring(3) : e.id;
                    if (MonsterFactory.Built.ContainsKey(id) || MonsterFactory.Built.ContainsKey(e.id)) continue;
                }
                yield return new VaultPage { kind = "Reg" + (e.category ?? ""), id = e.id, name = e.name ?? e.id, text = e.text, art = e.iconSheet };
            }
        }

        static string GodText(Deity d)
        {
            if (d == null) return string.Empty;
            string text = (R.Get<string>(d, "m_text") ?? string.Empty).Trim();
            string flav = R.Get<string>(d, "m_textFlavour");
            if (!string.IsNullOrEmpty(flav)) text += "\n" + flav.Replace("\n", " ");
            return text;
        }

        static string IdolText(SlotTier t)
        {
            return "Your own god: take any god's perk, then pick " + CustomGod.Slots(t) +
                   " starting monsters from every god's starters. Each one evolves along its own tree.";
        }

        /// <summary>The blob's line, then whose it is: a form's own (silver and gold can pick it too), or silver and gold's alone.</summary>
        static string BlobText(GhostBlobDef b)
        {
            foreach (var f in GhostForms.All)
                if (f.tier == SlotTier.Normal && GhostBlobs.Own(f) == b)
                    return b.summary + "\nThe " + Title(f.name) + "'s own. Silver and gold ghosts pick it too";
            return b.summary + "\nOnly silver and gold ghosts pick it";
        }

        /// <summary>A blob with no challenge of its own (the King) opens with the first form that can pick it.</summary>
        static bool AnyFormOpen(GhostBlobDef b)
        {
            foreach (var f in GhostForms.All)
            {
                if (!GhostBlobs.Fits(b, f)) continue;
                if (f.tier == SlotTier.Normal || Unlocks.IsUnlocked(Unlocks.IdFor("Ghost", f.tier))) return true;
            }
            return false;
        }

        static string IdolArt(SlotTier t) { return t == SlotTier.Gold ? "DeityGoldIdol" : "DeitySilverIdol"; }

        static string Join(string summary, string flavour)
        {
            string text = summary ?? string.Empty;
            if (!string.IsNullOrEmpty(flavour)) text += "\n" + flavour.Replace("\n", " ");
            return text;
        }

        /// <summary>"SELLSWORD" -> "Sellsword" (origin and form names are stored in capitals for the pickers).</summary>
        static string Title(string s)
        {
            if (string.IsNullOrEmpty(s)) return s;
            var parts = s.ToLowerInvariant().Split(' ');
            for (int i = 0; i < parts.Length; i++)
                if (parts[i].Length > 0) parts[i] = char.ToUpperInvariant(parts[i][0]) + parts[i].Substring(1);
            return string.Join(" ", parts);
        }

        /// <summary>
        /// Every FURTHER page belongs together: its name, text and picture come from one and the same source (god, idol,
        /// origin, ghost form or registry entry), and no per-slot sheet other than an origin's P1 (Hero..._P2.._P4,
        /// Gear..._Pn) became a page of its own. Core checks names, keys and pictures for repeats.
        /// </summary>
        static void SelfCheck(Action<string> bad)
        {
            var pages = LibraryEntries.PagesOf(s_further);
            if (pages.Count == 0) bad("FURTHER has no entries");
            foreach (var kv in pages)
            {
                var p = kv.Key; var e = kv.Value;
                string label = "FURTHER " + p.kind + " " + p.id;
                if (!string.IsNullOrEmpty(p.art))
                {
                    var slot = Regex.Match(p.art, "_P([0-9])$");
                    if (slot.Success && !(p.kind == "Hero" && slot.Groups[1].Value == "1")) bad(label + ": per-slot sheet " + p.art + " became a page");
                    if (p.art.StartsWith("Gear", StringComparison.Ordinal)) bad(label + ": gear sheet " + p.art + " became a page");
                }
                string want = null, name = null, art = null;
                if (p.kind == "God")
                {
                    var d = SystemDeity.GetDeity(p.id);
                    want = d != null ? (R.Get<string>(d, "m_text") ?? string.Empty).Trim() : null; name = p.id;
                    DeityFactory.ArtByName.TryGetValue(p.id, out art);
                }
                else if (p.kind == "Idol")
                {
                    var t = p.id == "Gold" ? SlotTier.Gold : SlotTier.Silver;
                    name = CustomGod.TierName(t); want = "Your own god"; art = IdolArt(t);
                }
                else if (p.kind == "Hero")
                {
                    var h = HeroClasses.All.Find(x => x != null && (x.id ?? x.name) == p.id);
                    if (h != null) { want = h.summary; name = h.name; art = h.portraitArt; }
                }
                else if (p.kind == "Ghost")
                {
                    var g = GhostForms.All.Find(x => x != null && (x.portraitArt ?? x.name) == p.id);
                    if (g != null) { want = g.summary; name = g.name; art = g.portraitArt; }
                }
                else if (p.kind == "Blob")
                {
                    var b = GhostBlobs.Find(p.id);
                    if (b != null) { want = b.summary; name = b.name; art = b.art; }
                }
                else
                {
                    var r = VaultRegistry.Entries.Find(x => x != null && x.id == p.id && "Reg" + (x.category ?? "") == p.kind);
                    if (r != null) { want = r.text; name = r.name ?? r.id; art = r.iconSheet; }
                }
                if (name == null) { bad(label + ": source not found"); continue; }
                if (!string.Equals(e.m_name ?? "", Title(name), StringComparison.OrdinalIgnoreCase)
                    && !string.Equals(e.m_name ?? "", name, StringComparison.OrdinalIgnoreCase))
                    bad(label + ": name '" + e.m_name + "' is not " + name);
                if (!string.IsNullOrEmpty(want) && !(p.text ?? "").StartsWith(want, StringComparison.Ordinal))
                    bad(label + ": text is not its own ('" + p.text + "')");
                if (art != null && p.art != art && p.art != art + "_P1") bad(label + ": picture " + p.art + " is not " + art);
            }
        }
    }
}
