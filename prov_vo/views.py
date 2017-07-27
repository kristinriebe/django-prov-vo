import sys # just for debugging
import json
from datetime import datetime

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse, HttpResponseRedirect
#from django.template import loader
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError
from django.views import generic
from django.http import JsonResponse
from django.db.models.fields.related import ManyToManyField
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt

from braces.views import JSONResponseMixin

#from rest_framework.renderers import XMLRenderer
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework import viewsets

import utils

from .models import (
    Activity,
    Entity,
    Agent,
    Used,
    WasGeneratedBy,
    WasAssociatedWith,
    WasAttributedTo,
    HadMember,
    HadStep,
    WasDerivedFrom,
    WasInformedBy,
    ActivityFlow,
    Collection
    #Bundle,
)

from .serializers import (
    ActivitySerializer,
    EntitySerializer,
    AgentSerializer,
    UsedSerializer,
    WasGeneratedBySerializer,
    WasAssociatedWithSerializer,
    WasAttributedToSerializer,
    HadMemberSerializer,
    WasDerivedFromSerializer,
    WasInformedBySerializer,
    W3CCollectionSerializer,
    W3CProvenanceSerializer,
    VOProvenanceSerializer,
    ProvenanceGraphSerializer
)

from .renderers import PROVNRenderer, PROVJSONRenderer

from .forms import ProvDalForm


class IndexView(generic.TemplateView):
    template_name = 'prov_vo/index.html'

class ActivityViewSet(viewsets.ModelViewSet):
    serializer_class = ActivitySerializer
    queryset = Activity.objects.all()

class EntityViewSet(viewsets.ModelViewSet):
    serializer_class = EntitySerializer
    queryset = Entity.objects.all()

class AgentViewSet(viewsets.ModelViewSet):
    serializer_class = AgentSerializer
    queryset = Agent.objects.all()

class UsedViewSet(viewsets.ModelViewSet):
    serializer_class = UsedSerializer
    queryset = Used.objects.all()

class WasGeneratedByViewSet(viewsets.ModelViewSet):
    serializer_class = WasGeneratedBySerializer
    queryset = WasGeneratedBy.objects.all()

class WasAssociatedWithViewSet(viewsets.ModelViewSet):
    serializer_class = WasAssociatedWithSerializer
    queryset = WasAssociatedWith.objects.all()

class WasAttributedToViewSet(viewsets.ModelViewSet):
    serializer_class = WasAttributedToSerializer
    queryset = WasAttributedTo.objects.all()

class HadMemberViewSet(viewsets.ModelViewSet):
    serializer_class = HadMemberSerializer
    queryset = HadMember.objects.all()

class WasDerivedFromViewSet(viewsets.ModelViewSet):
    serializer_class = WasDerivedFromSerializer
    queryset = WasDerivedFrom.objects.all()

# class ActivityFlowViewSet(viewsets.ModelViewSet):
#     serializer_class = ActivityFlowSerializer
#     queryset = ActivityFlow.objects.all()

class CollectionViewSet(viewsets.ModelViewSet):
    serializer_class = W3CCollectionSerializer
    queryset = Collection.objects.all()


def convert_to_dict_querysets(listqueryset):

    objdict = {}
    for q in listqueryset:
        objdict[q.id] = q

    return objdict


# simple prov-n view of everything
def allprov(request, format):

    # first store everything in a prov-dictionary
    prefix = {
        "rave": "http://www.rave-survey.org/prov/",
        "voprov": "http://www.ivoa.net/documents/ProvenanceDM/voprov/",
        "org": "http://www.ivoa.net/documents/ProvenanceDM/voprov/org/",
        "vo": "http://www.ivoa.net/documents/ProvenanceDM/voprov/vo",
        "prov": "http://www.w3.org/ns/prov#",  # defined by default
        "xsd": "http://www.w3.org/2000/10/XMLSchema#"  # defined by default
    }

    prov = {
        'prefix': prefix,
        'activity': convert_to_dict_querysets(Activity.objects.all()),
        'activityFlow': convert_to_dict_querysets(ActivityFlow.objects.all()),
        'entity': convert_to_dict_querysets(Entity.objects.all()),
        'collection': convert_to_dict_querysets(Collection.objects.all()),
        'agent': convert_to_dict_querysets(Agent.objects.all()),
        'used': convert_to_dict_querysets(Used.objects.all()),
        'wasGeneratedBy': convert_to_dict_querysets(WasGeneratedBy.objects.all()),
        'wasAssociatedWith': convert_to_dict_querysets(WasAssociatedWith.objects.all()),
        'wasAttributedTo': convert_to_dict_querysets(WasAttributedTo.objects.all()),
        'hadMember': convert_to_dict_querysets(HadMember.objects.all()),
        'wasDerivedFrom': convert_to_dict_querysets(WasDerivedFrom.objects.all()),
        'hadStep': convert_to_dict_querysets(HadStep.objects.all()),
        'wasInformedBy': convert_to_dict_querysets(WasInformedBy.objects.all())
    }

    # serialize it (W3C):
    serializer = W3CProvenanceSerializer(prov)
    data = serializer.data

    # write provenance information in desired format:
    if format == 'PROV-N':
        provstr = PROVNRenderer().render(data)
        return HttpResponse(provstr, content_type='text/plain; charset=utf-8')

    elif format == 'PROV-JSON':
        json_str = PROVJSONRenderer().render(data)
        return HttpResponse(json_str, content_type='application/json; charset=utf-8')

    else:
        # format is not known, return error
        provstr = "Sorry, unknown format %s was requested, cannot handle this." % format

    return HttpResponse(provstr, content_type='text/plain; charset=utf-8')


def prettyprovn(request):
    # use hyperlinks for ids
    # still missing new classes, just used for testing
    activity_list = Activity.objects.order_by('-startTime')[:]
    entity_list = Entity.objects.order_by('-name')[:]
    agent_list = Agent.objects.order_by('-name')[:]
    used_list = Used.objects.order_by('-id')[:]
    wasGeneratedBy_list = WasGeneratedBy.objects.order_by('-id')[:]
    wasAssociatedWith_list = WasAssociatedWith.objects.order_by('-id')[:]
    wasAttributedTo_list = WasAttributedTo.objects.order_by('-id')[:]

    return render(request, 'prov_vo/provn.html',
                 {'activity_list': activity_list,
                  'entity_list': entity_list,
                  'agent_list': agent_list,
                  'used_list': used_list,
                  'wasGeneratedBy_list': wasGeneratedBy_list,
                  'wasAssociatedWith_list': wasAssociatedWith_list,
                  'wasAttributedTo_list': wasAttributedTo_list
                 })


def graph(request):
    return render(request, 'prov_vo/graph.html', {'url': 'graphjson'})


def fullgraphjson(request):
    # TODO: should construct this similar to provdal-version

    activity_list = Activity.objects.all()
    entity_list = Entity.objects.all()
    agent_list = Agent.objects.all()

    used_list = Used.objects.all()
    wasGeneratedBy_list = WasGeneratedBy.objects.all()
    wasAssociatedWith_list = WasAssociatedWith.objects.all()
    wasAttributedTo_list = WasAttributedTo.objects.all()
    hadMember_list = HadMember.objects.all()

    nodes_dict = []
    count_nodes = 0
    count_act = 0

    links_dict = []
    count_link = 0

    map_activity_ids = {}
    map_entity_ids = {}
    map_agent_ids = {}


    for a in activity_list:
        nodes_dict.append({"name": a.name, "type": "activity"})
        map_activity_ids[a.id] = count_nodes
        count_nodes = count_nodes + 1

    for e in entity_list:
        nodes_dict.append({"name": e.name, "type": "entity"})
        map_entity_ids[e.id] = count_nodes
        count_nodes = count_nodes + 1

    for ag in agent_list:
        nodes_dict.append({"name": ag.name, "type": "agent"})
        map_agent_ids[ag.id] = count_nodes
        count_nodes = count_nodes + 1

    # add links (source, target, value)
    for u in used_list:
        links_dict.append({"source": map_activity_ids[u.activity.id], "target": map_entity_ids[u.entity.id], "value": 0.5, "type": "used"})
        count_link = count_link + 1

    for w in wasGeneratedBy_list:
        links_dict.append({"source": map_entity_ids[w.entity.id], "target": map_activity_ids[w.activity.id], "value": 0.5, "type": "wasGeneratedBy"})
        count_link = count_link + 1

    for w in wasAssociatedWith_list:
        links_dict.append({"source": map_activity_ids[w.activity.id], "target": map_agent_ids[w.agent.id], "value": 0.2, "type": "wasAssociatedWith"})
        count_link = count_link + 1

    for w in wasAttributedTo_list:
        links_dict.append({"source": map_entity_ids[w.entity.id], "target": map_agent_ids[w.agent.id], "value": 0.2, "type": "wasAttributedTo"})
        count_link = count_link + 1

    for h in hadMember_list:
        s =  map_entity_ids[h.collection_id]
        #print >>sys.stderr, 'h.collection_id, h.entity_id: ', h.collection_id, ", '"+h.entity_id+"'"
        t = map_entity_ids[h.entity_id]
        #print "map_entity_ids[h.collection_id]"
        #links_dict.append({"source": map_entity_ids[h.collection_id], "target": map_entity_ids[h.entity_id], "value": 0.2, "type": "hadMember"})
        links_dict.append({"source": s, "target": t, "value": 0.2, "type": "hadMember"})
        count_link = count_link + 1


    prov_dict = {"nodes": nodes_dict, "links": links_dict}

    return JsonResponse(prov_dict)



def provdal_form(request):

    if request.method == 'POST':
        form = ProvDalForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
        # process the data in form.cleaned_data as required
            try:
                obj_id = form.cleaned_data['obj_id']
                backward = form.cleaned_data['backward']
                #forward = form.cleaned_data['forward']
                format = form.cleaned_data['format']
                compliance = form.cleaned_data['model']

                return HttpResponseRedirect(reverse('prov_vo:provdal')+"?ID=%s&BACKWARD=%s&FORMAT=%s&MODEL=%s" % (str(obj_id), str(backward), str(format), str(compliance)))

            except ValueError:
                form = ProvDalForm(request.POST)
        else:
            #print form.errors # or add_error??
            pass

    # if a GET (or any other method) we'll create a blank form
    else:
        form = ProvDalForm()

    return render(request, 'prov_vo/provdalform.html', {'form': form})


def provdal(request):

    # entity_id = request.GET.get('ID') #default: None
    # There can be more than one ID given, so:
    id_list = request.GET.getlist('ID')
    backward = request.GET.get('BACKWARD', 'ALL') # can be 0,1,2, etc. or ALL
    #forward = request.GET.get('FORWARD', '0') # can be 0,1,2, etc. or ALL
    format = request.GET.get('FORMAT', 'PROV-N') # can be PROV-N, PROV-JSON, VOTABLE
    model = request.GET.get('MODEL', 'IVOA')  # one of IVOA, W3C (or None?)

    if format == 'GRAPH':
        ids = ''
        for i in id_list:
            ids += 'ID=%s&' % i
        return render(request, 'prov_vo/provdal_graph.html',
            {'url': reverse('prov_vo:provdal') + "?%sBACKWARD=%s&FORMAT=GRAPH-JSON&MODEL=%s" % (ids, str(backward), str(model))})

    # check step_flag, store as 'follow' for provenance functions
    backcountdown = -1    
    if backward == "ALL":
        # will search for further provenance, recursively
        follow = True # always
        backcountdown = -1
    elif backward == "1":
        # will just go back one step (backwards in time)
        follow = False
    elif backward.isdigit():
        backcountdown = int(backward)
        follow = True
    else:
        # raise error: not supported
        raise ValidationError(
            'Invalid value: %(value)s is not supported',
            code='invalid',
            params={'value': backward},
        )

    prefix = {
        "rave": "http://www.rave-survey.org/prov/",
        "voprov": "http://www.ivoa.net/documents/ProvenanceDM/voprov/",
        "org": "http://www.ivoa.net/documents/ProvenanceDM/voprov/org/",
        "vo": "http://www.ivoa.net/documents/ProvenanceDM/voprov/vo",
        "prov": "http://www.w3.org/ns/prov#",  # defined by default
        "xsd": "http://www.w3.org/2000/10/XMLSchema#"  # defined by default
    }

    prov = {
        'prefix': prefix,
        'activity': {},
        'activityFlow': {},
        'entity': {},
        'collection': {},  # not used, yet, stored with entities
        'agent': {},
        'used': {},
        'wasGeneratedBy': {},
        'wasAssociatedWith': {},
        'wasAttributedTo': {},
        'hadMember': {},
        'wasDerivedFrom': {},
        'hadStep': {},
        'wasInformedBy': {},
        'wasInfluencedBy': {}
    }

    # Note: even if collection class is used, Entity.objects.all() still contains all entities
    for obj_id in id_list:

        try:
            entity = Entity.objects.get(id=obj_id)
            # store current entity in dict and search for provenance:
            prov['entity'][entity.id] = entity
            prov = utils.find_entity(entity, prov, backcountdown, follow=follow)
        except Entity.DoesNotExist:
            pass
            # do not return, just continue with other ids
            # (and if none of them exists, return empty provenance record)

        try:
            activity = Activity.objects.get(id=obj_id)
            # or store current activity and search for its provenance
            activity_type = utils.get_activity_type(obj_id)

            prov[activity_type][activity.id] = activity
            prov = utils.find_activity(activity, prov, backcountdown, follow=follow)
        except Activity.DoesNotExist:
            pass


    # The prov dictionary now contains the complete provenance information,
    # for all given entity ids,
    # in the form of a dictionary of querysets. First serialize them according to
    # the specified model.
    if model == "W3C":
        serializer = W3CProvenanceSerializer(prov)
    elif model == "IVOA":
        serializer = VOProvenanceSerializer(prov)
    else:
        # raise error: not supported
        raise ValidationError(
           'Invalid value: %(value)s is not supported',
            code='invalid',
            params={'value': model},
        )

    data = serializer.data

    # Render provenance information in desired format:
    if format == 'PROV-N':
        provstr = PROVNRenderer().render(data)
        return HttpResponse(provstr, content_type='text/plain; charset=utf-8')

    elif format == 'PROV-JSON':

        json_str = PROVJSONRenderer().render(data)
        return HttpResponse(json_str, content_type='application/json; charset=utf-8')

    elif format == "GRAPH-JSON":
        # need to re-structure the serialized data
        serializer = ProvenanceGraphSerializer(data, model=model)
        prov_dict = serializer.data
        return JsonResponse(prov_dict)

    else:
        # format is not known, return error
        provstr = "Sorry, unknown format %s was requested, cannot handle this." % format
        return HttpResponse(provstr, content_type='text/plain; charset=utf-8')