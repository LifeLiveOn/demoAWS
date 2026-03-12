docker build -t flask-linktree-demo .
docker run -p 8080:8080 --env-file .env flask-linktree-demo