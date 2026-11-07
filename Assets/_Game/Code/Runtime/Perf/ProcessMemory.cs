using System;
using System.Runtime.InteropServices;

namespace Meridian.Perf
{
    /// <summary>U-086 (Bible §11.1 "working set", U-091 private commit): process memory from the OS on Windows; -1 elsewhere.</summary>
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

        [StructLayout(LayoutKind.Sequential)]
        struct MemoryStatus
        {
            public uint dwLength;
            public uint dwMemoryLoad;
            public ulong ullTotalPhys;
            public ulong ullAvailPhys;
            public ulong ullTotalPageFile;
            public ulong ullAvailPageFile;
            public ulong ullTotalVirtual;
            public ulong ullAvailVirtual;
            public ulong ullAvailExtendedVirtual;
        }

#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
        [DllImport("psapi.dll", SetLastError = true)]
        static extern bool GetProcessMemoryInfo(IntPtr process, out Counters counters, uint size);
        [DllImport("kernel32.dll")]
        static extern IntPtr GetCurrentProcess();
        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool GlobalMemoryStatusEx(ref MemoryStatus status);
#endif

        /// <summary>D-083: free physical memory of the machine (MB), the number the heavy-job gate reads; -1 off Windows.</summary>
        public static long FreeSystemMB()
        {
#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
            try
            {
                var s = new MemoryStatus { dwLength = (uint)Marshal.SizeOf<MemoryStatus>() };
                if (GlobalMemoryStatusEx(ref s)) return (long)(s.ullAvailPhys / (1024UL * 1024UL));
            }
            catch (Exception) { }
#endif
            return -1;
        }

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

        /// <summary>U-091 (D-089): private commit (PagefileUsage) in MB: page trimming cannot hide a leak in it; -1 off Windows.</summary>
        public static long PrivateMB()
        {
#if UNITY_STANDALONE_WIN || UNITY_EDITOR_WIN
            try
            {
                if (GetProcessMemoryInfo(GetCurrentProcess(), out var c, (uint)Marshal.SizeOf<Counters>()))
                    return (long)(ulong)c.PagefileUsage / (1024L * 1024L);
            }
            catch (Exception) { }
#endif
            return -1;
        }
    }
}
