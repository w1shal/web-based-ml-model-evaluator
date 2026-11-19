# CI/CD and release deployment

GitHub Actions runs lint, type checks, tests and coverage before building the API image and frontend. The Docker job packages both with a Compose deployment, extracts the archive into a fresh directory, starts the stack, and verifies the frontend, algorithm list and evaluation API schema over HTTPS. Each successful build delivers a commit-labelled archive under the run's Artifacts tab for seven days. A pull-request run uses GitHub's test merge commit. A push to main builds the merged release.

## Demonstrate the pipeline

Open Actions → CI/CD Pipeline → a successful run. Open the Docker job and expand “Deploy and verify the release on the runner”. The staging stack runs for the smoke tests and is removed afterwards. Download the evaluator-release artifact for a local demonstration. The package contains no generated keys or runtime database.

## Run the delivered version

On a machine with Docker Compose, a POSIX shell and OpenSSL, unzip the downloaded artifact, then run the following commands from the folder containing evaluator-release.tar.gz. Ports 80 and 443 must be available.

```sh
mkdir evaluator-release
tar -xzf evaluator-release.tar.gz -C evaluator-release
cd evaluator-release
gzip -dc api-image.tar.gz | docker load
cp .env.example .env
sed -i.bak "s/^JWT_SECRET=.*/JWT_SECRET=$(openssl rand -hex 32)/" .env
echo "API_TAG=$(cat REVISION)" >> .env
sh deploy/gen-dev-cert.sh
docker compose up -d
```

Open https://localhost and accept the local development certificate. Use a trusted certificate for a public hostname. For subsequent releases, retain the signing secret, Compose project name and data volume. Stop the stack with `docker compose down`. To roll back application binaries, load the previous release image and use its frontend assets and revision with the existing environment. Check database compatibility first.

This implements continuous delivery with temporary staging on the Actions runner. Deployment to a persistent hosting account requires a separately configured destination.
