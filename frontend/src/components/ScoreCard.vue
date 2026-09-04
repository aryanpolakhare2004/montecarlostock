<script setup lang="ts">
import { computed } from 'vue';
import TrendLineChart from './charts/TrendLineChart.vue';
import type { FundamentalsTrendRow } from './charts/TrendLineChart.vue';
import { fmtMoney, fmtPct, fmtScore } from '../format';
import type { FundamentalsReport } from '../types';

const props = defineProps<{ report: FundamentalsReport }>();

const s = computed(() => props.report.scores);
const t = computed(() => props.report.trends);
const fv = computed(() => props.report.fair_value);
const riskClass = computed(() => `score-value risk-${(s.value.risk_label || 'unknown').toLowerCase()}`);
const trendData = computed(() => props.report.metrics_history as unknown as FundamentalsTrendRow[]);
</script>

<template>
  <div class="scorecard">
    <h3>{{ report.company_name }} ({{ report.ticker }})</h3>
    <div class="score-grid">
      <div class="score-tile">
        <div class="score-label">Business quality</div>
        <div class="score-value">{{ fmtScore(s.business_quality) }}</div>
      </div>
      <div class="score-tile">
        <div class="score-label">Financial strength</div>
        <div class="score-value">{{ fmtScore(s.financial_strength) }}</div>
      </div>
      <div class="score-tile">
        <div class="score-label">Growth</div>
        <div class="score-value">{{ fmtScore(s.growth) }}</div>
      </div>
      <div class="score-tile">
        <div class="score-label">Valuation</div>
        <div class="score-value">{{ fmtScore(s.valuation) }}</div>
      </div>
      <div class="score-tile">
        <div class="score-label">Risk</div>
        <div :class="riskClass">{{ s.risk_label || 'n/a' }}</div>
      </div>
    </div>

    <div class="trend-row">
      <span>Revenue trend: <strong>{{ t.revenue_trend }}</strong></span>
      <span>Free cash flow: <strong>{{ t.fcf_status }}</strong></span>
      <span>Debt position: <strong>{{ t.debt_position }}</strong></span>
      <span>Share dilution: <strong>{{ t.share_dilution }}</strong></span>
    </div>

    <TrendLineChart v-if="report.metrics_history.length > 0" :data="trendData" />

    <details>
      <summary>Business quality evidence</summary>
      <ul v-if="report.evidence.business_quality?.length" class="evidence">
        <li v-for="(item, i) in report.evidence.business_quality" :key="i">{{ item }}</li>
      </ul>
      <p v-else class="hint">No evidence available.</p>
    </details>
    <details>
      <summary>Growth evidence</summary>
      <ul v-if="report.evidence.growth?.length" class="evidence">
        <li v-for="(item, i) in report.evidence.growth" :key="i">{{ item }}</li>
      </ul>
      <p v-else class="hint">No evidence available.</p>
    </details>
    <details>
      <summary>Financial strength evidence</summary>
      <ul v-if="report.evidence.financial_strength?.length" class="evidence">
        <li v-for="(item, i) in report.evidence.financial_strength" :key="i">{{ item }}</li>
      </ul>
      <p v-else class="hint">No evidence available.</p>
    </details>
    <details>
      <summary>Valuation evidence</summary>
      <ul v-if="report.evidence.valuation?.length" class="evidence">
        <li v-for="(item, i) in report.evidence.valuation" :key="i">{{ item }}</li>
      </ul>
      <p v-else class="hint">No evidence available.</p>
    </details>
    <details>
      <summary>Risk evidence</summary>
      <ul v-if="report.evidence.risk?.length" class="evidence">
        <li v-for="(item, i) in report.evidence.risk" :key="i">{{ item }}</li>
      </ul>
      <p v-else class="hint">No evidence available.</p>
    </details>

    <div class="case-box bull">
      <strong>Bull case:</strong> {{ report.bull_case }}
    </div>
    <div class="case-box bear">
      <strong>Bear case:</strong> {{ report.bear_case }}
    </div>
    <div class="case-box flags">
      <strong>Major red flags:</strong>
      <ul>
        <li v-for="(flag, i) in report.red_flags" :key="i">{{ flag }}</li>
      </ul>
    </div>

    <p>
      <strong>Estimated fair-value range:</strong>
      <template v-if="fv.low != null && fv.high != null">
        {{ fmtMoney(fv.low) }} &ndash; {{ fmtMoney(fv.high) }} (current price {{ fmtMoney(fv.current_price) }}, upside
        {{ fmtPct(fv.upside_low_pct) }} to {{ fmtPct(fv.upside_high_pct) }})
      </template>
      <template v-else>n/a (insufficient data)</template>
    </p>
    <p>
      <strong>Confidence:</strong> {{ report.confidence }}%
      <span class="hint">&mdash; narrative source: {{ report.narrative_source }}</span>
    </p>
  </div>
</template>
