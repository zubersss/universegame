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
        /// <summary>U-168: the cartoon path draws the current planet (GameState's), so the v2 models it never shows are not loaded.</summary>
        public static bool DrawsCurrentPlanet => Enabled && Meridian.Core.GameState.Instance != null && Converted(Meridian.Core.GameState.Instance.currentPlanet);
        /// <summary>The planets whose v4 art path is on when Enabled (C0: Earth).</summary>
        public static bool Converted(Meridian.Planets.PlanetId id) => id == Meridian.Planets.PlanetId.Earth || id == Meridian.Planets.PlanetId.Mars || id == Meridian.Planets.PlanetId.Mercury || id == Meridian.Planets.PlanetId.Venus || id == Meridian.Planets.PlanetId.Jupiter || id == Meridian.Planets.PlanetId.Saturn || id == Meridian.Planets.PlanetId.Uranus || id == Meridian.Planets.PlanetId.Neptune; // U-118: Mars joins Earth; U-123: Mercury; U-125: Venus; U-127: Jupiter; U-129: Saturn; U-130: Uranus; U-133: Neptune

        public const string SurveyorKey = "characters/surveyor/side";
        public const string EarthScene = "plains";

        /// <summary>U-110 (B-133): the painted scene set for an Earth biome: plains, forest or coast (the ocean band's shore); the biomes without a set yet take the plains. Pure.</summary>
        public static string SceneFor(Meridian.Terrain.Biome biome) => biome switch
        {
            Meridian.Terrain.Biome.Forest => "forest",
            Meridian.Terrain.Biome.Ocean => "coast",
            Meridian.Terrain.Biome.Desert => "desert", // U-161: B-179's sets
            Meridian.Terrain.Biome.Taiga => "taiga",
            Meridian.Terrain.Biome.Tundra => "tundra",
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
            if (planet == Meridian.Planets.PlanetId.Mars) return MarsSceneFor(x);
            return EarthScene;
        }
        /// <summary>U-159 (B-185, B-186): Mars's sets by landform: the polar caps' "polar", Olympus's "tharsis", the canyon's "canyon", the plains. Pure.</summary>
        public static string MarsSceneFor(int x) => Meridian.Terrain.MarsLandforms.At(x) switch
        {
            Meridian.Terrain.MarsFeature.PolarCap => "polar",
            Meridian.Terrain.MarsFeature.Olympus => "tharsis",
            Meridian.Terrain.MarsFeature.Canyon => "canyon",
            _ => "plains",
        };

        /// <summary>The storm veil's alpha for a dust storm's intensity (a smooth step: the wall arrives late and lands fully). Pure.</summary>
        public static float StormAlpha(float intensity) { float t = Mathf.Clamp01(intensity); return t * t * (3f - 2f * t); }
        /// <summary>U-123 (B-149): Mercury's three sets — day, twilight, night — by the terminator's zone at the camera column; a cold trap is the night set on either side
        /// (permanent shadow). The twilight set (the band the player runs through) stands in for a set not exported yet.</summary>
        public const string MercuryDayScene = "day", MercuryTwilightScene = "twilight", MercuryNightScene = "night", MercuryFallbackScene = MercuryTwilightScene;
        /// <summary>The Mercury set at column x for the terminator's clock (real seconds, MercuryClock) and the world width. Pure.</summary>
        public static string MercurySceneFor(int x, double realSeconds, int width)
        {
            if (width <= 0) return MercuryDayScene;
            if (Meridian.Terrain.MercuryLandforms.InColdTrap(x, width)) return MercuryNightScene;
            switch (Meridian.Terrain.MercuryTerminator.ZoneAt(x, realSeconds, width))
            {
                case Meridian.Terrain.MercuryZone.Night: return MercuryNightScene;
                case Meridian.Terrain.MercuryZone.Twilight: return MercuryTwilightScene;
                default: return MercuryDayScene;
            }
        }
        /// <summary>U-125 (B-152): Venus's two sets by the camera's height: the cloud deck above, the surface dive below. The deck set takes over at
        /// VenusDeckEnterY and hands back at VenusDeckLeaveY (between them the set stays as it is, so a hover on the line never flickers).</summary>
        public const string VenusDeckScene = "deck", VenusSurfaceScene = "surface", VenusFallbackScene = VenusSurfaceScene;
        public const float VenusDeckEnterY = 700f, VenusDeckLeaveY = 640f;
        /// <summary>The Venus set for a camera at height y, given the set shown now (null: none yet). Pure.</summary>
        public static string VenusSceneFor(float y, string current)
        {
            if (y >= VenusDeckEnterY) return VenusDeckScene;
            if (y <= VenusDeckLeaveY) return VenusSurfaceScene;
            if (current == VenusDeckScene || current == VenusSurfaceScene) return current;
            return y >= (VenusDeckEnterY + VenusDeckLeaveY) * 0.5f ? VenusDeckScene : VenusSurfaceScene;
        }
        /// <summary>The level a Venus set hangs off: the deck set off the cloud deck (the old backdrop's DeckY − 2), the surface set off the ground's band datum. Pure.</summary>
        public static float VenusDatumFor(string scene, float groundDatum) => scene == VenusDeckScene ? Meridian.Terrain.VenusLandforms.DeckY - 2f : groundDatum;
        /// <summary>U-127 (B-155): Jupiter's four sets by the camera's band of the cloud column (deck1 1100–900, deck2 900–600, deck3 600–300, the
        /// deep 300–100 with the CRUSH band on its near layer); a set holds JupiterBorderHold metres past its borders (no flicker on a line); each hangs
        /// off its band's floor, so the deep set's CRUSH band lies on the Crush Line. "spot" is the Red Spot's layer1 overlay.</summary>
        public const string JupiterDeck1 = "deck1", JupiterDeck2 = "deck2", JupiterDeck3 = "deck3", JupiterDeep = "deep", JupiterFallbackScene = JupiterDeck1, JupiterSpotScene = "spot";
        public const float JupiterBorderHold = 20f;
        /// <summary>The Jupiter set at height y (above the Datum: deck1). Pure.</summary>
        public static string JupiterSceneAt(float y) => y >= Meridian.Terrain.CloudColumn.CloudLayout.Deck1Bottom ? JupiterDeck1
            : y >= Meridian.Terrain.CloudColumn.CloudLayout.Deck2Bottom ? JupiterDeck2 : y >= Meridian.Terrain.CloudColumn.CloudLayout.Deck3Bottom ? JupiterDeck3 : JupiterDeep;
        /// <summary>The Jupiter set for a camera at y given the set shown now: the current one holds within JupiterBorderHold of its band. Pure.</summary>
        public static string JupiterSceneFor(float y, string current)
        {
            string at = JupiterSceneAt(y);
            if (current == null || current == at || JupiterFloor(current) < 0f) return at;
            return y > JupiterFloor(current) - JupiterBorderHold && y < JupiterTop(current) + JupiterBorderHold ? current : at;
        }
        /// <summary>A Jupiter set's floor (its datum), -1 for an unknown set. Pure.</summary>
        public static float JupiterFloor(string scene) => scene == JupiterDeck1 ? Meridian.Terrain.CloudColumn.CloudLayout.Deck1Bottom
            : scene == JupiterDeck2 ? Meridian.Terrain.CloudColumn.CloudLayout.Deck2Bottom : scene == JupiterDeck3 ? Meridian.Terrain.CloudColumn.CloudLayout.Deck3Bottom
            : scene == JupiterDeep ? Meridian.Terrain.CloudColumn.CloudLayout.CrushLine : -1f;
        static float JupiterTop(string scene) => scene == JupiterDeck1 ? float.MaxValue : scene == JupiterDeck2 ? Meridian.Terrain.CloudColumn.CloudLayout.Deck1Bottom
            : scene == JupiterDeck3 ? Meridian.Terrain.CloudColumn.CloudLayout.Deck2Bottom : Meridian.Terrain.CloudColumn.CloudLayout.Deck3Bottom;
        /// <summary>U-127: the Red Spot overlay's alpha at column x: 1 inside the zone, faded out over SpotFade columns past its edge. Pure.</summary>
        public const int SpotFade = 48;
        /// <summary>U-129 / U-130: the giants that share the deck machinery (the four sets by band, each off its band's floor): Jupiter, Saturn, Uranus.</summary>
        public static bool Decked(Meridian.Planets.PlanetId p) => p == Meridian.Planets.PlanetId.Jupiter || p == Meridian.Planets.PlanetId.Saturn || p == Meridian.Planets.PlanetId.Uranus || p == Meridian.Planets.PlanetId.Neptune;
        /// <summary>The decked giants with a zone overlay on the veil slot (Jupiter's Red Spot, Saturn's Hexagon); Uranus has none.</summary>
        public static bool HasZoneOverlay(Meridian.Planets.PlanetId p) => p == Meridian.Planets.PlanetId.Jupiter || p == Meridian.Planets.PlanetId.Saturn;
        /// <summary>U-130 (B-158, D-142): a Uranus set is "&lt;deck&gt;_&lt;light&gt;" (deck1_sun_left, deck2_night ...): the deck by the camera's band as
        /// Jupiter's, the light by the season clock (UranusSeason), every light one geometry, so the U-128 crossfade turns the light and nothing slides.
        /// "+survey" asks for the deck's survey layer0 (the methane bands lifted) under the same light's layers 1–2.</summary>
        public const string UranusFallbackScene = "deck1_sun_left", SurveySuffix = "+survey";
        /// <summary>The deck a set belongs to (the part before its light): "deck2_night" → "deck2"; a Jupiter / Saturn set is its own deck. Pure.</summary>
        public static string DeckOf(string scene)
        {
            if (string.IsNullOrEmpty(scene)) return scene;
            scene = scene.TrimEnd('~'); // U-144: a mirrored set ("deck2~") is its deck's
            int at = scene.IndexOf('@'); if (at >= 0) return scene.Substring(at + 1); // U-133: a zone set carries its band: "storm@deck2"
            int i = scene.IndexOfAny(new[] { '_', '+' }); return i < 0 ? scene : scene.Substring(0, i);
        }
        /// <summary>The light of a Uranus set ("deck2_sun_right+survey" → "sun_right"), null for a set without one. Pure.</summary>
        public static string LightOf(string scene)
        {
            if (string.IsNullOrEmpty(scene)) return null;
            string set = SetOf(scene); int i = set.IndexOf('_');
            return i < 0 ? null : set.Substring(i + 1);
        }
        /// <summary>The set whose layers load (the "+survey" ask dropped). Pure.</summary>
        public static string SetOf(string scene) { if (string.IsNullOrEmpty(scene)) return scene; int i = scene.IndexOfAny(new[] { '+', '@', '~' }); return i < 0 ? scene : scene.Substring(0, i); }
        /// <summary>U-144 (D-148): "~" marks a set shown mirrored (Neptune's −x wind zone: its layers flipped, never a second drawing); the U-128
        /// crossfade turns it like any other change of set.</summary>
        public const string MirrorSuffix = "~";
        public static bool MirrorOf(string scene) => !string.IsNullOrEmpty(scene) && scene.EndsWith(MirrorSuffix);
        /// <summary>The sibling set layer0 comes from: the deck's survey set when "+survey" is asked, else null (the set's own). Pure.</summary>
        public static string Layer0Of(string scene) => !string.IsNullOrEmpty(scene) && scene.EndsWith(SurveySuffix) ? DeckOf(scene) + "_" + Meridian.Planet.UranusSeason.Survey : null;
        /// <summary>A decked set's floor (its datum) by its deck, whatever its light: -1 for an unknown set. Pure.</summary>
        public static float DeckFloor(string scene) => JupiterFloor(DeckOf(scene));
        /// <summary>The Uranus set for a camera at (x, y) at game time t (a season of the given length), given the set shown now; survey asks for the
        /// survey layer0. The deck holds as Jupiter's at its band's borders, the light at a hemisphere's border (UranusSeason.LightFor). Pure.</summary>
        /// <summary>U-133 (B-161): Neptune's zone sets, the Dark Storm ("storm", its rim layer pulsed) and the Great Dark Spot ("spot", the same set
        /// with the Meridian far off; it shares the storm's layers 1–2). Shown over decks 1–3 as "&lt;zone&gt;@&lt;deck&gt;", hung off the band's floor.</summary>
        public const string NeptuneStormScene = "storm", NeptuneSpotScene = "spot";
        /// <summary>The sibling set a scene's layers 1–2 come from: the storm's for the spot, else null. Pure.</summary>
        public static string UpperOf(string scene) => SetOf(scene) == NeptuneSpotScene ? NeptuneStormScene : null;
        /// <summary>The Neptune set for a camera at (x, y) at game time t given the set shown now: the Deep keeps its set; above it the Great Dark
        /// Spot, then the drifting storm, else the band's deck. A zone holds JupiterBorderHold columns past its edge. Pure.</summary>
        public static string NeptuneSceneFor(float y, int x, int width, double t, string current)
        {
            string deck = JupiterSceneFor(y, DeckOf(current));
            // U-144: the −x wind zone shows its set mirrored (held ZoneHold columns past the zone's border).
            int dir = Meridian.Planet.Weather.NeptuneWind.DirectionFor(x, current == null ? 0 : MirrorOf(current) ? -1 : 1);
            string mirror = dir < 0 ? MirrorSuffix : "";
            if (deck == JupiterDeep) return JupiterDeep + mirror;
            string zone = SetOf(current);
            int hold = (int)JupiterBorderHold;
            if (Meridian.Planet.Weather.NeptuneStorms.InDarkSpot(x, width, zone == NeptuneSpotScene ? hold : 0)) return NeptuneSpotScene + "@" + deck + mirror;
            if (Meridian.Planet.Weather.NeptuneStorms.InStorm(x, t, width, zone == NeptuneStormScene ? hold : 0)) return NeptuneStormScene + "@" + deck + mirror;
            return deck + mirror;
        }
        public static string UranusSceneFor(float y, int x, int width, double t, double season, string current, bool survey) =>
            JupiterSceneFor(y, DeckOf(current)) + "_" + Meridian.Planet.UranusSeason.LightFor(x, width, t, season, LightOf(current)) + (survey ? SurveySuffix : "");
        /// <summary>U-129 (B-157): Saturn's North Polar Hexagon overlay (the six wind-walls on layer1, the tilted rings).</summary>
        public const string SaturnHexagonScene = "hexagon";
        /// <summary>A decked giant's zone overlay: Jupiter's Red Spot, Saturn's Hexagon. Pure.</summary>
        public static string OverlayFor(Meridian.Planets.PlanetId p) => p == Meridian.Planets.PlanetId.Saturn ? SaturnHexagonScene : JupiterSpotScene;
        /// <summary>The zone overlay's alpha at column x on a decked giant. Pure.</summary>
        public static float OverlayAlpha(Meridian.Planets.PlanetId p, int x) => p == Meridian.Planets.PlanetId.Saturn ? HexagonAlpha(x) : SpotAlpha(x);
        /// <summary>U-129: the Hexagon overlay's alpha: 1 inside the zone, faded over SpotFade columns past its edge. Pure.</summary>
        public static float HexagonAlpha(int x)
        {
            int d = Mathf.Abs(Meridian.Terrain.CloudColumn.CloudLayout.HexagonOffset(x)) - Meridian.Terrain.CloudColumn.CloudLayout.HexagonHalfWidth;
            return d <= 0 ? 1f : CrossfadeAlpha(SpotFade - d, SpotFade);
        }
        public static float SpotAlpha(int x)
        {
            int d = Mathf.Abs(Meridian.Terrain.CloudColumn.CloudLayout.RedSpotOffset(x)) - Meridian.Terrain.CloudColumn.CloudLayout.RedSpotHalfWidth;
            return d <= 0 ? 1f : CrossfadeAlpha(SpotFade - d, SpotFade);
        }
        /// <summary>The set a planet falls back to while a set is not exported yet (Mars: the canyon; Mercury: the twilight; Venus: the surface; Jupiter: deck1); null: the placeholder tints. Pure.</summary>
        public static string FallbackFor(Meridian.Planets.PlanetId planet) => planet == Meridian.Planets.PlanetId.Mars ? MarsFallbackScene : planet == Meridian.Planets.PlanetId.Mercury ? MercuryFallbackScene
            : planet == Meridian.Planets.PlanetId.Venus ? VenusFallbackScene : planet == Meridian.Planets.PlanetId.Uranus ? UranusFallbackScene : Decked(planet) ? JupiterFallbackScene : null;
        /// <summary>U-125: a set's datum: Venus's deck set hangs off the cloud deck, every other set off the ground's band datum.</summary>
        float DatumFor(string scene, float groundDatum) => planetId == Meridian.Planets.PlanetId.Venus ? VenusDatumFor(scene, groundDatum)
            : Decked(planetId) && DeckFloor(scene) >= 0f ? DeckDatum(scene) : groundDatum; // U-153: a decked set off the floe under the camera

        /// <summary>U-153 (P-52): a decked giant's floe datum glides (FloeDatumTime) to the floe under the camera; it snaps past FloeSnap (a load, a
        /// teleport) and holds where no floe is within FloeScanDepth under the camera (flying through open air).</summary>
        public const float FloeDatumTime = 0.5f, FloeScanDepth = 80f, FloeSnap = 120f;
        /// <summary>U-153: the smoothed standing height of the floe under the camera (NaN until one is found): every decked set hangs off it.</summary>
        public float FloeDatum => floeDatum;
        float floeDatum = float.NaN, floeDatumVel;
        Meridian.Terrain.CloudColumn.CloudWorldGenerator cloud;

        /// <summary>U-153: a decked set's datum: the floe under the camera (so the set's ground line sits at the floe tops, B-155's composition),
        /// clamped inside the set's band, through the U-128 crossfade alike; its band's floor until a floe is found. The CRUSH band rides the
        /// deep's floe line with it.</summary>
        float DeckDatum(string scene)
        {
            float floor = DeckFloor(scene);
            return float.IsNaN(floeDatum) ? floor : Mathf.Clamp(floeDatum, floor, JupiterTop(DeckOf(scene)));
        }

        void StepFloeDatum(float x, float y, float dt)
        {
            if (cloud == null || !cloud.FloeTopUnder(x, y, y - FloeScanDepth, out float top)) return;
            if (float.IsNaN(floeDatum) || dt <= 0f || Mathf.Abs(top - floeDatum) > FloeSnap) { floeDatum = top; floeDatumVel = 0f; return; }
            floeDatum = Mathf.SmoothDamp(floeDatum, top, ref floeDatumVel, FloeDatumTime, Mathf.Infinity, dt);
        }
        /// <summary>Mercury's clock for the stage: the terminator's real seconds plus the hazards' offset — the clock the creatures and the flares read, so the painted band is theirs.</summary>
        public double MercuryClock => Meridian.Terrain.MercuryTerminator.Now(clock != null ? clock.GameSeconds : 0) + (hazards != null ? hazards.mercuryClockOffset : 0);
        /// <summary>The set wanted at column x now: Earth by its band, Mars by its region, Mercury by the terminator's clock.</summary>
        string SceneNow(int x) => planetId == Meridian.Planets.PlanetId.Mercury ? MercurySceneFor(x, MercuryClock, worldWidth)
            : planetId == Meridian.Planets.PlanetId.Venus ? VenusSceneFor(Layers != null && Layers.view != null ? Layers.view.transform.position.y : 0f, Scene) // U-125: by the camera's height
            : planetId == Meridian.Planets.PlanetId.Neptune ? NeptuneSceneFor(Layers != null && Layers.view != null ? Layers.view.transform.position.y : 0f, x, worldWidth, GameTime, Scene) // U-133: the band and the storm zones
            : planetId == Meridian.Planets.PlanetId.Uranus ? UranusSceneFor(Layers != null && Layers.view != null ? Layers.view.transform.position.y : 0f, x, worldWidth, GameTime, seasonSeconds, Scene, SurveyView) // U-130: the band and the season's light
            : Decked(planetId) ? JupiterSceneFor(Layers != null && Layers.view != null ? Layers.view.transform.position.y : 0f, Scene) // U-127: by the camera's band
            : SceneFor(planetId, x);
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

        // ---- U-171 (B-200's read, B-202's art): the sea from below ----
        /// <summary>B-202's backgrounds/earth/sea_under under the water line over Earth's sea (its own set: the water column, the far and the near
        /// seabed, the surface seen from below), anchored on the water line and following the camera down; null off Earth's smooth sea.</summary>
        public ParallaxLayers SeaUnder { get; private set; }
        /// <summary>Over the land sets (the base set and an incoming one), under the terrain.</summary>
        public const int SeaUnderOrder = 20;
        /// <summary>The shore's crossfade (m): the sea weight is the sea columns' share within half of it either side of the camera (U-128's 3 m).</summary>
        public const float ShoreBlend = 3f;
        /// <summary>U-188: the water tiles' alpha out at sea while sea_under shows (TerrainChunk.WaterAlpha elsewhere).</summary>
        public const float SeaWaterAlpha = 0.2f;
        /// <summary>sea_under's layers that continue down (B-202's json gives them continue_rows 64): the water column, the far and the near seabed,
        /// and B-225's shallow seabed (layer4); the surface seen from below (layer3) does not.</summary>
        static readonly int[] SeaContinues = { 0, 1, 2, 4 };
        /// <summary>U-205 (B-225): a layer with a json shore_m (sea_under's shallow seabed: 40) shows only that far out from the shore, fading
        /// out over the last ShallowsFade metres (BLENDER's preview: 8).</summary>
        public const float ShallowsFade = 8f;
        /// <summary>How far the camera is out from the shore now (m; 0 on land), read up to the set's largest shore_m; tests read it.</summary>
        public float ShoreDistanceNow { get; private set; }
        System.Func<int, bool> seaAt; // one delegate for the planet's visit (no allocation a frame)

        /// <summary>U-205: how far x is out from the nearest land column's edge (m): 0 on land; `reach` + 1 where no land lies within `reach`
        /// columns either way. Pure over `sea`.</summary>
        public static float ShoreDistance(float x, int reach, System.Func<int, bool> sea)
        {
            int c = Mathf.FloorToInt(x);
            if (!sea(c)) return 0f;
            float frac = x - c, best = reach + 1f;
            for (int k = 1; k <= reach; k++)
            {
                if (!sea(c - k)) best = Mathf.Min(best, frac + k - 1f); // the land column's right edge
                if (!sea(c + k)) best = Mathf.Min(best, k - frac);      // the land column's left edge
                if (best <= k) break; // land found: nothing farther out is nearer
            }
            return best;
        }

        /// <summary>U-205: a shore layer's weight `d` metres out from the shore: whole up to shoreM − ShallowsFade, gone from shoreM on; 1 for a
        /// layer with no shore_m. Pure.</summary>
        public static float ShallowsWeight(float d, float shoreM) => shoreM <= 0f ? 1f : Mathf.Clamp01((shoreM - d) / ShallowsFade);
        /// <summary>The sea weight at the camera now (0 over land, 1 out at sea): sea_under's alpha; the land set's nearest layer fades by 1 − it.</summary>
        public float SeaWeight { get; private set; }
        float waterLine = float.NegativeInfinity;
        Meridian.Terrain.SolidWorldGenerator seaWorld;

        /// <summary>The sea columns' share within ShoreBlend / 2 of x (sampled per half metre: 7 samples). Pure over `sea`.</summary>
        public static float SeaShare(float x, System.Func<int, bool> sea)
        {
            int n = 0, s = 0;
            for (float d = -ShoreBlend * 0.5f; d <= ShoreBlend * 0.5f + 1e-3f; d += 0.5f, n++) if (sea(Mathf.FloorToInt(x + d))) s++;
            return n > 0 ? (float)s / n : 0f;
        }

        void ConfigureSea(PlanetSideRoot side, Meridian.Planets.PlanetConfig config)
        {
            seaWorld = config.id == Meridian.Planets.PlanetId.Earth && side.terrain != null && side.terrain.SmoothGround ? side.terrain.BaseGenerator as Meridian.Terrain.SolidWorldGenerator : null;
            SeaWeight = 0f; ShoreDistanceNow = 0f;
            Meridian.Terrain.TerrainChunk.LiquidAlpha = Meridian.Terrain.TerrainChunk.WaterAlpha; // U-188: each planet starts with the plain tint
            if (seaWorld == null) { if (SeaUnder != null) { SeaUnder.Release(); SeaUnder.gameObject.SetActive(false); } waterLine = float.NegativeInfinity; seaAt = null; return; }
            var world = seaWorld;
            seaAt = x => world.SeaAt(x);
            waterLine = config.datumY + 1f; // PlanetBackdrop's sea level: the water fills the datum row
            if (SeaUnder == null) { var g = new GameObject("CartoonSeaUnder"); g.transform.SetParent(transform, false); SeaUnder = g.AddComponent<ParallaxLayers>(); }
            SeaUnder.gameObject.SetActive(false); // until the camera is out at sea and under the surface
            SeaUnder.view = Layers.view;
            SeaUnder.orderOffset = SeaUnderOrder;
            SeaUnder.followBelow = true;
            SeaUnder.alpha = 0f;
            SeaUnder.continueOnly = SeaContinues; // the water column and the two seabeds go on down past their sheets (to any depth); the surface band does not
            seaConfigured = false;
        }
        bool seaConfigured;

        /// <summary>Out at sea the land set's nearest layer gives way and sea_under shows under the water line; at the shore they crossfade over
        /// ShoreBlend; above the water, or on land, sea_under is off (no draw).</summary>
        void FollowSea()
        {
            if (seaWorld == null || Layers == null || Layers.view == null) { SeaWeight = 0f; Meridian.Terrain.TerrainChunk.LiquidAlpha = Meridian.Terrain.TerrainChunk.WaterAlpha; return; }
            var cam = Layers.view;
            var c = cam.transform.position;
            float w = SeaShare(c.x, seaAt);
            SeaWeight = w;
            Layers.nearAlpha = 1f - w;
            if (Incoming != null) Incoming.nearAlpha = 1f - w;
            float half = Meridian.CameraRig.SideView.HalfHeight(cam);
            bool under = w > 0f && c.y - half < waterLine; // some of the frame is under the water line
            if (SeaUnder.gameObject.activeSelf != under) SeaUnder.gameObject.SetActive(under);
            // U-188 (BLENDER's 0.6.0 smoke read: at -2 m a flat grey-blue): sea_under paints the water; the tiles' own tint over it eases off with
            // the sea weight, so its surface band and light read from the first metre (in 0.01 steps: the chunks re-tint only on a change).
            Meridian.Terrain.TerrainChunk.LiquidAlpha = Mathf.Round(Mathf.Lerp(Meridian.Terrain.TerrainChunk.WaterAlpha, SeaWaterAlpha, under ? w : 0f) * 100f) / 100f;
            if (!under) return;
            if (!seaConfigured) { SeaUnder.ConfigureFor("earth", "sea_under", waterLine); SeaUnder.anchorY = waterLine; seaConfigured = true; }
            SeaUnder.alpha = w;
            // U-205 (B-225): the shallow seabed (the set's json: shore_m 40) shows by the shore only and fades out over its last 8 m.
            var layers = SeaUnder.Layout.layers;
            float reach = 0f;
            for (int i = 0; i < layers.Length; i++) reach = Mathf.Max(reach, layers[i].shore_m);
            if (reach <= 0f) { ShoreDistanceNow = 0f; return; }
            ShoreDistanceNow = ShoreDistance(c.x, Mathf.CeilToInt(reach), seaAt);
            for (int i = 0; i < layers.Length; i++)
                if (layers[i].shore_m > 0f) SeaUnder.SetLayerAlpha(layers[i].n, ShallowsWeight(ShoreDistanceNow, layers[i].shore_m));
        }
        /// <summary>The incoming set's alpha `t` seconds into a border crossfade (a smooth step over CrossfadeSeconds). Pure.</summary>
        public static float CrossfadeAlpha(float t, float seconds) { float k = seconds > 0f ? Mathf.Clamp01(t / seconds) : 1f; return k * k * (3f - 2f * k); }
        Meridian.Planets.PlanetId planetId;
        string planetName, incomingScene;
        float fadeT;
        int worldWidth, lastDawn = int.MinValue; // U-123: Mercury's clock
        TimeSystem clock;
        double seasonSeconds; long lastSeason = long.MinValue; // U-130: Uranus's season clock
        /// <summary>The game clock the stage reads (0 without a TimeSystem).</summary>
        public double GameTime => clock != null ? clock.GameSeconds : 0;
        /// <summary>U-130 (D-142, D-154): the Survey view on Uranus: on while the Rig's Survey module is the active module (Module keys / Q / E), off
        /// for any other; the deck's survey layer0 (the methane bands) crossfades in under the same light through the U-128 crossfade.</summary>
        public bool SurveyView => SurveyViewFor(rigInput != null ? rigInput.module : (Meridian.Rig.RigModule)0);
        /// <summary>D-154: the Survey view by the active module (no pulse, no ownership gate). Pure.</summary>
        public static bool SurveyViewFor(Meridian.Rig.RigModule active) => active == Meridian.Rig.RigModule.Survey;
        Meridian.Player.PlayerRigInput rigInput;
        /// <summary>U-146 (D-154's deferred half): a Survey scan pulses the survey bands for SurveyPulseBeats beats at SurveyPulseBpm: up over the
        /// first beat and down over the last through the U-128 smoothstep, held between. On Uranus the deck's survey layer0 is drawn over the
        /// view on the veil slot at SurveyPulsePeak × this; the Leviathan's bands (Neptune, D-148) read the same pulse (SurveyPulse).</summary>
        public const int SurveyPulseBeats = 4;
        public const float SurveyPulseBpm = 110f, SurveyPulsePeak = 0.55f;
        public static float SurveyPulseSeconds => SurveyPulseBeats * 60f / SurveyPulseBpm;
        /// <summary>The pulse's strength (0..1) this long after a scan. Pure.</summary>
        public static float SurveyPulseAlpha(float sinceScan)
        {
            float total = SurveyPulseSeconds, beat = 60f / SurveyPulseBpm;
            if (sinceScan < 0f || sinceScan >= total) return 0f;
            if (sinceScan < beat) return CrossfadeAlpha(sinceScan, beat);
            if (sinceScan > total - beat) return CrossfadeAlpha(total - sinceScan, beat);
            return 1f;
        }
        float lastSurveyScan = float.NegativeInfinity;
        Meridian.Player.PlayerRigInput surveyedFrom;
        /// <summary>U-146: the survey pulse now (0 when no scan is fresh): the Leviathan's bands light by it.</summary>
        public float SurveyPulse => SurveyPulseAlpha(Time.time - lastSurveyScan);
        void OnSurveyed(Vector2 centre)
        {
            lastSurveyScan = Time.time;
            if (!Active || planetId != Meridian.Planets.PlanetId.Uranus || Layers == null) return;
            // Uranus: the deck's survey layer0 alone on the veil slot (above the near layers), its alpha the pulse's.
            if (StormLayers == null) { var wgo = new GameObject("CartoonStormVeil"); wgo.transform.SetParent(transform, false); StormLayers = wgo.AddComponent<ParallaxLayers>(); StormLayers.orderOffset = StormVeilOrder; }
            StormLayers.gameObject.SetActive(true);
            StormLayers.view = Layers.view;
            StormLayers.alpha = 0f;
            StormLayers.scrollX = 0f;
            StormLayers.onlyLayer = 0; StormLayers.mirrorX = false;
            StormLayers.layer0Scene = null; StormLayers.upperScene = null;
            StormLayers.groundFill = null; StormLayers.fillFromSet = false; StormLayers.continueNearest = false; StormLayers.continueAnyBottom = false; // U-159: only Mars's veil continues
            StormLayers.ConfigureFor(planetName, DeckOf(Scene) + "_" + Meridian.Planet.UranusSeason.Survey, DatumFor(Scene, Layers.datumY));
        }
        void OnDestroy() { if (surveyedFrom != null) surveyedFrom.Surveyed -= OnSurveyed; }
        Meridian.Hazards.HazardSystem hazards;
        /// <summary>Rigged plants around the camp in C0 (every FloraSpacing m, jittered).</summary>
        public const int FloraCount = 42; // D-136 (2): was 48; the camp's density is the animated-object lever (the gate read 42 Animators against 40)
        public const float FloraSpacing = 2.5f;
        /// <summary>U-101 / B-113: gulls over the camp in C0.</summary>
        public const int GullCount = 1;
        /// <summary>U-204 F14: the camp's gull is Earth's alone (its species' planet). The stage asked for one on every planet, and off Earth it flew as its placeholder box.</summary>
        public static bool CampGullOn(Meridian.Planets.PlanetId planet) =>
            Meridian.Creatures.SpeciesSpec.Get(Meridian.Creatures.Species.Gull).planet == planet;

        public ParallaxLayers Layers { get; private set; }
        /// <summary>U-109: the sky above the painted layers (the gradient to space black and the starfield over the last third of the climb).</summary>
        public ClimbSky Sky { get; private set; }
        /// <summary>U-097: the planet's rigged flora (placeholder set until B-112).</summary>
        public Meridian.Flora.FloraRigs Flora { get; private set; }
        /// <summary>U-100: the cartoon ground placeholder over the block faces.</summary>
        public GroundStrip Ground { get; private set; }
        /// <summary>U-156: the smooth ground's mesh builder (a smooth planet only; null before the first).</summary>
        public SmoothGround Smooth { get; private set; }
        /// <summary>U-174: the Surface Line's view on a smooth planet.</summary>
        public SurfaceLineView SurfaceLine { get; private set; }
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
            planetId = config.id; planetName = config.id.ToString().ToLowerInvariant();
            worldWidth = config.worldWidth; clock = FindAnyObjectByType<TimeSystem>(); hazards = side.hazards; lastDawn = int.MinValue;
            seasonSeconds = Meridian.Planet.UranusSeason.SeasonSeconds(config.dayLengthRealMinutes); lastSeason = long.MinValue; // U-130
            rigInput = side.player != null ? side.player.GetComponent<Meridian.Player.PlayerRigInput>() : null;
            if (surveyedFrom != rigInput) { if (surveyedFrom != null) surveyedFrom.Surveyed -= OnSurveyed; surveyedFrom = rigInput; if (rigInput != null) rigInput.Surveyed += OnSurveyed; } // U-146
            lastSurveyScan = float.NegativeInfinity; // D-154: the Survey view follows the active module // U-123: Mercury's set and strips follow the terminator's clock
            float entryY = side.player != null ? side.player.transform.position.y : surfaceDatum;
            // U-153: a decked giant's sets hang off the floe under the camera; at load, the floe under the entry.
            cloud = Decked(config.id) && side.terrain != null ? side.terrain.BaseGenerator as Meridian.Terrain.CloudColumn.CloudWorldGenerator : null;
            floeDatum = float.NaN; floeDatumVel = 0f;
            StepFloeDatum(side.player != null ? side.player.transform.position.x : side.spawnX, entryY + 1f, 0f);
            Scene = config.id == Meridian.Planets.PlanetId.Venus ? VenusSceneFor(entryY, null) // U-125: the entry's height (the surface or the deck)
                : config.id == Meridian.Planets.PlanetId.Neptune ? NeptuneSceneFor(entryY, side.spawnX, worldWidth, GameTime, null) // U-133
                : config.id == Meridian.Planets.PlanetId.Uranus ? UranusSceneFor(entryY, side.spawnX, worldWidth, GameTime, seasonSeconds, null, SurveyView) // U-130: the entry's band, the season's light
                : Decked(config.id) ? JupiterSceneFor(entryY, null) // U-127: the entry's band
                : SceneNow(side.spawnX); // U-110 / U-118 / U-123: the spawn's band (Earth), region (Mars) or terminator zone (Mercury) picks the set
            Layers.SetOrderOffset(0);
            Layers.alpha = 1f;
            Layers.groundFill = Meridian.Planet.PlanetBackdrop.GroundColor(config.id); // U-139: ground, not black, under the set's bottom edge
            Layers.fillFromSet = Decked(config.id) || (side.terrain != null && side.terrain.SmoothGround); // U-153: on a decked giant the set's lowest layer goes on down instead; U-161: on the smooth ground too, never a flat block
            Layers.continueNearest = side.terrain != null && side.terrain.SmoothGround; // U-164 (D-169): the nearest layer's strip, not layer0's sky or sea
            Layers.layer0Scene = Layer0Of(Scene); // U-130: the survey layer0, else the set's own
            Layers.upperScene = UpperOf(Scene); // U-133: the spot shares the storm's layers 1–2
            Layers.mirrorX = MirrorOf(Scene); // U-144
            Layers.ConfigureFor(planetName, SetOf(Scene), DatumFor(Scene, surfaceDatum), FallbackFor(config.id));
            Layers.nearAlpha = 1f;
            ConfigureSea(side, config); // U-171
            // U-128: from here the datum and the set follow the camera's band (FollowBand); the spawn's band keeps this surface, so the camp frames do not move.
            // D-146: Mercury's bands take the generator's own surface (noise + the cold-trap bowls, no small craters): the plain by the spawn, each trap per column.
            // U-139: Mercury and Venus follow the walking surface — the band surface's noise averaged, the bowls exact, each POI's stamped ground across
            // its stamp and shoulders (TerrainStreamer.OriginalTop), the pad held at the spawn surface.
            bool follows = config.id == Meridian.Planets.PlanetId.Mercury || config.id == Meridian.Planets.PlanetId.Venus;
            var solid = follows && side.terrain != null ? side.terrain.BaseGenerator as Meridian.Terrain.SolidWorldGenerator : null;
            var streamer = side.terrain;
            bool stamped = (follows && solid != null) || (config.id == Meridian.Planets.PlanetId.Mars && streamer != null); // Mars: its bands, plus the POI stamps (LEAD 16:1x)
            Datum = new BandDatum(config.id, config.datumY, side.spawnX, surfaceDatum, config.worldWidth,
                solid != null ? x => solid.BandSurfaceHeight(x) + 1f : (System.Func<int, float>)null,
                stamped ? x => streamer.OriginalTop(x) + 1f : (System.Func<int, float>)null,
                stamped ? BandDatum.StampsOf(config.id) : null,
                streamer != null && streamer.SmoothGround ? streamer.CurveAt : (System.Func<int, float>)null); // U-161: the set on the walking curve
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
                StormLayers.onlyLayer = -1; StormLayers.mirrorX = false; // U-146: the pulse may have left the slot on one layer
                // U-159 (D-169): on the smooth ground the veil continues its own translucent bottom strip under its edge, never as ground.
                bool smoothMars = side.terrain != null && side.terrain.SmoothGround;
                StormLayers.groundFill = smoothMars ? new Color(0f, 0f, 0f, 0f) : (Color?)null;
                StormLayers.fillFromSet = smoothMars; StormLayers.continueNearest = smoothMars; StormLayers.continueAnyBottom = smoothMars;
                StormLayers.ConfigureFor("mars", StormScene, surfaceDatum);
                storm = side.dustStorm;
            }
            else if (HasZoneOverlay(config.id))
            {
                // U-127 / U-129: the zone overlay (Jupiter's Red Spot "spot", Saturn's "hexagon") over the deck set on the same veil slot, faded in by the zone.
                if (StormLayers == null) { var wgo = new GameObject("CartoonStormVeil"); wgo.transform.SetParent(transform, false); StormLayers = wgo.AddComponent<ParallaxLayers>(); StormLayers.orderOffset = StormVeilOrder; }
                StormLayers.gameObject.SetActive(true);
                StormLayers.view = cam;
                StormLayers.alpha = 0f;
                StormLayers.scrollX = 0f;
                StormLayers.onlyLayer = -1; StormLayers.mirrorX = false;
                StormLayers.groundFill = null; StormLayers.fillFromSet = false; StormLayers.continueNearest = false; StormLayers.continueAnyBottom = false; // U-159: only Mars's veil continues
                StormLayers.ConfigureFor(planetName, OverlayFor(config.id), DatumFor(Scene, surfaceDatum));
                storm = null;
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
            var floraTerrain = side.terrain;
            Flora.biomeRule = config.id == Meridian.Planets.PlanetId.Mercury ? (System.Func<int, string>)(x => Meridian.Flora.FloraRigs.MercuryBiomeFor(x, MercuryClock, worldWidth))
                : config.id == Meridian.Planets.PlanetId.Jupiter && floraTerrain != null ? (System.Func<int, string>)(x => Meridian.Flora.FloraRigs.JupiterBiomeFor(x, floraTerrain.TopSolidY(x) + 1f)) // U-127: the floe's band, or the Red Spot
                : config.id == Meridian.Planets.PlanetId.Saturn && floraTerrain != null ? (System.Func<int, string>)(x => Meridian.Flora.FloraRigs.SaturnBiomeFor(x, floraTerrain.TopSolidY(x) + 1f)) // U-129: the floe's band, or the Hexagon
                : config.id == Meridian.Planets.PlanetId.Neptune && floraTerrain != null ? (System.Func<int, string>)(x => Meridian.Flora.FloraRigs.NeptuneBiomeFor(floraTerrain.TopSolidY(x) + 1f,
                    Meridian.Planet.Weather.NeptuneStorms.InDarkSpot(x, worldWidth) || Meridian.Planet.Weather.NeptuneStorms.InStorm(x, GameTime, worldWidth))) // U-133: the band, or the storm zones when placed
                : config.id == Meridian.Planets.PlanetId.Uranus && floraTerrain != null ? (System.Func<int, string>)(x => Meridian.Flora.FloraRigs.UranusBiomeFor(floraTerrain.TopSolidY(x) + 1f, !Meridian.Planet.UranusSeason.InLitHalf(x, worldWidth, GameTime, seasonSeconds))) // U-130: the band, or the dark half when placed
                : null; // U-123: by the terminator's zone when placed (Venus: BiomeNameAt, vents / plains)
            // Bible §9.6: ≤ 40 animated objects in all. The reserve is what the gate counts besides the flora: the drawn surveyor, the ship's legs rig and its
            // puff sheet, one more for a prop or critter Animator in flight (D-136 (2): the 08:46 gate read 38 flora + 4 = 42).
            Flora.Reserved = 4 + GullCount;
            Flora.Load("flora/" + config.id.ToString().ToLowerInvariant() + "/rigset");
            Flora.Populate(FloraCount, FloraSpacing, side.spawnX + 0.5f, config.id.GetHashCode() * 31 + 7);
            if (Ground == null) { var ggo = new GameObject("CartoonGround"); ggo.transform.SetParent(transform, false); Ground = ggo.AddComponent<GroundStrip>(); }
            Ground.gameObject.SetActive(true);
            Ground.view = cam; Ground.terrain = side.terrain;
            Ground.mirrorRule = config.id == Meridian.Planets.PlanetId.Neptune ? (System.Func<int, bool>)(x => Meridian.Planet.Weather.NeptuneWind.Direction(x) < 0) : null; // U-144: the −x zone's floes mirrored
            Ground.cloud = cloud; // U-153: a decked giant's strips are laid per floe in view
            // U-156 (D-161 / D-162): a smooth planet's ground is its traced outline's mesh; the strips stay loaded (the placeholder band) but draw nothing.
            bool smoothGround = config.worldType == Meridian.Planets.WorldType.Solid && Meridian.Terrain.GroundField.Smooth(config.id) && side.terrain != null;
            Ground.suppressed = smoothGround;
            if (smoothGround) { if (Smooth == null) Smooth = gameObject.AddComponent<SmoothGround>(); Smooth.Configure(config.id, side.terrain, Ground); }
            else if (Smooth != null) Smooth.Deactivate();
            // U-174 (D-174): the Surface Line in the cutaway on a smooth planet (it draws only while the camera is below the surface).
            if (smoothGround) { if (SurfaceLine == null) SurfaceLine = gameObject.AddComponent<SurfaceLineView>(); SurfaceLine.enabled = true; SurfaceLine.Configure(config.id, side.terrain, side.sideCamera); }
            else if (SurfaceLine != null) SurfaceLine.enabled = false;
            Ground.topMaterialRule = config.id == Meridian.Planets.PlanetId.Neptune ? (System.Func<int, byte, float, int>)((x, tile, top) => GroundStrip.NeptuneStripFor(top)) : null; // U-153: the Deep's superionic floes by the floe's own top
            Ground.Load(config.id); // U-118: the planet's strips (Earth's four, Mars's regolith + basalt + frost, Mercury's regolith + slate)
            Ground.materialRule = config.id == Meridian.Planets.PlanetId.Mercury ? (System.Func<int, byte, int>)((x, tile) => GroundStrip.MercuryStripFor(x, MercuryClock, worldWidth)) // U-123: slate in the shadow
                : config.id == Meridian.Planets.PlanetId.Jupiter ? (System.Func<int, byte, int>)((x, tile) => GroundStrip.JupiterStripFor(x, tile))
                : config.id == Meridian.Planets.PlanetId.Saturn ? (System.Func<int, byte, int>)((x, tile) => GroundStrip.SaturnStripFor(tile)) // U-129: ring rock on the cores
                : config.id == Meridian.Planets.PlanetId.Neptune && floraTerrain != null ? (System.Func<int, byte, int>)((x, tile) => GroundStrip.NeptuneStripFor(floraTerrain.TopSolidY(x) + 1f)) // U-133: the Deep's superionic floes
                : config.id == Meridian.Planets.PlanetId.Uranus ? (System.Func<int, byte, int>)((x, tile) => GroundStrip.UranusStripFor(!Meridian.Planet.UranusSeason.InLitHalf(x, worldWidth, GameTime, seasonSeconds))) : null; // U-127: the Red Spot's brick floes; U-130: the dark half's slate
            Ground.SetDecks(GroundStrip.DecksFor(config.id), GroundStrip.VenusDeck); // U-125: the deck planks along Venus's floating station (none elsewhere)
            if (Meridian.Art.ModelView.CartoonMaterial != null) foreach (var mv in side.GetComponentsInChildren<Meridian.Art.ModelView>(true)) mv.Wear(Meridian.Art.ModelView.CartoonMaterial);
            // U-101: one gull (B-113) over the camp; the director keeps it (it flees and bumps like any critter).
            // U-204 F14 (B-228's "flat pale square" behind the Pilgrim on Mars, in 0.6.0's and 0.6.1's smoke too; named from 0.6.2's
            // player log): the gull was spawned on EVERY planet's stage. Off Earth its sheet is not loaded (the director keeps only the
            // planet's own species' art), so it flew as its 0.7 x 0.5 m placeholder box. Earth's camp alone has a gull.
            if (CampGullOn(config.id) && side.creatures != null && side.player != null && side.creatures.CountOf(Meridian.Creatures.Species.Gull) < GullCount)
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
                go.AddComponent<Meridian.Player.JetpackOverlay>().view = Surveyor; // U-183: the jetpack upgrades on the back
            }
        }

        void LateUpdate()
        {
            // U-141: the set's under-fill takes the strip's fill tile once it is in (no allocation: a reference compare per frame).
            if (Active && Ground != null)
            {
                var tile = Ground.FillTile;
                if (Layers != null && Layers.groundTile != tile) Layers.groundTile = tile;
                if (Incoming != null && Incoming.groundTile != tile) Incoming.groundTile = tile;
            }
            if (Active && Layers != null && Layers.view != null && Datum != null) FollowBand(Layers.view.transform.position.x);
            if (Active) FollowSea(); // U-171: after the band (a crossfade may swap the base set)
            if (Active && planetId == Meridian.Planets.PlanetId.Mercury && Ground != null && worldWidth > 0)
            {
                // U-123: the terminator creeps 1 m per 6 s; when its dawn column moves, the strips lay out again (slate ↔ regolith at the band's edges; ~35 columns, no allocation).
                int dawn = Mathf.FloorToInt(Meridian.Terrain.MercuryTerminator.Dawn(MercuryClock, worldWidth));
                if (dawn != lastDawn) { lastDawn = dawn; Ground.Invalidate(); }
            }
            if (Flora != null)
            {
                // U-133 (D-148): one wind input on the rig driver: Neptune's plants lean with the wind at the camera (0 elsewhere).
                float lean = 0f;
                if (Active && planetId == Meridian.Planets.PlanetId.Neptune && Layers != null && Layers.view != null)
                {
                    double now = Time.timeSinceLevelLoad;
                    lean = Meridian.Planet.Weather.NeptuneWind.Lean(Meridian.Planet.Weather.NeptuneWind.At(Mathf.FloorToInt(Layers.view.transform.position.x), now), Meridian.Planet.Weather.NeptuneWind.Gusting(now), now);
                }
                Flora.leanDegrees = Mathf.Round(lean * 4f) * 0.25f; // quarter-degree steps: the 300 roots are written only when the lean moves a step (the shiver flips at 12 Hz)
            }
            if (Active && planetId == Meridian.Planets.PlanetId.Uranus && StormLayers != null && StormLayers.gameObject.activeSelf)
            {
                // U-146: the scan pulse rides the veil slot; when it is over the slot lets its art go.
                if (Time.time - lastSurveyScan < SurveyPulseSeconds)
                    StormLayers.alpha = StormLayers.placeholders.Count > 0 && !StormLayers.placeholders[0] ? SurveyPulsePeak * SurveyPulse : 0f; // never a flat placeholder (before B-166's survey sets)
                else { StormLayers.Release(); StormLayers.gameObject.SetActive(false); }
            }
            if (Active && planetId == Meridian.Planets.PlanetId.Uranus && Ground != null && worldWidth > 0)
            {
                // U-130: when the season turns the lit half swaps; the floe strips lay out again (ice in the light, the dark half's slate).
                long k = Meridian.Planet.UranusSeason.SeasonIndex(GameTime, seasonSeconds);
                if (k != lastSeason) { lastSeason = k; Ground.Invalidate(); }
            }
            if (Active && HasZoneOverlay(planetId) && StormLayers != null && StormLayers.gameObject.activeSelf && Layers != null && Layers.view != null)
            {
                StormLayers.alpha = OverlayAlpha(planetId, Mathf.FloorToInt(Layers.view.transform.position.x)); // U-127 / U-129: the zone overlay inside its zone
                return;
            }
            if (StormLayers == null || storm == null || !StormLayers.gameObject.activeSelf) return;
            StormLayers.alpha = StormAlpha(storm.Intensity);
            if (storm.Intensity > 0f) StormLayers.scrollX += storm.Intensity * StormWind * Time.deltaTime; // the wind carries the wall
        }

        /// <summary>U-128: the datum of the camera's band (blended at the borders) drives every layer slot and the sky's anchor; at a border the band's set fades in over the base set, then takes its place.</summary>
        void FollowBand(float cameraX)
        {
            int x = Mathf.FloorToInt(cameraX);
            if (cloud != null) StepFloeDatum(cameraX, Layers.view.transform.position.y, Time.deltaTime); // U-153
            float d = Datum.FollowsCurve ? Mathf.Lerp(Datum.At(x), Datum.At(x + 1), cameraX - x) : Datum.At(x); // U-161: no step per column on a slope
            float baseD = DatumFor(Scene, d); // U-125: Venus's deck set hangs off the cloud deck
            SetDatum(Layers, baseD);
            if (Incoming != null && Incoming.gameObject.activeSelf) SetDatum(Incoming, DatumFor(incomingScene, d));
            if (StormLayers != null && StormLayers.gameObject.activeSelf) SetDatum(StormLayers, baseD); // the veil hangs where the base set does (Mars: the same; Jupiter: the band's floor)
            if (Sky != null) Sky.anchorY = ParallaxMath.AnchorY(baseD);
            string want = SceneNow(x);
            if (!Fading && want != Scene)
            {
                if (Incoming == null) { var igo = new GameObject("CartoonParallaxIncoming"); igo.transform.SetParent(transform, false); Incoming = igo.AddComponent<ParallaxLayers>(); }
                Incoming.gameObject.SetActive(true);
                Incoming.view = Layers.view;
                Incoming.orderOffset = IncomingOrder;
                Incoming.alpha = 0f;
                Incoming.groundFill = Layers.groundFill; // U-139
                Incoming.fillFromSet = Layers.fillFromSet; // U-153
                Incoming.continueNearest = Layers.continueNearest; // U-164
                Incoming.layer0Scene = Layer0Of(want);
                Incoming.upperScene = UpperOf(want);
                Incoming.mirrorX = MirrorOf(want);
                Incoming.ConfigureFor(planetName, SetOf(want), DatumFor(want, d), FallbackFor(planetId));
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
