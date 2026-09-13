pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git branch: 'employee', url: 'https://github.com/dhayalakshmi/payroll_app-.git'
            }
        }
        stage('Build') {
            steps {
                bat 'python -m pip install -r requirements.txt'
            }
        }
        stage('Docker Build') {
            steps {
                bat 'docker build -t payroll-flask:setF .'
            }
        }
        stage('Docker Build Manual-Style') {
            steps {
                bat 'docker build -t payroll-flask:setF-manual .'
            }
        }
        stage('Run and Verify Container') {
            steps {
                bat 'docker rm -f setF_container || exit 0'
                bat 'docker run -d -p 5003:5000 --name setF_container payroll-flask:setF'
                bat 'timeout /t 5'
                bat 'curl -f http://localhost:5003/ || (docker logs setF_container && exit 1)'
                bat 'echo Application verified successfully - container is responding'
            }
        }
    }
}
