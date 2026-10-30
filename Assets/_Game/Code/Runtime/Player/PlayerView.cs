using System.Collections.Generic;
using Meridian.Art;
using Meridian.Rig;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.InputSystem;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Player
{
    /// <summary>Shows the surveyor (frame 0 until animation lands) and faces the move direction.</summary>
    public sealed class PlayerView : MonoBehaviour
    {
        public PlayerController controller;
        public SpriteRenderer view;
        AsyncOperationHandle<IList<Sprite>> handle;

        void Start()
        {
            handle = Addressables.LoadAssetAsync<IList<Sprite>>(ArtKeys.Characters.Surveyor);
            handle.Completed += op =>
            {
                if (view == null) return; // scene unloaded before the load finished
                if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                Sprite first = op.Result[0];
                foreach (var s in op.Result) if (s.name.EndsWith("_0")) first = s;
                view.sprite = first;
            };
        }

        void LateUpdate()
        {
            if (controller != null) view.flipX = controller.Facing < 0;
        }

        void OnDestroy()
        {
            if (handle.IsValid()) Addressables.Release(handle);
        }
    }
}
