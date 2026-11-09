using System.Collections.Generic;
using Meridian.Art;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.UI
{
    /// <summary>U-178: a UI fx sheet's frames (B-214's fx/ui/rank_up, expedition_seal) in frame order, for an Image to step through at 12 fps.</summary>
    public static class UiFrames
    {
        public const float Fps = 12f;

        /// <summary>Loads `key`'s frames sorted by their trailing index; `ready` gets them (never on failure). Release the handle when done.</summary>
        public static AsyncOperationHandle<IList<Sprite>> Load(string key, System.Action<Sprite[]> ready)
        {
            var h = ArtLoad.Asset<IList<Sprite>>(key);
            h.Completed += op =>
            {
                if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                var list = new List<Sprite>(op.Result);
                list.Sort((a, b) => Meridian.Player.JetpackOverlay.FrameOf(a).CompareTo(Meridian.Player.JetpackOverlay.FrameOf(b)));
                ready(list.ToArray());
            };
            return h;
        }
    }
}
