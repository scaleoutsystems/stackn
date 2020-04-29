from django.conf import settings
import logging
import requests as r

logger = logging.getLogger(__file__)


def create_session_resources(session, prefs, project):

    print("1; going for the dispatch!")

    parameters = {'release': str(session.slug),
                  'chart': session.chart,
                  'global.domain': settings.DOMAIN,
                  'project.name': project.slug,
                  }
    parameters.update(prefs)

    url = settings.CHART_CONTROLLER_URL + '/deploy'

    retval = r.get(url, parameters)
    print("CREATE_SESSION:helm chart creator returned {}".format(retval))

    if retval.status_code >= 200 or retval.status_code < 205:
        return True

    return False


def delete_session_resources(session):
    print("trying to delete {}".format(session.slug))
    parameters = {'release': str(session.slug)}
    retval = r.get(settings.CHART_CONTROLLER_URL + '/delete', parameters)

    if retval:
        print('delete success!')
        return True
    print('delete failed!?')
    return False
