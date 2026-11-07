#!/bin/bash
# Builds build/CrawlFurther.Core.dll (the library), then build/CrawlFurther.dll (the content mod) and
# build/ExampleGod.dll (examples/ExampleGod, the docs' sample mod) against it.
# References come from lib/ (the game's and BepInEx's own DLLs; never committed). OUT_DIR=... writes both DLLs
# somewhere else (private builds); the default is build/.
set -e
cd "$(dirname "$0")"
L=lib
OUT_DIR=${OUT_DIR:-build}
mkdir -p "$OUT_DIR"
# the C# compiler: Roslyn's csc.dll from a .NET SDK (CSC=... picks another, for example "mcs" or a csc.exe path)
if [ -z "$CSC" ]; then
  CSC_DLL=$(ls -d /usr/lib/dotnet/sdk/*/Roslyn/bincore/csc.dll /usr/share/dotnet/sdk/*/Roslyn/bincore/csc.dll \
            "$HOME"/.dotnet/sdk/*/Roslyn/bincore/csc.dll 2>/dev/null | sort -V | tail -1)
  [ -n "$CSC_DLL" ] || { echo "no .NET SDK found: install one, or set CSC to a C# compiler"; exit 1; }
  CSC="dotnet $CSC_DLL"
fi
FLAGS="-nologo -noconfig -nostdlib+ -target:library -langversion:7.3 -optimize+ -debug- -nowarn:CS1701,CS1702"
REFS="-r:$L/mscorlib.dll -r:$L/System.dll -r:$L/System.Core.dll -r:$L/UnityEngine.dll -r:$L/UnityEngine.UI.dll
      -r:$L/Assembly-CSharp.dll -r:$L/Assembly-CSharp-firstpass.dll -r:$L/ex2D.Runtime.dll
      -r:$L/BepInEx.dll -r:$L/0Harmony.dll"
# sorted, so both assemblies list their types (and so apply their Harmony patches) in the same order on every machine
sources() { find "$1" -name "*.cs" -not -path "*/obj/*" -not -path "*/bin/*" | LC_ALL=C sort; }

$CSC $FLAGS $REFS -out:"$OUT_DIR/CrawlFurther.Core.dll" $(sources src/CrawlFurther.Core)
$CSC $FLAGS $REFS -r:"$OUT_DIR/CrawlFurther.Core.dll" -out:"$OUT_DIR/CrawlFurther.dll" $(sources src/CrawlFurther)
$CSC $FLAGS $REFS -r:"$OUT_DIR/CrawlFurther.Core.dll" -out:"$OUT_DIR/ExampleGod.dll" $(sources examples/ExampleGod)
ls -la "$OUT_DIR/CrawlFurther.Core.dll" "$OUT_DIR/CrawlFurther.dll" "$OUT_DIR/ExampleGod.dll"
