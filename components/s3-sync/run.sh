#!/bin/bash


mkdir -p $MOUNTPOINT

#[[ -z "${S3UID}" ]] || FUSE_OPTS="$FUSE_OPTS -o uid=${S3UID}"
#[[ -z "${S3GID}" ]] || FUSE_OPTS="$FUSE_OPTS -o gid=${S3GID}"
[[ -z "${AUTOROLE}" ]] || FUSE_OPTS="$FUSE_OPTS -o iam_role=auto"
[[ -z "${ALLOWEMPTY}" ]] || FUSE_OPTS="$FUSE_OPTS -o nonempty"
[[ -z "${ALLOWOTHERS}" ]] || FUSE_OPTS="$FUSE_OPTS -o allow_other"
#[[ -z "${REPOURL}" ]] || FUSE_OPTS="$FUSE_OPTS -o url=${REPOURL}"

echo Mounting $BUCKET  on $MOUNTPOINT with $FUSE_OPTS...
echo "exec s3fs  $BUCKET $MOUNTPOINT  $FUSE_OPTS -o umask=0000 -o url=$REPOURL -o use_path_request_style,use_cache=/tmp -f"
exec s3fs  $BUCKET $MOUNTPOINT  $FUSE_OPTS -o umask=0000 -o url=$REPOURL -o allow_other -o use_path_request_style,use_cache=/tmp -f
#-o no_check_certificate
#-o uid=1000 -o gid=100
