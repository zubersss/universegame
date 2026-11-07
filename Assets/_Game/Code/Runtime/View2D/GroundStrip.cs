using System.Collections.Generic;
using Meridian.Art;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.View2D
{
    /// <summary>
    /// U-100: the cartoon ground placeholder. While the v4 path is on, every visible terrain column gets a 1 m slice of the
    /// `terrain/earth/ground_strip` sheet (8 frames of 64×128 px: ink top line, one-tone grass lip, flat dirt) hung from
    /// its top solid tile, a flat dirt fill (a tile cut from the same sheet) down to the frame bottom, and an ink edge
    /// where neighbouring columns differ in height (dug walls). Drawn just in front of the 3D block faces, which keep
    /// collision and digging; columns follow digs through TerrainStreamer.TileChanged. Pooled renderers, no allocation per frame.
    /// </summary>
    public sealed class GroundStrip : MonoBehaviour
    {
        public const string Key = "terrain/earth/ground_strip";
        /// <summary>U-111 (B-130): the strips by material: grass over soil, bare soil where dug, stone where the block is stone, sand on the coast.</summary>
        public static readonly string[] Keys = { Key, Key + "_soil", Key + "_stone", Key + "_sand" };
        public const int Grass = 0, Soil = 1, Stone = 2, Sand = 3;
        /// <summary>U-118 (B-140): Mars draws the regolith strip, basalt where the block is basalt, and (D-143) the frost strip over snow and ice once BLENDER adds it — until then a missing sheet falls back to the regolith strip; hematite reads regolith.</summary>
        public static readonly string[] MarsKeys = { "terrain/mars/ground_strip", "terrain/mars/ground_strip_basalt", "terrain/mars/ground_strip_frost" };
        public const int Regolith = 0, Basalt = 1, Frost = 2;
        /// <summary>U-123 (B-148): Mercury draws the blinding regolith strip, and the slate kind where the column is in shadow — the night side and a cold trap's permanent
        /// shadow. The shadow moves with the terminator, so the rule needs its clock: CartoonStage sets materialRule; the pure MaterialFor reads regolith.</summary>
        public static readonly string[] MercuryKeys = { "terrain/mercury/ground_strip", "terrain/mercury/ground_strip_slate" };
        public const int MercuryRegolith = 0, Slate = 1;
        /// <summary>U-123: a per-column rule (column, top tile → material index) that overrides MaterialFor while set; Invalidate lays the columns out again.</summary>
        public System.Func<int, byte, int> materialRule;
        /// <summary>The Mercury strip at column x for the terminator's clock: slate in the night zone and on a cold trap's floor (permanent shadow), regolith in the sun. Pure.</summary>
        public static int MercuryStripFor(int x, double realSeconds, int width)
        {
            if (width <= 0) return MercuryRegolith;
            if (Meridian.Terrain.MercuryLandforms.PermanentShadow(x, width)) return Slate;
            return Meridian.Terrain.MercuryTerminator.ZoneAt(x, realSeconds, width) == Meridian.Terrain.MercuryZone.Night ? Slate : MercuryRegolith;
        }
        /// <summary>Lays the columns out again on the next LateUpdate (the terminator crept, a rule changed).</summary>
        public void Invalidate() => dirty = true;
        /// <summary>The planet's strip keys (Earth's four, Mars's two; other planets Earth's until their strips exist). Pure.</summary>
        public static string[] KeysFor(Meridian.Planets.PlanetId planet) => planet == Meridian.Planets.PlanetId.Mars ? MarsKeys : planet == Meridian.Planets.PlanetId.Mercury ? MercuryKeys
            : planet == Meridian.Planets.PlanetId.Venus ? VenusKeys : Keys;
        /// <summary>U-126 (D-137): a giant's floe strip is 8 tiles + cap_left (frame 8) + cap_right (frame 9) on the B-130 contract; Earth's,
        /// Mars's, Mercury's and Venus's are 8 frames and never cap. A column ends a floe where the ground beside it falls away by more than
        /// FloeEdgeDrop (the gap to the next floe); the caps hang in the air columns just outside, so a floe reads cap + n tiles + cap at any n ≥ 1.</summary>
        public const int TileFrames = 8, CapLeft = 8, CapRight = 9;
        public const float FloeEdgeDrop = 3f;
        public static bool HasCaps(int frames) => frames > CapRight;
        public static int TileFrame(int x) => ((x % TileFrames) + TileFrames) % TileFrames;
        public static bool FloeEnd(float top, float besideTop) => besideTop < top - FloeEdgeDrop;
        /// <summary>U-126: a floe of `length` tiles from column x0 as (column, frame) pairs: cap_left just outside, the tiles, cap_right just outside. Pure.</summary>
        public static void FloeFrames(int x0, int length, List<Vector2Int> into)
        {
            into.Clear();
            if (length < 1) return;
            into.Add(new Vector2Int(x0 - 1, CapLeft));
            for (int i = 0; i < length; i++) into.Add(new Vector2Int(x0 + i, TileFrame(x0 + i)));
            into.Add(new Vector2Int(x0 + length, CapRight));
        }
        /// <summary>U-126: how many floe caps drew on the last pass (tests and captures).</summary>
        public int CapsShown { get; private set; }
        readonly List<SpriteRenderer> caps = new List<SpriteRenderer>(8);

        /// <summary>U-125 (B-153): Venus's two kinds: the basalt crust on every ground column (vents, tesserae and sulphur patches read as crust on the
        /// drawn strip) and the deck planks, laid along the floating station's deck (SetDecks), never on a terrain column.</summary>
        public static readonly string[] VenusKeys = { "terrain/venus/ground_strip", "terrain/venus/ground_strip_deck" };
        public const int VenusCrust = 0, VenusDeck = 1;
        /// <summary>U-125: the planet's floating decks as (x0, x1, deck top y): Venus's stations from PoiCatalog (the aerostat decks' top at floatY + DeckTop). Pure.</summary>
        public static List<Vector3> DecksFor(Meridian.Planets.PlanetId planet)
        {
            var runs = new List<Vector3>(2);
            if (planet != Meridian.Planets.PlanetId.Venus) return runs;
            foreach (var poi in Meridian.Planet.POI.PoiCatalog.For(planet))
                if (poi.Floating) runs.Add(new Vector3(poi.x, poi.x + poi.floatWidth, poi.floatY + Meridian.Planet.POI.PoiCatalog.DeckTop));
            return runs;
        }
        /// <summary>The strip a column draws on `planet` from its top solid tile. Pure.</summary>
        public static int MaterialFor(Meridian.Planets.PlanetId planet, byte topTile) => planet == Meridian.Planets.PlanetId.Mars
            ? (topTile == TileId.Basalt ? Basalt : (topTile == TileId.Snow || topTile == TileId.Ice) ? Frost : Regolith)
            : planet == Meridian.Planets.PlanetId.Mercury ? MercuryRegolith // U-123: the shadow (slate) is the clock's rule, materialRule
            : planet == Meridian.Planets.PlanetId.Venus ? VenusCrust // U-125: the deck planks are the station's, never a column's
            : MaterialFor(topTile);

        /// <summary>The strip a column draws from its top solid tile: grass, sand and stone their own, every other tile (soil, snow, a dug face) the soil. Pure.</summary>
        public static int MaterialFor(byte topTile) => topTile == TileId.Grass ? Grass : topTile == TileId.Sand ? Sand : topTile == TileId.Stone ? Stone : Soil;
        /// <summary>The strips sit in front of the block mesh front faces (BlockMesher.FrontZ −0.5): the depth test hid their bodies behind the faces (U-118 crops: only the lip above the line showed, the block grain stood in for the painted band).</summary>
        public const float Z = Meridian.Terrain.BlockMesher.FrontZ - 0.1f, StripHeight = 2f, FillDepth = 20f, EdgeWidth = 0.09f;
        public const int Order = 1;
        static readonly Color Ink = new Color(0.33f, 0.39f, 0.5f); // × the dirt tone ≈ #1E1A17
        static readonly Color Back = new Color(0.62f, 0.62f, 0.66f); // a dug hole's back wall: the dirt tone, shaded

        public TerrainStreamer terrain;
        public Camera view;

        /// <summary>Ready once the grass strip is in; the other materials fall back to it until theirs arrive.</summary>
        public bool Ready => frames != null;
        public int Columns => count;
        /// <summary>U-111: how many of the four material sheets are in (tests and captures).</summary>
        public int MaterialsLoaded { get { int n = 0; for (int i = 0; i < framesBy.Length; i++) if (framesBy[i] != null) n++; return n; } }
        /// <summary>The material index drawn at column x on the last pass (−1: not in view). Tests read it.</summary>
        public int MaterialAt(int x) { int i = x - firstColumn; return i >= 0 && i < count && i < materialAt.Count ? materialAt[i] : -1; }

        Sprite[] frames; // the grass strip: the fallback
        Sprite dirt;
        Sprite[][] framesBy = new Sprite[4][];
        Sprite[] fillBy = new Sprite[4];
        string[] keys = Keys;
        Meridian.Planets.PlanetId planet = Meridian.Planets.PlanetId.Earth;
        readonly List<int> materialAt = new List<int>(64);
        AsyncOperationHandle<IList<Sprite>> handle;
        AsyncOperationHandle<IList<Sprite>>[] handles = new AsyncOperationHandle<IList<Sprite>>[4];
        readonly List<SpriteRenderer> tops = new List<SpriteRenderer>(64), fills = new List<SpriteRenderer>(64), edges = new List<SpriteRenderer>(64), backs = new List<SpriteRenderer>(64);
        int firstColumn = int.MinValue, lastColumn = int.MinValue, count;
        bool dirty = true;
        // U-125: the floating decks (x0, x1, deck top y) and the strip kind laid along them.
        readonly List<Vector3> deckRuns = new List<Vector3>(2);
        readonly List<SpriteRenderer> deckTops = new List<SpriteRenderer>(32);
        int deckMaterial = -1;
        /// <summary>U-125: how many deck-plank frames drew on the last pass (tests and captures).</summary>
        public int DeckFramesShown { get; private set; }

        /// <summary>U-125: the runs (x0, x1, deck top y) to lay the `material` kind along, one frame per metre; empty clears them.</summary>
        public void SetDecks(List<Vector3> runs, int material)
        {
            deckRuns.Clear();
            if (runs != null) deckRuns.AddRange(runs);
            deckMaterial = deckRuns.Count > 0 ? material : -1;
            dirty = true;
        }

        void OnEnable() { if (terrain != null) terrain.TileChanged += OnTile; }
        void OnDisable() { if (terrain != null) terrain.TileChanged -= OnTile; }

        public void Load() => Load(Meridian.Planets.PlanetId.Earth);

        /// <summary>Loads the planet's strips (U-118: KeysFor); a second Load re-configures for another planet.</summary>
        public void Load(Meridian.Planets.PlanetId planet)
        {
            if (terrain != null) { terrain.TileChanged -= OnTile; terrain.TileChanged += OnTile; }
            if (handle.IsValid()) ArtLoad.Release(handle); // U-121: a second Load (re-configure) must not orphan the first handle (ResidencyTests' lone planet_earth holder)
            for (int m = 0; m < handles.Length; m++) if (handles[m].IsValid()) ArtLoad.Release(handles[m]);
            this.planet = planet;
            keys = KeysFor(planet);
            framesBy = new Sprite[keys.Length][]; fillBy = new Sprite[keys.Length]; handles = new AsyncOperationHandle<IList<Sprite>>[keys.Length];
            frames = null; dirt = null; dirty = true;
            var loadKeys = keys;
            for (int m = 0; m < keys.Length; m++)
            {
                int material = m;
                string key = keys[m];
                // D-143: a strip kind not exported yet (the Mars frost strip) is probed, never loaded blind — a missing key logs an Addressables exception; the first key's strip stands in.
                var probe = Addressables.LoadResourceLocationsAsync(key);
                probe.Completed += loc =>
                {
                    bool exists = loc.Status == AsyncOperationStatus.Succeeded && loc.Result != null && loc.Result.Count > 0;
                    ArtLoad.Release(loc);
                    if (!exists || this == null || !ReferenceEquals(loadKeys, keys)) return; // gone, or re-configured for another planet meanwhile
                    var h = ArtLoad.Asset<IList<Sprite>>(key);
                    handles[material] = h;
                    if (material == 0) handle = h;
                h.Completed += op =>
                {
                    if (this == null || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                    var fr = new Sprite[op.Result.Count];
                    op.Result.CopyTo(fr, 0);
                    // A flat fill tile: the bottom 8 px of the sheet's first slice (1 m wide), tiled for the fills and the edges. D-146: one texel
                    // in from each side (62 px at a PPU that keeps it 1 m): the sheet's gutters are transparent, and with bilinear filtering the
                    // full-width tile's edge sampled them — a dark sliver at every column join that fell between pixels (the Mercury night seams).
                    var r = fr[0].rect;
                    var fill = Sprite.Create(fr[0].texture, FillRect(r), new Vector2(0.5f, 1f), FillPpu(r, fr[0].pixelsPerUnit), 0, SpriteMeshType.FullRect);
                    framesBy[material] = fr; fillBy[material] = fill;
                    if (material == 0) { frames = fr; dirt = fill; }
                    dirty = true;
                };
                };
            }
        }

        void OnTile(int x, int y, byte old, byte now) { if (x >= firstColumn - 1 && x <= lastColumn + 1) dirty = true; }

        void LateUpdate()
        {
            if (view == null || terrain == null || frames == null) return;
            float half = view.orthographicSize * view.aspect + 2f;
            int first = Mathf.FloorToInt(view.transform.position.x - half), last = Mathf.CeilToInt(view.transform.position.x + half);
            if (!dirty && first == firstColumn && last == lastColumn) return;
            firstColumn = first; lastColumn = last; dirty = false;
            count = last - first + 1;
            while (tops.Count < count) { tops.Add(Make("Strip", Order, null)); fills.Add(Make("Fill", Order - 1, dirt)); edges.Add(Make("Edge", Order + 1, dirt)); backs.Add(Make("Back", Order - 2, dirt)); }
            while (materialAt.Count < tops.Count) materialAt.Add(-1);
            float prevTop = terrain.TopSolidY(first - 1) + 1f;
            int capCount = 0;
            for (int i = 0; i < tops.Count; i++)
            {
                bool on = i < count;
                tops[i].enabled = on; fills[i].enabled = on;
                if (!on) { edges[i].enabled = false; backs[i].enabled = false; continue; }
                int x = first + i;
                int topY = terrain.TopSolidY(x);
                float top = topY + 1f; // the ground line
                // U-111: the column's material from its top solid tile; a sheet not in yet falls back to the grass strip.
                byte tile = terrain.GetTile(x, topY);
                int material = materialRule != null ? materialRule(x, tile) : MaterialFor(planet, tile);
                if (material < 0 || material >= framesBy.Length) material = 0;
                var set = framesBy[material] ?? frames;
                var fillTile = fillBy[material] ?? dirt;
                materialAt[i] = framesBy[material] != null ? material : 0;
                var t = tops[i];
                t.sprite = set[HasCaps(set.Length) ? TileFrame(x) : ((x % set.Length) + set.Length) % set.Length]; // U-126: a capped sheet tiles its first 8 frames only
                t.transform.position = new Vector3(x + 0.5f, top, Z);
                var f = fills[i];
                if (f.sprite != fillTile) f.sprite = fillTile;
                f.transform.position = new Vector3(x + 0.5f, top - StripHeight, Z);
                f.size = new Vector2(1f, FillDepth);
                // A step between this column and the one before: an ink edge down the wall.
                float step = Mathf.Abs(top - prevTop);
                var e = edges[i];
                e.enabled = step > 0.01f;
                if (e.enabled) { e.transform.position = new Vector3(x, Mathf.Max(top, prevTop), Z - 0.001f); e.size = new Vector2(EdgeWidth, step); }
                // A dug column (lower than both neighbours' lowest): a shaded back wall up to that line, so no block face shows in the hole.
                float rim = Mathf.Min(prevTop, terrain.TopSolidY(x + 1) + 1f);
                var bk = backs[i];
                bk.enabled = rim > top + 0.01f;
                if (bk.enabled) { bk.transform.position = new Vector3(x + 0.5f, rim, Z + 0.001f); bk.size = new Vector2(1f, rim - top); }
                // U-126: a floe's ends take its caps in the air columns just outside (a capped sheet only).
                if (HasCaps(set.Length))
                {
                    float nextTop = terrain.TopSolidY(x + 1) + 1f;
                    if (FloeEnd(top, prevTop)) PlaceCap(ref capCount, set[CapLeft], x - 1, top);
                    if (FloeEnd(top, nextTop)) PlaceCap(ref capCount, set[CapRight], x + 1, top);
                }
                prevTop = top;
            }
            for (int i = capCount; i < caps.Count; i++) caps[i].enabled = false;
            CapsShown = capCount;
            LayDecks(first, last);
        }

        void PlaceCap(ref int n, Sprite frame, int column, float top)
        {
            if (n == caps.Count) caps.Add(Make("Cap", Order, null));
            var c = caps[n++];
            c.enabled = true;
            c.sprite = frame;
            c.transform.position = new Vector3(column + 0.5f, top, Z);
        }

        /// <summary>U-125: the deck kind along each floating deck in view (no fill: the hull below is the station's props); hidden until its sheet is in.</summary>
        void LayDecks(int first, int last)
        {
            int n = 0;
            var set = deckMaterial >= 0 && deckMaterial < framesBy.Length ? framesBy[deckMaterial] : null;
            if (set != null)
                for (int r = 0; r < deckRuns.Count; r++)
                {
                    var run = deckRuns[r];
                    int x0 = Mathf.Max(first, Mathf.FloorToInt(run.x)), x1 = Mathf.Min(last, Mathf.CeilToInt(run.y) - 1);
                    for (int x = x0; x <= x1; x++)
                    {
                        if (n == deckTops.Count) deckTops.Add(Make("Deck", Order, null));
                        var t = deckTops[n++];
                        t.enabled = true;
                        t.sprite = set[((x % set.Length) + set.Length) % set.Length];
                        t.transform.position = new Vector3(x + 0.5f, run.z, Z);
                    }
                }
            for (int i = n; i < deckTops.Count; i++) deckTops[i].enabled = false;
            DeckFramesShown = n;
        }

        /// <summary>D-146: the fill tile inside a strip's frame 0 — rows 1–6 of its bottom 8, one texel in from every side, so bilinear filtering
        /// only ever blends the band's own uniform texels: not the transparent gutter at the sides, and not (Repeat wraps v) the sheet's
        /// transparent top row under the bottom edge — the 13:47 frames showed that as horizontal lines once the tile stopped landing on whole pixels. Pure.</summary>
        public static Rect FillRect(Rect frame) => new Rect(frame.x + 1f, frame.y + 1f, frame.width - 2f, 6f);
        /// <summary>D-146: the fill tile's pixels per unit, so its inset width still spans one column (1 m). Pure.</summary>
        public static float FillPpu(Rect frame, float ppu) => ppu * (frame.width - 2f) / frame.width;

        SpriteRenderer Make(string name, int order, Sprite tile)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = order;
            if (tile != null) { sr.sprite = tile; sr.drawMode = SpriteDrawMode.Tiled; sr.tileMode = SpriteTileMode.Continuous; }
            if (name == "Edge") sr.color = Ink;
            else if (name == "Back") sr.color = Back;
            return sr;
        }

        void OnDestroy()
        {
            if (terrain != null) terrain.TileChanged -= OnTile;
            for (int m = 0; m < handles.Length; m++) if (handles[m].IsValid()) ArtLoad.Release(handles[m]); // U-111: the four strips (the grass handle is handles[Grass])
        }
    }
}
