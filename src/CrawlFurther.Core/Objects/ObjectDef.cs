using System;
using System.Collections.Generic;
using UnityEngine;

namespace CrawlFurther.Objects
{
    /// <summary>
    /// A room object: a trap, an interactable or a contact hazard. Register it with <see cref="ObjectKit.Register"/>.
    ///
    /// Art (one sheet, cells with the floor point at (cellW / 2, cellH - 2), like monsters):
    ///  - Use / Touch: "Idle" (loop, required); optional "Use" (plays on use, then back to Idle), "Spent" (after the
    ///    last use), "Off" (while a fight locks the room) and "Vault" (the vault picture). Any other anim becomes a
    ///    state for <see cref="ModObject.Play"/>: it loops unless listed in <see cref="once"/>, and <see cref="then"/>
    ///    names the state that follows it.
    ///  - Trap: "Inactive", "Activate", "Active", "Deactivate", optional "Disabled", and one anim per
    ///    <see cref="ObjTrapAttack"/> (default "Action").
    /// Text is plain words: no "[word]" (GUIText drops it) and none of % { | } ~.
    /// </summary>
    public class ObjectDef
    {
        /// <summary>Unique id; the prefab is "ModObj" + id.</summary>
        public string id;
        /// <summary>Name on the vault page and the tip title.</summary>
        public string name;
        /// <summary>The vault line: one line of up to 90 characters.</summary>
        public string vault;
        /// <summary>The two HUD tip lines shown the first time a player meets it in a room (up to 60 characters each).</summary>
        public string tip1, tip2;
        /// <summary>The sheet; null means "Obj" + id.</summary>
        public string art;
        public ObjKind kind = ObjKind.Use;
        public ObjUser users = ObjUser.Hero;
        /// <summary>Use: the vanilla action prompt text.</summary>
        public string actionText = "USE";
        /// <summary>Uses before it is spent (0: unlimited).</summary>
        public int uses = 1;
        /// <summary>Seconds between uses.</summary>
        public float cooldown;
        /// <summary>Paid by the user on each use; health is taken exactly, with no resistance.</summary>
        public int costGold, costEcto;
        public float costHealth;
        /// <summary>Use / Touch: off while the room's doors are locked.</summary>
        public bool offDuringFight = true;
        /// <summary>Use: the hero may use it while the doors are locked. Off by default because the hero's action button
        /// is his attack: a usable object next to him would take his swing.</summary>
        public bool heroInFight;
        /// <summary>Use: the vanilla little hop and short pause of the user (the fountain's feel).</summary>
        public bool bounce = true;
        /// <summary>Extra condition for using it (null: always).</summary>
        public Func<ObjUse, bool> canUse;
        /// <summary>Use: runs on use, after the costs are paid. Touch: runs when someone steps on it.</summary>
        public Action<ObjUse> onUse;
        /// <summary>Touch: distance in pixels from the floor point that triggers it.</summary>
        public float touchRadius = 5f;
        /// <summary>Touch: seconds before the same player can trigger it again.</summary>
        public float rearm = 3f;
        /// <summary>Vanilla AudioCue played on use ("" or null: none).</summary>
        public string useSound = "SoundPropActivate";
        /// <summary>Extra states that play once instead of looping.</summary>
        public HashSet<string> once = new HashSet<string>();
        /// <summary>State -> the state that follows it when it ends.</summary>
        public Dictionary<string, string> then = new Dictionary<string, string>();

        /// <summary>Trap: its attacks, fired in order.</summary>
        public List<ObjTrapAttack> attacks = new List<ObjTrapAttack>();
        /// <summary>Trap: the ghost aims it with the stick.</summary>
        public bool aims = true;
        /// <summary>Trap: the allowed aim angles in degrees (null: any, snapped to <see cref="snap"/>).</summary>
        public float[] angles;
        public float snap = 7.5f, startAngle;
        /// <summary>Trap: the vanilla trap budget value (1 = a dart turret).</summary>
        public float difficulty = 1f;
        /// <summary>Trap: the attack node, in pixels from the floor point (y up).</summary>
        public Vector2 node = new Vector2(0, 7);
        /// <summary>Trap: height of the vanilla "enter" arrow.</summary>
        public float enterArrowY = 12f;

        /// <summary>Use: the action trigger box in pixels.</summary>
        public Vector2 useBox = new Vector2(30f, 22f);
        /// <summary>The solid footprint in pixels (x 0: none) and its height above the floor point.</summary>
        public Vector2 bodySize = new Vector2(10f, 5f);
        public float bodyY = 1.5f;
        public ObjSpawn spawn = new ObjSpawn();
        /// <summary>A <see cref="UI.Secrets"/> id found the first time a human player uses, triggers or enters it.</summary>
        public string secret;
        /// <summary>Runs once on the template after it is built.</summary>
        public Action<GameObject> customize;
        /// <summary>Runs on every spawned instance (pooled reuse too): add your own components here, never on the template.</summary>
        public Action<GameObject> onSpawned;

        public string PrefabName { get { return "ModObj" + id; } }
    }
}
