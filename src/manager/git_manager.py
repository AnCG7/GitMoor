import subprocess
import os
import re
import shutil
import threading
import shlex
import veiltk as vk

Event = vk.Event

class GitManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.git_exe = None
        
        # 命令执行完成事件
        self.on_command_completed = Event()
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @staticmethod
    def _git_executable_name():
        """返回当前平台 Git 可执行文件名称"""
        return "git.exe" if os.name == "nt" else "git"
    
    @staticmethod
    def get_executable_filetypes():
        """返回当前平台文件浏览器过滤器（用于选择 Git 可执行文件）"""
        if os.name == "nt":
            return [("Executable files", "*.exe"), ("All files", "*.*")]
        else:
            return [("All files", "*")]

    @staticmethod
    def normalize_git_url(path):
        r"""
        跨平台路径规范化，将 Windows UNC 路径转换为 Git 支持的 file:// 协议格式。
        - URL（含 ://）：原样透传
        - UNC 路径（\\server\share 或 //server/share）：显式构造 file:////{host}{rest}
        - 本地路径：反斜杠转正斜杠
        """
        if not path:
            return path

        # 1. 已是 URL（包含 ://），原样返回
        if "://" in path:
            return path

        # 2. UNC 路径：\\server\share 或 //server/share
        if path.startswith("//") or path.startswith("\\\\"):
            normalized = path.replace("\\", "/")          # 统一斜杠 → //server/share/...
            without_prefix = normalized[2:]               # 去掉 // → server/share/...
            first_slash = without_prefix.find("/")
            if first_slash == -1:
                return f"file:////{without_prefix}"      # 只有主机名，无子路径
            host = without_prefix[:first_slash]
            rest = without_prefix[first_slash:]           # /share/...
            return f"file:////{host}{rest}"

        # 3. 本地路径：反斜杠 → 正斜杠
        return path.replace("\\", "/")

    @staticmethod
    def strip_file_protocol(path):
        r"""
        将 file:// 协议 URL 还原为文件系统路径（normalize_git_url 的反向操作）。
        仅用于文件系统检查（os.path.isdir / os.path.exists），Git 命令仍使用 normalize_git_url。
        - file:////host/share/path → \\host\share\path（UNC）
        - file:///C:/path → C:\path（Windows 本地绝对路径）
        - file://C:/path → C:\path
        - 无 file:// → 原样返回
        """
        if not path or not path.startswith("file://"):
            return path

        remaining = path[len("file://"):]

        if os.name == "nt":
            # Windows: 正斜杠 → 反斜杠
            remaining = remaining.replace("/", "\\")
            # file:///C:/path → \C:\path → 去掉前置多余反斜杠
            if len(remaining) >= 3 and remaining[0] == "\\" and remaining[1].isalpha() and remaining[2] == ":":
                remaining = remaining[1:]
        else:
            remaining = remaining.replace("\\", "/")

        return remaining

    def set_git_exe_path(self, git_exe_path):
        """设置 Git 可执行文件路径"""
        if git_exe_path and os.path.isdir(git_exe_path):
            self.git_exe = os.path.join(git_exe_path, self._git_executable_name())
        else:
            self.git_exe = git_exe_path if git_exe_path else "git"
    
    def get_git_exe_path(self):
        """获取当前 Git 可执行文件路径"""
        return self.git_exe
    
    def _run_command(self, command, cwd=None):
        """运行Git命令（shell=False，避免 cmd.exe 转义干扰路径）"""
        try:
            git_exe = self.git_exe or "git"
            if isinstance(command, str):
                args = [git_exe] + shlex.split(command, posix=(os.name != "nt"))
            else:
                args = [git_exe] + list(command)

            kwargs = {
                "cwd": cwd,
                "capture_output": True,
                "text": True,
                "shell": False,
                "encoding": "utf-8",
                "errors": "replace",
            }
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            result = subprocess.run(args, **kwargs)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return 1, "", str(e)
    
    def run_command_async(self, command, cwd=None, callback_event=None):
        """异步运行Git命令"""
        def _run():
            code, stdout, stderr = self._run_command(command, cwd)
            if callback_event:
                callback_event.broadcast(command, code, stdout, stderr)
            else:
                self.on_command_completed.broadcast(command, code, stdout, stderr)
        
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        return thread
    
    def validate_git_executable(self, git_path):
        """验证Git可执行文件路径是否有效"""
        if not git_path:
            return False, "git_path_not_set"
        
        if not os.path.exists(git_path):
            return False, f"git_path_not_exists: {git_path}"
        
        actual_path = git_path
        if os.path.isdir(git_path):
            git_exe_path = os.path.join(git_path, GitManager._git_executable_name())
            if not os.path.exists(git_exe_path):
                return False, f"git_exe_not_found: {git_path}"
            actual_path = git_exe_path
        
        try:
            kwargs = {
                "capture_output": True,
                "text": True,
                "timeout": 5,
                "shell": False,
                "encoding": "utf-8",
                "errors": "replace",
            }
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.CREATE_NO_WINDOW

            result = subprocess.run([actual_path, "--version"], **kwargs)
            if result.returncode != 0:
                return False, f"git_executable_invalid: {actual_path}"
            return True, "git_executable_valid"
        except Exception as e:
            return False, f"git_executable_error: {str(e)}"
    
    def get_git_version(self):
        """获取Git版本"""
        code, stdout, stderr = self._run_command(["--version"])
        if code != 0:
            return None
        
        match = re.search(r"git version ([0-9]+\.[0-9]+\.[0-9]+)", stdout)
        if match:
            return match.group(1)
        return None
    
    def get_lfs_version(self):
        """获取Git LFS版本"""
        code, stdout, stderr = self._run_command(["lfs", "version"])
        if code != 0:
            return None
        
        match = re.search(r"git-lfs/([0-9]+\.[0-9]+\.[0-9]+)", stdout)
        if match:
            return match.group(1)
        return None
    
    def is_lfs_installed(self):
        """检查系统级 Git LFS 是否已安装"""
        code, stdout, stderr = self._run_command(["lfs", "version"])
        return code == 0

    def verify_repo_lfs_status(self, repo_path):
        """
        深度检查特定仓库的 LFS 是否成功安装（读取 filter 配置和 hooks）
        返回: (bool, str) -> (是否健康, 状态信息)
        """
        # 1. 检查 filter.lfs.required
        code, stdout, _ = self._run_command(
            ["config", "--local", "--get", "filter.lfs.required"],
            cwd=repo_path
        )
        if code != 0 or stdout.strip() != "true":
            return False, "lfs_filter_missing"

        # 2. 检查 hooks/pre-push 是否存在
        code, hooks_dir, _ = self._run_command(
            ["rev-parse", "--git-path", "hooks"],
            cwd=repo_path
        )
        if code == 0:
            hooks_path = os.path.join(repo_path, hooks_dir.strip(), "pre-push")
            if not os.path.exists(hooks_path):
                return False, "lfs_hooks_missing"

        return True, "lfs_repo_healthy"
    
    def is_lfs_version_compatible(self):
        """检查Git LFS版本是否兼容（2.10+支持本地磁盘协议）"""
        version = self.get_lfs_version()
        if not version:
            return False, "lfs_version_not_found"
        
        major, minor, patch = map(int, version.split("."))
        
        if major > 2 or (major == 2 and minor >= 10):
            return True, f"lfs_version_compatible: {version}"
        else:
            return False, f"lfs_version_incompatible: {version}"
    
    def is_version_compatible(self):
        """检查Git版本是否兼容（2.10+）"""
        version = self.get_git_version()
        if not version:
            return False, "git_version_not_found"
        
        major, minor, patch = map(int, version.split("."))
        
        if major > 2 or (major == 2 and minor >= 10):
            return True, f"git_version_compatible: {version}"
        else:
            return False, f"git_version_incompatible: {version}"
    
    @staticmethod
    def find_git_executable():
        """查找Git可执行文件路径（跨平台）"""
        # 1. 使用 shutil.which 跨平台搜索 PATH
        git_cmd = shutil.which("git")
        if git_cmd:
            # Windows: shutil.which 会用 PATHEXT（大写 .EXE）拼接路径，
            # 导致返回 git.EXE 而非 git.exe，统一规范化扩展名为小写
            if os.name == "nt":
                name, ext = os.path.splitext(git_cmd)
                if ext:
                    git_cmd = name + ext.lower()
            return git_cmd

        # 2. Windows 兜底：扫描常见安装路径
        if os.name == "nt":
            common_paths = [
                r"C:\Program Files\Git\bin\git.exe",
                r"C:\Program Files (x86)\Git\bin\git.exe",
                r"C:\Git\bin\git.exe",
            ]
            for git_path in common_paths:
                if os.path.exists(git_path):
                    return git_path

        return None
    
    def check_git_on_startup(self, git_exe_path="", enable_lfs=False):
        """启动时检查Git"""
        if git_exe_path:
            valid, message = self.validate_git_executable(git_exe_path)
            if valid:
                self.git_exe = git_exe_path if not os.path.isdir(git_exe_path) else os.path.join(git_exe_path, GitManager._git_executable_name())
                
                messages = []
                messages.append("git_executable_found")
                
                if enable_lfs:
                    lfs_installed = self.is_lfs_installed()
                    if not lfs_installed:
                        return False, git_exe_path, "lfs_not_installed"
                    
                    lfs_compatible, lfs_message = self.is_lfs_version_compatible()
                    if not lfs_compatible:
                        return False, git_exe_path, lfs_message
                    messages.append(lfs_message)
                
                return True, git_exe_path, "\n".join(messages)
            else:
                return False, git_exe_path, message
        
        found_git_path = self.find_git_executable()
        if found_git_path:
            valid, message = self.validate_git_executable(found_git_path)
            if valid:
                self.git_exe = found_git_path
                
                messages = []
                messages.append("git_executable_auto_found")
                
                if enable_lfs:
                    lfs_installed = self.is_lfs_installed()
                    if not lfs_installed:
                        return False, found_git_path, "lfs_not_installed"
                    
                    lfs_compatible, lfs_message = self.is_lfs_version_compatible()
                    if not lfs_compatible:
                        return False, found_git_path, lfs_message
                    messages.append(lfs_message)
                
                return True, found_git_path, "\n".join(messages)
            else:
                return False, found_git_path, message
        
        return False, None, "git_executable_not_found"
    
    def create_bare_repo(self, repo_path):
        """创建裸仓库（纯本地操作，不接受 file:// 协议）"""
        safe_path = repo_path.replace("\\", "/")
        return self._run_command(["init", "--bare", safe_path])
    
    def clone_repo(self, repo_url, target_path):
        """克隆仓库"""
        safe_url = self.normalize_git_url(repo_url)
        return self._run_command(["clone", safe_url, target_path])

    def add_remote(self, repo_path, remote_name="origin", remote_url=""):
        """添加远程仓库（用于 Work 关联 Bare）"""
        safe_url = self.normalize_git_url(remote_url)
        return self._run_command(["remote", "add", remote_name, safe_url], cwd=repo_path)
    
    def enable_lfs(self, repo_path):
        """启用LFS"""
        return self._run_command(["lfs", "install"], cwd=repo_path)
    
    def add_file(self, file_path, repo_path):
        """添加文件到Git"""
        return self._run_command(["add", file_path], cwd=repo_path)
    
    def commit(self, message, repo_path):
        """提交更改"""
        return self._run_command(["commit", "-m", message], cwd=repo_path)
