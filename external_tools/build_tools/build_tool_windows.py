import os
import sys
import subprocess
import importlib.util


def _stream_command(cmd, cwd=None, desc=None):
    """
    以实时逐行输出的方式运行命令，返回退出码。
    用户可直观看到下载进度、编译日志，避免误以为程序宕机。
    """
    if desc:
        print(desc)
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=cwd,
            encoding="utf-8",
            errors="replace",
        )
        for line in process.stdout:
            print(line, end="", flush=True)
        process.wait()
        return process.returncode
    except KeyboardInterrupt:
        print("\n用户取消操作。")
        process.terminate()
        sys.exit(1)


PROJECT_DIR = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAIN_PY_PATH = os.path.normpath(os.path.join(PROJECT_DIR, "main.py"))
ASSETS_DIR = os.path.normpath(os.path.join(PROJECT_DIR, "assets"))
ICON_DIR = os.path.normpath(os.path.join(ASSETS_DIR, "images", "icon"))
ICON_SIZES = [16, 24, 32, 48, 64, 128, 256]
OUTPUT_DIR = os.path.join(SCRIPT_DIR, "dist")
APP_NAME = "GitMoor"
TEMP_BUILD_DIR = os.path.join(SCRIPT_DIR, "_temp_build")
BUILD_DIR = os.path.join(TEMP_BUILD_DIR, "build")
OUTPUT_ICON_PATH = os.path.join(TEMP_BUILD_DIR, "app.ico")
REQUIRED_PACKAGES = {
    "PIL": "Pillow",
    "PyInstaller": "pyinstaller",
}
PACKAGE_USAGE = {
    "PIL": "用于合成应用图标（将多尺寸 PNG 合成为 .ico 文件）",
    "PyInstaller": "用于将 Python 程序打包为独立可执行文件（.exe）",
}
VALID_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff"}

# 注意：根目录下的 dev/ 文件夹不参与打包（仅存放开发期文件）


def phase_cleanup_legacy():
    print_separator("第一阶段：检查遗留文件")

    legacy_paths = [
        (TEMP_BUILD_DIR, "临时构建目录"),
        (OUTPUT_DIR, "上次生成的输出目录"),
    ]

    existing = [(p, label) for p, label in legacy_paths if os.path.exists(p)]

    if not existing:
        print("未发现遗留文件，跳过。")
        return

    print("发现以下遗留文件/目录：")
    print("-" * 40)
    for p, label in existing:
        print(f"  [{label}] {p}")
    print("-" * 40)

    choice = input("\n是否清理这些遗留文件？(y/n): ").strip().lower()
    if choice != "y":
        print("将跳过清理，后续步骤会覆盖已有文件。")
        return

    print()
    import shutil

    for p, label in existing:
        if not os.path.exists(p):
            print(f"  [跳过] {label} → 已不存在（可能已手动删除）")
            continue
        if os.path.isdir(p):
            shutil.rmtree(p)
            print(f"  已删除目录：{label} → {p}")
        elif os.path.isfile(p):
            os.remove(p)
            print(f"  已删除文件：{label} → {p}")

    print("遗留文件清理完成。")


def print_separator(title=""):
    print()
    print("=" * 60)
    if title:
        print(f"  {title}")
        print("=" * 60)
    print()


def check_and_install_dependencies():
    print_separator("第二阶段：依赖检查")

    installed = {}
    missing = {}

    for import_name, pip_name in REQUIRED_PACKAGES.items():
        spec = importlib.util.find_spec(import_name)
        if spec is not None:
            installed[import_name] = pip_name
        else:
            missing[import_name] = pip_name

    print("依赖状态：")
    print("-" * 40)
    for import_name, pip_name in installed.items():
        print(f"  [已安装] {import_name} (pip: {pip_name})")
    for import_name, pip_name in missing.items():
        print(f"  [未安装] {import_name} (pip: {pip_name})")
    print("-" * 40)

    if not missing:
        print("所有依赖已就绪！")
        return True

    print(f"\n以下依赖需要安装：")
    for import_name, pip_name in missing.items():
        usage = PACKAGE_USAGE.get(import_name, "")
        print(f"  - {pip_name} → {usage}")

    print(f"\n如自动安装较慢或意外失败，可以退出并用下列命令手动安装：")
    for import_name, pip_name in missing.items():
        print(f"  pip install {pip_name}")

    choice = input("\n是否安装以上依赖？(y/n): ").strip().lower()
    if choice != "y":
        print("\n未安装必要依赖，工具无法继续运行。")
        sys.exit(1)

    print()
    for import_name, pip_name in missing.items():
        print(f"正在安装 {pip_name}...")
        print("-" * 40)
        ret = _stream_command(
            [sys.executable, "-m", "pip", "install", pip_name],
            desc="（下载和安装过程中将显示详细进度）",
        )
        print("-" * 40)
        if ret != 0:
            print(f"\n依赖 {import_name} 安装失败（退出码: {ret}），工具无法继续运行。")
            sys.exit(1)
        print(f"{pip_name} 安装成功！\n")

    print("\n重新验证依赖...")
    all_ok = True
    for import_name in missing:
        spec = importlib.util.find_spec(import_name)
        if spec is None:
            print(f"  [失败] {import_name} 仍不可用")
            all_ok = False
        else:
            print(f"  [通过] {import_name}")

    if not all_ok:
        print("\n部分依赖验证失败，工具无法继续运行。")
        sys.exit(1)

    print("所有依赖已就绪！")
    return True


def scan_image_sizes(assets_dir):
    from PIL import Image

    size_map = {}
    if not os.path.isdir(assets_dir):
        print(f"错误：assets 目录不存在 → {assets_dir}")
        return size_map

    for filename in os.listdir(assets_dir):
        ext = os.path.splitext(filename)[1].lower()
        if ext not in VALID_IMAGE_EXTENSIONS:
            continue

        filepath = os.path.join(assets_dir, filename)
        try:
            with Image.open(filepath) as img:
                w, h = img.size
                if w == h and w in ICON_SIZES:
                    size_map[w] = filepath
        except Exception as e:
            print(f"  警告：无法读取 {filename} → {e}")

    return size_map


def check_icon_sizes(size_map):
    missing_sizes = []
    for s in ICON_SIZES:
        if s not in size_map:
            missing_sizes.append(s)
    return missing_sizes


def generate_ico(size_map, output_path):
    from PIL import Image

    # 按尺寸从大到小排列，确保 images[0] 是最大尺寸（256x256）
    sorted_sizes = sorted(ICON_SIZES, reverse=True)

    images = []
    for s in sorted_sizes:
        filepath = size_map[s]
        with Image.open(filepath) as img:
            img = img.convert("RGBA")
            if img.size != (s, s):
                img = img.resize((s, s), Image.LANCZOS)
            images.append(img.copy())

    if images:
        # 不传 sizes 参数！避免 Pillow 用内部低质量缩放覆盖已准备好的各尺寸图片
        images[0].save(
            output_path,
            format="ICO",
            append_images=images[1:],
        )

    return output_path


def auto_generate_missing_icons(size_map, missing_sizes):
    """
    从已有的最大尺寸图片自动缩放生成缺失尺寸的图标。
    返回更新后的 size_map。
    """
    from PIL import Image

    # 选择最大可用尺寸作为缩放源
    available_sizes = sorted(size_map.keys(), reverse=True)
    source_size = available_sizes[0]
    source_path = size_map[source_size]

    print(f"\n将使用 {source_size}×{source_size} 图片作为缩放源：")
    print(f"  源文件：{os.path.basename(source_path)}")
    print(f"  缩放算法：Lanczos（最高质量）")
    print()

    # 确保临时构建目录存在
    os.makedirs(TEMP_BUILD_DIR, exist_ok=True)

    with Image.open(source_path) as src_img:
        src_img = src_img.convert("RGBA")
        for s in missing_sizes:
            resized = src_img.resize((s, s), Image.LANCZOS)
            generated_path = os.path.join(TEMP_BUILD_DIR, f"icon_generated_{s}.png")
            resized.save(generated_path, format="PNG")
            size_map[s] = generated_path
            print(f"  [已生成] {s}×{s} → {generated_path}")

    print()
    print("缺失尺寸自动生成完成！")
    print(f"\n  提示：自动生成的中间 PNG 文件保存在：")
    print(f"  {os.path.abspath(TEMP_BUILD_DIR)}")
    print(f"  如果您需要单独使用这些图片，可在构建完成前从该目录取用。")
    print(f"  （构建结束后该临时目录将被清理）")
    return size_map


def phase_generate_icon():
    print_separator("第三阶段：生成 Windows .ico 图标")

    while True:
        print(f"扫描图片目录：{ICON_DIR}")
        size_map = scan_image_sizes(ICON_DIR)

        print("\n已找到的图标尺寸：")
        print("-" * 40)
        for s in ICON_SIZES:
            if s in size_map:
                print(f"  [  有  ] {s}×{s} → {os.path.basename(size_map[s])}")
            else:
                print(f"  [缺少  ] {s}×{s}")
        print("-" * 40)

        missing_sizes = check_icon_sizes(size_map)

        if not missing_sizes:
            print("所有图标尺寸齐全！")
            break

        # 检查是否至少有一个可用尺寸作为缩放源
        if not size_map:
            print("\n错误：未找到任何可用的图标图片！")
            print("请将至少一张正方形图标图片放入 assets/images/icon 目录。")
            print()
            choice = input("输入 c 继续检查 / 输入 q 退出: ").strip().lower()
            if choice == "q":
                print("用户选择退出，工具中止运行。")
                sys.exit(0)
            elif choice == "c":
                print("重新检查图片尺寸...")
                continue
            else:
                print("无效输入，请输入 c 或 q。")
                continue

        # 有部分尺寸缺失，提供自动生成选项
        available_sizes = sorted(size_map.keys(), reverse=True)
        source_size = available_sizes[0]
        source_file = os.path.basename(size_map[source_size])

        print(f"\n缺少以下尺寸的图标图片：")
        for s in missing_sizes:
            print(f"  - {s}×{s}")

        print(f"\n可以从已有的最大尺寸图片自动生成缺失尺寸：")
        print(f"  源图片：{source_file}（{source_size}×{source_size}）")
        print(f"  缩放算法：Lanczos（最高质量）")
        print()
        print("请选择：")
        print("  a - 自动从源图片缩放生成缺失尺寸（推荐）")
        print("  m - 手动提供，将图片放入 assets/images/icon 后重新检查")
        print("  q - 退出")
        print()
        choice = input("请输入选择 (a/m/q): ").strip().lower()

        if choice == "a":
            size_map = auto_generate_missing_icons(size_map, missing_sizes)
            break
        elif choice == "m":
            print("\n请将对应尺寸的图片放入 assets/images/icon 目录后继续。")
            print()
            sub_choice = input("输入 c 继续检查 / 输入 q 退出: ").strip().lower()
            if sub_choice == "q":
                print("用户选择退出，工具中止运行。")
                sys.exit(0)
            elif sub_choice == "c":
                print("重新检查图片尺寸...")
                continue
            else:
                print("无效输入，重新检查图片尺寸...")
                continue
        elif choice == "q":
            print("用户选择退出，工具中止运行。")
            sys.exit(0)
        else:
            print("无效输入，请输入 a、m 或 q。")
            continue

    print(f"\n正在生成 .ico 文件...")
    os.makedirs(TEMP_BUILD_DIR, exist_ok=True)
    icon_path = generate_ico(size_map, OUTPUT_ICON_PATH)

    if os.path.exists(icon_path):
        file_size = os.path.getsize(icon_path)
        print(f".ico 文件生成成功！")
        print(f"  路径：{icon_path}")
        print(f"  大小：{file_size:,} 字节")
    else:
        print("错误：.ico 文件生成失败！")
        sys.exit(1)

    return icon_path


def build_exe(main_py, icon_path, output_dir, app_name):
    print_separator("第四阶段：打包应用程序")

    import shutil

    os.makedirs(output_dir, exist_ok=True)

    veiltk_path = os.path.normpath(os.path.join(PROJECT_DIR, "veil_tkinter"))
    veiltk_assets_path = os.path.join(veiltk_path, "veiltk", "assets")
    project_assets_path = ASSETS_DIR
    app_setting_path = os.path.normpath(os.path.join(PROJECT_DIR, "app_setting.json"))
    src_path = PROJECT_DIR

    # 所有 Python 运行时文件放入 _runtime/ 子目录，保持第一层干净
    contents_dir = "_runtime"

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--onedir",
        "--windowed",
        f"--contents-directory={contents_dir}",
        f"--icon={icon_path}",
        f"--name={app_name}",
        f"--distpath={output_dir}",
        f"--workpath={BUILD_DIR}",
        f"--specpath={TEMP_BUILD_DIR}",
        f"--paths={veiltk_path}",
        f"--paths={src_path}",
        "--collect-submodules=veiltk",
        "--collect-submodules=src",
        # app_setting.json 是只读默认配置，放进 _runtime/ 不暴露给用户
        f"--add-data={app_setting_path};.",
        main_py,
    ]

    print("PyInstaller 命令：")
    print(f"  {' '.join(cmd)}")
    print()
    print("正在打包，请稍候（以下为 PyInstaller 实时输出）...")
    print("-" * 60)

    ret = _stream_command(cmd, cwd=SCRIPT_DIR)

    print("-" * 60)

    if ret != 0:
        print("错误：EXE 打包失败！")
        sys.exit(1)

    print("应用程序打包完成！")

    # ---- 后置步骤：复制运行时资源到输出目录 ----
    # 这些资源（模板、语言文件、主题样式等）作为外部文件放在 exe 同级目录，
    # 一方面方便程序在运行时读取，另一方面也便于用户按需修改。
    print()
    print("正在复制运行时资源到输出目录...")
    app_dir = os.path.join(output_dir, app_name)

    # 复制项目 assets 目录（模板、本地化等）
    target_assets = os.path.join(app_dir, "assets")
    if os.path.exists(target_assets):
        shutil.rmtree(target_assets)
    shutil.copytree(project_assets_path, target_assets)
    print(f"  [assets/] → {target_assets}")

    # 复制 veiltk assets（主题样式文件）
    target_veiltk_assets = os.path.join(app_dir, "veiltk", "assets")
    os.makedirs(target_veiltk_assets, exist_ok=True)
    if os.path.exists(target_veiltk_assets):
        shutil.rmtree(target_veiltk_assets)
    shutil.copytree(veiltk_assets_path, target_veiltk_assets)
    print(f"  [veiltk/assets/] → {target_veiltk_assets}")

    print("资源文件复制完成！")


def phase_deploy_and_report(output_dir, app_name):
    print_separator("第五阶段：验证与部署")

    import shutil

    app_dir = os.path.join(output_dir, app_name)
    exe_path = os.path.join(app_dir, f"{app_name}.exe")

    if not os.path.isdir(app_dir):
        print(f"错误：未找到输出目录 → {app_dir}")
        sys.exit(1)

    if not os.path.exists(exe_path):
        print(f"错误：输出目录中未找到主程序 → {exe_path}")
        sys.exit(1)

    # 计算目录总大小
    def get_dir_size(path):
        total = 0
        for dirpath, _, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.exists(fp):
                    total += os.path.getsize(fp)
        return total

    dir_size = get_dir_size(app_dir)
    exe_size = os.path.getsize(exe_path)

    print("构建成功！输出目录信息：")
    print("-" * 40)
    print(f"  输出目录：{app_dir}")
    print(f"  目录总大小：{dir_size:,} 字节 ({dir_size / (1024 * 1024):.2f} MB)")
    print(f"  主程序大小：{exe_size:,} 字节 ({exe_size / (1024 * 1024):.2f} MB)")
    print("-" * 40)

    # 清理中间文件
    cleanup_candidates = [TEMP_BUILD_DIR]

    print("\n以下中间文件可以清理：")
    for path in cleanup_candidates:
        exists = "存在" if os.path.exists(path) else "不存在"
        print(f"  [{exists}] {path}")

    choice = input("\n是否清理中间文件？(y/n): ").strip().lower()
    if choice == "y":
        for path in cleanup_candidates:
            if not os.path.exists(path):
                print(f"  [跳过] {path} → 已不存在")
                continue
            if os.path.isdir(path):
                shutil.rmtree(path)
                print(f"  已删除目录：{path}")
            elif os.path.isfile(path):
                os.remove(path)
                print(f"  已删除文件：{path}")

    # 部署说明
    print()
    print_separator("第六阶段：部署说明")

    print(f"输出目录结构：")
    print(f"  {app_dir}")
    print(f"    ├── {app_name}.exe          ← 主程序")
    print(f"    ├── assets/                ← 项目资源（可修改）")
    print(f"    │   └── templates/         ← Git 模板（可自行增删）")
    print(f"    ├── veiltk/assets/         ← 主题资源（可修改）")
    print(f"    └── _runtime/              ← Python 运行时 + 默认配置")
    print()
    print(f"直接运行 {app_name}.exe 即可启动应用。")
    print(f"如需分发，请将整个 {app_name}/ 目录打包发送。")
    print()
    print(f"[自定义模板说明]")
    print(f"  你可以在 assets/templates/ 目录下添加自己的 Git 模板：")
    print(f"  - gitignore/  →  放入 *.gitignore 文件")
    print(f"  - gitattributes/ → 放入 *.gitattributes 文件")
    print(f"  - 文件名去掉后缀即为模板名，如 Python.gitignore → 模板名 \"Python\"")
    print(f"  - 同名的两个文件会自动配套，无需额外配置")

    print()
    print("=" * 60)
    print("  全部完成！")
    print("=" * 60)


def main():
    print_separator("EXE 构建工具")

    print("配置信息：")
    print(f"  入口文件：{MAIN_PY_PATH}")
    print(f"  图标目录：{ICON_DIR}")
    print(f"  输出目录：{OUTPUT_DIR}")
    print(f"  应用名称：{APP_NAME}")

    if not os.path.exists(MAIN_PY_PATH):
        print(f"\n错误：入口文件不存在 → {MAIN_PY_PATH}")
        sys.exit(1)

    check_and_install_dependencies()
    phase_cleanup_legacy()
    icon_path = phase_generate_icon()
    build_exe(MAIN_PY_PATH, icon_path, OUTPUT_DIR, APP_NAME)
    phase_deploy_and_report(OUTPUT_DIR, APP_NAME)


if __name__ == "__main__":
    main()
