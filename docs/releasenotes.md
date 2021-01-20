# Release Notes

## v0.4.0 (upcoming release)

### New functionality
- Studio Administration module to monitor and manage resources as an alternative to Django Admin

### Bug fixes

- Project's detailed page is now listing only the related activity logs
- Public models are no more shown after the corresponding project has been removed

### Other

- New improved functionality for adding users as members to your project

## v0.3.0

### New functionality

- You can now set environment variables in a model deployment
- New CLI command `stackn get settings` for listing all the settings needed to set up the CLI client. 
The keycloak host is now set automatically after providing the studio host.
- Added a chart to the models module in STACKn to show how model metrics have changed over time and runs (draft)
- Create and delete project volumes with the CLI

```bash
stackn create volume -s 10Mi -n example-vol
stackn get volumes
stackn delete volume -n example-vol
stackn create lab -f medium -e jupyter-minimal -v example-vol1,example-vol2
```

- A possibility to specify which buckets (arbitrary number) from the Minio instance should be mounted in the deployed container
- A possibility to create jobs from command line

```
stackn create job -c job.json
stackn get jobs
```

### Other

- Freshened up and new optimized STACKn documentation
- STACKn is now using ONLY Keycloak for authentication

## v0.2.0

### New functionality

- Introduced ownership for Lab Sessions
- Asynchronous allocation of Project resources with Celery tasks
- Added API permission classes
- Added Cron Jobs under Experiments
- Introduced Project Activity log
- Added resource limits for deployments
- Introduced basic monitoring overview
- Defined default project structure through

```bash
stackn init
```

- Added new commands in the CLI client

```bash
stackn project add members ...

stackn --version

stackn lab create -flavor ... -environment ...

stackn lab list all

stackn create/get/delete dataset ...
```

- STACKn local deploy (instructions available for macOS and Linux)

### Bug fixes

- Only the Project owner can grant access to it
- Cleaned up obsolete k8s jobs from the kubernetes cluster
- Optimized Django migrations management


## v0.1.0

- Experiments view now working.
- Default versioning for models vX.Y.Z (can be configured by user).
- Model deployments integrated with Keycloak.
- CLI reworked. Now possible to login and manage all projects, no need for project-specific configuration files.
- Add members to projects via UI.
- Manual scaling of model deployments.
- Basic monitoring of model deployments.
- Many bug fixes.
