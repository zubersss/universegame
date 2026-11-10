using System.Collections.Generic;
using Meridian.Core;
using UnityEngine;

namespace Meridian.View2D.Living
{
    /// <summary>
    /// U-216 (D-205 / D-206, STYLE_V7 §3 "Alive"): THE LIVING STAGE, behind a flag, at Earth's camp, on stand-in pieces
    /// (LivingPlaceholders) until BLENDER's painted ones land (U-217). Four things, each of which can be switched off alone
    /// so the built player's probe can price it:
    /// (1) WIND: the scenery in layers (near, play, play_front, foreground), each ONE mesh with one material; the wind field
    ///     (LivingWind) bends every rooted piece in the vertex shader and the surveyor passing parts them;
    /// (2) AIR: motes and drifting leaves carried by the gusts, shafts of light that breathe, a cloud's shadow sliding by;
    /// (3) one PHYSICS piece: a vine hanging from a snag as a chain (VineChain), swung by the wind and brushed by the body;
    /// (4) LIGHT: one piece (a rock) taking the 2D renderer's lights through a normal map, under a small warm lamp.
    /// The stage only draws: it never stops, slows or lifts the surveyor (D-206). A rooted piece whose ground is dug away
    /// goes with a puff. With the flag off this object does not exist and the shader's wind is still: no change to play.
    /// </summary>
    public sealed class LivingStage : MonoBehaviour
    {
        /// <summary>The switch a built player takes.</summary>
        public const string Switch = "-meridianLivingStage";

        static bool on;
        /// <summary>The flag (off unless the player was started with the switch; tests and captures set it and put it back).</summary>
        public static bool Enabled
        {
            get => on;
            set
            {
                on = value;
                if (value) Ensure();
                else if (Instance != null) Instance.Clear();
            }
        }
        /// <summary>The four parts, each on by default; the probe prices one by switching it off.</summary>
        public static bool WindOn = true, AirOn = true, VineOn = true, LightOn = true;
        /// <summary>The scatter's and the wind's seed.</summary>
        public static int Seed = 216;

        public static LivingStage Instance { get; private set; }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.SubsystemRegistration)]
        static void Boot()
        {
            Instance = null;
            on = System.Array.IndexOf(System.Environment.GetCommandLineArgs(), Switch) >= 0;
            WindOn = AirOn = VineOn = LightOn = true;
        }

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void BootAfterScene() { if (on) Ensure(); else LivingWind.PushStill(); }

        static void Ensure()
        {
            if (Instance != null || !Application.isPlaying) return;
            var go = new GameObject("LivingStage");
            DontDestroyOnLoad(go);
            Instance = go.AddComponent<LivingStage>();
        }

        // ---------- the layers ----------

        public enum Layer { Near, Play, PlayFront, Foreground }
        public const int Layers = 4;
        /// <summary>The share of the camera's travel a layer follows (contract §12.10; the stage file's table when pieces land).</summary>
        public static readonly float[] Parallax = { 0.08f, 0f, 0f, -0.35f };
        /// <summary>Sorting orders: near and play stand BEHIND the ground's lip (the smooth ground draws at 1), play_front over the
        /// surveyor and the animals, the foreground over the world; the air between the two.</summary>
        public static readonly int[] Orders = { -1, 0, SpriteCharacterView.SurveyorOrder + 1, 60 };
        public const int ShaftOrder = 44, MoteOrder = 45;
        /// <summary>The stage reaches this far west and east of the camp's spawn point (m).</summary>
        public const float West = 30f, East = 40f;

        sealed class LayerMesh
        {
            public GameObject go; public Mesh mesh; public MeshRenderer renderer;
            public readonly List<LivingInstance> instances = new List<LivingInstance>(96);
        }

        readonly LayerMesh[] layers = new LayerMesh[Layers];
        LivingPiece[] pieces;
        Texture2D colour, normal;
        Material unlit, lit;
        readonly List<Vector3> vertices = new List<Vector3>(8192);
        readonly List<Vector2> uv0 = new List<Vector2>(8192);
        readonly List<Vector4> uv1 = new List<Vector4>(8192), uv2 = new List<Vector4>(8192);
        readonly List<Color32> colors = new List<Color32>(8192);
        readonly List<int> triangles = new List<int>(32768);

        public bool Built { get; private set; }
        PlanetSideRoot builtFor;
        SceneDirector director;
        float anchorX;
        public LivingWind Wind { get; private set; }
        /// <summary>Tests and the report: what stands, what was dug away, the vertices of each layer, the draw calls the stage adds.</summary>
        public int InstanceCount(Layer l) => layers[(int)l] != null ? layers[(int)l].instances.Count : 0;
        public int VertexCount(Layer l) => layers[(int)l] != null && layers[(int)l].mesh != null ? layers[(int)l].mesh.vertexCount : 0;
        public int Removed { get; private set; }
        public int DrawCalls => !Built ? 0 : Layers + (AirOn ? 2 : 0) + (VineOn && Chain != null ? 1 : 0) + (LightOn && rockGo != null ? 1 : 0);
        public Mesh MeshOf(Layer l) => layers[(int)l] != null ? layers[(int)l].mesh : null;
        public Transform LayerRoot(Layer l) => layers[(int)l] != null ? layers[(int)l].go.transform : null;

        void LateUpdate()
        {
            if (director == null) director = FindAnyObjectByType<SceneDirector>();
            var side = director != null ? director.PlanetSide : null;
            bool want = on && CartoonStage.Enabled && side != null && side.gameObject.activeInHierarchy && side.Config != null
                && side.Config.id == Meridian.Planets.PlanetId.Earth && side.terrain != null && side.terrain.SmoothGround && side.player != null && side.sideCamera != null;
            if (!want) { if (Built) Clear(); return; }
            if (Built && builtFor != side) Clear();
            if (!Built)
            {
                if (!side.terrain.IsSettled) return; // the ground under the camp first
                Build(side);
            }
            Step(side, Time.deltaTime);
        }

        void OnDestroy() { Clear(); if (Instance == this) Instance = null; }

        // ---------- building ----------

        static float Roll(int i, int salt) => Meridian.Mining.DigRun.Hash01(Seed, i, salt);

        void Build(PlanetSideRoot side)
        {
            builtFor = side;
            var t = side.terrain;
            anchorX = side.spawnX + 0.5f;
            shipStands = side.ship != null && side.ship.Body != null;
            shipX = shipStands ? side.ship.Body.position.x : 0f;
            Wind = new LivingWind(Seed);
            LivingPlaceholders.Paint(Seed, out colour, out normal);
            var unlitSource = Resources.Load<Material>("LivingStage");
            var litSource = Resources.Load<Material>("LivingStageLit");
            if (unlitSource == null || litSource == null)
            {
                Debug.LogWarning("[MERIDIAN] LivingStage: its materials are not under Resources (LivingStage, LivingStageLit).");
                on = false;
                Clear();
                return;
            }
            unlit = new Material(unlitSource) { name = "LivingStage (stage)", mainTexture = colour };
            unlit.SetShaderPassEnabled("NormalsRendering", false); // unlit pieces write no normals
            lit = new Material(litSource) { name = "LivingStage (lit piece)", mainTexture = colour };
            lit.SetTexture("_NormalMap", normal);
            pieces = new LivingPiece[LivingPlaceholders.Kinds];
            for (int k = 0; k < pieces.Length; k++) pieces[k] = LivingPlaceholders.Piece((LivingPlaceholders.Kind)k);

            for (int l = 0; l < Layers; l++)
            {
                var lm = new LayerMesh { go = new GameObject("Living_" + (Layer)l) };
                lm.go.transform.SetParent(transform, false);
                lm.mesh = new Mesh { name = "Living_" + (Layer)l };
                lm.mesh.MarkDynamic();
                lm.go.AddComponent<MeshFilter>().sharedMesh = lm.mesh;
                lm.renderer = lm.go.AddComponent<MeshRenderer>();
                lm.renderer.sharedMaterial = unlit;
                lm.renderer.sortingOrder = Orders[l];
                lm.renderer.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                lm.renderer.receiveShadows = false;
                layers[l] = lm;
            }

            // the scatter: by the seed alone, so two runs stand the same stage
            Scatter(t, Layer.Play, 1.0f, 0.35f, 1f, new Color32(255, 255, 255, 255), new[] { LivingPlaceholders.Kind.Fern, LivingPlaceholders.Kind.Grass, LivingPlaceholders.Kind.Shrub, LivingPlaceholders.Kind.Grass, LivingPlaceholders.Kind.Reed, LivingPlaceholders.Kind.Fern, LivingPlaceholders.Kind.Grass }, 0f, 101);
            Scatter(t, Layer.Near, 1.6f, 0.5f, 1.15f, new Color32(198, 214, 204, 255), new[] { LivingPlaceholders.Kind.Shrub, LivingPlaceholders.Kind.Fern, LivingPlaceholders.Kind.Reed }, 0.1f, 202);
            Scatter(t, Layer.PlayFront, 1.5f, 0.5f, PlayFrontScale, new Color32(255, 255, 255, 255), new[] { LivingPlaceholders.Kind.Tuft }, -0.04f, 303); // D-206: at most 0.30 m tall
            // the foreground: large dark leaves rooted under the frame's lower edge, only their upper third over the ground line
            Scatter(t, Layer.Foreground, 11f, 3f, 1.6f, new Color32(150, 170, 160, 255), new[] { LivingPlaceholders.Kind.BigLeaf }, 3.2f, 404);

            // the snag the vine hangs from (a standing piece on the play layer), east of the camp
            float sx = FreeColumn(t, anchorX + 9f);
            var snag = pieces[(int)LivingPlaceholders.Kind.Snag];
            var snagRoot = new Vector2(sx, t.SurfaceAt(sx) - 0.05f);
            layers[(int)Layer.Play].instances.Insert(0, new LivingInstance { piece = (int)LivingPlaceholders.Kind.Snag, at = snagRoot, scale = 1f, phase = 0f, tint = new Color32(255, 255, 255, 255) });
            for (int l = 0; l < Layers; l++) Upload(layers[l]);

            // (3) the vine: a chain from the snag's branch tip
            var vinePiece = pieces[(int)LivingPlaceholders.Kind.Vine];
            var hold = snagRoot + Vector2.Scale(LivingPlaceholders.SnagHold - snag.pivot, snag.sizeM);
            int links = Mathf.Max(4, Mathf.RoundToInt(vinePiece.sizeM.y / VineLinkM));
            Chain = new VineChain(hold, links, vinePiece.sizeM.y / links);
            BuildVine(vinePiece);

            // (4) the lit piece: a rock under a small warm lamp
            float rx = FreeColumn(t, anchorX + 5f);
            BuildLitRock(new Vector2(rx, t.SurfaceAt(rx)));

            // (2) the air
            BuildAir(side);

            if (side.rig != null) { side.rig.Dug += OnDug; hookedRig = side.rig; }
            fx = FindAnyObjectByType<Meridian.FX.FxPool>();
            sideFx = FindAnyObjectByType<Meridian.FX.SideFx>();
            Built = true;
        }

        /// <summary>A column near x with ground under it and clear of the ship (searched eastward).</summary>
        float FreeColumn(Meridian.Terrain.TerrainStreamer t, float x)
        {
            for (int k = 0; k < 24; k++)
            {
                float at = x + k;
                if (Rooted(t, new Vector2(at, t.SurfaceAt(at)))) return at;
            }
            return x;
        }

        /// <summary>Ground stands under a root there, and the Pilgrim does not (the camp's own flat ground counts: the stage stands ON the
        /// camp; only the ship's footing is kept clear).</summary>
        bool Rooted(Meridian.Terrain.TerrainStreamer t, Vector2 root) =>
            (!shipStands || Mathf.Abs(root.x - shipX) > ShipClearM) && t.FieldAt(root + Vector2.down * RootProbeM) >= Meridian.Terrain.GroundField.Iso;
        /// <summary>Nothing is rooted this near the landed ship's middle (m): its fins and the pad's platform.</summary>
        public const float ShipClearM = 4.5f;
        float shipX; bool shipStands;

        /// <summary>D-206: play_front stands over the surveyor's feet, so it is low: a tuft (0.29 m) at this scale and the scatter's
        /// largest size (x 1.15) is 0.295 m.</summary>
        public const float PlayFrontScale = 0.88f, PlayFrontMaxM = 0.30f;
        /// <summary>How far under its root a piece's ground is asked for (m).</summary>
        public const float RootProbeM = 0.15f;
        public const float VineLinkM = 0.25f;

        void Scatter(Meridian.Terrain.TerrainStreamer t, Layer layer, float everyM, float jitterM, float scale, Color32 tint, LivingPlaceholders.Kind[] kinds, float sinkM, int salt)
        {
            var list = layers[(int)layer].instances;
            int n = Mathf.FloorToInt((West + East) / everyM);
            for (int i = 0; i < n; i++)
            {
                float x = anchorX - West + (i + 0.5f) * everyM + (Roll(i, salt) - 0.5f) * 2f * jitterM;
                var root = new Vector2(x, t.SurfaceAt(x));
                if (!Rooted(t, root)) continue; // the pad, a hole
                var kind = kinds[Mathf.Min(kinds.Length - 1, Mathf.FloorToInt(Roll(i, salt + 1) * kinds.Length))];
                list.Add(new LivingInstance
                {
                    piece = (int)kind, at = root + Vector2.down * sinkM, scale = scale * Mathf.Lerp(0.85f, 1.15f, Roll(i, salt + 2)),
                    flip = layer == Layer.Foreground && Roll(i, salt + 3) > 0.5f, // D-206: never on near, play or play_front
                    phase = Roll(i, salt + 4), tint = tint,
                });
            }
        }

        void Upload(LayerMesh lm)
        {
            vertices.Clear(); uv0.Clear(); uv1.Clear(); uv2.Clear(); colors.Clear(); triangles.Clear();
            for (int i = 0; i < lm.instances.Count; i++)
            {
                var inst = lm.instances[i];
                LivingMesh.Append(pieces[inst.piece], inst, vertices, uv0, uv1, uv2, colors, triangles);
            }
            lm.mesh.Clear();
            lm.mesh.SetVertices(vertices);
            lm.mesh.SetUVs(0, uv0);
            lm.mesh.SetUVs(1, uv1);
            lm.mesh.SetUVs(2, uv2);
            lm.mesh.SetColors(colors);
            lm.mesh.SetTriangles(triangles, 0, false);
            lm.mesh.RecalculateBounds();
            var b = lm.mesh.bounds; b.Expand(new Vector3(2f, 2f, 0.1f)); lm.mesh.bounds = b; // the bend moves vertices past their rest
        }

        // ---------- a piece's ground dug away ----------

        Meridian.Rig.RigTools hookedRig;
        Meridian.FX.FxPool fx;
        Meridian.FX.SideFx sideFx;
        /// <summary>The pieces asked about by the last dig (the report's "what the check costs": a distance test each, a field read for the near ones).</summary>
        public int LastDigAsked { get; private set; }
        public int LastDigRead { get; private set; }

        void OnDug(Vector2 at)
        {
            if (!Built || builtFor == null) return;
            var t = builtFor.terrain;
            float reach = Meridian.Rig.RigTools.BrushRadius + 0.6f;
            LastDigAsked = LastDigRead = 0;
            for (int l = 0; l < Layers; l++)
            {
                if (l == (int)Layer.Foreground) continue; // rooted under the frame, not in this ground
                var lm = layers[l];
                float shift = lm.go.transform.position.x;
                bool changed = false;
                for (int i = 0; i < lm.instances.Count; i++)
                {
                    var inst = lm.instances[i];
                    LastDigAsked++;
                    if (inst.gone || pieces[inst.piece].motion == LivingMotion.Hangs) continue;
                    var root = new Vector2(inst.at.x + shift, inst.at.y);
                    if ((root - at).sqrMagnitude > reach * reach) continue;
                    LastDigRead++;
                    if (t.FieldAt(new Vector2(root.x, t.SurfaceAt(root.x)) + Vector2.down * RootProbeM) >= Meridian.Terrain.GroundField.Iso) continue;
                    inst.gone = true;
                    lm.instances[i] = inst;
                    changed = true;
                    Removed++;
                    if (fx != null && sideFx != null) { var puff = sideFx.PuffAt(root); if (puff != null) fx.Play(puff, root + Vector2.up * 0.2f, 0.8f); }
                }
                if (changed) Upload(lm);
            }
        }

        // ---------- (3) the vine ----------

        public VineChain Chain { get; private set; }
        GameObject vineGo; Mesh vineMesh;
        readonly List<Vector3> vineVertices = new List<Vector3>(64);
        float vineHalf;

        void BuildVine(in LivingPiece piece)
        {
            vineGo = new GameObject("Living_Vine");
            vineGo.transform.SetParent(transform, false);
            vineMesh = new Mesh { name = "Living_Vine" };
            vineMesh.MarkDynamic();
            vineGo.AddComponent<MeshFilter>().sharedMesh = vineMesh;
            var r = vineGo.AddComponent<MeshRenderer>();
            r.sharedMaterial = unlit; r.sortingOrder = Orders[(int)Layer.Play];
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;
            vineHalf = piece.sizeM.x * 0.5f;
            int n = Chain.Count;
            var uv = new List<Vector2>(n * 2); var zero = new List<Vector4>(n * 2); var white = new List<Color32>(n * 2); var tris = new List<int>((n - 1) * 6);
            vineVertices.Clear();
            for (int i = 0; i < n; i++)
            {
                float v = 1f - (float)i / (n - 1);
                vineVertices.Add(Vector3.zero); vineVertices.Add(Vector3.zero);
                uv.Add(new Vector2(piece.uv.xMin, piece.uv.yMin + piece.uv.height * v));
                uv.Add(new Vector2(piece.uv.xMax, piece.uv.yMin + piece.uv.height * v));
                zero.Add(Vector4.zero); zero.Add(Vector4.zero);
                white.Add(new Color32(255, 255, 255, 255)); white.Add(new Color32(255, 255, 255, 255));
                if (i + 1 < n) { int a = i * 2; tris.Add(a); tris.Add(a + 1); tris.Add(a + 2); tris.Add(a + 1); tris.Add(a + 3); tris.Add(a + 2); }
            }
            PoseVine();
            vineMesh.SetVertices(vineVertices);
            vineMesh.SetUVs(0, uv); vineMesh.SetUVs(1, zero); vineMesh.SetUVs(2, zero);
            vineMesh.SetColors(white);
            vineMesh.SetTriangles(tris, 0, false);
            vineMesh.bounds = new Bounds(Chain.Anchor + Vector2.down * (piece.sizeM.y * 0.5f), new Vector3(piece.sizeM.y * 2.5f, piece.sizeM.y * 2.5f, 1f));
        }

        void PoseVine()
        {
            int n = Chain.Count;
            for (int i = 0; i < n; i++)
            {
                Vector2 p = Chain[i];
                Vector2 along = Chain[Mathf.Min(n - 1, i + 1)] - Chain[Mathf.Max(0, i - 1)];
                Vector2 across = along.sqrMagnitude > 1e-8f ? new Vector2(-along.y, along.x).normalized : Vector2.right;
                if (across.x < 0f) across = -across; // the picture's left stays left
                vineVertices[i * 2] = p - across * vineHalf;
                vineVertices[i * 2 + 1] = p + across * vineHalf;
            }
        }

        // ---------- (4) the lit piece ----------

        GameObject rockGo, lampGo;
        /// <summary>The lamp reads the normal map (false: this URP build did not let the stage switch that on; the rock is then lit flat).</summary>
        public bool LampUsesNormals { get; private set; }

        void BuildLitRock(Vector2 at)
        {
            rockGo = new GameObject("Living_LitRock");
            rockGo.transform.SetParent(transform, false);
            var mesh = new Mesh { name = "Living_LitRock" };
            vertices.Clear(); uv0.Clear(); uv1.Clear(); uv2.Clear(); colors.Clear(); triangles.Clear();
            LivingMesh.Append(pieces[(int)LivingPlaceholders.Kind.Rock], new LivingInstance { piece = (int)LivingPlaceholders.Kind.Rock, at = at, scale = 1f, tint = new Color32(255, 255, 255, 255) }, vertices, uv0, uv1, uv2, colors, triangles);
            mesh.SetVertices(vertices); mesh.SetUVs(0, uv0); mesh.SetUVs(1, uv1); mesh.SetUVs(2, uv2); mesh.SetColors(colors); mesh.SetTriangles(triangles, 0, true);
            rockGo.AddComponent<MeshFilter>().sharedMesh = mesh;
            var r = rockGo.AddComponent<MeshRenderer>();
            r.sharedMaterial = lit; r.sortingOrder = Orders[(int)Layer.Play];
            r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; r.receiveShadows = false;

            lampGo = new GameObject("Living_Lamp");
            lampGo.transform.SetParent(transform, false);
            lampGo.transform.position = new Vector3(at.x + 1.1f, at.y + 1.5f, 0f);
            var lamp = lampGo.AddComponent<UnityEngine.Rendering.Universal.Light2D>();
            lamp.lightType = UnityEngine.Rendering.Universal.Light2D.LightType.Point;
            lamp.pointLightOuterRadius = 3.5f;
            lamp.pointLightInnerRadius = 0.5f;
            lamp.intensity = LampIntensity;
            lamp.color = new Color(1f, 0.82f, 0.58f);
            // URP 17.6 gives the light's normal-map quality no setter: the serialized field is set by name (a pilot's stand-in for
            // an authored light). If a later URP renames it the lamp still lights the rock, flat, and LampUsesNormals says so.
            var field = typeof(UnityEngine.Rendering.Universal.Light2D).GetField("m_NormalMapQuality", System.Reflection.BindingFlags.Instance | System.Reflection.BindingFlags.NonPublic);
            if (field != null) { field.SetValue(lamp, UnityEngine.Rendering.Universal.Light2D.NormalMapQuality.Fast); LampUsesNormals = true; }
        }

        /// <summary>D-206 (Q3): a light of the game's adds at most about this in its pool over the painted colour.</summary>
        public const float LampIntensity = 0.35f;

        // ---------- (2) the air ----------

        public const int Motes = 40, Leaves = 8, Shafts = 10;
        GameObject moteGo, shaftGo; Mesh moteMesh, shaftMesh;
        readonly Vector2[] motePos = new Vector2[Motes + Leaves];
        readonly float[] motePhase = new float[Motes + Leaves];
        readonly List<Vector3> moteVertices = new List<Vector3>((Motes + Leaves) * 4);
        readonly List<Color32> moteColors = new List<Color32>((Motes + Leaves) * 4);
        readonly List<Vector3> shaftVertices = new List<Vector3>((Shafts + 1) * 4);
        readonly List<Color32> shaftColors = new List<Color32>((Shafts + 1) * 4);
        /// <summary>The box round the camera the motes live in (half sizes, m).</summary>
        public const float AirHalfX = 13f, AirHalfY = 7.5f;

        Mesh QuadMesh(string name, int quads, LivingPlaceholders.Kind[] kinds, List<Vector3> verts, List<Color32> cols, out GameObject go, int order)
        {
            go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var mesh = new Mesh { name = name };
            mesh.MarkDynamic();
            var uv = new List<Vector2>(quads * 4); var zero = new List<Vector4>(quads * 4); var tris = new List<int>(quads * 6);
            verts.Clear(); cols.Clear();
            for (int q = 0; q < quads; q++)
            {
                var r = LivingPlaceholders.UvOf(kinds[q]);
                uv.Add(new Vector2(r.xMin, r.yMin)); uv.Add(new Vector2(r.xMax, r.yMin)); uv.Add(new Vector2(r.xMin, r.yMax)); uv.Add(new Vector2(r.xMax, r.yMax));
                for (int k = 0; k < 4; k++) { verts.Add(Vector3.zero); cols.Add(new Color32(255, 255, 255, 0)); zero.Add(Vector4.zero); }
                int a = q * 4;
                tris.Add(a); tris.Add(a + 2); tris.Add(a + 1); tris.Add(a + 1); tris.Add(a + 2); tris.Add(a + 3);
            }
            mesh.SetVertices(verts); mesh.SetUVs(0, uv); mesh.SetUVs(1, zero); mesh.SetUVs(2, zero); mesh.SetColors(cols); mesh.SetTriangles(tris, 0, false);
            mesh.bounds = new Bounds(Vector3.zero, new Vector3(1e5f, 1e5f, 10f)); // it follows the camera: always in view
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterial = unlit; mr.sortingOrder = order;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off; mr.receiveShadows = false;
            return mesh;
        }

        void BuildAir(PlanetSideRoot side)
        {
            var kinds = new LivingPlaceholders.Kind[Motes + Leaves];
            for (int i = 0; i < kinds.Length; i++) kinds[i] = i < Motes ? LivingPlaceholders.Kind.Mote : LivingPlaceholders.Kind.Leaf;
            moteMesh = QuadMesh("Living_Motes", kinds.Length, kinds, moteVertices, moteColors, out moteGo, MoteOrder);
            Vector2 cam = side.sideCamera.transform.position;
            for (int i = 0; i < kinds.Length; i++)
            {
                motePos[i] = cam + new Vector2((Roll(i, 601) * 2f - 1f) * AirHalfX, (Roll(i, 602) * 2f - 1f) * AirHalfY);
                motePhase[i] = Roll(i, 603);
            }
            var shaftKinds = new LivingPlaceholders.Kind[Shafts + 1];
            for (int i = 0; i < Shafts; i++) shaftKinds[i] = LivingPlaceholders.Kind.Shaft;
            shaftKinds[Shafts] = LivingPlaceholders.Kind.Cloud;
            shaftMesh = QuadMesh("Living_Shafts", Shafts + 1, shaftKinds, shaftVertices, shaftColors, out shaftGo, ShaftOrder);
        }

        void StepAir(PlanetSideRoot side, float dt)
        {
            Vector2 cam = side.sideCamera.transform.position;
            float t = Wind.Clock;
            // the motes and the leaves: carried by the gust where they are, a slow bob of their own, wrapped round the camera
            for (int i = 0; i < Motes + Leaves; i++)
            {
                var p = motePos[i];
                float gust = Wind.Gust(p.x), phase = motePhase[i];
                bool leaf = i >= Motes;
                var v = Wind.Direction * (Wind.Strength * (leaf ? 1.6f : 0.5f) * (0.25f + gust));
                v.y += (leaf ? -0.25f : 0.05f) + 0.12f * Mathf.Sin(t * (0.7f + phase) + phase * 6.2832f);
                p += v * dt;
                if (p.x > cam.x + AirHalfX) p.x -= 2f * AirHalfX; else if (p.x < cam.x - AirHalfX) p.x += 2f * AirHalfX;
                if (p.y > cam.y + AirHalfY) p.y -= 2f * AirHalfY; else if (p.y < cam.y - AirHalfY) p.y += 2f * AirHalfY;
                motePos[i] = p;
                float half = leaf ? 0.11f : Mathf.Lerp(0.02f, 0.045f, phase), halfY = leaf ? 0.075f : half;
                float turn = leaf ? phase * 6.2832f + t * (1.1f + phase) : 0f;
                float c = Mathf.Cos(turn), s = Mathf.Sin(turn);
                Vector2 ax = new Vector2(c, s) * half, ay = new Vector2(-s, c) * halfY;
                int a = i * 4;
                moteVertices[a] = p - ax - ay; moteVertices[a + 1] = p + ax - ay; moteVertices[a + 2] = p - ax + ay; moteVertices[a + 3] = p + ax + ay;
                byte alpha = leaf ? (byte)230 : (byte)(70f + 110f * (0.5f + 0.5f * Mathf.Sin(t * (1.3f + phase) + phase * 11f))); // a mote glints in and out of the light
                var col = leaf ? new Color32(255, 255, 255, alpha) : new Color32(255, 246, 214, alpha);
                moteColors[a] = moteColors[a + 1] = moteColors[a + 2] = moteColors[a + 3] = col;
            }
            moteMesh.SetVertices(moteVertices);
            moteMesh.SetColors(moteColors);

            // the shafts: slanted bands from the upper right that breathe; the cloud's shadow sliding over the ground with the long gust
            float ground = side.terrain.SurfaceAt(anchorX);
            for (int i = 0; i < Shafts; i++)
            {
                float x = anchorX - West + 3f + i * 7f + 2f * Roll(i, 701), w = 1.2f + Roll(i, 702), top = 9f, lean = 2.6f; // two or three in a 20 m view
                int a = i * 4;
                shaftVertices[a] = new Vector3(x - w, ground - 0.3f, 0f); shaftVertices[a + 1] = new Vector3(x + w, ground - 0.3f, 0f);
                shaftVertices[a + 2] = new Vector3(x - w + lean, ground + top, 0f); shaftVertices[a + 3] = new Vector3(x + w + lean, ground + top, 0f);
                byte alpha = (byte)(255f * Mathf.Clamp01(0.17f + 0.07f * Mathf.Sin(t * 0.45f + i * 2.1f) + 0.04f * Wind.Gust(x)));
                shaftColors[a] = shaftColors[a + 1] = shaftColors[a + 2] = shaftColors[a + 3] = new Color32(255, 240, 205, alpha);
            }
            {
                float span = West + East + 40f;
                float x = anchorX - West - 20f + Mathf.Repeat(t * LivingWind.GustSpeedA * 0.6f + 30f, span), hw = 13f, hh = 3.2f;
                int a = Shafts * 4;
                shaftVertices[a] = new Vector3(x - hw, ground - hh * 0.6f, 0f); shaftVertices[a + 1] = new Vector3(x + hw, ground - hh * 0.6f, 0f);
                shaftVertices[a + 2] = new Vector3(x - hw, ground + hh * 1.4f, 0f); shaftVertices[a + 3] = new Vector3(x + hw, ground + hh * 1.4f, 0f);
                shaftColors[a] = shaftColors[a + 1] = shaftColors[a + 2] = shaftColors[a + 3] = new Color32(24, 34, 52, 46);
            }
            shaftMesh.SetVertices(shaftVertices);
            shaftMesh.SetColors(shaftColors);
        }

        // ---------- every frame ----------

        void Step(PlanetSideRoot side, float dt)
        {
            Wind.Set(WindDirection, WindOn ? WindStrength : 0f);
            Wind.Step(dt);
            var player = side.player;
            bool onFoot = player.isActiveAndEnabled && player.Body != null;
            Vector2 feet = onFoot ? (Vector2)player.transform.position : Vector2.zero;
            Wind.SetPusher(feet, onFoot && WindOn);
            Wind.Push();

            float camX = side.sideCamera.transform.position.x;
            for (int l = 0; l < Layers; l++)
            {
                float shift = (camX - anchorX) * Parallax[l];
                var tr = layers[l].go.transform;
                if (tr.position.x != shift) tr.position = new Vector3(shift, 0f, 0f);
            }

            if (moteGo.activeSelf != AirOn) { moteGo.SetActive(AirOn); shaftGo.SetActive(AirOn); }
            if (AirOn) StepAir(side, dt);

            if (vineGo.activeSelf != VineOn) vineGo.SetActive(VineOn);
            if (VineOn)
            {
                Chain.Step(dt, Wind, feet + Vector2.up * 0.9f, new Vector2(0.3f, 0.9f), onFoot);
                PoseVine();
                vineMesh.SetVertices(vineVertices);
            }

            if (rockGo.activeSelf != LightOn) { rockGo.SetActive(LightOn); lampGo.SetActive(LightOn); }
        }

        /// <summary>The camp's wind: from the west, a moderate breeze (the stage file's when pieces land).</summary>
        public static Vector2 WindDirection = Vector2.right;
        public static float WindStrength = 0.6f;

        // ---------- taking it down ----------

        void Clear()
        {
            if (hookedRig != null) { hookedRig.Dug -= OnDug; hookedRig = null; }
            for (int i = transform.childCount - 1; i >= 0; i--)
            {
                var child = transform.GetChild(i).gameObject;
                var mf = child.GetComponent<MeshFilter>();
                if (mf != null && mf.sharedMesh != null) Destroy(mf.sharedMesh);
                Destroy(child);
            }
            for (int l = 0; l < Layers; l++) layers[l] = null;
            if (unlit != null) Destroy(unlit);
            if (lit != null) Destroy(lit);
            if (colour != null) Destroy(colour);
            if (normal != null) Destroy(normal);
            unlit = lit = null; colour = normal = null;
            moteGo = shaftGo = vineGo = rockGo = lampGo = null;
            moteMesh = shaftMesh = vineMesh = null;
            Chain = null; Wind = null; builtFor = null;
            Built = false; Removed = 0;
            LivingWind.PushStill();
        }
    }
}
