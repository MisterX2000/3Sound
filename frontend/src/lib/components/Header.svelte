<script lang="ts">
  import type { BreadcrumbItem, ViewMode } from '../../types';
  import { audio } from '../audio.svelte';
  import {
    Search,
    X,
    Volume2,
    VolumeX,
    Square,
    RotateCw,
    Folder,
    LayoutGrid,
    Home,
    ChevronRight
  } from '@lucide/svelte';

  interface Props {
    appTitle: string;
    viewMode: ViewMode;
    searchQuery: string;
    categories: string[];
    activeCategory: string;
    isRescanning: boolean;
    totalSoundCount: number;
    categoryCounts: Record<string, number>;
    currentFolder: string;
    breadcrumbs: BreadcrumbItem[];
    onSelectCategory: (cat: string) => void;
    onToggleView: (mode: ViewMode) => void;
    onSearchChange: (q: string) => void;
    onClearSearch: () => void;
    onRescan: () => void;
    onOpenFolder: (path: string) => void;
  }

  let {
    appTitle,
    viewMode,
    searchQuery,
    categories,
    activeCategory,
    isRescanning,
    totalSoundCount,
    categoryCounts,
    currentFolder,
    breadcrumbs,
    onSelectCategory,
    onToggleView,
    onSearchChange,
    onClearSearch,
    onRescan,
    onOpenFolder,
  }: Props = $props();

  let searchInputEl = $state<HTMLInputElement | null>(null);

  export function focusSearch() {
    searchInputEl?.focus();
    searchInputEl?.select();
  }

  const volumePercent = $derived(
    audio.isMuted ? '0%' : `${Math.round(audio.masterVolume * 100)}%`
  );
</script>

<header class="sticky top-0 z-40 bg-slate-950/85 backdrop-blur-xl border-b border-slate-800/80 px-3 sm:px-6 py-2.5 sm:py-3">
  <div class="max-w-7xl mx-auto flex flex-col gap-2 sm:gap-2.5">
    
    <!-- Top Row: Logo/Title, Flexible Search Bar, Controls -->
    <!-- Desktop (lg+): Unified 1-row layout (Brand | Search | Controls) with no height jumps -->
    <!-- Mobile & Tablet (<lg): Clean 2-row layout: Row 1 = Brand + Actions; Row 2 = Search + ViewMode -->
    <div class="flex flex-wrap lg:flex-nowrap items-center justify-between gap-2 md:gap-3">
      
      <!-- Brand Section (Left on Desktop, Left on Mobile/Tablet Row 1) -->
      <div class="flex items-center gap-2 sm:gap-2.5 shrink-0 order-1">
        <div class="h-9 w-9 sm:h-10 sm:w-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/20 text-white shrink-0">
          <Volume2 class="w-4 h-4 sm:w-5 sm:h-5 text-white" />
        </div>
        <h1 class="text-base sm:text-lg font-bold tracking-tight text-white flex items-center gap-1.5 sm:gap-2 whitespace-nowrap shrink-0">
          <span>{appTitle}</span>
          <span class="hidden sm:inline-flex text-[11px] sm:text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-800 text-indigo-300 border border-slate-700 whitespace-nowrap shrink-0">
            {totalSoundCount} Sounds
          </span>
        </h1>
      </div>

      <!-- Action Controls (Right on Mobile/Tablet Row 1, Right on Desktop Toolbar) -->
      <div class="flex items-center gap-1.5 sm:gap-2 order-2 lg:order-3 shrink-0">
        
        <!-- View Mode Switch: Desktop only (Mobile/Tablet View Mode sits in Row 2 next to Search) -->
        <div class="hidden lg:flex items-center bg-slate-900 border border-slate-800 rounded-xl p-0.5 sm:p-1 text-xs shadow-inner shrink-0">
          <button
            type="button"
            onclick={() => onToggleView('flat')}
            title="Flat View (All categories)"
            class="flex items-center gap-1.5 px-2 sm:px-2.5 py-1 rounded-lg transition font-medium cursor-pointer"
            class:bg-indigo-600={viewMode === 'flat'}
            class:text-white={viewMode === 'flat'}
            class:shadow-sm={viewMode === 'flat'}
            class:text-slate-400={viewMode !== 'flat'}
            class:hover:text-slate-200={viewMode !== 'flat'}
          >
            <LayoutGrid class="w-3.5 h-3.5" />
            <span>Flat</span>
          </button>
          <button
            type="button"
            onclick={() => onToggleView('folder')}
            title="Folder View (Browse directory hierarchy)"
            class="flex items-center gap-1.5 px-2 sm:px-2.5 py-1 rounded-lg transition font-medium cursor-pointer"
            class:bg-indigo-600={viewMode === 'folder'}
            class:text-white={viewMode === 'folder'}
            class:shadow-sm={viewMode === 'folder'}
            class:text-slate-400={viewMode !== 'folder'}
            class:hover:text-slate-200={viewMode !== 'folder'}
          >
            <Folder class="w-3.5 h-3.5" />
            <span>Folders</span>
          </button>
        </div>

        <!-- Master Volume Control with Percentage Display -->
        <div class="flex items-center gap-1 sm:gap-1.5 bg-slate-900 border border-slate-800 px-2 sm:px-2.5 py-1 rounded-xl shadow-inner shrink-0">
          <button
            type="button"
            onclick={() => audio.toggleMute()}
            title={audio.isMuted ? 'Unmute master audio' : 'Mute master audio'}
            class="text-slate-400 hover:text-slate-200 transition cursor-pointer p-0.5"
          >
            {#if audio.isMuted || audio.masterVolume === 0}
              <VolumeX class="w-4 h-4 text-rose-400" />
            {:else}
              <Volume2 class="w-4 h-4 text-indigo-400" />
            {/if}
          </button>
          <input
            id="master-volume"
            name="volume"
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={audio.masterVolume}
            oninput={(e) => audio.setVolume(parseFloat((e.target as HTMLInputElement).value))}
            class="w-12 sm:w-16 md:w-16 lg:w-20 accent-indigo-500 cursor-pointer h-1.5 bg-slate-800 rounded-lg appearance-none"
            title="Master volume ({volumePercent})"
            aria-label="Master volume control"
          />
          <span class="hidden sm:inline text-[10px] sm:text-[11px] text-slate-400 font-mono w-6 sm:w-7 text-right select-none">{volumePercent}</span>
        </div>

        <!-- Stop All Button (Always rendered, zero DOM width shifts) -->
        <button
          type="button"
          onclick={() => audio.stopAll()}
          disabled={audio.playingIds.length === 0}
          title={audio.playingIds.length > 0 ? "Stop all currently playing sounds (Esc)" : "No sounds currently playing"}
          aria-label="Stop all currently playing sounds"
          class="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-1 sm:py-1.5 rounded-xl border transition text-xs font-medium shadow-sm whitespace-nowrap shrink-0 {audio.playingIds.length > 0 ? 'bg-rose-500/20 text-rose-400 border-rose-500/30 hover:bg-rose-500/30 cursor-pointer' : 'bg-slate-900/50 text-slate-500 border-slate-800/60 opacity-40 cursor-not-allowed'}"
        >
          <Square class="w-3.5 h-3.5 {audio.playingIds.length > 0 ? 'fill-current' : 'opacity-60'}" />
          <span class="hidden sm:inline">Stop All</span>
        </button>

        <!-- Rescan Button -->
        <button
          type="button"
          onclick={onRescan}
          disabled={isRescanning}
          title="Rescan sounds directory from filesystem"
          class="p-1.5 sm:p-2 rounded-xl bg-slate-900 border border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700 transition cursor-pointer shadow-sm disabled:opacity-50 shrink-0"
        >
          <RotateCw class="h-3.5 w-3.5 sm:h-4 sm:w-4 {isRescanning ? 'animate-spin text-indigo-400' : ''}" />
        </button>

      </div>

      <!-- Search Section & ViewMode -->
      <!-- On mobile/tablet (<lg): forms Row 2 (flex-1 Search + View Mode switch) -->
      <!-- On desktop (lg+): forms Center column between Brand and Controls (lg:order-2 lg:flex-1 lg:max-w-md) -->
      <div class="basis-full lg:basis-auto flex-1 lg:order-2 flex items-center gap-2 min-w-0 lg:max-w-md lg:mx-4 order-3">
        <div class="relative flex-1 min-w-0">
          <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
            <Search class="h-4 w-4" />
          </div>
          <input
            bind:this={searchInputEl}
            id="soundboard-search"
            name="q"
            type="search"
            placeholder="Search sounds or categories... (Press / to focus)"
            value={searchQuery}
            oninput={(e) => onSearchChange((e.target as HTMLInputElement).value)}
            class="w-full pl-9 pr-8 py-1.5 sm:py-2 rounded-xl bg-slate-900 border border-slate-800 text-xs sm:text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition"
            aria-label="Search sounds or categories"
          />
          {#if searchQuery}
            <button
              type="button"
              onclick={onClearSearch}
              class="absolute inset-y-0 right-0 pr-2.5 flex items-center text-slate-500 hover:text-slate-300 cursor-pointer"
              title="Clear search"
            >
              <X class="h-3.5 w-3.5" />
            </button>
          {/if}
        </div>

        <!-- Mobile/Tablet View Mode Switch (sits next to search bar on Row 2 for <lg) -->
        <div class="flex lg:hidden items-center bg-slate-900 border border-slate-800 rounded-xl p-0.5 text-xs shadow-inner shrink-0">
          <button
            type="button"
            onclick={() => onToggleView('flat')}
            title="Flat View (All categories)"
            class="flex items-center gap-1 px-2 py-1.5 rounded-lg transition font-medium cursor-pointer"
            class:bg-indigo-600={viewMode === 'flat'}
            class:text-white={viewMode === 'flat'}
            class:shadow-sm={viewMode === 'flat'}
            class:text-slate-400={viewMode !== 'flat'}
            class:hover:text-slate-200={viewMode !== 'flat'}
          >
            <LayoutGrid class="w-3.5 h-3.5" />
            <span class="text-[11px]">Flat</span>
          </button>
          <button
            type="button"
            onclick={() => onToggleView('folder')}
            title="Folder View (Browse directory hierarchy)"
            class="flex items-center gap-1 px-2 py-1.5 rounded-lg transition font-medium cursor-pointer"
            class:bg-indigo-600={viewMode === 'folder'}
            class:text-white={viewMode === 'folder'}
            class:shadow-sm={viewMode === 'folder'}
            class:text-slate-400={viewMode !== 'folder'}
            class:hover:text-slate-200={viewMode !== 'folder'}
          >
            <Folder class="w-3.5 h-3.5" />
            <span class="text-[11px]">Folders</span>
          </button>
        </div>
      </div>

    </div>

    <!-- Row 2: Navigation / Filter Subheader Bar -->
    <div class="pt-2 border-t border-slate-800/60 flex items-center justify-between gap-3 overflow-hidden min-h-[40px]">
      
      <!-- Flat View: Category Pills Carousel -->
      {#if viewMode === 'flat'}
        <div class="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none text-xs flex-1">
          <div class="flex items-center gap-1.5">
            {#each categories as cat (cat)}
              {@const count = categoryCounts[cat] || 0}
              <button
                type="button"
                onclick={() => onSelectCategory(cat)}
                class="px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition flex items-center gap-1.5 cursor-pointer"
                class:bg-indigo-600={activeCategory === cat}
                class:text-white={activeCategory === cat}
                class:shadow-md={activeCategory === cat}
                class:shadow-indigo-600={activeCategory === cat}
                class:bg-slate-900={activeCategory !== cat}
                class:text-slate-300={activeCategory !== cat}
                class:hover:bg-slate-800={activeCategory !== cat}
                class:hover:text-white={activeCategory !== cat}
                class:border={activeCategory !== cat}
                class:border-slate-800={activeCategory !== cat}
              >
                <span>{cat}</span>
                <span
                  class="text-[10px] px-1.5 py-0.2 rounded-full"
                  class:bg-indigo-700={activeCategory === cat}
                  class:text-indigo-100={activeCategory === cat}
                  class:bg-slate-800={activeCategory !== cat}
                  class:text-slate-400={activeCategory !== cat}
                >
                  {count}
                </span>
              </button>
            {/each}
          </div>
        </div>
      {:else}
        <!-- Folder View: Interactive Breadcrumbs Bar (Starts with Home, zero layout shift) -->
        <div class="flex items-center gap-1.5 text-xs text-slate-400 overflow-x-auto pb-1 scrollbar-none flex-1">
          <!-- Home Breadcrumb -->
          <button
            type="button"
            onclick={() => onOpenFolder('')}
            class="flex items-center gap-1.5 px-2.5 py-1 rounded-lg transition shrink-0 cursor-pointer"
            class:text-white={currentFolder === ''}
            class:font-semibold={currentFolder === ''}
            class:bg-slate-900={currentFolder === ''}
            class:border={currentFolder === ''}
            class:border-slate-700={currentFolder === ''}
            class:shadow-sm={currentFolder === ''}
            class:text-slate-400={currentFolder !== ''}
            class:hover:text-slate-200={currentFolder !== ''}
          >
            <Home class="w-3.5 h-3.5 text-indigo-400" />
            <span>Home</span>
          </button>

          <!-- Nested Path Breadcrumbs -->
          {#each breadcrumbs as crumb (crumb.path)}
            <div class="flex items-center gap-1.5 shrink-0">
              <ChevronRight class="w-3 h-3 text-slate-600 select-none" />
              <button
                type="button"
                onclick={() => !crumb.isLast && onOpenFolder(crumb.path)}
                class="px-2.5 py-1 rounded-lg transition shrink-0"
                class:text-white={crumb.isLast}
                class:font-semibold={crumb.isLast}
                class:bg-slate-900={crumb.isLast}
                class:border={crumb.isLast}
                class:border-slate-700={crumb.isLast}
                class:shadow-sm={crumb.isLast}
                class:cursor-default={crumb.isLast}
                class:text-slate-400={!crumb.isLast}
                class:hover:text-slate-200={!crumb.isLast}
                class:cursor-pointer={!crumb.isLast}
              >
                <span>{crumb.name}</span>
              </button>
            </div>
          {/each}
        </div>
      {/if}

      <!-- Overlap Switch Toggle -->
      <label class="flex items-center gap-2 cursor-pointer text-xs text-slate-400 select-none whitespace-nowrap shrink-0">
        <input
          type="checkbox"
          checked={audio.allowOverlap}
          onchange={() => audio.toggleOverlap()}
          class="sr-only peer"
        />
        <div class="w-7 h-4 bg-slate-800 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-3 after:w-3 after:transition-all peer-checked:bg-indigo-600 relative"></div>
        <span class="text-slate-300 font-medium">Overlap</span>
      </label>

    </div>

  </div>
</header>
