pipeline {
    agent any

    options {
        disableConcurrentBuilds()   // dos deploys a la vez pisarían el contenedor
        timestamps()
    }

    environment {
        REPO_SSH   = 'git@github.com:ivdevV/Odoo16iRG.git'
        BRANCH     = 'Dev_iRG'
        DEPLOY_DIR = 'betaodoo16'
        CONTAINER  = 'nat16_odoo_latest'
    }

    stages {

        stage('TestPep8') {
            steps {
                echo 'Testing Pep8..'
                // Placeholder como en el original. Si quieres lint real:
                // sh 'pip install flake8 --quiet && flake8 addons-extra --max-line-length=120'
            }
        }

        stage('Deliver for development iRG Odoo') {
            // NOTA: este job solo construye Dev_iRG (Branch Specifier del job),
            // así que no hace falta 'when { branch ... }' — de hecho en un job
            // Pipeline simple (no multibranch) BRANCH_NAME no existe y el when
            // nunca se cumpliría, saltándose el deploy.
            steps {
                echo 'Deploying to DEV..'
                sshPublisher(publishers: [
                    sshPublisherDesc(
                        configName: 'odoo-dev',   // tu config de Publish over SSH
                        verbose: true,
                        transfers: [
                            sshTransfer(
                                execTimeout: 300000,
                                execCommand: '''
set -e

cd /root/betaodoo16

# 1. Clonar PRIMERO a un directorio temporal (shallow: solo la rama, sin historia)
rm -rf Odoo16iRG_new
git clone --depth 1 --branch Dev_iRG git@github.com:ivdevV/Odoo16iRG.git Odoo16iRG_new

# 2. Solo si el clone fue bien, paramos Odoo y hacemos el swap
docker container stop nat16_odoo_latest

rm -rf addons-extra_old
[ -d addons-extra ] && mv addons-extra addons-extra_old
mv Odoo16iRG_new/addons-extra ./addons-extra
rm -rf Odoo16iRG_new

# 3. Permisos (rutas reales del proyecto)
chmod 777 -R addons-extra/addons_uisep/document_processing_with_ai/temporary_files || true
chmod 775 -R addons-extra/addons_uisep/isep_scorm_elearning/static/media || true
chown 101:101 -R addons-extra

# 4. Arrancar y esperar
docker container start nat16_odoo_latest
sleep 30

# 5. Volcar log y VALIDAR que Odoo cargo bien
echo "===== Logs de DEV ====="
tail -n 500 /root/betaodoo16/log/odoo-bin.log
echo "===== Fin logs de DEV ====="

if tail -n 300 /root/betaodoo16/log/odoo-bin.log | grep -q "Failed to load registry"; then
    echo "ERROR: Odoo no pudo cargar el registry tras el deploy"
    exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -q "^nat16_odoo_latest$"; then
    echo "ERROR: el contenedor no esta corriendo tras el deploy"
    exit 1
fi

echo "Deploy OK"
'''
                            )
                        ]
                    )
                ])
                echo 'Deployed to DEV..'
            }
        }
    }

    post {
        always {
            echo 'Cleaning up!'
            cleanWs()
        }
        failure {
            echo 'Build FAILED — revisa la consola. El addons-extra anterior queda en addons-extra_old en el servidor por si hay que revertir a mano.'
        }
    }
}
