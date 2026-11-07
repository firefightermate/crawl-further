using UnityEngine;

namespace CrawlFurther.Monsters
{
    /// <summary>
    /// A drawn overlay made by <see cref="ModStatus.RegisterOverlay(string, string, string, float)"/> or
    /// <see cref="ModStatus.Indicator"/>: a looping (or one-shot) visual that follows whoever carries it.
    /// Keep the indicator ones and pass them to <see cref="ModInd"/>.
    /// </summary>
    public class StatusOverlayDef
    {
        internal string statusName;
        internal Status status;
        internal GameObject small, big;     // big: the sheet's "<anim>Big" variant for large victims (falls back to small)
        internal OverlayAt at;
        internal float offsetY;
        internal bool liftOverHead;         // registered at offsetY 12 or more: never sits inside a tall victim's head
        internal float height;              // opaque top of the art above the cell bottom (for stacking head overlays)
        internal bool indicator;            // not tied to a status: shown and hidden by code (ModInd); dropped on death
        internal bool once;                 // one-shot: frees its slot when its anim ends
    }
}
