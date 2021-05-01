#!/bin/bash

###########################
####### LOAD CONFIG #######
###########################

if [ -z $CONFIG_FILE_PATH ] ; then
  CONFIG_FILE_PATH="$1/backups/pg_backup.config"
fi

if [ ! -r ${CONFIG_FILE_PATH} ] ; then
  echo "Could not load config file from ${CONFIG_FILE_PATH}" 1>&2
  exit 1
fi

source "${CONFIG_FILE_PATH}"

###########################
### INITIALISE DEFAULTS ###
###########################

if [ ! $HOSTNAME ]; then
  HOSTNAME="localhost"
fi;

if [ ! $USERNAME ]; then
  USERNAME="postgres"
fi;

if [ ! $PASSWORD ]; then
  PASSWORD=""
fi;

if [ ! $BACKUP_DIR ]; then
  BACKUP_DIR="$1/backups/"
fi;

###########################
#### START THE BACKUPS ####
###########################

function perform_backups()
{
  BACKUP_NAME="`date +\%Y-\%m-\%d`-deploy"

  echo "Making backup directory in $BACKUP_DIR"

  if ! mkdir -p $BACKUP_DIR; then
    echo "Cannot create backup directory in $BACKUP_DIR." 1>&2
    exit 1;
  fi;

  ###########################
  ###### FULL BACKUPS #######
  ###########################

  echo -e "\n\nPerforming full backups"
  echo -e "--------------------------------------------\n"

  for DATABASE in ${DATABASE_WHITELIST//,/ }
  do
    echo "Uncompressed backup of $DATABASE"

    if ! (export PGPASSWORD="$PASSWORD"; pg_dump -O -h "$HOSTNAME" -U "$USERNAME" "$DATABASE" > $BACKUP_DIR"$BACKUP_NAME".sql.in_progress); then
      echo "Failed to produce uncompressed backup of database $DATABASE" 1>&2
    else
      mv $BACKUP_DIR"$BACKUP_NAME".sql.in_progress $BACKUP_DIR"$BACKUP_NAME".sql
    fi
  done

  echo -e "\nAll database backups complete!"
}

# DEPLOYMENT BACKUPS

find $BACKUP_DIR -maxdepth 1 -name "*-deploy.*" -exec rm -rf '{}' ';'
perform_backups
exit 0;
