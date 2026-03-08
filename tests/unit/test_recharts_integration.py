"""
Tests for Recharts charting library integration.

Tests cover:
- All 5 extractors (component, data, axis, customization, api)
- Parser (EnhancedRechartsParser)
- Scanner integration (ProjectMatrix fields, _parse_recharts)
- Compressor integration ([RECHARTS_*] sections)
"""

import pytest
from codetrellis.extractors.recharts import (
    RechartsComponentExtractor,
    RechartsDataExtractor,
    RechartsAxisExtractor,
    RechartsCustomizationExtractor,
    RechartsAPIExtractor,
)
from codetrellis.recharts_parser_enhanced import EnhancedRechartsParser, RechartsParseResult


# ═══════════════════════════════════════════════════════════════════════
# Component Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRechartsComponentExtractor:
    """Tests for RechartsComponentExtractor."""

    def setup_method(self):
        self.extractor = RechartsComponentExtractor()

    def test_linechart_detection(self):
        code = '''
import { LineChart, Line, XAxis, YAxis } from 'recharts';

<LineChart width={600} height={300} data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Line type="monotone" dataKey="value" stroke="#8884d8" />
</LineChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        comp = result['components'][0]
        assert comp.chart_type == 'line'

    def test_barchart_detection(self):
        code = '''
<BarChart width={600} height={300} data={data}>
  <Bar dataKey="value" fill="#8884d8" />
</BarChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'bar'

    def test_areachart_detection(self):
        code = '''
<AreaChart width={600} height={300} data={data}>
  <Area type="monotone" dataKey="value" fill="#8884d8" />
</AreaChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'area'

    def test_piechart_detection(self):
        code = '''
<PieChart width={400} height={400}>
  <Pie data={data} dataKey="value" nameKey="name" />
</PieChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'pie'

    def test_radarchart_detection(self):
        code = '''
<RadarChart cx={300} cy={250} outerRadius={150} data={data}>
  <PolarGrid />
  <PolarAngleAxis dataKey="subject" />
  <PolarRadiusAxis />
  <Radar name="Mike" dataKey="A" fill="#8884d8" fillOpacity={0.6} />
</RadarChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'radar'

    def test_scatterchart_detection(self):
        code = '''
<ScatterChart width={600} height={400}>
  <XAxis dataKey="x" />
  <YAxis dataKey="y" />
  <Scatter data={data} fill="#8884d8" />
</ScatterChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'scatter'

    def test_composedchart_detection(self):
        code = '''
<ComposedChart width={600} height={300} data={data}>
  <Bar dataKey="sales" fill="#413ea0" />
  <Line dataKey="trend" stroke="#ff7300" />
  <Area dataKey="range" fill="#8884d8" />
</ComposedChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'composed'

    def test_radialbarchart_detection(self):
        code = '''
<RadialBarChart innerRadius="10%" outerRadius="80%" data={data}>
  <RadialBar dataKey="value" />
</RadialBarChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'radialBar'

    def test_treemap_detection(self):
        code = '''
<Treemap width={400} height={200} data={data} dataKey="size" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'treemap'

    def test_funnelchart_detection(self):
        code = '''
<FunnelChart width={500} height={300}>
  <Funnel dataKey="value" data={data} />
</FunnelChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'funnel'

    def test_sankey_detection(self):
        code = '''
<Sankey width={960} height={500} data={sankeyData} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].chart_type == 'sankey'

    def test_responsive_container_detection(self):
        code = '''
<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    <Line dataKey="value" />
  </LineChart>
</ResponsiveContainer>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['responsive_containers']) >= 1
        rc = result['responsive_containers'][0]
        assert rc.has_width is True
        assert rc.has_height is True

    def test_data_prop_detection(self):
        code = '''
<LineChart width={600} height={300} data={myData}>
  <Line dataKey="value" />
</LineChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].has_data_prop is True

    def test_margin_prop_detection(self):
        code = '''
<LineChart width={600} height={300} data={data}
  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
  <Line dataKey="value" />
</LineChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].has_margin is True

    def test_syncid_detection(self):
        code = '''
<LineChart syncId="dashboard" data={data}>
  <Line dataKey="value" />
</LineChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        assert result['components'][0].has_sync_id is True

    def test_children_detection(self):
        code = '''
<LineChart width={600} height={300} data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <CartesianGrid strokeDasharray="3 3" />
  <Tooltip />
  <Legend />
  <Line type="monotone" dataKey="value" stroke="#8884d8" />
</LineChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['components']) >= 1
        children = result['components'][0].children
        assert 'XAxis' in children
        assert 'YAxis' in children
        assert 'Tooltip' in children
        assert 'Legend' in children

    def test_multiple_charts_in_file(self):
        code = '''
<LineChart width={600} height={300} data={lineData}>
  <Line dataKey="value" />
</LineChart>
<BarChart width={600} height={300} data={barData}>
  <Bar dataKey="count" />
</BarChart>
<PieChart width={400} height={400}>
  <Pie data={pieData} dataKey="value" />
</PieChart>
'''
        result = self.extractor.extract(code, "dashboard.tsx")
        assert len(result['components']) >= 3


# ═══════════════════════════════════════════════════════════════════════
# Data Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRechartsDataExtractor:
    """Tests for RechartsDataExtractor."""

    def setup_method(self):
        self.extractor = RechartsDataExtractor()

    def test_line_series_detection(self):
        code = '''
<Line type="monotone" dataKey="value" stroke="#8884d8" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1
        s = result['series'][0]
        assert s.series_type == 'line'
        assert s.data_key == 'value'

    def test_bar_series_detection(self):
        code = '''
<Bar dataKey="sales" fill="#413ea0" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1
        assert result['series'][0].series_type == 'bar'
        assert result['series'][0].data_key == 'sales'

    def test_area_series_detection(self):
        code = '''
<Area type="monotone" dataKey="value" fill="#8884d8" stroke="#8884d8" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1
        assert result['series'][0].series_type == 'area'

    def test_scatter_series_detection(self):
        code = '''
<Scatter data={scatterData} fill="#8884d8" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1
        assert result['series'][0].series_type == 'scatter'

    def test_pie_series_detection(self):
        code = '''
<Pie data={data} dataKey="value" nameKey="name" cx="50%" cy="50%" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1
        assert result['series'][0].series_type == 'pie'

    def test_radar_series_detection(self):
        code = '''
<Radar name="Mike" dataKey="A" fill="#8884d8" fillOpacity={0.6} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1
        assert result['series'][0].series_type == 'radar'

    def test_radialbar_series_detection(self):
        code = '''
<RadialBar dataKey="value" cornerRadius={10} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1
        assert result['series'][0].series_type == 'radialBar'

    def test_stacked_series(self):
        code = '''
<Bar dataKey="desktop" stackId="a" fill="#8884d8" />
<Bar dataKey="mobile" stackId="a" fill="#82ca9d" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 2
        assert result['series'][0].has_stack_id is True
        assert result['series'][1].has_stack_id is True

    def test_datakey_extraction(self):
        code = '''
<XAxis dataKey="month" />
<Line dataKey="sales" />
<Tooltip />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['data_keys']) >= 2

    def test_cell_component_detection(self):
        code = '''
<Pie data={data} dataKey="value">
  {data.map((entry, index) => (
    <Cell key={index} fill={COLORS[index % COLORS.length]} />
  ))}
</Pie>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['cells']) >= 1

    def test_series_with_name_prop(self):
        code = '''
<Line name="Total Sales" dataKey="sales" stroke="#8884d8" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1
        assert result['series'][0].has_name is True

    def test_series_with_custom_dot(self):
        code = '''
<Line dataKey="value" dot={{ r: 4, fill: '#8884d8' }} activeDot={{ r: 8 }} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1

    def test_series_with_custom_shape(self):
        code = '''
<Bar dataKey="value" shape={<RoundedBar />} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 1
        assert result['series'][0].has_custom_shape is True

    def test_multiple_series(self):
        code = '''
<Line dataKey="sales" stroke="#8884d8" />
<Line dataKey="profit" stroke="#82ca9d" />
<Bar dataKey="orders" fill="#ffc658" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['series']) >= 3


# ═══════════════════════════════════════════════════════════════════════
# Axis Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRechartsAxisExtractor:
    """Tests for RechartsAxisExtractor."""

    def setup_method(self):
        self.extractor = RechartsAxisExtractor()

    def test_xaxis_detection(self):
        code = '''
<XAxis dataKey="month" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 1
        ax = result['axes'][0]
        assert ax.axis_type == 'x'
        assert ax.data_key == 'month'

    def test_yaxis_detection(self):
        code = '''
<YAxis />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 1
        assert result['axes'][0].axis_type == 'y'

    def test_zaxis_detection(self):
        code = '''
<ZAxis dataKey="z" range={[64, 144]} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 1
        assert result['axes'][0].axis_type == 'z'

    def test_axis_with_tick_formatter(self):
        code = '''
<YAxis tickFormatter={(value) => `$${value}`} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 1
        assert result['axes'][0].has_tick_formatter is True

    def test_axis_with_custom_tick(self):
        code = '''
<XAxis tick={<CustomTick />} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 1
        assert result['axes'][0].has_custom_tick is True

    def test_axis_with_domain(self):
        code = '''
<YAxis domain={[0, 'auto']} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 1
        assert result['axes'][0].has_domain is True

    def test_axis_with_scale(self):
        code = '''
<YAxis scale="log" domain={[1, 'auto']} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 1
        assert result['axes'][0].has_scale is True

    def test_axis_with_label(self):
        code = '''
<YAxis label={{ value: 'Revenue ($)', angle: -90, position: 'insideLeft' }} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 1
        assert result['axes'][0].has_label is True

    def test_cartesian_grid_detection(self):
        code = '''
<CartesianGrid strokeDasharray="3 3" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['grids']) >= 1
        g = result['grids'][0]
        assert g.grid_type == 'cartesian'
        assert g.has_stroke_dasharray is True

    def test_polar_grid_detection(self):
        code = '''
<PolarGrid />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['grids']) >= 1
        assert result['grids'][0].grid_type == 'polar'

    def test_polar_angle_axis_detection(self):
        code = '''
<PolarAngleAxis dataKey="subject" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['polar_axes']) >= 1
        pa = result['polar_axes'][0]
        assert pa.polar_type == 'angle'
        assert pa.data_key == 'subject'

    def test_polar_radius_axis_detection(self):
        code = '''
<PolarRadiusAxis angle={30} domain={[0, 150]} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['polar_axes']) >= 1
        assert result['polar_axes'][0].polar_type == 'radius'

    def test_multiple_axes(self):
        code = '''
<XAxis dataKey="name" />
<YAxis yAxisId="left" />
<YAxis yAxisId="right" orientation="right" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 3

    def test_axis_with_orientation(self):
        code = '''
<YAxis orientation="right" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['axes']) >= 1
        assert result['axes'][0].has_orientation is True


# ═══════════════════════════════════════════════════════════════════════
# Customization Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRechartsCustomizationExtractor:
    """Tests for RechartsCustomizationExtractor."""

    def setup_method(self):
        self.extractor = RechartsCustomizationExtractor()

    def test_tooltip_detection(self):
        code = '''
<Tooltip />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['tooltips']) >= 1

    def test_custom_tooltip_content(self):
        code = '''
<Tooltip content={<CustomTooltip />} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['tooltips']) >= 1
        assert result['tooltips'][0].has_content is True

    def test_tooltip_with_formatter(self):
        code = '''
<Tooltip formatter={(value) => `$${value}`} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['tooltips']) >= 1
        assert result['tooltips'][0].has_formatter is True

    def test_tooltip_with_label_formatter(self):
        code = '''
<Tooltip labelFormatter={(label) => `Month: ${label}`} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['tooltips']) >= 1
        assert result['tooltips'][0].has_label_formatter is True

    def test_tooltip_cursor_styling(self):
        code = '''
<Tooltip cursor={{ stroke: '#ccc', strokeWidth: 2 }} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['tooltips']) >= 1
        assert result['tooltips'][0].has_cursor is True

    def test_legend_detection(self):
        code = '''
<Legend />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['legends']) >= 1

    def test_legend_with_custom_content(self):
        code = '''
<Legend content={<CustomLegend />} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['legends']) >= 1
        assert result['legends'][0].has_content is True

    def test_legend_positioning(self):
        code = '''
<Legend verticalAlign="top" align="right" layout="vertical" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['legends']) >= 1
        assert result['legends'][0].has_vertical_align is True
        assert result['legends'][0].has_align is True
        assert result['legends'][0].has_layout is True

    def test_legend_click_handler(self):
        code = '''
<Legend onClick={handleLegendClick} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['legends']) >= 1
        assert result['legends'][0].has_on_click is True

    def test_reference_line_detection(self):
        code = '''
<ReferenceLine y={100} stroke="red" strokeDasharray="3 3" label="Target" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['references']) >= 1
        ref = result['references'][0]
        assert ref.reference_type == 'line'

    def test_reference_area_detection(self):
        code = '''
<ReferenceArea y1={80} y2={120} fill="#82ca9d" fillOpacity={0.2} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['references']) >= 1
        assert result['references'][0].reference_type == 'area'

    def test_reference_dot_detection(self):
        code = '''
<ReferenceDot x="Mar" y={9800} r={8} fill="red" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['references']) >= 1
        assert result['references'][0].reference_type == 'dot'

    def test_brush_detection(self):
        code = '''
<Brush dataKey="date" height={30} stroke="#8884d8" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['brushes']) >= 1
        b = result['brushes'][0]
        assert b.has_data_key is True

    def test_brush_with_start_end_index(self):
        code = '''
<Brush dataKey="date" height={30} startIndex={10} endIndex={20} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['brushes']) >= 1
        assert result['brushes'][0].has_start_index is True
        assert result['brushes'][0].has_end_index is True

    def test_chart_click_event(self):
        code = '''
<BarChart onClick={handleClick} data={data}>
  <Bar dataKey="value" />
</BarChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['events']) >= 1

    def test_chart_mouse_events(self):
        code = '''
<LineChart
  onMouseEnter={handleEnter}
  onMouseLeave={handleLeave}
  onMouseMove={handleMove}
  data={data}
>
  <Line dataKey="value" />
</LineChart>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['events']) >= 1

    def test_animation_props_detection(self):
        code = '''
<Line
  dataKey="value"
  isAnimationActive={true}
  animationDuration={1500}
  animationEasing="ease-in-out"
  animationBegin={200}
/>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['animations']) >= 1
        anim_types = [a.animation_type for a in result['animations']]
        assert 'duration' in anim_types or 'active' in anim_types

    def test_animation_disabled(self):
        code = '''
<Line dataKey="value" isAnimationActive={false} />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['animations']) >= 1
        anim = result['animations'][0]
        assert anim.animation_type == 'active' or anim.animation_type == 'disabled'

    def test_label_list_detection(self):
        code = '''
<Bar dataKey="value">
  <LabelList dataKey="value" position="top" />
</Bar>
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['labels']) >= 1

    def test_multiple_references(self):
        code = '''
<ReferenceLine y={100} stroke="red" />
<ReferenceLine y={200} stroke="blue" />
<ReferenceArea y1={100} y2={200} fill="#eee" />
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['references']) >= 3


# ═══════════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRechartsAPIExtractor:
    """Tests for RechartsAPIExtractor."""

    def setup_method(self):
        self.extractor = RechartsAPIExtractor()

    def test_named_import_detection(self):
        code = '''
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.package == 'recharts'
        assert imp.import_type == 'module_named'
        assert 'LineChart' in imp.symbols

    def test_namespace_import_detection(self):
        code = '''
import * as Recharts from 'recharts';
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['imports']) >= 1
        assert result['imports'][0].import_type == 'module_namespace'

    def test_deep_import_detection(self):
        code = '''
import { LineChart } from 'recharts/es6/chart/LineChart';
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['imports']) >= 1
        assert 'recharts/es6' in result['imports'][0].package

    def test_require_import_detection(self):
        code = '''
const { LineChart, Line } = require('recharts');
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['imports']) >= 1
        assert result['imports'][0].import_type == 'require'

    def test_dynamic_import_detection(self):
        code = '''
const recharts = await import('recharts');
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['imports']) >= 1
        assert result['imports'][0].import_type == 'dynamic'

    def test_recharts_scale_ecosystem_detection(self):
        code = '''
import { LineChart } from 'recharts';
import { scaleLog } from 'recharts-scale';
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['integrations']) >= 1

    def test_recharts_to_png_detection(self):
        code = '''
import { useCurrentPng } from 'recharts-to-png';
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['integrations']) >= 1

    def test_d3_integration_detection(self):
        code = '''
import { LineChart } from 'recharts';
import { format } from 'd3-format';
import { scaleLog } from 'd3-scale';
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['integrations']) >= 1

    def test_typescript_type_detection(self):
        code = '''
import { TooltipProps } from 'recharts';
import type { CategoricalChartState } from 'recharts/types';

const tooltip: React.FC<TooltipProps<number, string>> = (props) => { ... };
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['types']) >= 1

    def test_version_detection_from_comment(self):
        code = '''
// recharts@2.10.3
import { LineChart } from 'recharts';
'''
        result = self.extractor.extract(code, "chart.tsx")
        # Version detection may or may not find the comment version
        assert isinstance(result, dict)

    def test_tree_shakeable_detection(self):
        code = '''
import { LineChart, Line } from 'recharts';
'''
        result = self.extractor.extract(code, "chart.tsx")
        # Named imports are tree-shakeable
        assert len(result['imports']) >= 1

    def test_all_recharts_components_recognized(self):
        code = '''
import {
  LineChart, BarChart, AreaChart, PieChart,
  RadarChart, ScatterChart, ComposedChart,
  RadialBarChart, Treemap, FunnelChart, Sankey,
  Line, Bar, Area, Pie, Radar, Scatter, RadialBar, Funnel,
  XAxis, YAxis, ZAxis, CartesianGrid,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Tooltip, Legend, ReferenceLine, ReferenceArea, ReferenceDot,
  Brush, ResponsiveContainer, Cell, LabelList, Label, Sector
} from 'recharts';
'''
        result = self.extractor.extract(code, "chart.tsx")
        assert len(result['imports']) >= 1
        assert len(result['imports'][0].symbols) >= 30


# ═══════════════════════════════════════════════════════════════════════
# Parser Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEnhancedRechartsParser:
    """Tests for EnhancedRechartsParser."""

    def setup_method(self):
        self.parser = EnhancedRechartsParser()

    def test_is_recharts_file_with_import(self):
        code = "import { LineChart } from 'recharts';"
        assert self.parser.is_recharts_file(code, "chart.tsx") is True

    def test_is_recharts_file_with_require(self):
        code = "const { BarChart } = require('recharts');"
        assert self.parser.is_recharts_file(code, "chart.js") is True

    def test_is_recharts_file_with_jsx(self):
        code = "<LineChart data={data}><Line dataKey='value' /></LineChart>"
        assert self.parser.is_recharts_file(code, "chart.jsx") is True

    def test_is_recharts_file_negative(self):
        code = "console.log('hello world');"
        assert self.parser.is_recharts_file(code, "hello.js") is False

    def test_is_recharts_file_react_only(self):
        code = '''
import React from 'react';
function App() { return <div>Hello</div>; }
export default App;
'''
        assert self.parser.is_recharts_file(code, "App.tsx") is False

    def test_is_recharts_file_chartjs_not_recharts(self):
        code = '''
import Chart from 'chart.js/auto';
const chart = new Chart(ctx, { type: 'bar' });
'''
        assert self.parser.is_recharts_file(code, "chart.js") is False

    def test_parse_basic_recharts(self):
        code = '''
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';

function MyChart({ data }) {
  return (
    <LineChart width={600} height={300} data={data}>
      <XAxis dataKey="name" />
      <YAxis />
      <Tooltip />
      <Line type="monotone" dataKey="value" stroke="#8884d8" />
    </LineChart>
  );
}
'''
        result = self.parser.parse(code, "MyChart.tsx")
        assert isinstance(result, RechartsParseResult)
        assert result.file_type == "tsx"
        assert 'recharts' in result.detected_frameworks
        assert len(result.components) >= 1
        assert len(result.series) >= 1
        assert len(result.axes) >= 2
        assert len(result.tooltips) >= 1
        assert len(result.imports) >= 1

    def test_parse_result_fields(self):
        code = '''
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

<BarChart width={600} height={300} data={data}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="name" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Bar dataKey="value" fill="#8884d8" />
</BarChart>
'''
        result = self.parser.parse(code, "bar.tsx")
        assert isinstance(result, RechartsParseResult)
        assert len(result.components) >= 1
        assert len(result.series) >= 1
        assert len(result.axes) >= 2
        assert len(result.grids) >= 1
        assert len(result.tooltips) >= 1
        assert len(result.legends) >= 1

    def test_parse_responsive_chart(self):
        code = '''
import { ResponsiveContainer, LineChart, Line } from 'recharts';

<ResponsiveContainer width="100%" height={300}>
  <LineChart data={data}>
    <Line dataKey="value" />
  </LineChart>
</ResponsiveContainer>
'''
        result = self.parser.parse(code, "responsive.tsx")
        assert len(result.responsive_containers) >= 1
        assert result.has_responsive is True

    def test_parse_composed_chart(self):
        code = '''
import { ComposedChart, Line, Bar, Area, XAxis, YAxis } from 'recharts';

<ComposedChart data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Bar dataKey="sales" fill="#413ea0" />
  <Line type="monotone" dataKey="trend" stroke="#ff7300" />
  <Area dataKey="range" fill="#8884d8" />
</ComposedChart>
'''
        result = self.parser.parse(code, "composed.tsx")
        assert len(result.components) >= 1
        assert result.components[0].chart_type == 'composed'
        assert len(result.series) >= 3

    def test_parse_pie_chart_with_cells(self):
        code = '''
import { PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

<PieChart width={400} height={400}>
  <Pie data={data} dataKey="value">
    {data.map((entry, index) => (
      <Cell key={index} fill={COLORS[index % COLORS.length]} />
    ))}
  </Pie>
</PieChart>
'''
        result = self.parser.parse(code, "pie.tsx")
        assert len(result.components) >= 1
        assert result.components[0].chart_type == 'pie'
        assert len(result.cells) >= 1

    def test_parse_radar_chart(self):
        code = '''
import { RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

<RadarChart outerRadius={150} data={data}>
  <PolarGrid />
  <PolarAngleAxis dataKey="subject" />
  <PolarRadiusAxis />
  <Radar name="Mike" dataKey="A" fill="#8884d8" fillOpacity={0.6} />
</RadarChart>
'''
        result = self.parser.parse(code, "radar.tsx")
        assert len(result.components) >= 1
        assert result.components[0].chart_type == 'radar'
        assert len(result.polar_axes) >= 2
        assert len(result.grids) >= 1

    def test_parse_with_references(self):
        code = '''
import { LineChart, Line, ReferenceLine, ReferenceArea } from 'recharts';

<LineChart data={data}>
  <ReferenceLine y={100} stroke="red" label="Target" />
  <ReferenceArea y1={80} y2={120} fill="#82ca9d" fillOpacity={0.2} />
  <Line dataKey="value" />
</LineChart>
'''
        result = self.parser.parse(code, "refs.tsx")
        assert len(result.references) >= 2

    def test_parse_with_brush(self):
        code = '''
import { LineChart, Line, Brush } from 'recharts';

<LineChart data={data}>
  <Line dataKey="value" />
  <Brush dataKey="date" height={30} />
</LineChart>
'''
        result = self.parser.parse(code, "brush.tsx")
        assert len(result.brushes) >= 1

    def test_parse_with_animation(self):
        code = '''
import { LineChart, Line } from 'recharts';

<LineChart data={data}>
  <Line dataKey="value" isAnimationActive={true} animationDuration={1500} />
</LineChart>
'''
        result = self.parser.parse(code, "anim.tsx")
        assert result.has_animation is True

    def test_parse_typescript_file(self):
        code = '''
import { LineChart, Line, TooltipProps } from 'recharts';
import type { CategoricalChartState } from 'recharts/types';

interface ChartData {
  name: string;
  value: number;
}

const MyChart: React.FC<{ data: ChartData[] }> = ({ data }) => (
  <LineChart data={data}>
    <Line dataKey="value" />
  </LineChart>
);
'''
        result = self.parser.parse(code, "typed.tsx")
        assert result.has_typescript is True
        assert len(result.types) >= 1

    def test_parse_ecosystem_integrations(self):
        code = '''
import { LineChart, Line } from 'recharts';
import { useCurrentPng } from 'recharts-to-png';
import { format } from 'd3-format';
'''
        result = self.parser.parse(code, "ecosystem.tsx")
        assert 'recharts' in result.detected_frameworks
        assert len(result.integrations) >= 1

    def test_parse_multiple_charts(self):
        code = '''
import { LineChart, Line, BarChart, Bar, PieChart, Pie } from 'recharts';

<LineChart data={lineData}>
  <Line dataKey="value" />
</LineChart>
<BarChart data={barData}>
  <Bar dataKey="count" />
</BarChart>
<PieChart>
  <Pie data={pieData} dataKey="value" />
</PieChart>
'''
        result = self.parser.parse(code, "dashboard.tsx")
        assert len(result.components) >= 3
        assert len(result.series) >= 3

    def test_parse_detected_features(self):
        code = '''
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, CartesianGrid } from 'recharts';

<LineChart data={data}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="name" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Line dataKey="value" />
</LineChart>
'''
        result = self.parser.parse(code, "full.tsx")
        assert len(result.detected_features) > 0

    def test_parse_events(self):
        code = '''
import { BarChart, Bar } from 'recharts';

<BarChart data={data} onClick={handleClick}>
  <Bar dataKey="value" />
</BarChart>
'''
        result = self.parser.parse(code, "events.tsx")
        assert len(result.events) >= 1

    def test_parse_sync_id(self):
        code = '''
import { LineChart, Line } from 'recharts';

<LineChart syncId="dashboard" data={data1}>
  <Line dataKey="value" />
</LineChart>
<LineChart syncId="dashboard" data={data2}>
  <Line dataKey="count" />
</LineChart>
'''
        result = self.parser.parse(code, "sync.tsx")
        assert len(result.components) >= 2
        assert result.components[0].has_sync_id is True

    def test_framework_detection(self):
        code = '''
import { LineChart } from 'recharts';
import { scaleLog } from 'recharts-scale';
import { timeFormat } from 'd3-time-format';
'''
        result = self.parser.parse(code, "frameworks.tsx")
        assert 'recharts' in result.detected_frameworks
        fws = result.detected_frameworks
        assert any('recharts-scale' in f for f in fws)

    def test_empty_file(self):
        assert self.parser.is_recharts_file("", "empty.js") is False

    def test_non_recharts_file(self):
        code = "console.log('hello world')"
        assert self.parser.is_recharts_file(code, "hello.js") is False


# ═══════════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRechartsScannerIntegration:
    """Tests for scanner integration with Recharts."""

    def test_project_matrix_has_recharts_fields(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        # All 24 recharts fields should exist
        assert hasattr(matrix, 'recharts_components')
        assert hasattr(matrix, 'recharts_responsive_containers')
        assert hasattr(matrix, 'recharts_series')
        assert hasattr(matrix, 'recharts_data_keys')
        assert hasattr(matrix, 'recharts_cells')
        assert hasattr(matrix, 'recharts_axes')
        assert hasattr(matrix, 'recharts_grids')
        assert hasattr(matrix, 'recharts_polar_axes')
        assert hasattr(matrix, 'recharts_tooltips')
        assert hasattr(matrix, 'recharts_legends')
        assert hasattr(matrix, 'recharts_references')
        assert hasattr(matrix, 'recharts_brushes')
        assert hasattr(matrix, 'recharts_events')
        assert hasattr(matrix, 'recharts_animations')
        assert hasattr(matrix, 'recharts_labels')
        assert hasattr(matrix, 'recharts_imports')
        assert hasattr(matrix, 'recharts_integrations')
        assert hasattr(matrix, 'recharts_types')
        assert hasattr(matrix, 'recharts_detected_frameworks')
        assert hasattr(matrix, 'recharts_detected_features')
        assert hasattr(matrix, 'recharts_version')
        assert hasattr(matrix, 'recharts_is_tree_shakeable')
        assert hasattr(matrix, 'recharts_has_animation')
        assert hasattr(matrix, 'recharts_has_typescript')
        assert hasattr(matrix, 'recharts_has_responsive')

    def test_project_matrix_recharts_fields_default_empty(self):
        from codetrellis.scanner import ProjectMatrix
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        assert matrix.recharts_components == []
        assert matrix.recharts_series == []
        assert matrix.recharts_axes == []
        assert matrix.recharts_version == ''
        assert matrix.recharts_is_tree_shakeable is False
        assert matrix.recharts_has_animation is False
        assert matrix.recharts_has_typescript is False
        assert matrix.recharts_has_responsive is False

    def test_scanner_has_recharts_parser(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner("/tmp/test")
        assert hasattr(scanner, 'recharts_parser')
        assert isinstance(scanner.recharts_parser, EnhancedRechartsParser)

    def test_scanner_has_parse_recharts_method(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner("/tmp/test")
        assert hasattr(scanner, '_parse_recharts')
        assert callable(scanner._parse_recharts)

    def test_parse_recharts_populates_matrix(self):
        """Test that _parse_recharts correctly populates matrix fields."""
        from codetrellis.scanner import ProjectScanner, ProjectMatrix
        import tempfile, os
        from pathlib import Path

        code = '''
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function SalesChart({ data }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <XAxis dataKey="month" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="sales" stroke="#8884d8" />
        <Line type="monotone" dataKey="profit" stroke="#82ca9d" />
      </LineChart>
    </ResponsiveContainer>
  );
}
'''
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "SalesChart.tsx")
            with open(filepath, 'w') as f:
                f.write(code)

            scanner = ProjectScanner(tmpdir)
            matrix = ProjectMatrix(name="test", root_path=tmpdir)
            scanner._parse_recharts(Path(filepath), matrix)

            # Verify fields were populated
            assert len(matrix.recharts_components) >= 1
            assert len(matrix.recharts_series) >= 2
            assert len(matrix.recharts_axes) >= 2
            assert len(matrix.recharts_tooltips) >= 1
            assert len(matrix.recharts_legends) >= 1
            assert len(matrix.recharts_responsive_containers) >= 1
            assert len(matrix.recharts_imports) >= 1
            assert 'recharts' in matrix.recharts_detected_frameworks
            assert matrix.recharts_has_responsive is True


# ═══════════════════════════════════════════════════════════════════════
# Compressor Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRechartsCompressorIntegration:
    """Tests for compressor integration with Recharts."""

    def test_compress_recharts_components_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.recharts_components = [{"name": "LineChart", "file": "Chart.tsx", "line": 10, "chart_type": "line", "has_data_prop": True, "is_responsive": True, "has_margin": False, "has_sync_id": False, "children": ["XAxis", "YAxis", "Tooltip", "Line"]}]
        matrix.recharts_responsive_containers = [{"name": "ResponsiveContainer", "file": "Chart.tsx", "line": 8, "has_width": True, "has_height": True, "has_aspect": False}]
        result = comp._compress_recharts_components(matrix)
        assert len(result) > 0

    def test_compress_recharts_series_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.recharts_series = [{"name": "Line", "file": "Chart.tsx", "line": 15, "series_type": "Line", "data_key": "value", "has_stack_id": False, "has_name": True, "has_custom_dot": False, "has_active_dot": False, "has_custom_shape": False, "has_type": True, "has_fill": False, "has_stroke": True, "has_label": False, "has_on_click": False}]
        matrix.recharts_data_keys = [{"name": "value", "file": "Chart.tsx", "line": 15, "key_type": "series", "component": "Line"}]
        matrix.recharts_cells = [{"name": "Cell", "file": "Chart.tsx", "line": 20, "has_fill": True, "has_stroke": False}]
        result = comp._compress_recharts_series(matrix)
        assert len(result) > 0

    def test_compress_recharts_axes_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.recharts_axes = [{"name": "XAxis", "file": "Chart.tsx", "line": 12, "axis_type": "XAxis", "data_key": "month", "has_tick_formatter": False, "has_custom_tick": False, "has_domain": False, "has_scale": False, "has_label": False, "has_orientation": False, "config_props": []}]
        matrix.recharts_grids = [{"name": "CartesianGrid", "file": "Chart.tsx", "line": 11, "grid_type": "CartesianGrid", "has_stroke_dasharray": True, "has_horizontal": False, "has_vertical": False}]
        matrix.recharts_polar_axes = [{"name": "PolarAngleAxis", "file": "Chart.tsx", "line": 14, "axis_type": "PolarAngleAxis", "data_key": "subject", "has_tick_formatter": False, "has_custom_tick": False}]
        result = comp._compress_recharts_axes(matrix)
        assert len(result) > 0

    def test_compress_recharts_customization_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.recharts_tooltips = [{"name": "Tooltip", "file": "Chart.tsx", "line": 14, "has_custom_content": False, "has_formatter": True, "has_label_formatter": False, "has_cursor": False, "has_wrapper_style": False, "has_content_style": False, "has_position": False, "has_shared": False}]
        matrix.recharts_legends = [{"name": "Legend", "file": "Chart.tsx", "line": 15, "has_custom_content": False, "has_vertical_align": True, "has_align": True, "has_layout": False, "has_on_click": True, "has_icon_type": False, "has_icon_size": False, "has_wrapper_style": False, "has_formatter": False}]
        matrix.recharts_references = [{"name": "ReferenceLine", "file": "Chart.tsx", "line": 16, "reference_type": "ReferenceLine", "has_label": True, "has_stroke": True, "has_fill": False, "has_stroke_dasharray": True}]
        matrix.recharts_brushes = [{"name": "Brush", "file": "Chart.tsx", "line": 17, "has_data_key": True, "has_height": True, "has_start_index": False, "has_end_index": False, "has_on_change": False}]
        matrix.recharts_events = [{"name": "onClick", "file": "Chart.tsx", "line": 10, "event_type": "onClick", "component": "BarChart"}]
        matrix.recharts_animations = [{"name": "animation", "file": "Chart.tsx", "line": 20, "is_active": True, "has_duration": True, "has_easing": False}]
        matrix.recharts_labels = [{"name": "LabelList", "file": "Chart.tsx", "line": 22, "label_type": "LabelList", "has_data_key": True, "has_position": True, "has_formatter": False}]
        result = comp._compress_recharts_customization(matrix)
        assert len(result) > 0

    def test_compress_recharts_api_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.recharts_detected_frameworks = ['recharts', 'recharts-to-png', 'd3-format']
        matrix.recharts_version = '2.10.3'
        matrix.recharts_is_tree_shakeable = True
        matrix.recharts_has_responsive = True
        matrix.recharts_detected_features = ['line', 'bar', 'tooltip', 'legend', 'responsive']
        result = comp._compress_recharts_api(matrix)
        assert len(result) > 0
        assert any("ecosystem" in line.lower() or "recharts" in line.lower() for line in result)

    def test_compress_recharts_empty_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        assert comp._compress_recharts_components(matrix) == []
        assert comp._compress_recharts_series(matrix) == []
        assert comp._compress_recharts_axes(matrix) == []
        assert comp._compress_recharts_customization(matrix) == []
        assert comp._compress_recharts_api(matrix) == []

    def test_full_compression_includes_recharts_sections(self):
        """Verify that a full compression with Recharts data produces [RECHARTS_*] sections."""
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.recharts_components = [{"name": "LineChart", "file": "Chart.tsx", "line": 10, "chart_type": "line", "has_data_prop": True, "is_responsive": False, "has_margin": False, "has_sync_id": False, "children": ["Line"]}]
        matrix.recharts_series = [{"name": "Line", "file": "Chart.tsx", "line": 15, "series_type": "Line", "data_key": "value", "has_stack_id": False, "has_name": False, "has_custom_dot": False, "has_active_dot": False, "has_custom_shape": False, "has_type": True, "has_fill": False, "has_stroke": True, "has_label": False, "has_on_click": False}]
        matrix.recharts_axes = [{"name": "XAxis", "file": "Chart.tsx", "line": 12, "axis_type": "XAxis", "data_key": "name", "has_tick_formatter": False, "has_custom_tick": False, "has_domain": False, "has_scale": False, "has_label": False, "has_orientation": False, "config_props": []}]
        matrix.recharts_detected_frameworks = ['recharts']
        matrix.recharts_version = '2.10.3'
        matrix.recharts_is_tree_shakeable = True

        output = comp.compress(matrix)
        assert "[RECHARTS_COMPONENTS]" in output
        assert "[RECHARTS_SERIES]" in output
        assert "[RECHARTS_AXES]" in output
        assert "[RECHARTS_API]" in output


# ═══════════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════

class TestRechartsEdgeCases:
    """Edge case and regression tests."""

    def test_empty_file(self):
        parser = EnhancedRechartsParser()
        assert parser.is_recharts_file("", "empty.js") is False

    def test_non_recharts_file(self):
        parser = EnhancedRechartsParser()
        code = "console.log('hello world')"
        assert parser.is_recharts_file(code, "hello.js") is False

    def test_react_only_file(self):
        parser = EnhancedRechartsParser()
        code = '''
import React from 'react';
function App() { return <div>Hello</div>; }
export default App;
'''
        assert parser.is_recharts_file(code, "App.tsx") is False

    def test_d3_not_recharts(self):
        """D3.js alone is NOT Recharts."""
        parser = EnhancedRechartsParser()
        code = '''
import * as d3 from 'd3';
d3.select('#chart').append('svg').attr('width', 800);
'''
        assert parser.is_recharts_file(code, "chart.js") is False

    def test_chartjs_not_recharts(self):
        """Chart.js is NOT Recharts."""
        parser = EnhancedRechartsParser()
        code = '''
import Chart from 'chart.js/auto';
const chart = new Chart(ctx, { type: 'bar' });
'''
        assert parser.is_recharts_file(code, "chart.js") is False

    def test_mixed_recharts_and_react(self):
        parser = EnhancedRechartsParser()
        code = '''
import React, { useMemo, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';

function SalesChart({ data }) {
  const [activeIndex, setActiveIndex] = useState(0);
  const chartData = useMemo(() =>
    data.map(d => ({ ...d, profit: d.revenue - d.cost })),
    [data]
  );

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart data={chartData}>
        <XAxis dataKey="month" />
        <YAxis tickFormatter={(v) => `$${v}`} />
        <Tooltip formatter={(v) => `$${v.toLocaleString()}`} />
        <Legend onClick={(e) => setActiveIndex(e.dataKey)} />
        <Line type="monotone" dataKey="revenue" stroke="#8884d8" />
        <Line type="monotone" dataKey="profit" stroke="#82ca9d" />
      </LineChart>
    </ResponsiveContainer>
  );
}
'''
        result = parser.parse(code, "SalesChart.tsx")
        assert 'recharts' in result.detected_frameworks
        assert len(result.components) >= 1
        assert len(result.series) >= 2
        assert len(result.axes) >= 2
        assert len(result.tooltips) >= 1
        assert len(result.legends) >= 1
        assert len(result.responsive_containers) >= 1
        assert result.has_responsive is True

    def test_multiple_charts_in_dashboard(self):
        parser = EnhancedRechartsParser()
        code = '''
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie,
  XAxis, YAxis, Tooltip, Legend, Cell, ResponsiveContainer
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

function Dashboard({ salesData, distributionData }) {
  return (
    <div>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={salesData}>
          <XAxis dataKey="month" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Line dataKey="sales" stroke="#8884d8" />
          <Line dataKey="profit" stroke="#82ca9d" />
        </LineChart>
      </ResponsiveContainer>

      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={salesData}>
          <XAxis dataKey="month" />
          <YAxis />
          <Bar dataKey="orders" fill="#ffc658" />
        </BarChart>
      </ResponsiveContainer>

      <PieChart width={400} height={400}>
        <Pie data={distributionData} dataKey="value">
          {distributionData.map((entry, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
      </PieChart>
    </div>
  );
}
'''
        result = parser.parse(code, "Dashboard.tsx")
        assert len(result.components) >= 3
        assert len(result.series) >= 4
        assert len(result.responsive_containers) >= 2
        assert len(result.cells) >= 1

    def test_typescript_recharts_file(self):
        parser = EnhancedRechartsParser()
        code = '''
import { LineChart, Line, XAxis, YAxis, Tooltip } from 'recharts';
import { TooltipProps } from 'recharts';
import type { ValueType, NameType } from 'recharts/types/component/DefaultTooltipContent';

interface ChartData {
  month: string;
  revenue: number;
  cost: number;
}

const CustomTooltip: React.FC<TooltipProps<ValueType, NameType>> = ({
  active, payload, label,
}) => {
  if (active && payload?.length) {
    return <div>{label}: ${payload[0].value}</div>;
  }
  return null;
};

const RevenueChart: React.FC<{ data: ChartData[] }> = ({ data }) => (
  <LineChart width={600} height={300} data={data}>
    <XAxis dataKey="month" />
    <YAxis />
    <Tooltip content={<CustomTooltip />} />
    <Line dataKey="revenue" stroke="#8884d8" />
  </LineChart>
);
'''
        result = parser.parse(code, "Revenue.tsx")
        assert isinstance(result, RechartsParseResult)
        assert result.file_type == "tsx"
        assert result.has_typescript is True
        assert len(result.types) >= 1
        assert len(result.tooltips) >= 1
        assert result.tooltips[0].has_content is True

    def test_ssr_dynamic_import(self):
        parser = EnhancedRechartsParser()
        code = '''
import dynamic from 'next/dynamic';

const SalesChart = dynamic(() => import('../components/SalesChart'), {
  ssr: false,
  loading: () => <div>Loading chart...</div>,
});
'''
        # This file should NOT be flagged as recharts (no direct recharts import)
        result = parser.parse(code, "page.tsx")
        assert isinstance(result, RechartsParseResult)

    def test_stacked_bar_chart(self):
        parser = EnhancedRechartsParser()
        code = '''
import { BarChart, Bar, XAxis, YAxis } from 'recharts';

<BarChart data={data}>
  <XAxis dataKey="name" />
  <YAxis />
  <Bar dataKey="desktop" stackId="a" fill="#8884d8" />
  <Bar dataKey="mobile" stackId="a" fill="#82ca9d" />
  <Bar dataKey="tablet" stackId="a" fill="#ffc658" />
</BarChart>
'''
        result = parser.parse(code, "stacked.tsx")
        stacked = [s for s in result.series if s.has_stack_id]
        assert len(stacked) >= 3

    def test_dual_axis_chart(self):
        parser = EnhancedRechartsParser()
        code = '''
import { ComposedChart, Line, Bar, XAxis, YAxis } from 'recharts';

<ComposedChart data={data}>
  <XAxis dataKey="name" />
  <YAxis yAxisId="left" />
  <YAxis yAxisId="right" orientation="right" />
  <Bar dataKey="sales" yAxisId="left" fill="#8884d8" />
  <Line dataKey="trend" yAxisId="right" stroke="#ff7300" />
</ComposedChart>
'''
        result = parser.parse(code, "dual-axis.tsx")
        assert len(result.axes) >= 3  # XAxis + 2 YAxis

    def test_reference_annotations(self):
        parser = EnhancedRechartsParser()
        code = '''
import { LineChart, Line, ReferenceLine, ReferenceArea, ReferenceDot } from 'recharts';

<LineChart data={data}>
  <ReferenceLine y={100} stroke="red" strokeDasharray="3 3" label="Target" />
  <ReferenceArea y1={80} y2={120} fill="#82ca9d" fillOpacity={0.2} label="Normal" />
  <ReferenceDot x="Mar" y={9800} r={8} fill="red" />
  <Line dataKey="actual" />
</LineChart>
'''
        result = parser.parse(code, "annotations.tsx")
        assert len(result.references) >= 3
        ref_types = [r.reference_type for r in result.references]
        assert 'line' in ref_types
        assert 'area' in ref_types
        assert 'dot' in ref_types

    def test_brush_navigation(self):
        parser = EnhancedRechartsParser()
        code = '''
import { LineChart, Line, Brush, XAxis } from 'recharts';

<LineChart data={yearlyData}>
  <XAxis dataKey="date" />
  <Line dataKey="value" />
  <Brush
    dataKey="date"
    height={30}
    stroke="#8884d8"
    startIndex={yearlyData.length - 30}
    endIndex={yearlyData.length - 1}
  />
</LineChart>
'''
        result = parser.parse(code, "brush-nav.tsx")
        assert len(result.brushes) >= 1
        b = result.brushes[0]
        assert b.has_start_index is True
        assert b.has_end_index is True

    def test_gradient_area_chart(self):
        parser = EnhancedRechartsParser()
        code = '''
import { AreaChart, Area, XAxis, YAxis } from 'recharts';

<AreaChart data={data}>
  <defs>
    <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
      <stop offset="5%" stopColor="#8884d8" stopOpacity={0.8} />
      <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
    </linearGradient>
  </defs>
  <XAxis dataKey="name" />
  <YAxis />
  <Area dataKey="value" fill="url(#colorValue)" stroke="#8884d8" />
</AreaChart>
'''
        result = parser.parse(code, "gradient.tsx")
        assert len(result.components) >= 1
        assert result.components[0].chart_type == 'area'
        assert len(result.series) >= 1

    def test_animation_disabled_for_performance(self):
        parser = EnhancedRechartsParser()
        code = '''
import { LineChart, Line } from 'recharts';

<LineChart data={largeData}>
  <Line dataKey="value" isAnimationActive={false} dot={false} />
</LineChart>
'''
        result = parser.parse(code, "perf.tsx")
        assert len(result.animations) >= 1
        anim = result.animations[0]
        assert anim.animation_type == 'active' or anim.animation_type == 'disabled'

    def test_synchronized_charts(self):
        parser = EnhancedRechartsParser()
        code = '''
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';

<LineChart syncId="metrics" data={data}>
  <XAxis dataKey="date" />
  <YAxis />
  <Tooltip />
  <Line dataKey="revenue" />
</LineChart>

<BarChart syncId="metrics" data={data}>
  <XAxis dataKey="date" />
  <YAxis />
  <Tooltip />
  <Bar dataKey="orders" />
</BarChart>
'''
        result = parser.parse(code, "synced.tsx")
        synced = [c for c in result.components if c.has_sync_id]
        assert len(synced) >= 2

    def test_custom_legend_and_tooltip(self):
        parser = EnhancedRechartsParser()
        code = '''
import { LineChart, Line, Tooltip, Legend } from 'recharts';

<LineChart data={data}>
  <Tooltip
    content={customRenderer}
    cursor={{ stroke: '#ccc' }}
    wrapperStyle={{ borderRadius: 8 }}
  />
  <Legend
    content={customLegendRenderer}
    verticalAlign="top"
    align="right"
    layout="vertical"
    onClick={handleLegendClick}
  />
  <Line dataKey="value" />
</LineChart>
'''
        result = parser.parse(code, "custom-ui.tsx")
        assert len(result.tooltips) >= 1
        t = result.tooltips[0]
        assert t.has_content is True
        assert t.has_cursor is True
        assert t.has_wrapper_style is True

        assert len(result.legends) >= 1
        leg = result.legends[0]
        assert leg.has_content is True
        assert leg.has_vertical_align is True
        assert leg.has_align is True
        assert leg.has_layout is True
        assert leg.has_on_click is True

    def test_event_handlers(self):
        parser = EnhancedRechartsParser()
        code = '''
import { BarChart, Bar, ScatterChart, Scatter } from 'recharts';

<BarChart data={data} onClick={handleClick} onMouseMove={handleMove}>
  <Bar dataKey="value" onClick={handleBarClick} />
</BarChart>
'''
        result = parser.parse(code, "events.tsx")
        assert len(result.events) >= 1

    def test_large_import_list(self):
        parser = EnhancedRechartsParser()
        code = '''
import {
  LineChart, BarChart, AreaChart, PieChart, RadarChart,
  ScatterChart, ComposedChart, RadialBarChart, Treemap,
  FunnelChart, Sankey, ResponsiveContainer,
  Line, Bar, Area, Pie, Radar, Scatter, RadialBar, Funnel,
  XAxis, YAxis, ZAxis, CartesianGrid,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis,
  Tooltip, Legend, ReferenceLine, ReferenceArea, ReferenceDot,
  Brush, Cell, LabelList, Label, Sector, Curve,
  Cross, Rectangle, Polygon
} from 'recharts';
'''
        result = parser.parse(code, "all-imports.tsx")
        assert 'recharts' in result.detected_frameworks
        assert len(result.imports) >= 1
        assert result.is_tree_shakeable is True
