"""レイヤ構造の契約を検証する."""

import ast
from pathlib import Path

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "codex_httpd"
API_ROOT = SRC_ROOT / "api"
USECASE_ROOT = SRC_ROOT / "usecases"
INFRA_ROOT = SRC_ROOT / "infrastructure"
ROUTERS_ROOT = API_ROOT / "routers"


def _python_files(root: Path) -> list[Path]:
    """指定ディレクトリ配下の Python ファイルを列挙する."""
    return sorted(path for path in root.rglob("*.py") if path.is_file())


def _codex_imports(path: Path) -> set[str]:
    """ファイル内の codex_httpd から始まる import を抽出する."""
    tree = ast.parse(path.read_text(), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("codex_httpd"):
                    imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith("codex_httpd"):
                imports.add(node.module)
    return imports


def _usecase_constructor_calls(path: Path) -> list[str]:
    """UseCase クラスの直接生成呼び出しを列挙する."""
    tree = ast.parse(path.read_text(), filename=str(path))
    calls: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id.endswith("UseCase"):
            calls.append(node.func.id)
    return calls


def test_api_layer_does_not_depend_on_infrastructure() -> None:
    """API 層が Infrastructure 層に直接依存しないことを確認する."""
    for path in _python_files(API_ROOT):
        imports = _codex_imports(path)
        infra_imports = sorted(module for module in imports if module.startswith("codex_httpd.infrastructure"))
        assert not infra_imports, f"{path} が Infrastructure へ依存しています: {infra_imports}"


def test_usecase_layer_does_not_depend_on_api_or_infrastructure() -> None:
    """UseCase 層が API/Infrastructure 層へ依存しないことを確認する."""
    for path in _python_files(USECASE_ROOT):
        imports = _codex_imports(path)
        forbidden = sorted(
            module for module in imports if module.startswith("codex_httpd.api") or module.startswith("codex_httpd.infrastructure")
        )
        assert not forbidden, f"{path} が不正なレイヤへ依存しています: {forbidden}"


def test_infrastructure_layer_does_not_depend_on_api() -> None:
    """Infrastructure 層が API 層へ依存しないことを確認する."""
    for path in _python_files(INFRA_ROOT):
        imports = _codex_imports(path)
        api_imports = sorted(module for module in imports if module.startswith("codex_httpd.api"))
        assert not api_imports, f"{path} が API 層に依存しています: {api_imports}"


def test_routers_do_not_access_container_directly() -> None:
    """ルータが app.state.container を直接参照しないことを確認する."""
    for path in _python_files(ROUTERS_ROOT):
        source = path.read_text()
        assert "app.state.container" not in source, f"{path} が app.state.container を直接参照しています"
        assert "request.app.state" not in source, f"{path} が request.app.state を直接参照しています"


def test_routers_do_not_construct_usecases_directly() -> None:
    """ルータ内で UseCase を直接 new しないことを確認する."""
    for path in _python_files(ROUTERS_ROOT):
        calls = _usecase_constructor_calls(path)
        assert not calls, f"{path} が UseCase を直接生成しています: {calls}"
