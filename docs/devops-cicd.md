# A.14 DevOps and CI/CD

## Overview
The Ticket Tracking System uses GitHub Actions for Continuous Integration and Continuous Deployment (CI/CD). This document describes the automated pipeline that builds, tests, and deploys the code, enabling frequent and reliable releases.

## CI/CD Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Developer                                │
│                              │                                   │
│                              ▼                                   │
│                      Commits to GitHub                           │
└─────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Actions Triggered                      │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Code Checkout  │→ │  Dependencies   │→ │   Run Tests     │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│                                                      │            │
│                                                      ▼            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │  Build Images   │← │   Lint Code     │← │  Code Quality   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
│           │                                                       │
└───────────┼───────────────────────────────────────────────────────┘
            │
            ▼
┌─────────────────────────────────────────────────────────────────┐
│                  Deploy to Railway (Production)                  │
│                                                                   │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐ │
│  │ Service Deploy  │→ │ Health Checks   │→ │ Rollback/Done   │ │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Current GitHub Actions Workflows

### 1. Auth Test Suite
**File**: `.github/workflows/auth-tests.yml`

**Trigger**: Push and Pull Request events

**Purpose**: Validates authentication service functionality

**Steps**:
1. **Checkout Repository**: Uses `actions/checkout@v4`
2. **Setup Python 3.11**: Uses `actions/setup-python@v5`
3. **Install Dependencies**: `pip install -r requirements.txt`
4. **Run Tests**: `python manage.py test users.tests`

**Configuration**:
```yaml
name: Auth Test Suite
on:
  push:
  pull_request:
jobs:
  auth-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: auth
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      - name: Run authentication test suite
        run: python manage.py test users.tests
```

## Pipeline Stages Explained

### Stage 1: Code Checkout
- **Tool**: `actions/checkout@v4`
- **Purpose**: Clones the repository with full history
- **Configuration**: Default settings retrieve full repository
- **Duration**: ~5-10 seconds

### Stage 2: Environment Setup
- **Python Services**: `actions/setup-python@v5` with Python 3.11
- **Node.js Frontend**: `actions/setup-node@v4` with Node.js 18+
- **Caching**: Dependencies cached to speed up subsequent runs
- **Duration**: ~15-30 seconds (with cache), ~2-3 minutes (without cache)

### Stage 3: Dependency Installation
- **Backend**: `pip install -r requirements.txt`
- **Frontend**: `npm ci` (clean install from package-lock.json)
- **Benefits**: Reproducible builds, faster installation
- **Duration**: ~30-60 seconds (with cache)

### Stage 4: Code Quality Checks

#### Linting
- **Python**: `flake8` or `pylint` (planned)
- **JavaScript**: `eslint` (configured in frontend)
- **Configuration**: `.eslintrc` or `setup.cfg`

#### Code Formatting
- **Python**: `black` (planned)
- **JavaScript**: `prettier` (planned)

#### Static Analysis
- **Python**: `mypy` for type checking (planned)
- **Security**: `bandit` for security issues (planned)

### Stage 5: Automated Testing

#### Unit Tests
- **Backend**: Django's `manage.py test`
- **Frontend**: `npm test` with Jest/Vitest
- **Coverage**: Code coverage reports generated

#### Integration Tests
- **Database**: Uses SQLite in-memory or PostgreSQL container
- **Services**: Mock external service dependencies
- **Fixtures**: Test data loaded from fixtures

#### End-to-End Tests
- **Tool**: Playwright or Cypress (planned)
- **Scope**: Critical user workflows
- **Browser**: Headless Chrome/Firefox

### Stage 6: Build Artifacts

#### Docker Image Building
```bash
docker build -t service-name:${{ github.sha }} .
docker tag service-name:${{ github.sha }} service-name:latest
```

#### Frontend Build
```bash
npm run build
# Creates optimized production bundle in dist/
```

### Stage 7: Deployment

#### Railway Deployment
- **Method**: Git-based deployment (automatic)
- **Trigger**: Push to `main` or `production` branch
- **Process**:
  1. Railway detects git push
  2. Builds Docker image from Dockerfile
  3. Runs health checks
  4. Routes traffic to new deployment
  5. Keeps old deployment running during transition
  6. Automatic rollback if health checks fail

#### Manual Deployment (Alternative)
```bash
# Using Railway CLI
railway up
```

## Environment-Specific Configuration

### Development Branch
- **Branch**: `develop` or feature branches
- **Actions**: Run tests, linting
- **Deployment**: No automatic deployment
- **Notifications**: GitHub PR comments

### Staging Branch
- **Branch**: `staging`
- **Actions**: Full CI/CD pipeline
- **Deployment**: Auto-deploy to staging environment
- **Notifications**: Slack/Email on deployment

### Production Branch
- **Branch**: `main` or `production`
- **Actions**: Full CI/CD with additional security scans
- **Deployment**: Auto-deploy to production (Railway)
- **Approval**: Optional manual approval gate
- **Notifications**: Multiple channels (Slack, Email, PagerDuty)

## Automation Scripts

### Docker Initialization Script
**Location**: `Scripts/docker.sh`

**Purpose**: Automate local development environment setup

**Operations**:
1. Create `.env` files from templates
2. Build Docker images
3. Start containers with docker-compose
4. Run database migrations
5. Seed initial data

**Usage**:
```bash
bash ./Scripts/docker.sh
```

### Service Entrypoint Scripts
Each service has an `entrypoint.sh` or `start.sh` script:

**Example** (`auth/entrypoint.sh`):
```bash
#!/bin/bash
set -e  # Exit on error

echo "Running database migrations..."
python manage.py makemigrations
python manage.py migrate

echo "Seeding initial data..."
python manage.py seed_systems --force
python manage.py seed_tts --force
python manage.py seed_accounts --force

echo "Starting Django server..."
python manage.py runserver 0.0.0.0:8000
```

### Database Initialization
**Location**: `Docker/db-init/`

**Purpose**: Create multiple logical databases in single PostgreSQL instance

**Script Example**:
```sql
-- Create databases
CREATE DATABASE authservice;
CREATE DATABASE ticketmanagement;
CREATE DATABASE workflowmanagement;
CREATE DATABASE messagingservice;
CREATE DATABASE notificationservice;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE authservice TO postgres;
GRANT ALL PRIVILEGES ON DATABASE ticketmanagement TO postgres;
-- ... etc
```

## Testing Strategy

### Test Pyramid

```
         ▲
        /│\
       / │ \
      /  │  \     E2E Tests (10%)
     /   │   \    - Critical user workflows
    /────┼────\   - Browser automation
   /     │     \
  /      │      \ Integration Tests (30%)
 /       │       \- Service interaction
/────────┼────────\- Database operations
         │
    Unit Tests (60%)
    - Business logic
    - Model validation
    - Serializers
```

### Test Execution
- **Local**: `python manage.py test` or `npm test`
- **CI**: Automated on every push
- **Coverage Goal**: >80% code coverage

### Test Database
- **CI Environment**: PostgreSQL service container
- **Configuration**:
  ```yaml
  services:
    postgres:
      image: postgres:15
      env:
        POSTGRES_PASSWORD: testpass
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
  ```

## Continuous Monitoring

### Health Checks
Each service implements health check endpoints:
```python
@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'auth-service',
        'version': '1.0.0'
    })
```

### Performance Monitoring
- **Tool**: Railway built-in monitoring
- **Metrics**: CPU, Memory, Response time, Error rate
- **Alerts**: Configured thresholds trigger notifications

### Log Aggregation
- **Development**: Docker logs (`docker logs <container>`)
- **Production**: Railway log aggregation
- **External**: Sentry for error tracking (planned)

## Deployment Strategies

### Current: Rolling Deployment
- **Description**: Gradually replace old instances with new ones
- **Downtime**: Zero-downtime deployment
- **Rollback**: Automatic if health checks fail
- **Risk**: Low

### Planned: Blue-Green Deployment
- **Description**: Maintain two identical environments
- **Process**:
  1. Deploy to "Green" (inactive) environment
  2. Run smoke tests
  3. Switch traffic from "Blue" to "Green"
  4. Keep "Blue" as rollback option
- **Benefits**: Instant rollback, safe testing
- **Cost**: Higher (requires duplicate resources)

### Planned: Canary Deployment
- **Description**: Gradually route traffic to new version
- **Process**:
  1. Deploy new version alongside old
  2. Route 10% traffic to new version
  3. Monitor metrics
  4. Gradually increase to 100%
- **Benefits**: Early detection of issues
- **Complexity**: Requires sophisticated routing

## CI/CD Best Practices

### 1. Keep Builds Fast
- **Target**: <5 minutes for CI pipeline
- **Strategies**:
  - Cache dependencies
  - Parallel test execution
  - Incremental builds
  - Optimize Docker layers

### 2. Fail Fast
- **Order**: Fastest tests first (linting → unit → integration → e2e)
- **Early Exit**: Stop pipeline on first failure
- **Quick Feedback**: Developers notified immediately

### 3. Reproducible Builds
- **Lock Files**: `requirements.txt` with pinned versions
- **Docker**: Specify exact base image versions
- **Deterministic**: Same input → same output

### 4. Automated Rollbacks
- **Health Checks**: Automated checks after deployment
- **Failure Detection**: <1 minute to detect issues
- **Rollback**: Automatic revert to previous version

### 5. Security in Pipeline
- **Dependency Scanning**: Check for known vulnerabilities
- **Secret Management**: Use GitHub Secrets, never commit secrets
- **Image Scanning**: Scan Docker images for vulnerabilities

## Future CI/CD Enhancements

### Planned Improvements
- [ ] **Multi-stage builds**: Reduce Docker image size
- [ ] **Parallel testing**: Run tests across multiple services simultaneously
- [ ] **Automated database migrations**: Test migrations in CI before production
- [ ] **Performance testing**: Load testing in staging environment
- [ ] **Security scanning**: SAST/DAST tools integrated
- [ ] **Code coverage reports**: Publish to Codecov or similar
- [ ] **Deployment previews**: Auto-deploy PRs to preview environments
- [ ] **Slack/Discord notifications**: Real-time deployment status
- [ ] **Automated changelog**: Generate from commit messages
- [ ] **Release management**: Semantic versioning and release notes

### Advanced Workflows
- [ ] **Matrix builds**: Test across multiple Python/Node versions
- [ ] **Scheduled jobs**: Nightly builds and tests
- [ ] **Dependency updates**: Automated Dependabot PRs
- [ ] **Container registry**: Push images to Docker Hub/GHCR
- [ ] **Infrastructure as Code**: Terraform for Railway resources

## Troubleshooting CI/CD

### Common Issues

#### 1. Build Failures
**Symptom**: Tests pass locally but fail in CI

**Causes**:
- Environment differences
- Missing dependencies
- Database state issues

**Solutions**:
- Match local Python/Node versions to CI
- Check for missing system dependencies
- Ensure clean database state for tests

#### 2. Slow Builds
**Symptom**: CI pipeline takes >10 minutes

**Solutions**:
- Enable dependency caching
- Parallelize independent jobs
- Optimize Docker layer caching
- Remove unnecessary test fixtures

#### 3. Deployment Failures
**Symptom**: Deployment succeeds but app doesn't work

**Causes**:
- Missing environment variables
- Database migration issues
- Service dependencies not met

**Solutions**:
- Verify all environment variables set
- Run migrations before deployment
- Check service health endpoints

## Metrics and KPIs

### Key Performance Indicators
- **Build Time**: Target <5 minutes
- **Test Coverage**: Target >80%
- **Deployment Frequency**: Daily to main branch
- **Lead Time**: <1 hour from commit to production
- **Mean Time to Recovery (MTTR)**: <15 minutes
- **Change Failure Rate**: <5%

### Current Metrics
- Build Time: ~3 minutes (auth tests)
- Test Coverage: Variable by service
- Deployment Frequency: On-demand
- Lead Time: ~10-15 minutes

## Resources

### Documentation
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Railway Documentation](https://docs.railway.app/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)

### Tools
- **GitHub Actions**: CI/CD automation
- **Railway**: Cloud deployment platform
- **Docker**: Containerization
- **PostgreSQL**: Database
- **RabbitMQ**: Message queue
