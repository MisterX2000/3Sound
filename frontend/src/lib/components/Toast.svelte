<script lang="ts">
  import { Check } from '@lucide/svelte';

  interface Props {
    message: string | null;
  }

  const { message }: Props = $props();
</script>

{#if message}
  <div
    class="fixed bottom-5 right-5 z-50 flex items-center gap-2.5 px-4 py-2.5 rounded-xl bg-slate-900 border border-slate-700 shadow-2xl text-xs text-slate-200 pointer-events-none transition-all duration-300 animate-in fade-in slide-in-from-bottom-5"
  >
    <Check class="w-4 h-4 text-emerald-400 shrink-0" />
    <span>{message}</span>
  </div>
{/if}
