pipeline {
    agent any
    stages {
        stage('Build') {
            steps {
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" -m pip install -r requirements.txt'
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" -m py_compile app.py'
            }
        }
        stage('Test') {
            steps {
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\Python\\Python314\\python.exe" -c "import app; print(\'Test OK\')"'
            }
        }
        stage('Create Docker Image') {
            steps {
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" build -t flask-payroll-app .'
            }
        }
        stage('Start and Stop Container') {
            steps {
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" rm -f payroll-container || exit 0'
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" run -d -p 8000:8000 --name payroll-container flask-payroll-app'
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" ps'
                bat 'ping 127.0.0.1 -n 11 > nul'
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" stop payroll-container'
                bat '"C:\\Users\\HP\\AppData\\Local\\Programs\\DockerDesktop\\resources\\bin\\docker.exe" rm -f payroll-container'
            }
        }
    }
}
