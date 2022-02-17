#!/bin/bash
set -euo pipefail

REVISION=$(git rev-parse HEAD)

INFRA_REFLECT_FILE="proxy-model.py.changes"
INFRA_REFLECT_REPO_PATH="https://raw.githubusercontent.com/neonlabsorg/proxy-model.py/369-calculate-hashes/develop_changes/"
MAINTENANCE_FILES="
./proxy/environment.py
./proxy/proxy.py"

echo "MAINTENANCE_FILES=$MAINTENANCE_FILES"
rm -rf ./neon-infra-inventories/
git clone -b 369-calculate-hashes https://github.com/neonlabsorg/neon-infra-inventories.git

git ls-files -s $MAINTENANCE_FILES > "${INFRA_REFLECT_FILE}"".""${REVISION}"
echo "------ ${INFRA_REFLECT_FILE}:" && cat ./neon-infra-inventories/develop_changes/"${INFRA_REFLECT_FILE}"
echo "------ ${INFRA_REFLECT_FILE}.${REVISION}:" && cat ./"${INFRA_REFLECT_FILE}"".""${REVISION}"
echo "==========================================================================="
if diff -B ./neon-infra-inventories/develop_changes/"${INFRA_REFLECT_FILE}" ./"${INFRA_REFLECT_FILE}"".""${REVISION}"; then
  echo "==========================================================================="
  echo "The changes in maintenance files: "$MAINTENANCE_FILES "are reflected in the infra file ${INFRA_REFLECT_REPO_PATH}${INFRA_REFLECT_FILE}";
else
  echo "==========================================================================="
  echo "The changes in maintenance files: "$MAINTENANCE_FILES "are NOT reflected in the infra file ${INFRA_REFLECT_REPO_PATH}${INFRA_REFLECT_FILE}" | grep --color=always "are NOT reflected";
  if [[ ${BUILDKITE_BRANCH} == "develop" ]]; then
       exit 1
  fi
fi
echo "==========================================================================="
