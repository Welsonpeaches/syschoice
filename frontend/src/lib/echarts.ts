/**
 * Only register the chart types and components this app actually renders,
 * which keeps the bundle far smaller than the default `echarts` entry.
 */
import { LineChart, RadarChart } from 'echarts/charts'
import { GridComponent, TooltipComponent } from 'echarts/components'
import * as echarts from 'echarts/core'
import { SVGRenderer } from 'echarts/renderers'

echarts.use([LineChart, RadarChart, GridComponent, TooltipComponent, SVGRenderer])

export { echarts }
export type { ECharts, EChartsCoreOption } from 'echarts/core'
