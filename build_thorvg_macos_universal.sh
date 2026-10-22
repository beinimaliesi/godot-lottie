#!/usr/bin/env bash
# Build ThorVG for both macOS architectures, then combine the static libraries.
# MIN_MACOS must match macos_deployment_target when building the extension.
set -euo pipefail
[[ "$(uname -s)" == Darwin ]] || { echo 'macOS host required.' >&2; exit 1; }
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
THORVG_DIR="$SCRIPT_DIR/thirdparty/thorvg"
MIN_MACOS="${MIN_MACOS:-11.0}"
JOBS="${JOBS:-$(sysctl -n hw.ncpu)}"
SDK="$(xcrun --sdk macosx --show-sdk-path)"
CC_PATH="$(xcrun --sdk macosx -f clang)"
CXX_PATH="$(xcrun --sdk macosx -f clang++)"
AR_PATH="$(xcrun --sdk macosx -f ar)"
for tool in meson ninja lipo; do command -v "$tool" >/dev/null; done

for arch in arm64 x86_64; do
    if [[ "$arch" == arm64 ]]; then family=aarch64; threads=false; else family=x86_64; threads=true; fi
    build_dir="$THORVG_DIR/builddir_macos-$arch"
    rm -rf "$build_dir"
    mkdir -p "$build_dir"
    cat > "$build_dir/.cross.ini" <<CROSS
[binaries]
c = '$CC_PATH'
cpp = '$CXX_PATH'
ar = '$AR_PATH'
pkg-config = 'false'
[built-in options]
c_args = ['-arch', '$arch', '-isysroot', '$SDK', '-mmacosx-version-min=$MIN_MACOS']
cpp_args = ['-arch', '$arch', '-isysroot', '$SDK', '-mmacosx-version-min=$MIN_MACOS']
c_link_args = ['-arch', '$arch', '-isysroot', '$SDK', '-mmacosx-version-min=$MIN_MACOS']
cpp_link_args = ['-arch', '$arch', '-isysroot', '$SDK', '-mmacosx-version-min=$MIN_MACOS']
[host_machine]
system = 'darwin'
cpu_family = '$family'
cpu = '$family'
endian = 'little'
CROSS
    meson setup "$build_dir" "$THORVG_DIR" --cross-file "$build_dir/.cross.ini" \
        -Dbuildtype=release -Doptimization=3 -Db_ndebug=true \
        -Ddefault_library=static -Dstatic=true -Dsimd=true -Dthreads="$threads" \
        -Dpartial=true -Dengines=sw -Dloaders=lottie,png -Dextra=lottie_exp \
        -Dbindings=capi -Dtests=false --backend=ninja
    meson compile -C "$build_dir" -j "$JOBS"
done

# Keep the Universal library separate from native build_thorvg.sh outputs.
output="$THORVG_DIR/builddir_macos-universal/src/libthorvg-1.a"
mkdir -p "$(dirname "$output")"
lipo -create "$THORVG_DIR/builddir_macos-arm64/src/libthorvg-1.a" \
    "$THORVG_DIR/builddir_macos-x86_64/src/libthorvg-1.a" -output "$output"
lipo "$output" -verify_arch arm64 x86_64
lipo -info "$output"
