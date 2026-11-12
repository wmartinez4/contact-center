#!/usr/bin/env python3
"""Generate the demo prompts with ElevenLabs, convert them to Connect's format and import them.

    AWS_PROFILE=<profile> CONNECT_INSTANCE_ID=<id> DEMO_PREFIX=demo python3 build_prompts.py [--voice Sarah] [--dry-run]

Needs ELEVENLABS_API_KEY in the project .env (poc/../.env). Audio is cached in poc/prompts/ so a text is only
generated once (the free plan has 10,000 characters). Connect wants .wav, 8 kHz, mono, u-law.
Only voices that the plan allows through the API work: on the free plan that means the standard (premade) voices.
"""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request

import boto3

from prompts_spec import all_prompts

HERE = os.path.dirname(os.path.abspath(__file__))
POC = os.path.abspath(os.path.join(HERE, "..", ".."))
ROOT = os.path.abspath(os.path.join(POC, ".."))
CACHE = os.path.join(POC, "prompts")
REGION = os.environ.get("AWS_REGION", "us-east-1")
IID = os.environ.get("CONNECT_INSTANCE_ID", "")
PREFIX = os.environ.get("DEMO_PREFIX", "demo")

ap = argparse.ArgumentParser()
ap.add_argument("--voice", default="Sarah")
ap.add_argument("--dry-run", action="store_true")
ap.add_argument("--retrim", action="store_true", help="trim silence from the cached audio again (no new generation)")
args = ap.parse_args()

env = {}
for line in open(os.path.join(ROOT, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
KEY = env.get("ELEVENLABS_API_KEY", "")
assert KEY, "ELEVENLABS_API_KEY missing in .env"


def el(path, body=None):
    req = urllib.request.Request("https://api.elevenlabs.io" + path, data=json.dumps(body).encode() if body else None,
                                 headers={"xi-api-key": KEY, "Content-Type": "application/json"})
    return urllib.request.urlopen(req, timeout=90).read()


TRIM = ("silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,areverse,"
        "silenceremove=start_periods=1:start_threshold=-50dB:start_silence=0.05,areverse")


# the first audio of a call can lose its first moments while the media path opens: give it a lead-in of silence (seconds)
# Silence before the first prompt a caller hears, so the start is not lost while the call audio connects
LEAD = {"notice_en": 1.2, "notice_es": 1.2}


def trim(path, key=None):
    """Cut the silence at the start and at the end, so prompts do not leave dead air before the next one."""
    tmp = path + ".tmp.wav"
    af = TRIM + (f",adelay={int(LEAD[key] * 1000)}" if key in LEAD else "")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", path, "-af", af, "-ar", "8000", "-ac", "1", "-c:a", "pcm_mulaw", tmp], check=True)
    os.replace(tmp, path)


os.makedirs(CACHE, exist_ok=True)
prompts = all_prompts()
if args.retrim:
    done = 0
    for k in prompts:
        p = os.path.join(CACHE, f"{k}.wav")
        if os.path.exists(p):
            trim(p, k)
            done += 1
    print("trimmed", done, "cached prompts")
todo = {k: t for k, t in prompts.items() if not os.path.exists(os.path.join(CACHE, f"{k}.wav"))}
need = sum(len(t) for t in todo.values())
sub = json.loads(el("/v1/user/subscription"))
left = sub["character_limit"] - sub["character_count"]
print(f"prompts: {len(prompts)} | to generate: {len(todo)} | characters needed: {need} | left: {left}")
if args.dry_run:
    sys.exit(0)
if need > left - 100:
    sys.exit("not enough ElevenLabs characters left; aborting before generating anything")

voice_id = next(v["voice_id"] for v in json.loads(el("/v1/voices"))["voices"] if v["name"].split(" -")[0].strip() == args.voice)
for k, text in todo.items():
    mp3 = os.path.join(CACHE, f"{k}.mp3")
    audio = el(f"/v1/text-to-speech/{voice_id}?output_format=mp3_44100_128", {"text": text, "model_id": "eleven_multilingual_v2"})
    open(mp3, "wb").write(audio)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", "8000", "-ac", "1", "-c:a", "pcm_mulaw", os.path.join(CACHE, f"{k}.wav")], check=True)
    os.remove(mp3)
    trim(os.path.join(CACHE, f"{k}.wav"), k)
    print("generated", k)

if not IID:
    sys.exit("CONNECT_INSTANCE_ID not set: audio generated, nothing imported")
sess = boto3.Session(region_name=REGION)
account = sess.client("sts").get_caller_identity()["Account"]
s3, connect = sess.client("s3"), sess.client("connect")
bucket = f"amazon-connect-{PREFIX}-recordings-{account}"
existing = {}
tok = None
while True:
    r = connect.list_prompts(InstanceId=IID, **({"NextToken": tok} if tok else {}))
    existing.update({p["Name"]: p["Id"] for p in r["PromptSummaryList"]})
    tok = r.get("NextToken")
    if not tok:
        break
for k in prompts:
    name = f"{PREFIX}-p-{k}"
    key = f"{PREFIX}/prompts/{k}.wav"
    s3.upload_file(os.path.join(CACHE, f"{k}.wav"), bucket, key)
    uri = f"s3://{bucket}/{key}"
    if name in existing:
        connect.update_prompt(InstanceId=IID, PromptId=existing[name], S3Uri=uri)
        print("updated prompt", name)
    else:
        connect.create_prompt(InstanceId=IID, Name=name, S3Uri=uri)
        print("created prompt", name)
print("done")
