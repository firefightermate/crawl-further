using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Jinx
{
    using CrawlFurther.Content.Gods.Umbrael;
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Jinx's clip events: the Wild Card, and moves left to chance.</summary>
    public class JinxMonster : MonsterBehaviour
    {
        const string SurgeModifier = "modwildcard";

        Player m_player;
        exSprite m_sprite;
        PlayerData m_surgeData;
        GameObject m_surgeFx;

        protected override void Awake()
        {
            base.Awake();
            m_player = GetComponent<Player>();
            m_sprite = GetComponent<exSprite>();
        }

        void OnDisable() { EndSurge(); }

        /// <summary>Wild Card: a card flips over the monster and deals a random boon: Hearts heal 1, Spades 1.5x damage for
        /// 3 s, Diamonds a plate (up to 2), Clubs a 2.5 s sprint.</summary>
        public void ModWildCard()
        {
            int suit = Random.Range(0, 4);
            if (JinxFx.WildCard != null)
            {
                var fx = SystemPool.Spawn(JinxFx.WildCard, (Vector2)transform.position + new Vector2(0f, 18f));
                var anim = fx != null ? fx.GetComponent<exSpriteAnimation>() : null;
                if (anim != null && JinxFx.Suits != null && JinxFx.Suits[suit] != null) StartCoroutine(ShowSuit(anim, JinxFx.Suits[suit]));
            }
            switch (suit)
            {
                case 0: Monster.Heal(1f); break;
                case 1: StartCoroutine(DamageSurge(3f)); break;
                case 2: Monster.AddPlate(Mathf.Max(2, Monster.Traits.maxPlates)); break;
                default: Monster.ModSprint(2.5f); break;
            }
        }

        IEnumerator ShowSuit(exSpriteAnimation anim, exSpriteAnimClip face)
        {
            yield return new WaitForSeconds(0.32f);
            if (anim != null && anim.isActiveAndEnabled) anim.Play(face);
        }

        IEnumerator DamageSurge(float t)
        {
            var pd = m_player != null ? R.Get<PlayerData>(m_player, "m_playerData") : null;
            if (pd == null) yield break;
            EndSurge();
            m_surgeData = pd;
            pd.GameData.AddBaseModifier(SurgeModifier, new PlayerModifier { m_modify = PlayerModifier.eType.MonsterDamage, m_type = ValueModifier.eModifierType.Multiply, m_value = 1.5f });
            if (m_sprite != null) m_sprite.color = new Color(1f, 0.7f, 0.7f, m_sprite.color.a);
            // follows the feet in front of the body (not parented: a child despawned while this body is being pooled
            // would have to change the hierarchy mid-deactivation)
            if (JinxFx.SurgeAura != null) m_surgeFx = ModAttach.Spawn(JinxFx.SurgeAura, gameObject, Vector2.zero, 0.01f);
            yield return new WaitForSeconds(t);
            EndSurge();
        }

        // The surge sits on the controlling player's own modifier stack: if this body is despawned before it ends, the
        // coroutine dies with it and the x1.5 would follow that player into every later monster.
        void EndSurge()
        {
            if (m_surgeData == null) return;
            if (m_surgeData.GameData != null) m_surgeData.GameData.RemoveModifiers(SurgeModifier);
            m_surgeData = null;
            ModAttach.Drop(m_surgeFx, gameObject);
            m_surgeFx = null;
            if (m_sprite != null) m_sprite.color = new Color(1f, 1f, 1f, m_sprite.color.a);
        }

        /// <summary>Jack-in-the-Box Pop: spring out of the box somewhere near the hero.</summary>
        public void ModPopNearHero()
        {
            var hero = Monster.HeroPos;
            var off = (Vector2)(Quaternion.Euler(0, 0, Random.Range(0f, 360f)) * Vector2.right) * Random.Range(22f, 34f);
            if (JinxFx.PopPuff != null || JinxFx.ConfettiPop != null) SystemPool.Spawn(JinxFx.PopPuff ?? JinxFx.WildCard ?? JinxFx.ConfettiPop, transform.position);
            ModUtil.Teleport(gameObject, ModUtil.SafePoint(hero, hero + off));
            Monster.FaceHero();
        }

        /// <summary>Card Sharp Shuffle: trade places with the ally standing nearest the hero.</summary>
        public void ModShuffle()
        {
            var hero = Monster.HeroPos;
            Player best = null; float bd = 1e9f;
            foreach (var p in FindObjectsOfType<Player>())
            {
                if (p == null || p == m_player || p.gameObject == ModUtil.Hero() || ModUtil.IsGhost(p)) continue;
                var h = p.GetComponent<Health>();
                if (h == null || !h.IsAlive()) continue;
                // never yank another player's body (human or bot) across the room, and never move a boss or boss part
                var pd = p.GetPlayerData();
                if (pd != null && (pd.IsHuman || pd.IsBot)) continue;
                if (p.GetComponentInParent<Boss>() != null) continue;
                float d = ((Vector2)p.transform.position - hero).sqrMagnitude;
                if (d < bd) { bd = d; best = p; }
            }
            if (best == null) { ModPopNearHero(); return; }
            Vector2 me = transform.position, them = best.transform.position;
            var fl = JinxFx.Shuffle ?? UmbraelFx.SwapFlash;
            if (fl != null) { SystemPool.Spawn(fl, me); SystemPool.Spawn(fl, them); }
            ModUtil.Teleport(best.gameObject, me);
            ModUtil.Teleport(gameObject, them);
            Monster.FaceHero();
        }

        /// <summary>Dice Imp Roll: the die lands on 1-6 and bursts into that many shards.</summary>
        public void ModRollDice()
        {
            if (JinxFx.DieShard == null) return;
            int n = Random.Range(1, 7);
            FloatNumber.RollOver(gameObject, n, 6);
            float start = Random.Range(0f, 360f);
            for (int i = 0; i < n; i++)
                FxFactory.SpawnOwned(JinxFx.DieShard, (Vector2)transform.position + new Vector2(0f, 6f), Monster.OwnSource(), start + i * 360f / n);
        }
    }
}
