# Downloading Ego4D and Ego-Exo4D

**Paper:** https://arxiv.org/abs/XXXX.XXXXX (placeholder) ·
**Dataset:** https://huggingface.co/datasets/ORG/alm-sounding-actions (placeholder)

The benchmark audio is cut from Ego4D and Ego-Exo4D videos, which we cannot
redistribute. This guide explains how to get access to both datasets and how to
download only the files the benchmark needs.

| Goal | Ego4D | Ego-Exo4D | Disk space |
|---|---|---|---|
| Rebuild the released benchmark (`build_benchmark.py`) | 198 `full_scale` videos | 220 takes (ego view) | about 215 GiB |
| Re-run the construction (`construct_benchmark.py`) | annotations + 329 `full_scale` videos | `test` split (ego view) + metadata + annotations | about 480 GiB |

Sizes were measured on our copies of the datasets (Ego4D v2.1); the downloaders
print the exact size before starting. The commands below are for version 1.7.3
of the `ego4d` package.

## 1. Request access

Ego4D and Ego-Exo4D are free for research, but each has its own license
agreement. Follow the instructions at <https://ego4d-data.org/docs/start-here/>
(Ego4D) and <https://docs.ego-exo4d-data.org/> (Ego-Exo4D) to sign them. Once a
request is approved, you receive by email an AWS access key ID and secret
access key for that dataset. Approval is not immediate, so request access early.

## 2. Install the downloaders and store the credentials

The official downloaders come with the `ego4d` Python package, which is already
in this repository's environment (`environment.yml`):

```bash
pip install ego4d        # provides the `ego4d` and `egoexo` commands
```

Both tools read the credentials from the standard AWS files. Store the two key
pairs as two named profiles in `~/.aws/credentials`:

```ini
[ego4d]
aws_access_key_id = <Ego4D access key id>
aws_secret_access_key = <Ego4D secret access key>

[egoexo]
aws_access_key_id = <Ego-Exo4D access key id>
aws_secret_access_key = <Ego-Exo4D secret access key>
```

You can also write them with the AWS CLI (`pip install awscli`):
`aws configure --profile ego4d` and `aws configure --profile egoexo`.

Select the profile with `--aws_profile_name` for `ego4d` and with
`--s3_profile` for `egoexo`; both default to the `default` profile.

## 3. Download the sources of the benchmark

List the videos and takes used by the benchmark:

```bash
python scripts/list_source_videos.py --out-dir downloads/
# -> downloads/ego4d_video_uids.txt  (198 Ego4D video uids)
# -> downloads/egoexo4d_take_uids.txt (220 Ego-Exo4D take uids)
```

**Ego4D** (about 135 GiB):

```bash
ego4d --output_directory /data/ego4d \
      --datasets full_scale \
      --video_uid_file downloads/ego4d_video_uids.txt \
      --aws_profile_name ego4d
```

The videos are written to `/data/ego4d/v2/full_scale/<video_uid>.mp4`, along with
the metadata file `/data/ego4d/ego4d.json`.

**Ego-Exo4D** (about 80 GiB):

```bash
egoexo -o /data/egoexo4d \
       --parts takes --views ego \
       --uids $(cat downloads/egoexo4d_take_uids.txt) \
       --s3_profile egoexo
```

The benchmark uses one file per take, `/data/egoexo4d/takes/<take_name>/ego_preview.mp4`,
which carries the audio track. The `takes` part has no option to download only
that file: `--views ego` keeps it, together with the ego-view (Aria) videos and
the `best_exo` preview (`<take_name>/aria_and_*_with_audio.mp4`), and skips
the other exocentric cameras, which would add about 600 GiB.

Both commands print the download size and ask for confirmation (add `-y` to
skip the prompt). If a download is interrupted, run the same command again:
files that are already complete are not downloaded twice.

Then build the benchmark (see the [README](../README.md#rebuilding-the-benchmark)):

```bash
python scripts/build_benchmark.py --ego4d-root /data/ego4d --egoexo4d-root /data/egoexo4d --out benchmark/
```

The script first checks that every source video is present and lists the
missing ones.

## 4. Download the sources of the construction pipeline

The construction starts from the annotations and needs every video of the
Ego4D Moments `val` split and every take of the Ego-Exo4D `test` split.

**Ego4D annotations** (about 8 GiB; the pipeline reads
`v2/annotations/moments_val.json`):

```bash
ego4d --output_directory /data/ego4d --datasets annotations --aws_profile_name ego4d
```

**Ego4D videos** (329 videos, about 205 GiB, estimated from their duration):

```bash
python scripts/list_source_videos.py --out-dir downloads/ --construction --ego4d-root /data/ego4d
ego4d --output_directory /data/ego4d --datasets full_scale \
      --video_uid_file downloads/ego4d_moments_val_video_uids.txt --aws_profile_name ego4d
```

96 of these videos have no audio track. They cannot be identified before
downloading (`ego4d.json` lists an audio codec for all of them); the pipeline
skips them.

**Ego-Exo4D** (1,121 takes, about 265 GiB: `takes.json` from the `metadata` part,
`annotations/splits.json` from the `annotations` part, and the ego-view videos):

```bash
egoexo -o /data/egoexo4d \
       --parts metadata annotations takes --views ego --splits test \
       --s3_profile egoexo
```

## Expected layout

```text
/data/ego4d/                      # --ego4d-root
├── ego4d.json
└── v2/
    ├── annotations/moments_val.json          (construction only)
    └── full_scale/<video_uid>.mp4
/data/egoexo4d/                   # --egoexo4d-root
├── takes.json                                (construction only)
├── annotations/splits.json                   (construction only)
└── takes/<take_name>/ego_preview.mp4
```

## Using a copy you already have

You can point `--ego4d-root` and `--egoexo4d-root` to existing copies, as long as
they contain the same files:

- **Ego4D**: the `full_scale` videos. The benchmark timestamps are positions in
  the full videos, so `clips` or other derived versions cannot be used.
- **Ego-Exo4D**: `ego_preview.mp4` of each take. The benchmark audio was cut
  from this file; the other videos of a take have no audio track or were not
  used.

If your copy is organised differently, create a folder of symbolic links with
the layout above, for example:

```bash
mkdir -p /data/ego4d/v2/full_scale
while read uid; do
  ln -s /my/ego4d/videos/$uid.mp4 /data/ego4d/v2/full_scale/$uid.mp4
done < downloads/ego4d_video_uids.txt
```

## Troubleshooting

- **`403 Forbidden`, or "could not get manifests for all parts".** The
  credentials are missing, have expired, or the wrong profile is used. Check
  the profile name (`--aws_profile_name` / `--s3_profile`) and ask for new
  credentials through the license process if needed.
- **Missing videos reported by `build_benchmark.py`.** A download did not
  complete; run the download command again.
- **Disk space.** The downloaders only write to the output directory; check
  that it has room for the sizes above before starting.
