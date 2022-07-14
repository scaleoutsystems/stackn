# Release Notes

## v0.6.0

### New functionality
- Major revamp removing Keycloak and instead using solely Django built-in User model.
- OAuth2 now supported. See github and google example in studio/settings.py 
- Deployment using docker-compose now available (still need a k8s cluster such as microk8s to deploy apps via helm charts)
- Auth requests submodule used in nginx ingress for apps. This removes a lot of overhead since Keycloak required a reverse proxy per application.
- A set of default apps and project templates are now loaded upon deployment. I.e you just need to modify cluster.conf and studio/settings.py to get started with docker-compose.
- It's now possile to deploy apps using the CLI: `$ stackn create appinstance` (experimental feature).

### Bug fixes
- Several minor bug fixes and improvements


### Other
- Regular views permissions are now handled by django-guardian
- Contribution.md has been updated (related to new integration and code tests) 


## v0.5.0

### New functionality
- Apps and project templates added  as separate folders (can be installed via CLI)
- CLI has been refactored
- Added support for MLflow
- Default environments (images) added to "default" project template
- Functionalities added to CLI, including "insecure" mode enabling local deployment without certificates
- Support for setting app tags added
- New static files for django admin site
- Various updated to the UI for easier navigation and structure
- Model cards added after model deployment, also support in CLI
-  Can now deploy STACKn in either debug mode with the develop server, or in production mode with gunicorn and serving static content with nginx
- Reloader added for making updates on change on ConfigMaps and Secrets

### Bug fixes
- Fix in publishmodel object: onetoone project field to foreignkey
- Keycloak resources now deleted properly when project is deleted
- Random credentials are now generated when creating new projects from templates
- Fix bug in celery worker deployment
- Longer length of project names is now allowed
- Deleting projects via CLI now works
- Various bug fixes in UI
- Various minor bug fixes

### Other
- [master](https://github.com/scaleoutsystems/stackn/tree/master) branch is archived, new default branch is [main](https://github.com/scaleoutsystems/stackn/tree/main)
- README.md has been restructured (instructions for local deployment) 
<br />
<br />

## v0.4.0

### New functionality

### Bug fixes

- Project's detailed page is now listing only the related activity logs
- Public models are no more shown after the corresponding project has been removed

### Other

- New improved functionality for adding users as members to your project
<br />
<br />

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
<br />
<br />

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
<br />
<br />

## v0.1.0

- Experiments view now working.
- Default versioning for models vX.Y.Z (can be configured by user).
- Model deployments integrated with Keycloak.
- CLI reworked. Now possible to login and manage all projects, no need for project-specific configuration files.
- Add members to projects via UI.
- Manual scaling of model deployments.
- Basic monitoring of model deployments.
- Many bug fixes.
