import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent


def main():
    parser = argparse.ArgumentParser(description="Build APK cài thử của Lịch Việt")
    parser.add_argument("--java-home", type=Path)
    parser.add_argument("--sdk", type=Path)
    args = parser.parse_args()
    java_candidates = [args.java_home, Path(os.environ["JAVA_HOME"]) if os.environ.get("JAVA_HOME") else None,
                       ROOT / ".tools" / "jdk"]
    java_candidates.extend(sorted((ROOT / ".tools" / "jdk").glob("jdk*"), reverse=True))
    java_home = next((path for path in java_candidates if path and (path / "bin" / "java.exe").is_file()), None)
    if java_home is None:
        raise SystemExit("Chưa tìm thấy JDK. Dùng --java-home để chỉ thư mục JDK 17.")
    sdk_candidates = [args.sdk, ROOT / ".tools" / "android-sdk"]
    sdk_candidates.extend(Path(os.environ[key]) for key in ("ANDROID_HOME", "ANDROID_SDK_ROOT") if os.environ.get(key))
    sdk = next((path for path in sdk_candidates if path and (path / "platforms" / "android-35" / "android.jar").is_file()), None)
    if sdk is None:
        raise SystemExit("Chưa tìm thấy Android SDK Platform 35. Dùng --sdk để chỉ thư mục SDK.")
    java = str(java_home / "bin" / "java.exe")
    environment = os.environ.copy()
    environment.update(JAVA_HOME=str(java_home), ANDROID_HOME=str(sdk), ANDROID_SDK_ROOT=str(sdk),
                       GRADLE_USER_HOME=str(ROOT / ".tools" / "gradle-cache"))
    output = ROOT / "output" / "android"
    output.mkdir(parents=True, exist_ok=True)
    # Chi tao APK debug de cai thu; khong dung khoa ky cua du an khac.
    command = [java, "-Dorg.gradle.appname=gradlew", "-classpath", "gradle/wrapper/gradle-wrapper.jar",
               "org.gradle.wrapper.GradleWrapperMain", ":app:assembleDebug", ":app:testDebugUnitTest",
               ":app:lintDebug", "--no-daemon", "--console=plain"]
    subprocess.run(command, cwd=ROOT / "android", env=environment, check=True, timeout=900)
    source = ROOT / "android" / "app" / "build" / "outputs" / "apk" / "debug" / "app-debug.apk"
    apk = output / "LichViet-Android-debug.apk"
    shutil.copy2(source, apk)
    build_tools = sdk / "build-tools" / "35.0.0"
    signature = subprocess.run([java, "-jar", str(build_tools / "lib" / "apksigner.jar"), "verify", "--verbose", str(apk)],
                               capture_output=True, text=True, check=True, timeout=60)
    manifest = subprocess.run([str(build_tools / "aapt2.exe"), "dump", "badging", str(apk)],
                              capture_output=True, text=True, encoding="utf-8", check=True, timeout=60)
    suites = []
    for file in (ROOT / "android" / "app" / "build" / "test-results" / "testDebugUnitTest").glob("TEST-*.xml"):
        suites.append(ET.parse(file).getroot().attrib)
    report = dict(apk=str(apk), size_bytes=apk.stat().st_size, sha256=hashlib.sha256(apk.read_bytes()).hexdigest(),
                  signature=signature.stdout, manifest=manifest.stdout, unit_tests=suites,
                  lint_report=str(ROOT / "android/app/build/reports/lint-results-debug.html"),
                  device_tested=False, build_type="debug")
    (output / "verification.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"APK: {apk}")


if __name__ == "__main__":
    main()
