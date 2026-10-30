using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Art
{
    /// <summary>Puts the sprite at an asset key (frame 0 of a sheet) on a SpriteRenderer; releases it on destroy.</summary>
    public sealed class AddressableSprite : MonoBehaviour
    {
        public string key;
        public SpriteRenderer target;
        public float worldWidth; // 0 = native size; otherwise scale so the sprite is this wide
        AsyncOperationHandle<IList<Sprite>> handle;

        void Start()
        {
            if (string.IsNullOrEmpty(key) || target == null) return;
            handle = Addressables.LoadAssetAsync<IList<Sprite>>(key);
            handle.Completed += op =>
            {
                if (target == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                Sprite pick = op.Result[0];
                foreach (var s in op.Result) if (s.name.EndsWith("_0")) pick = s;
                target.sprite = pick;
                if (worldWidth > 0f && pick.bounds.size.x > 0f)
                    target.transform.localScale = Vector3.one * (worldWidth / pick.bounds.size.x);
            };
        }

        void OnDestroy()
        {
            if (handle.IsValid()) Addressables.Release(handle);
        }
    }
}
