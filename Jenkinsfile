// =============================================================================
// Jenkinsfile — Declarative CI/CD Pipeline
// MLOps Fraud Detection — Data Science → Production Pipeline
//
// Pipeline Stages:
//   1. Checkout Code
//   2. Static Analysis & Security Scan  (Bandit)
//   3. Unit Tests                        (pytest)
//   4. Build Docker Image                (multi-stage)
//   5. Push to Local Registry            (localhost:5000)
//   6. Deploy to Kubernetes              (kubectl apply)
//   7. Smoke Test                        (curl /predict)
//   8. Post-pipeline notifications
//
// Prerequisites on the Jenkins controller container:
//   - Docker CLI available (mount /var/run/docker.sock)
//   - kubectl configured with kubeconfig mounted at /root/.kube/config
//   - A local Docker registry running at localhost:5000
//     (docker run -d -p 5000:5000 --name registry registry:2)
//   - Python 3.10+ available (or use the provided agent Docker image)
//
// Jenkins Job Configuration:
//   - Type: Pipeline
//   - SCM: Git → point to this repository
//   - Script Path: Jenkinsfile
// =============================================================================

pipeline {

    agent any

    // ── Environment Variables ─────────────────────────────────────────────────
    environment {
        // Docker image name and tag strategy: <name>:<build-number>
        IMAGE_NAME        = "fraud-detection-api"
        IMAGE_TAG         = "${BUILD_NUMBER}"
        IMAGE_FULL        = "localhost:5000/${IMAGE_NAME}:${IMAGE_TAG}"
        IMAGE_LATEST      = "localhost:5000/${IMAGE_NAME}:latest"

        // Kubernetes namespace and deployment name (must match deployment.yaml)
        K8S_NAMESPACE     = "mlops"
        K8S_DEPLOYMENT    = "fraud-detection-deployment"
        K8S_CONTAINER     = "fraud-detection-api"

        // Minikube NodePort for the post-deploy smoke test
        MINIKUBE_IP       = sh(script: "minikube ip 2>/dev/null || echo '192.168.49.2'", returnStdout: true).trim()
        APP_NODEPORT      = "30800"

        // Python virtual environment path (keeps the workspace clean)
        VENV_DIR          = "${WORKSPACE}/.venv"

        // Bandit output report path
        BANDIT_REPORT     = "${WORKSPACE}/bandit-report.json"

        // Pytest output report path
        PYTEST_REPORT     = "${WORKSPACE}/pytest-report.xml"
    }

    // ── Pipeline Options ──────────────────────────────────────────────────────
    options {
        // Maximum total build time — prevents stuck builds from blocking agents
        timeout(time: 30, unit: 'MINUTES')

        // Keep only the last 10 build logs to conserve disk space
        buildDiscarder(logRotator(numToKeepStr: '10'))

        // Add timestamps to all console log lines
        timestamps()

        // Do not allow concurrent builds of the same job (prevents race
        // conditions on Kubernetes deployments)
        disableConcurrentBuilds()
    }

    // ── Triggers ──────────────────────────────────────────────────────────────
    triggers {
        // Poll the SCM every 5 minutes for new commits
        // Replace with a GitHub/GitLab webhook for production environments.
        pollSCM('H/5 * * * *')
    }

    // ── Pipeline Stages ───────────────────────────────────────────────────────
    stages {

        // ── Stage 1: Checkout ─────────────────────────────────────────────────
        stage('1 · Checkout Code') {
            steps {
                echo "━━━ Stage 1: Checkout Code ━━━"
                checkout scm
                script {
                    // Capture the short Git SHA for image labelling
                    env.GIT_SHORT_SHA = sh(
                        script: "git rev-parse --short HEAD",
                        returnStdout: true
                    ).trim()
                    echo "Branch: ${env.GIT_BRANCH ?: 'unknown'} | Commit: ${env.GIT_SHORT_SHA}"
                }
            }
        }

        // ── Stage 2: Static Analysis & Security Scan ─────────────────────────
        stage('2 · Static Analysis & Security Scan') {
            steps {
                echo "━━━ Stage 2: Static Analysis & Security Scan (Bandit) ━━━"
                sh """
                    # Create or reuse the virtual environment
                    if [ ! -d "${VENV_DIR}" ]; then
                        python3 -m venv ${VENV_DIR}
                    fi

                    # Activate venv and install dependencies
                    . ${VENV_DIR}/bin/activate
                    pip install --quiet --upgrade pip
                    pip install --quiet -r requirements.txt

                    echo "Running Bandit SAST scan on app/ directory…"
                    bandit \
                        --recursive app/ \
                        --format json \
                        --output ${BANDIT_REPORT} \
                        --severity-level medium \
                        --confidence-level medium \
                        --exit-zero \
                    || true

                    # Parse the report and fail if any HIGH severity issues exist
                    HIGH_COUNT=\$(python3 -c "
import json, sys
try:
    with open('${BANDIT_REPORT}') as f:
        report = json.load(f)
    high = [r for r in report.get('results', []) if r['issue_severity'] == 'HIGH']
    print(len(high))
except Exception as e:
    print('0')
")
                    echo "Bandit HIGH severity issues found: \${HIGH_COUNT}"

                    if [ "\${HIGH_COUNT}" -gt "0" ]; then
                        echo "ERROR: Bandit detected \${HIGH_COUNT} HIGH severity issue(s)."
                        echo "Review ${BANDIT_REPORT} and resolve issues before merging."
                        exit 1
                    fi

                    echo "Security scan passed — no HIGH severity issues detected."
                """
            }
            post {
                always {
                    // Archive the Bandit JSON report as a build artifact
                    archiveArtifacts artifacts: 'bandit-report.json', allowEmptyArchive: true
                }
            }
        }

        // ── Stage 3: Unit Tests ───────────────────────────────────────────────
        stage('3 · Unit Tests') {
            steps {
                echo "━━━ Stage 3: Unit Tests (pytest) ━━━"
                sh """
                    . ${VENV_DIR}/bin/activate

                    echo "Running pytest suite…"
                    pytest tests/ \
                        --verbose \
                        --tb=short \
                        --junit-xml=${PYTEST_REPORT} \
                        --no-header \
                        -rN
                """
            }
            post {
                always {
                    // Publish JUnit XML results to the Jenkins test results dashboard
                    junit allowEmptyResults: false, testResults: 'pytest-report.xml'
                }
                failure {
                    echo "ERROR: Unit tests failed. Docker build will not proceed."
                }
            }
        }

        // ── Stage 4: Build Docker Image ───────────────────────────────────────
        stage('4 · Build Docker Image') {
            steps {
                echo "━━━ Stage 4: Build Docker Image ━━━"
                sh """
                    echo "Building image: ${IMAGE_FULL}"

                    docker build \
                        --platform linux/amd64 \
                        --tag ${IMAGE_FULL} \
                        --tag ${IMAGE_LATEST} \
                        --label "git.sha=${GIT_SHORT_SHA}" \
                        --label "build.number=${BUILD_NUMBER}" \
                        --label "build.url=${BUILD_URL}" \
                        --file Dockerfile \
                        .

                    echo "Docker image built successfully:"
                    docker image inspect ${IMAGE_FULL} \
                        --format '  ID: {{.Id}}\\n  Size: {{.Size}} bytes\\n  Created: {{.Created}}'
                """
            }
        }

        // ── Stage 5: Push to Local Registry ──────────────────────────────────
        stage('5 · Push to Local Registry') {
            steps {
                echo "━━━ Stage 5: Push to Local Registry (localhost:5000) ━━━"
                sh """
                    # Verify the local registry is reachable before pushing
                    echo "Checking registry availability…"
                    curl --silent --fail http://localhost:5000/v2/_catalog \
                        || { echo "ERROR: Local registry at localhost:5000 is not reachable."; exit 1; }

                    echo "Pushing ${IMAGE_FULL}…"
                    docker push ${IMAGE_FULL}

                    echo "Pushing ${IMAGE_LATEST}…"
                    docker push ${IMAGE_LATEST}

                    echo "Images pushed successfully."
                    curl --silent http://localhost:5000/v2/${IMAGE_NAME}/tags/list
                """
            }
        }

        // ── Stage 6: Deploy to Kubernetes ────────────────────────────────────
        stage('6 · Deploy to Kubernetes') {
            steps {
                echo "━━━ Stage 6: Deploy to Kubernetes (Minikube) ━━━"
                sh """
                    # Ensure the namespace exists (idempotent)
                    kubectl get namespace ${K8S_NAMESPACE} 2>/dev/null \
                        || kubectl create namespace ${K8S_NAMESPACE}

                    # Apply the full manifest (Deployment, Service, HPA)
                    echo "Applying Kubernetes manifests…"
                    kubectl apply -f deployment.yaml --namespace=${K8S_NAMESPACE}

                    # Update the container image to the exact build-tagged version
                    # This ensures the rollout uses the immutable image digest, not :latest
                    echo "Updating container image to ${IMAGE_FULL}…"
                    kubectl set image deployment/${K8S_DEPLOYMENT} \
                        ${K8S_CONTAINER}=${IMAGE_FULL} \
                        --namespace=${K8S_NAMESPACE}

                    # Record the change for rollout history
                    kubectl annotate deployment/${K8S_DEPLOYMENT} \
                        kubernetes.io/change-cause="Jenkins build #${BUILD_NUMBER} | commit ${GIT_SHORT_SHA}" \
                        --overwrite \
                        --namespace=${K8S_NAMESPACE}

                    # Block the pipeline until the rollout is complete or times out
                    echo "Waiting for rollout to complete (timeout: 3 minutes)…"
                    kubectl rollout status deployment/${K8S_DEPLOYMENT} \
                        --namespace=${K8S_NAMESPACE} \
                        --timeout=3m

                    echo "Rollout complete. Current pod status:"
                    kubectl get pods \
                        --namespace=${K8S_NAMESPACE} \
                        --selector=app=fraud-detection \
                        --output=wide
                """
            }
            post {
                failure {
                    echo "Deployment failed — initiating automatic rollback…"
                    sh """
                        kubectl rollout undo deployment/${K8S_DEPLOYMENT} \
                            --namespace=${K8S_NAMESPACE} || true
                        echo "Rollback initiated. Check cluster state manually."
                    """
                }
            }
        }

        // ── Stage 7: Smoke Test ───────────────────────────────────────────────
        stage('7 · Smoke Test') {
            steps {
                echo "━━━ Stage 7: Post-Deploy Smoke Test ━━━"
                sh """
                    APP_URL="http://${MINIKUBE_IP}:${APP_NODEPORT}"
                    echo "Target URL: \${APP_URL}"

                    # Wait for the NodePort to be reachable (up to 60 seconds)
                    MAX_RETRIES=12
                    RETRY_COUNT=0
                    until curl --silent --fail "\${APP_URL}/" > /dev/null 2>&1; do
                        RETRY_COUNT=\$((RETRY_COUNT + 1))
                        if [ \${RETRY_COUNT} -ge \${MAX_RETRIES} ]; then
                            echo "ERROR: Health check endpoint not reachable after \${MAX_RETRIES} retries."
                            exit 1
                        fi
                        echo "Waiting for service to become ready… (\${RETRY_COUNT}/\${MAX_RETRIES})"
                        sleep 5
                    done

                    echo "Health check passed. Running inference smoke test…"

                    # POST a sample normal transaction and validate the response schema
                    PREDICT_RESPONSE=\$(curl --silent --fail \
                        --request POST \
                        --header "Content-Type: application/json" \
                        --data '{"amount": 85.50, "distance_from_home": 4.2}' \
                        "\${APP_URL}/predict")

                    echo "Predict response: \${PREDICT_RESPONSE}"

                    # Validate the JSON response contains the expected fields
                    echo "\${PREDICT_RESPONSE}" | python3 -c "
import json, sys
body = json.load(sys.stdin)
required = {'is_anomaly', 'anomaly_score', 'label', 'model_version', 'processing_time_ms'}
missing = required - body.keys()
if missing:
    print(f'SMOKE TEST FAILED: Missing fields in response: {missing}')
    sys.exit(1)
if body['label'] not in ('ANOMALY', 'NORMAL'):
    print(f'SMOKE TEST FAILED: Invalid label value: {body[\"label\"]}')
    sys.exit(1)
print(f'Smoke test PASSED. Prediction: {body[\"label\"]} | Score: {body[\"anomaly_score\"]}')
"
                    echo "All smoke tests passed. Deployment verified."
                """
            }
        }

    } // end stages

    // ── Post-Pipeline Actions ─────────────────────────────────────────────────
    post {

        success {
            echo """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅  Pipeline SUCCEEDED — Build #${BUILD_NUMBER}
  Image  : ${IMAGE_FULL}
  Commit : ${GIT_SHORT_SHA}
  URL    : http://${MINIKUBE_IP}:${APP_NODEPORT}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        }

        failure {
            echo """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ❌  Pipeline FAILED — Build #${BUILD_NUMBER}
  Check the stage logs above for the root cause.
  If the Kubernetes deploy stage failed, a rollback was
  automatically attempted.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        }

        unstable {
            echo "⚠️  Pipeline UNSTABLE — Build #${BUILD_NUMBER}. Test failures detected."
        }

        always {
            echo "Archiving build artifacts…"
            archiveArtifacts artifacts: 'bandit-report.json, pytest-report.xml',
                             allowEmptyArchive: true

            // Clean up dangling Docker images to prevent disk exhaustion on
            // the Jenkins agent over time.
            sh "docker image prune --filter dangling=true --force || true"

            echo "Build #${BUILD_NUMBER} complete. Duration: ${currentBuild.durationString}"
        }
    }
}
