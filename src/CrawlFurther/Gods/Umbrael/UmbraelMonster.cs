using UnityEngine;

namespace CrawlFurther.Content.Gods.Umbrael
{
    using CrawlFurther.Monsters;
    using CrawlFurther.Util;

    /// <summary>Clip events every Umbrael monster can use: the Glimmer's mirror images.</summary>
    public class UmbraelMonster : MonsterBehaviour
    {
        /// <summary>Two decoys appear beside the monster.</summary>
        public void ModMirrorImage()
        {
            if (UmbraelFx.DecoySpawner == null) return;
            for (int i = 0; i < 2; i++)
            {
                var off = new Vector2(i == 0 ? -18f : 18f, Random.Range(-8f, 8f));
                FxFactory.SpawnOwned(UmbraelFx.DecoySpawner, ModUtil.SafePoint(transform.position, (Vector2)transform.position + off), Monster.OwnSource());
            }
        }
    }
}
