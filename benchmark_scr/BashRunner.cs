using System.Diagnostics;

namespace benchmark_scr {

    internal static class BashRunner {

        public static async Task<int> RunAsync(string fileName, params string[] args) {
            var psi = new ProcessStartInfo {
                FileName = fileName,
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };

            foreach (var arg in args)
                psi.ArgumentList.Add(arg);

            using var process = new Process { StartInfo = psi };

            process.OutputDataReceived += (_, e) => {
                if (!string.IsNullOrEmpty(e.Data))
                    Console.WriteLine(e.Data);
            };

            process.ErrorDataReceived += (_, e) => {
                if (!string.IsNullOrEmpty(e.Data))
                    Console.Error.WriteLine(e.Data);
            };

            process.Start();
            process.BeginOutputReadLine();
            process.BeginErrorReadLine();

            await process.WaitForExitAsync();
            return process.ExitCode;
        }
    }
}