using Meridian.Core;
using Meridian.Player;
using UnityEngine;

namespace Meridian.View2D
{
    /// <summary>
    /// U-094 (Bible §9 v4, D-086): the v4 2D render path for the side view, switched on per planet while the conversion
    /// runs (C0: Earth only). On: the side camera turns orthographic 16.875 m tall with the §5.1 stage rules, the painted
    /// parallax scene replaces the 3D stage layers / depth bands / sky backdrop, and the surveyor draws as a
    /// SpriteCharacterView (characters/surveyor/side) instead of the 3D model. Gameplay, terrain and physics are untouched;
    /// the 3D path stays for every planet not converted yet (and for the archive).
    /// </summary>
    public sealed class CartoonStage : MonoBehaviour
    {
        /// <summary>Master switch (tests, the C0 style-test entry). Off by default until LEAD converts a planet.</summary>
        public static bool Enabled;
        /// <summary>The planets whose v4 art path is on when Enabled (C0: Earth).</summary>
        public static bool Converted(Meridian.Planets.PlanetId id) => id == Meridian.Planets.PlanetId.Earth;

        public const string SurveyorKey = "characters/surveyor/side";
        public const string EarthScene = "plains";

        public ParallaxLayers Layers { get; private set; }
        public SpriteCharacterView Surveyor { get; private set; }
        public bool Active { get; private set; }

        /// <summary>Called by PlanetSideRoot.Configure after everything else is set up.</summary>
        public void ConfigureFor(PlanetSideRoot side, Meridian.Planets.PlanetConfig config, float surfaceDatum)
        {
            Active = Enabled && config != null && Converted(config.id);
            // The 3D scenery (stage layers, depth bands, sky backdrop) runs only off the cartoon path; each has its own object.
            SetActive(side.stage, !Active, side);
            SetActive(side.depthBands, !Active, side);
            SetActive(side.backdrop, !Active, side);
            if (!Active) { if (Layers != null) Layers.gameObject.SetActive(false); return; }

            var cam = side.sideCamera;
            var follow = cam != null ? cam.GetComponent<CameraFollow>() : null;
            if (follow != null) follow.UseCartoonFrame();
            else if (cam != null) { cam.orthographic = true; cam.orthographicSize = SheetClock.FrameHeight * 0.5f; }
            // Bible §9.4 v4: no bloom / HDR post on the cartoon camera; the film pass (U-095) is a renderer feature, not a volume.
            if (cam != null) { var extra = cam.GetComponent<UnityEngine.Rendering.Universal.UniversalAdditionalCameraData>(); if (extra != null) extra.renderPostProcessing = false; }


            if (Layers == null)
            {
                var go = new GameObject("CartoonParallax");
                go.transform.SetParent(transform, false);
                Layers = go.AddComponent<ParallaxLayers>();
            }
            Layers.gameObject.SetActive(true);
            Layers.view = cam;
            Layers.ConfigureFor(config.id.ToString().ToLowerInvariant(), EarthScene, surfaceDatum);

            if (side.player != null && Surveyor == null)
            {
                // The 3D/sheet surveyor views step aside; the v3 sheet draws at the feet with its squash root.
                var view = side.player.GetComponentInChildren<PlayerView>(true);
                if (view != null) view.enabled = false;
                foreach (var r in side.player.GetComponentsInChildren<Renderer>(true)) r.enabled = false;
                var go = new GameObject("CartoonSurveyor");
                go.transform.SetParent(side.player.transform, false);
                Surveyor = go.AddComponent<SpriteCharacterView>();
                Surveyor.player = side.player;
                Surveyor.key = SurveyorKey;
            }
        }

        static void SetActive(Component c, bool on, PlanetSideRoot side)
        {
            if (c == null || c.gameObject == side.gameObject) return;
            if (c.gameObject.activeSelf != on) c.gameObject.SetActive(on);
        }
    }
}
