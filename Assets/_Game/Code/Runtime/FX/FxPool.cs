using UnityEngine;

namespace Meridian.FX
{
    /// <summary>
    /// U-033: pooled one-shot fx (dig sparks, landing dust): Play(key, position) takes a free sprite,
    /// plays the sheet's clip once and frees it. Fixed pool, no allocation per frame; when every slot
    /// is busy the oldest is reused.
    /// </summary>
    public sealed class FxPool : MonoBehaviour
    {
        public const int Size = 48;

        /// <summary>One-shots alive across all pools (BudgetMonitor counts them as particles).</summary>
        public static int TotalAlive { get; private set; }
        public int Alive { get; private set; }

        readonly SpriteRenderer[] slots = new SpriteRenderer[Size];
        readonly FxSheet[] sheets = new FxSheet[Size];
        readonly float[] started = new float[Size];
        readonly int[] shown = new int[Size];

        void Awake()
        {
            for (int i = 0; i < Size; i++)
            {
                var go = new GameObject("Fx" + i);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sortingOrder = 40; // over the player, ship and terrain
                sr.enabled = false;
                slots[i] = sr;
            }
        }

        /// <summary>Starts `key` at `position` (its sheet pivot lands there). Returns false when the art isn't loaded yet.</summary>
        public bool Play(string key, Vector2 position, float scale = 1f, float rotationDeg = 0f)
        {
            var sheet = FxSheet.Get(key);
            if (!sheet.Ready) return false;
            int pick = -1;
            float oldest = float.MaxValue;
            for (int i = 0; i < Size; i++)
            {
                if (sheets[i] == null) { pick = i; break; }
                if (started[i] < oldest) { oldest = started[i]; pick = i; }
            }
            if (sheets[pick] == null) { Alive++; TotalAlive++; }
            sheets[pick] = sheet;
            started[pick] = Time.time;
            shown[pick] = -1;
            var sr = slots[pick];
            if (sheet.material != null) sr.sharedMaterial = sheet.material;
            sr.transform.SetPositionAndRotation(new Vector3(position.x, position.y, 0f), Quaternion.Euler(0f, 0f, rotationDeg));
            sr.transform.localScale = new Vector3(scale, scale, 1f);
            sr.enabled = true;
            return true;
        }

        void Update()
        {
            float now = Time.time;
            for (int i = 0; i < Size; i++)
            {
                var sheet = sheets[i];
                if (sheet == null) continue;
                int f = sheet.FrameAt(now - started[i]);
                if (f < 0 || (sheet.clip.loop && now - started[i] > 2f)) { Free(i); continue; }
                if (f != shown[i]) { shown[i] = f; slots[i].sprite = sheet.frames[f]; }
            }
        }

        void Free(int i)
        {
            sheets[i] = null;
            slots[i].enabled = false;
            Alive--; TotalAlive--;
        }

        void OnDestroy()
        {
            TotalAlive -= Alive;
            Alive = 0;
        }
    }
}
