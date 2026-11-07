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
        /// <summary>Rigged plants around the camp in C0 (every FloraSpacing m, jittered).</summary>
        public const int FloraCount = 48;
        public const float FloraSpacing = 2.5f;
        /// <summary>U-101 / B-113: gulls over the camp in C0.</summary>
        public const int GullCount = 1;

        public ParallaxLayers Layers { get; private set; }
        /// <summary>U-109: the sky above the painted layers (the gradient to space black and the starfield over the last third of the climb).</summary>
        public ClimbSky Sky { get; private set; }
        /// <summary>U-097: the planet's rigged flora (placeholder set until B-112).</summary>
        public Meridian.Flora.FloraRigs Flora { get; private set; }
        /// <summary>U-100: the cartoon ground placeholder over the block faces.</summary>
        public GroundStrip Ground { get; private set; }
        public SpriteCharacterView Surveyor { get; private set; }
        public bool Active { get; private set; }

        /// <summary>Called by PlanetSideRoot.Configure after everything else is set up.</summary>
        public void ConfigureFor(PlanetSideRoot side, Meridian.Planets.PlanetConfig config, float surfaceDatum)
        {
            Active = Enabled && config != null && Converted(config.id);
            // U-100: every 3D model (props, the Pilgrim) wears the flat silhouette on the cartoon path; off, their own materials.
            Meridian.Art.ModelView.CartoonMaterial = Active && Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.cartoon : null;
            if (Ground != null) Ground.gameObject.SetActive(Active);
            // The 3D scenery (stage layers, depth bands, sky backdrop) runs only off the cartoon path; each has its own object.
            SetActive(side.stage, !Active, side);
            SetActive(side.depthBands, !Active, side);
            SetActive(side.backdrop, !Active, side);
            if (!Active) { if (Layers != null) Layers.gameObject.SetActive(false); if (Sky != null) Sky.gameObject.SetActive(false); return; }

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
            // U-109: the climb sky behind the painted layers, measured against layer0's top edge every frame.
            if (Sky == null) { var sgo = new GameObject("CartoonClimbSky"); sgo.transform.SetParent(transform, false); Sky = sgo.AddComponent<ClimbSky>(); }
            Sky.gameObject.SetActive(true);
            Sky.view = cam; Sky.layers = Layers;
            Sky.ConfigureFor(config, surfaceDatum);
            if (Flora == null) { var fgo = new GameObject("CartoonFlora"); fgo.transform.SetParent(transform, false); Flora = fgo.AddComponent<Meridian.Flora.FloraRigs>(); }
            Flora.view = cam; Flora.player = side.player != null ? side.player.transform : null; Flora.terrain = side.terrain;
            Flora.Reserved = 1 + GullCount; // the surveyor and the critters (Bible §9.6: ≤ 40 animated objects in all)
            Flora.Load("flora/" + config.id.ToString().ToLowerInvariant() + "/rigset");
            Flora.Populate(FloraCount, FloraSpacing, side.spawnX + 0.5f, config.id.GetHashCode() * 31 + 7);
            if (Ground == null) { var ggo = new GameObject("CartoonGround"); ggo.transform.SetParent(transform, false); Ground = ggo.AddComponent<GroundStrip>(); }
            Ground.gameObject.SetActive(true);
            Ground.view = cam; Ground.terrain = side.terrain;
            Ground.Load();
            if (Meridian.Art.ModelView.CartoonMaterial != null) foreach (var mv in side.GetComponentsInChildren<Meridian.Art.ModelView>(true)) mv.Wear(Meridian.Art.ModelView.CartoonMaterial);
            // U-101: one gull (B-113) over the camp; the director keeps it (it flees and bumps like any critter).
            if (side.creatures != null && side.player != null && side.creatures.CountOf(Meridian.Creatures.Species.Gull) < GullCount)
                side.creatures.Spawn(Meridian.Creatures.Species.Gull, (Vector2)side.player.transform.position + new Vector2(7f, 3.5f));

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
            // U-107: PlanetBackdrop lives on the side camera's object; switching that object off silenced CameraFollow (the ship
            // flew out of frame in the C0 stage). A component on the camera is muted by `enabled` (its OnDisable hides its quads).
            if (side.sideCamera != null && c.gameObject == side.sideCamera.gameObject)
            {
                if (c is Behaviour b && b.enabled != on) b.enabled = on;
                return;
            }
            if (c.gameObject.activeSelf != on) c.gameObject.SetActive(on);
        }
    }
}
