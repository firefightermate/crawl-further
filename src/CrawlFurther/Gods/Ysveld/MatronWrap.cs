using System.Collections;
using UnityEngine;

namespace CrawlFurther.Content.Gods.Ysveld
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>
    /// Widow Matron, Wrap: a hero pinned by frost within 60 px of her is wrapped in silk. His pin lasts 1.2 s instead of
    /// 0.8 (the root is laid again inside the crowd-control window), and her next Impale on him hits double (basic 1).
    /// Tell: silk spiralling round him; her hourglass glows red (IdleWrap / RunWrap) until the doubled Impale is thrown.
    /// </summary>
    public class MatronWrap : YsveldBehaviour
    {
        public const float Reach = 60f, PinTime = 1.2f, Charge = 6f;
        public static exSpriteAnimClip WrapIdle, WrapRun;
        public static GameObject DoubleImpale;
        float m_charged;

        protected override void OnEnable() { base.OnEnable(); m_charged = 0f; YsvRime.Pinned += OnPinned; }

        protected override void OnDisable() { base.OnDisable(); YsvRime.Pinned -= OnPinned; }

        void OnPinned(GameObject hero, DamageSource src)
        {
            if (!Alive || hero == null || ((Vector2)hero.transform.position - Me).sqrMagnitude > Reach * Reach) return;
            var wrap = YsveldFx.Wrap != null ? ModAttach.Spawn(YsveldFx.Wrap, hero, Vector2.zero) : null;
            StartCoroutine(Wrapped(hero, wrap));
            m_charged = Charge;
            SetStance(WrapIdle, WrapRun);
            NextBasic(1);
        }

        IEnumerator Wrapped(GameObject hero, GameObject wrap)
        {
            yield return new WaitForSeconds(ModStatus.RootTime * 0.5f);
            var p = hero != null ? hero.GetComponent<Player>() : null;
            var root = FxFactory.GetStatus("StatusStuckToFloor");
            if (p != null && root != null) p.AddStatus(root, Own, "modysvwrap");
            yield return new WaitForSeconds(PinTime - ModStatus.RootTime * 0.5f);
            if (wrap != null) ModAttach.Drop(wrap, hero);
        }

        public override void OnAttackSpawned(GameObject fx, GameObject template)
        {
            if (template != DoubleImpale) return;
            m_charged = 0f;
            Unwrap();
        }

        void Unwrap() { SetStance(null, null); NextBasic(0); }

        void Update()
        {
            if (m_charged <= 0f) return;
            m_charged -= Time.deltaTime;
            if (m_charged <= 0f || !Alive) { m_charged = 0f; Unwrap(); }
        }
    }
}
