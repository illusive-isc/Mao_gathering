"""
Mao_gathering Server
画像のアップロード・削除を受け付け、config.txt を更新して git push する。

エンドポイント:
  POST   /upload   - 画像アップロード (form: username, type, image)
  DELETE /delete   - 画像削除       (JSON: username, type, index[1始まり])
"""

import os
import re
import subprocess
import shutil
from flask import Flask, request, jsonify

app = Flask(__name__)

REPO_DIR      = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH   = os.path.join(REPO_DIR, "config.txt")
PERMS_PATH    = os.path.join(REPO_DIR, "permissions.txt")
IMAGES_DIR    = os.path.join(REPO_DIR, "images")

# Windows 用フォールバック付き git パス解決
_GIT = shutil.which("git") or r"C:\Program Files\Git\mingw64\bin\git.exe"

_VALID_NAME = re.compile(r"^[A-Za-z0-9_]+$")


# ---------------------------------------------------------------------------
# 権限チェック
# ---------------------------------------------------------------------------

def _read_permissions():
    admins, staff = set(), set()
    section = None
    with open(PERMS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line == "[admin]":
                section = "admin"
            elif line == "[staff]":
                section = "staff"
            elif line and not line.startswith("#"):
                if section == "admin":
                    admins.add(line)
                elif section == "staff":
                    staff.add(line)
    return admins, staff


def _is_authorized(username: str) -> bool:
    admins, staff = _read_permissions()
    return username in admins or username in staff


# ---------------------------------------------------------------------------
# config.txt 操作
# ---------------------------------------------------------------------------

def _read_config():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return f.readlines()


def _write_config(lines):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)


def _type_entries(lines, type_name):
    """config.txt の行リストから指定タイプのエントリ (行インデックス, 行) を返す。"""
    result = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.split(":")[0] == type_name:
            result.append((i, line))
    return result


# ---------------------------------------------------------------------------
# 画像ファイル操作
# ---------------------------------------------------------------------------

def _image_folder(type_name: str) -> str:
    folder = os.path.join(IMAGES_DIR, type_name)
    os.makedirs(folder, exist_ok=True)
    return folder


def _sorted_images(folder: str):
    return sorted(
        f for f in os.listdir(folder) if re.match(r"^\d{3}\.jpg$", f, re.IGNORECASE)
    )


def _next_number(type_name: str) -> int:
    files = _sorted_images(_image_folder(type_name))
    if not files:
        return 1
    return int(files[-1][:3]) + 1


# ---------------------------------------------------------------------------
# Git 操作
# ---------------------------------------------------------------------------

def _git(*args):
    subprocess.run([_GIT, "-C", REPO_DIR, *args], check=True)


def _commit_and_push(message: str):
    _git("add", "config.txt")
    _git("add", "images/")
    # 差分がなければ commit をスキップ
    result = subprocess.run(
        [_GIT, "-C", REPO_DIR, "diff", "--cached", "--quiet"]
    )
    if result.returncode != 0:
        _git("commit", "-m", message)
    _git("push")


# ---------------------------------------------------------------------------
# エンドポイント
# ---------------------------------------------------------------------------

@app.route("/upload", methods=["POST"])
def upload():
    username  = (request.form.get("username") or "").strip()
    type_name = (request.form.get("type")     or "").strip()
    image     = request.files.get("image")

    if not username or not type_name or not image:
        return jsonify({"error": "username, type, image are required"}), 400
    if not _VALID_NAME.match(username) or not _VALID_NAME.match(type_name):
        return jsonify({"error": "invalid username or type"}), 400
    if not _is_authorized(username):
        return jsonify({"error": "forbidden"}), 403

    # 画像保存
    num      = _next_number(type_name)
    filename = f"{num:03d}.jpg"
    folder   = _image_folder(type_name)
    image.save(os.path.join(folder, filename))

    # config.txt 更新 — 同タイプの末尾に追加（タイプが存在しない場合はファイル末尾）
    lines     = _read_config()
    new_entry = f"{type_name}:{username}\n"
    entries   = _type_entries(lines, type_name)

    if entries:
        last_idx = entries[-1][0]
        lines.insert(last_idx + 1, new_entry)
    else:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] += "\n"
        lines.append(new_entry)

    _write_config(lines)
    _commit_and_push(f"add: {type_name}/{filename} by {username}")

    return jsonify({"success": True, "file": filename}), 200


@app.route("/delete", methods=["DELETE"])
def delete():
    body = request.get_json(force=True, silent=True) or {}

    username  = str(body.get("username") or "").strip()
    type_name = str(body.get("type")     or "").strip()
    index     = body.get("index")  # 1始まり、そのタイプ内での順番

    if not username or not type_name or index is None:
        return jsonify({"error": "username, type, index are required"}), 400
    if not isinstance(index, int) or index < 1:
        return jsonify({"error": "index must be a positive integer"}), 400
    if not _is_authorized(username):
        return jsonify({"error": "forbidden"}), 403

    # config.txt から対象行を削除
    lines   = _read_config()
    entries = _type_entries(lines, type_name)

    if index > len(entries):
        return jsonify({"error": "index out of range"}), 400

    target_line_idx = entries[index - 1][0]
    lines.pop(target_line_idx)
    _write_config(lines)

    # 画像ファイルを削除して連番を詰める
    folder = _image_folder(type_name)
    files  = _sorted_images(folder)

    if index - 1 < len(files):
        os.remove(os.path.join(folder, files[index - 1]))
        # 後続ファイルを繰り上げリネーム (一時名を経由してコンフリクト回避)
        subsequent = files[index:]
        tmp_paths = []
        for fname in subsequent:
            old = os.path.join(folder, fname)
            tmp = old + ".tmp"
            os.rename(old, tmp)
            tmp_paths.append(tmp)
        for i, tmp in enumerate(tmp_paths, start=index):
            os.rename(tmp, os.path.join(folder, f"{i:03d}.jpg"))

    _commit_and_push(f"delete: {type_name} index {index} by {username}")

    return jsonify({"success": True}), 200


# ---------------------------------------------------------------------------
# 起動
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
