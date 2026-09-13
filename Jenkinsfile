pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                git branch: 'payroll3', url: 'https://github.com/dhayalakshmi/payroll_app-.git'
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
        
    
    }
}
