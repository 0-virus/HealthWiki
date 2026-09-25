"""Run with unittest or directly. Generated videos stay in a temporary directory."""
import json
import subprocess
import sys
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
import analyze_video as a


class AnalysisChecks(unittest.TestCase):
    def test_time_windows_cover_every_frame_once(self):
        times=2.1+np.arange(69)/30
        rows=a.windows(times,times[0],times[-1],1)
        self.assertEqual([len(r["frames_zero_based"]) for r in rows],[30,30,9])
        self.assertEqual(sum((r["frames_zero_based"] for r in rows),[]),list(range(69)))
        self.assertAlmostEqual(rows[-1]["end_s"],times[-1])
        low=a.windows(np.array([0,.2,.4]),0,.4,.1)
        self.assertTrue(any(not r["frames_zero_based"] for r in low))
        self.assertEqual(sum((r["frames_zero_based"] for r in low),[]),[0,1,2])

    def test_critical_union_and_frame_selection(self):
        times=np.arange(91)/30
        cfg={"play":{"start_frame":0,"end_frame":90},"critical":[
            {"start_s":1,"end_s":1.4,"reason":"memo","origin":"memo"},
            {"start_s":1.2,"end_s":1.7,"reason":"reach","origin":"crux"}]}
        plan=a.segment_plan(cfg,times)
        self.assertEqual(len(plan["critical_merged"]),1)
        self.assertEqual(len(plan["critical_tenth_second"]),7)
        indices=sum((r["frames_zero_based"] for r in plan["critical_tenth_second"]),[])
        self.assertEqual(indices,list(range(30,52)))

    def test_com_translation(self):
        lm=np.zeros((33,3));lm[:,:2]=[100,200];lm[:,2]=1
        center,q=a.center_of_mass(lm)
        np.testing.assert_allclose(center,[100,200]);self.assertAlmostEqual(q,1)
        lm[:,:2]+=[20,-30]
        np.testing.assert_allclose(a.center_of_mass(lm)[0],[120,170])

    def test_confirmation_is_required(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/"request.json";path.write_text(json.dumps({"player":{"confirmed":False}}),encoding="utf-8")
            with self.assertRaisesRegex(ValueError,"confirmation"):a.read_manifest(path)

    def test_render_with_irregular_timestamps_audio_and_native_review_frames(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/"synthetic.mp4";ticks=[0,1,2,4,5,6,8,9,10,11,13,14,15,16,18,19,20,21,22,24]
            with av.open(str(source),"w") as c:
                v=c.add_stream("libx264",rate=30);v.width=320;v.height=480;v.pix_fmt="yuv420p"
                audio=c.add_stream("aac",rate=48000);audio.layout="mono"
                for i,tick in enumerate(ticks):
                    raw=np.full((480,320,3),40,np.uint8);raw[250:270,50+i*5:70+i*5]=150
                    f=av.VideoFrame.from_ndarray(raw,format="rgb24");f.pts=tick;f.time_base=Fraction(1,30)
                    for packet in v.encode(f):c.mux(packet)
                for packet in v.encode():c.mux(packet)
                for i in range(40):
                    f=av.AudioFrame.from_ndarray(np.zeros((1,1024),np.float32),format="fltp",layout="mono")
                    f.sample_rate=48000;f.pts=i*1024;f.time_base=Fraction(1,48000)
                    for packet in audio.encode(f):c.mux(packet)
                for packet in audio.encode():c.mux(packet)
            times,w,h,rate=a.probe(source)
            cfg={"source":source.name,"source_sha256":a.sha256(source),
                 "player":{"confirmed":True,"description":"synthetic test fixture, not a person",
                           "confirmation_text":"unit-test fixture only","confirmed_at":"test"},
                 "roi":[0,0,1,1],"camera_note":"synthetic stationary camera",
                 "play":{"start_frame":2,"end_frame":18,"outcome":"unresolved",
                         "start_evidence":"synthetic boundary","end_evidence":"synthetic boundary"},
                 "critical":[{"start_s":.2,"end_s":.5,"origin":"crux","reason":"fixture"}]}
            manifest=root/"run.json";manifest.write_text(json.dumps(cfg),encoding="utf-8")
            data=np.zeros((len(times),33,3),np.float32);data[:,:,2]=1
            for i in range(len(times)):data[i,:,:2]=[80+i*5,250]
            cache=root/"cache.npz";np.savez_compressed(cache,landmarks=data,pts_seconds=times,source_sha256=cfg["source_sha256"])
            out=root/"output"
            proc=subprocess.run([sys.executable,str(Path(a.__file__)),"--manifest",str(manifest),"--out",str(out),"--pose-cache",str(cache)],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)
            check=json.loads((out/"validation.json").read_text(encoding="utf-8"))
            self.assertTrue(check["pts_preserved"]);self.assertTrue(check["audio_packets_preserved"])
            self.assertEqual(check["decoded_frames"],20)
            centers=json.loads((out/"centers.json").read_text(encoding="utf-8"))
            with av.open(str(out/"overlay.mp4")) as c:
                frames=[f.to_ndarray(format="bgr24") for f in c.decode(video=0)]
            # Old center locations return to the background; only the current point remains.
            old_center=frames[18][248:253,88:93].astype(int)
            self.assertLess(int(np.abs(old_center-40).max()),8)
            self.assertGreater(int(frames[18][250,170,1]),150)
            self.assertIsNone(centers[1]["com_xy"])
            np.testing.assert_allclose(centers[18]["com_xy"],[170,250],atol=.001)
            self.assertIsNone(centers[19]["com_xy"])
            self.assertTrue(list((out/"review").glob("critical-*.jpg")))
            again=subprocess.run([sys.executable,str(Path(a.__file__)),"--manifest",str(manifest),"--out",str(out),"--pose-cache",str(cache)],capture_output=True,text=True)
            self.assertNotEqual(again.returncode,0);self.assertIn("already exists",again.stderr)


if __name__=="__main__":unittest.main()
