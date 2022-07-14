![alt text](https://thumb.tildacdn.com/tild3162-6435-4365-a230-656137616436/-/resize/560x/-/format/webp/stacknlogo3.png)
# STACKn CLI

> Warning - This is CLI is in a experimental stage. No guarantees provided.

## Installation

```bash
git clone
```

### Recommended to not "taint" your global environment.
Create local environment
```bash
python3 -m venv env
```
Activate the local environment
```bash
source env/bin/activate
```
Install the module and pull dependencies (automagically.)
- . or the directory where scaleout-cli module is located.
```bash
python3 -m pip install -e .
```
## Basic usage

- Access help
```bash
stackn --help
```

- login to studio:
```bash
stackn login -u <username> -p <password> --url <studio-url>
```
- List project templates
```bash
stackn get project-templates
```

- create project:
```bash
stackn create project -t <project template | default: default>
```

- list projects:
```bash
stackn get projects
```

- list app instances:
```bash
stackn get app
```

- create model object:
```bash
stackn create model-obj -t <type> -v <version>
```

- list model objects:
```bash
stackn get model-obj -t <type>
```
- switch current project
```bash
stackn set current -p <project-name>
```
## Admin usage

- create app templates (based on helm charts). See /components/studio/charts for examples. config.json is required. Run inside app folder.
```bash
stackn create app
```

- create project templates. Requires template.json at CWD. Add image.png inside CWD to imbed image in Studio. Run inside project template folder.
```bash
stackn create projecttemplate
```
Example template.json:
```json
{
  "name": "Test",
  "slug": "test",
  "description": "test project template",
  "template": {
    "flavors": {
        "Medium": {
            "cpu": {
                "requirement": "100m",
                "limit": "1000m"
            },
            "mem": {
                "requirement": "1Gi",
                "limit": "8Gi"
            },
            "gpu": {
                "requirement": "0",
                "limit": "0"
            },
            "ephmem": {
                "requirement": "50Mi",
                "limit": "100Mi"
            }
        }
    },
    "environments": {
        "Jupyter Lab": {
            "repository": "ghcr.io/scaleoutsystems/stackn",
            "image": "jupyter-stackn:develop",
            "app": "jupyter-lab"
        }
    },
    "apps": {
        "minio-vol": {
            "slug": "volumeK8s",
            "volume.size": "5Gi",
            "permission": "project",
            "volume.accessModes": "ReadWriteMany",
            "volume.storageClass": "nfs-csi",
            "storageClass": "nfs-csi"
        },
        "project-vol": {
            "slug": "volumeK8s",
            "volume.size": "5Gi",
            "permission": "project",
            "volume.accessModes": "ReadWriteMany",
            "volume.storageClass": "nfs-csi",
            "storageClass": "nfs-csi"
        },
        "project-minio": {
            "slug": "minio",
            "app:volumeK8s": ["minio-vol"],
            "credentials.access_key": "accesskey2",
            "credentials.secret_key": "secretkey193",
            "permission": "project"
        },
        "jupyter-lab": {
            "slug": "jupyter-lab",
            "app:volumeK8s": ["project-vol"],
            "environment": "Jupyter Lab",
            "permission": "project",
            "flavor": "Medium"
        }
    },
    "settings": {
        "project-S3": "project-minio" 
    }
  }
}
```




