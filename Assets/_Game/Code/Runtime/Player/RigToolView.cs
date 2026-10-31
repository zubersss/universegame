using System.Collections.Generic;
using Meridian.Art;
using Meridian.FX;
using Meridian.Rendering;
using Meridian.Rig;
using Meridian.Terrain;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Player
{
    /// <summary>
    /// U-046: the selected Rig module in the surveyor's hand (props/rig/*, pivot [0.375, 0.5] at the grip),
    /// rotated to the aim; the Beam's ray (fx/beam_ray, pivot [0, 0.5], tiled in x from the muzzle to the
    /// hit); the Builder's ghost (fx/builder_ghost, 8-frame pulse) on the target cell, red when blocked.
    /// </summary>
    public sealed class RigToolView : MonoBehaviour
    {
        /// <summary>The grip, relative to the surveyor's feet (facing right; mirrored when facing left).</summary>
        public static readonly Vector2 Hand = new Vector2(0.12f, 0.95f);
        public const float BeamHeight = 0.25f;
        public static readonly Color Blocked = new Color(1f, 0.3f, 0.25f, 0.9f);

        public PlayerRigInput input;
        public RigTools rig;

        public SpriteRenderer Tool { get; private set; }
        public SpriteRenderer Beam { get; private set; }
        public SpriteRenderer Ghost { get; private set; }
        public Vector2 HandWorld { get; private set; }
        public Vector2 MuzzleWorld { get; private set; }
        public float AimDegrees { get; private set; }
        public float BeamLength { get; private set; }
        public bool GhostBlocked { get; private set; }

        readonly Sprite[] tools = new Sprite[RigModules.Count + 1];
        readonly List<AsyncOperationHandle<IList<Sprite>>> handles = new List<AsyncOperationHandle<IList<Sprite>>>();
        FxSheet beamSheet, ghostSheet;
        float beamAge, ghostAge;
        readonly RaycastHit2D[] hits = new RaycastHit2D[8];
        static readonly ContactFilter2D AnyCollider = ContactFilter2D.noFilter;

        void Awake()
        {
            Tool = Child("RigTool", 6);
            Beam = Child("BeamRay", 6);
            Beam.drawMode = SpriteDrawMode.Tiled;
            Beam.tileMode = SpriteTileMode.Continuous;
            Ghost = Child("BuilderGhost", 6);
            Beam.enabled = Ghost.enabled = false;
        }

        SpriteRenderer Child(string name, int order)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sortingOrder = order;
            return sr;
        }

        void Start()
        {
            for (int m = 1; m <= RigModules.Count; m++) LoadTool((RigModule)m);
            beamSheet = FxSheet.Get(ArtKeys.Fx.BeamRay);
            ghostSheet = FxSheet.Get(ArtKeys.Fx.BuilderGhost);
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) Addressables.Release(h);
        }

        void LoadTool(RigModule m)
        {
            string key = RigModules.ArtKey(m);
            var h = Addressables.LoadAssetAsync<IList<Sprite>>(key);
            handles.Add(h);
            h.Completed += op =>
            {
                if (op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0) return;
                tools[(int)m] = op.Result[0];
                if (Tool != null && input != null && input.module == m) Show(m);
            };
        }

        RigModule shown;

        void Show(RigModule m)
        {
            shown = m;
            Tool.sprite = tools[(int)m];
            var mat = ArtMaterials.MaterialFor(RigModules.ArtKey(m));
            if (mat != null) Tool.sharedMaterial = mat;
        }

        /// <summary>Where the tool points: the aim while the rig is aimed, else straight ahead.</summary>
        void LateUpdate()
        {
            if (input == null) return;
            if (shown != input.module || Tool.sprite == null) Show(input.module);

            bool left = input.AimWorld.x < transform.position.x;
            var feet = (Vector2)transform.position;
            HandWorld = feet + new Vector2(left ? -Hand.x : Hand.x, Hand.y);
            Vector2 dir = input.AimWorld - HandWorld;
            if (dir.sqrMagnitude < 1e-4f) dir = left ? Vector2.left : Vector2.right;
            AimDegrees = Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg;
            Tool.transform.position = HandWorld;
            Tool.transform.rotation = Quaternion.Euler(0f, 0f, AimDegrees);
            Tool.flipY = left; // keep the tool upright when pointing left
            var muzzle = RigModules.Muzzle(input.module);
            if (left) muzzle.y = -muzzle.y;
            MuzzleWorld = HandWorld + (Vector2)(Tool.transform.rotation * muzzle);

            UpdateBeam(dir.normalized);
            UpdateGhost();
        }

        void UpdateBeam(Vector2 dir)
        {
            bool on = input.module == RigModule.Beam && input.Using && beamSheet != null && beamSheet.Ready;
            if (Beam.enabled != on) Beam.enabled = on;
            if (!on) { beamAge = 0f; BeamLength = 0f; return; }
            // To the first terrain hit, at most the Rig's reach, never past the aim point.
            float max = Mathf.Min(RigTools.Reach, Vector2.Distance(MuzzleWorld, input.AimWorld) + 0.5f);
            float len = max;
            int n = Physics2D.Raycast(MuzzleWorld, dir, AnyCollider, hits, max);
            for (int i = 0; i < n; i++)
                if (hits[i].collider.GetComponentInParent<TerrainChunk>() != null) { len = hits[i].distance; break; }
            BeamLength = len;
            beamAge += Time.deltaTime;
            int f = beamSheet.FrameAt(beamAge);
            if (f >= 0 && Beam.sprite != beamSheet.frames[f])
            {
                Beam.sprite = beamSheet.frames[f];
                if (beamSheet.material != null) Beam.sharedMaterial = beamSheet.material;
            }
            Beam.transform.position = MuzzleWorld;
            Beam.transform.rotation = Quaternion.Euler(0f, 0f, AimDegrees);
            Beam.size = new Vector2(Mathf.Max(0.01f, len), BeamHeight);
        }

        void UpdateGhost()
        {
            bool on = input.module == RigModule.Builder && rig != null && ghostSheet != null && ghostSheet.Ready
                      && (input.AimWorld - (Vector2)transform.position).sqrMagnitude <= (RigTools.Reach + 1f) * (RigTools.Reach + 1f);
            if (Ghost.enabled != on) Ghost.enabled = on;
            if (!on) { ghostAge = 0f; return; }
            var cell = RigTools.TileOf(input.AimWorld);
            Ghost.transform.position = new Vector3(cell.x + 0.5f, cell.y + 0.5f, 0f);
            ghostAge += Time.deltaTime;
            int f = ghostSheet.FrameAt(ghostAge);
            if (f >= 0 && Ghost.sprite != ghostSheet.frames[f])
            {
                Ghost.sprite = ghostSheet.frames[f];
                if (ghostSheet.material != null) Ghost.sharedMaterial = ghostSheet.material;
                float w = Ghost.sprite.bounds.size.x;
                Ghost.transform.localScale = w > 0f ? Vector3.one / w : Vector3.one; // one tile
            }
            byte tile = rig.SelectedTile;
            GhostBlocked = tile == TileId.Air || !rig.CanPlace(input.AimWorld, tile);
            var c = GhostBlocked ? Blocked : Color.white;
            if (Ghost.color != c) Ghost.color = c;
        }
    }
}
