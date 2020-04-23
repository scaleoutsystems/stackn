import logging
from django.shortcuts import render
from .models import Page

logger = logging.getLogger(__name__)

DEFAULT_PAGE = """<div class="position-relative overflow-hidden p-3 p-md-5 m-md-3 text-center bg-light">
                        <div class="container">
                            <div class="row">
                                <div class="col">
                                    <img src="https://static.tildacdn.com/tild3039-3264-4638-b663-363939353030/bg1.png">
                                </div>
                    
                                <div class="modal fade" id="create-modal" tabindex="-1" role="dialog" aria-hidden="true">
                                    <div class="modal-dialog">
                                        <div class="modal-content">
                    
                                        </div>
                                    </div>
                                </div>
                    
                                <div class="col">
                                    <h1 class="display-4 font-weight-normal">Scaleout platform</h1>
                                    <p class="lead font-weight-normal">Welcome to our privacy preserving federated machine learning
                                        platform. We are currently in closed beta. Apply here and you will be up and running in notime.</p>
                                    <a class="access-request btn btn-outline-primary" type="button" name="button">Apply here</a>
                                </div>
                            </div>
                        </div>
                    </div>"""
DEFAULT_MODAL = """<script type="text/javascript">
                            $(function () {
                        
                              $(".access-request").modalForm({formURL: "/access/apply/", modalID: "#create-modal"});
                        
                            });
                        </script>"""


def index(request):
    template = 'index.html'
    try:
        startpage = Page.objects.filter(name='startpage').first().page
    except AttributeError:
        startpage = DEFAULT_PAGE

    try:
        modalscript = Page.objects.filter(name='modalscript').first().page
    except AttributeError:
        modalscript = DEFAULT_MODAL

    return render(request, template, locals())
