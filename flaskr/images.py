from PIL import Image
import imagehash
import io
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from flaskr.db import get_db
from base64 import b64encode


bp = Blueprint('images', __name__, url_prefix='/images')


@bp.route('/dataset', methods=('GET', 'POST'))
def dataset():
    if request.method == 'POST':
        file = request.files['image']
        title = request.form['title']
        db = get_db()
        error = None

        if not file:
            error = 'Image is required.'
        elif not title:
            error = 'Title is required.'
        elif db.execute(
                'SELECT id FROM images WHERE title = ?', (title,)
        ).fetchone() is not None:
            error = 'Image {} is already registered.'.format(title)

        if error is None:
            img = Image.open(file)
            hash = str(imagehash.phash(img))

            stream = io.BytesIO()
            img.save(stream, format="JPEG")

            db.execute(
                'INSERT INTO images (title, hash, image) VALUES (?, ?, ?)',
                (title, hash, stream.getvalue())
            )
            db.commit()
            return redirect(url_for('images.dataset'))

        flash(error)

    if request.method == 'GET':
        images = get_db().execute('SELECT * FROM images').fetchall()
        transformed_images = []
        for image in images:
            transformed_image = {}
            transformed_image['title'] = image["title"]
            transformed_image['hash'] = image["hash"]
            transformed_image['image'] = b64encode(image["image"]).decode("utf-8")
            transformed_images.append(transformed_image)
        g.images = transformed_images
        return render_template('images/dataset.html')


@bp.route('/test', methods=('GET', 'POST'))
def test():
    if request.method == 'POST':
        file = request.files['image']

        db = get_db()
        error = None

        if not file:
            error = 'Image is required.'

        if error is None:
            img = Image.open(file)
            hash = str(imagehash.phash(img))

            images = db.execute(
                'SELECT * FROM images'
            ).fetchall()

            differences = []
            for image in images:
                difference = {}
                difference["title"] = image["title"]
                difference["difference"] = imagehash.hex_to_hash(hash) - imagehash.hex_to_hash(image['hash'])
                differences.append(difference)

            session.clear()
            session['filename'] = file.filename
            session['differences'] = differences

            return redirect(url_for('images.test'))

        flash(error)

    g.differences = session.get('differences')
    g.filename = session.get('filename')
    return render_template('images/test.html')
