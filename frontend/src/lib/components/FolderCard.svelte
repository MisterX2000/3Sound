<script lang="ts">
  import type { FolderInfo } from '../../types';
  import { Folder, ChevronRight } from '@lucide/svelte';

  interface Props {
    folder: FolderInfo;
    searchQuery: string;
    onOpenFolder: (path: string) => void;
  }

  const { folder, searchQuery, onOpenFolder }: Props = $props();

  function handleClick() {
    onOpenFolder(folder.path);
  }

  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleClick();
    }
  }

  const folderCount = $derived(folder.subfolders ? folder.subfolders.length : 0);
  const soundCount = $derived(folder.total_sound_count || 0);
  const subtitle = $derived(
    [
      folderCount > 0 ? `${folderCount} folder${folderCount === 1 ? '' : 's'}` : null,
      `${soundCount} sound${soundCount === 1 ? '' : 's'}`
    ].filter(Boolean).join(' • ')
  );
</script>

<div
  role="button"
  tabindex="0"
  onclick={handleClick}
  onkeydown={handleKeyDown}
  class="group relative flex flex-col text-left rounded-2xl bg-slate-900 border border-slate-800/90 hover:border-indigo-500/50 shadow-md hover:shadow-xl hover:shadow-indigo-500/10 transition-all duration-200 transform hover:-translate-y-0.5 active:translate-y-0 overflow-hidden cursor-pointer select-none focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/50"
>
  <!-- Artwork Container -->
  <div class="relative w-full aspect-[4/3] bg-slate-950 overflow-hidden flex items-center justify-center">
    {#if folder.image_url}
      <img
        src={folder.image_url}
        alt={folder.name}
        loading="lazy"
        decoding="async"
        class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
      />
    {:else}
      <div class="w-full h-full flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 via-indigo-950/20 to-slate-950 text-indigo-400 group-hover:text-indigo-300 group-hover:from-slate-900 group-hover:to-indigo-950/40 transition-all">
        <Folder class="w-12 h-12 transform group-hover:scale-110 transition-transform" />
      </div>
    {/if}

    <!-- Gradient Overlay -->
    <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/40 to-transparent pointer-events-none"></div>

    <!-- Folder Badge (Top Left) -->
    <div class="absolute top-2 left-2 px-1.5 py-0.5 rounded bg-slate-950/80 backdrop-blur-md border border-slate-700/60 text-[10px] font-medium text-indigo-300 flex items-center gap-1 z-10 pointer-events-none">
      <Folder class="w-3 h-3 text-indigo-400" />
      <span>Folder</span>
    </div>

    <!-- Total Count Badge (Top Right) -->
    <div class="absolute top-2 right-2 px-1.5 py-0.5 rounded bg-slate-950/80 backdrop-blur-md border border-slate-700/60 text-[10px] font-mono text-slate-200 z-10 pointer-events-none">
      {soundCount}
    </div>

    <!-- Hover Overlay -->
    <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/30 backdrop-blur-[1px] pointer-events-none">
      <div class="w-9 h-9 rounded-full bg-indigo-600 text-white flex items-center justify-center shadow-lg shadow-indigo-600/50 transform scale-90 group-hover:scale-100 transition-transform">
        <ChevronRight class="w-4 h-4" />
      </div>
    </div>
  </div>

  <!-- Info Body -->
  <div class="p-3 w-full flex-1 flex flex-col justify-between">
    <div>
      <h4 title={searchQuery ? (folder.path || folder.name) : folder.name} class="font-semibold text-sm text-slate-100 group-hover:text-indigo-300 transition-colors line-clamp-1">
        {searchQuery ? (folder.path || folder.name) : folder.name}
      </h4>
      <p class="text-[11px] text-slate-400 truncate mt-0.5">
        {subtitle}
      </p>
    </div>
  </div>
</div>
