using System.Collections.Generic;
using Meridian.Art;
using Meridian.Planets;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.ResourceManagement.ResourceLocations;

namespace Meridian.Ship
{
    /// <summary>
    /// The Escape Line drawn in the world (Bible §5.1). U-104 (B-121, D-090): the hand-painted dotted line `ui/hud/escape_line`
    /// tiled across the view at the planet's Escape Line y, with its little sign `ui/hud/escape_sign` standing on the line a
    /// third of the frame left of centre, lettered ESCAPE LINE at runtime in Patrick Hand (TextMeshPro, the sign ships blank).
    /// Until the art is in the catalog the U-018 band and its drifting TextMesh label draw as before.
    /// </summary>
    public sealed class EscapeLineBand : MonoBehaviour
    {
        public const string Lettering = "ESCAPE LINE";
        /// <summary>The sign stands this fraction of the view's half width left of the camera.</summary>
        public const float SignOffset = -0.35f;
        /// <summary>The lettering box inside the 192 × 224 px sign (metres at PPU 64): centred on the board, a touch crooked.</summary>
        public const float BoardCentreY = 2.45f, BoardWidth = 2.3f, BoardHeight = 0.95f, BoardTiltDeg = -3f;

        public Camera view;
        public SpriteRenderer band;
        public TextMesh label;
        public float scrollSpeed = 0.6f;
        public float bandHeight = 1.2f;
        float lineY;

        /// <summary>The planet's Escape Line height (world y).</summary>
        public float LineY => lineY;
        /// <summary>U-104: the painted line and the sign once their art is in (null on the legacy band).</summary>
        public SpriteRenderer Line { get; private set; }
        public SpriteRenderer Sign { get; private set; }
        public TMPro.TextMeshPro SignText { get; private set; }
        public bool UsesArt => Line != null && Line.sprite != null;
        /// <summary>World y of the sign's foot (= the line) while the art draws.</summary>
        public float SignY => Sign != null ? Sign.transform.position.y : float.NaN;
        /// <summary>The sign's text (a string, so tests need no TextMeshPro reference); null before the sign exists.</summary>
        public string SignLettering => SignText != null ? SignText.text : null;

        readonly List<AsyncOperationHandle> handles = new List<AsyncOperationHandle>(2);
        Meridian.FX.FxLoop legacyFlow; // U-033: SceneAuthoring's FxLoop that flows the old band's clip and drives its renderer's enabled flag

        public void ConfigureFor(PlanetConfig planet) => lineY = planet.EscapeLineY;

        void Start()
        {
            Probe<Sprite>(ArtKeys.Ui.EscapeLine, s =>
            {
                if (Line == null)
                {
                    var go = new GameObject("PaintedLine");
                    go.transform.SetParent(transform, false);
                    Line = go.AddComponent<SpriteRenderer>();
                    Line.drawMode = SpriteDrawMode.Tiled;
                    if (band != null) { Line.sortingLayerID = band.sortingLayerID; Line.sortingOrder = band.sortingOrder; }
                    var unlit = Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.unlit : null;
                    if (unlit != null) Line.sharedMaterial = unlit;
                }
                Line.sprite = s;
                Line.size = new Vector2(Line.size.x, s.bounds.size.y);
                if (band != null) band.enabled = false;
                if (label != null) label.gameObject.SetActive(false);
            });
            Probe<Sprite>(ArtKeys.Ui.EscapeSign, s =>
            {
                if (Sign == null)
                {
                    var go = new GameObject("Sign");
                    go.transform.SetParent(transform, false);
                    Sign = go.AddComponent<SpriteRenderer>();
                    if (band != null) { Sign.sortingLayerID = band.sortingLayerID; Sign.sortingOrder = band.sortingOrder + 1; }
                    var unlit = Meridian.Rendering.ArtMaterials.Active != null ? Meridian.Rendering.ArtMaterials.Active.unlit : null;
                    if (unlit != null) Sign.sharedMaterial = unlit;
                    // The lettering: a world-space TextMeshPro in the HUD face, ink-coloured, sized to the board.
                    var tgo = new GameObject("Lettering");
                    tgo.transform.SetParent(go.transform, false);
                    tgo.transform.localPosition = new Vector3(0f, BoardCentreY, -0.01f);
                    tgo.transform.localRotation = Quaternion.Euler(0f, 0f, BoardTiltDeg);
                    SignText = tgo.AddComponent<TMPro.TextMeshPro>();
                    var theme = Meridian.UI.UiTheme.Active;
                    if (theme.hudFont != null) SignText.font = theme.hudFont;
                    SignText.text = Lettering;
                    SignText.color = new Color(0.118f, 0.102f, 0.09f, 1f); // ink #1E1A17
                    SignText.alignment = TMPro.TextAlignmentOptions.Center;
                    SignText.textWrappingMode = TMPro.TextWrappingModes.NoWrap;
                    SignText.enableAutoSizing = true;
                    SignText.fontSizeMin = 1f; SignText.fontSizeMax = 8f;
                    SignText.rectTransform.sizeDelta = new Vector2(BoardWidth, BoardHeight);
                    var mr = SignText.GetComponent<MeshRenderer>();
                    if (mr != null) { mr.sortingLayerID = Sign.sortingLayerID; mr.sortingOrder = Sign.sortingOrder + 1; }
                }
                Sign.sprite = s;
            });
        }

        void Probe<T>(string address, System.Action<T> set) where T : class
        {
            var probe = Addressables.LoadResourceLocationsAsync(address, typeof(T));
            probe.Completed += l =>
            {
                IResourceLocation loc = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0 ? l.Result[0] : null;
                ArtLoad.Release(l);
                if (loc == null || this == null) return;
                var h = ArtLoad.Asset<T>(loc, address);
                handles.Add(h);
                h.Completed += op => { if (this != null && op.Status == AsyncOperationStatus.Succeeded && op.Result != null) set(op.Result); };
            };
        }

        void LateUpdate()
        {
            if (view == null) return;
            float halfWidth = Meridian.CameraRig.SideView.HalfHeight(view) * view.aspect;
            float width = halfWidth * 2f + 4f;
            transform.position = new Vector3(view.transform.position.x, lineY, 0f);
            if (UsesArt)
            {
                // The painted dots stay put in the world (the strip shifts by whole periods as the camera moves), the sign rides the frame.
                float period = Line.sprite.bounds.size.x;
                float x = period > 0f ? Mathf.Round(view.transform.position.x / period) * period - view.transform.position.x : 0f;
                if (Mathf.Abs(Line.size.x - width) > 0.01f) Line.size = new Vector2(width + 2f * period, Line.size.y);
                Line.transform.localPosition = new Vector3(x, 0f, 0f);
                if (Sign != null) Sign.transform.localPosition = new Vector3(halfWidth * SignOffset, 0f, 0f);
                // The U-018 band and its U-033 flow loop stay off while the painting draws (the loop re-enables its renderer every frame).
                if (legacyFlow == null) legacyFlow = GetComponent<Meridian.FX.FxLoop>();
                if (legacyFlow != null && legacyFlow.enabled) { legacyFlow.active = false; legacyFlow.enabled = false; }
                if (band != null && band.enabled) band.enabled = false;
                if (label != null && label.gameObject.activeSelf) label.gameObject.SetActive(false);
                return;
            }
            if (band != null)
            {
                band.size = new Vector2(width, bandHeight);
                var c = band.color;
                c.a = 0.22f + 0.08f * Mathf.Sin(Time.time * scrollSpeed * 3f);
                band.color = c;
            }
            if (label != null)
            {
                // Label drifts slowly along the band and wraps across the view.
                float x = Mathf.Repeat(Time.time * scrollSpeed * 2f, width) - width * 0.5f;
                label.transform.localPosition = new Vector3(x, 0.9f, 0f);
            }
        }

        void OnDestroy()
        {
            foreach (var h in handles) if (h.IsValid()) ArtLoad.Release(h);
        }
    }
}
