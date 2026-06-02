# Releasing a CustomPiOS distro on unofficialpi.org

How to publish a CustomPiOS-based distro image (FullPageOS, OctoPi, …) so it is
downloadable and shows up in Raspberry Pi Imager. This repo hosts the images and
**generates** the rpi-imager JSON from per-image snippet files; it does not build
the images (CustomPiOS CI does that).

## The four surfaces that must agree

A release is done only when the **same zip** is reachable and hash-matched from:

1. **GitHub Issue** — the `<Distro> <version> Status` announcement (links testers click).
2. **GitHub tag/release** — `git tag <version>` on the CI-verified commit.
3. **unofficialpi.org** — the hosted `.zip` + `.zip.md5` under `/Distros/<Distro>/…`.
4. **rpi-imager JSON** — `rpi-imager/rpi-imager-<distro>.json`, generated here.

## How the imager JSON is built (this repo)

`src/create_rpi-imager-distro.py <Distro>` connects over SFTP and scans these
folders, newest-first, taking the latest N `*.json` **snippet** files in each:

| Folder | Channel | Name suffix |
|--------|---------|-------------|
| `/Distros/<Distro>` | Stable (2) | `(Stable)` |
| `/Distros/<Distro>/nightly` | Nightly armhf (2) | `(Nightly)` |
| `/Distros/<Distro>/nightly-arm64` | Nightly arm64 (2) | `(Nightly) 64-bit` |
| `/Distros/<Distro>/rc` | RC (2) | `(RC)` |

It writes the assembled list to `/rpi-imager/rpi-imager-<distro>.json`.
arm64 images are auto-detected from `arm64` in the snippet `url` (they gain the
`64-bit` name and the arm64-only device list). A single `rc` folder therefore
holds both arches; the newest 2 snippets win, so a new RC supersedes the old.

### Snippet file format

Each image has a sibling `<builddate>_rpi-imager-snipplet.json` in its folder
(for `rc`, use an arch-distinct name so the two arches don't collide, e.g.
`<builddate>_armhf_rpi-imager-snipplet.json`). The generator builds the final
download URL as `web.url + folder + "/" + <builddate> + "_" + snippet.url`, so
`snippet.url` is the zip basename **without** the `<builddate>_` prefix.

```json
{
  "name": "FullpageOS",
  "description": "A raspberrypi distro to display a full page browser on boot",
  "url": "<rpiosdate>-fullpageos-trixie-<arch>-lite-<version>.zip",
  "icon": "https://raw.githubusercontent.com/guysoft/FullPageOS/devel/media/rpi-imager-FullPageOS.png",
  "release_date": "<builddate>",
  "extract_sha256": "<sha256 of the .img>",
  "extract_size": <bytes of the .img>,
  "image_download_size": <bytes of the .zip>,
  "image_download_sha256": "<sha256 of the .zip>"
}
```

## Naming convention

```
zip:          <builddate>_<rpiosdate>-<distro>-<debian>-<arch>-lite-<version>.zip
.img inside:  <rpiosdate>-<distro>-<debian>-<arch>-lite-<version>.img
snippet:      <builddate>_[<arch>_]rpi-imager-snipplet.json
```

`<builddate>` = day published, `<rpiosdate>` = the Raspberry Pi OS base date.
Example (FullPageOS 1.0.0-rc1):
`2026-05-28_2026-04-21-fullpageos-trixie-armhf-lite-1.0.0-rc1.zip`.

## Release workflow

```
- [ ] 1. CI is green for the commit (build armhf+arm64 + e2e-test). Record run id.
- [ ] 2. Tag it on GitHub (lightweight, on devel HEAD): see custompios-release skill.
- [ ] 3. Build zips from the verified .img files + write .md5 sidecars.
- [ ] 4. Write a snippet json per arch (hashes/sizes from step 3).
- [ ] 5. Upload zip + .md5 + snippet to /Distros/<Distro>/rc (or nightly/, or root for stable).
- [ ] 6. Regenerate the imager JSON.
- [ ] 7. Verify all four surfaces resolve to the same zip + hashes.
- [ ] 8. File / update the GitHub status issue with the download links.
```

### 3. Build zips + md5 (on the build host)

Hardlink the verified image to its convention name (free, same filesystem) and
zip to real disk, then hash:

```bash
ln -f <ci-image>.img /tmp/build/<rpiosdate>-<distro>-trixie-armhf-lite-<version>.img
( cd /tmp/build && zip -1 /out/<builddate>_<rpiosdate>-<distro>-trixie-armhf-lite-<version>.zip \
    <rpiosdate>-<distro>-trixie-armhf-lite-<version>.img )
( cd /out && md5sum <zip> > <zip>.md5 )
sha256sum /out/<zip>                 # -> image_download_sha256
stat -c%s /out/<zip>                 # -> image_download_size
sha256sum <ci-image>.img             # -> extract_sha256
stat -c%s  <ci-image>.img            # -> extract_size
```

### 5. Upload (uses this repo's tooling; reads src/config.ini)

```bash
python3 src/upload_ftp.py /out/<builddate>_..._armhf...zip      /Distros/<Distro>/rc
python3 src/upload_ftp.py /out/<builddate>_..._armhf...zip.md5  /Distros/<Distro>/rc
python3 src/upload_ftp.py /out/<builddate>_armhf_rpi-imager-snipplet.json /Distros/<Distro>/rc
# repeat for arm64
```

`upload_ftp.py <file> <remote_dir>` uploads to a temp path then renames into
`<remote_dir>`, creating the folder if missing.

### 6. Regenerate the imager JSON (reads src/config.yaml)

```bash
python3 src/create_rpi-imager-distro.py <Distro>
```

### 7. Verify (read-only)

```bash
# imager entry resolves + hashes line up
curl -fsSL https://unofficialpi.org/rpi-imager/rpi-imager-<distro>.json \
  | jq '.os_list[] | select(.name|test("RC")) | {name,url,image_download_sha256,extract_sha256}'
curl -fsSLI "<that url>" | head -1            # expect HTTP 200
curl -fsSL  "<that url>.md5"                   # matches image_download (md5 sidecar)
```

Assert: imager `url` is 200; `image_download_sha256` == sha256 of that zip;
`extract_sha256` == sha256 of the `.img` inside; sizes match; the Issue and the
imager JSON name the same version.

## Channels

- **Stable**: upload zip+md5+snippet to `/Distros/<Distro>/` (root). For OctoPi the
  generator keeps the filename as-is; others get the `<builddate>_` prefix.
- **Nightly**: `/Distros/<Distro>/nightly` (armhf) and `/nightly-arm64` (arm64).
- **RC**: `/Distros/<Distro>/rc` (both arches, arch-distinct snippet names).

## Notes

- `src/config.ini` (used by `upload_ftp.py`) and `src/config.yaml` (used by the
  generator) hold SFTP credentials and are gitignored. Never commit them.
- The GitHub-side steps (tag, status issue, contributor thanks, CI verification)
  are documented in the `custompios-release` agent skill.
