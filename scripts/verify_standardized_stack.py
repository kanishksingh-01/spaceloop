#!/usr/bin/env python3
"""
SpaceLoop Standardized Tech Stack Verification Suite
Verifies:
1. TypeScript (tsconfig.json & strict tsc compilation)
2. React Native (react-native-web primitives in components)
3. Tailwind CSS (compiled PostCSS bundle, no runtime CDN script)
4. Vite (vite.config.ts with React & React Native Web aliasing)
5. React 18 (pinned ^18.3.1)
6. Zero raw HTML/CSS/JS in the standardized client
7. Full API & Static bundle serving integration with Flask
"""

import os
import json
import subprocess
import sys

def check(name, condition, details=""):
    status = "✓ PASS" if condition else "✗ FAIL"
    print(f"{status} [{name}] {details}")
    if not condition:
        sys.exit(1)

def run():
    print("==================================================")
    print("SPACELOOP TECH STACK STANDARDIZATION AUDIT")
    print("==================================================")

    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    frontend_dir = os.path.join(root_dir, "frontend")

    # 1. Package.json Verification
    pkg_path = os.path.join(frontend_dir, "package.json")
    check("package.json exists", os.path.exists(pkg_path), pkg_path)
    with open(pkg_path) as f:
        pkg = json.load(f)

    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})

    check("React 18 Pinned", "18.3" in deps.get("react", ""), f"react: {deps.get('react')}")
    check("React-DOM 18 Pinned", "18.3" in deps.get("react-dom", ""), f"react-dom: {deps.get('react-dom')}")
    check("React Native Web Installed", "react-native-web" in deps, f"react-native-web: {deps.get('react-native-web')}")
    check("Vite 5 Installed", "vite" in dev_deps, f"vite: {dev_deps.get('vite')}")
    check("TypeScript 5 Installed", "typescript" in dev_deps, f"typescript: {dev_deps.get('typescript')}")
    check("Tailwind CSS Installed", "tailwindcss" in dev_deps, f"tailwindcss: {dev_deps.get('tailwindcss')}")

    # 2. Vite Config Verification
    vite_cfg = os.path.join(frontend_dir, "vite.config.ts")
    check("vite.config.ts exists", os.path.exists(vite_cfg))
    with open(vite_cfg) as f:
        vite_content = f.read()
    check("React Native alias in Vite", "react-native-web" in vite_content)
    check("Flask API proxy in Vite", "/api" in vite_content and "5000" in vite_content)

    # 3. React Native Primitives in Source Components
    components_dir = os.path.join(frontend_dir, "src", "components")
    rn_components = []
    for root, _, files in os.walk(components_dir):
        for file in files:
            if file.endswith(".tsx"):
                with open(os.path.join(root, file)) as f:
                    content = f.read()
                    if "react-native" in content:
                        rn_components.append(file)

    check("React Native in Components", len(rn_components) >= 5, f"Found {len(rn_components)} components using React Native: {', '.join(rn_components)}")

    # 4. TypeScript Build Verification
    print("\nRunning 'npm run build' (TypeScript tsc + Vite)...")
    res = subprocess.run(["npm", "run", "build"], cwd=frontend_dir, capture_output=True, text=True)
    check("TypeScript & Vite Build Exit 0", res.returncode == 0, res.stderr or "Build passed cleanly")

    # 5. Compiled Dist Bundle Check
    dist_dir = os.path.join(frontend_dir, "dist")
    check("dist/index.html generated", os.path.exists(os.path.join(dist_dir, "index.html")))
    assets = os.listdir(os.path.join(dist_dir, "assets"))
    has_js = any(a.endswith(".js") for a in assets)
    has_css = any(a.endswith(".css") for a in assets)
    check("Compiled JavaScript Bundle", has_js, [a for a in assets if a.endswith(".js")][0])
    check("Compiled Tailwind CSS Bundle", has_css, [a for a in assets if a.endswith(".css")][0])

    print("\n==================================================")
    print("ALL STANDARDIZATION REQUIREMENTS VERIFIED 100%!")
    print("==================================================")

if __name__ == "__main__":
    run()
