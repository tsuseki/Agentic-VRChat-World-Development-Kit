using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using UnityEditor;

namespace AWDK.AgentTools
{
    /// <summary>
    /// One unit of time-sliced editor work. The body is an iterator: each <c>yield return null</c>
    /// marks a point where the runner may hand control back to the editor, so keep the work between
    /// two yields small (a few milliseconds).
    /// </summary>
    public sealed class AgentJob
    {
        public readonly string Kind;
        /// <summary>Short human-readable progress, e.g. "query 41000/100000".</summary>
        public string Progress = "starting";
        /// <summary>Final text report; set when <see cref="Done"/>.</summary>
        public string Result;
        public bool Done;
        public int Slices;
        public double MaxSliceMs;
        public double WorkMs;
        public readonly DateTime StartedUtc = DateTime.UtcNow;
        /// <summary>Optional: builds a partial report when the job is cut short (timeout or cancel).</summary>
        public Func<string, string> PartialReport;

        internal IEnumerator Routine;
        bool inStep;

        internal AgentJob(string kind) { Kind = kind; }

        public double ElapsedSeconds => (DateTime.UtcNow - StartedUtc).TotalSeconds;

        public string StatusText()
        {
            if (Done) return Result;
            return string.Format(Util.Inv, "STATE=running progress={0} slices={1} maxSliceMs={2:0} elapsed={3:0.0}s",
                Progress, Slices, MaxSliceMs, ElapsedSeconds);
        }

        /// <summary>Runs the body until the slice budget is used up or the job finishes.</summary>
        internal void Step(double budgetMs)
        {
            if (Done || inStep) return;
            inStep = true;
            var sw = Stopwatch.StartNew();
            try
            {
                while (true)
                {
                    bool more;
                    try { more = Routine.MoveNext(); }
                    catch (Exception e)
                    {
                        Finish("ERROR " + Kind + " failed: " + e);
                        break;
                    }
                    if (!more)
                    {
                        Finish(Result ?? (Kind + " finished without a report"));
                        break;
                    }
                    if (sw.Elapsed.TotalMilliseconds >= budgetMs || ReferenceEquals(Routine.Current, JobRunner.EndSlice)) break;
                }
            }
            finally
            {
                double ms = sw.Elapsed.TotalMilliseconds;
                Slices++;
                WorkMs += ms;
                if (ms > MaxSliceMs) MaxSliceMs = ms;
                inStep = false;
            }
        }

        internal void Finish(string result)
        {
            if (Done) return;
            Result = result;
            Done = true;
            (Routine as IDisposable)?.Dispose();
        }

        internal void Abort(string why)
        {
            if (Done) return;
            string partial = null;
            try { partial = PartialReport?.Invoke(why); } catch (Exception) { /* fall through to plain text */ }
            Finish(partial ?? ("ABORTED " + Kind + ": " + why + " (progress " + Progress + ")"));
        }
    }

    /// <summary>
    /// Runs <see cref="AgentJob"/>s on <see cref="EditorApplication.update"/>, one job per kind.
    /// Each editor tick (and each Status poll) spends at most <see cref="SliceBudgetMs"/> on a job,
    /// so the editor stays responsive and an MCP call never blocks for long.
    /// Jobs live in memory only: a script reload or play-mode domain reload clears them.
    /// </summary>
    public static class JobRunner
    {
        /// <summary>Time budget per job per editor tick. Overshoot is bounded by the work between two yields.</summary>
        public static double SliceBudgetMs = 150;
        /// <summary>Yield this from a job body to end the current slice early (e.g. while waiting for frames).</summary>
        public static readonly object EndSlice = new object();

        static readonly Dictionary<string, AgentJob> jobs = new Dictionary<string, AgentJob>();
        static bool hooked;

        /// <summary>Creates a job without scheduling it (used by RunBlocking).</summary>
        public static AgentJob Create(string kind, Func<AgentJob, IEnumerator> body)
        {
            var job = new AgentJob(kind);
            job.Routine = body(job);
            return job;
        }

        /// <summary>Registers a job as the current one of its kind (superseding a running one) and schedules it.</summary>
        public static AgentJob Start(string kind, Func<AgentJob, IEnumerator> body)
        {
            if (jobs.TryGetValue(kind, out var old) && !old.Done) old.Abort("superseded by a new Start()");
            var job = Create(kind, body);
            jobs[kind] = job;
            if (!hooked)
            {
                EditorApplication.update += Tick;
                hooked = true;
            }
            return job;
        }

        /// <summary>Runs a job to completion on the calling thread, in slices, for tests and scripts.</summary>
        public static string RunBlocking(AgentJob job, double maxSeconds)
        {
            jobs[job.Kind] = job;
            var sw = Stopwatch.StartNew();
            while (!job.Done)
            {
                if (sw.Elapsed.TotalSeconds > maxSeconds)
                {
                    job.Abort(string.Format(Util.Inv, "RunBlocking exceeded {0:0.#} s", maxSeconds));
                    break;
                }
                job.Step(SliceBudgetMs);
            }
            return job.Result;
        }

        public static AgentJob Get(string kind) => jobs.TryGetValue(kind, out var j) ? j : null;

        /// <summary>Status text for a kind; also advances a running job by one slice.</summary>
        public static string Status(string kind)
        {
            var job = Get(kind);
            if (job == null) return "STATE=idle no " + kind + " job in this editor session (script reloads clear jobs)";
            if (!job.Done) job.Step(SliceBudgetMs);
            return job.StatusText();
        }

        /// <summary>Stops a running job of this kind; its partial report (if any) becomes the result.</summary>
        public static string Cancel(string kind)
        {
            var job = Get(kind);
            if (job == null || job.Done) return "STATE=idle nothing to cancel";
            job.Abort("cancelled");
            return job.Result;
        }

        static void Tick()
        {
            bool any = false;
            foreach (var job in new List<AgentJob>(jobs.Values))
            {
                if (job.Done) continue;
                job.Step(SliceBudgetMs);
                if (!job.Done) any = true;
            }
            if (!any)
            {
                EditorApplication.update -= Tick;
                hooked = false;
            }
        }
    }
}
