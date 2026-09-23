pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                bat 'python -m py_compile payrollM3.py'
            }
        }
        stage('Test') {
            steps {
                bat 'python -c "import payrollM3; print(\'Test OK\')"'
            }
        }
        stage('Create Docker Image') {
            steps {
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" build -t payroll-app .'
            }
        }
        stage('Start and Stop Container') {
            steps {
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" rm -f payroll-container || exit 0'
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" run --name payroll-container payroll-app'
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" ps -a'
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" rm -f payroll-container'
            }
        }
    }
}
