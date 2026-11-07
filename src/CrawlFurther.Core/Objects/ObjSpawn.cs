namespace CrawlFurther.Objects
{
    /// <summary>When and where an object is placed at random (see <see cref="ObjectKit"/>).</summary>
    public class ObjSpawn
    {
        /// <summary>Weight among the objects a room may get; 0 never places it at random (place it by code instead).</summary>
        public float weight = 10f;
        /// <summary>
        /// Its own chance per room (0 to 1), rolled before the shared roll and outside the weight pool, so the odds stay
        /// the same however many other objects are installed. Use it for rare finds and leave <see cref="weight"/> at 0.
        /// </summary>
        public float chance;
        /// <summary>Floors it may appear on (SystemGame.GetLevel()).</summary>
        public int minFloor = 1, maxFloor = 99;
        public ObjRoom rooms = ObjRoom.Quiet | ObjRoom.Fight | ObjRoom.Statue | ObjRoom.Trapped | ObjRoom.Stairs;
        /// <summary>Never in a room that is any of these (a stairs room is also Quiet or Fight).</summary>
        public ObjRoom notRooms;
        public ObjEnv env = ObjEnv.Any;
        /// <summary>At most this many per floor (0: no cap).</summary>
        public int maxPerFloor = 1;
        public ObjPlace place = ObjPlace.Open;
        /// <summary>Place two linked copies in the room (<see cref="ModObject.partner"/>), e.g. warp pads.</summary>
        public bool pair;
    }
}
