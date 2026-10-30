using UnityEngine;

namespace Meridian.Rig
{
    /// <summary>A dug tile's item lying in the world: a small physics body showing the material.</summary>
    public sealed class ItemDrop : MonoBehaviour
    {
        /// <summary>Item id; in M1 the tile id it came from (inventory items arrive in M3).</summary>
        public byte itemId;
        public SpriteRenderer view;
        public Rigidbody2D body;
    }
}
