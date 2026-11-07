using System;
using System.Collections.Generic;

namespace CrawlFurther.Items
{
    /// <summary>Points a vanilla hero frame at a redrawn one (the hero holding the new weapon).</summary>
    public delegate void HeroFrameMap(exAtlas atlas, int index, out exAtlas outAtlas, out int outIndex);

    /// <summary>
    /// A hero weapon: a copy of a vanilla Weapon prefab with one combo of its own. The hero keeps the base weapon's
    /// frames and sounds; the attacks are re-timed and fire this weapon's effects. Pass it to
    /// <see cref="ItemRegistry.Register(WeaponDef)"/>.
    /// </summary>
    public class WeaponDef
    {
        /// <summary>Unique id. The prefab is named "ModWeapon" + id; its shop pedestal frame is "Wpn" + id and its shop
        /// bubble comes from the sheet "IconWpn" + id + "Bubble" (anim "Bubble").</summary>
        public string id;
        public string name, description;
        /// <summary>A free-form label for logs and checks ("Tether", "Returning").</summary>
        public string family;
        /// <summary>The vanilla Weapon prefab: hero frames, sounds, bot data and aim behaviour, e.g. "WeaponSpear".</summary>
        public string baseWeapon;
        /// <summary>Base combo to inherit the idle pose and colour swap from (-1: none).</summary>
        public int baseCombo = -1;
        public float cost, damageMult = 1f, comboCooldown;
        /// <summary>Chance weight in the weapon shop group "GroupWeaponsPurchasable".</summary>
        public float shopChance = 25f;
        /// <summary>The effect list; AnimAttack ids in <see cref="attacks"/> index it. Called once, at build time.</summary>
        public Func<List<DamageEffectData>> effects;
        public List<WeaponAttack> attacks = new List<WeaponAttack>();
        /// <summary>Optional: hero frames redrawn with this weapon in hand. Null shows the base weapon's frames.</summary>
        public HeroFrameMap heroFrames;
    }
}
