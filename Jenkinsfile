// Pipeline declarativo. O endereço de e-mail NÃO está aqui: vem da variável
// de ambiente NOTIFY_EMAIL do container (ver docker-compose.yml / .env).
pipeline {
    agent any

    options {
        timestamps()
        timeout(time: 15, unit: 'MINUTES')
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        PACKAGE_NAME = "d20-arena-${BUILD_NUMBER}"
    }

    stages {
        stage('Preparar ambiente') {
            steps {
                sh '''
                    python3 -m venv .venv
                    . .venv/bin/activate
                    pip install --quiet --upgrade pip
                    pip install --quiet -r requirements-dev.txt
                '''
            }
        }

        stage('Testes') {
            steps {
                sh '''
                    . .venv/bin/activate
                    mkdir -p reports
                    pytest \
                      --cov=app --cov=scripts \
                      --cov-report=term-missing \
                      --cov-report=xml:coverage.xml \
                      --cov-report=html:htmlcov \
                      --cov-fail-under=90 \
                      --junitxml=reports/junit.xml
                '''
            }
            post {
                always {
                    junit allowEmptyResults: true, testResults: 'reports/junit.xml'
                    archiveArtifacts artifacts: 'reports/**, coverage.xml, htmlcov/**', allowEmptyArchive: true
                }
            }
        }

        stage('Build / Pacote') {
            steps {
                sh '''
                    mkdir -p dist
                    zip -rq "dist/${PACKAGE_NAME}.zip" app scripts requirements.txt Dockerfile README.md \
                        -x "*/__pycache__/*"
                '''
                archiveArtifacts artifacts: 'dist/*.zip', fingerprint: true
            }
        }

        stage('Notificar') {
            steps {
                sh 'python3 scripts/send_email.py --status SUCCESS'
            }
        }
    }

    post {
        failure {
            // Se algo falhar antes da etapa Notificar, o e-mail de falha sai aqui.
            sh 'python3 scripts/send_email.py --status FAILURE || true'
        }
    }
}
