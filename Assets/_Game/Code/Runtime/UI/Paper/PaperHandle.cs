using Meridian.Art;
using UnityEngine;
using UnityEngine.ResourceManagement.AsyncOperations;

namespace Meridian.UI
{
    /// <summary>U-124: holds a UI sprite's Addressables handle (a paper panel, a title card, the Film switch) for as long as its
    /// GameObject lives, then releases it: no static pin across scenes.</summary>
    public sealed class PaperHandle : MonoBehaviour
    {
        public AsyncOperationHandle handle;

        void OnDestroy() { if (handle.IsValid()) ArtLoad.Release(handle); }
    }
}
