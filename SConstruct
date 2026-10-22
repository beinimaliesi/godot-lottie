#!/usr/bin/env python

"""
ThorVG-Godot Build Configuration
Builds optimized Lottie animation extension for Godot Engine
"""

import os
import sys
import shutil

env = SConscript("thirdparty/godot-cpp/SConstruct", {"api_version": "4.7"})

# ThorVG software-rendering loops use OpenMP on Linux.
# This is independent of ThorVG's std::thread task scheduler.
if env["platform"] == "linux":
    env.Append(CCFLAGS=["-fopenmp"])
    env.Append(LINKFLAGS=["-fopenmp"])

# Source files
env.Append(CPPPATH=["src/"])
sources = Glob("src/*.cpp")

# ThorVG integration - Platform-specific library handling
env.Append(CPPPATH=["thirdparty/thorvg/inc"])
# TVG_STATIC tells thorvg.h to skip the __declspec(dllimport) decoration on
# its public API symbols, which is required when linking against the static
# libthorvg-1.a / thorvg-1.lib (otherwise MSVC emits LNK4217 and refuses to
# link). Safe on non-Windows -- on Linux/macOS it just makes TVG_API empty,
# which is what those builds already use.
env.Append(CPPDEFINES=["TVG_STATIC"])

# Android: statically link libc++ into the extension so the .so does not
# require libc++_shared.so to be present alongside it at runtime.
if env["platform"] == "android":
    # The NDK provides OpenMP; link its runtime statically for Android.
    env.Append(LINKFLAGS=["-static-libstdc++", "-fopenmp", "-static-openmp"])


# Determine ThorVG library location and linking method.
#
# Android, iOS and Web are cross-compiled and each ABI/target needs its own
# ThorVG build, so we look in arch-specific build directories for those.
# Native desktop builds use the canonical `builddir`.
if env["platform"] == "web":
    thorvg_lib_dir = os.path.join("thirdparty", "thorvg", "build_wasm", "src")
elif env["platform"] == "macos" and env["arch"] == "universal":
    thorvg_lib_dir = os.path.join("thirdparty", "thorvg", "builddir_macos-universal", "src")
    if not os.path.isfile(os.path.join(thorvg_lib_dir, "libthorvg-1.a")):
        print("Missing Universal ThorVG library. Run ./build_thorvg_macos_universal.sh first.")
        Exit(1)
elif env["platform"] == "android":
    arch = env.get("arch", "arm64")
    thorvg_lib_dir = os.path.join("thirdparty", "thorvg", "builddir_android_" + arch, "src")
elif env["platform"] == "ios":
    # iOS has device (arm64) and simulator (arm64 / x86_64) builds.
    # build_thorvg_ios.sh produces:
    #   builddir_ios-arm64/                  (device)
    #   builddir_ios-arm64-simulator/        (Apple Silicon Mac simulator)
    #   builddir_ios-x86_64-simulator/       (Intel Mac simulator)
    arch = env.get("arch", "arm64")
    sim_suffix = "-simulator" if env.get("ios_simulator", False) else ""
    thorvg_lib_dir = os.path.join("thirdparty", "thorvg", "builddir_ios-" + arch + sim_suffix, "src")
else:
    thorvg_lib_dir = os.path.join("thirdparty", "thorvg", "builddir", "src")

if os.path.exists(thorvg_lib_dir):
    env.Append(LIBPATH=[thorvg_lib_dir])

    # Platform-specific library files
    platform_libs = {
        "windows": [
            ("thorvg-1.lib", lambda: env.Append(LIBS=["thorvg-1"])),
            ("libthorvg-1.a", lambda: env.Append(LINKFLAGS=[os.path.join(thorvg_lib_dir, "libthorvg-1.a")]))
        ],
        "linux": [
            ("libthorvg-1.a", lambda: env.Append(LIBS=["thorvg-1"])),
            ("libthorvg-1.so", lambda: env.Append(LIBS=["thorvg-1"]))
        ],
        "macos": [
            ("libthorvg-1.a", lambda: env.Append(LIBS=["thorvg-1"])),
            ("libthorvg-1.dylib", lambda: env.Append(LIBS=["thorvg-1"]))
        ],
        "android": [
            ("libthorvg-1.a", lambda: env.Append(LIBS=["thorvg-1"]))
        ],
        "ios": [
            ("libthorvg-1.a", lambda: env.Append(LIBS=["thorvg-1"]))
        ],
        "web": [
            ("libthorvg-1.a", lambda: env.Append(LIBS=["thorvg-1"]))
        ]
    }
    
    # Try to find and link appropriate library for current platform
    lib_found = False
    if env["platform"] in platform_libs:
        for lib_name, link_func in platform_libs[env["platform"]]:
            lib_path = os.path.join(thorvg_lib_dir, lib_name)
            if os.path.isfile(lib_path):
                link_func()
                lib_found = True
                print("Using ThorVG library: {}".format(lib_name))
                break
    
    if not lib_found:
        print("Warning: ThorVG library not found in {}".format(thorvg_lib_dir))
        print("Available files:", os.listdir(thorvg_lib_dir) if os.path.exists(thorvg_lib_dir) else "Directory not found")
else:
    print("Error: ThorVG build directory not found: {}".format(thorvg_lib_dir))
    print("Please run the appropriate build script first:")
    print("  Windows: build_thorvg.bat") 
    print("  Linux/macOS: ./build_thorvg.sh")

# Platform-specific distribution directory (iOS intermediates stay in build/ios).
bin_dir = os.path.join("demo", "addons", "godot_lottie", "bin", env["platform"])

# Output library name
if env["platform"] == "macos":
    library = env.SharedLibrary(
        os.path.join(bin_dir, "libgodot_lottie.{}.{}.framework/libgodot_lottie.{}.{}").format(
            env["platform"], env["target"], env["platform"], env["target"]
        ),
        source=sources,
    )
elif env["platform"] == "ios":
    # Link dependencies here so unused code is removed before distribution.
    # Godot's iOS exporter packages the dylib for embedding and signing.
    name = "libgodot_lottie{}{}".format(env["suffix"], env["SHLIBSUFFIX"])
    env.Append(LINKFLAGS=["-Wl,-install_name,@rpath/" + name])
    library = env.SharedLibrary(
        os.path.join("build", "ios", name),
        source=sources,
    )
else:
    library = env.SharedLibrary(
        os.path.join(bin_dir, "libgodot_lottie{}{}".format(env["suffix"], env["SHLIBSUFFIX"])),
        source=sources,
    )

Default(library)

# Copy ThorVG runtime DLL on Windows (Linux/macOS use static linking)
if env["platform"] == "windows":
    thorvg_runtime_dir = thorvg_lib_dir if 'thorvg_lib_dir' in locals() else os.path.join("thirdparty", "thorvg", "builddir", "src")
    thorvg_runtime = os.path.join(thorvg_runtime_dir, "thorvg-1.dll")
    dest_dir = bin_dir
    dest_dll = os.path.join(dest_dir, "thorvg-1.dll")

    if os.path.isfile(thorvg_runtime):
        def _copy_thorvg_dll(target, source, env):
            try:
                if not os.path.isdir(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(thorvg_runtime, dest_dll)
                print("Copied ThorVG runtime to {}".format(dest_dll))
            except Exception as e:
                print("Warning: Failed to copy ThorVG runtime DLL: {}".format(e))

        try:
            env.AddPostAction(library, _copy_thorvg_dll)
        except Exception:
            # Fallback: immediate copy
            try:
                if not os.path.isdir(dest_dir):
                    os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(thorvg_runtime, dest_dll)
                print("Copied ThorVG runtime to {} (fallback)".format(dest_dll))
            except Exception as e:
                print("Warning: Could not copy ThorVG runtime: {}".format(e))
