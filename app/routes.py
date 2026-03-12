import os
from boto3.dynamodb.conditions import Key
import uuid
from flask import Blueprint, request, redirect, url_for, render_template, flash
from werkzeug.utils import secure_filename
from app.aws import users_table, links_table, s3

routes = Blueprint('routes', __name__)


def upload_profile_image(file, username):
    bucket_name = os.getenv("S3_BUCKET_NAME")
    if not bucket_name:
        return None, "S3 bucket is not configured. Set S3_BUCKET_NAME."

    filename = secure_filename(file.filename)
    key = f"profile-images/{username}/{uuid.uuid4()}-{filename}"

    s3.upload_fileobj(
        file,
        bucket_name,
        key,
        ExtraArgs={
            "ContentType": file.mimetype or "application/octet-stream"
        }
    )

    return key, None


@routes.route('/')
def home():
    return render_template('home.html')


@routes.route('/register', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        username = request.form['username']
        bio = request.form["bio"]

        item = {
            'username': username,
            'bio': bio
        }

        profile_image = request.files.get("profile_image")
        if profile_image and profile_image.filename:
            try:
                image_key, upload_error = upload_profile_image(
                    profile_image, username)
                if upload_error:
                    flash(upload_error, "warning")
                elif image_key:
                    item['profile_image_key'] = image_key
            except Exception:
                flash("Profile image upload failed.", "danger")

        users_table.put_item(Item=item)

        return redirect(f"/{username}")
    return render_template('create_profile.html')


@routes.route('/<username>')
def profile(username):

    user = users_table.get_item(Key={'username': username}).get('Item')

    if user and user.get('profile_image_key'):
        bucket_name = os.getenv("S3_BUCKET_NAME")
        if bucket_name:
            user['profile_image_url'] = s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': user['profile_image_key']
                },
                ExpiresIn=3600
            )

    links = links_table.query(
        KeyConditionExpression=Key("username").eq(username)
    )

    return render_template('profile.html', user=user, links=links.get('Items', []))


@routes.route('/<username>/edit', methods=['GET', 'POST'])
def edit_profile(username):
    user = users_table.get_item(Key={'username': username}).get('Item')

    if not user:
        flash("Profile not found.", "danger")
        return redirect(url_for('routes.home'))

    if request.method == 'POST':
        bio = request.form["bio"]
        expression_attribute_names = {
            '#bio': 'bio'
        }
        expression_attribute_values = {
            ':bio': bio
        }
        update_expression = "SET #bio = :bio"

        profile_image = request.files.get("profile_image")
        if profile_image and profile_image.filename:
            try:
                image_key, upload_error = upload_profile_image(
                    profile_image, username)
                if upload_error:
                    flash(upload_error, "warning")
                elif image_key:
                    expression_attribute_names['#profile_image_key'] = 'profile_image_key'
                    expression_attribute_values[':profile_image_key'] = image_key
                    update_expression += ", #profile_image_key = :profile_image_key"
            except Exception:
                flash("Profile image upload failed.", "danger")

        users_table.update_item(
            Key={'username': username},
            UpdateExpression=update_expression,
            ExpressionAttributeNames=expression_attribute_names,
            ExpressionAttributeValues=expression_attribute_values
        )

        flash("Profile updated successfully!", "success")
        return redirect(f"/{username}")

    if user.get('profile_image_key'):
        bucket_name = os.getenv("S3_BUCKET_NAME")
        if bucket_name:
            user['profile_image_url'] = s3.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': bucket_name,
                    'Key': user['profile_image_key']
                },
                ExpiresIn=3600
            )

    return render_template('edit_profile.html', user=user)


@routes.route('/<username>/links', methods=['GET', 'POST'])
def add_links(username):
    if request.method == "POST":

        title = request.form["title"]
        url = request.form["url"]

        links_table.put_item(
            Item={
                "username": username,
                "link_id": str(uuid.uuid4()),
                "title": title,
                "url": url
            }
        )
        flash("Link posted successfully!", "success")

        return redirect(f"/{username}/links")

    links = links_table.query(
        KeyConditionExpression=Key("username").eq(username)
    )
    return render_template("add_links.html", username=username, links=links.get('Items', []))


@routes.route('/<username>/links/<link_id>/edit', methods=['GET', 'POST'])
def edit_link(username, link_id):
    link = links_table.get_item(Key={
        'username': username,
        'link_id': link_id
    }).get('Item')

    if not link:
        flash("Link not found.", "danger")
        return redirect(f"/{username}/links")

    if request.method == 'POST':
        title = request.form["title"]
        url = request.form["url"]

        links_table.update_item(
            Key={
                'username': username,
                'link_id': link_id
            },
            UpdateExpression="SET #title = :title, #url = :url",
            ExpressionAttributeNames={
                '#title': 'title',
                '#url': 'url'
            },
            ExpressionAttributeValues={
                ':title': title,
                ':url': url
            }
        )

        flash("Link updated successfully!", "success")
        return redirect(f"/{username}/links")

    return render_template('edit_link.html', username=username, link=link)
