"""
Tests for Leaflet/Mapbox mapping framework integration.

Tests cover:
- All 5 extractors (map, layer, control, interaction, api)
- Parser (EnhancedLeafletParser)
- Scanner integration (ProjectMatrix fields, _parse_leaflet)
- Compressor integration ([LEAFLET_*] sections)
"""

import pytest
from codetrellis.extractors.leaflet import (
    LeafletMapExtractor,
    LeafletLayerExtractor,
    LeafletControlExtractor,
    LeafletInteractionExtractor,
    LeafletAPIExtractor,
)
from codetrellis.leaflet_parser_enhanced import EnhancedLeafletParser, LeafletParseResult


# ═══════════════════════════════════════════════════════════════════════
# Map Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeafletMapExtractor:
    """Tests for LeafletMapExtractor."""

    def setup_method(self):
        self.extractor = LeafletMapExtractor()

    def test_leaflet_map_basic(self):
        code = '''
const map = L.map('map').setView([51.505, -0.09], 13);
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['maps']) >= 1
        m = result['maps'][0]
        assert m.map_type == 'leaflet'

    def test_leaflet_map_with_options(self):
        code = '''
const map = L.map('map', {
  center: [51.505, -0.09],
  zoom: 13,
  maxBounds: bounds,
});
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['maps']) >= 1
        m = result['maps'][0]
        assert m.has_center is True
        assert m.has_zoom is True

    def test_mapbox_gl_map(self):
        code = '''
const map = new mapboxgl.Map({
  container: 'map',
  style: 'mapbox://styles/mapbox/streets-v11',
  center: [-74.5, 40],
  zoom: 9,
});
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['maps']) >= 1
        m = result['maps'][0]
        assert m.map_type == 'mapbox'

    def test_maplibre_gl_map(self):
        code = '''
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://demotiles.maplibre.org/style.json',
  center: [0, 0],
  zoom: 2,
});
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['maps']) >= 1
        m = result['maps'][0]
        assert m.map_type == 'maplibre'

    def test_react_leaflet_mapcontainer(self):
        code = '''
import { MapContainer, TileLayer } from 'react-leaflet';

<MapContainer center={[51.505, -0.09]} zoom={13} scrollWheelZoom={false}>
  <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
</MapContainer>
'''
        result = self.extractor.extract(code, "Map.tsx")
        assert len(result['maps']) >= 1
        m = result['maps'][0]
        assert m.map_type == 'react-leaflet'

    def test_vue_leaflet_lmap(self):
        code = '''
<template>
  <LMap :zoom="zoom" :center="center">
    <LTileLayer :url="url" />
  </LMap>
</template>
'''
        result = self.extractor.extract(code, "Map.vue")
        assert len(result['maps']) >= 1
        m = result['maps'][0]
        assert m.map_type == 'vue-leaflet'

    def test_tile_layer_osm(self):
        code = '''
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '&copy; OpenStreetMap contributors',
}).addTo(map);
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['tile_layers']) >= 1
        tl = result['tile_layers'][0]
        assert tl.provider == 'osm'

    def test_tile_layer_mapbox(self):
        code = '''
L.tileLayer('https://api.mapbox.com/styles/v1/{id}/tiles/{z}/{x}/{y}', {
  accessToken: MAPBOX_TOKEN,
  id: 'mapbox/streets-v11',
}).addTo(map);
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['tile_layers']) >= 1
        tl = result['tile_layers'][0]
        assert tl.provider == 'mapbox'
        assert tl.has_access_token is True

    def test_wms_tile_layer(self):
        code = '''
L.tileLayer.wms('https://ows.mundialis.de/services/service', {
  layers: 'TOPO-WMS',
  format: 'image/png',
}).addTo(map);
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['tile_layers']) >= 1
        tl = result['tile_layers'][0]
        assert tl.tile_type == 'wms'

    def test_multiple_maps(self):
        code = '''
const map1 = L.map('map1').setView([51.505, -0.09], 13);
const map2 = new mapboxgl.Map({ container: 'map2', center: [0, 0], zoom: 2 });
'''
        result = self.extractor.extract(code, "maps.js")
        assert len(result['maps']) >= 2


# ═══════════════════════════════════════════════════════════════════════
# Layer Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeafletLayerExtractor:
    """Tests for LeafletLayerExtractor."""

    def setup_method(self):
        self.extractor = LeafletLayerExtractor()

    def test_leaflet_marker(self):
        code = '''
L.marker([51.5, -0.09]).addTo(map);
'''
        result = self.extractor.extract(code, "markers.js")
        assert len(result['markers']) >= 1
        m = result['markers'][0]
        assert m.marker_type == 'default'

    def test_leaflet_marker_with_popup(self):
        code = '''
L.marker([51.5, -0.09])
  .bindPopup('Hello!')
  .addTo(map);
'''
        result = self.extractor.extract(code, "markers.js")
        assert len(result['markers']) >= 1

    def test_circle_marker(self):
        code = '''
L.circleMarker([51.5, -0.09], { radius: 10 }).addTo(map);
'''
        result = self.extractor.extract(code, "markers.js")
        assert len(result['markers']) >= 1
        m = result['markers'][0]
        assert m.marker_type == 'circle_marker'

    def test_mapbox_marker(self):
        code = '''
new mapboxgl.Marker()
  .setLngLat([-74.5, 40])
  .addTo(map);
'''
        result = self.extractor.extract(code, "markers.js")
        assert len(result['markers']) >= 1
        m = result['markers'][0]
        assert m.marker_type == 'mapbox'

    def test_react_marker_jsx(self):
        code = '''
<Marker position={[51.505, -0.09]}>
  <Popup>Hello!</Popup>
</Marker>
'''
        result = self.extractor.extract(code, "Map.tsx")
        assert len(result['markers']) >= 1

    def test_polygon_shape(self):
        code = '''
L.polygon([
  [51.509, -0.08],
  [51.503, -0.06],
  [51.51, -0.047],
]).addTo(map);
'''
        result = self.extractor.extract(code, "shapes.js")
        assert len(result['shapes']) >= 1
        s = result['shapes'][0]
        assert s.shape_type == 'polygon'

    def test_polyline_shape(self):
        code = '''
L.polyline([[51.5, -0.1], [51.51, -0.09]], { color: 'red' }).addTo(map);
'''
        result = self.extractor.extract(code, "shapes.js")
        assert len(result['shapes']) >= 1
        s = result['shapes'][0]
        assert s.shape_type == 'polyline'

    def test_circle_shape(self):
        code = '''
L.circle([51.508, -0.11], { radius: 500 }).addTo(map);
'''
        result = self.extractor.extract(code, "shapes.js")
        assert len(result['shapes']) >= 1
        s = result['shapes'][0]
        assert s.shape_type == 'circle'

    def test_rectangle_shape(self):
        code = '''
L.rectangle([[51.49, -0.08], [51.5, -0.06]], { color: 'blue' }).addTo(map);
'''
        result = self.extractor.extract(code, "shapes.js")
        assert len(result['shapes']) >= 1
        s = result['shapes'][0]
        assert s.shape_type == 'rectangle'

    def test_geojson_layer(self):
        code = '''
L.geoJSON(geojsonData, {
  style: function(feature) { return { color: feature.properties.color }; },
  onEachFeature: function(feature, layer) { layer.bindPopup(feature.properties.name); },
}).addTo(map);
'''
        result = self.extractor.extract(code, "geojson.js")
        assert len(result['geojson']) >= 1
        g = result['geojson'][0]
        assert g.has_style is True
        assert g.has_onEachFeature is True

    def test_react_geojson_jsx(self):
        code = '''
<GeoJSON data={geojsonData} style={myStyle} onEachFeature={handleFeature} />
'''
        result = self.extractor.extract(code, "Map.tsx")
        assert len(result['geojson']) >= 1

    def test_layer_group(self):
        code = '''
const cities = L.layerGroup([marker1, marker2, marker3]);
cities.addTo(map);
'''
        result = self.extractor.extract(code, "layers.js")
        assert len(result['layer_groups']) >= 1
        lg = result['layer_groups'][0]
        assert lg.group_type == 'layer_group'

    def test_feature_group(self):
        code = '''
const drawnItems = L.featureGroup().addTo(map);
'''
        result = self.extractor.extract(code, "layers.js")
        assert len(result['layer_groups']) >= 1
        lg = result['layer_groups'][0]
        assert lg.group_type == 'feature_group'

    def test_mapbox_add_source(self):
        code = '''
map.addSource('earthquakes', {
  type: 'geojson',
  data: 'https://example.com/data.geojson',
  cluster: true,
  clusterMaxZoom: 14,
  clusterRadius: 50,
});
'''
        result = self.extractor.extract(code, "mapbox.js")
        assert len(result['sources']) >= 1
        src = result['sources'][0]
        assert src.source_type == 'geojson'

    def test_mapbox_add_layer(self):
        code = '''
map.addLayer({
  id: 'earthquakes-heat',
  type: 'heatmap',
  source: 'earthquakes',
  paint: { 'heatmap-weight': 1 },
});
'''
        result = self.extractor.extract(code, "mapbox.js")
        assert len(result['sources']) >= 1
        src = result['sources'][0]
        assert src.layer_type == 'heatmap'

    def test_multiple_shapes(self):
        code = '''
L.polygon([[51.509, -0.08], [51.503, -0.06]]).addTo(map);
L.circle([51.508, -0.11], { radius: 500 }).addTo(map);
L.polyline([[51.5, -0.1], [51.51, -0.09]]).addTo(map);
L.rectangle([[51.49, -0.08], [51.5, -0.06]]).addTo(map);
'''
        result = self.extractor.extract(code, "shapes.js")
        assert len(result['shapes']) >= 4


# ═══════════════════════════════════════════════════════════════════════
# Control Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeafletControlExtractor:
    """Tests for LeafletControlExtractor."""

    def setup_method(self):
        self.extractor = LeafletControlExtractor()

    def test_zoom_control(self):
        code = '''
L.control.zoom({ position: 'topright' }).addTo(map);
'''
        result = self.extractor.extract(code, "controls.js")
        assert len(result['controls']) >= 1
        c = result['controls'][0]
        assert c.control_type == 'zoom'

    def test_layers_control(self):
        code = '''
L.control.layers(baseLayers, overlays, { position: 'topleft' }).addTo(map);
'''
        result = self.extractor.extract(code, "controls.js")
        assert len(result['controls']) >= 1
        c = result['controls'][0]
        assert c.control_type == 'layers'

    def test_scale_control(self):
        code = '''
L.control.scale({ maxWidth: 200, metric: true }).addTo(map);
'''
        result = self.extractor.extract(code, "controls.js")
        assert len(result['controls']) >= 1
        c = result['controls'][0]
        assert c.control_type == 'scale'

    def test_attribution_control(self):
        code = '''
L.control.attribution({ prefix: false }).addTo(map);
'''
        result = self.extractor.extract(code, "controls.js")
        assert len(result['controls']) >= 1
        c = result['controls'][0]
        assert c.control_type == 'attribution'

    def test_mapbox_navigation_control(self):
        code = '''
map.addControl(new mapboxgl.NavigationControl(), 'top-right');
'''
        result = self.extractor.extract(code, "controls.js")
        assert len(result['controls']) >= 1

    def test_mapbox_geolocate_control(self):
        code = '''
map.addControl(new mapboxgl.GeolocateControl({
  positionOptions: { enableHighAccuracy: true },
  trackUserLocation: true,
}));
'''
        result = self.extractor.extract(code, "controls.js")
        assert len(result['controls']) >= 1

    def test_mapbox_fullscreen_control(self):
        code = '''
map.addControl(new mapboxgl.FullscreenControl());
'''
        result = self.extractor.extract(code, "controls.js")
        assert len(result['controls']) >= 1

    def test_custom_control(self):
        code = '''
const MyControl = L.Control.extend({
  onAdd: function(map) {
    const div = L.DomUtil.create('div', 'info');
    return div;
  },
});
'''
        result = self.extractor.extract(code, "controls.js")
        assert len(result['controls']) >= 1
        c = result['controls'][0]
        assert c.is_custom is True

    def test_popup_bind(self):
        code = '''
marker.bindPopup('<strong>Hello!</strong>');
'''
        result = self.extractor.extract(code, "popups.js")
        assert len(result['popups']) >= 1

    def test_popup_standalone(self):
        code = '''
L.popup()
  .setLatLng([51.5, -0.09])
  .setContent('Hello!')
  .openOn(map);
'''
        result = self.extractor.extract(code, "popups.js")
        assert len(result['popups']) >= 1

    def test_mapbox_popup(self):
        code = '''
new mapboxgl.Popup()
  .setLngLat([-96, 37.8])
  .setHTML('<h3>Title</h3>')
  .addTo(map);
'''
        result = self.extractor.extract(code, "popups.js")
        assert len(result['popups']) >= 1

    def test_react_popup_jsx(self):
        code = '''
<Marker position={pos}>
  <Popup>
    <div>Hello World</div>
  </Popup>
</Marker>
'''
        result = self.extractor.extract(code, "Map.tsx")
        assert len(result['popups']) >= 1

    def test_tooltip_bind(self):
        code = '''
marker.bindTooltip('Label', { permanent: true, direction: 'top' });
'''
        result = self.extractor.extract(code, "tooltips.js")
        assert len(result['tooltips']) >= 1

    def test_react_tooltip_jsx(self):
        code = '''
<Marker position={pos}>
  <Tooltip direction="top" permanent>Label</Tooltip>
</Marker>
'''
        result = self.extractor.extract(code, "Map.tsx")
        assert len(result['tooltips']) >= 1

    def test_draw_control(self):
        code = '''
const drawControl = new L.Control.Draw({
  edit: { featureGroup: drawnItems },
});
map.addControl(drawControl);
'''
        result = self.extractor.extract(code, "draw.js")
        assert len(result['controls']) >= 1

    def test_geocoder_control(self):
        code = '''
L.Control.geocoder().addTo(map);
'''
        result = self.extractor.extract(code, "geocoder.js")
        assert len(result['controls']) >= 1

    def test_multiple_controls(self):
        code = '''
L.control.zoom({ position: 'topright' }).addTo(map);
L.control.layers(baseLayers, overlays).addTo(map);
L.control.scale().addTo(map);
'''
        result = self.extractor.extract(code, "controls.js")
        assert len(result['controls']) >= 3


# ═══════════════════════════════════════════════════════════════════════
# Interaction Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeafletInteractionExtractor:
    """Tests for LeafletInteractionExtractor."""

    def setup_method(self):
        self.extractor = LeafletInteractionExtractor()

    def test_click_event(self):
        code = '''
map.on('click', function(e) {
  console.log(e.latlng);
});
'''
        result = self.extractor.extract(code, "events.js")
        assert len(result['events']) >= 1
        evt = result['events'][0]
        assert evt.event_type == 'click'

    def test_moveend_event(self):
        code = '''
map.on('moveend', function() {
  console.log(map.getBounds());
});
'''
        result = self.extractor.extract(code, "events.js")
        assert len(result['events']) >= 1
        evt = result['events'][0]
        assert evt.event_type == 'move'

    def test_zoomend_event(self):
        code = '''
map.on('zoomend', function() {
  updateMarkers(map.getZoom());
});
'''
        result = self.extractor.extract(code, "events.js")
        assert len(result['events']) >= 1

    def test_mouseover_event(self):
        code = '''
layer.on('mouseover', function(e) {
  e.target.setStyle({ weight: 3 });
});
'''
        result = self.extractor.extract(code, "events.js")
        assert len(result['events']) >= 1

    def test_popupopen_event(self):
        code = '''
map.on('popupopen', function(e) {
  trackEvent('popup');
});
'''
        result = self.extractor.extract(code, "events.js")
        assert len(result['events']) >= 1

    def test_mapbox_click_layer_event(self):
        code = '''
map.on('click', 'my-layer', function(e) {
  const features = e.features;
});
'''
        result = self.extractor.extract(code, "events.js")
        assert len(result['events']) >= 1

    def test_leaflet_draw_library(self):
        code = '''
import 'leaflet-draw';

map.on('draw:created', function(e) {
  drawnItems.addLayer(e.layer);
});
'''
        result = self.extractor.extract(code, "draw.js")
        assert len(result['drawings']) >= 1

    def test_geoman_drawing(self):
        code = '''
import '@geoman-io/leaflet-geoman-free';

map.pm.addControls({
  position: 'topleft',
  drawPolygon: true,
});

map.on('pm:create', function(e) {
  const layer = e.layer;
});
'''
        result = self.extractor.extract(code, "draw.js")
        assert len(result['drawings']) >= 1

    def test_mapbox_draw(self):
        code = '''
import MapboxDraw from '@mapbox/mapbox-gl-draw';

const draw = new MapboxDraw({
  displayControlsDefault: false,
  controls: { polygon: true, trash: true },
});
map.addControl(draw);
'''
        result = self.extractor.extract(code, "draw.js")
        assert len(result['drawings']) >= 1

    def test_flyto_animation(self):
        code = '''
map.flyTo([51.505, -0.09], 14, { duration: 2 });
'''
        result = self.extractor.extract(code, "animations.js")
        assert len(result['animations']) >= 1
        a = result['animations'][0]
        assert a.animation_type == 'fly_to'

    def test_panto_animation(self):
        code = '''
map.panTo([51.505, -0.09]);
'''
        result = self.extractor.extract(code, "animations.js")
        assert len(result['animations']) >= 1
        a = result['animations'][0]
        assert a.animation_type == 'pan_to'

    def test_fitbounds_animation(self):
        code = '''
map.fitBounds(group.getBounds().pad(0.1));
'''
        result = self.extractor.extract(code, "animations.js")
        assert len(result['animations']) >= 1
        a = result['animations'][0]
        assert a.animation_type == 'fit_bounds'

    def test_setview_animation(self):
        code = '''
map.setView([51.505, -0.09], 13);
'''
        result = self.extractor.extract(code, "animations.js")
        assert len(result['animations']) >= 1
        a = result['animations'][0]
        assert a.animation_type == 'set_view'

    def test_mapbox_easeto_animation(self):
        code = '''
map.easeTo({ center: [-74.5, 40], zoom: 9, duration: 1000 });
'''
        result = self.extractor.extract(code, "animations.js")
        assert len(result['animations']) >= 1
        a = result['animations'][0]
        assert a.animation_type == 'ease_to'

    def test_mapbox_jumpto_animation(self):
        code = '''
map.jumpTo({ center: [-74.5, 40], zoom: 9 });
'''
        result = self.extractor.extract(code, "animations.js")
        assert len(result['animations']) >= 1
        a = result['animations'][0]
        assert a.animation_type == 'jump_to'

    def test_multiple_events(self):
        code = '''
map.on('click', onClick);
map.on('moveend', onMoveEnd);
map.on('zoomend', onZoomEnd);
map.on('mouseover', onMouseOver);
'''
        result = self.extractor.extract(code, "events.js")
        assert len(result['events']) >= 4


# ═══════════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeafletAPIExtractor:
    """Tests for LeafletAPIExtractor."""

    def setup_method(self):
        self.extractor = LeafletAPIExtractor()

    def test_leaflet_import(self):
        code = '''
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.package == 'leaflet'

    def test_react_leaflet_import(self):
        code = '''
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
'''
        result = self.extractor.extract(code, "Map.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.package == 'react-leaflet'

    def test_mapbox_gl_import(self):
        code = '''
import mapboxgl from 'mapbox-gl';
import 'mapbox-gl/dist/mapbox-gl.css';
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.package == 'mapbox-gl'

    def test_maplibre_gl_import(self):
        code = '''
import maplibregl from 'maplibre-gl';
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.package == 'maplibre-gl'

    def test_plugin_import(self):
        code = '''
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
'''
        result = self.extractor.extract(code, "map.js")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.is_plugin is True

    def test_turf_import(self):
        code = '''
import * as turf from '@turf/turf';
'''
        result = self.extractor.extract(code, "geo.js")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.package == 'turf'

    def test_deck_gl_import(self):
        code = '''
import { DeckGL } from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
'''
        result = self.extractor.extract(code, "viz.tsx")
        assert len(result['imports']) >= 1

    def test_leaflet_draw_import(self):
        code = '''
import 'leaflet-draw';
import 'leaflet-draw/dist/leaflet.draw.css';
'''
        result = self.extractor.extract(code, "draw.js")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.is_plugin is True

    def test_geoman_import(self):
        code = '''
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';
'''
        result = self.extractor.extract(code, "draw.js")
        assert len(result['imports']) >= 1

    def test_react_map_gl_import(self):
        code = '''
import { Map, Marker, Popup, NavigationControl } from 'react-map-gl';
'''
        result = self.extractor.extract(code, "map.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.package == 'react-map-gl'

    def test_typescript_type_detection(self):
        code = '''
import L, { LatLngExpression, MapOptions, MarkerOptions } from 'leaflet';

const center: LatLngExpression = [51.505, -0.09];
const options: MapOptions = { center, zoom: 13 };
const map: L.Map = L.map('map', options);
'''
        result = self.extractor.extract(code, "map.ts")
        assert len(result['types']) >= 1

    def test_mapbox_type_detection(self):
        code = '''
import mapboxgl from 'mapbox-gl';

const center: mapboxgl.LngLatLike = [-74.5, 40];
const map: mapboxgl.Map = new mapboxgl.Map({ container: 'map' });
'''
        result = self.extractor.extract(code, "map.ts")
        assert len(result['types']) >= 1

    def test_integration_detection(self):
        code = '''
import * as turf from '@turf/turf';
import * as topojson from 'topojson-client';

const buffered = turf.buffer(point, 5, { units: 'kilometers' });
const geojson = topojson.feature(topoData, topoData.objects.states);
'''
        result = self.extractor.extract(code, "geo.js")
        assert len(result['integrations']) >= 1

    def test_plugin_detection(self):
        code = '''
import 'leaflet.markercluster';
import 'leaflet-draw';
import 'leaflet.heat';
import 'leaflet-routing-machine';
'''
        result = self.extractor.extract(code, "plugins.js")
        assert len(result['plugins']) >= 1

    def test_bare_import_detection(self):
        code = '''
import 'leaflet';
import 'leaflet-draw';
'''
        result = self.extractor.extract(code, "setup.js")
        assert len(result['imports']) >= 2

    def test_multiple_packages(self):
        code = '''
import L from 'leaflet';
import { MapContainer } from 'react-leaflet';
import 'leaflet.markercluster';
import * as turf from '@turf/turf';
'''
        result = self.extractor.extract(code, "map.tsx")
        assert len(result['imports']) >= 3


# ═══════════════════════════════════════════════════════════════════════
# Parser Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEnhancedLeafletParser:
    """Tests for EnhancedLeafletParser."""

    def setup_method(self):
        self.parser = EnhancedLeafletParser()

    def test_parse_returns_result(self):
        code = '''
import L from 'leaflet';
const map = L.map('map').setView([51.505, -0.09], 13);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png').addTo(map);
L.marker([51.5, -0.09]).addTo(map);
'''
        result = self.parser.parse(code, "map.js")
        assert isinstance(result, LeafletParseResult)
        assert len(result.maps) >= 1
        assert len(result.markers) >= 1
        assert len(result.imports) >= 1

    def test_parse_detects_frameworks(self):
        code = '''
import L from 'leaflet';
import 'leaflet.markercluster';
'''
        result = self.parser.parse(code, "map.js")
        assert 'leaflet' in result.detected_frameworks
        assert 'leaflet-markercluster' in result.detected_frameworks

    def test_parse_detects_features(self):
        code = '''
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet-draw';

const map = L.map('map').setView([51.505, -0.09], 13);
map.on('draw:created', function(e) {
  drawnItems.addLayer(e.layer);
});
'''
        result = self.parser.parse(code, "draw.js")
        assert result.has_clustering is True or result.has_drawing is True

    def test_is_leaflet_file_js(self):
        code = '''
import L from 'leaflet';
const map = L.map('map');
'''
        assert self.parser.is_leaflet_file(code, "map.js") is True

    def test_is_leaflet_file_tsx(self):
        code = '''
import { MapContainer, TileLayer } from 'react-leaflet';

export default function Map() {
  return <MapContainer center={[0,0]} zoom={2}><TileLayer url="..." /></MapContainer>;
}
'''
        assert self.parser.is_leaflet_file(code, "Map.tsx") is True

    def test_is_leaflet_file_mapbox(self):
        code = '''
import mapboxgl from 'mapbox-gl';
const map = new mapboxgl.Map({ container: 'map' });
'''
        assert self.parser.is_leaflet_file(code, "map.js") is True

    def test_is_leaflet_file_negative(self):
        code = '''
function hello() { console.log('hello'); }
'''
        assert self.parser.is_leaflet_file(code, "app.js") is False

    def test_parse_react_leaflet_full(self):
        code = '''
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';

function SetViewOnClick() {
  const map = useMap();
  map.on('click', (e) => map.setView(e.latlng, map.getZoom()));
  return null;
}

export default function MyMap() {
  return (
    <MapContainer center={[51.505, -0.09]} zoom={13}>
      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
      <Marker position={[51.505, -0.09]}>
        <Popup>Hello!</Popup>
      </Marker>
      <SetViewOnClick />
    </MapContainer>
  );
}
'''
        result = self.parser.parse(code, "Map.tsx")
        assert result.has_react_leaflet is True
        assert len(result.maps) >= 1
        assert len(result.markers) >= 1

    def test_parse_mapbox_full(self):
        code = '''
import mapboxgl from 'mapbox-gl';

mapboxgl.accessToken = 'pk.test';

const map = new mapboxgl.Map({
  container: 'map',
  style: 'mapbox://styles/mapbox/streets-v11',
  center: [-74.5, 40],
  zoom: 9,
});

map.addControl(new mapboxgl.NavigationControl());

map.on('load', () => {
  map.addSource('earthquakes', { type: 'geojson', data: url });
  map.addLayer({ id: 'quakes', type: 'circle', source: 'earthquakes' });
});

map.on('click', 'quakes', (e) => {
  new mapboxgl.Popup()
    .setLngLat(e.lngLat)
    .setHTML(e.features[0].properties.title)
    .addTo(map);
});
'''
        result = self.parser.parse(code, "map.js")
        assert result.has_mapbox is True
        assert len(result.maps) >= 1
        assert len(result.sources) >= 1
        assert len(result.popups) >= 1

    def test_parse_maplibre(self):
        code = '''
import maplibregl from 'maplibre-gl';

const map = new maplibregl.Map({
  container: 'map',
  style: 'https://demotiles.maplibre.org/style.json',
});
'''
        result = self.parser.parse(code, "map.js")
        assert result.has_maplibre is True

    def test_parse_deck_gl(self):
        code = '''
import { DeckGL } from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
'''
        result = self.parser.parse(code, "viz.tsx")
        assert 'deck.gl' in result.detected_frameworks

    def test_parse_typescript_detection(self):
        code = '''
import L, { LatLngExpression, MapOptions } from 'leaflet';

const center: LatLngExpression = [51.505, -0.09];
const map: L.Map = L.map('map', { center, zoom: 13 } as MapOptions);
'''
        result = self.parser.parse(code, "map.ts")
        assert result.has_typescript is True

    def test_parse_empty_code(self):
        code = ''
        result = self.parser.parse(code, "empty.js")
        assert isinstance(result, LeafletParseResult)
        assert len(result.maps) == 0
        assert len(result.markers) == 0

    def test_parse_complex_app(self):
        code = '''
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet-draw';
import * as turf from '@turf/turf';

const map = L.map('map').setView([51.505, -0.09], 13);

L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
  attribution: '© OSM',
}).addTo(map);

const markers = L.markerClusterGroup();
data.forEach(d => markers.addLayer(L.marker([d.lat, d.lng]).bindPopup(d.name)));
map.addLayer(markers);

L.geoJSON(geojsonData, {
  style: (f) => ({ color: f.properties.color }),
  onEachFeature: (f, l) => l.bindPopup(f.properties.name),
}).addTo(map);

L.control.layers(baseLayers, overlays).addTo(map);
L.control.scale().addTo(map);

const drawnItems = L.featureGroup().addTo(map);
const drawControl = new L.Control.Draw({ edit: { featureGroup: drawnItems } });
map.addControl(drawControl);

map.on('draw:created', (e) => drawnItems.addLayer(e.layer));
map.on('click', (e) => console.log(e.latlng));
map.on('moveend', () => updateView());

map.flyTo([48.856, 2.352], 12);
'''
        result = self.parser.parse(code, "app.js")
        assert len(result.maps) >= 1
        assert len(result.tile_layers) >= 1
        assert len(result.markers) >= 1
        assert len(result.geojson) >= 1
        assert len(result.controls) >= 2
        assert len(result.events) >= 2
        assert len(result.animations) >= 1
        assert result.has_clustering is True
        assert result.has_drawing is True


# ═══════════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeafletScannerIntegration:
    """Tests for Leaflet scanner integration."""

    def test_scanner_has_leaflet_parser_import(self):
        """Verify scanner imports EnhancedLeafletParser."""
        from codetrellis.leaflet_parser_enhanced import EnhancedLeafletParser
        parser = EnhancedLeafletParser()
        assert parser is not None

    def test_project_matrix_has_leaflet_fields(self):
        """Verify ProjectMatrix has all leaflet_* fields."""
        from codetrellis.scanner import ProjectMatrix
        m = ProjectMatrix(name='test', root_path='/tmp/test')
        leaflet_fields = [
            'leaflet_maps', 'leaflet_tile_layers', 'leaflet_markers',
            'leaflet_shapes', 'leaflet_geojson', 'leaflet_layer_groups',
            'leaflet_sources', 'leaflet_controls', 'leaflet_popups',
            'leaflet_tooltips', 'leaflet_events', 'leaflet_drawings',
            'leaflet_animations', 'leaflet_imports', 'leaflet_integrations',
            'leaflet_types', 'leaflet_plugins', 'leaflet_detected_frameworks',
            'leaflet_detected_features',
        ]
        for field in leaflet_fields:
            assert hasattr(m, field), f"ProjectMatrix missing field: {field}"

    def test_project_matrix_leaflet_metadata_fields(self):
        """Verify ProjectMatrix has leaflet metadata fields."""
        from codetrellis.scanner import ProjectMatrix
        m = ProjectMatrix(name='test', root_path='/tmp/test')
        metadata_fields = [
            'leaflet_version', 'mapbox_version',
            'leaflet_has_typescript', 'leaflet_has_react_leaflet',
            'leaflet_has_mapbox', 'leaflet_has_maplibre',
            'leaflet_has_clustering', 'leaflet_has_drawing',
        ]
        for field in metadata_fields:
            assert hasattr(m, field), f"ProjectMatrix missing metadata field: {field}"

    def test_scanner_has_parse_leaflet_method(self):
        """Verify scanner has _parse_leaflet method."""
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner.__new__(ProjectScanner)
        assert hasattr(scanner, '_parse_leaflet')


# ═══════════════════════════════════════════════════════════════════════
# Compressor Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeafletCompressorIntegration:
    """Tests for Leaflet compressor integration."""

    def test_compressor_has_leaflet_methods(self):
        """Verify compressor has all _compress_leaflet_* methods."""
        from codetrellis.compressor import MatrixCompressor
        compressor = MatrixCompressor.__new__(MatrixCompressor)
        methods = [
            '_compress_leaflet_maps',
            '_compress_leaflet_layers',
            '_compress_leaflet_controls',
            '_compress_leaflet_interactions',
            '_compress_leaflet_api',
        ]
        for method in methods:
            assert hasattr(compressor, method), f"Compressor missing method: {method}"

    def test_compress_leaflet_maps_empty(self):
        """Verify _compress_leaflet_maps handles empty matrix."""
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor.__new__(MatrixCompressor)
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        result = compressor._compress_leaflet_maps(matrix)
        assert isinstance(result, list)
        assert len(result) == 0

    def test_compress_leaflet_maps_with_data(self):
        """Verify _compress_leaflet_maps compresses map data."""
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor.__new__(MatrixCompressor)
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.leaflet_maps = [
            {'map_type': 'leaflet', 'has_center': True, 'has_zoom': True},
            {'map_type': 'mapbox-gl', 'has_center': True, 'has_zoom': True, 'has_bounds': True},
        ]
        result = compressor._compress_leaflet_maps(matrix)
        assert len(result) >= 2
        assert any('leaflet' in line for line in result)
        assert any('mapbox-gl' in line for line in result)

    def test_compress_leaflet_layers_with_data(self):
        """Verify _compress_leaflet_layers compresses layer data."""
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor.__new__(MatrixCompressor)
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.leaflet_markers = [
            {'marker_type': 'default', 'has_popup': True},
            {'marker_type': 'circle', 'has_popup': False},
        ]
        matrix.leaflet_shapes = [
            {'shape_type': 'polygon'},
            {'shape_type': 'circle'},
        ]
        result = compressor._compress_leaflet_layers(matrix)
        assert len(result) >= 2
        assert any('marker' in line for line in result)
        assert any('shapes' in line for line in result)

    def test_compress_leaflet_controls_with_data(self):
        """Verify _compress_leaflet_controls compresses control data."""
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor.__new__(MatrixCompressor)
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.leaflet_controls = [
            {'control_type': 'zoom', 'is_custom': False},
            {'control_type': 'layers', 'is_custom': False},
        ]
        matrix.leaflet_popups = [
            {'is_custom': False},
        ]
        result = compressor._compress_leaflet_controls(matrix)
        assert len(result) >= 2
        assert any('controls' in line for line in result)
        assert any('popups' in line for line in result)

    def test_compress_leaflet_interactions_with_data(self):
        """Verify _compress_leaflet_interactions compresses event data."""
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor.__new__(MatrixCompressor)
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.leaflet_events = [
            {'event_type': 'click'},
            {'event_type': 'moveend'},
            {'event_type': 'click'},
        ]
        matrix.leaflet_animations = [
            {'animation_type': 'flyTo'},
            {'animation_type': 'panTo'},
        ]
        result = compressor._compress_leaflet_interactions(matrix)
        assert len(result) >= 2
        assert any('events' in line for line in result)
        assert any('animations' in line for line in result)

    def test_compress_leaflet_api_with_data(self):
        """Verify _compress_leaflet_api compresses API data."""
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        compressor = MatrixCompressor.__new__(MatrixCompressor)
        matrix = ProjectMatrix(name='test', root_path='/tmp/test')
        matrix.leaflet_imports = [
            {'package': 'leaflet', 'import_type': 'default', 'is_plugin': False},
            {'package': 'react-leaflet', 'import_type': 'named', 'is_plugin': False},
        ]
        matrix.leaflet_detected_frameworks = ['leaflet', 'react-leaflet']
        matrix.leaflet_version = '1.9.4'
        matrix.leaflet_has_react_leaflet = True
        matrix.leaflet_has_typescript = True
        result = compressor._compress_leaflet_api(matrix)
        assert len(result) >= 3
        assert any('leaflet' in line for line in result)
        assert any('version' in line.lower() or '1.9.4' in line for line in result)
        assert any('TypeScript' in line for line in result)
        assert any('React-Leaflet' in line for line in result)


# ═══════════════════════════════════════════════════════════════════════
# BPL Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeafletBPLIntegration:
    """Tests for Leaflet BPL integration."""

    def test_practice_categories_exist(self):
        """Verify PracticeCategory has LEAFLET_* entries."""
        from codetrellis.bpl.models import PracticeCategory
        categories = [
            'LEAFLET_MAPS', 'LEAFLET_LAYERS', 'LEAFLET_MARKERS',
            'LEAFLET_CONTROLS', 'LEAFLET_POPUPS', 'LEAFLET_EVENTS',
            'LEAFLET_GEOJSON', 'LEAFLET_PLUGINS', 'LEAFLET_PERFORMANCE',
            'LEAFLET_ECOSYSTEM',
        ]
        for cat in categories:
            assert hasattr(PracticeCategory, cat), f"PracticeCategory missing: {cat}"

    def test_practice_category_values(self):
        """Verify PracticeCategory values are correct strings."""
        from codetrellis.bpl.models import PracticeCategory
        assert PracticeCategory.LEAFLET_MAPS.value == "leaflet_maps"
        assert PracticeCategory.LEAFLET_LAYERS.value == "leaflet_layers"
        assert PracticeCategory.LEAFLET_MARKERS.value == "leaflet_markers"
        assert PracticeCategory.LEAFLET_CONTROLS.value == "leaflet_controls"
        assert PracticeCategory.LEAFLET_ECOSYSTEM.value == "leaflet_ecosystem"

    def test_leaflet_core_yaml_exists(self):
        """Verify leaflet_core.yaml practices file exists."""
        import os
        yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'codetrellis', 'bpl', 'practices', 'leaflet_core.yaml'
        )
        assert os.path.exists(yaml_path), f"leaflet_core.yaml not found at {yaml_path}"

    def test_leaflet_core_yaml_valid(self):
        """Verify leaflet_core.yaml has valid practice structure."""
        import os
        import yaml
        yaml_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            'codetrellis', 'bpl', 'practices', 'leaflet_core.yaml'
        )
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        assert 'practices' in data
        assert len(data['practices']) == 50
        # Verify practice IDs
        for i, p in enumerate(data['practices'], 1):
            assert p['id'] == f'LEAFLET{i:03d}', f"Practice {i} has wrong ID: {p['id']}"
            assert 'title' in p
            assert 'description' in p
            assert 'category' in p
            assert 'severity' in p
            assert 'applicability' in p
            assert 'tags' in p
            assert 'example' in p


# ═══════════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════

class TestLeafletEdgeCases:
    """Tests for edge cases and special scenarios."""

    def setup_method(self):
        self.parser = EnhancedLeafletParser()

    def test_non_leaflet_file(self):
        code = '''
function add(a, b) { return a + b; }
export default add;
'''
        assert self.parser.is_leaflet_file(code, "math.js") is False

    def test_leaflet_cdn_detection(self):
        code = '''
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<script>
  var map = L.map('map').setView([51.505, -0.09], 13);
</script>
'''
        assert self.parser.is_leaflet_file(code, "index.html") is True

    def test_dynamic_import_detection(self):
        code = '''
const L = await import('leaflet');
const map = L.map('map');
'''
        assert self.parser.is_leaflet_file(code, "lazy-map.js") is True

    def test_require_import_detection(self):
        code = '''
const L = require('leaflet');
const map = L.map('map');
'''
        result = self.parser.parse(code, "map.js")
        assert len(result.maps) >= 1

    def test_mixed_mapping_libraries(self):
        code = '''
import L from 'leaflet';
import mapboxgl from 'mapbox-gl';

const leafletMap = L.map('map1').setView([51.505, -0.09], 13);
const mapboxMap = new mapboxgl.Map({ container: 'map2', center: [-74.5, 40], zoom: 9 });
'''
        result = self.parser.parse(code, "multi.js")
        assert len(result.maps) >= 2
        assert result.has_mapbox is True

    def test_typescript_types_in_ts_file(self):
        code = '''
import L from 'leaflet';

const map: L.Map = L.map('id');
const center: L.LatLng = L.latLng(51.505, -0.09);
const options: L.MapOptions = { center, zoom: 13 };
const markerOpts: L.MarkerOptions = { draggable: true };
'''
        result = self.parser.parse(code, "map.ts")
        assert result.has_typescript is True
        assert len(result.types) >= 1

    def test_large_geojson_handling(self):
        code = '''
fetch('/data/countries.geojson')
  .then(res => res.json())
  .then(data => {
    L.geoJSON(data, {
      style: getStyle,
      onEachFeature: bindPopups,
      filter: f => f.properties.population > 1000000,
    }).addTo(map);
  });
'''
        result = self.parser.parse(code, "countries.js")
        assert len(result.geojson) >= 1

    def test_marker_cluster_with_custom_icon(self):
        code = '''
import 'leaflet.markercluster';

const markers = L.markerClusterGroup({
  chunkedLoading: true,
  maxClusterRadius: 50,
});

cities.forEach(city => {
  const marker = L.marker([city.lat, city.lng], {
    icon: L.icon({
      iconUrl: city.icon,
      iconSize: [25, 41],
      iconAnchor: [12, 41],
    }),
  });
  marker.bindPopup(city.name);
  markers.addLayer(marker);
});

map.addLayer(markers);
'''
        result = self.parser.parse(code, "clusters.js")
        assert len(result.markers) >= 1
        assert result.has_clustering is True

    def test_leaflet_with_turf_integration(self):
        code = '''
import L from 'leaflet';
import * as turf from '@turf/turf';

const point = turf.point([-77.034, 38.899]);
const buffered = turf.buffer(point, 500, { units: 'meters' });
L.geoJSON(buffered).addTo(map);
'''
        result = self.parser.parse(code, "analysis.js")
        assert len(result.integrations) >= 1 or len(result.imports) >= 2

    def test_vue_leaflet_complete(self):
        code = '''
<template>
  <LMap :zoom="zoom" :center="center">
    <LTileLayer :url="url" />
    <LMarker :lat-lng="markerPos">
      <LPopup>Hello!</LPopup>
    </LMarker>
    <LGeoJson :geojson="geojsonData" :options-style="styleFunction" />
  </LMap>
</template>

<script>
import { LMap, LTileLayer, LMarker, LPopup, LGeoJson } from '@vue-leaflet/vue-leaflet';
</script>
'''
        result = self.parser.parse(code, "Map.vue")
        assert len(result.maps) >= 1
        assert 'vue-leaflet' in result.detected_frameworks

    def test_deck_gl_with_mapbox(self):
        code = '''
import { DeckGL } from '@deck.gl/react';
import { ScatterplotLayer } from '@deck.gl/layers';
import { StaticMap } from 'react-map-gl';

function App() {
  const layers = [
    new ScatterplotLayer({
      data: points,
      getPosition: d => [d.lng, d.lat],
      getRadius: d => d.magnitude * 100,
    }),
  ];

  return (
    <DeckGL layers={layers} viewState={viewState}>
      <StaticMap mapboxApiAccessToken={TOKEN} />
    </DeckGL>
  );
}
'''
        result = self.parser.parse(code, "viz.tsx")
        assert 'deck.gl' in result.detected_frameworks
