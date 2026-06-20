"""任务库 — 已迁移到 script.task.TaskRepository。
本文件保留向后兼容包装，供尚未迁移的代码使用。
"""
import logging

from script.task import get_repo


# 向后兼容：通过属性访问缓存
class _CacheProxy:
    """代理到 Repository._cache，过渡期兼容旧代码"""
    def __getitem__(self, key):
        return get_repo()._cache[key]
    def get(self, key, default=None):
        return get_repo()._cache.get(key, default)
    def __setitem__(self, key, value):
        get_repo()._cache[key] = value
    def __delitem__(self, key):
        del get_repo()._cache[key]
    def pop(self, key, default=None):
        return get_repo()._cache.pop(key, default)


TASK_CONFIG_CACHE = _CacheProxy()


def get_task_config_by_id(task_id):
    """[deprecated] 请使用 get_repo().get_full_config(task_id)"""
    return get_repo().get_full_config(task_id)


def load_task_list():
    """[deprecated] 请使用 get_repo().list_all()"""
    return get_repo().list_all()


def get_full_task_config(name_or_id, version=None):
    """[deprecated] 请使用 get_repo().get_full_config(name_or_id, version)"""
    return get_repo().get_full_config(name_or_id, version)


def save_full_task_config(name_or_id, data, version=None):
    """[deprecated] 请使用 get_repo().save(name_or_id, data, version)"""
    get_repo().save(name_or_id, data, version)


def create_task(name, version, description=""):
    """[deprecated] 请使用 get_repo().create(name, version, description)"""
    return get_repo().create(name, version, description)


def build_task_zip(name, version=None):
    """[deprecated] 请使用 get_repo().build_zip(name, version)"""
    return get_repo().build_zip(name, version)


def import_task(zip_base64):
    """[deprecated] 请使用 get_repo().import_task(zip_base64)"""
    return get_repo().import_task(zip_base64)


def delete_task(name, version=None):
    """[deprecated] 请使用 get_repo().delete(name, version)"""
    return get_repo().delete(name, version)


def save_as_new_version(name_or_id, new_version, old_version=None):
    """[deprecated] 请使用 get_repo().save_as_new_version(name_or_id, new_version, old_version)"""
    return get_repo().save_as_new_version(name_or_id, new_version, old_version)


def resolve_task_version(name, version=None):
    """[deprecated] 请使用 get_repo().resolve(name, version)
    注意：旧接口返回 (task_id, config) 或 (None, error_dict)；
    新接口返回 (task_id, config) 或 (None, None)。包装层保持旧语义。
    """
    task_id, config = get_repo().resolve(name, version)
    if task_id is None:
        return None, {"error": f"任务不存在: {name}"}
    return task_id, config


def list_steps_for_task(task_id):
    """[deprecated] 请使用 get_repo().list_steps_for_task(task_id)"""
    return get_repo().list_steps_for_task(task_id)
