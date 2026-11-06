using System.Collections.Generic;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.Art
{
    /// <summary>
    /// U-086: every Addressables asset load in the game goes through here, so Residency (Bible §11.1 v3) can count
    /// the live handles per group. Same semantics as Addressables.LoadAssetAsync; callers release the handle as before.
    /// </summary>
    public static class ArtLoad
    {
        public static AsyncOperationHandle<T> Asset<T>(string key)
        {
            var h = Addressables.LoadAssetAsync<T>(key);
            Meridian.Perf.Residency.Track(key, h);
            return h;
        }

        /// <summary>A load by resource location (models and generated materials); `key` names the group.</summary>
        public static AsyncOperationHandle<T> Asset<T>(IResourceLocation location, string key)
        {
            var h = Addressables.LoadAssetAsync<T>(location);
            Meridian.Perf.Residency.Track(key, h);
            return h;
        }

        /// <summary>U-090: every asset under an Addressables label (a stage set), tracked under `group` with the label as its key.</summary>
        public static AsyncOperationHandle<IList<T>> Assets<T>(string label, string group)
        {
            var h = Addressables.LoadAssetsAsync<T>(label, null);
            Meridian.Perf.Residency.Track(h, group, label);
            return h;
        }

        /// <summary>
        /// U-091: every release goes through here. Addressables shares one operation per asset, so a released handle stays
        /// IsValid while another holder (the session preload, a second view) keeps the operation alive; Residency drops
        /// the entry here instead of waiting for IsValid to turn false. Untracked handles (location lists) just release.
        /// </summary>
        public static void Release(AsyncOperationHandle handle)
        {
            if (!handle.IsValid()) return;
            Meridian.Perf.Residency.Untrack(handle);
            Addressables.Release(handle);
        }

        public static void Release<T>(AsyncOperationHandle<T> handle) => Release((AsyncOperationHandle)handle);

        /// <summary>A load the game keeps for the whole session (TerrainTileSet.Preload): reported under "session", never judged.</summary>
        public static AsyncOperationHandle<T> Session<T>(string key)
        {
            var h = Addressables.LoadAssetAsync<T>(key);
            Meridian.Perf.Residency.Track(h, Meridian.Perf.Residency.Session);
            return h;
        }
    }
}
