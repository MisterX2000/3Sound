<script lang="ts">
  import type { ViewMode } from '../../types';
  import { SearchX, Home } from '@lucide/svelte';

  interface Props {
    searchQuery: string;
    viewMode: ViewMode;
    currentFolder?: string;
    onClearSearch: () => void;
    onReturnHome?: () => void;
  }

  const { searchQuery, viewMode, currentFolder, onClearSearch, onReturnHome }: Props = $props();
</script>

<div class="py-20 text-center text-slate-400">
  <div class="h-12 w-12 mx-auto rounded-xl bg-slate-900 border border-slate-800 flex items-center justify-center text-slate-500 mb-3 shadow-inner">
    <SearchX class="w-6 h-6 text-slate-400" />
  </div>
  <p class="text-base font-semibold">
    No sounds{viewMode === 'folder' ? ' or folders' : ''} found matching "{searchQuery}"
  </p>
  <div class="mt-4 flex items-center justify-center gap-2">
    <button
      type="button"
      onclick={onClearSearch}
      class="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-indigo-500/50 text-xs font-medium text-indigo-400 hover:text-indigo-300 transition-colors shadow-sm cursor-pointer"
    >
      Clear search query
    </button>
    {#if viewMode === 'folder' && currentFolder}
      <button
        type="button"
        onclick={onReturnHome}
        class="px-3.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs text-slate-400 hover:text-slate-200 transition-colors flex items-center gap-1.5 shadow-sm cursor-pointer"
      >
        <Home class="w-3.5 h-3.5" />
        <span>Return to Home</span>
      </button>
    {/if}
  </div>
</div>
