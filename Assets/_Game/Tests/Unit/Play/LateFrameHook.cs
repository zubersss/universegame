using UnityEngine;

namespace Meridian.Tests
{
    /// <summary>
    /// U-209's frame strips: runs a callback at the end of every frame's LateUpdate, after every other script (the tool view, the drawn
    /// surveyor, the camera), so a capture grabs what THAT frame draws. A test coroutine resumes between Update and LateUpdate: a grab
    /// made there holds the frame before's poses with this frame's Update already run (debris a frame early in the picture).
    /// </summary>
    [DefaultExecutionOrder(32000)]
    public sealed class LateFrameHook : MonoBehaviour
    {
        public System.Action late;

        void LateUpdate() => late?.Invoke();
    }
}
