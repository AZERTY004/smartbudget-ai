pipeline {
    agent any

    environment {
        // Variables d'environnement pour le build Docker
        DOCKER_IMAGE = 'smartbudget-ai'
        DOCKER_TAG = "v${env.BUILD_NUMBER}"
        // Remplacer par l'URL de votre registry Azure (ex: monregistry.azurecr.io) si besoin
        REGISTRY = '' 
    }

    stages {
        stage('Checkout') {
            steps {
                echo 'Récupération du code source depuis Git...'
                checkout scm
            }
        }

        stage('Tests & Validation (CI)') {
            steps {
                echo 'Vérification de la syntaxe Python...'
                // Exécute un test basique pour s'assurer qu'il n'y a pas d'erreur de syntaxe
                sh 'python -m py_compile app.py'
            }
        }

        stage('Build Docker Image') {
            steps {
                echo 'Construction de l\'image Docker...'
                script {
                    // Si un registre est défini, on tag avec le registre
                    if (env.REGISTRY != '') {
                        sh "docker build -t ${REGISTRY}/${DOCKER_IMAGE}:${DOCKER_TAG} -t ${REGISTRY}/${DOCKER_IMAGE}:latest ."
                    } else {
                        sh "docker build -t ${DOCKER_IMAGE}:${DOCKER_TAG} -t ${DOCKER_IMAGE}:latest ."
                    }
                }
            }
        }

        stage('Deploy (CD)') {
            steps {
                echo 'Déploiement du conteneur...'
                script {
                    // Supprime l'ancien conteneur s'il existe
                    sh 'docker rm -f smartbudget-app || true'
                    // Lance le nouveau conteneur
                    sh "docker run -d -p 5000:5000 --name smartbudget-app ${DOCKER_IMAGE}:latest"
                }
            }
        }
    }

    post {
        success {
            echo 'Pipeline terminé avec succès ! L\'application tourne sur le port 5000.'
        }
        failure {
            echo 'Le pipeline a échoué. Veuillez vérifier les logs Jenkins.'
        }
    }
}
