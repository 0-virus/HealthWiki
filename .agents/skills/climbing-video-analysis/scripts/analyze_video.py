"""Local pose and current COM overlay with timestamp-based review windows.

One user-confirmed attempt per manifest. Natural-language analysis is written by
the agent after reviewing the generated video and contact sheets, not by this code.
"""
import argparse
import hashlib
import json
import math
from importlib.metadata import version
from decimal import Decimal
from pathlib import Path

import av
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

POINTS = {"LH": (15, 17, 19), "LE": (13,), "RH": (16, 18, 20), "RE": (14,),
          "LF": (29, 31), "LK": (25,), "RF": (30, 32), "RK": (26,)}
CHAINS = (("LH", "LE"), ("RH", "RE"), ("LF", "LK"), ("RF", "RK"))
LEFT, RIGHT, CENTER, GRAY = (255, 220, 30), (170, 80, 255), (30, 235, 255), (180, 180, 180)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def read_manifest(path):
    cfg = json.loads(path.read_text(encoding="utf-8"))
    player = cfg.get("player", {})
    if player.get("confirmed") is not True or not all(
        isinstance(player.get(k), str) and player[k].strip()
        for k in ("description", "confirmation_text", "confirmed_at")
    ):
        raise ValueError("Explicit user confirmation of this player/attempt is required before processing.")
    source = (path.parent / cfg["source"]).resolve()
    if not source.is_file() or sha256(source) != cfg.get("source_sha256"):
        raise ValueError("Source missing or hash mismatch; recheck the confirmed video.")
    roi = cfg.get("roi")
    if not isinstance(roi, list) or len(roi) != 4 or not all(
        isinstance(v, (int, float)) and math.isfinite(v) for v in roi
    ) or not (0 <= roi[0] < roi[2] <= 1 and 0 <= roi[1] < roi[3] <= 1):
        raise ValueError("roi must be normalized [left, top, right, bottom] within the image.")
    play = cfg.get("play", {})
    if play.get("outcome") not in ("cleared", "failed", "unresolved"):
        raise ValueError("play.outcome must be cleared, failed, or unresolved.")
    if not all(isinstance(play.get(k), str) and play[k].strip()
               for k in ("start_evidence", "end_evidence")):
        raise ValueError("Document observed start/end evidence, including unresolved boundaries.")
    if not isinstance(cfg.get("camera_note"), str) or not cfg["camera_note"].strip():
        raise ValueError("camera_note must describe camera movement and screen-space limitations.")
    return cfg, source


def probe(source):
    times, sizes, rotations = [], set(), set()
    with av.open(str(source)) as c:
        if len(c.streams.video) != 1:
            raise ValueError("Select one video stream in a preserved derivative before processing.")
        s = c.streams.video[0]
        for f in c.decode(video=0):
            if f.time is None: raise ValueError("A video frame has no timestamp.")
            times.append(float(f.time)); sizes.add((f.width, f.height)); rotations.add(f.rotation)
        rate = s.average_rate
    if not times or rate is None or len(sizes) != 1 or rotations != {0}:
        raise ValueError("Empty video, unknown rate, changing dimensions or rotation: normalize a derivative first.")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("Non-increasing frame timestamps are not supported; preserve and normalize a derivative.")
    w, h = next(iter(sizes))
    if w % 2 or h % 2: raise ValueError("H.264 yuv420p requires even dimensions; pad a preserved derivative.")
    return np.array(times), w, h, rate


def windows(times, start, end, step):
    """Half-open windows, except the final window includes the endpoint frame."""
    a, stop, step = Decimal(str(start)), Decimal(str(end)), Decimal(str(step))
    if step <= 0 or a >= stop: raise ValueError("Window endpoints/step are invalid.")
    result = []
    while a < stop:
        b = min(a + step, stop); last = b == stop
        lo = int(np.searchsorted(times, float(a) - 1e-8, side="left"))
        hi = int(np.searchsorted(times, float(b) + (1e-8 if last else -1e-8), side="right" if last else "left"))
        ids = list(range(lo, hi))
        result.append({"start_s": float(a), "end_s": float(b), "end_inclusive": last,
                       "frames_zero_based": ids, "observation": "unreviewed" if ids else "no_source_frame"})
        a = b
    return result


def segment_plan(cfg, times):
    play = cfg["play"]; a, b = play.get("start_frame"), play.get("end_frame")
    if type(a) is not int or type(b) is not int or not (0 <= a < b < len(times)):
        raise ValueError("play frames must be actual zero-based indices with start < end.")
    start, end = float(times[a]), float(times[b])
    critical = []
    for item in cfg.get("critical", []):
        x, y = item["start_s"], item["end_s"]
        if not (math.isfinite(x) and math.isfinite(y) and start <= x < y <= end):
            raise ValueError("Critical interval must lie inside the observed play interval.")
        if not item.get("reason") or item.get("origin") not in ("memo", "crux", "both"):
            raise ValueError("Each critical interval needs a reason and origin (memo/crux/both).")
        critical.append({"start_s": x, "end_s": y, "reasons": [item["reason"]], "origins": [item["origin"]]})
    merged = []
    for item in sorted(critical, key=lambda x: x["start_s"]):
        if merged and item["start_s"] <= merged[-1]["end_s"]:
            merged[-1]["end_s"] = max(merged[-1]["end_s"], item["end_s"])
            merged[-1]["reasons"] += item["reasons"]; merged[-1]["origins"] += item["origins"]
        else: merged.append(item)
    coarse = windows(times, start, end, 1)
    fine = []
    for group, item in enumerate(merged):
        for row in windows(times, item["start_s"], item["end_s"], .1):
            row.update(group=group, reasons=item["reasons"], origins=item["origins"]); fine.append(row)
    for prefix, rows in (("S", coarse), ("C", fine)):
        for i, row in enumerate(rows, 1):
            row["id"] = f"{prefix}{i:03d}"
            ids = row["frames_zero_based"]
            row["review_frames"] = ids if prefix == "C" or len(ids) <= 3 else [ids[0], ids[len(ids)//2], ids[-1]]
    return {"start_s": start, "end_s": end, "one_second": coarse, "critical_tenth_second": fine,
            "critical_merged": merged, "frame_numbering": "zero-based; video labels are one-based"}


def center_of_mass(lm):
    """Reuse the P08 Dempster 12-segment approximation; see execution reference."""
    xy, q = lm[:, :2], lm[:, 2]
    parts = [(0.081, xy[[7, 8]].mean(0), q[[7, 8]].mean()),
             (0.497, xy[[23, 24]].mean(0)*.505 + xy[[11, 12]].mean(0)*.495, q[[11, 12, 23, 24]].min())]
    for sh, el, wr, hip, kn, an, toe in ((11,13,15,23,25,27,31), (12,14,16,24,26,28,32)):
        for m, a, b, f in ((.028,sh,el,.436), (.022,el,wr,.682), (.1,hip,kn,.433),
                            (.0465,kn,an,.433), (.0145,an,toe,.5)):
            parts.append((m, xy[a]*(1-f)+xy[b]*f, min(q[a], q[b])))
    return sum(m*p for m,p,_ in parts), float(sum(m*q for m,_,q in parts))


def roi_pixels(cfg, w, h):
    x0, y0, x1, y1 = cfg["roi"]
    box = (int(x0*w), int(y0*h), int(x1*w), int(y1*h))
    if box[2]-box[0] < 32 or box[3]-box[1] < 32: raise ValueError("ROI too small.")
    return box


def infer(source, model, cfg, times, w, h):
    import mediapipe as mp
    data = np.full((len(times),33,3), np.nan, dtype=np.float32)
    status = ["outside_play"]*len(times)
    x0,y0,x1,y1 = roi_pixels(cfg,w,h)
    options = mp.tasks.vision.PoseLandmarkerOptions(
        base_options=mp.tasks.BaseOptions(model_asset_path=str(model)),
        running_mode=mp.tasks.vision.RunningMode.VIDEO, num_poses=4,
        min_pose_detection_confidence=.3, min_pose_presence_confidence=.3, min_tracking_confidence=.5)
    with av.open(str(source)) as c, mp.tasks.vision.PoseLandmarker.create_from_options(options) as detector:
        for i,f in enumerate(c.decode(video=0)):
            if not cfg["play"]["start_frame"] <= i <= cfg["play"]["end_frame"]: continue
            rgb=np.ascontiguousarray(f.to_ndarray(format="rgb24")[y0:y1,x0:x1])
            result=detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB,data=rgb),round(times[i]*1000))
            # Never pick whichever person happened to be returned first.
            status[i] = "ambiguous" if len(result.pose_landmarks)>1 else "not_detected"
            if len(result.pose_landmarks)==1:
                data[i]=[[x0+p.x*(x1-x0),y0+p.y*(y1-y0),min(p.visibility,p.presence)] for p in result.pose_landmarks[0]]
                status[i]="estimated"
            if i%150==0: print(f"inference {i}/{len(times)}",flush=True)
    return data,status


def draw_pose(frame,lm):
    if not np.isfinite(lm).all(): return None,None
    center,q=center_of_mass(lm);h,w=frame.shape[:2];scale=w/1080
    inside=lambda p: np.isfinite(p).all() and 0<=p[0]<w and 0<=p[1]<h
    points={name:(lm[list(ids),:2].mean(0),float(lm[list(ids),2].min())) for name,ids in POINTS.items()}
    for limb,joint in CHAINS:
        color=LEFT if limb.startswith("L") else RIGHT
        a,aq=points[limb];b,bq=points[joint]
        for p,pq,r,rq in ((a,aq,b,bq),(b,bq,center,q)):
            if not (inside(p) and inside(r)):continue
            if min(pq,rq)>=.6:
                cv2.line(frame,tuple(p.astype(int)),tuple(r.astype(int)),color,max(1,round(3*scale)),cv2.LINE_AA)
            else:
                distance=np.linalg.norm(r-p)
                for t in np.arange(0,distance,max(8,16*scale)):
                    u=p+(r-p)*t/max(distance,1);v=p+(r-p)*min(t+max(4,8*scale),distance)/max(distance,1)
                    cv2.line(frame,tuple(u.astype(int)),tuple(v.astype(int)),GRAY,max(1,round(2*scale)),cv2.LINE_AA)
    for name,(p,pq) in points.items():
        if not inside(p):continue
        color=LEFT if name.startswith("L") else RIGHT;pt=tuple(p.astype(int));radius=max(3,round(7*scale))
        cv2.circle(frame,pt,radius+2,(0,0,0),-1,cv2.LINE_AA)
        cv2.circle(frame,pt,radius,color if pq>=.6 else GRAY,-1 if pq>=.6 else 1,cv2.LINE_AA)
        cv2.putText(frame,name,(pt[0]+radius+3,pt[1]-radius),cv2.FONT_HERSHEY_SIMPLEX,max(.35,.5*scale),color,1,cv2.LINE_AA)
    if inside(center):
        pt=tuple(center.astype(int));cv2.circle(frame,pt,max(6,round(12*scale)),(0,0,0),-1,cv2.LINE_AA)
        cv2.circle(frame,pt,max(4,round(9*scale)),CENTER,-1 if q>=.6 else 2,cv2.LINE_AA)
    return center,q


def caption(frame,lines,font):
    image=Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB));draw=ImageDraw.Draw(image,"RGBA")
    size=font.size;pad=max(5,size//2);line_h=round(size*1.4)
    wrapped=[]
    for line in lines:
        current=""
        for word in line.split():
            candidate=f"{current} {word}".strip()
            if current and font.getlength(candidate)>image.width-2*pad:
                wrapped.append(current);current=word
            else:current=candidate
        wrapped.append(current)
    draw.rectangle((0,0,image.width,line_h*len(wrapped)+pad*2),fill=(8,15,25,210))
    for j,line in enumerate(wrapped):draw.text((pad,pad+j*line_h),line,font=font,fill="white")
    return cv2.cvtColor(np.asarray(image),cv2.COLOR_RGB2BGR)


def render(source,out,cfg,times,w,h,rate,data,status,plan,font_path):
    font=ImageFont.truetype(str(font_path),max(13,round(w/42)))
    rows=[];thumbs={};durations={}
    review_rows=plan["one_second"]+plan["critical_tenth_second"]
    wanted={i for row in review_rows for i in row["review_frames"]}
    x0,y0,x1,y1=roi_pixels(cfg,w,h)
    with av.open(str(source)) as src,av.open(str(out/"overlay.mp4"),"w",options={"movflags":"+faststart"}) as dst:
        video=dst.add_stream("libx264",rate=rate);video.width=w;video.height=h;video.pix_fmt="yuv420p"
        video.options={"crf":"19","preset":"veryfast"};video.time_base=src.streams.video[0].time_base
        video.codec_context.time_base=src.streams.video[0].time_base
        audio={s.index:dst.add_stream_from_template(s) for s in src.streams.audio};i=0
        for packet in src.demux():
            if packet.stream.type=="audio":
                if packet.dts is not None:packet.stream=audio[packet.stream.index];dst.mux(packet)
                continue
            if packet.stream.type!="video":continue
            for f in packet.decode():
                raw=f.to_ndarray(format="bgr24");frame=raw.copy();point=quality=None
                active=cfg["play"]["start_frame"]<=i<=cfg["play"]["end_frame"]
                if active:point,quality=draw_pose(frame,data[i])
                lines=[f"Frame {i+1}/{len(times)} | source {times[i]:.3f}s | play {plan['start_s']:.3f}-{plan['end_s']:.3f}s",
                       "Left: cyan | Right: pink | Current COM estimate: yellow",
                       "Gray/hollow: uncertain | 2D estimate, not measured COM or forces",
                       f"Tracking: {status[i]} | screen coordinates: camera motion may affect them"]
                frame=caption(frame,lines,font)
                vf=av.VideoFrame.from_ndarray(frame,format="bgr24");vf.pts=f.pts;vf.time_base=f.time_base;vf.duration=f.duration
                durations[f.pts]=f.duration
                for p in video.encode(vf):p.duration=durations[p.pts];dst.mux(p)
                if i in wanted:
                    thumb=Image.fromarray(cv2.cvtColor(raw[y0:y1,x0:x1],cv2.COLOR_BGR2RGB));thumb.thumbnail((420,420));thumbs[i]=thumb
                rows.append({"frame_zero_based":i,"time_s":float(times[i]),"status":status[i],
                             "com_xy":point.tolist() if point is not None else None,"com_quality":quality})
                if i%150==0:print(f"render {i}/{len(times)}",flush=True)
                i+=1
        for p in video.encode():p.duration=durations[p.pts];dst.mux(p)
        if i!=len(times):raise ValueError("Frame count changed during rendering.")
    write_json(out/"centers.json",rows)
    review=out/"review";review.mkdir()
    # Fine windows include every native frame. Coarse sheets show first/middle/last.
    for scheme,segments in (("one-second",plan["one_second"]),("critical",plan["critical_tenth_second"])):
        tiles=[(row,i) for row in segments for i in row["review_frames"]]
        for start in range(0,len(tiles),9):
            chunk=tiles[start:start+9];sheet=Image.new("RGB",(1260,470*math.ceil(len(chunk)/3)),"#eeeeee")
            d=ImageDraw.Draw(sheet)
            for j,(row,i) in enumerate(chunk):
                x,y=j%3*420,j//3*470;thumb=thumbs[i];sheet.paste(thumb,(x+(420-thumb.width)//2,y+46))
                d.text((x+8,y+5),f"{row['id']} [{row['start_s']:.3f}, {row['end_s']:.3f}]",fill="black")
                d.text((x+8,y+23),f"source {times[i]:.3f}s / frame {i+1}",fill="black")
                row.setdefault("sheets",[])
                filename=f"review/{scheme}-{start//9+1:03d}.jpg"
                if filename not in row["sheets"]:row["sheets"].append(filename)
            sheet.save(out/filename,quality=92)


def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False),encoding="utf-8")


def audio_hash(source):
    hashes={}
    with av.open(str(source)) as c:
        for s in c.streams.audio:hashes[s.index]=hashlib.sha256()
        for p in c.demux():
            if p.stream.index in hashes and p.size:hashes[p.stream.index].update(bytes(p))
    return [h.hexdigest() for h in hashes.values()]


def verify(source,out,times):
    with av.open(str(source)) as c:
        source_duration=float(c.streams.video[0].duration*c.streams.video[0].time_base)
    with av.open(str(out/"overlay.mp4")) as c:
        output_duration=float(c.streams.video[0].duration*c.streams.video[0].time_base)
        actual=np.array([float(f.time) for f in c.decode(video=0)])
    if len(actual)!=len(times) or not np.allclose(actual,times,atol=1e-5,rtol=0):
        raise ValueError("Output frame timestamps/count differ from the source.")
    if audio_hash(source)!=audio_hash(out/"overlay.mp4"):raise ValueError("Copied audio differs.")
    if abs(source_duration-output_duration)>1e-5:raise ValueError("Output video duration differs from source.")
    return {"decoded_frames":len(actual),"pts_preserved":True,"audio_packets_preserved":True,
            "video_duration_s":output_duration,"duration_preserved":True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest",type=Path,required=True);parser.add_argument("--out",type=Path,required=True)
    parser.add_argument("--model",type=Path);parser.add_argument("--font",type=Path)
    parser.add_argument("--pose-cache",type=Path,help="NPZ from this source: landmarks, pts_seconds, source_sha256")
    args=parser.parse_args();cfg,source=read_manifest(args.manifest.resolve())
    times,w,h,rate=probe(source);plan=segment_plan(cfg,times)
    if args.out.exists():raise ValueError("Output directory already exists. Choose a new run directory.")
    font=args.font or Path("C:/Windows/Fonts/malgun.ttf")
    if not font.is_file():raise ValueError("Provide an installed TrueType font via --font.")
    if args.pose_cache:
        with np.load(args.pose_cache,allow_pickle=False) as cache:
            data=cache["landmarks"].copy()
            if str(cache["source_sha256"].item())!=cfg["source_sha256"] or not np.array_equal(cache["pts_seconds"],times):
                raise ValueError("Pose cache is not bound to the same source/timestamps.")
        if data.shape!=(len(times),33,3):raise ValueError("Invalid pose cache shape.")
        data[:cfg["play"]["start_frame"]]=np.nan;data[cfg["play"]["end_frame"]+1:]=np.nan
        status=["estimated" if np.isfinite(row).all() else "not_detected" for row in data]
        for i in range(len(times)):
            if not cfg["play"]["start_frame"]<=i<=cfg["play"]["end_frame"]:status[i]="outside_play"
    else:
        if not args.model or not args.model.is_file():raise ValueError("Provide a local pose model with --model.")
        if len(set(np.rint(times*1000).astype(int)))!=len(times):raise ValueError("Model requires distinct millisecond timestamps.")
        data,status=infer(source,args.model,cfg,times,w,h)
    args.out.mkdir(parents=True)
    write_json(args.out/"manifest.json",dict(cfg,source=str(source)))
    np.savez_compressed(args.out/"pose-data.npz",landmarks=data,pts_seconds=times,source_sha256=cfg["source_sha256"])
    render(source,args.out,cfg,times,w,h,rate,data,status,plan,font)
    write_json(args.out/"segments.json",plan)
    result=verify(source,args.out,times)
    if sha256(source)!=cfg["source_sha256"]:raise ValueError("Source changed during processing.")
    result.update(source_unchanged=True,source_sha256=cfg["source_sha256"],
                  width=w,height=h,nominal_fps=str(rate),detected_frames=status.count("estimated"),
                  model_sha256=sha256(args.model) if args.model and not args.pose_cache else None,
                  libraries={name:version(name) for name in ("av","numpy","Pillow")},
                  pose_backend="reviewed cache" if args.pose_cache else f"mediapipe {version('mediapipe')}",
                  opencv_version=cv2.__version__,
                  review_status="agent must inspect sheets and write every report row")
    write_json(args.out/"validation.json",result)
    print(f"Video and review windows ready: {args.out}. Natural-language report remains to be written.")


if __name__=="__main__":main()
