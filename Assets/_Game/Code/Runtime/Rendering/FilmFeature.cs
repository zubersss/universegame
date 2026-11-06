using Meridian.Art;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.RenderGraphModule;
using UnityEngine.Rendering.RenderGraphModule.Util;
using UnityEngine.Rendering.Universal;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.Rendering
{
    /// <summary>
    /// U-095 (Bible §9.4 v4, contract §11.6): the film look as one URP renderer feature with one blit after post-processing:
    /// grain, dust and scratches from the three 512² overlays (fx/film/*, loaded once for the session), a vignette, a
    /// ±2 % flicker and a warm grade, all in MERIDIAN/FilmPass. Off when GameSettings.FilmEffects is off (the pass is
    /// not recorded at all). Game cameras only. No allocation per frame.
    /// </summary>
    public sealed class FilmFeature : ScriptableRendererFeature
    {
        public const float GrainAmount = 0.10f, DustAmount = 0.7f, ScratchAmount = 0.55f, Vignette = 0.35f, Grade = 0.6f;
        /// <summary>Flicker amplitude: the frame's brightness factor stays within 1 ± this.</summary>
        public const float FlickerAmplitude = 0.02f;
        public const int OverlaySize = 512;
        public const string GrainKey = "fx/film/grain", DustKey = "fx/film/dust", ScratchesKey = "fx/film/scratches";

        [SerializeField] Material material;
        FilmPass pass;

        /// <summary>Frames in which the pass was recorded (tests: the toggle removes it).</summary>
        public static int FramesRendered { get; private set; }
        /// <summary>The feature that recorded last (tests).</summary>
        public static FilmFeature Instance { get; private set; }
        public Material Material => material;

        /// <summary>The flicker factor for a 12 Hz step: a hash of the step, scaled to ± FlickerAmplitude (pure, tested).</summary>
        public static float Flicker(int step)
        {
            uint h = (uint)step * 2654435761u;
            h ^= h >> 13; h *= 0x5bd1e995u; h ^= h >> 15;
            float unit = (h & 0xffffffu) / (float)0xffffff; // 0..1
            return 1f + (unit * 2f - 1f) * FlickerAmplitude;
        }

        static float Hash01(int step, int salt)
        {
            uint h = (uint)(step * 73856093) ^ (uint)(salt * 19349663);
            h ^= h >> 13; h *= 0x5bd1e995u; h ^= h >> 15;
            return (h & 0xffffffu) / (float)0xffffff;
        }

        public override void Create()
        {
            pass = new FilmPass { renderPassEvent = RenderPassEvent.AfterRenderingPostProcessing };
            pass.requiresIntermediateTexture = true;
            Instance = this;
        }

        public override void AddRenderPasses(ScriptableRenderer renderer, ref RenderingData renderingData)
        {
            if (material == null || !Meridian.Core.GameSettings.FilmEffects) return;
            if (renderingData.cameraData.cameraType != CameraType.Game) return;
            if (SystemInfo.graphicsDeviceType == GraphicsDeviceType.Null) return; // -nographics test runs: no blit target can exist (it crashed the null device)
            pass.material = material;
            renderer.EnqueuePass(pass);
        }

        // ---------- overlays, loaded once for the session ----------

        static AsyncOperationHandle<Texture2D> grainH, dustH, scratchH;
        static Texture2D grain, dust, scratches;
        static bool loading;

        static void EnsureOverlays()
        {
            if (loading) return;
            loading = true;
            Load(GrainKey, ref grainH, t => grain = t);
            Load(DustKey, ref dustH, t => dust = t);
            Load(ScratchesKey, ref scratchH, t => scratches = t);
        }

        static void Load(string key, ref AsyncOperationHandle<Texture2D> handle, System.Action<Texture2D> set)
        {
            handle = ArtLoad.Session<Texture2D>(key);
            handle.Completed += op => { if (op.Status == AsyncOperationStatus.Succeeded) set(op.Result); };
        }

        sealed class FilmPass : ScriptableRenderPass
        {
            public Material material;
            static readonly int TileId = Shader.PropertyToID("_Tile"), OffsetsId = Shader.PropertyToID("_Offsets"),
                Offsets2Id = Shader.PropertyToID("_Offsets2"), AmountsId = Shader.PropertyToID("_Amounts"),
                GrainId = Shader.PropertyToID("_Grain"), DustId = Shader.PropertyToID("_Dust"), ScratchesId = Shader.PropertyToID("_Scratches");

            public override void RecordRenderGraph(RenderGraph renderGraph, ContextContainer frameData)
            {
                var resources = frameData.Get<UniversalResourceData>();
                var camera = frameData.Get<UniversalCameraData>();
                if (resources.isActiveTargetBackBuffer || material == null) return;
                EnsureOverlays();

                // 12 Hz steps: grain and scratches jitter on twos like the drawings; dust drifts slowly.
                int step = Mathf.FloorToInt(Time.time * 12f);
                float w = camera.cameraTargetDescriptor.width, h = camera.cameraTargetDescriptor.height;
                material.SetVector(TileId, new Vector4(w / OverlaySize, h / OverlaySize, 0f, 0f));
                material.SetVector(OffsetsId, new Vector4(Hash01(step, 1), Hash01(step, 2), Time.time * 0.012f, Time.time * 0.004f));
                material.SetVector(Offsets2Id, new Vector4(Hash01(step, 3) * 0.08f, 0f, Flicker(step), Grade));
                material.SetVector(AmountsId, new Vector4(grain != null ? GrainAmount : 0f, dust != null ? DustAmount : 0f, scratches != null ? ScratchAmount : 0f, Vignette));
                if (grain != null) material.SetTexture(GrainId, grain);
                if (dust != null) material.SetTexture(DustId, dust);
                if (scratches != null) material.SetTexture(ScratchesId, scratches);

                var source = resources.activeColorTexture;
                var desc = renderGraph.GetTextureDesc(source);
                desc.name = "Film";
                desc.clearBuffer = false;
                desc.depthBufferBits = 0;
                var dest = renderGraph.CreateTexture(desc);
                renderGraph.AddBlitPass(new RenderGraphUtils.BlitMaterialParameters(source, dest, material, 0), "Film pass");
                resources.cameraColor = dest;
                FramesRendered++;
            }
        }
    }
}
