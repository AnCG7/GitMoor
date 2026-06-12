import os
import veiltk as vk
from src.viewmodel.base_viewmodel import BaseViewModel
from src.manager.git_manager import GitManager
from src.manager.template_manager import TemplateManager
from src.manager.localdata_manager import LocalDataManager
from src.utils.utils import Utils

Event = vk.Event


class CreateViewModel(BaseViewModel):
    def __init__(self):
        super().__init__()
        self.git_manager = GitManager.get_instance()
        self.template_manager = TemplateManager.get_instance()
        self.local_data_manager = LocalDataManager.get_instance()
        self.on_create_completed = Event()

    @staticmethod
    def _to_localized_text(message):
        formatted = Utils.format_localized_message(message)
        return vk.LocalizedText(formatted, text_type=vk.LocalizedText.TextType.STRING)

    @staticmethod
    def normalize_text(text):
        """去除文本首尾空白字符，用于路径/名称矫正"""
        return (text or "").strip()

    def validate_input(self, bare_repo_path, work_repo_path, repo_name):
        if not bare_repo_path:
            return False, vk.LocalizedText("bare_repo_path_empty"), "bare_repo_path_empty"
        if not work_repo_path:
            return False, vk.LocalizedText("work_repo_path_empty"), "work_repo_path_empty"
        if not repo_name:
            return False, vk.LocalizedText("repo_name_empty"), "repo_name_empty"
        return True, vk.LocalizedText("input_validation_success"), "input_validation_success"

    def create_repo(self, bare_repo_path, work_repo_path, repo_name, gitignore_template, enable_lfs, gitattributes_template):
        try:
            valid, message, raw_msg = self.validate_input(bare_repo_path, work_repo_path, repo_name)
            if not valid:
                self.on_create_completed.broadcast(False, message, raw_msg)
                return

            # 去除路径/仓库名首尾空白字符
            bare_repo_path = (bare_repo_path or "").strip()
            work_repo_path = (work_repo_path or "").strip()
            repo_name = (repo_name or "").strip()

            # 剥离用户可能手动输入的 file:// 协议前缀（转为文件系统路径供 os.path 检查）
            bare_repo_path = self.git_manager.strip_file_protocol(bare_repo_path)
            work_repo_path = self.git_manager.strip_file_protocol(work_repo_path)

            git_path = self.local_data_manager.get_value_value("git_exe_path", "")
            self.git_manager.set_git_exe_path(git_path)

            valid, message = self.git_manager.validate_git_executable(git_path)
            if not valid:
                self.on_create_completed.broadcast(False, self._to_localized_text(message), message)
                return

            compatible, version_message = self.git_manager.is_version_compatible()
            if not compatible:
                self.on_create_completed.broadcast(False, self._to_localized_text(version_message), version_message)
                return

            if not os.path.isdir(bare_repo_path):
                raw = f"bare_repo_path_invalid: {bare_repo_path}"
                self.on_create_completed.broadcast(False, self._to_localized_text(raw), raw)
                return

            if not os.path.isdir(work_repo_path):
                raw = f"work_repo_path_invalid: {work_repo_path}"
                self.on_create_completed.broadcast(False, self._to_localized_text(raw), raw)
                return

            bare_repo_full_path = os.path.join(bare_repo_path, f"{repo_name}.git")
            if os.path.exists(bare_repo_full_path):
                raw = f"bare_directory_exists: {bare_repo_full_path}"
                self.on_create_completed.broadcast(False, self._to_localized_text(raw), raw)
                return

            work_repo_full_path = os.path.join(work_repo_path, repo_name)
            if os.path.exists(work_repo_full_path):
                raw = f"work_directory_exists: {work_repo_full_path}"
                self.on_create_completed.broadcast(False, self._to_localized_text(raw), raw)
                return

            code, stdout, stderr = self.git_manager.create_bare_repo(bare_repo_full_path)
            if code != 0:
                raw = f"create_bare_repo_failed: {stderr}"
                self.on_create_completed.broadcast(False, self._to_localized_text(raw), raw)
                return

            code, stdout, stderr = self.git_manager.clone_repo(bare_repo_full_path, work_repo_full_path)
            if code != 0:
                raw = f"clone_repo_failed: {stderr}"
                self.on_create_completed.broadcast(False, self._to_localized_text(raw), raw)
                return

            if gitignore_template != "no_template":
                gitignore_content = self.template_manager.get_template_content("gitignore", gitignore_template)
                if gitignore_content is not None:
                    gitignore_path = os.path.join(work_repo_full_path, ".gitignore")
                    with open(gitignore_path, 'w', encoding='utf-8') as f:
                        f.write(gitignore_content)

            if enable_lfs:
                code, stdout, stderr = self.git_manager.enable_lfs(work_repo_full_path)
                if code != 0:
                    raw = f"enable_lfs_failed: {stderr}"
                    self.on_create_completed.broadcast(False, self._to_localized_text(raw), raw)
                    return

                if gitattributes_template != "no_template":
                    gitattributes_content = self.template_manager.get_template_content("gitattributes", gitattributes_template)
                    if gitattributes_content is not None:
                        gitattributes_path = os.path.join(work_repo_full_path, ".gitattributes")
                        with open(gitattributes_path, 'w', encoding='utf-8') as f:
                            f.write(gitattributes_content)

            self.on_create_completed.broadcast(True, vk.LocalizedText("repo_creation_success"), "repo_creation_success")
        except Exception as e:
            raw = f"repo_creation_error: {str(e)}"
            self.on_create_completed.broadcast(False, self._to_localized_text(raw), raw)

    def get_path(self, path_type, default=""):
        return self.local_data_manager.get_path(path_type, default)

    def save_path(self, path_type, path):
        self.local_data_manager.save_path(path_type, path)

    def validate_git_config(self, enable_lfs):
        git_path = self.local_data_manager.get_value_value("git_exe_path", "")
        self.git_manager.set_git_exe_path(git_path)

        valid, message = self.git_manager.validate_git_executable(git_path)
        if not valid:
            return False, self._to_localized_text(message)

        if enable_lfs:
            lfs_installed = self.git_manager.is_lfs_installed()
            if not lfs_installed:
                return False, vk.LocalizedText("lfs_not_installed")

            lfs_compatible, lfs_message = self.git_manager.is_lfs_version_compatible()
            if not lfs_compatible:
                return False, self._to_localized_text(lfs_message)

        return True, vk.LocalizedText("git_config_valid")

    def get_template_setting(self, setting_key, default="no_template"):
        return self.local_data_manager.get_value_value(setting_key, default)

    def save_template_setting(self, setting_key, value):
        self.local_data_manager.set_value(setting_key, value)

    def get_enable_lfs(self, default=False):
        return self.local_data_manager.get_value_value("enable_lfs", default)

    def set_enable_lfs(self, value):
        self.local_data_manager.set_value("enable_lfs", value)

    def get_repo_name(self):
        return self.local_data_manager.get_repo_name()

    def set_repo_name(self, repo_name):
        self.local_data_manager.set_repo_name(repo_name)

    def get_result(self):
        return self.local_data_manager.get_create_result()

    def save_result(self, result_data, color_type):
        """保存结构化结果数据（包含 prefix_key 和 raw_message）"""
        self.local_data_manager.set_create_result(result_data, color_type)

    def format_result_text(self, result_data):
        """根据结构化数据和当前语言生成显示文本"""
        if result_data is None:
            return ""
        prefix_key = result_data.get("prefix_key", "")
        raw_message = result_data.get("raw_message", "")
        prefix = vk.LocalizedText(prefix_key).get_text()
        message = Utils.format_localized_message(raw_message)
        return f"{prefix}: {message}"

    def destroy(self):
        super().destroy()
