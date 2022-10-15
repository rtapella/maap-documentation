import geoviews as gv
import holoviews as hv
import panel as pn
import param
from geoviews import opts, tile_sources as gvts
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

class Dashboard(param.Parameterized):
    button = param.Action(lambda x: x.param.trigger('button'), label='Update geometries')
    mapview = Mapview()

    @param.depends('button')
    def update_geometries(self):
        box_data = self.mapview.box_stream.data
        print(f"box data {box_data}")
        return pn.widgets.TextInput(name='A widget', value=str(box_data))

    def view(self):
        return pn.Row(
            pn.Column(self.mapview.show()),
            pn.Column(self.param['button'], self.update_geometries)
        )

d = Dashboard()
d.view().show()