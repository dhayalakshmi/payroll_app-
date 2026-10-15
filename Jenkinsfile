pipeline {
    agent any

    environment {
        DOCKER_IMAGE = "dhayalakshmi04/payroll-reports-app:latest"
    }

    stages {
        stage('Clone Repository') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                bat "docker build -t %DOCKER_IMAGE% ."
            }
        }

        stage('Push to DockerHub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-cred',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    bat """
                    echo %DOCKER_PASS%| docker login -u %DOCKER_USER% --password-stdin
                    docker push %DOCKER_IMAGE%
                    """
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                withCredentials([file(credentialsId: 'kubeconfig', variable: 'KUBECONFIG')]) {
                    bat 'kubectl apply -f deployment.yaml'
                    bat 'kubectl rollout restart deployment/payroll-reports-app'
                }
            }
        }
    }

    post {
        success { echo 'CI/CD Pipeline executed successfully!' }
        failure { echo 'Pipeline failed. Please check logs.' }
    }
}
