
# Chart Deployer


To be used to deploy our platform dependant helm charts.
> Note that this is intended to be used as a machine-to-machine interface. This is not a user facing service.

## Example usage:

### Deploying a chart in our library
```bash
$ curl http://service-url/deploy?release=sassy-struts&chart=alliance-chart
{"helm": {"command": ["helm", "install", "sassy-struts", "charts/alliance-chart"], "cwd": "/app", "status": "CompletedProcess(args=['helm', 'install', 'sassy-struts', 'charts/alliance-chart'], returncode=0)"}}
```

### Removing a running helm chart (by release name)
```bash
$ curl http://service-url/delete?release=sassy-struts
{"helm": {"command": ["helm", "delete", "sassy-struts"], "cwd": "/app", "status": "CompletedProcess(args=['helm', 'delete', 'sassy-struts'], returncode=0)"}}
```


