pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                dir('/home/docker/jenkins/be') {
                    git branch: 'develop', url: 'https://gitlab.com/sep4904175122/be-automated-grading-support-system', credentialsId: '551641f8-d988-4e5c-905f-8e64be14cc0f'
                }
            }
        }
        stage('Build') {
            steps {
                dir('/home/docker/jenkins/be') {
                    sh '''
                    export DOCKER_CRED_HELPER=""
                    export DOCKER_CONFIG=/tmp/docker-jenkins-$BUILD_NUMBER
                    mkdir -p /tmp/docker-jenkins-$BUILD_NUMBER
                    docker-compose build
                    '''
                }
            }
        }
        stage('Deploy') {
            steps {
                dir('/home/docker/jenkins/be') {
                    sh 'docker-compose down'
                    sh 'docker-compose up -d'
                }
            }
        }
    }
}