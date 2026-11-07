using System;
using UnityEngine;

namespace CrawlFurther.Ghosts
{
    /// <summary>
    /// A blob a ghost can spawn with Back instead of its form's own. Players pick one per player on the ghost page of the
    /// origin picker, under the forms; the default is always the form's own. Register it with
    /// <see cref="GhostBlobs.Register"/>.
    /// </summary>
    public class GhostBlobDef
    {
        /// <summary>Unique id ("Mote"); it is what a player's pick stores.</summary>
        public string id;
        /// <summary>The name shown in the picker ("Mote Blob").</summary>
        public string name;
        /// <summary>One plain line of what it does, shown in the picker (no numbers).</summary>
        public string summary;
        /// <summary>The monster spawned for a player: a mod prefab, or the player's own plain fodder.</summary>
        public Func<PlayerData, GameObject> prefab;
        /// <summary>The monster sheet whose Portrait frame is drawn dark while the blob is locked (optional).</summary>
        public string art;
        /// <summary>The challenge that opens it (<see cref="UI.Unlocks"/> id); null: always open.</summary>
        public string unlock;
        /// <summary>Which ghost forms may pick it; null: every form.</summary>
        public Func<GhostFormDef, bool> fits;
        /// <summary>What one costs, in bodies of ectoplasm (the game charges one body for a blob).</summary>
        public int bodies = 1;
    }
}
