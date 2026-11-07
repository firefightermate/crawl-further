"""Find C# sources by file name: the library (src/CrawlFurther.Core) and the content mod (src/CrawlFurther) keep their
files in per-area folders, so the art tools look files up by name instead of hard-coding folders."""
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def src_file(name):
    """The one file called `name` (e.g. "WeaponPack.cs") anywhere under src/."""
    hits = glob.glob(os.path.join(ROOT, "src", "**", name), recursive=True)
    if len(hits) != 1:
        raise SystemExit("%d files named %s under src/" % (len(hits), name))
    return hits[0]


def pack_files():
    """Every *Pack.cs of the content mod, in file-name order."""
    return sorted(glob.glob(os.path.join(ROOT, "src", "CrawlFurther", "**", "*Pack.cs"), recursive=True),
                  key=os.path.basename)
