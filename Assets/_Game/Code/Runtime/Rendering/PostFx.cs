using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Meridian.Rendering
{
    /// <summary>
    /// U-074 (Bible 2.0 §10.5): bloom on emission for the 3D view. One global Volume with a Bloom override, built at
    /// runtime (no asset to author), and post-processing switched on for the cameras that ask. SSAO stays off (budget).
    /// </summary>
    public static class PostFx
    {
        public const float BloomThreshold = 1.0f, BloomIntensity = 0.6f, BloomScatter = 0.6f;
        static Volume volume;

        /// <summary>Creates the global bloom volume once and turns post-processing on for `cam`.</summary>
        public static void Ensure(Camera cam)
        {
            if (volume == null)
            {
                var go = new GameObject("PostFx (bloom)");
                if (Application.isPlaying) Object.DontDestroyOnLoad(go); // EditMode tests: a plain scene object
                volume = go.AddComponent<Volume>();
                volume.isGlobal = true;
                volume.priority = 10f;
                var profile = ScriptableObject.CreateInstance<VolumeProfile>();
                profile.name = "PostFx_Bloom";
                var bloom = profile.Add<Bloom>(true);
                bloom.threshold.Override(BloomThreshold);
                bloom.intensity.Override(BloomIntensity);
                bloom.scatter.Override(BloomScatter);
                volume.sharedProfile = profile;
            }
            if (cam != null)
            {
                var data = cam.GetUniversalAdditionalCameraData();
                if (data != null) data.renderPostProcessing = true;
            }
        }

        public static Bloom ActiveBloom => volume != null && volume.sharedProfile != null && volume.sharedProfile.TryGet<Bloom>(out var b) ? b : null;
    }
}
