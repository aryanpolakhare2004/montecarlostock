<script setup lang="ts">
import { nextTick, ref, watch } from 'vue';
import { api } from '../api';

interface Entry {
  command: string | null;
  output: string;
}

const WELCOME: Entry = {
  command: null,
  output:
    "mcstock terminal -- type 'help' for commands.\n" +
    'Try: analyst MSFT   |   compare MU,WDC,STX   |   price AAPL --days 60',
};

const entries = ref<Entry[]>([WELCOME]);
const input = ref('');
const history = ref<string[]>([]);
const historyIndex = ref<number | null>(null);
const busy = ref(false);
const inputRef = ref<HTMLInputElement | null>(null);
const bottomRef = ref<HTMLDivElement | null>(null);

watch(entries, async () => {
  await nextTick();
  bottomRef.value?.scrollIntoView({ block: 'end' });
}, { deep: true });

async function runCommand(command: string) {
  const trimmed = command.trim();
  if (!trimmed) return;

  if (trimmed.toLowerCase() === 'clear') {
    entries.value = [];
    input.value = '';
    history.value = [...history.value, trimmed];
    historyIndex.value = null;
    return;
  }

  history.value = [...history.value, trimmed];
  historyIndex.value = null;
  input.value = '';
  busy.value = true;
  try {
    const response = await api.terminal({ command: trimmed });
    entries.value = [...entries.value, { command: trimmed, output: response.output }];
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    entries.value = [...entries.value, { command: trimmed, output: `error: ${message}` }];
  } finally {
    busy.value = false;
  }
}

function onKeyDown(evt: KeyboardEvent) {
  if (evt.key === 'Enter') {
    runCommand(input.value);
  } else if (evt.key === 'ArrowUp') {
    evt.preventDefault();
    if (history.value.length === 0) return;
    const nextIndex = historyIndex.value === null ? history.value.length - 1 : Math.max(0, historyIndex.value - 1);
    historyIndex.value = nextIndex;
    input.value = history.value[nextIndex];
  } else if (evt.key === 'ArrowDown') {
    evt.preventDefault();
    if (historyIndex.value === null) return;
    const nextIndex = historyIndex.value + 1;
    if (nextIndex >= history.value.length) {
      historyIndex.value = null;
      input.value = '';
    } else {
      historyIndex.value = nextIndex;
      input.value = history.value[nextIndex];
    }
  }
}
</script>

<template>
  <section class="terminal-page" @click="inputRef?.focus()">
    <h2>Terminal</h2>
    <p class="hint">
      A text-only console over the same backend as the other tabs -- <code>help</code> lists every command.
      Output is plain text/ASCII, so it stays scriptable and fast to scan.
    </p>
    <div class="terminal">
      <div class="terminal-entry" v-for="(entry, i) in entries" :key="i">
        <div v-if="entry.command !== null" class="terminal-prompt-line">mcstock&gt; {{ entry.command }}</div>
        <pre class="terminal-output">{{ entry.output }}</pre>
      </div>
      <div v-if="busy" class="terminal-output terminal-busy">running…</div>
      <div class="terminal-input-line">
        <span class="terminal-prompt">mcstock&gt;</span>
        <input
          ref="inputRef"
          class="terminal-input"
          v-model="input"
          @keydown="onKeyDown"
          autofocus
          spellcheck="false"
          autocomplete="off"
        />
      </div>
      <div ref="bottomRef" />
    </div>
  </section>
</template>
