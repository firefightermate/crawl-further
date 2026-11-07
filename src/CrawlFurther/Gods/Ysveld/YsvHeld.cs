using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>The Hoarclaw's seize: when its grab hits the hero, he is held at the pincers.</summary>
    public class YsvGrabFx : MonoBehaviour
    {
        void MsgOnAttackContact(DamageInfo d)
        {
            if (d == null || d.m_victim == null) return;
            var hero = ModUtil.Hero();
            if (hero == null || d.m_victim != hero) return;
            var src = d.m_source ?? FxFactory.SourceOf(gameObject);
            var owner = src != null ? src.m_sourceOwner : null;
            if (owner == null) return;
            var h = hero.GetComponent<YsvHeld>() ?? hero.AddComponent<YsvHeld>();
            h.Begin(owner);
        }
    }

    /// <summary>
    /// On the hero while seized: kept 22 px out along the way the Hoarclaw faces for 0.5 s (frost shackles on his feet),
    /// then hurled 330 px/s straight away from it. Curling Stone: if he crosses ice in the first 0.3 s of the throw he
    /// keeps sliding (<see cref="YsvSlide.Curl"/>) until he leaves the ice or meets a monster; a wall at the end costs
    /// 0.8 and a pip.
    /// </summary>
    public class YsvHeld : MonoBehaviour
    {
        public const float Hold = 0.5f, Throw = 330f, Reach = 22f, CurlSpeed = 260f, CurlWindow = 0.3f, WallHit = 0.8f;
        GameObject m_owner, m_shackle;
        float m_left;

        public void Begin(GameObject owner)
        {
            if (m_owner != null) return;
            if (!ModStatus.AllowCrowdControl(gameObject)) return;   // inside the crowd-control immunity: the claw hits but can't hold
            m_owner = owner; m_left = Hold;
            if (YsveldFx.GrabHold != null) m_shackle = ModAttach.Spawn(YsveldFx.GrabHold, gameObject, Vector2.zero);
            enabled = true;
        }

        void Update()
        {
            if (m_owner == null) { enabled = false; return; }
            var mh = GetComponent<Health>();
            if (!YsvUtil.Alive(m_owner) || (mh != null && !mh.IsAlive())) { Release(false); return; }
            var mv = m_owner.GetComponent<PlayerMovement>();
            var face = mv != null ? mv.GetFaceDirection() : Vector2.right;
            if (face.sqrMagnitude < 0.01f) face = Vector2.right;
            Vector2 them = m_owner.transform.position;
            ModUtil.Teleport(gameObject, ModUtil.SafePoint(them, them + face.normalized * Reach));
            m_left -= Time.deltaTime;
            if (m_left <= 0f) Release(true);
        }

        void Release(bool hurl)
        {
            if (m_shackle != null) { ModAttach.Drop(m_shackle, gameObject); m_shackle = null; }
            if (hurl && m_owner != null)
            {
                var d = (Vector2)transform.position - (Vector2)m_owner.transform.position;
                if (d.sqrMagnitude < 0.01f) d = Vector2.right;
                var mv = GetComponent<PlayerMovement>();
                if (mv != null) mv.AddImpulse(d.normalized * Throw);
                if (YsveldFx.GrabFling != null) SystemPool.Spawn(YsveldFx.GrabFling, transform.position);
                StartCoroutine(WatchForIce(d.normalized, m_owner));
            }
            m_owner = null;
        }

        IEnumerator WatchForIce(Vector2 dir, GameObject claw)
        {
            float t = 0f;
            while (t < CurlWindow)
            {
                var slide = GetComponent<YsvSlide>();
                if (slide != null && slide.OnIce)
                {
                    slide.Curl(dir, CurlSpeed, claw, (s, wall) =>
                    {
                        if (!wall) return;
                        var src = YsvUtil.Source(claw);
                        YsvUtil.Hurt(gameObject, WallHit, -dir, src);
                        YsvUtil.Rime(gameObject, src, 1, true);
                        if (YsveldFx.CurlCrash != null) SystemPool.Spawn(YsveldFx.CurlCrash, (Vector2)transform.position + dir * 4f);
                    });
                    break;
                }
                t += Time.deltaTime;
                yield return null;
            }
            enabled = false;
        }

        void OnDisable()
        {
            if (m_shackle != null) { ModAttach.Drop(m_shackle, gameObject); m_shackle = null; }
            m_owner = null;
        }
    }
}
