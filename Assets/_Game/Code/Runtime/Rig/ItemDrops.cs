using System.Collections.Generic;
using Meridian.Terrain;
using UnityEngine;

namespace Meridian.Rig
{
    /// <summary>Pooled item drops (no Instantiate/Destroy churn while digging).</summary>
    public sealed class ItemDrops : MonoBehaviour
    {
        public const float DropScale = 0.35f;
        public const int MaxLive = 64;

        readonly Stack<ItemDrop> pool = new Stack<ItemDrop>();
        readonly List<ItemDrop> live = new List<ItemDrop>(MaxLive);

        public IReadOnlyList<ItemDrop> Live => live;

        public ItemDrop Spawn(byte itemId, Vector2 position, Sprite sprite)
        {
            ItemDrop d;
            if (live.Count >= MaxLive) { d = live[0]; live.RemoveAt(0); }
            else d = pool.Count > 0 ? pool.Pop() : Create();
            d.itemId = itemId;
            d.view.sprite = sprite;
            d.transform.position = position;
            d.body.linearVelocity = new Vector2(Random.Range(-1f, 1f), 2f);
            d.gameObject.SetActive(true);
            live.Add(d);
            return d;
        }

        public void Collect(ItemDrop d)
        {
            if (!live.Remove(d)) return;
            d.gameObject.SetActive(false);
            pool.Push(d);
        }

        ItemDrop Create()
        {
            var go = new GameObject("ItemDrop");
            go.transform.SetParent(transform, false);
            go.transform.localScale = Vector3.one * DropScale;
            var d = go.AddComponent<ItemDrop>();
            d.view = go.AddComponent<SpriteRenderer>();
            d.view.sortingOrder = 5;
            d.body = go.AddComponent<Rigidbody2D>();
            d.body.interpolation = RigidbodyInterpolation2D.Interpolate;
            go.AddComponent<BoxCollider2D>().size = Vector2.one * 0.9f;
            return d;
        }
    }
}
