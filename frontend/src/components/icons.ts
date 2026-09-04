import { defineComponent, h, type VNode } from 'vue';

const base = {
  fill: 'none',
  stroke: 'currentColor',
  'stroke-width': 1.6,
  'stroke-linecap': 'round' as const,
  'stroke-linejoin': 'round' as const,
};

function icon(name: string, children: () => VNode[]) {
  return defineComponent({
    name,
    props: { size: { type: Number, default: 18 } },
    setup(props) {
      return () => h('svg', { width: props.size, height: props.size, viewBox: '0 0 24 24', ...base }, children());
    },
  });
}

export const HomeIcon = icon('HomeIcon', () => [
  h('path', { d: 'M3 11l9-7 9 7' }),
  h('path', { d: 'M5 10v9a1 1 0 0 0 1 1h4v-6h4v6h4a1 1 0 0 0 1-1v-9' }),
]);

export const LineChartIcon = icon('LineChartIcon', () => [
  h('path', { d: 'M3 3v18h18' }),
  h('path', { d: 'M7 15l4-4 3 3 5-6' }),
]);

export const BarChartIcon = icon('BarChartIcon', () => [
  h('path', { d: 'M3 3v18h18' }),
  h('rect', { x: 7, y: 12, width: 3, height: 6 }),
  h('rect', { x: 12, y: 8, width: 3, height: 10 }),
  h('rect', { x: 17, y: 5, width: 3, height: 13 }),
]);

export const TargetIcon = icon('TargetIcon', () => [
  h('circle', { cx: 12, cy: 12, r: 8 }),
  h('circle', { cx: 12, cy: 12, r: 4 }),
  h('circle', { cx: 12, cy: 12, r: 0.8, fill: 'currentColor' }),
]);

export const ScaleIcon = icon('ScaleIcon', () => [
  h('path', { d: 'M12 3v17' }),
  h('path', { d: 'M5 7h14' }),
  h('path', { d: 'M5 7l-3 6a3 3 0 0 0 6 0z' }),
  h('path', { d: 'M19 7l-3 6a3 3 0 0 0 6 0z' }),
]);

export const BriefcaseIcon = icon('BriefcaseIcon', () => [
  h('rect', { x: 3, y: 7, width: 18, height: 13, rx: 2 }),
  h('path', { d: 'M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2' }),
  h('path', { d: 'M3 13h18' }),
]);

export const SlidersIcon = icon('SlidersIcon', () => [
  h('line', { x1: 4, y1: 6, x2: 20, y2: 6 }),
  h('circle', { cx: 9, cy: 6, r: 2, fill: 'var(--bg)' }),
  h('line', { x1: 4, y1: 12, x2: 20, y2: 12 }),
  h('circle', { cx: 15, cy: 12, r: 2, fill: 'var(--bg)' }),
  h('line', { x1: 4, y1: 18, x2: 20, y2: 18 }),
  h('circle', { cx: 7, cy: 18, r: 2, fill: 'var(--bg)' }),
]);

export const ArrowUpRightIcon = icon('ArrowUpRightIcon', () => [
  h('path', { d: 'M7 17L17 7' }),
  h('path', { d: 'M8 7h9v9' }),
]);

export const ActivityIcon = icon('ActivityIcon', () => [
  h('polyline', { points: '3,12 8,12 10,18 14,6 16,12 21,12' }),
]);

export const SearchIcon = icon('SearchIcon', () => [
  h('circle', { cx: 10, cy: 10, r: 6.5 }),
  h('line', { x1: 15, y1: 15, x2: 20.5, y2: 20.5 }),
]);

export const LayersIcon = icon('LayersIcon', () => [
  h('polygon', { points: '12,3 21,8 12,13 3,8' }),
  h('polyline', { points: '3,13 12,18 21,13' }),
  h('polyline', { points: '3,18 12,23 21,18' }),
]);

export const EyeIcon = icon('EyeIcon', () => [
  h('path', { d: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z' }),
  h('circle', { cx: 12, cy: 12, r: 3 }),
]);

export const TerminalIcon = icon('TerminalIcon', () => [
  h('rect', { x: 3, y: 4, width: 18, height: 16, rx: 2 }),
  h('path', { d: 'M7 9l3 3-3 3' }),
  h('line', { x1: 12, y1: 15, x2: 17, y2: 15 }),
]);

export const DownloadIcon = icon('DownloadIcon', () => [
  h('path', { d: 'M12 3v12' }),
  h('path', { d: 'M7 10l5 5 5-5' }),
  h('path', { d: 'M4 19h16' }),
]);

export const SunIcon = icon('SunIcon', () => [
  h('circle', { cx: 12, cy: 12, r: 4.5 }),
  h('path', { d: 'M12 2.5v2.5M12 19v2.5M4.5 12H2M22 12h-2.5M5.6 5.6l1.8 1.8M16.6 16.6l1.8 1.8M5.6 18.4l1.8-1.8M16.6 7.4l1.8-1.8' }),
]);

export const MoonIcon = icon('MoonIcon', () => [
  h('path', { d: 'M20 14.5A8.5 8.5 0 1 1 9.5 4a6.8 6.8 0 0 0 10.5 10.5z' }),
]);

export const MonitorIcon = icon('MonitorIcon', () => [
  h('rect', { x: 3, y: 4, width: 18, height: 12, rx: 1.5 }),
  h('path', { d: 'M8 20h8M12 16v4' }),
]);

export const ClockIcon = icon('ClockIcon', () => [
  h('circle', { cx: 12, cy: 12, r: 9 }),
  h('path', { d: 'M12 7v5l3 3' }),
]);
