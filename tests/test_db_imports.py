import importlib


def test_db_base_module_imports():
    importlib.import_module("buma.db.base")


def test_db_models_module_imports():
    importlib.import_module("buma.db.models")
