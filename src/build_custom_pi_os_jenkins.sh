#!/bin/bash
set -x
set -e

CUSTOM_PI_OS_WORKSPACE=workspace

if [ "${VARIANT}" != "" ]; then
    CUSTOM_PI_OS_WORKSPACE=workspace-${VARIANT}
fi

pushd "${DISTRO_PATH}"
    sudo /usr/local/bin/custompios_build_repo "${DISTRO_PATH}" "${VARIANT}"
    
    
    # Create zip with date naming
    ZIPNAME=$(ls ./src/${CUSTOM_PI_OS_WORKSPACE}/*.zip | head -n 1)
    BASENAME=$(basename $(ls ./src/${CUSTOM_PI_OS_WORKSPACE}/*.zip | head -n 1))
    DIRNAME=$(realpath "./src/${CUSTOM_PI_OS_WORKSPACE}")
    DATE=$(date --rfc-3339=date)
    NEW_ZIP_NAME=${DIRNAME}/${DATE}_${BASENAME}
    TEMP_COPY_DIR=/mnt/sda1/unofficialpi/upload_cache
    TEMP_COPY_DEST="${TEMP_COPY_DIR}/custompios/${BUILD_NUMBER}"
    mkdir -p "${TEMP_COPY_DEST}"
    
    RPI_JSON_PATH_BASE=rpi-imager-snipplet.json
    FULL_RPI_JSON_PATH="${DIRNAME}/${RPI_JSON_PATH_BASE}"
    NEW_RPI_JSON_PATH_BASE=${DATE}_${RPI_JSON_PATH_BASE}
    echo ${FULL_RPI_JSON_PATH}
    
    shopt -s nullglob
    for export_file in "${DIRNAME}"/*.tar.gz
    do
        cp "${export_file}" "${TEMP_COPY_DEST}"/$(date --rfc-3339=date)_$(basename ${export_file}) || true
    done
    
    mv "${ZIPNAME}" "${NEW_ZIP_NAME}"
    
    mv "${NEW_ZIP_NAME}" "${TEMP_COPY_DEST}"/`basename ${NEW_ZIP_NAME}`
    
    pushd "${TEMP_COPY_DEST}"
        md5sum `basename ${NEW_ZIP_NAME}` > `basename ${NEW_ZIP_NAME}`.md5
        echo mv "${FULL_RPI_JSON_PATH}" "${NEW_RPI_JSON_PATH_BASE}"
        ls ${FULL_RPI_JSON_PATH}
        mv "${FULL_RPI_JSON_PATH}" "${NEW_RPI_JSON_PATH_BASE}"
    popd
    
    
popd


# Add files to  ftp upload publish script
pushd "${TEMP_COPY_DEST}"
    unset IFS; a=("$PWD"/*); printf '%s\0' "${a[@]}" > "${TEMP_COPY_DEST}/files"
    
    echo  FileNamesPath=${TEMP_COPY_DEST}/files > "${TEMP_COPY_DEST}/upload_this"
    echo "Directory=${FTP_PUBLISH_PATH}" >> "${TEMP_COPY_DEST}/upload_this"
popd
