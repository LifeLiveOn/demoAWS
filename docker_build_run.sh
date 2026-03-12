docker build -t flask-linktree-demo .
docker run -p 8000:8000 --env-file .env flask-linktree-demo