using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Zhekra
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Acid Bloater, Deflate and Refill: it whistles, opens its spiracles and zips round the room like a let-go balloon:
    /// <see cref="Darts"/> fast straight darts that glance off walls (1.2 on contact), leaving acid mist on its path. Then
    /// it hangs limp for <see cref="LimpTime"/> s (it takes <see cref="LimpDamage"/>x) and swells back over
    /// <see cref="RefillTime"/> s; its bubble drops 2, 4 or 6 drops by size (basic 2 / 1 / 0). Tell: body size, and the
    /// whistle from the spiracles before it zips.
    /// </summary>
    public class BloaterDeflate : ZhkBehaviour
    {
        public const int Darts = 3;
        public const float DartSpeed = 230f, DartTime = 0.24f, LimpTime = 2f, LimpDamage = 1.3f, RefillTime = 5f, MistStep = 12f;
        /// <summary>Idle and run full / mid / low, and the limp hang (set by the kit).</summary>
        public static exSpriteAnimClip[] Idles, Runs;
        public static exSpriteAnimClip LimpClip;

        int m_size;           // 0 full, 1 mid, 2 low
        float m_refill, m_limpUntil;
        bool m_zipping;

        protected override void OnEnable() { base.OnEnable(); m_refill = -1f; m_limpUntil = 0f; m_zipping = false; Size(0); }

        void Size(int s)
        {
            m_size = Mathf.Clamp(s, 0, 2);
            Stage(Idles, Runs, m_size);
            NextBasic(m_size);
        }

        void Update()
        {
            if (!Alive || m_refill < 0f || Time.time < m_limpUntil) return;
            m_refill += Time.deltaTime;
            Size(m_refill >= RefillTime ? 0 : m_refill >= RefillTime * 0.5f ? 1 : 2);
            if (m_refill >= RefillTime) m_refill = -1f;
        }

        /// <summary>Clip event (after the whistle): the darts.</summary>
        public void ModZhkDeflate()
        {
            if (!Alive || m_zipping) return;
            StartCoroutine(Zip());
        }

        IEnumerator Zip()
        {
            m_zipping = true;
            Size(2);
            var dir = HeroPos - Me;
            dir = dir.sqrMagnitude > 1f ? dir.normalized : Face;
            for (int k = 0; k < Darts && Alive; k++)
            {
                if (k > 0)
                {
                    var to = HeroPos - Me;
                    if (to.sqrMagnitude > 1f) dir = (Vector2)(Quaternion.Euler(0, 0, Random.Range(-35f, 35f)) * to.normalized);
                }
                var hit = ZhekraFx.ZipHit != null ? FxFactory.SpawnOwned(ZhekraFx.ZipHit, Me + new Vector2(0f, 12f), Own) : null;
                float mist = 0f;
                for (float t = 0f; t < DartTime && Alive; t += Time.deltaTime)
                {
                    float step = DartSpeed * Time.deltaTime;
                    Vector2 me = Me, next = me + dir * step;
                    if (!ModUtil.Clear(me, next + dir * 8f))
                    {
                        // glance off: keep whichever half of the motion is clear
                        var fx = new Vector2(-dir.x, dir.y); var fy = new Vector2(dir.x, -dir.y);
                        dir = ModUtil.Clear(me, me + fx * 10f) ? fx : ModUtil.Clear(me, me + fy * 10f) ? fy : -dir;
                        next = me + dir * step;
                    }
                    Monster.Face(next + dir);
                    ModUtil.Teleport(gameObject, next);
                    if (hit != null && hit.activeInHierarchy) hit.transform.position = new Vector3(next.x, next.y + 12f, hit.transform.position.z);
                    mist += step;
                    if (mist >= MistStep && ZhekraFx.Mist != null) { mist = 0f; FxFactory.SpawnOwned(ZhekraFx.Mist, next, Own); }
                    yield return null;
                }
                yield return new WaitForSeconds(0.06f);
            }
            m_zipping = false;
            if (!Alive) yield break;
            m_limpUntil = Time.time + LimpTime;
            m_refill = 0f;
            Hold(LimpClip, LimpTime);
        }

        public override float HeroHitScale(DamageInfo d) { return Time.time < m_limpUntil ? LimpDamage : 1f; }
    }
}
