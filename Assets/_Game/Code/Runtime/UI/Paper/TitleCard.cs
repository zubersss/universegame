using System.Collections.Generic;
using Meridian.Art;
using Meridian.Core;
using Meridian.Planets;
using Meridian.Transitions;
using UnityEngine;
using UnityEngine.AddressableAssets;
using UnityEngine.ResourceManagement.AsyncOperations;
using UnityEngine.UI;

namespace Meridian.UI
{
    /// <summary>
    /// U-124 (Bible C3, B-151): the planet's title card as a silent-film intertitle after every entry. When the entry's iris has
    /// opened (TransitionDirector.Completed with LastWasEntry), `ui/titlecards/&lt;planet&gt;` (≤ 1920×540, drawn 1:1) slides in from the
    /// left, holds, and slides out to the right, over the HUD and under the menus. The key is probed first: a planet without a card
    /// shows nothing and logs nothing. Batch runs skip it unless a test asks (ShowOverride), like the boot menu. The slide is one
    /// anchoredPosition write per frame while a card is up (no allocation); the card's texture is released when it leaves.
    /// </summary>
    public sealed class TitleCard : MonoBehaviour
    {
        public const float SlideSeconds = 0.4f, HoldSeconds = 1.6f;
        public const float TotalSeconds = SlideSeconds * 2f + HoldSeconds;
        /// <summary>The card's centre above the screen's middle (canvas px at 1080p): the landing ship stays in view below it.</summary>
        public const float CardY = 180f;
        public const int SortingOrder = 450; // over the HUD and panels (100–113), under the menus (500) and the iris (1000)
        /// <summary>Tests set true / false; null = show unless running in batch mode.</summary>
        public static bool? ShowOverride;

        public TransitionDirector transitions;
        public SceneDirector scenes;
        public Image Card { get; private set; }
        /// <summary>The key of the card on screen now, or null (tests read it).</summary>
        public string Showing { get; private set; }
        /// <summary>The key last asked for (shown or probed absent; tests read it).</summary>
        public string LastAsked { get; private set; }
        /// <summary>Seconds since the card started; negative when no card is up.</summary>
        public float T { get; private set; } = -1f;

        RectTransform rect;
        AsyncOperationHandle handle;

        /// <summary>The card's x at time t (canvas px): from off the left edge to the centre, held, then off the right edge. Pure.</summary>
        public static float SlideX(float t, float width = 1920f)
        {
            if (t < SlideSeconds) return Mathf.Lerp(-width, 0f, Ease(t / SlideSeconds));
            if (t < SlideSeconds + HoldSeconds) return 0f;
            return Mathf.Lerp(0f, width, Ease((t - SlideSeconds - HoldSeconds) / SlideSeconds));
        }

        static float Ease(float u) { u = Mathf.Clamp01(u); return u * u * (3f - 2f * u); }

        void Awake()
        {
            var canvas = UiKit.Canvas(transform, "TitleCardCanvas", SortingOrder);
            Card = UiKit.Panel(canvas.transform, "TitleCard", new Vector2(0.5f, 0.5f), new Vector2(-1920f, CardY), new Vector2(1600f, 452f), Color.white);
            Card.preserveAspect = true;
            Card.raycastTarget = false;
            Card.enabled = false;
            rect = Card.rectTransform;
            enabled = false; // no Update until a card is up
        }

        void Start()
        {
            if (transitions == null) transitions = FindAnyObjectByType<TransitionDirector>();
            if (scenes == null) scenes = FindAnyObjectByType<SceneDirector>();
            if (transitions != null) transitions.Completed += OnTransition;
        }

        void OnDestroy()
        {
            if (transitions != null) transitions.Completed -= OnTransition;
            ReleaseCard();
        }

        void OnTransition()
        {
            if (!(ShowOverride ?? !Application.isBatchMode)) return;
            if (transitions == null || !transitions.LastWasEntry) return;
            var side = scenes != null ? scenes.PlanetSide : null;
            if (side == null || side.Config == null) return;
            Show(side.Config.id);
        }

        /// <summary>Probes the planet's card and slides it in when it exists (a card already up is replaced).</summary>
        public void Show(PlanetId planet)
        {
            string key = ArtKeys.Ui.TitleCard(planet);
            LastAsked = key;
            Hide(); // a new planet's card replaces the one up now at once (the 15:26 capture showed the previous card while the next one loaded)
            var probe = Addressables.LoadResourceLocationsAsync(key);
            probe.Completed += l =>
            {
                bool exists = l.Status == AsyncOperationStatus.Succeeded && l.Result != null && l.Result.Count > 0;
                ArtLoad.Release(l);
                if (!exists || this == null || LastAsked != key) return; // a newer card was asked for meanwhile
                ReleaseCard();
                var h = ArtLoad.Asset<IList<Sprite>>(key);
                handle = h;
                h.Completed += op =>
                {
                    if (this == null || LastAsked != key || op.Status != AsyncOperationStatus.Succeeded || op.Result == null || op.Result.Count == 0 || op.Result[0] == null) return;
                    var sprite = op.Result[0];
                    Card.sprite = sprite;
                    rect.sizeDelta = sprite.rect.size; // 1:1 at 1080p (the art is ≤ 1920×540)
                    Card.enabled = true;
                    Showing = key;
                    T = 0f;
                    rect.anchoredPosition = new Vector2(SlideX(0f), CardY);
                    enabled = true;
                };
            };
        }

        void Update()
        {
            if (T < 0f) { enabled = false; return; }
            T += Time.unscaledDeltaTime; // the card plays over a paused game too
            rect.anchoredPosition = new Vector2(SlideX(T), CardY);
            if (T < TotalSeconds) return;
            Hide();
        }

        /// <summary>Takes the card down now and releases its art (the end of the slide, a newer card, a capture that wants the screen).</summary>
        public void Hide()
        {
            T = -1f;
            if (Card != null) Card.enabled = false;
            Showing = null;
            ReleaseCard();
            enabled = false;
        }

        void ReleaseCard()
        {
            if (Card != null) Card.sprite = null;
            if (handle.IsValid()) ArtLoad.Release(handle);
            handle = default;
        }

        /// <summary>Tests and captures: puts the card at time t of its slide (t = SlideSeconds: centred, the held frame).</summary>
        public void Seek(float t)
        {
            if (Showing == null) return;
            T = t;
            rect.anchoredPosition = new Vector2(SlideX(T), CardY);
        }
    }
}
