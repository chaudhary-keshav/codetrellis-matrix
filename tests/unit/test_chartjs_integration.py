"""
Tests for Chart.js charting library integration.

Tests cover:
- All 5 extractors (chart_config, dataset, scale, plugin, api)
- Parser (EnhancedChartJSParser)
- Scanner integration (ProjectMatrix fields, _parse_chartjs)
- Compressor integration ([CHARTJS_*] sections)
"""

import pytest
from codetrellis.extractors.chartjs import (
    ChartConfigExtractor,
    ChartDatasetExtractor,
    ChartScaleExtractor,
    ChartPluginExtractor,
    ChartAPIExtractor,
)
from codetrellis.chartjs_parser_enhanced import EnhancedChartJSParser, ChartJSParseResult


# ═══════════════════════════════════════════════════════════════════════
# Chart Config Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestChartConfigExtractor:
    """Tests for ChartConfigExtractor."""

    def setup_method(self):
        self.extractor = ChartConfigExtractor()

    def test_new_chart_constructor_detection(self):
        code = '''
const myChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [{ label: 'Sales', data: [12, 19, 3] }]
  },
  options: {
    responsive: true,
    plugins: { legend: { position: 'top' } }
  }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        inst = result['instances'][0]
        assert inst.chart_type == 'bar'
        assert inst.creation_method == 'constructor'
        assert inst.has_options is True
        assert inst.has_data is True

    def test_line_chart_type_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'line',
  data: { labels: ['A', 'B'], datasets: [{ data: [1, 2] }] }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        assert result['instances'][0].chart_type == 'line'

    def test_pie_chart_type_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'pie',
  data: { labels: ['Red', 'Blue'], datasets: [{ data: [10, 20] }] }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        assert result['instances'][0].chart_type == 'pie'

    def test_doughnut_chart_type_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'doughnut',
  data: { datasets: [{ data: [30, 50, 20] }] }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        assert result['instances'][0].chart_type == 'doughnut'

    def test_radar_chart_type_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'radar',
  data: { labels: ['A', 'B', 'C'], datasets: [{ data: [1, 2, 3] }] }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        assert result['instances'][0].chart_type == 'radar'

    def test_scatter_chart_type_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'scatter',
  data: { datasets: [{ data: [{x:1,y:2},{x:3,y:4}] }] }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        assert result['instances'][0].chart_type == 'scatter'

    def test_bubble_chart_type_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'bubble',
  data: { datasets: [{ data: [{x:1,y:2,r:5}] }] }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        assert result['instances'][0].chart_type == 'bubble'

    def test_polararea_chart_type_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'polarArea',
  data: { labels: ['A', 'B'], datasets: [{ data: [10, 20] }] }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        assert result['instances'][0].chart_type == 'polarArea'

    def test_responsive_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'bar',
  data: { labels: [], datasets: [] },
  options: {
    responsive: true,
    maintainAspectRatio: false
  }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        assert result['instances'][0].is_responsive is True

    def test_plugins_in_config_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'bar',
  data: {},
  options: {},
  plugins: [customPlugin]
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['instances']) >= 1
        assert result['instances'][0].has_plugins is True

    def test_react_component_detection(self):
        code = '''
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
const chart = <Line data={data} options={options} />;
const barChart = <Bar data={barData} />;
'''
        result = self.extractor.extract(code, "Chart.tsx")
        assert len(result['instances']) >= 1

    def test_v2_global_defaults_detection(self):
        code = '''
Chart.defaults.global.defaultFontFamily = "'Inter', sans-serif";
Chart.defaults.global.defaultFontSize = 14;
Chart.defaults.global.defaultFontColor = '#333';
'''
        result = self.extractor.extract(code, "config.js")
        assert len(result['defaults']) >= 1
        default_entry = result['defaults'][0]
        assert default_entry.is_v2_style is True

    def test_v3_defaults_detection(self):
        code = '''
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 14;
Chart.defaults.color = '#333';
Chart.defaults.plugins.legend.position = 'bottom';
'''
        result = self.extractor.extract(code, "config.js")
        assert len(result['defaults']) >= 1

    def test_multiple_charts_in_one_file(self):
        code = '''
const barChart = new Chart(ctx1, {
  type: 'bar',
  data: { labels: ['A'], datasets: [{ data: [1] }] }
});

const lineChart = new Chart(ctx2, {
  type: 'line',
  data: { labels: ['A'], datasets: [{ data: [1] }] }
});

const pieChart = new Chart(ctx3, {
  type: 'pie',
  data: { labels: ['A'], datasets: [{ data: [1] }] }
});
'''
        result = self.extractor.extract(code, "dashboard.js")
        assert len(result['instances']) >= 3

    def test_angular_basechart_detection(self):
        code = '''
<canvas baseChart
  [type]="'bar'"
  [data]="barChartData"
  [options]="barChartOptions">
</canvas>
'''
        result = self.extractor.extract(code, "chart.component.html")
        assert len(result['instances']) >= 1

    def test_config_type_detection(self):
        code = '''
const config = {
  type: 'bar',
  data: {
    labels: ['A', 'B'],
    datasets: [{ data: [1, 2] }]
  },
  options: {
    responsive: true
  }
};
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['configs']) >= 1


# ═══════════════════════════════════════════════════════════════════════
# Dataset Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestChartDatasetExtractor:
    """Tests for ChartDatasetExtractor."""

    def setup_method(self):
        self.extractor = ChartDatasetExtractor()

    def test_basic_dataset_detection(self):
        code = '''
const data = {
  labels: ['Jan', 'Feb', 'Mar'],
  datasets: [{
    label: 'Revenue',
    data: [120, 190, 300],
    backgroundColor: 'rgba(54, 162, 235, 0.5)',
    borderColor: 'rgba(54, 162, 235, 1)',
    borderWidth: 1
  }]
};
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['datasets']) >= 1
        ds = result['datasets'][0]
        assert ds.has_label is True
        assert ds.has_data is True
        assert ds.has_background_color is True
        assert ds.has_border_color is True

    def test_multiple_datasets_detection(self):
        code = '''
const data = {
  labels: ['Q1', 'Q2', 'Q3', 'Q4'],
  datasets: [
    {
      label: 'Revenue',
      data: [120, 190, 300, 250],
      borderColor: '#3b82f6'
    },
    {
      label: 'Expenses',
      data: [80, 120, 180, 150],
      borderColor: '#ef4444'
    }
  ]
};
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['datasets']) >= 2

    def test_fill_detection(self):
        code = '''
datasets: [{
  label: 'Temperature',
  data: [20, 22, 25],
  fill: 'origin',
  backgroundColor: 'rgba(54, 162, 235, 0.2)'
}]
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['datasets']) >= 1
        assert result['datasets'][0].has_fill is True

    def test_tension_detection(self):
        code = '''
datasets: [{
  label: 'Smooth Line',
  data: [10, 20, 15],
  tension: 0.4
}]
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['datasets']) >= 1
        assert result['datasets'][0].has_tension is True

    def test_point_style_detection(self):
        code = '''
datasets: [{
  label: 'Points',
  data: [10, 20, 30],
  pointStyle: 'triangle',
  pointRadius: 6
}]
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['datasets']) >= 1
        assert result['datasets'][0].has_point_style is True

    def test_dataset_type_override_detection(self):
        code = '''
datasets: [
  {
    label: 'Bars',
    data: [12, 19, 3],
    type: 'bar'
  },
  {
    label: 'Line',
    data: [10, 15, 8],
    type: 'line'
  }
]
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['datasets']) >= 1
        has_override = any(ds.has_type_override for ds in result['datasets'])
        assert has_override is True

    def test_data_point_xy_format(self):
        code = '''
datasets: [{
  data: [
    { x: 10, y: 20 },
    { x: 15, y: 30 },
    { x: 20, y: 10 }
  ]
}]
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['data_points']) >= 1

    def test_hover_style_detection(self):
        code = '''
datasets: [{
  label: 'Sales',
  data: [10, 20, 30],
  hoverBackgroundColor: 'rgba(255, 99, 132, 0.8)',
  hoverBorderColor: 'rgba(255, 99, 132, 1)',
  hoverBorderWidth: 2
}]
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['datasets']) >= 1
        assert result['datasets'][0].has_hover_style is True


# ═══════════════════════════════════════════════════════════════════════
# Scale Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestChartScaleExtractor:
    """Tests for ChartScaleExtractor."""

    def setup_method(self):
        self.extractor = ChartScaleExtractor()

    def test_v3_linear_scale_detection(self):
        code = '''
options: {
  scales: {
    y: {
      type: 'linear',
      beginAtZero: true,
      title: { display: true, text: 'Revenue ($)' }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        scale = result['scales'][0]
        assert scale.scale_type == 'linear'

    def test_v3_category_scale_detection(self):
        code = '''
options: {
  scales: {
    x: {
      type: 'category',
      title: { display: true, text: 'Month' }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        assert result['scales'][0].scale_type == 'category'

    def test_v3_time_scale_detection(self):
        code = '''
options: {
  scales: {
    x: {
      type: 'time',
      time: {
        unit: 'month',
        displayFormats: { month: 'MMM yyyy' }
      }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        scale = result['scales'][0]
        assert scale.scale_type == 'time'
        assert scale.has_time_config is True

    def test_v3_logarithmic_scale_detection(self):
        code = '''
options: {
  scales: {
    y: {
      type: 'logarithmic',
      min: 1,
      max: 10000
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        assert result['scales'][0].scale_type == 'logarithmic'

    def test_v2_xaxes_yaxes_detection(self):
        code = '''
options: {
  scales: {
    xAxes: [{
      display: true,
      scaleLabel: { display: true, labelString: 'Month' }
    }],
    yAxes: [{
      ticks: { beginAtZero: true }
    }]
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        has_v2 = any(s.is_v2_style for s in result['scales'])
        assert has_v2 is True

    def test_begin_at_zero_detection(self):
        code = '''
options: {
  scales: {
    y: {
      beginAtZero: true
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        assert result['scales'][0].has_begin_at_zero is True

    def test_ticks_configuration_detection(self):
        code = '''
options: {
  scales: {
    y: {
      ticks: {
        callback: function(value) { return '$' + value; },
        stepSize: 10
      }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        assert result['scales'][0].has_ticks is True

    def test_grid_configuration_detection(self):
        code = '''
options: {
  scales: {
    y: {
      grid: {
        display: true,
        color: 'rgba(0, 0, 0, 0.1)'
      }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        assert result['scales'][0].has_grid is True

    def test_stacked_scales_detection(self):
        code = '''
options: {
  scales: {
    x: { stacked: true },
    y: { stacked: true }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        has_stacked = any(s.has_stacked for s in result['scales'])
        assert has_stacked is True

    def test_min_max_detection(self):
        code = '''
options: {
  scales: {
    y: {
      min: 0,
      max: 100,
      suggestedMin: 10,
      suggestedMax: 90
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        scale = result['scales'][0]
        assert scale.has_min is True
        assert scale.has_max is True

    def test_radial_linear_scale_detection(self):
        code = '''
options: {
  scales: {
    r: {
      type: 'radialLinear',
      angleLines: { display: true },
      pointLabels: { display: true }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        assert result['scales'][0].scale_type == 'radialLinear'

    def test_axis_title_detection(self):
        code = '''
options: {
  scales: {
    x: {
      title: { display: true, text: 'Date' }
    },
    y: {
      title: { display: true, text: 'Value' }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 1
        has_title = any(s.has_title for s in result['scales'])
        assert has_title is True

    def test_multiple_scales_detection(self):
        code = '''
options: {
  scales: {
    x: { type: 'category' },
    y: { type: 'linear', position: 'left' },
    y1: { type: 'linear', position: 'right' }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['scales']) >= 2

    def test_axis_callback_detection(self):
        code = '''
options: {
  scales: {
    y: {
      ticks: {
        callback: function(value) {
          return '$' + value.toLocaleString();
        }
      }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['axis_features']) >= 1
        has_callback = any(af.has_callback for af in result['axis_features'])
        assert has_callback is True


# ═══════════════════════════════════════════════════════════════════════
# Plugin Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestChartPluginExtractor:
    """Tests for ChartPluginExtractor."""

    def setup_method(self):
        self.extractor = ChartPluginExtractor()

    def test_chart_register_detection(self):
        code = '''
import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
} from 'chart.js';

Chart.register(
  BarController,
  BarElement,
  CategoryScale,
  LinearScale,
  Tooltip,
  Legend
);
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['registrations']) >= 1
        reg = result['registrations'][0]
        assert reg.registration_method == 'register'

    def test_v2_plugins_register_detection(self):
        code = '''
Chart.plugins.register({
  id: 'myPlugin',
  beforeDraw: function(chart) { }
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['registrations']) >= 1

    def test_registerables_detection(self):
        code = '''
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['registrations']) >= 1

    def test_builtin_plugin_tooltip_detection(self):
        code = '''
options: {
  plugins: {
    tooltip: {
      mode: 'index',
      intersect: false,
      callbacks: {
        label: (ctx) => `${ctx.dataset.label}: $${ctx.parsed.y}`
      }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['plugins']) >= 1
        tooltip = [p for p in result['plugins'] if p.plugin_id == 'tooltip']
        assert len(tooltip) >= 1
        assert tooltip[0].plugin_type == 'builtin'

    def test_builtin_plugin_legend_detection(self):
        code = '''
options: {
  plugins: {
    legend: {
      position: 'bottom',
      labels: { usePointStyle: true }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['plugins']) >= 1
        legend = [p for p in result['plugins'] if p.plugin_id == 'legend']
        assert len(legend) >= 1

    def test_builtin_plugin_title_detection(self):
        code = '''
options: {
  plugins: {
    title: {
      display: true,
      text: 'Monthly Revenue',
      font: { size: 18, weight: 'bold' }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['plugins']) >= 1
        title = [p for p in result['plugins'] if p.plugin_id == 'title']
        assert len(title) >= 1

    def test_builtin_plugin_decimation_detection(self):
        code = '''
options: {
  plugins: {
    decimation: {
      enabled: true,
      algorithm: 'lttb',
      samples: 500
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['plugins']) >= 1
        decimation = [p for p in result['plugins'] if p.plugin_id == 'decimation']
        assert len(decimation) >= 1

    def test_ecosystem_plugin_datalabels_detection(self):
        code = '''
import ChartDataLabels from 'chartjs-plugin-datalabels';
Chart.register(ChartDataLabels);

options: {
  plugins: {
    datalabels: {
      anchor: 'end',
      align: 'top',
      formatter: (value) => '$' + value
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['plugins']) >= 1
        datalabels = [p for p in result['plugins'] if p.plugin_id == 'datalabels']
        assert len(datalabels) >= 1
        assert datalabels[0].plugin_type == 'ecosystem'

    def test_ecosystem_plugin_zoom_detection(self):
        code = '''
import zoomPlugin from 'chartjs-plugin-zoom';
Chart.register(zoomPlugin);

options: {
  plugins: {
    zoom: {
      zoom: {
        wheel: { enabled: true },
        mode: 'x'
      },
      pan: { enabled: true, mode: 'x' }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['plugins']) >= 1
        zoom = [p for p in result['plugins'] if p.plugin_id == 'zoom']
        assert len(zoom) >= 1

    def test_ecosystem_plugin_annotation_detection(self):
        code = '''
import annotationPlugin from 'chartjs-plugin-annotation';
Chart.register(annotationPlugin);

options: {
  plugins: {
    annotation: {
      annotations: {
        targetLine: {
          type: 'line',
          yMin: 75,
          yMax: 75,
          borderColor: 'red'
        }
      }
    }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['plugins']) >= 1
        annotation = [p for p in result['plugins'] if p.plugin_id == 'annotation']
        assert len(annotation) >= 1

    def test_custom_inline_plugin_detection(self):
        code = '''
const chart = new Chart(ctx, {
  type: 'line',
  data: {},
  plugins: [{
    id: 'customBackground',
    beforeDraw: (chart) => {
      const { ctx, chartArea: { left, top, width, height } } = chart;
      ctx.save();
      ctx.fillStyle = '#f8fafc';
      ctx.fillRect(left, top, width, height);
      ctx.restore();
    }
  }]
});
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['plugins']) >= 1
        custom = [p for p in result['plugins'] if p.plugin_type == 'custom']
        assert len(custom) >= 1

    def test_multiple_builtin_plugins_detection(self):
        code = '''
options: {
  plugins: {
    tooltip: { mode: 'index' },
    legend: { position: 'top' },
    title: { display: true, text: 'Chart' },
    subtitle: { display: true, text: 'Sub' },
    filler: {},
    decimation: { enabled: true }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['plugins']) >= 4


# ═══════════════════════════════════════════════════════════════════════
# API Extractor Tests
# ═══════════════════════════════════════════════════════════════════════

class TestChartAPIExtractor:
    """Tests for ChartAPIExtractor."""

    def setup_method(self):
        self.extractor = ChartAPIExtractor()

    def test_named_import_detection(self):
        code = '''
import { Chart, registerables } from 'chart.js';
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.import_type == 'module_named'
        assert imp.package == 'chart.js'
        assert imp.is_tree_shakeable is True

    def test_auto_import_detection(self):
        code = '''
import Chart from 'chart.js/auto';
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['imports']) >= 1
        imp = result['imports'][0]
        assert imp.is_auto is True

    def test_namespace_import_detection(self):
        code = '''
import * as Chart from 'chart.js';
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['imports']) >= 1

    def test_require_import_detection(self):
        code = '''
const Chart = require('chart.js');
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['imports']) >= 1

    def test_cdn_import_detection(self):
        code = '''
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
'''
        result = self.extractor.extract(code, "index.html")
        assert len(result['imports']) >= 1

    def test_unpkg_cdn_import_detection(self):
        code = '''
<script src="https://unpkg.com/chart.js@4.4.0/dist/chart.umd.js"></script>
'''
        result = self.extractor.extract(code, "index.html")
        assert len(result['imports']) >= 1

    def test_cdnjs_cdn_import_detection(self):
        code = '''
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.min.js"></script>
'''
        result = self.extractor.extract(code, "index.html")
        assert len(result['imports']) >= 1

    def test_react_chartjs_2_integration_detection(self):
        code = '''
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
'''
        result = self.extractor.extract(code, "Chart.tsx")
        assert len(result['integrations']) >= 1
        react_int = [i for i in result['integrations'] if i.integration_type == 'react']
        assert len(react_int) >= 1

    def test_vue_chartjs_integration_detection(self):
        code = '''
import { Bar } from 'vue-chartjs';
'''
        result = self.extractor.extract(code, "Chart.vue")
        assert len(result['integrations']) >= 1
        vue_int = [i for i in result['integrations'] if i.integration_type == 'vue']
        assert len(vue_int) >= 1

    def test_ng2_charts_integration_detection(self):
        code = '''
import { NgChartsModule } from 'ng2-charts';
'''
        result = self.extractor.extract(code, "chart.module.ts")
        assert len(result['integrations']) >= 1
        ng_int = [i for i in result['integrations'] if i.integration_type == 'angular']
        assert len(ng_int) >= 1

    def test_svelte_chartjs_integration_detection(self):
        code = '''
import { Bar } from 'svelte-chartjs';
'''
        result = self.extractor.extract(code, "Chart.svelte")
        assert len(result['integrations']) >= 1
        svelte_int = [i for i in result['integrations'] if i.integration_type == 'svelte']
        assert len(svelte_int) >= 1

    def test_date_adapter_detection(self):
        code = '''
import 'chartjs-adapter-date-fns';
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['integrations']) >= 1 or len(result['imports']) >= 1

    def test_v2_version_detection(self):
        code = '''
Chart.defaults.global.defaultFontFamily = 'Arial';
options: {
  scales: {
    xAxes: [{ display: true }],
    yAxes: [{ ticks: { beginAtZero: true } }]
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        fw_info = result['framework_info']
        assert fw_info['is_v2'] is True

    def test_v3_version_detection(self):
        code = '''
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);
'''
        result = self.extractor.extract(code, "chart.js")
        fw_info = result['framework_info']
        assert fw_info['is_v3_plus'] is True

    def test_v4_version_detection(self):
        code = '''
import Chart from 'chart.js/auto';
'''
        result = self.extractor.extract(code, "chart.js")
        fw_info = result['framework_info']
        # v4 is chart.js/auto with ESM-only
        assert fw_info['is_auto'] is True

    def test_animation_detection(self):
        code = '''
options: {
  animation: {
    duration: 1500,
    easing: 'easeOutBounce'
  },
  transitions: {
    active: { animation: { duration: 200 } }
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['animations']) >= 1
        assert result['framework_info']['has_animation'] is True

    def test_interaction_detection(self):
        code = '''
options: {
  interaction: {
    mode: 'index',
    intersect: false
  },
  hover: {
    mode: 'nearest'
  },
  onClick: (event, elements) => {
    console.log(elements);
  }
}
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['interactions']) >= 1
        assert result['framework_info']['has_interaction'] is True

    def test_typescript_types_detection(self):
        code = '''
import { ChartConfiguration, ChartData, ChartOptions, ChartType } from 'chart.js';

const config: ChartConfiguration<'bar'> = {
  type: 'bar',
  data: chartData,
  options: chartOptions
};

const data: ChartData<'bar'> = {
  labels: ['A', 'B'],
  datasets: [{ data: [1, 2] }]
};
'''
        result = self.extractor.extract(code, "chart.ts")
        assert len(result['types']) >= 1
        assert result['framework_info']['has_typescript'] is True

    def test_tree_shakeable_detection(self):
        code = '''
import {
  Chart,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js';

Chart.register(
  BarController, BarElement, CategoryScale, LinearScale
);
'''
        result = self.extractor.extract(code, "chart.js")
        assert result['framework_info']['is_tree_shakeable'] is True

    def test_multiple_imports(self):
        code = '''
import { Chart, registerables } from 'chart.js';
import 'chartjs-adapter-date-fns';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import zoomPlugin from 'chartjs-plugin-zoom';
'''
        result = self.extractor.extract(code, "chart.js")
        assert len(result['imports']) >= 1

    def test_helpers_detection(self):
        code = '''
import { color } from 'chart.js/helpers';
const c = Chart.helpers.color('#ff0000');
'''
        result = self.extractor.extract(code, "chart.js")
        assert isinstance(result, dict)

    def test_v1_detection(self):
        code = '''
var myLineChart = new Chart(ctx).Line(data);
var myBarChart = new Chart(ctx).Bar(data);
var myPieChart = new Chart(ctx).Pie(data);
'''
        result = self.extractor.extract(code, "chart.js")
        fw_info = result['framework_info']
        assert fw_info['is_v1'] is True


# ═══════════════════════════════════════════════════════════════════════
# Parser Tests
# ═══════════════════════════════════════════════════════════════════════

class TestEnhancedChartJSParser:
    """Tests for EnhancedChartJSParser."""

    def setup_method(self):
        self.parser = EnhancedChartJSParser()

    def test_is_chartjs_file_import(self):
        code = '''
import Chart from 'chart.js/auto';
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is True

    def test_is_chartjs_file_named_import(self):
        code = '''
import { Chart, registerables } from 'chart.js';
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is True

    def test_is_chartjs_file_constructor(self):
        code = '''
const chart = new Chart(ctx, config);
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is True

    def test_is_chartjs_file_require(self):
        code = '''
const Chart = require('chart.js');
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is True

    def test_is_chartjs_file_react_chartjs_2(self):
        code = '''
import { Line, Bar } from 'react-chartjs-2';
'''
        assert self.parser.is_chartjs_file(code, "Chart.tsx") is True

    def test_is_chartjs_file_vue_chartjs(self):
        code = '''
import { Bar } from 'vue-chartjs';
'''
        assert self.parser.is_chartjs_file(code, "Chart.vue") is True

    def test_is_chartjs_file_ng2_charts(self):
        code = '''
import { NgChartsModule } from 'ng2-charts';
'''
        assert self.parser.is_chartjs_file(code, "chart.module.ts") is True

    def test_is_chartjs_file_cdn(self):
        code = '''
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
'''
        assert self.parser.is_chartjs_file(code, "index.html") is True

    def test_is_chartjs_file_chart_register(self):
        code = '''
Chart.register(BarController, BarElement, CategoryScale);
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is True

    def test_is_chartjs_file_chart_defaults(self):
        code = '''
Chart.defaults.font.family = 'Inter';
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is True

    def test_is_chartjs_file_plugin_import(self):
        code = '''
import ChartDataLabels from 'chartjs-plugin-datalabels';
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is True

    def test_is_chartjs_file_adapter_import(self):
        code = '''
import 'chartjs-adapter-date-fns';
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is True

    def test_is_chartjs_file_svelte_chartjs(self):
        code = '''
import { Bar } from 'svelte-chartjs';
'''
        assert self.parser.is_chartjs_file(code, "Chart.svelte") is True

    def test_is_chartjs_file_angular_chart_js(self):
        code = '''
import 'angular-chart.js';
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is True

    def test_is_chartjs_file_negative(self):
        code = '''
import React from 'react';
function App() { return <div>Hello</div>; }
'''
        assert self.parser.is_chartjs_file(code, "App.tsx") is False

    def test_is_chartjs_file_empty(self):
        assert self.parser.is_chartjs_file("", "empty.js") is False

    def test_is_chartjs_file_d3_not_chartjs(self):
        """D3.js is NOT Chart.js."""
        code = '''
import * as d3 from 'd3';
d3.select('#chart').append('svg').attr('width', 800);
'''
        assert self.parser.is_chartjs_file(code, "chart.js") is False

    def test_full_parse_bar_chart(self):
        code = '''
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);

const ctx = document.getElementById('myChart').getContext('2d');
const myChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
    datasets: [{
      label: 'Monthly Revenue',
      data: [12000, 19000, 30000, 25000, 22000, 31000],
      backgroundColor: 'rgba(54, 162, 235, 0.5)',
      borderColor: 'rgba(54, 162, 235, 1)',
      borderWidth: 1
    }]
  },
  options: {
    responsive: true,
    plugins: {
      legend: { position: 'top' },
      title: { display: true, text: 'Monthly Revenue' }
    },
    scales: {
      y: {
        beginAtZero: true,
        ticks: {
          callback: function(value) { return '$' + value.toLocaleString(); }
        }
      }
    }
  }
});
'''
        result = self.parser.parse(code, "bar-chart.js")
        assert isinstance(result, ChartJSParseResult)
        assert result.file_type == "js"

        # Check instances
        assert len(result.instances) >= 1
        assert result.instances[0].chart_type == 'bar'

        # Check datasets
        assert len(result.datasets) >= 1

        # Check scales
        assert len(result.scales) >= 1

        # Check plugins
        assert len(result.plugins) >= 1

        # Check registrations
        assert len(result.registrations) >= 1

        # Check imports
        assert len(result.imports) >= 1

        # Check frameworks detected
        assert 'chart.js' in result.detected_frameworks

    def test_full_parse_line_chart(self):
        code = '''
import Chart from 'chart.js/auto';

const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [{
      label: 'Revenue',
      data: [100, 200, 150],
      fill: 'origin',
      tension: 0.4,
      borderColor: '#3b82f6',
      backgroundColor: 'rgba(59, 130, 246, 0.2)'
    }]
  },
  options: {
    responsive: true,
    interaction: { mode: 'index', intersect: false },
    animation: { duration: 1000, easing: 'easeOutQuart' }
  }
});
'''
        result = self.parser.parse(code, "line-chart.js")
        assert isinstance(result, ChartJSParseResult)
        assert len(result.instances) >= 1
        assert result.instances[0].chart_type == 'line'
        assert result.is_auto is True
        assert result.has_animation is True
        assert result.has_interaction is True

    def test_full_parse_pie_chart(self):
        code = '''
import { Chart, ArcElement, Tooltip, Legend } from 'chart.js';
Chart.register(ArcElement, Tooltip, Legend);

const chart = new Chart(ctx, {
  type: 'pie',
  data: {
    labels: ['Red', 'Blue', 'Yellow'],
    datasets: [{
      label: 'Votes',
      data: [12, 19, 3],
      backgroundColor: [
        'rgba(255, 99, 132, 0.5)',
        'rgba(54, 162, 235, 0.5)',
        'rgba(255, 206, 86, 0.5)'
      ]
    }]
  },
  options: {
    plugins: {
      legend: { position: 'right' }
    }
  }
});
'''
        result = self.parser.parse(code, "pie-chart.js")
        assert len(result.instances) >= 1
        assert result.instances[0].chart_type == 'pie'
        assert result.is_tree_shakeable is True
        assert len(result.registrations) >= 1

    def test_full_parse_mixed_chart(self):
        code = '''
import Chart from 'chart.js/auto';

const chart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Jan', 'Feb', 'Mar', 'Apr'],
    datasets: [
      {
        label: 'Revenue',
        data: [120, 190, 300, 250],
        type: 'bar'
      },
      {
        label: 'Trend',
        data: [100, 160, 240, 280],
        type: 'line',
        borderColor: '#ef4444',
        fill: false
      }
    ]
  }
});
'''
        result = self.parser.parse(code, "mixed-chart.js")
        assert len(result.instances) >= 1

    def test_full_parse_react_chartjs2(self):
        code = '''
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

function RevenueChart({ data }) {
  const chartData = {
    labels: data.map(d => d.month),
    datasets: [{
      label: 'Revenue',
      data: data.map(d => d.value),
      borderColor: '#3b82f6',
      tension: 0.3
    }]
  };

  return <Line data={chartData} options={{ responsive: true }} />;
}
'''
        result = self.parser.parse(code, "RevenueChart.tsx")
        assert isinstance(result, ChartJSParseResult)
        assert result.file_type == "tsx"
        assert 'react-chartjs-2' in result.detected_frameworks
        assert 'chart.js' in result.detected_frameworks
        assert len(result.imports) >= 1
        assert len(result.registrations) >= 1
        assert len(result.instances) >= 1

    def test_full_parse_vue_chartjs(self):
        code = '''
import { Bar } from 'vue-chartjs';
import {
  Chart as ChartJS,
  BarElement,
  CategoryScale,
  LinearScale,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(BarElement, CategoryScale, LinearScale, Title, Tooltip, Legend);

const chartData = {
  labels: ['Q1', 'Q2', 'Q3'],
  datasets: [{
    label: 'Sales',
    data: [40, 60, 80],
    backgroundColor: '#3b82f6'
  }]
};
'''
        result = self.parser.parse(code, "Chart.vue")
        assert 'vue-chartjs' in result.detected_frameworks

    def test_full_parse_ng2_charts(self):
        code = '''
import { NgChartsModule } from 'ng2-charts';
import { ChartConfiguration, ChartData } from 'chart.js';

const barChartData: ChartData<'bar'> = {
  labels: ['Q1', 'Q2', 'Q3'],
  datasets: [{
    data: [65, 59, 80],
    label: 'Series A'
  }]
};
'''
        result = self.parser.parse(code, "chart.component.ts")
        assert result.file_type == "ts"
        assert 'ng2-charts' in result.detected_frameworks
        assert result.has_typescript is True

    def test_full_parse_v2_code(self):
        code = '''
var ctx = document.getElementById('myChart').getContext('2d');
var myChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['A', 'B', 'C'],
    datasets: [{
      label: 'Values',
      data: [12, 19, 3],
      backgroundColor: '#3b82f6'
    }]
  },
  options: {
    scales: {
      xAxes: [{
        display: true,
        scaleLabel: { display: true, labelString: 'Category' }
      }],
      yAxes: [{
        ticks: { beginAtZero: true }
      }]
    }
  }
});
Chart.defaults.global.defaultFontFamily = 'Arial';
'''
        result = self.parser.parse(code, "chart-v2.js")
        assert isinstance(result, ChartJSParseResult)
        assert len(result.instances) >= 1
        assert len(result.scales) >= 1
        # v2 detection
        has_v2 = any(s.is_v2_style for s in result.scales)
        assert has_v2 is True

    def test_full_parse_with_plugins(self):
        code = '''
import Chart from 'chart.js/auto';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import zoomPlugin from 'chartjs-plugin-zoom';
import annotationPlugin from 'chartjs-plugin-annotation';

Chart.register(ChartDataLabels, zoomPlugin, annotationPlugin);

const chart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['A', 'B', 'C'],
    datasets: [{
      label: 'Values',
      data: [12, 19, 3]
    }]
  },
  options: {
    plugins: {
      datalabels: { anchor: 'end', align: 'top' },
      zoom: { zoom: { wheel: { enabled: true } } },
      annotation: {
        annotations: {
          line1: { type: 'line', yMin: 10, yMax: 10 }
        }
      }
    }
  }
});
'''
        result = self.parser.parse(code, "chart-plugins.js")
        assert 'chartjs-plugin-datalabels' in result.detected_frameworks
        assert 'chartjs-plugin-zoom' in result.detected_frameworks
        assert 'chartjs-plugin-annotation' in result.detected_frameworks
        assert len(result.plugins) >= 3
        assert len(result.registrations) >= 1

    def test_full_parse_time_series(self):
        code = '''
import Chart from 'chart.js/auto';
import 'chartjs-adapter-date-fns';

const chart = new Chart(ctx, {
  type: 'line',
  data: {
    datasets: [{
      label: 'Temperature',
      data: [
        { x: '2024-01-01', y: 20 },
        { x: '2024-02-01', y: 22 },
        { x: '2024-03-01', y: 25 }
      ]
    }]
  },
  options: {
    scales: {
      x: {
        type: 'time',
        time: {
          unit: 'month',
          displayFormats: { month: 'MMM yyyy' }
        }
      }
    }
  }
});
'''
        result = self.parser.parse(code, "time-series.js")
        assert 'chartjs-adapter-date-fns' in result.detected_frameworks
        assert len(result.scales) >= 1
        time_scales = [s for s in result.scales if s.scale_type == 'time']
        assert len(time_scales) >= 1

    def test_framework_detection(self):
        code = '''
import { Chart } from 'chart.js';
import { Line } from 'react-chartjs-2';
import 'chartjs-adapter-date-fns';
import ChartDataLabels from 'chartjs-plugin-datalabels';
import zoomPlugin from 'chartjs-plugin-zoom';
'''
        result = self.parser.parse(code, "chart.tsx")
        fws = result.detected_frameworks
        assert 'chart.js' in fws
        assert 'react-chartjs-2' in fws
        assert 'chartjs-adapter-date-fns' in fws
        assert 'chartjs-plugin-datalabels' in fws
        assert 'chartjs-plugin-zoom' in fws

    def test_detect_chartjs_version_v2(self):
        code = '''
Chart.defaults.global.defaultFontFamily = 'Arial';
options: {
  scales: {
    xAxes: [{}],
    yAxes: [{}]
  }
}
'''
        result = self.parser.parse(code, "chart.js")
        # v2 has Chart.defaults.global and xAxes/yAxes
        assert result.chartjs_version in ['v2', '']

    def test_detect_chartjs_version_v3(self):
        code = '''
import { Chart, registerables } from 'chart.js';
Chart.register(...registerables);
'''
        result = self.parser.parse(code, "chart.js")
        # v3+ has Chart.register and registerables
        assert result.chartjs_version in ['v3', 'v4', '']

    def test_file_type_detection_tsx(self):
        code = 'import { Line } from "react-chartjs-2";'
        result = self.parser.parse(code, "Chart.tsx")
        assert result.file_type == "tsx"

    def test_file_type_detection_ts(self):
        code = 'import Chart from "chart.js/auto";'
        result = self.parser.parse(code, "chart.ts")
        assert result.file_type == "ts"

    def test_file_type_detection_html(self):
        code = '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>'
        result = self.parser.parse(code, "index.html")
        assert result.file_type == "html"


# ═══════════════════════════════════════════════════════════════════════
# Scanner Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestChartJSScannerIntegration:
    """Tests for scanner.py Chart.js integration."""

    def test_project_matrix_has_chartjs_fields(self):
        from codetrellis.scanner import ProjectMatrix
        m = ProjectMatrix(name="test", root_path="/tmp/test")
        # Verify all Chart.js fields exist
        assert hasattr(m, 'chartjs_instances')
        assert hasattr(m, 'chartjs_chart_types')
        assert hasattr(m, 'chartjs_configs')
        assert hasattr(m, 'chartjs_defaults')
        assert hasattr(m, 'chartjs_datasets')
        assert hasattr(m, 'chartjs_data_points')
        assert hasattr(m, 'chartjs_scales')
        assert hasattr(m, 'chartjs_axis_features')
        assert hasattr(m, 'chartjs_plugins')
        assert hasattr(m, 'chartjs_registrations')
        assert hasattr(m, 'chartjs_imports')
        assert hasattr(m, 'chartjs_integrations')
        assert hasattr(m, 'chartjs_types')
        assert hasattr(m, 'chartjs_animations')
        assert hasattr(m, 'chartjs_interactions')
        assert hasattr(m, 'chartjs_detected_frameworks')
        assert hasattr(m, 'chartjs_detected_features')
        assert hasattr(m, 'chartjs_version')
        assert hasattr(m, 'chartjs_is_tree_shakeable')
        assert hasattr(m, 'chartjs_is_auto')
        assert hasattr(m, 'chartjs_has_animation')
        assert hasattr(m, 'chartjs_has_interaction')
        assert hasattr(m, 'chartjs_has_typescript')

    def test_project_matrix_default_values(self):
        from codetrellis.scanner import ProjectMatrix
        m = ProjectMatrix(name="test", root_path="/tmp/test")
        assert m.chartjs_instances == []
        assert m.chartjs_scales == []
        assert m.chartjs_plugins == []
        assert m.chartjs_version == ""
        assert m.chartjs_is_tree_shakeable is False
        assert m.chartjs_is_auto is False
        assert m.chartjs_has_animation is False
        assert m.chartjs_has_interaction is False
        assert m.chartjs_has_typescript is False

    def test_scanner_has_chartjs_parser(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        assert hasattr(scanner, 'chartjs_parser')
        assert isinstance(scanner.chartjs_parser, EnhancedChartJSParser)

    def test_scanner_has_parse_chartjs_method(self):
        from codetrellis.scanner import ProjectScanner
        scanner = ProjectScanner()
        assert hasattr(scanner, '_parse_chartjs')
        assert callable(scanner._parse_chartjs)


# ═══════════════════════════════════════════════════════════════════════
# Compressor Integration Tests
# ═══════════════════════════════════════════════════════════════════════

class TestChartJSCompressorIntegration:
    """Tests for compressor.py Chart.js integration."""

    def test_compressor_has_chartjs_methods(self):
        from codetrellis.compressor import MatrixCompressor
        comp = MatrixCompressor()
        assert hasattr(comp, '_compress_chartjs_charts')
        assert hasattr(comp, '_compress_chartjs_datasets')
        assert hasattr(comp, '_compress_chartjs_scales')
        assert hasattr(comp, '_compress_chartjs_plugins')
        assert hasattr(comp, '_compress_chartjs_api')

    def test_compress_chartjs_charts_empty(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        result = comp._compress_chartjs_charts(matrix)
        assert result == []

    def test_compress_chartjs_charts_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.chartjs_instances = [{"name": "myChart", "file": "chart.js", "line": 5, "chart_type": "bar", "creation_method": "constructor", "has_options": True, "has_data": True, "has_plugins": False, "is_responsive": True, "canvas_ref": "ctx"}]
        matrix.chartjs_chart_types = [{"name": "bar", "file": "chart.js", "line": 5, "chart_type": "bar", "is_mixed": False, "is_stacked": False, "sub_types": []}]
        matrix.chartjs_configs = [{"name": "config", "file": "chart.js", "line": 3, "config_type": "inline", "has_type": True, "has_data": True, "has_options": True, "has_plugins": False}]
        result = comp._compress_chartjs_charts(matrix)
        assert len(result) > 0

    def test_compress_chartjs_datasets_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.chartjs_datasets = [{"name": "Revenue", "file": "chart.js", "line": 10, "dataset_type": "bar", "has_label": True, "has_data": True, "has_background_color": True, "has_border_color": True, "has_fill": False, "has_tension": False, "has_point_style": False, "has_bar_options": False, "has_hover_style": False, "has_type_override": False, "overridden_type": ""}]
        result = comp._compress_chartjs_datasets(matrix)
        assert len(result) > 0

    def test_compress_chartjs_scales_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.chartjs_scales = [{"name": "y", "file": "chart.js", "line": 20, "scale_type": "linear", "axis_id": "y", "axis_position": "left", "has_min": False, "has_max": False, "has_suggested_min": False, "has_suggested_max": False, "has_ticks": True, "has_grid": True, "has_title": False, "has_stacked": False, "has_begin_at_zero": True, "has_reverse": False, "has_time_config": False, "has_adapter": False, "is_v2_style": False}]
        result = comp._compress_chartjs_scales(matrix)
        assert len(result) > 0

    def test_compress_chartjs_plugins_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.chartjs_plugins = [{"name": "tooltip", "file": "chart.js", "line": 25, "plugin_type": "builtin", "plugin_id": "tooltip", "has_options": True, "hooks": [], "options_keys": ["mode", "intersect"]}]
        matrix.chartjs_registrations = [{"name": "register", "file": "chart.js", "line": 3, "registration_method": "register", "registered_items": ["BarController", "BarElement"]}]
        result = comp._compress_chartjs_plugins(matrix)
        assert len(result) > 0

    def test_compress_chartjs_api_with_data(self):
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.chartjs_detected_frameworks = ['chart.js', 'react-chartjs-2', 'chartjs-plugin-datalabels']
        matrix.chartjs_version = 'v4'
        matrix.chartjs_is_tree_shakeable = True
        matrix.chartjs_detected_features = ['charts', 'datasets', 'scales', 'plugins']
        result = comp._compress_chartjs_api(matrix)
        assert len(result) > 0
        assert any("ecosystem" in line.lower() or "chart" in line.lower() for line in result)

    def test_full_compression_includes_chartjs_sections(self):
        """Verify that a full compression with Chart.js data produces [CHARTJS_*] sections."""
        from codetrellis.compressor import MatrixCompressor
        from codetrellis.scanner import ProjectMatrix
        comp = MatrixCompressor()
        matrix = ProjectMatrix(name="test", root_path="/tmp/test")
        matrix.chartjs_instances = [{"name": "myChart", "file": "chart.js", "line": 5, "chart_type": "bar", "creation_method": "constructor", "has_options": True, "has_data": True, "has_plugins": False, "is_responsive": True, "canvas_ref": "ctx"}]
        matrix.chartjs_scales = [{"name": "y", "file": "chart.js", "line": 20, "scale_type": "linear", "axis_id": "y", "axis_position": "left", "has_min": False, "has_max": False, "has_suggested_min": False, "has_suggested_max": False, "has_ticks": True, "has_grid": False, "has_title": False, "has_stacked": False, "has_begin_at_zero": True, "has_reverse": False, "has_time_config": False, "has_adapter": False, "is_v2_style": False}]
        matrix.chartjs_plugins = [{"name": "tooltip", "file": "chart.js", "line": 25, "plugin_type": "builtin", "plugin_id": "tooltip", "has_options": True, "hooks": [], "options_keys": []}]
        matrix.chartjs_detected_frameworks = ['chart.js']
        matrix.chartjs_version = 'v4'
        matrix.chartjs_is_tree_shakeable = True

        # Run full compression
        output = comp.compress(matrix)
        assert "[CHARTJS_CHARTS]" in output
        assert "[CHARTJS_SCALES]" in output
        assert "[CHARTJS_PLUGINS]" in output
        assert "[CHARTJS_API]" in output


# ═══════════════════════════════════════════════════════════════════════
# Edge Case Tests
# ═══════════════════════════════════════════════════════════════════════

class TestChartJSEdgeCases:
    """Edge case and regression tests."""

    def test_empty_file(self):
        parser = EnhancedChartJSParser()
        assert parser.is_chartjs_file("", "empty.js") is False

    def test_non_chartjs_file(self):
        parser = EnhancedChartJSParser()
        code = "console.log('hello world')"
        assert parser.is_chartjs_file(code, "hello.js") is False

    def test_react_only_file(self):
        parser = EnhancedChartJSParser()
        code = '''
import React from 'react';
function App() { return <div>Hello</div>; }
export default App;
'''
        assert parser.is_chartjs_file(code, "App.tsx") is False

    def test_d3_not_chartjs(self):
        """D3.js is NOT Chart.js."""
        parser = EnhancedChartJSParser()
        code = '''
import * as d3 from 'd3';
d3.select('#chart').append('svg').attr('width', 800);
const xScale = d3.scaleLinear().domain([0, 100]).range([0, 500]);
'''
        assert parser.is_chartjs_file(code, "chart.js") is False

    def test_mixed_chartjs_and_react(self):
        parser = EnhancedChartJSParser()
        code = '''
import React, { useRef, useMemo } from 'react';
import { Line } from 'react-chartjs-2';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

function LineChart({ data }) {
  const chartData = useMemo(() => ({
    labels: data.map(d => d.month),
    datasets: [{
      label: 'Revenue',
      data: data.map(d => d.value),
      borderColor: '#3b82f6',
      tension: 0.3
    }]
  }), [data]);

  return <Line data={chartData} options={{ responsive: true }} />;
}
'''
        result = parser.parse(code, "LineChart.tsx")
        assert 'chart.js' in result.detected_frameworks
        assert 'react-chartjs-2' in result.detected_frameworks
        assert len(result.instances) >= 1
        assert len(result.imports) >= 1

    def test_multiple_charts_in_one_file(self):
        parser = EnhancedChartJSParser()
        code = '''
import Chart from 'chart.js/auto';

const barChart = new Chart(ctx1, {
  type: 'bar',
  data: {
    labels: ['A', 'B'],
    datasets: [{ label: 'Sales', data: [10, 20] }]
  }
});

const lineChart = new Chart(ctx2, {
  type: 'line',
  data: {
    labels: ['A', 'B'],
    datasets: [{ label: 'Trend', data: [15, 25] }]
  }
});

const pieChart = new Chart(ctx3, {
  type: 'pie',
  data: {
    labels: ['X', 'Y'],
    datasets: [{ data: [30, 70] }]
  }
});
'''
        result = parser.parse(code, "dashboard.js")
        assert len(result.instances) >= 3

    def test_typescript_chartjs_file(self):
        parser = EnhancedChartJSParser()
        code = '''
import {
  Chart,
  ChartConfiguration,
  ChartData,
  ChartOptions,
  BarController,
  BarElement,
  CategoryScale,
  LinearScale
} from 'chart.js';

Chart.register(BarController, BarElement, CategoryScale, LinearScale);

const data: ChartData<'bar'> = {
  labels: ['Jan', 'Feb'],
  datasets: [{
    label: 'Revenue',
    data: [100, 200]
  }]
};

const options: ChartOptions<'bar'> = {
  responsive: true,
  scales: {
    y: { beginAtZero: true }
  }
};

const config: ChartConfiguration<'bar'> = {
  type: 'bar',
  data,
  options
};
'''
        result = parser.parse(code, "chart.ts")
        assert isinstance(result, ChartJSParseResult)
        assert result.file_type == "ts"
        assert 'chart.js' in result.detected_frameworks
        assert result.has_typescript is True
        assert len(result.types) >= 1

    def test_cdn_html_file(self):
        parser = EnhancedChartJSParser()
        code = '''
<!DOCTYPE html>
<html>
<head>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
  <canvas id="myChart"></canvas>
  <script>
    const ctx = document.getElementById('myChart').getContext('2d');
    const chart = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: ['Red', 'Blue'],
        datasets: [{
          label: 'Votes',
          data: [12, 19]
        }]
      }
    });
  </script>
</body>
</html>
'''
        result = parser.parse(code, "index.html")
        assert result.file_type == "html"
        assert len(result.instances) >= 1
        assert len(result.imports) >= 1

    def test_v2_legacy_code(self):
        parser = EnhancedChartJSParser()
        code = '''
var ctx = document.getElementById('myChart').getContext('2d');
var myChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['A', 'B', 'C'],
    datasets: [{
      label: 'Values',
      data: [12, 19, 3]
    }]
  },
  options: {
    scales: {
      xAxes: [{
        display: true
      }],
      yAxes: [{
        ticks: { beginAtZero: true }
      }]
    }
  }
});
Chart.defaults.global.defaultFontFamily = 'Arial';
'''
        result = parser.parse(code, "chart-v2.js")
        assert isinstance(result, ChartJSParseResult)
        assert len(result.instances) >= 1
        assert len(result.defaults) >= 1

    def test_stacked_chart(self):
        parser = EnhancedChartJSParser()
        code = '''
import Chart from 'chart.js/auto';

const chart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Q1', 'Q2', 'Q3'],
    datasets: [
      { label: 'Product A', data: [10, 20, 30] },
      { label: 'Product B', data: [20, 30, 10] }
    ]
  },
  options: {
    scales: {
      x: { stacked: true },
      y: { stacked: true }
    }
  }
});
'''
        result = parser.parse(code, "stacked-chart.js")
        has_stacked = any(s.has_stacked for s in result.scales)
        assert has_stacked is True

    def test_dual_axis_chart(self):
        parser = EnhancedChartJSParser()
        code = '''
import Chart from 'chart.js/auto';

const chart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: ['Jan', 'Feb', 'Mar'],
    datasets: [
      {
        label: 'Revenue ($)',
        data: [1200, 1900, 3000],
        yAxisID: 'y',
        borderColor: '#3b82f6'
      },
      {
        label: 'Customers',
        data: [50, 80, 120],
        yAxisID: 'y1',
        borderColor: '#ef4444'
      }
    ]
  },
  options: {
    scales: {
      y: { type: 'linear', position: 'left' },
      y1: { type: 'linear', position: 'right' }
    }
  }
});
'''
        result = parser.parse(code, "dual-axis.js")
        assert len(result.scales) >= 2

    def test_custom_plugin_with_hooks(self):
        parser = EnhancedChartJSParser()
        code = '''
import Chart from 'chart.js/auto';

const chart = new Chart(ctx, {
  type: 'line',
  data: { labels: ['A'], datasets: [{ data: [1] }] },
  plugins: [{
    id: 'customBackground',
    beforeDraw: (chart) => {
      const { ctx, chartArea: { left, top, width, height } } = chart;
      ctx.save();
      ctx.fillStyle = '#f8fafc';
      ctx.fillRect(left, top, width, height);
      ctx.restore();
    },
    afterDraw: (chart) => {
      // additional drawing
    }
  }]
});
'''
        result = parser.parse(code, "custom-plugin.js")
        custom_plugins = [p for p in result.plugins if p.plugin_type == 'custom']
        assert len(custom_plugins) >= 1

    def test_chartjs_with_animation_disabled(self):
        parser = EnhancedChartJSParser()
        code = '''
import Chart from 'chart.js/auto';

const chart = new Chart(ctx, {
  type: 'bar',
  data: { labels: ['A'], datasets: [{ data: [1] }] },
  options: {
    animation: false
  }
});
'''
        result = parser.parse(code, "no-animation.js")
        assert isinstance(result, ChartJSParseResult)

    def test_large_dataset_config(self):
        parser = EnhancedChartJSParser()
        code = '''
import Chart from 'chart.js/auto';

const chart = new Chart(ctx, {
  type: 'line',
  data: {
    datasets: [{
      label: 'Big Data',
      data: largeArray,
      pointRadius: 0,
      pointHitRadius: 10
    }]
  },
  options: {
    parsing: false,
    animation: false,
    plugins: {
      decimation: {
        enabled: true,
        algorithm: 'lttb',
        samples: 500
      }
    }
  }
});
'''
        result = parser.parse(code, "large-data.js")
        assert len(result.instances) >= 1
        decimation_plugins = [p for p in result.plugins if p.plugin_id == 'decimation']
        assert len(decimation_plugins) >= 1

    def test_scatter_with_xy_data(self):
        parser = EnhancedChartJSParser()
        code = '''
import Chart from 'chart.js/auto';

const chart = new Chart(ctx, {
  type: 'scatter',
  data: {
    datasets: [{
      label: 'Scatter Data',
      data: [
        { x: 10, y: 20 },
        { x: 15, y: 30 },
        { x: 20, y: 10 }
      ]
    }]
  },
  options: {
    scales: {
      x: { type: 'linear' },
      y: { type: 'linear' }
    }
  }
});
'''
        result = parser.parse(code, "scatter.js")
        assert len(result.instances) >= 1
        assert result.instances[0].chart_type == 'scatter'

    def test_bubble_chart_with_xyr_data(self):
        parser = EnhancedChartJSParser()
        code = '''
import Chart from 'chart.js/auto';

const chart = new Chart(ctx, {
  type: 'bubble',
  data: {
    datasets: [{
      label: 'Bubble Data',
      data: [
        { x: 10, y: 20, r: 5 },
        { x: 15, y: 10, r: 10 }
      ]
    }]
  }
});
'''
        result = parser.parse(code, "bubble.js")
        assert len(result.instances) >= 1
        assert result.instances[0].chart_type == 'bubble'
