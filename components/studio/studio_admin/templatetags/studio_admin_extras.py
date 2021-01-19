from django import template

register = template.Library()


@register.filter(name='get_resource_value')
def get_resource_value(projects_resources, args):
    arg_list = [arg.strip() for arg in args.split(',')]

    project_slug = arg_list[0]

    if len(arg_list) == 2:
        total_x = arg_list[1]
        return projects_resources[project_slug][total_x]

    resource_type = arg_list[1]
    q_type = arg_list[2]
    r_type = arg_list[3]

    return projects_resources[project_slug][resource_type][q_type][r_type]
