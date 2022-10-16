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

provider = 'NASA_MAAP'
cmr_search_url = "https://cmr.maap-project.org/search"

class Mapview(param.Parameterized):
    tiles         = gvts.CartoLight.opts('WMTS', xaxis=None, yaxis=None, width=1200, height=700, global_extent=True)
    box_polygons  = gv.Polygons([]).opts(fill_alpha=0.1)
    box_colours   = ['red','blue','green','orange','purple']
    box_stream    = hv.streams.BoxEdit(source=box_polygons, num_objects=1, styles={'fill_color': box_colours})

    def show(self):
        return self.tiles * self.box_polygons

    def add_layer_to_map(self, s3_url):
        tititler_url = "https://l40l1vwmvi.execute-api.us-west-2.amazonaws.com"
        rescale = "0,400"
        colormap_name = "gist_earth_r"
        color_formula = "gamma r 2"
        #tititler_url = "https://titiler.maap-project.org"
        tiles_url = tititler_url + "/cog/tiles/{Z}/{Y}/{X}.png?url=" + f"{s3_url}&rescale={rescale}&colormap_name={colormap_name}&color_formula={color_formula}"
        #tiles_url = tititler_url + "/cog/tiles/{z}/{x}/{y}.png?url=" + f"{granule_s3_url}&rescale=350,850&colormap_name={colormap_name}"
        data_layer = gvts.WMTS(tiles_url)
        return self.tiles * data_layer

class CollectionSelection(param.Parameterized):
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
    update_geometries_button = param.Action(lambda x: x.param.trigger('update_geometries_button'), label='Update geometries')
    granule_button = param.Action(lambda x: x.param.trigger('granule_button'), label='Search for granules')
    add_layer_to_map_button = param.Action(lambda x: x.param.trigger('add_layer_to_map_button'), label='Update Map')
    collection_selection = CollectionSelection().show()
    mapview = Mapview()

    @param.depends('update_geometries_button')
    def update_geometry(self):
        box_data = self.mapview.box_stream.data or {}
        llong = box_data.get('x0', [0.])[0]
        llat =  box_data.get('y0', [0.])[0]
        ulong = box_data.get('x1', [0.])[0]
        ulat = box_data.get('y1', [0.])[0]
        self.bbox = ','.join(map(str, [llong, llat, ulong, ulat]))
        return pn.Row(
            pn.widgets.FloatInput(name='Lower Longitude', value=llong),
            pn.widgets.FloatInput(name='Lower Latitude', value=llat),
            pn.widgets.FloatInput(name='Upper Longitude', value=ulong),
            pn.widgets.FloatInput(name='Upper Latitude', value=ulat),
        )

    @param.depends('granule_button') 
    def search_for_granules(self):
        selected_collection = self.collection_selection.value
        granules_search = GranulesSearch(collection=selected_collection, bbox = self.bbox)
        self.granules_search = granules_search.show()
        return self.granules_search

    @param.depends('add_layer_to_map_button')
    def add_layer_to_map(self):
        return self.mapview.add_layer_to_map(self.granules_search.value)

    def view(self):
        return pn.Row(
            pn.Column(self.mapview.show()),
            pn.Column(
                self.collection_selection,
                self.param['update_geometries_button'],
                self.update_geometry,
                self.param['granule_button'],
                self.search_for_granules,
                self.param['add_layer_to_map_button'],
                self.add_layer_to_map
            )
        )

d = Dashboard()
d.view().show()