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

        /// <summary>A load the game keeps for the whole session (TerrainTileSet.Preload): reported under "session", never judged.</summary>
        public static AsyncOperationHandle<T> Session<T>(string key)
        {
            var h = Addressables.LoadAssetAsync<T>(key);
            Meridian.Perf.Residency.Track(h, Meridian.Perf.Residency.Session);
            return h;
        }
    }
}
