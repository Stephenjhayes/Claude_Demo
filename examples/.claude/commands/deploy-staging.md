# Deploy to Staging

Deploy the current branch to the staging environment safely.

## Pre-flight Checks
1. Confirm we're NOT on `main` or `production` branch
2. Run `npm run build` — abort if it fails
3. Run `npm run test` — abort if any tests fail
4. Run `npm run lint` — warn but don't abort

## Deployment Steps
1. Build the Docker image: `docker build -t myapp:staging .`
2. Run database migrations: `npm run db:migrate -- --env staging`
3. Deploy to staging server: `./scripts/deploy.sh staging`
4. Wait 30 seconds, then health check: `curl https://staging.myapp.com/health`

## Post-Deploy Verification
- Check the health endpoint returns `{ "status": "ok" }`
- Verify the deploy timestamp updated: `curl https://staging.myapp.com/version`
- Report the staging URL and any migration output

## On Failure
If any step fails, capture the error output, roll back the deployment using `./scripts/rollback.sh staging`, and report what went wrong with suggestions for fixing it.
