using UnityEngine;

namespace Meridian.Rig
{
    /// <summary>A dug tile's item lying in the world: a small physics body showing the material.</summary>
    public sealed class ItemDrop : MonoBehaviour
    {
        /// <summary>Item id (Items.ItemRegistry; tile items keep their TileId).</summary>
        public int itemId;
        public SpriteRenderer view;
        public Rigidbody2D body;
        /// <summary>Time.time it spawned (pickup waits a moment so the pop reads).</summary>
        public float spawnedAt;
    }
}
