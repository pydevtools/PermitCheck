# CI/CD Integration Guide

Integrate PermitCheck into your continuous integration pipelines.

## GitHub Actions

### Basic Integration

```yaml
name: License Check

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  license-compliance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install PermitCheck
        run: pip install permitcheck
      
      - name: Check License Compliance
        run: permitcheck -l python --format console
```

### With SARIF Upload

```yaml
name: License Security Check

on: [push, pull_request]

jobs:
  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install PermitCheck
        run: pip install permitcheck
      
      - name: Run License Check
        run: permitcheck -l python --format sarif -o results.sarif
        continue-on-error: true
      
      - name: Upload SARIF Results
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
          category: license-compliance
```

### With Artifact Upload

```yaml
name: License Report

on: [push, pull_request]

jobs:
  license-report:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install PermitCheck
        run: pip install permitcheck
      
      - name: Generate Reports
        run: |
          permitcheck -l python --format html -o license-report.html
          permitcheck -l python --format json -o license-report.json
          permitcheck -l python --format csv -o license-report.csv
      
      - name: Upload Reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: license-reports
          path: |
            license-report.html
            license-report.json
            license-report.csv
```

### Pull Request Comments

```yaml
name: License PR Comment

on: pull_request

jobs:
  license-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install PermitCheck
        run: pip install permitcheck
      
      - name: Generate Markdown Report
        run: |
          permitcheck -l python --format markdown -o report.md || true
      
      - name: Comment PR
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```

## GitLab CI

### Basic Integration

```yaml
license-check:
  image: python:3.12
  stage: test
  script:
    - pip install permitcheck
    - permitcheck -l python --format console
  allow_failure: false
```

### With Artifacts

```yaml
license-compliance:
  image: python:3.12
  stage: test
  script:
    - pip install permitcheck
    - permitcheck -l python --format json -o license-report.json
    - permitcheck -l python --format html -o license-report.html
  artifacts:
    reports:
      license_scanning: license-report.json
    paths:
      - license-report.html
    when: always
    expire_in: 30 days
```

### With Merge Request Integration

```yaml
license-check-mr:
  image: python:3.12
  stage: test
  script:
    - pip install permitcheck
    - permitcheck -l python --format markdown -o report.md
  artifacts:
    paths:
      - report.md
  only:
    - merge_requests
```

## Jenkins

### Declarative Pipeline

```groovy
pipeline {
    agent any
    
    stages {
        stage('License Check') {
            steps {
                sh '''
                    python3 -m pip install permitcheck
                    permitcheck -l python --format json -o license-report.json
                '''
            }
        }
        
        stage('Publish Report') {
            steps {
                archiveArtifacts artifacts: 'license-report.json'
                
                script {
                    def report = readJSON file: 'license-report.json'
                    if (report.summary.errors > 0) {
                        error("License compliance check failed with ${report.summary.errors} errors")
                    }
                }
            }
        }
    }
}
```

### With HTML Report

```groovy
pipeline {
    agent any
    
    stages {
        stage('License Check') {
            steps {
                sh '''
                    pip install permitcheck
                    permitcheck -l python --format html -o license-report.html
                '''
            }
        }
    }
    
    post {
        always {
            publishHTML([
                allowMissing: false,
                alwaysLinkToLastBuild: true,
                keepAll: true,
                reportDir: '.',
                reportFiles: 'license-report.html',
                reportName: 'License Compliance Report'
            ])
        }
    }
}
```

## CircleCI

```yaml
version: 2.1

jobs:
  license-check:
    docker:
      - image: cimg/python:3.12
    steps:
      - checkout
      - run:
          name: Install PermitCheck
          command: pip install permitcheck
      - run:
          name: Check License Compliance
          command: permitcheck -l python --format json -o license-report.json
      - store_artifacts:
          path: license-report.json
          destination: license-reports

workflows:
  main:
    jobs:
      - license-check
```

## Travis CI

```yaml
language: python
python:
  - "3.12"

install:
  - pip install permitcheck

script:
  - permitcheck -l python --format console

after_success:
  - permitcheck -l python --format html -o license-report.html

deploy:
  provider: pages
  skip_cleanup: true
  local_dir: .
  github_token: $GITHUB_TOKEN
  on:
    branch: main
```

## Azure Pipelines

```yaml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
- task: UsePythonVersion@0
  inputs:
    versionSpec: '3.12'
  
- script: |
    pip install permitcheck
    permitcheck -l python --format sarif -o results.sarif
  displayName: 'License Compliance Check'
  
- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: 'results.sarif'
    artifactName: 'license-results'
```

## Bitbucket Pipelines

```yaml
pipelines:
  default:
    - step:
        name: License Check
        image: python:3.12
        script:
          - pip install permitcheck
          - permitcheck -l python --format console
        artifacts:
          - license-report.*
```

## Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: permitcheck
        name: License Compliance Check
        entry: permitcheck -l python --format console
        language: system
        pass_filenames: false
        always_run: true
```

## Docker Integration

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt permitcheck

COPY . .

RUN permitcheck -l python --format json -o /tmp/license-report.json

CMD ["python", "app.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  license-check:
    image: python:3.12
    volumes:
      - .:/app
    working_dir: /app
    command: >
      sh -c "pip install permitcheck &&
             permitcheck -l python --format html -o reports/license.html"
```

## Best Practices

### 1. Fail Fast

```yaml
- name: License Check
  run: permitcheck -l python --format console
  # Will fail pipeline if license violations found
```

### 2. Non-Blocking Checks

```yaml
- name: License Check (Warning Only)
  run: permitcheck -l python --format console
  continue-on-error: true
```

### 3. Generate Multiple Reports

```bash
#!/bin/bash
set -e

# Console for logs
permitcheck -l python --format console

# JSON for automation
permitcheck -l python --format json -o license-report.json

# HTML for humans
permitcheck -l python --format html -o license-report.html

# SARIF for security tools
permitcheck -l python --format sarif -o results.sarif
```

### 4. Cache Dependencies

```yaml
- name: Cache PermitCheck
  uses: actions/cache@v3
  with:
    path: ~/.permitcheck
    key: permitcheck-${{ hashFiles('**/requirements.txt') }}
```

### 5. Scheduled Audits

```yaml
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
```

## Exit Codes

- `0` - Success (all licenses compliant)
- `1` - Failure (license violations found)

Use in scripts:

```bash
if ! permitcheck -l python --format console; then
    echo "License compliance check failed!"
    exit 1
fi
```

## Next Steps

- Review [Output Formats](output-formats.md)
- Explore [API Reference](api-reference.md)
- Check [Configuration](configuration.md)
