pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    stages {

        stage('TestPep8') {
            steps {
                echo 'Testing Pep8..'
            }
        }

        // ==================== DEV (rama Dev_iRG -> beta) ====================
        stage('Deliver for development iRG Odoo') {
            when { branch 'Dev_iRG' }
            steps {
                echo 'Deploying to DEV..'
                sshPublisher(publishers: [
                    sshPublisherDesc(
                        configName: 'odoo-dev',
                        verbose: true,
                        transfers: [
                            sshTransfer(
                                execTimeout: 300000,
                                execCommand: '''
set -e
APP_DIR=/root/betaodoo16
CONTAINER=nat16_odoo_latest
BRANCH=Dev_iRG

cd "$APP_DIR"

# Clonar PRIMERO a temporal (solo la rama, sin historia)
rm -rf Odoo16iRG_new
git clone --depth 1 --branch "$BRANCH" git@github.com:ivdevV/Odoo16iRG.git Odoo16iRG_new

# Solo si el clone fue bien: parar, swap
docker container stop "$CONTAINER"
rm -rf addons-extra_old
[ -d addons-extra ] && mv addons-extra addons-extra_old
mv Odoo16iRG_new/addons-extra ./addons-extra
rm -rf Odoo16iRG_new

# Preservar datos no versionados (media SCORM y temporales) del deploy anterior
if [ -d addons-extra_old/addons_uisep/isep_scorm_elearning/static/media ]; then
    rm -rf addons-extra/addons_uisep/isep_scorm_elearning/static/media
    mv addons-extra_old/addons_uisep/isep_scorm_elearning/static/media addons-extra/addons_uisep/isep_scorm_elearning/static/
fi
if [ -d addons-extra_old/addons_uisep/document_processing_with_ai/temporary_files ]; then
    rm -rf addons-extra/addons_uisep/document_processing_with_ai/temporary_files
    mv addons-extra_old/addons_uisep/document_processing_with_ai/temporary_files addons-extra/addons_uisep/document_processing_with_ai/
fi

chmod 777 -R addons-extra/addons_uisep/document_processing_with_ai/temporary_files || true
chmod 775 -R addons-extra/addons_uisep/isep_scorm_elearning/static/media || true
chown 101:101 -R addons-extra

docker container start "$CONTAINER"
sleep 30

echo "===== Logs de DEV ====="
tail -n 500 "$APP_DIR/log/odoo-bin.log"
echo "===== Fin logs de DEV ====="

if tail -n 300 "$APP_DIR/log/odoo-bin.log" | grep -q "Failed to load registry"; then
    echo "ERROR: Odoo no pudo cargar el registry tras el deploy"
    exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "ERROR: el contenedor no esta corriendo tras el deploy"
    exit 1
fi
echo "Deploy DEV OK"
'''
                            )
                        ]
                    )
                ])
                echo 'Deployed to DEV..'
            }
        }

        // ==================== PROD (rama main -> app.institutoraimongaja.com) ====================
        stage('Deploy for Production iRG') {
            when { branch 'main' }
            steps {
                // Igual que el original: aprobacion manual con timeout de 5 min
                timeout(time: 5, unit: 'MINUTES') {
                    input message: 'Do you want to approve the deployment?', ok: 'Yes'
                }

                echo 'Deploying to Prod iRG..'
                sshPublisher(publishers: [
                    sshPublisherDesc(
                        configName: 'odoo-prod',
                        verbose: true,
                        transfers: [
                            sshTransfer(
                                execTimeout: 600000,
                                execCommand: '''
set -e
APP_DIR=/root/nativo16
CONTAINER=nat16_odoo_latest
PG_CONTAINER=nat16_pgodoo_latest
DB_NAME=Base16
BRANCH=main

cd "$APP_DIR"

# 0. BACKUP de la BD antes de tocar nada (si falla, se aborta el deploy)
mkdir -p /root/backups
docker exec "$PG_CONTAINER" pg_dump -U odoo -Fc "$DB_NAME" > "/root/backups/pre-deploy-$(date +%Y%m%d-%H%M%S).dump"
ls -t /root/backups/pre-deploy-*.dump | tail -n +11 | xargs -r rm
echo "Backup de BD completado"

# 1. Clonar PRIMERO a temporal
rm -rf Odoo16iRG_new
git clone --depth 1 --branch "$BRANCH" git@github.com:ivdevV/Odoo16iRG.git Odoo16iRG_new

# 2. Solo si el clone fue bien: parar y archivar el addons actual por commit
docker container stop "$CONTAINER"
COMMIT=$(git -C Odoo16iRG_new rev-parse HEAD)
mkdir -p old_addons-extra
rm -rf "old_addons-extra/$COMMIT"
[ -d addons-extra ] && mv addons-extra "old_addons-extra/$COMMIT"
mv Odoo16iRG_new/addons-extra ./addons-extra
rm -rf Odoo16iRG_new
# conservar solo los 5 archivados mas recientes
ls -dt old_addons-extra/*/ 2>/dev/null | tail -n +6 | xargs -r rm -rf

# 3. Preservar datos NO versionados (media SCORM de alumnos y temporales IA)
if [ -d "old_addons-extra/$COMMIT/addons_uisep/isep_scorm_elearning/static/media" ]; then
    rm -rf addons-extra/addons_uisep/isep_scorm_elearning/static/media
    mv "old_addons-extra/$COMMIT/addons_uisep/isep_scorm_elearning/static/media" addons-extra/addons_uisep/isep_scorm_elearning/static/
fi
if [ -d "old_addons-extra/$COMMIT/addons_uisep/document_processing_with_ai/temporary_files" ]; then
    rm -rf addons-extra/addons_uisep/document_processing_with_ai/temporary_files
    mv "old_addons-extra/$COMMIT/addons_uisep/document_processing_with_ai/temporary_files" addons-extra/addons_uisep/document_processing_with_ai/
fi

# 4. Permisos
chmod 777 -R addons-extra/addons_uisep/document_processing_with_ai/temporary_files || true
chmod 775 -R addons-extra/addons_uisep/isep_scorm_elearning/static/media || true
chown 101:101 -R addons-extra

# 5. Arrancar Odoo y nginx (como el original)
docker container start "$CONTAINER"
docker container restart nginx
sleep 30

echo "===== Logs de PRODUCTION ====="
tail -n 500 "$APP_DIR/log/odoo-bin.log"
echo "===== Fin logs de PRODUCTION ====="

if tail -n 300 "$APP_DIR/log/odoo-bin.log" | grep -q "Failed to load registry"; then
    echo "ERROR: Odoo PROD no pudo cargar el registry"
    exit 1
fi
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
    echo "ERROR: el contenedor de PROD no esta corriendo"
    exit 1
fi
echo "Deploy PROD OK"
'''
                            )
                        ]
                    )
                ])
                echo 'Deployed to Prod..'
            }
        }
    }

    post {
        always {
            echo 'Cleaning up!'
            cleanWs()
        }
        failure {
            echo 'Build FAILED. Rollback disponible: addons-extra_old (dev) / old_addons-extra/<commit> (prod) + dump en /root/backups (prod).'
        }
    }
}
