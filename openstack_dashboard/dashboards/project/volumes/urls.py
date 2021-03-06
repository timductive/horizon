# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nebula, Inc.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

from openstack_dashboard.dashboards.project.volumes.views \
    import CreateSnapshotView
from openstack_dashboard.dashboards.project.volumes.views import CreateView
from openstack_dashboard.dashboards.project.volumes.views import DetailView
from openstack_dashboard.dashboards.project.volumes.views \
    import EditAttachmentsView
from openstack_dashboard.dashboards.project.volumes.views import IndexView


urlpatterns = patterns('openstack_dashboard.dashboards.project.volumes.views',
    url(r'^$', IndexView.as_view(), name='index'),
    url(r'^create/$', CreateView.as_view(), name='create'),
    url(r'^(?P<volume_id>[^/]+)/attach/$',
        EditAttachmentsView.as_view(),
        name='attach'),
    url(r'^(?P<volume_id>[^/]+)/create_snapshot/$',
        CreateSnapshotView.as_view(),
        name='create_snapshot'),
    url(r'^(?P<volume_id>[^/]+)/$',
        DetailView.as_view(),
        name='detail'),
)
