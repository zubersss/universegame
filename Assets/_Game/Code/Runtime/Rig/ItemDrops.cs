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

        /// <summary>Pickup (U-045): drops this close to the collector go into the inventory once they're this old.</summary>
        public const float PickupRadius = 1.2f, PickupDelay = 0.4f;
        /// <summary>Who picks drops up (the surveyor; RigTools sets it) and where they go (GameState's inventory).</summary>
        public Transform collector;
        public Meridian.Items.Inventory inventory;
        /// <summary>Raised per picked-up drop with its item id (pickup sound, HUD).</summary>
        public event System.Action<int> PickedUp;
        /// <summary>U-158: an item that went straight into the pack (a pocket's yield) raises the same pickup cue.</summary>
        public void NotifyPicked(int itemId)
        {
            PickedUp?.Invoke(itemId);
            if (collector != null) PickedUpAt?.Invoke(itemId, (Vector2)collector.position + new Vector2(0f, 0.9f));
        }
        /// <summary>U-195: as PickedUp, with where the drop was when the pack took it (the icon's flight to the PACK readout starts there).</summary>
        public event System.Action<int, Vector2> PickedUpAt;

        void Start()
        {
            if (inventory == null && Meridian.Core.GameState.Instance != null) inventory = Meridian.Core.GameState.Instance.inventory;
        }

        void FixedUpdate()
        {
            if (collector == null || inventory == null || live.Count == 0) return;
            Vector2 c = collector.position;
            float now = Time.time;
            for (int i = live.Count - 1; i >= 0; i--)
            {
                var d = live[i];
                if (now - d.spawnedAt < PickupDelay) continue;
                if (((Vector2)d.transform.position - c).sqrMagnitude > PickupRadius * PickupRadius) continue;
                if (inventory.Add(d.itemId, 1) != 0) continue; // full: it stays on the ground
                int id = d.itemId;
                Vector2 at = d.transform.position;
                Collect(d);
                PickedUp?.Invoke(id);
                PickedUpAt?.Invoke(id, at);
            }
        }

        public ItemDrop Spawn(int itemId, Vector2 position, Sprite sprite)
        {
            ItemDrop d;
            if (live.Count >= MaxLive) { d = live[0]; live.RemoveAt(0); }
            else d = pool.Count > 0 ? pool.Pop() : Create();
            d.itemId = itemId;
            d.spawnedAt = Time.time;
            d.view.sprite = sprite != null ? sprite : Meridian.UI.ItemIcons.Get(itemId); // U-059: crafted finds show their icon
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
            Meridian.Terrain.SolidRescue.Register(d.body, true); // U-156 / D-165; U-158: held still while its ground is unloaded (a drop left behind fell through the missing outline)
            d.body.interpolation = RigidbodyInterpolation2D.Interpolate;
            go.AddComponent<BoxCollider2D>().size = Vector2.one * 0.9f;
            return d;
        }
    }
}
