from pathlib import Path
import hashlib
import urllib.request
import zipfile

name = "Godot_v4.7.2-stable_linux.x86_64.zip"
url = "https://github.com/godotengine/godot/releases/download/4.7.2-stable/" + name
expected = "cadd3204e728a35d3f13adb7fd0d7902636b79f6b95c40c265eb73b6c35329e4"
cache = Path.home() / ".cache/reverse-plan-engine"
cache.mkdir(parents=True, exist_ok=True)
archive = cache / name
urllib.request.urlretrieve(url, archive)
with archive.open("rb") as stream:
    actual = hashlib.file_digest(stream, "sha256").hexdigest()
if actual != expected:
    archive.unlink(missing_ok=True)
    raise SystemExit("Godot SHA256 mismatch")
with zipfile.ZipFile(archive) as z:
    binary = cache / name[:-4]
    binary.write_bytes(z.read(name[:-4]))
    binary.chmod(0o755)
print(binary)
