pipeline {
    agent any

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
                bat 'python -m py_compile app.py'
            }
        }

        stage('Build & Deploy (CD)') {
            steps {
                echo 'Simulation du déploiement continu...'
                echo 'Déploiement Cloud offloadé sur Azure App Service (voir GitHub Actions) !'
            }
        }
    }

    post {
        success {
            echo 'Pipeline Jenkins terminé avec succès !'
        }
        failure {
            echo 'Le pipeline a échoué. Veuillez vérifier les logs Jenkins.'
        }
    }
}
