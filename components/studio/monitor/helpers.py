import requests as r

def pod_up(app_name):
    query_up = 'sum(up{app="'+app_name+'"})'
    query_count = 'count(up{app="'+app_name+'"})'
    # print(query)
    response = r.get('http://stackn-prometheus-server/api/v1/query', params={'query':query_up})
    result_up = response.json()['data']['result']
    response = r.get('http://stackn-prometheus-server/api/v1/query', params={'query':query_count})
    result_count = response.json()['data']['result']
    num_pods_up = result_up[0]['value'][1]
    num_pods_count = result_count[0]['value'][1]
    return num_pods_up, num_pods_count
    # print(num_pods_up)

def get_total_labs_cpu_usage_60s(project_slug):
    query = 'sum(sum (rate (container_cpu_usage_seconds_total{image!=""}[60s])) by (pod) * on(pod) group_left kube_pod_labels{label_project="'+project_slug+'", label_type="lab"})'
    response = r.get('http://stackn-prometheus-server/api/v1/query', params={'query':query})
    result = response.json()['data']['result']
    if result:
        cpu_usage = result[0]['value'][1]
        return "{:.1f}".format(float(cpu_usage))
    return 0

def get_total_cpu_usage_60s_ts(project_slug, resource_type):
    query = '''(sum (sum ( irate (container_cpu_usage_seconds_total{image!=""}[60s] ) ) by (pod) * on(pod) group_left kube_pod_labels{label_type="'''+resource_type+'",label_project="'+project_slug+'"})) [30m:30s]'
    print(query)
    response = r.get('http://stackn-prometheus-server/api/v1/query', params={'query':query})
    # print(response.json())
    result = response.json()['data']['result']
    if result:
        return result[0]['values']
    return 0

def get_total_labs_memory_usage_60s(project_slug):
    query = 'sum(sum (rate (container_memory_usage_bytes{image!=""}[60s])) by (pod) * on(pod) group_left kube_pod_labels{label_project="'+project_slug+'", label_type="lab"})'
    response = r.get('http://stackn-prometheus-server/api/v1/query', params={'query':query})
    result = response.json()['data']['result']
    if result:
        memory_usage = result[0]['value'][1]
        return "{:.3f}".format(float(memory_usage)/1e9*0.931323)
    return 0

def get_labs_memory_requests(project_slug):
    query = 'sum(kube_pod_container_resource_requests_memory_bytes * on(pod) group_left kube_pod_labels{label_project="'+project_slug+'"})'
    # query = 'kube_pod_container_resource_requests_cpu_cores'
    
    response = r.get('http://stackn-prometheus-server/api/v1/query', params={'query':query})
    result = response.json()['data']['result']
    if result:
        memory = result[0]['value'][1]
        return "{:.2f}".format(float(memory)/1e9*0.931323)
    return 0

def get_labs_cpu_requests(project_slug):
    query = 'sum(kube_pod_container_resource_requests_cpu_cores * on(pod) group_left kube_pod_labels{label_project="'+project_slug+'"})'

    response = r.get('http://stackn-prometheus-server/api/v1/query', params={'query':query})
    result = response.json()['data']['result']
    if result:
        num_cpus = result[0]['value'][1]
        return num_cpus
    return 0