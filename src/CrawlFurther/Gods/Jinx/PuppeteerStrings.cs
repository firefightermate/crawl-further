using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Puppeteer, Strings Attached: Curtain Call hauls up to three allies onto marks round the hero (with nobody to pull,
    /// two Jack-in-the-Boxes spring up), and keeps them on its strings for <see cref="HoldTime"/> s: while it lives they
    /// take 30 % less damage from the hero. Tell: a violet string from its hands to each, and a cross over their heads.
    /// Only AI-driven monsters are hauled: never one another person is playing, and never a boss.
    /// </summary>
    public class PuppeteerStrings : JinxBehaviour
    {
        public const float HoldTime = 6f, Reach = 200f, Ring = 26f;
        public const int MaxHauled = 3, MaxJacks = 2, Beads = 7;

        readonly List<JinxStrung> m_held = new List<JinxStrung>();
        readonly List<GameObject> m_beads = new List<GameObject>();

        protected override void OnEnable() { base.OnEnable(); m_held.Clear(); }

        protected override void OnDisable()
        {
            base.OnDisable();
            m_held.Clear();
            ClearBeads();
        }

        /// <summary>Clip event: the strings haul the allies in.</summary>
        public void ModJinxCurtainCall()
        {
            var hero = ModUtil.Hero();
            if (hero == null || !Alive) return;
            Vector2 hp = hero.transform.position;
            var list = new List<Player>();
            int jacks = 0;
            foreach (var p in FindObjectsOfType<Player>())
            {
                if (p == null || p == Body || p.gameObject == hero || ModUtil.IsGhost(p)) continue;
                var h = p.GetComponent<Health>();
                if (h == null || !h.IsAlive()) continue;
                if (p.gameObject.name.StartsWith("ModJackMinion")) jacks++;
                var pd = p.GetPlayerData();
                if (pd != null && pd.IsHuman) continue;
                if (p.GetComponentInParent<Boss>() != null) continue;
                if (((Vector2)p.transform.position - Me).sqrMagnitude > Reach * Reach) continue;
                list.Add(p);
            }
            list.Sort((x, y) => ((Vector2)x.transform.position - Me).sqrMagnitude.CompareTo(((Vector2)y.transform.position - Me).sqrMagnitude));
            int n = Mathf.Min(MaxHauled, list.Count);
            float start = Random.Range(0f, 360f);
            for (int i = 0; i < n; i++)
            {
                var p = list[i];
                Vector2 old = p.transform.position;
                var spot = ModUtil.SafePoint(hp, hp + (Vector2)(Quaternion.Euler(0, 0, start + i * 360f / n) * Vector2.right) * Ring, 4f);
                if (JinxFx.Confetti != null) { SystemPool.Spawn(JinxFx.Confetti, old); SystemPool.Spawn(JinxFx.Confetti, spot); }
                ModUtil.Teleport(p.gameObject, spot);
                var mv = p.GetComponent<PlayerMovement>();
                if (mv != null && (hp - spot).sqrMagnitude > 0.01f) mv.SetDirection((hp - spot).normalized);
                Tie(p.gameObject);
            }
            if (n == 0 && JinxFx.JackSpawner != null && jacks < MaxJacks)
            {
                var spots = new[] { ModUtil.SafePoint(hp, hp + new Vector2(-Ring, 4f)), ModUtil.SafePoint(hp, hp + new Vector2(Ring, 4f)) };
                foreach (var s in spots) FxFactory.SpawnOwned(JinxFx.JackSpawner, s, Own);
                StartCoroutine(StringJacks(spots));
            }
        }

        IEnumerator StringJacks(Vector2[] spots)
        {
            yield return new WaitForSeconds(0.7f);
            if (!Alive) yield break;
            foreach (var p in FindObjectsOfType<Player>())
            {
                if (p == null || !p.gameObject.name.StartsWith("ModJackMinion")) continue;
                foreach (var s in spots)
                    if (((Vector2)p.transform.position - s).sqrMagnitude < 14f * 14f) { Tie(p.gameObject); break; }
            }
        }

        void Tie(GameObject ally)
        {
            var s = ally.GetComponent<JinxStrung>() ?? ally.AddComponent<JinxStrung>();
            s.Hold(this, HoldTime);
            if (!m_held.Contains(s)) m_held.Add(s);
        }

        void LateUpdate()
        {
            m_held.RemoveAll(s => s == null || s.Holder != this || !s.isActiveAndEnabled);
            int need = Alive ? m_held.Count * Beads : 0;
            while (m_beads.Count < need && JinxFx.StringBead != null)
            {
                var b = SystemPool.Spawn(JinxFx.StringBead, Me);
                if (b == null) break;
                m_beads.Add(b);
            }
            while (m_beads.Count > need) { Drop(m_beads[m_beads.Count - 1]); m_beads.RemoveAt(m_beads.Count - 1); }
            for (int i = 0; i < m_held.Count && i * Beads < m_beads.Count; i++)
            {
                Vector2 hand = Me + new Vector2((i % 2 == 0 ? 10f : -9f) * Side, 26f);
                Vector2 head = FloatNumber.OverHead(m_held[i].gameObject, 0f);
                for (int k = 0; k < Beads; k++)
                {
                    var b = m_beads[i * Beads + k];
                    if (b == null) continue;
                    Vector2 p = Vector2.Lerp(hand, head, (k + 0.5f) / Beads);
                    p.y -= Mathf.Sin((k + 0.5f) / Beads * Mathf.PI) * 4f;    // a little sag
                    b.transform.position = new Vector3(Mathf.Round(p.x), Mathf.Round(p.y), transform.position.z - 0.05f);
                }
            }
        }

        static void Drop(GameObject b)
        {
            if (b != null && b.activeInHierarchy && !SystemMain.GetDeloadInProgress()) SystemPool.Despawn(b);
        }

        void ClearBeads()
        {
            foreach (var b in m_beads) Drop(b);
            m_beads.Clear();
        }
    }
}
