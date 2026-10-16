using System.Collections;
using System.Diagnostics;
using System.IO;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.TestTools;
using Debug = UnityEngine.Debug;

namespace AWDK.AgentTools.Tests
{
    public class JobAndPerfTests
    {
        static IEnumerator Busy(AgentJob job, int units, double msPerUnit)
        {
            for (int i = 0; i < units; i++)
            {
                var sw = Stopwatch.StartNew();
                while (sw.Elapsed.TotalMilliseconds < msPerUnit) { }
                job.Progress = i + "/" + units;
                yield return null;
            }
            job.Result = "DONE";
        }

        [UnityTest]
        public IEnumerator JobRunner_SlicesWorkOnEditorUpdate()
        {
            JobRunner.Start("TestBusy", j => Busy(j, 100, 10));
            StringAssert.StartsWith("STATE=running", JobRunner.Get("TestBusy").StatusText());
            var sw = Stopwatch.StartNew();
            while (!JobRunner.Get("TestBusy").Done && sw.Elapsed.TotalSeconds < 30) yield return null;
            var job = JobRunner.Get("TestBusy");
            Assert.AreEqual("DONE", job.Result);
            Assert.Greater(job.Slices, 3);
            Assert.Less(job.MaxSliceMs, JobRunner.SliceBudgetMs + 50);
        }

        [Test]
        public void JobRunner_ReportsExceptionsAndCancel()
        {
            var bad = JobRunner.Create("TestThrow", j => Throwing());
            StringAssert.StartsWith("ERROR TestThrow failed", JobRunner.RunBlocking(bad, 5));

            JobRunner.Start("TestCancel", j => Busy(j, 1000, 5));
            StringAssert.StartsWith("ABORTED TestCancel: cancelled", JobRunner.Cancel("TestCancel"));
            StringAssert.StartsWith("STATE=idle", JobRunner.Status("NeverStarted"));
        }

        static IEnumerator Throwing()
        {
            yield return null;
            throw new System.InvalidOperationException("boom");
        }

        [Test]
        public void PerfSample_RequiresPlayMode()
        {
            StringAssert.StartsWith("ERROR PerfSample needs play mode", PerfSample.Start("Temp/AgentToolsTests/perf.json"));
        }

        [UnityTest]
        public IEnumerator PerfSample_WritesJsonInPlayMode()
        {
            TestScene.Fresh();
            var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.name = "Heavy";
            Object.DestroyImmediate(cube.GetComponent<Collider>());
            yield return new EnterPlayMode();

            var outJson = Path.GetFullPath("Temp/AgentToolsTests/perf.json");
            if (File.Exists(outJson)) File.Delete(outJson);
            var started = PerfSample.Start(outJson, 0.2f, 5, 30, "Heavy");
            StringAssert.StartsWith("STARTED", started);
            var sw = Stopwatch.StartNew();
            string status = PerfSample.Status();
            while (!status.EndsWith("COMPLETE") && !status.StartsWith("ERROR") && sw.Elapsed.TotalSeconds < 60)
            {
                yield return null;
                status = PerfSample.Status();
            }
            bool rendererBack = GameObject.Find("Heavy").GetComponent<Renderer>().enabled;
            yield return new ExitPlayMode();

            Debug.Log("[PerfSample]\n" + status);
            StringAssert.EndsWith("COMPLETE", status);
            StringAssert.Contains("disabledRenderers=1", status);
            Assert.IsTrue(rendererBack, "disabled renderers are restored after the sample");
            var json = File.ReadAllText(outJson);
            StringAssert.Contains("\"frames\": 30", json);
            StringAssert.Contains("\"cpuFrameMs\": {\"mean\": ", json);
        }
    }
}
