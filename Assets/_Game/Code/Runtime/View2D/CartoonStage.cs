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
        /// <summary>P-48 (D-086 / D-099): the v4 cartoon path is the game's path on converted planets; on by default. Tests of the 3D path on Earth switch it off for their run and restore it.</summary>
        public static bool Enabled = true;
        /// <summary>The planets whose v4 art path is on when Enabled (C0: Earth).</summary>
        public static bool Converted(Meridian.Planets.PlanetId id) => id == Meridian.Planets.PlanetId.Earth || id == Meridian.Planets.PlanetId.Mars; // U-118: Mars joins Earth

        public const string SurveyorKey = "characters/surveyor/side";
        public const string EarthScene = "plains";

        /// <summary>U-110 (B-133): the painted scene set for an Earth biome: plains, forest or coast (the ocean band's shore); the biomes without a set yet take the plains. Pure.</summary>
        public static string SceneFor(Meridian.Terrain.Biome biome) => biome switch
        {
            Meridian.Terrain.Biome.Forest => "forest",
            Meridian.Terrain.Biome.Ocean => "coast",
            _ => EarthScene,
        };

        /// <summary>The scene set in use (U-110: set from the spawn column's biome at ConfigureFor).</summary>
        public string Scene { get; private set; } = EarthScene;

        /// <summary>U-118 (B-141): Mars sets by region — the canyon its own set, every other region the plains set; until B-141's plains lands, the plains fall back to the canyon set. The storm set is the veil.</summary>
        public const string MarsFallbackScene = "canyon", StormScene = "storm";
        /// <summary>U-118: the storm veil's sorting offset over the base set, and its wind scroll per second at full intensity (a quarter of the storm's wind: the wall is far).</summary>
        public const int StormVeilOrder = 5;
        public const float StormWind = Meridian.Planet.Weather.DustStorm.WindSpeed * 0.25f;
        /// <summary>The painted set for a planet at column x: Earth by its biome band, Mars by its region (StageRegions), the plains elsewhere. Pure.</summary>
        public static string SceneFor(Meridian.Planets.PlanetId planet, int x)
        {
            if (planet == Meridian.Planets.PlanetId.Earth) return SceneFor(Meridian.Terrain.EarthBiomes.At(x));
            if (planet == Meridian.Planets.PlanetId.Mars) return Meridian.Planet.Backdrop.StageRegions.At(planet, x) == "mars_canyon" ? "canyon" : "plains";
            return EarthScene;
        }
        /// <summary>The storm veil's alpha for a dust storm's intensity (a smooth step: the wall arrives late and lands fully). Pure.</summary>
        public static float StormAlpha(float intensity) { float t = Mathf.Clamp01(intensity); return t * t * (3f - 2f * t); }
        /// <summary>U-118: the B-141 storm set over the base layers on Mars; its alpha follows the dust storm, its scroll the wind.</summary>
        public ParallaxLayers StormLayers { get; private set; }
        Meridian.Planet.Weather.DustStorm storm;

        // ---- U-128: the datum and the set follow the camera's band ----
        /// <summary>The per-band datum sampler (null off the cartoon path); tests and captures read it.</summary>
        public BandDatum Datum { get; private set; }
        /// <summary>The set fading in at a band border (its own ParallaxLayers above the base set); null or inactive between borders.</summary>
        public ParallaxLayers Incoming { get; private set; }
        public bool Fading { get; private set; }
        /// <summary>Border crossfades completed since ConfigureFor (tests read it).</summary>
        public int Crossfades { get; private set; }
        public const float CrossfadeSeconds = 1.5f;
        public const int IncomingOrder = 3;
        /// <summary>The incoming set's alpha `t` seconds into a border crossfade (a smooth step over CrossfadeSeconds). Pure.</summary>
        public static float CrossfadeAlpha(float t, float seconds) { float k = seconds > 0f ? Mathf.Clamp01(t / seconds) : 1f; return k * k * (3f - 2f * k); }
        Meridian.Planets.PlanetId planetId;
        string planetName, incomingScene;
        float fadeT;
        /// <summary>Rigged plants around the camp in C0 (every FloraSpacing m, jittered).</summary>
        public const int FloraCount = 42; // D-136 (2): was 48; the camp's density is the animated-object lever (the gate read 42 Animators against 40)
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
            if (!Active) { if (Layers != null) Layers.gameObject.SetActive(false); if (Sky != null) Sky.gameObject.SetActive(false); if (StormLayers != null) StormLayers.gameObject.SetActive(false); storm = null; return; }

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
            Scene = SceneFor(config.id, side.spawnX); // U-110 / U-118: the spawn's band (Earth) or region (Mars) picks the set
            Layers.SetOrderOffset(0);
            Layers.alpha = 1f;
            Layers.ConfigureFor(config.id.ToString().ToLowerInvariant(), Scene, surfaceDatum, config.id == Meridian.Planets.PlanetId.Mars ? MarsFallbackScene : null);
            // U-128: from here the datum and the set follow the camera's band (FollowBand); the spawn's band keeps this surface, so the camp frames do not move.
            planetId = config.id; planetName = config.id.ToString().ToLowerInvariant();
            Datum = new BandDatum(config.id, config.datumY, side.spawnX, surfaceDatum);
            Fading = false; Crossfades = 0;
            if (Incoming != null) { Incoming.Release(); Incoming.gameObject.SetActive(false); }
            // U-118: Mars draws the dust storm as the B-141 storm set's veil over the base layers (alpha = the storm's intensity, the wind scrolls it).
            if (config.id == Meridian.Planets.PlanetId.Mars)
            {
                if (StormLayers == null) { var wgo = new GameObject("CartoonStormVeil"); wgo.transform.SetParent(transform, false); StormLayers = wgo.AddComponent<ParallaxLayers>(); StormLayers.orderOffset = StormVeilOrder; }
                StormLayers.gameObject.SetActive(true);
                StormLayers.view = cam;
                StormLayers.alpha = 0f;
                StormLayers.scrollX = 0f;
                StormLayers.ConfigureFor("mars", StormScene, surfaceDatum);
                storm = side.dustStorm;
            }
            else { if (StormLayers != null) StormLayers.gameObject.SetActive(false); storm = null; }
            // U-109: the climb sky behind the painted layers, measured against layer0's top edge every frame.
            if (Sky == null) { var sgo = new GameObject("CartoonClimbSky"); sgo.transform.SetParent(transform, false); Sky = sgo.AddComponent<ClimbSky>(); }
            Sky.gameObject.SetActive(true);
            Sky.view = cam; Sky.layers = Layers;
            Sky.ConfigureFor(config, surfaceDatum);
            if (Flora == null) { var fgo = new GameObject("CartoonFlora"); fgo.transform.SetParent(transform, false); Flora = fgo.AddComponent<Meridian.Flora.FloraRigs>(); }
            Flora.view = cam; Flora.player = side.player != null ? side.player.transform : null; Flora.terrain = side.terrain;
            Flora.planet = config.id; // U-110: the biome bands pick the plants
            // Bible §9.6: ≤ 40 animated objects in all. The reserve is what the gate counts besides the flora: the drawn surveyor, the ship's legs rig and its
            // puff sheet, one more for a prop or critter Animator in flight (D-136 (2): the 08:46 gate read 38 flora + 4 = 42).
            Flora.Reserved = 4 + GullCount;
            Flora.Load("flora/" + config.id.ToString().ToLowerInvariant() + "/rigset");
            Flora.Populate(FloraCount, FloraSpacing, side.spawnX + 0.5f, config.id.GetHashCode() * 31 + 7);
            if (Ground == null) { var ggo = new GameObject("CartoonGround"); ggo.transform.SetParent(transform, false); Ground = ggo.AddComponent<GroundStrip>(); }
            Ground.gameObject.SetActive(true);
            Ground.view = cam; Ground.terrain = side.terrain;
            Ground.Load(config.id); // U-118: the planet's strips (Earth's four, Mars's regolith + basalt)
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
                foreach (var a in side.player.GetComponentsInChildren<Animator>(true)) a.enabled = false; // D-136 (2): the hidden 3D / sheet views drive nothing on the cartoon path (and count as animated objects while enabled)
                var go = new GameObject("CartoonSurveyor");
                go.transform.SetParent(side.player.transform, false);
                Surveyor = go.AddComponent<SpriteCharacterView>();
                Surveyor.player = side.player;
                Surveyor.key = SurveyorKey;
            }
        }

        void LateUpdate()
        {
            if (Active && Layers != null && Layers.view != null && Datum != null) FollowBand(Layers.view.transform.position.x);
            if (StormLayers == null || storm == null || !StormLayers.gameObject.activeSelf) return;
            StormLayers.alpha = StormAlpha(storm.Intensity);
            if (storm.Intensity > 0f) StormLayers.scrollX += storm.Intensity * StormWind * Time.deltaTime; // the wind carries the wall
        }

        /// <summary>U-128: the datum of the camera's band (blended at the borders) drives every layer slot and the sky's anchor; at a border the band's set fades in over the base set, then takes its place.</summary>
        void FollowBand(float cameraX)
        {
            int x = Mathf.FloorToInt(cameraX);
            float d = Datum.At(x);
            SetDatum(Layers, d);
            if (Incoming != null && Incoming.gameObject.activeSelf) SetDatum(Incoming, d);
            if (StormLayers != null && StormLayers.gameObject.activeSelf) SetDatum(StormLayers, d);
            if (Sky != null) Sky.anchorY = ParallaxMath.AnchorY(d);
            string want = SceneFor(planetId, x);
            if (!Fading && want != Scene)
            {
                if (Incoming == null) { var igo = new GameObject("CartoonParallaxIncoming"); igo.transform.SetParent(transform, false); Incoming = igo.AddComponent<ParallaxLayers>(); }
                Incoming.gameObject.SetActive(true);
                Incoming.view = Layers.view;
                Incoming.orderOffset = IncomingOrder;
                Incoming.alpha = 0f;
                Incoming.ConfigureFor(planetName, want, d, planetId == Meridian.Planets.PlanetId.Mars ? MarsFallbackScene : null);
                incomingScene = want; fadeT = 0f; Fading = true;
            }
            if (!Fading) return;
            fadeT += Time.deltaTime;
            Incoming.alpha = CrossfadeAlpha(fadeT, CrossfadeSeconds);
            if (fadeT < CrossfadeSeconds) return;
            // The incoming set is the base set now; the old one releases its art.
            var old = Layers;
            Layers = Incoming;
            Incoming = old;
            Layers.SetOrderOffset(0);
            Layers.alpha = 1f;
            Incoming.Release();
            Incoming.gameObject.SetActive(false);
            Scene = incomingScene;
            Fading = false;
            Crossfades++;
            if (Sky != null) Sky.layers = Layers;
        }

        static void SetDatum(ParallaxLayers l, float d) { l.datumY = d; l.anchorY = ParallaxMath.AnchorY(d); }

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
