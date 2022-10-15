from email.policy import default
import geoviews as gv
import holoviews as hv
import panel as pn
import param
from geoviews import opts, tile_sources as gvts
import requests
import json
gv.extension('bokeh', logo=False)
pn.extension()

# opts.defaults(
#     opts.Layout(sublabel_format='', vspace=0.1, hspace=0.1, fig_size=200),
#     opts.WMTS(zoom=0))

class Mapview(param.Parameterized):
    tiles         = gvts.CartoLight.opts('WMTS', xaxis=None, yaxis=None, width=1200, height=700, global_extent=True)
    box_polygons  = gv.Polygons([]).opts(fill_alpha=0.1)
    box_colours   = ['red','blue','green','orange','purple']
    box_stream    = hv.streams.BoxEdit(source=box_polygons, num_objects=1, styles={'fill_color': box_colours})

    def show(self):
        return self.tiles * self.box_polygons

class CollectionSelection(param.Parameterized):
    provider = 'NASA_MAAP'
    cmr_search_url = "https://cmr.maap-project.org/search"
    collections_search_url = f"{cmr_search_url}/collections.json?provider={provider}&page_size=100"
    granules_search_url = f"{cmr_search_url}/collections.json"
    
    def perform_search(self):
        response = requests.get(self.collections_search_url)
        collections = json.loads(response.text)['feed']['entry']
        self.collection_names = list(collection['short_name'] for collection in collections)

    def show(self):
        self.perform_search()
        return pn.widgets.Select(name='Select', options=self.collection_names)    

class GranulesSearch(param.Parameterized):
    cmr_search_url = "https://cmr.maap-project.org/search"
    granules_search_url = f"{cmr_search_url}/granules.json"
    collection = ''
    bbox = ''
    granule_urls = []

    def perform_search(self):
        search_url_with_params = f"{self.granules_search_url}?short_name={self.collection}&bounding_box[]={self.bbox}"
        # Search for granules and select a granule to visualize
        # get all granules from search
        granules_response = requests.get(search_url_with_params)
        granules_objects = json.loads(granules_response.text)['feed']['entry']
        self.granule_urls = list(granule['links'][0]['href'] for granule in granules_objects)

    def show(self):
        self.perform_search()
        return pn.widgets.Select(name='Select', options=self.granule_urls)    

class Dashboard(param.Parameterized):
    button = param.Action(lambda x: x.param.trigger('button'), label='Update geometries')
    granule_button = param.Action(lambda x: x.param.trigger('granule_button'), label='Search for granules')
    collection_selection = CollectionSelection()
    mapview = Mapview()

    @param.depends('button')
    def update_geometry(self):
        box_data = self.mapview.box_stream.data or {}
        print(f"box data {box_data}")
        # print(f"selected_collection {self.collection_selection.value}")
        self.lower_longitude = box_data.get('x0', [0.])[0]
        self.lower_latitude =  box_data.get('y0', [0.])[0]
        self.upper_longitude = box_data.get('x1', [0.])[0]
        self.upper_latitude = box_data.get('y1', [0.])[0]
        return pn.Row(
            pn.widgets.FloatInput(name='Lower Latitude', value=self.lower_latitude),
            pn.widgets.FloatInput(name='Lower Longitude', value=self.lower_longitude),
            pn.widgets.FloatInput(name='Upper Longitude', value=self.upper_longitude),
            pn.widgets.FloatInput(name='Upper Longitude', value=self.upper_latitude),
        )

    @param.depends('granule_button') 
    def search_for_granules(self):
        granules_search = GranulesSearch(collection='ABLVIS2', bbox = '0,0,0,0')
        return granules_search.show()


    def view(self):
        return pn.Row(
            pn.Row(
                pn.Column(self.mapview.show()),
                pn.Column(self.collection_selection.show()),
            ),
            pn.Column(self.param['button'], self.update_geometry),
            pn.Column(self.param['granule_button'], self.search_for_granules)
        )

d = Dashboard()
d.view().show()