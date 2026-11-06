using System;
using System.Runtime.InteropServices;

namespace Meridian.Perf
{
    /// <summary>U-086 (Bible §11.1 v3 "RAM (built game)"): the process working set from the OS on Windows; -1 elsewhere.</summary>
    public static class ProcessMemory
    {
        [StructLayout(LayoutKind.Sequential)]
        struct Counters
        {
            public uint cb;
            public uint PageFaultCount;
            public UIntPtr PeakWorkingSetSize;
            public UIntPtr WorkingSetSize;
            public UIntPtr QuotaPeakPagedPoolUsage;
            public UIntPtr QuotaPagedPoolUsage;
            public UIntPtr QuotaPeakNonPagedPoolUsage;
            public UIntPtr QuotaNonPagedPoolUsage;
            public UIntPtr PagefileUsage;
            public UIntPtr PeakPagefileUsage;
        }

#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
        [DllImport("psapi.dll", SetLastError = true)]
        static extern bool GetProcessMemoryInfo(IntPtr process, out Counters counters, uint size);
        [DllImport("kernel32.dll")]
        static extern IntPtr GetCurrentProcess();
#endif

        public static long WorkingSetMB()
        {
#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
            try
            {
                if (GetProcessMemoryInfo(GetCurrentProcess(), out var c, (uint)Marshal.SizeOf<Counters>()))
                    return (long)(ulong)c.WorkingSetSize / (1024L * 1024L);
            }
            catch (Exception) { }
#endif
            return -1;
        }
    }
}
