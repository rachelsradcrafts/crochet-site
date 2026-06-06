import os
import re
from datetime import date
from pathlib import Path

from flask import Flask, abort, redirect, render_template, request, url_for
from werkzeug.utils import secure_filename


BASE_DIR = Path(__file__).resolve().parent
PUBLIC_DIR = BASE_DIR / "public"
IMAGES_ROOT = PUBLIC_DIR / "images"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif"}


def create_app() -> Flask:
    app = Flask(
        __name__,
        static_folder=str(PUBLIC_DIR),
        static_url_path="",
    )

    app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024

    #enable_admin = os.environ.get("ENABLE_ADMIN") == "1"
    enable_admin = True

    @app.get("/")
    def index():
        return render_template("index.html", items=gallery_items())

    if enable_admin:
        register_admin_routes(app)
    else:
        @app.route("/admin")
        @app.route("/admin/<path:_path>")
        def admin_disabled(_path=None):
            abort(404)

    return app


def register_admin_routes(app: Flask) -> None:
    @app.get("/admin")
    def admin():
        return render_template("admin.html", items=gallery_items())

    @app.get("/admin/new")
    def new_item_form():
        return render_template("new_item.html", today=date.today().isoformat())

    @app.post("/admin/new")
    def create_item():
        name = request.form.get("name", "").strip()
        price = request.form.get("price", "").strip()
        sort_date = request.form.get("sort_date", "").strip()

        if not name:
            abort(400, "Item name is required.")

        folder_name = slug_from_name(name)
        item_dir = IMAGES_ROOT / folder_name

        if item_dir.exists():
            abort(400, f"An item folder already exists for {folder_name!r}.")

        item_dir.mkdir(parents=True)

        write_text(item_dir / "price.txt", normalize_price(price))
        write_text(item_dir / "date.txt", sort_date or date.today().isoformat())

        uploaded_files = request.files.getlist("images")
        image_count = 0

        for uploaded in uploaded_files:
            if not uploaded.filename:
                continue

            original_name = secure_filename(uploaded.filename)
            ext = Path(original_name).suffix.lower()

            if ext not in ALLOWED_EXTENSIONS:
                continue

            image_count += 1
            output_name = f"{image_count:03d}{ext}"
            uploaded.save(item_dir / output_name)

        if image_count == 0:
            abort(400, "At least one valid image is required.")

        return redirect(url_for("admin"))


def gallery_items() -> list[dict]:
    if not IMAGES_ROOT.exists():
        return []

    items = []

    for entry in sorted(IMAGES_ROOT.iterdir()):
        if not entry.is_dir():
            continue

        images = sorted(
            [
                file.name
                for file in entry.iterdir()
                if file.is_file() and file.suffix.lower() in ALLOWED_EXTENSIONS
            ],
            key=natural_sort_key,
        )

        if not images:
            continue

        items.append(
            {
                "id": id_from_folder(entry.name),
                "name": display_name_from_folder(entry.name),
                "folder": entry.name,
                "price": read_price(entry),
                "sort_date": read_date(entry),
                "images": images,
            }
        )

    return items


def display_name_from_folder(folder_name: str) -> str:
    return re.sub(r"[-_]+", " ", folder_name).title()


def id_from_folder(folder_name: str) -> str:
    value = folder_name.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def slug_from_name(name: str) -> str:
    value = name.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    return value or "item"


def read_price(folder_path: Path) -> str:
    price_file = folder_path / "price.txt"

    if not price_file.exists():
        return "Price TBD"

    price = price_file.read_text(encoding="utf-8").strip()

    if not price:
        return "Price TBD"

    if price.startswith("$"):
        return price

    return "$" + price


def normalize_price(price: str) -> str:
    price = price.strip()

    if not price:
        return "Price TBD"

    if price.startswith("$"):
        return price

    return "$" + price


def read_date(folder_path: Path) -> str:
    date_file = folder_path / "date.txt"

    if not date_file.exists():
        return "1900-01-01"

    value = date_file.read_text(encoding="utf-8").strip()
    return value or "1900-01-01"


def write_text(path: Path, value: str) -> None:
    path.write_text(value + "\n", encoding="utf-8")


def natural_sort_key(value: str):
    return [
        int(part) if part.isdigit() else part.lower()
        for part in re.split(r"(\d+)", value)
    ]


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=2000, debug=True)