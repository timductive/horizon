# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

import json
import logging
import httplib2

from horizon import exceptions
from horizon import forms
from horizon import tables
from horizon import tabs

from django.conf import settings
from django.core.urlresolvers import reverse
from django.core.urlresolvers import reverse_lazy
from django.utils.translation import ugettext_lazy as _

from openstack_dashboard import api
from openstack_dashboard.api.base import url_for

from openstack_dashboard.dashboards.project.stacks.forms import StackCreateForm
from openstack_dashboard.dashboards.project.stacks.forms import TemplateForm
from openstack_dashboard.dashboards.project.stacks.tables import StacksTable
from openstack_dashboard.dashboards.project.stacks.tabs \
    import ResourceDetailTabs
from openstack_dashboard.dashboards.project.stacks.tabs import StackDetailTabs


LOG = logging.getLogger(__name__)

def get_rs_token(request):
    #Setup RS Token
    rs_user = request.user.username
    rs_password = getattr(settings, 'RACKSPACE_PASSWORD', False)
    url = 'https://identity.api.rackspacecloud.com/v2.0/tokens'
    data = {}
    data['auth'] = {}
    data['auth']['passwordCredentials'] = {'username':rs_user,'password':rs_password}
    h = httplib2.Http(".cache")
    resp, content = h.request(
        uri=url,
        method='POST',
        headers={'Content-Type': 'application/json; charset=UTF-8'},
        body=json.dumps(data),
        )
    content = json.loads(content)
    rs_token = content.get('access').get('token').get('id')
    return rs_token

def get_stacks(request):
    endpoint = url_for(request, 'orchestration')
    stacks_list_url = endpoint + '/stacks?limit=20'
    rs_user = request.user.username
    rs_password = getattr(settings, 'RACKSPACE_PASSWORD', False)

    headers = {}
    # headers['X-Auth-User'] = rs_user
    headers['X-Auth-Token'] = get_rs_token(request)
    # headers['X-Auth-Key'] = rs_password
    headers['Content-Type'] = 'application/json; charset=UTF-8'

    h = httplib2.Http(disable_ssl_certificate_validation=True)
    resp, content = h.request(
        uri=stacks_list_url,
        method='GET',
        headers=headers,
        )
    stacks = content #json.loads(content)
    print 'STACKS'
    print stacks
    return stacks

class IndexView(tables.DataTableView):
    table_class = StacksTable
    template_name = 'project/stacks/index.html'

    def get_data(self):
        request = self.request
        try:
            stacks = api.heat.stacks_list(self.request)
            #stacks = get_stacks(self.request)
        except:
            exceptions.handle(request, _('Unable to retrieve stack list.'))
            stacks = []
        return stacks


class SelectTemplateView(forms.ModalFormView):
    form_class = TemplateForm
    template_name = 'project/stacks/select_template.html'
    success_url = reverse_lazy('horizon:project:stacks:launch')

    def get_form_kwargs(self):
        kwargs = super(SelectTemplateView, self).get_form_kwargs()
        kwargs['next_view'] = CreateStackView
        return kwargs


class CreateStackView(forms.ModalFormView):
    form_class = StackCreateForm
    template_name = 'project/stacks/create.html'
    success_url = reverse_lazy('horizon:project:stacks:index')

    def get_initial(self):
        initial = {}
        if 'template_data' in self.kwargs:
            initial['template_data'] = self.kwargs['template_data']
        if 'template_url' in self.kwargs:
            initial['template_url'] = self.kwargs['template_url']
        if 'parameters' in self.kwargs:
            initial['parameters'] = json.dumps(self.kwargs['parameters'])
        return initial

    def get_form_kwargs(self):
        kwargs = super(CreateStackView, self).get_form_kwargs()
        if 'parameters' in self.kwargs:
            kwargs['parameters'] = self.kwargs['parameters']
        else:
            data = json.loads(self.request.POST['parameters'])
            kwargs['parameters'] = data
        return kwargs


class DetailView(tabs.TabView):
    tab_group_class = StackDetailTabs
    template_name = 'project/stacks/detail.html'

    def get_context_data(self, **kwargs):
        context = super(DetailView, self).get_context_data(**kwargs)
        context["stack"] = self.get_data(self.request)
        return context

    def get_data(self, request, **kwargs):
        if not hasattr(self, "_stack"):
            stack_id = kwargs['stack_id']
            try:
                stack = api.heat.stack_get(request, stack_id)
                self._stack = stack
                request.session['stack_id'] = stack.id
                request.session['stack_name'] = stack.stack_name
            except:
                msg = _("Unable to retrieve stack.")
                redirect = reverse('horizon:project:stacks:index')
                exceptions.handle(request, msg, redirect=redirect)
        return self._stack

    def get_tabs(self, request, **kwargs):
        stack = self.get_data(request, **kwargs)
        return self.tab_group_class(request, stack=stack, **kwargs)


class ResourceView(tabs.TabView):
    tab_group_class = ResourceDetailTabs
    template_name = 'project/stacks/resource.html'

    def get_context_data(self, **kwargs):
        context = super(ResourceView, self).get_context_data(**kwargs)
        context["resource"] = self.get_data(self.request, **kwargs)
        context["metadata"] = self.get_metadata(self.request, **kwargs)
        return context

    def get_data(self, request, **kwargs):
        if not hasattr(self, "_resource"):
            try:
                resource = api.heat.resource_get(
                    request,
                    kwargs['stack_id'],
                    kwargs['resource_name'])
                self._resource = resource
            except:
                msg = _("Unable to retrieve resource.")
                redirect = reverse('horizon:project:stacks:index')
                exceptions.handle(request, msg, redirect=redirect)
        return self._resource

    def get_metadata(self, request, **kwargs):
        if not hasattr(self, "_metadata"):
            try:
                metadata = api.heat.resource_metadata_get(
                    request,
                    kwargs['stack_id'],
                    kwargs['resource_name'])
                self._metadata = json.dumps(metadata, indent=2)
            except:
                msg = _("Unable to retrieve metadata.")
                redirect = reverse('horizon:project:stacks:index')
                exceptions.handle(request, msg, redirect=redirect)
        return self._metadata

    def get_tabs(self, request, **kwargs):
        resource = self.get_data(request, **kwargs)
        metadata = self.get_metadata(request, **kwargs)
        return self.tab_group_class(
            request, resource=resource, metadata=metadata, **kwargs)
