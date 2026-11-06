using System;
using UnityEngine;

namespace Meridian.Planet.Backdrop
{
    /// <summary>
    /// U-090: the region's `stage.json` (contract §10), authored by BLENDER beside ridge_mid.glb and addressed by
    /// ArtImporter as `backgrounds/&lt;planet&gt;_&lt;region&gt;/stage`. Set-pieces sit at `at` (a fraction of the region
    /// width from its western edge) at depth `z`; the foreground lists its piece names and spacing; haze_rgb tints
    /// the far layers. Default() stands in for regions without one.
    /// </summary>
    [Serializable]
    public sealed class StageManifest
    {
        [Serializable]
        public sealed class SetPiece
        {
            public string key = "setpiece_a";
            public float at = 0.5f;
            public float z = 100f;
            public float scale = 1f;
            public bool mirror;
        }

        [Serializable]
        public sealed class Foreground
        {
            public string[] pieces = DefaultPieces;
            public float spacing_m = 12f;
        }

        public static readonly string[] DefaultPieces = { "tuft", "fern", "boulder", "log" };

        public string region = "";
        public SetPiece[] setpieces = Array.Empty<SetPiece>();
        public Foreground foreground = new Foreground();
        public float[] haze_rgb = { 0.72f, 0.78f, 0.86f };

        public Color Haze => haze_rgb != null && haze_rgb.Length >= 3 ? new Color(haze_rgb[0], haze_rgb[1], haze_rgb[2], 1f) : new Color(0.72f, 0.78f, 0.86f, 1f);
        public float Spacing => foreground != null && foreground.spacing_m > 1f ? foreground.spacing_m : 12f;
        public string[] Pieces => foreground != null && foreground.pieces != null && foreground.pieces.Length > 0 ? foreground.pieces : DefaultPieces;

        public static StageManifest Default(string region) => new StageManifest { region = region };

        /// <summary>Parses a stage.json; a broken file logs once and falls back to Default.</summary>
        public static StageManifest Parse(string region, string json)
        {
            if (string.IsNullOrEmpty(json)) return Default(region);
            try
            {
                var m = JsonUtility.FromJson<StageManifest>(json);
                if (m == null) return Default(region);
                if (string.IsNullOrEmpty(m.region)) m.region = region;
                if (m.setpieces == null) m.setpieces = Array.Empty<SetPiece>();
                if (m.foreground == null) m.foreground = new Foreground();
                return m;
            }
            catch (Exception e)
            {
                Debug.LogWarning($"[StageLayers] {region}/stage.json unreadable ({e.Message}); using defaults.");
                return Default(region);
            }
        }
    }
}
